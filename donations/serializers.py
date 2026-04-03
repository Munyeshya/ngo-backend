from uuid import uuid4

from django.contrib.auth import get_user_model
from django.utils.text import slugify
from rest_framework import serializers
from .models import Donation

User = get_user_model()


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

    def validate(self, attrs):
        project = attrs["project"]
        if not project.can_accept_donations():
            raise serializers.ValidationError(
                {
                    "project": "This project is currently not accepting donations while under admin review."
                }
            )
        return attrs

    def create(self, validated_data):
        request = self.context.get("request")
        donor_user = None

        if request and request.user and request.user.is_authenticated:
            donor_user = request.user
        else:
            donor_email = validated_data["donor_email"]
            donor_user = User.objects.filter(email=donor_email, role=User.ROLE_DONOR).first()

            if donor_user is None and not User.objects.filter(email=donor_email).exists():
                username_root = slugify(donor_email.split("@")[0]) or "donor"
                donor_user = User(
                    username=f"{username_root}-{uuid4().hex[:8]}",
                    email=donor_email,
                    role=User.ROLE_DONOR,
                    is_active=True,
                    is_verified=False,
                )
                donor_user.set_unusable_password()
                donor_user.save()

        donation = Donation.objects.create(
            donor=donor_user,
            status=Donation.STATUS_COMPLETED,
            **validated_data
        )
        return donation
