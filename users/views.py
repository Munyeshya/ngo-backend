from rest_framework import generics, permissions
from .models import User, StaffApplication
from .serializers import *
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.exceptions import PermissionDenied
from .permissions import IsAdminUserRole, IsAdminOrSelf
from core.views import success_response
from rest_framework import generics, permissions, status


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        user = serializer.instance
        message = "User registered successfully."

        if user.role == User.ROLE_STAFF:
            send_staff_application_received_email(user)
            message = "Staff registration submitted successfully. Await admin approval before login."

        return success_response(
            message=message,
            data=serializer.data,
            status_code=status.HTTP_201_CREATED,
        )


class ProfileView(generics.RetrieveAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    def retrieve(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_object())
        return success_response(
            message="User profile fetched successfully.",
            data=serializer.data,
        )

from .serializers import (
    UserRegisterSerializer,
    UserProfileSerializer,
    CustomTokenObtainPairSerializer,
    AdminUserUpdateSerializer,
    SelfUserUpdateSerializer,
    DonorClaimRequestSerializer,
    DonorClaimVerifySerializer,
    StaffApplicationSerializer,
    StaffApplicationReviewSerializer,
)
from .utils import (
    issue_donor_claim_token,
    send_donor_claim_email,
    send_donor_claim_success_email,
    send_staff_application_received_email,
    send_staff_application_submitted_email,
    send_staff_application_review_email,
    send_staff_status_email,
)


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            if not refresh_token:
                return Response(
                    {"detail": "Refresh token is required."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            token = RefreshToken(refresh_token)
            token.blacklist()

            return success_response(
                message="Logged out successfully.",
                data={},
                status_code=status.HTTP_200_OK,
            )
        except Exception:
            return Response(
                {"detail": "Invalid or expired refresh token."},
                status=status.HTTP_400_BAD_REQUEST
            )

class AdminOnlyView(APIView):
    permission_classes = [IsAdminUserRole]

    def get(self, request):
        return success_response(
            message="Welcome admin, you have access to this endpoint.",
            data={
                "user_id": request.user.id,
                "username": request.user.username,
                "role": request.user.role,
            },
        )

class UserListView(generics.ListAPIView):
    queryset = User.objects.all().order_by("-id")
    serializer_class = UserProfileSerializer
    permission_classes = [IsAdminUserRole]

    def list(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_queryset(), many=True)
        return success_response(
            message="Users fetched successfully.",
            data=serializer.data,
        )


class UserDetailView(generics.RetrieveUpdateAPIView):
    queryset = User.objects.all()

    def get_permissions(self):
        if self.request.method in ["PUT", "PATCH"]:
            return [permissions.IsAuthenticated(), IsAdminOrSelf()]
        return [IsAdminUserRole()]

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            target_user = self.get_object()
            if self.request.user.role == "admin" and self.request.user.id != target_user.id:
                return AdminUserUpdateSerializer
            return SelfUserUpdateSerializer
        return UserProfileSerializer

    def retrieve(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_object())
        return success_response(
            message="User fetched successfully.",
            data=serializer.data,
        )

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        self.check_object_permissions(request, instance)
        previous_is_active = instance.is_active
        previous_role = instance.role

        partial = kwargs.pop("partial", False)
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        updated_user = serializer.instance
        if (
            request.user.role == User.ROLE_ADMIN
            and previous_role == User.ROLE_STAFF
            and updated_user.role == User.ROLE_STAFF
            and previous_is_active != updated_user.is_active
        ):
            send_staff_status_email(updated_user)

        return success_response(
            message="User updated successfully.",
            data=serializer.data,
        )


class MyStaffApplicationView(generics.RetrieveUpdateAPIView):
    serializer_class = StaffApplicationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        user = self.request.user
        if user.role != User.ROLE_STAFF:
            raise PermissionDenied("Only staff users can manage staff applications.")
        application, _ = StaffApplication.objects.get_or_create(user=user)
        return application

    def retrieve(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_object())
        return success_response(
            message="Staff application fetched successfully.",
            data=serializer.data,
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        previous_status = instance.status
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        instance.refresh_from_db()
        if instance.status == StaffApplication.STATUS_UNDER_REVIEW and previous_status != StaffApplication.STATUS_UNDER_REVIEW:
            send_staff_application_submitted_email(instance)

        return success_response(
            message="Staff application updated successfully.",
            data=self.get_serializer(instance).data,
        )


class StaffApplicationListView(generics.ListAPIView):
    queryset = StaffApplication.objects.select_related("user", "reviewed_by").order_by("-updated_at")
    serializer_class = StaffApplicationSerializer
    permission_classes = [IsAdminUserRole]

    def list(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_queryset(), many=True)
        return success_response(
            message="Staff applications fetched successfully.",
            data=serializer.data,
        )


class StaffApplicationReviewView(generics.RetrieveUpdateAPIView):
    queryset = StaffApplication.objects.select_related("user", "reviewed_by")
    serializer_class = StaffApplicationReviewSerializer
    permission_classes = [IsAdminUserRole]

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return StaffApplicationReviewSerializer
        return StaffApplicationSerializer

    def retrieve(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_object())
        return success_response(
            message="Staff application fetched successfully.",
            data=serializer.data,
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        instance.reviewed_by = request.user
        instance.save(update_fields=["reviewed_by"])

        if instance.status == StaffApplication.STATUS_APPROVED:
            user = instance.user
            user.is_verified = True
            user.save(update_fields=["is_verified"])
            send_staff_status_email(user)
        else:
            send_staff_application_review_email(instance)

        return success_response(
            message="Staff application reviewed successfully.",
            data=StaffApplicationSerializer(instance).data,
        )

class DonorClaimRequestView(generics.GenericAPIView):
    serializer_class = DonorClaimRequestSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        if user:
            token = issue_donor_claim_token(user)
            send_donor_claim_email(user, token)

        return success_response(
            message="A donor claim verification email has been sent if the account exists.",
            data={},
            status_code=status.HTTP_200_OK,
        )


class DonorClaimVerifyView(generics.GenericAPIView):
    serializer_class = DonorClaimVerifySerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        send_donor_claim_success_email(user)

        return success_response(
            message="Donor account verified successfully. You can now log in.",
            data={
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "role": user.role,
                "is_verified": user.is_verified,
            },
            status_code=status.HTTP_200_OK,
        )
