from decimal import Decimal

from django.db.models import Sum
from rest_framework import serializers

from .models import (
    Project,
    Partner,
    ProjectUpdate,
    ProjectUpdateImage,
    ProjectInterest,
    ProjectReport,
    ProjectCashout,
)


class PartnerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Partner
        fields = [
            "id",
            "name",
            "logo",
            "website",
            "description",
            "is_active",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class ProjectSerializer(serializers.ModelSerializer):
    partners = PartnerSerializer(many=True, read_only=True)
    partner_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Partner.objects.all(),
        write_only=True,
        source="partners",
        required=False,
    )
    created_by = serializers.StringRelatedField(read_only=True)
    project_type_display = serializers.CharField(source="get_project_type_display", read_only=True)
    total_donated = serializers.SerializerMethodField()
    total_cashouts = serializers.SerializerMethodField()
    available_balance = serializers.SerializerMethodField()
    reports_count = serializers.SerializerMethodField()
    funding_percentage = serializers.SerializerMethodField()
    remaining_amount = serializers.SerializerMethodField()
    exceeded_amount = serializers.SerializerMethodField()
    is_goal_reached = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = [
            "id",
            "title",
            "description",
            "project_type",
            "project_type_display",
            "status",
            "moderation_status",
            "funding_status",
            "moderation_note",
            "budget",
            "target_amount",
            "total_donated",
            "total_cashouts",
            "available_balance",
            "reports_count",
            "funding_percentage",
            "remaining_amount",
            "exceeded_amount",
            "is_goal_reached",
            "start_date",
            "end_date",
            "location",
            "feature_image",
            "partners",
            "partner_ids",
            "created_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_by", "created_at", "updated_at"]

    def validate(self, attrs):
        start_date = attrs.get("start_date")
        end_date = attrs.get("end_date")

        if start_date and end_date and end_date < start_date:
            raise serializers.ValidationError(
                {"end_date": "End date cannot be earlier than start date."}
            )

        return attrs

    def _completed_total(self, obj):
        total = obj.donations.filter(status="completed").aggregate(
            total=Sum("amount")
        )["total"]
        return total or Decimal("0.00")

    def get_total_donated(self, obj):
        return self._completed_total(obj)

    def get_total_cashouts(self, obj):
        return obj.total_cashouts()

    def get_available_balance(self, obj):
        return obj.available_balance()

    def get_reports_count(self, obj):
        return obj.reports.filter(status=ProjectReport.STATUS_OPEN).count()

    def get_funding_percentage(self, obj):
        total = self._completed_total(obj)
        target = obj.target_amount or Decimal("0.00")
        if target <= 0:
            return 0
        return round((total / target) * 100, 2)

    def get_remaining_amount(self, obj):
        total = self._completed_total(obj)
        target = obj.target_amount or Decimal("0.00")
        remaining = target - total
        return remaining if remaining > 0 else Decimal("0.00")

    def get_exceeded_amount(self, obj):
        total = self._completed_total(obj)
        target = obj.target_amount or Decimal("0.00")
        exceeded = total - target
        return exceeded if exceeded > 0 else Decimal("0.00")

    def get_is_goal_reached(self, obj):
        total = self._completed_total(obj)
        target = obj.target_amount or Decimal("0.00")
        return target > 0 and total >= target
class ProjectUpdateImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectUpdateImage
        fields = [
            "id",
            "image",
            "caption",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class ProjectUpdateSerializer(serializers.ModelSerializer):
    images = ProjectUpdateImageSerializer(many=True, read_only=True)
    project_title = serializers.CharField(source="project.title", read_only=True)
    created_by = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = ProjectUpdate
        fields = [
            "id",
            "project",
            "project_title",
            "title",
            "description",
            "update_type",
            "cashout_amount",
            "remaining_balance",
            "images",
            "created_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_by", "created_at", "updated_at"]


class ProjectUpdateImageCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectUpdateImage
        fields = [
            "id",
            "project_update",
            "image",
            "caption",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class ProjectReportSerializer(serializers.ModelSerializer):
    project_title = serializers.CharField(source="project.title", read_only=True)
    reported_by_username = serializers.CharField(source="reported_by.username", read_only=True)

    class Meta:
        model = ProjectReport
        fields = [
            "id",
            "project",
            "project_title",
            "reported_by",
            "reported_by_username",
            "reason_type",
            "claim_text",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "reported_by",
            "status",
            "created_at",
            "updated_at",
        ]


class ProjectCashoutSerializer(serializers.ModelSerializer):
    project_title = serializers.CharField(source="project.title", read_only=True)
    requested_by_username = serializers.CharField(source="requested_by.username", read_only=True)

    class Meta:
        model = ProjectCashout
        fields = [
            "id",
            "project",
            "project_title",
            "requested_by",
            "requested_by_username",
            "amount",
            "purpose",
            "remaining_balance",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "requested_by",
            "remaining_balance",
            "created_at",
        ]

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Cashout amount must be greater than zero.")
        return value

    def validate(self, attrs):
        project = attrs["project"]
        amount = attrs["amount"]
        request = self.context.get("request")

        if request and request.user.role == "staff" and project.created_by_id != request.user.id:
            raise serializers.ValidationError({"project": "You can only cash out from your own projects."})

        if not project.can_cash_out():
            raise serializers.ValidationError(
                {"project": "This project is currently restricted from cashout activity."}
            )

        if amount > project.available_balance():
            raise serializers.ValidationError(
                {"amount": "Cashout amount exceeds the available project balance."}
            )

        return attrs

class ProjectInterestSerializer(serializers.ModelSerializer):
    project_title = serializers.CharField(source="project.title", read_only=True)
    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = ProjectInterest
        fields = [
            "id",
            "project",
            "project_title",
            "user",
            "username",
            "name",
            "email",
            "is_active",
            "created_at",
        ]
        read_only_fields = ["id", "user", "created_at"]


class ProjectInterestCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectInterest
        fields = [
            "project",
            "name",
            "email",
        ]

    def validate(self, attrs):
        request = self.context.get("request")
        project = attrs["project"]
        email = attrs["email"]

        existing = ProjectInterest.objects.filter(project=project, email=email).first()
        if existing and existing.is_active:
            raise serializers.ValidationError(
                {"email": "This email is already subscribed to this project."}
            )

        attrs["existing_interest"] = existing
        attrs["request_user"] = request.user if request and request.user.is_authenticated else None
        return attrs

    def create(self, validated_data):
        existing_interest = validated_data.pop("existing_interest", None)
        request_user = validated_data.pop("request_user", None)

        if existing_interest:
            existing_interest.name = validated_data.get("name")
            existing_interest.user = request_user or existing_interest.user
            existing_interest.is_active = True
            existing_interest.save()
            return existing_interest

        return ProjectInterest.objects.create(
            user=request_user,
            is_active=True,
            **validated_data,
        )
