from decimal import Decimal

from rest_framework import serializers
from .models import Project, Partner
from django.db.models import Sum


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
    total_donated = serializers.SerializerMethodField()
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
            "status",
            "budget",
            "target_amount",
            "total_donated",
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