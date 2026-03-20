from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import Donation

User = get_user_model()


class DonationSerializer(serializers.ModelSerializer):
    project_title = serializers.CharField(source="project.title", read_only=True)
    donor_username = serializers.CharField(source="donor.username", read_only=True)

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
            "donor",
            "status",
            "transaction_reference",
            "donated_at",
            "updated_at",
        ]


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

        donor_email = validated_data["donor_email"]

        if donor_user is None:
            existing_user = User.objects.filter(email=donor_email).first()
            if existing_user:
                donor_user = existing_user

        donation = Donation.objects.create(
            donor=donor_user,
            status=Donation.STATUS_COMPLETED,
            **validated_data
        )
        return donation