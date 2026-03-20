from decimal import Decimal

from rest_framework import serializers
from .models import Donation
from users.models import User


class DonationSerializer(serializers.ModelSerializer):
    donor_display_name = serializers.SerializerMethodField()
    project_title = serializers.CharField(source="project.title", read_only=True)

    class Meta:
        model = Donation
        fields = [
            "id",
            "project",
            "project_title",
            "donor",
            "donor_name",
            "donor_email",
            "donor_display_name",
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

    def get_donor_display_name(self, obj):
        if obj.is_anonymous:
            return "Anonymous Donor"
        return obj.donor_name


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
        if value <= Decimal("0.00"):
            raise serializers.ValidationError("Donation amount must be greater than zero.")
        return value

    def create(self, validated_data):
        request = self.context.get("request")
        donor_user = None

        if request and request.user and request.user.is_authenticated:
            donor_user = request.user
        else:
            donor_email = validated_data["donor_email"]
            donor_name = validated_data["donor_name"]

            donor_user = User.objects.filter(email=donor_email).first()
            if not donor_user:
                base_username = donor_email.split("@")[0].lower().replace(" ", "_")
                username = base_username
                counter = 1
                while User.objects.filter(username=username).exists():
                    username = f"{base_username}_{counter}"
                    counter += 1

                donor_user = User.objects.create(
                    username=username,
                    email=donor_email,
                    first_name=donor_name,
                    role=User.ROLE_DONOR,
                    is_active=True,
                )
                donor_user.set_unusable_password()
                donor_user.save()

        donation = Donation.objects.create(
            donor=donor_user,
            status=Donation.STATUS_COMPLETED,
            **validated_data,
        )
        return donation