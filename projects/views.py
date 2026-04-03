from rest_framework import generics, permissions, status
from core.views import success_response
from users.permissions import IsAdminUserRole, IsStaffUserRole, IsAdminOrStaffProjectOwner,IsAdminOrStaffProjectUpdateOwner,IsAdminOrStaffProjectUpdateImageOwner
from .models import Partner, Project, ProjectUpdate, ProjectUpdateImage,ProjectInterest, ProjectReport, ProjectCashout
from .serializers import PartnerSerializer, ProjectSerializer,ProjectUpdateSerializer,ProjectUpdateImageSerializer,ProjectUpdateImageCreateSerializer,ProjectInterestSerializer,ProjectInterestCreateSerializer, ProjectReportSerializer, ProjectCashoutSerializer
from .utils import send_project_update_notifications

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
    filterset_fields = ["status", "project_type", "location", "partners"]
    search_fields = ["title", "description", "location", "project_type"]
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

        if request.user.role == "staff":
            application = getattr(request.user, "staff_application", None)
            if not application or not application.can_create_projects():
                return success_response(
                    message="Your staff verification must be approved before you can create projects.",
                    data={},
                    status_code=status.HTTP_403_FORBIDDEN,
                )

        if request.user.role == "staff":
            protected_fields = {"moderation_status", "funding_status", "moderation_note"}
            if protected_fields.intersection(request.data.keys()):
                return success_response(
                    message="Staff users cannot set project moderation controls.",
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

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        if not user or not user.is_authenticated:
            return queryset

        if user.role == "admin":
            return queryset

        if user.role == "staff":
            return queryset.filter(created_by=user)

        return queryset

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

        if request.user.role == "staff":
            protected_fields = {"moderation_status", "funding_status", "moderation_note"}
            if protected_fields.intersection(request.data.keys()):
                return success_response(
                    message="Staff users cannot change project moderation controls.",
                    data={},
                    status_code=status.HTTP_403_FORBIDDEN,
                )

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

class ProjectUpdateListCreateView(generics.ListCreateAPIView):
    queryset = ProjectUpdate.objects.select_related("project", "created_by", "project__created_by").prefetch_related("images")
    serializer_class = ProjectUpdateSerializer
    filterset_fields = ["project"]
    search_fields = ["title", "description", "project__title"]
    ordering_fields = ["created_at", "title"]
    ordering = ["-created_at"]

    def get_permissions(self):
        if self.request.method == "POST":
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        if not user or not user.is_authenticated:
            return queryset

        if user.role == "admin":
            return queryset

        if user.role == "staff":
            return queryset.filter(project__created_by=user)

        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return success_response(
                message="Project updates fetched successfully.",
                data={
                    "count": self.paginator.page.paginator.count,
                    "next": self.paginator.get_next_link(),
                    "previous": self.paginator.get_previous_link(),
                    "results": serializer.data,
                },
            )

        serializer = self.get_serializer(queryset, many=True)
        return success_response(
            message="Project updates fetched successfully.",
            data=serializer.data,
        )

    def create(self, request, *args, **kwargs):
        if request.user.role not in ["admin", "staff"]:
            return success_response(
                message="You do not have permission to create a project update.",
                data={},
                status_code=status.HTTP_403_FORBIDDEN,
            )

        project_id = request.data.get("project")
        if request.user.role == "staff":
            owns_project = Project.objects.filter(id=project_id, created_by=request.user).exists()
            if not owns_project:
                return success_response(
                    message="You can only create updates for your own projects.",
                    data={},
                    status_code=status.HTTP_403_FORBIDDEN,
                )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        project_update = serializer.save(created_by=request.user)

        sent_count = send_project_update_notifications(project_update)

        response_serializer = self.get_serializer(project_update)
        return success_response(
            message=f"Project update created successfully. Notifications sent to {sent_count} recipient(s).",
            data=response_serializer.data,
            status_code=status.HTTP_201_CREATED,
        )


class ProjectUpdateDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = ProjectUpdate.objects.select_related("project", "created_by", "project__created_by").prefetch_related("images")
    serializer_class = ProjectUpdateSerializer

    def get_permissions(self):
        if self.request.method in ["PUT", "PATCH", "DELETE"]:
            return [permissions.IsAuthenticated(), IsAdminOrStaffProjectUpdateOwner()]
        return [permissions.AllowAny()]

    def retrieve(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_object())
        return success_response(
            message="Project update fetched successfully.",
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
            message="Project update updated successfully.",
            data=serializer.data,
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.check_object_permissions(request, instance)
        self.perform_destroy(instance)

        return success_response(
            message="Project update deleted successfully.",
            data={},
        )


class ProjectUpdateImageCreateView(generics.CreateAPIView):
    queryset = ProjectUpdateImage.objects.select_related("project_update", "project_update__project")
    serializer_class = ProjectUpdateImageCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        if request.user.role not in ["admin", "staff"]:
            return success_response(
                message="You do not have permission to upload a project update image.",
                data={},
                status_code=status.HTTP_403_FORBIDDEN,
            )

        project_update_id = request.data.get("project_update")
        if not project_update_id:
            return success_response(
                message="Project update field is required.",
                data={},
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        if request.user.role == "staff":
            owns_update_project = ProjectUpdate.objects.filter(
                id=project_update_id,
                project__created_by=request.user
            ).exists()

            if not owns_update_project:
                return success_response(
                    message="You can only upload images for updates under your own projects.",
                    data={},
                    status_code=status.HTTP_403_FORBIDDEN,
                )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        response_serializer = ProjectUpdateImageSerializer(serializer.instance)
        return success_response(
            message="Project update image uploaded successfully.",
            data=response_serializer.data,
            status_code=status.HTTP_201_CREATED,
        )


class ProjectUpdateImageDeleteView(generics.DestroyAPIView):
    queryset = ProjectUpdateImage.objects.select_related("project_update", "project_update__project")
    serializer_class = ProjectUpdateImageSerializer

    def get_permissions(self):
        return [permissions.IsAuthenticated(), IsAdminOrStaffProjectUpdateImageOwner()]

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.check_object_permissions(request, instance)
        self.perform_destroy(instance)

        return success_response(
            message="Project update image deleted successfully.",
            data={},
        )
    
class ProjectInterestSubscribeView(generics.CreateAPIView):
    queryset = ProjectInterest.objects.select_related("project", "user")
    serializer_class = ProjectInterestCreateSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        interest = serializer.save()

        response_serializer = ProjectInterestSerializer(interest)
        return success_response(
            message="Project interest subscription saved successfully.",
            data=response_serializer.data,
            status_code=status.HTTP_201_CREATED,
        )


class ProjectInterestUnsubscribeView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        project_id = request.data.get("project")
        email = request.data.get("email")

        if not project_id or not email:
            return success_response(
                message="Project and email are required.",
                data={},
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        interest = ProjectInterest.objects.filter(
            project_id=project_id,
            email=email,
            is_active=True
        ).first()

        if not interest:
            return success_response(
                message="No active subscription found for this project and email.",
                data={},
                status_code=status.HTTP_404_NOT_FOUND,
            )

        interest.is_active = False
        interest.save()

        return success_response(
            message="Project interest unsubscribed successfully.",
            data={},
            status_code=status.HTTP_200_OK,
        )


class MyProjectInterestsView(generics.ListAPIView):
    serializer_class = ProjectInterestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ProjectInterest.objects.select_related("project", "user").filter(
            user=self.request.user,
            is_active=True
        ).order_by("-created_at")

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return success_response(
                message="My project interests fetched successfully.",
                data={
                    "count": self.paginator.page.paginator.count,
                    "next": self.paginator.get_next_link(),
                    "previous": self.paginator.get_previous_link(),
                    "results": serializer.data,
                },
            )

        serializer = self.get_serializer(queryset, many=True)
        return success_response(
            message="My project interests fetched successfully.",
            data=serializer.data,
        )


class ProjectReportListCreateView(generics.ListCreateAPIView):
    queryset = ProjectReport.objects.select_related("project", "reported_by", "project__created_by")
    serializer_class = ProjectReportSerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [permissions.IsAuthenticated()]
        return [IsAdminUserRole()]

    def get_queryset(self):
        queryset = super().get_queryset()
        project_id = self.request.query_params.get("project")
        status_filter = self.request.query_params.get("status")

        if project_id:
            queryset = queryset.filter(project_id=project_id)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        return queryset

    def list(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_queryset(), many=True)
        return success_response(
            message="Project reports fetched successfully.",
            data=serializer.data,
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        report = serializer.save(reported_by=request.user)

        project = report.project
        if project.moderation_status == Project.MODERATION_CLEAR:
            project.moderation_status = Project.MODERATION_UNDER_REVIEW
            project.moderation_note = "Project flagged for admin review after user report."
            project.save(update_fields=["moderation_status", "moderation_note", "updated_at"])

        return success_response(
            message="Project report submitted successfully.",
            data=self.get_serializer(report).data,
            status_code=status.HTTP_201_CREATED,
        )


class ProjectCashoutListCreateView(generics.ListCreateAPIView):
    queryset = ProjectCashout.objects.select_related("project", "requested_by", "project__created_by")
    serializer_class = ProjectCashoutSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        project_id = self.request.query_params.get("project")

        if user.role == "admin":
            filtered = queryset
        elif user.role == "staff":
            filtered = queryset.filter(project__created_by=user)
        else:
            return queryset.none()

        if project_id:
            filtered = filtered.filter(project_id=project_id)
        return filtered

    def list(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_queryset(), many=True)
        return success_response(
            message="Project cashouts fetched successfully.",
            data=serializer.data,
        )

    def create(self, request, *args, **kwargs):
        if request.user.role not in ["admin", "staff"]:
            return success_response(
                message="You do not have permission to record a cashout.",
                data={},
                status_code=status.HTTP_403_FORBIDDEN,
            )

        serializer = self.get_serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        cashout = serializer.save(
            requested_by=request.user,
            remaining_balance=serializer.validated_data["project"].available_balance() - serializer.validated_data["amount"],
        )

        ProjectUpdate.objects.create(
            project=cashout.project,
            title=f"Project cashout recorded - {cashout.amount}",
            description=cashout.purpose,
            update_type=ProjectUpdate.TYPE_CASHOUT,
            cashout_amount=cashout.amount,
            remaining_balance=cashout.remaining_balance,
            created_by=request.user,
        )

        return success_response(
            message="Project cashout recorded successfully.",
            data=self.get_serializer(cashout).data,
            status_code=status.HTTP_201_CREATED,
        )
