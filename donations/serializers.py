from rest_framework import serializers
from .models import Donation


class DonationSerializer(serializers.ModelSerializer):
    project_title = serializers.CharField(source="project.title", read_only=True)
    donor = serializers.SerializerMethodField()
    donor_username = serializers.SerializerMethodField()
    donor_name = serializers.SerializerMethodField()
    donor_email = serializers.SerializerMethodField()

    class Meta:
        model = Donation
        fields = [
            "id",
            "project",
            "project_title",
            "donor",
            "donor_username",
            "donor_name",
            "donor_email",
            "amount",
            "payment_method",
            "status",
            "message",
            "is_anonymous",
            "transaction_reference",
            "donated_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "status",
            "transaction_reference",
            "donated_at",
            "updated_at",
        ]

    def _can_view_identity(self, obj):
        if not obj.is_anonymous:
            return True

        request = self.context.get("request")
        if not request or not request.user or not request.user.is_authenticated:
            return False

        return request.user.role == "admin" or obj.donor_id == request.user.id

    def get_donor(self, obj):
        if not self._can_view_identity(obj):
            return None
        return obj.donor_id

    def get_donor_username(self, obj):
        if not self._can_view_identity(obj) or not obj.donor:
            return None
        return obj.donor.username

    def get_donor_name(self, obj):
        if not self._can_view_identity(obj):
            return "Anonymous"
        return obj.donor_name

    def get_donor_email(self, obj):
        if not self._can_view_identity(obj):
            return None
        return obj.donor_email


class PublicDonationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Donation
        fields = [
            "project",
            "donor_name",
            "donor_email",
            "amount",
            "payment_method",
            "message",
            "is_anonymous",
        ]

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Donation amount must be greater than zero.")
        return value

    def create(self, validated_data):
        request = self.context.get("request")
        donor_user = None

        if request and request.user and request.user.is_authenticated:
            donor_user = request.user

        donation = Donation.objects.create(
            donor=donor_user,
            status=Donation.STATUS_COMPLETED,
            **validated_data
        )
        return donation
