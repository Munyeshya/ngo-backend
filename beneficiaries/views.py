from rest_framework import generics, permissions, status
from core.views import success_response
from users.permissions import IsAdminUserRole, IsAdminOrStaffBeneficiaryProjectOwner,IsAdminOrStaffBeneficiaryImageProjectOwner
from .models import Beneficiary, BeneficiaryImage
from projects.models import Project
from .serializers import *


class BeneficiaryListCreateView(generics.ListCreateAPIView):
    queryset = Beneficiary.objects.select_related("project").prefetch_related("images")
    serializer_class = BeneficiarySerializer
    filterset_fields = ["project", "is_active"]
    search_fields = ["name", "description", "project__title"]
    ordering_fields = ["created_at", "name"]
    ordering = ["-created_at"]

    def get_permissions(self):
        if self.request.method == "POST":
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    def create(self, request, *args, **kwargs):
        if request.user.role not in ["admin", "staff"]:
            return success_response(
                message="You do not have permission to create a beneficiary.",
                data={},
                status_code=status.HTTP_403_FORBIDDEN,
            )

        project_id = request.data.get("project")
        if request.user.role == "staff":
            owns_project = Project.objects.filter(id=project_id, created_by=request.user).exists()
            if not owns_project:
                return success_response(
                    message="You can only add beneficiaries to your own projects.",
                    data={},
                    status_code=status.HTTP_403_FORBIDDEN,
                )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return success_response(
            message="Beneficiary created successfully.",
            data=serializer.data,
            status_code=status.HTTP_201_CREATED,
        )

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return success_response(
                message="Beneficiaries fetched successfully.",
                data={
                    "count": self.paginator.page.paginator.count,
                    "next": self.paginator.get_next_link(),
                    "previous": self.paginator.get_previous_link(),
                    "results": serializer.data,
                },
            )

        serializer = self.get_serializer(queryset, many=True)
        return success_response(
            message="Beneficiaries fetched successfully.",
            data=serializer.data,
        )


class BeneficiaryDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Beneficiary.objects.select_related("project").prefetch_related("images")
    serializer_class = BeneficiarySerializer

    def get_permissions(self):
        if self.request.method in ["PUT", "PATCH", "DELETE"]:
            return [permissions.IsAuthenticated(), IsAdminOrStaffBeneficiaryProjectOwner()]
        return [permissions.AllowAny()]

    def retrieve(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_object())
        return success_response(
            message="Beneficiary fetched successfully.",
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
            message="Beneficiary updated successfully.",
            data=serializer.data,
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.check_object_permissions(request, instance)

        self.perform_destroy(instance)
        return success_response(
            message="Beneficiary deleted successfully.",
            data={},
        )


class BeneficiaryImageCreateView(generics.CreateAPIView):
    queryset = BeneficiaryImage.objects.select_related("beneficiary", "beneficiary__project")
    serializer_class = BeneficiaryImageCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        if request.user.role not in ["admin", "staff"]:
            return success_response(
                message="You do not have permission to upload a beneficiary image.",
                data={},
                status_code=status.HTTP_403_FORBIDDEN,
            )

        beneficiary_id = request.data.get("beneficiary")
        if not beneficiary_id:
            return success_response(
                message="Beneficiary field is required.",
                data={},
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        if request.user.role == "staff":
            owns_beneficiary_project = Beneficiary.objects.filter(
                id=beneficiary_id,
                project__created_by=request.user
            ).exists()

            if not owns_beneficiary_project:
                return success_response(
                    message="You can only upload images for beneficiaries under your own projects.",
                    data={},
                    status_code=status.HTTP_403_FORBIDDEN,
                )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        response_serializer = BeneficiaryImageSerializer(serializer.instance)
        return success_response(
            message="Beneficiary image uploaded successfully.",
            data=response_serializer.data,
            status_code=status.HTTP_201_CREATED,
        )


class BeneficiaryImageDeleteView(generics.DestroyAPIView):
    queryset = BeneficiaryImage.objects.select_related("beneficiary", "beneficiary__project")
    serializer_class = BeneficiaryImageSerializer

    def get_permissions(self):
        return [permissions.IsAuthenticated(), IsAdminOrStaffBeneficiaryImageProjectOwner()]

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.check_object_permissions(request, instance)

        self.perform_destroy(instance)
        return success_response(
            message="Beneficiary image deleted successfully.",
            data={},
        )