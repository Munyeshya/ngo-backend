from rest_framework import generics, permissions, status
from core.views import success_response
from users.permissions import IsAdminUserRole, IsStaffUserRole, IsAdminOrStaffProjectOwner
from .models import Partner, Project
from .serializers import PartnerSerializer, ProjectSerializer


class PartnerListCreateView(generics.ListCreateAPIView):
    queryset = Partner.objects.all()
    serializer_class = PartnerSerializer
    filterset_fields = ["is_active"]
    search_fields = ["name", "description", "website"]
    ordering_fields = ["name", "created_at"]
    ordering = ["name"]

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAdminUserRole()]
        return [permissions.AllowAny()]

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return success_response(
                message="Partners fetched successfully.",
                data={
                    "count": self.paginator.page.paginator.count,
                    "next": self.paginator.get_next_link(),
                    "previous": self.paginator.get_previous_link(),
                    "results": serializer.data,
                },
            )

        serializer = self.get_serializer(queryset, many=True)
        return success_response(
            message="Partners fetched successfully.",
            data=serializer.data,
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return success_response(
            message="Partner created successfully.",
            data=serializer.data,
            status_code=status.HTTP_201_CREATED,
        )


class PartnerDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Partner.objects.all()
    serializer_class = PartnerSerializer

    def get_permissions(self):
        if self.request.method in ["PUT", "PATCH", "DELETE"]:
            return [IsAdminUserRole()]
        return [permissions.AllowAny()]

    def retrieve(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_object())
        return success_response(
            message="Partner fetched successfully.",
            data=serializer.data,
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return success_response(
            message="Partner updated successfully.",
            data=serializer.data,
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return success_response(
            message="Partner deleted successfully.",
            data={},
        )


class ProjectListCreateView(generics.ListCreateAPIView):
    queryset = Project.objects.select_related("created_by").prefetch_related("partners")
    serializer_class = ProjectSerializer
    filterset_fields = ["status", "location", "partners"]
    search_fields = ["title", "description", "location"]
    ordering_fields = ["created_at", "start_date", "budget", "title"]
    ordering = ["-created_at"]

    def get_permissions(self):
        if self.request.method == "POST":
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def create(self, request, *args, **kwargs):
        if request.user.role not in ["admin", "staff"]:
            return success_response(
                message="You do not have permission to create a project.",
                data={},
                status_code=status.HTTP_403_FORBIDDEN,
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return success_response(
            message="Project created successfully.",
            data=serializer.data,
            status_code=status.HTTP_201_CREATED,
        )

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return success_response(
                message="Projects fetched successfully.",
                data={
                    "count": self.paginator.page.paginator.count,
                    "next": self.paginator.get_next_link(),
                    "previous": self.paginator.get_previous_link(),
                    "results": serializer.data,
                },
            )

        serializer = self.get_serializer(queryset, many=True)
        return success_response(
            message="Projects fetched successfully.",
            data=serializer.data,
        )


class ProjectDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Project.objects.select_related("created_by").prefetch_related("partners")
    serializer_class = ProjectSerializer

    def get_permissions(self):
        if self.request.method in ["PUT", "PATCH", "DELETE"]:
            return [permissions.IsAuthenticated(), IsAdminOrStaffProjectOwner()]
        return [permissions.AllowAny()]

    def perform_update(self, serializer):
        serializer.save()

    def retrieve(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_object())
        return success_response(
            message="Project fetched successfully.",
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
            message="Project updated successfully.",
            data=serializer.data,
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.check_object_permissions(request, instance)

        self.perform_destroy(instance)
        return success_response(
            message="Project deleted successfully.",
            data={},
        )