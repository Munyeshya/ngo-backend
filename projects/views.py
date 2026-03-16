from rest_framework import generics, permissions, status
from core.views import success_response
from users.permissions import IsAdminUserRole
from .models import Partner, Project
from .serializers import PartnerSerializer, ProjectSerializer


class PartnerListCreateView(generics.ListCreateAPIView):
    queryset = Partner.objects.all()
    serializer_class = PartnerSerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAdminUserRole()]
        return [permissions.IsAuthenticated()]

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
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


class ProjectListCreateView(generics.ListCreateAPIView):
    queryset = Project.objects.select_related("created_by").prefetch_related("partners")
    serializer_class = ProjectSerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAdminUserRole()]
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return success_response(
            message="Projects fetched successfully.",
            data=serializer.data,
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return success_response(
            message="Project created successfully.",
            data=serializer.data,
            status_code=status.HTTP_201_CREATED,
        )