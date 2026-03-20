from rest_framework import generics, permissions, status

from core.views import success_response
from .models import Donation
from .serializers import DonationSerializer, PublicDonationCreateSerializer


class DonationListCreateView(generics.ListCreateAPIView):
    queryset = Donation.objects.select_related("project", "donor", "project__created_by")
    filterset_fields = ["project", "status", "payment_method", "is_anonymous"]
    search_fields = ["donor_name", "donor_email", "project__title", "transaction_reference"]
    ordering_fields = ["donated_at", "amount"]
    ordering = ["-donated_at"]

    def get_permissions(self):
        if self.request.method == "POST":
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        if user.role == "admin":
            return queryset
        if user.role == "staff":
            return queryset.filter(project__created_by=user)
        if user.role == "donor":
            return queryset.filter(donor=user)
        return queryset.none()

    def get_serializer_class(self):
        if self.request.method == "POST":
            return PublicDonationCreateSerializer
        return DonationSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return success_response(
                message="Donations fetched successfully.",
                data={
                    "count": self.paginator.page.paginator.count,
                    "next": self.paginator.get_next_link(),
                    "previous": self.paginator.get_previous_link(),
                    "results": serializer.data,
                },
            )

        serializer = self.get_serializer(queryset, many=True)
        return success_response(
            message="Donations fetched successfully.",
            data=serializer.data,
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        donation = serializer.save()

        response_serializer = DonationSerializer(donation)
        return success_response(
            message="Donation created successfully.",
            data=response_serializer.data,
            status_code=status.HTTP_201_CREATED,
        )


class DonationDetailView(generics.RetrieveAPIView):
    queryset = Donation.objects.select_related("project", "donor", "project__created_by")
    serializer_class = DonationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        if user.role == "admin":
            return queryset
        if user.role == "staff":
            return queryset.filter(project__created_by=user)
        if user.role == "donor":
            return queryset.filter(donor=user)
        return queryset.none()

    def retrieve(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_object())
        return success_response(
            message="Donation fetched successfully.",
            data=serializer.data,
        )


class MyDonationsView(generics.ListAPIView):
    serializer_class = DonationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Donation.objects.select_related("project", "donor").filter(
            donor=self.request.user
        ).order_by("-donated_at")

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return success_response(
                message="My donations fetched successfully.",
                data={
                    "count": self.paginator.page.paginator.count,
                    "next": self.paginator.get_next_link(),
                    "previous": self.paginator.get_previous_link(),
                    "results": serializer.data,
                },
            )

        serializer = self.get_serializer(queryset, many=True)
        return success_response(
            message="My donations fetched successfully.",
            data=serializer.data,
        )