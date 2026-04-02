from rest_framework import generics, permissions
from .models import User
from .serializers import *
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
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

        return success_response(
            message="User registered successfully.",
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
    DonorClaimAccountSerializer,
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

        partial = kwargs.pop("partial", False)
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return success_response(
            message="User updated successfully.",
            data=serializer.data,
        )

class DonorClaimAccountView(generics.GenericAPIView):
    serializer_class = DonorClaimAccountSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        return success_response(
            message="Donor account claimed successfully. You can now log in.",
            data={
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "role": user.role,
            },
            status_code=status.HTTP_200_OK,
        )
