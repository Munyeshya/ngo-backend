from django.db.models import Sum
from rest_framework import serializers
from .models import Project, Partner


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
    remaining_amount = serializers.SerializerMethodField()
    funding_percentage = serializers.SerializerMethodField()
    is_goal_reached = serializers.SerializerMethodField()
    exceeded_amount = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = [
            "id",
            "title",
            "description",
            "status",
            "budget",
            "target_amount",
            "start_date",
            "end_date",
            "location",
            "feature_image",
            "partners",
            "partner_ids",
            "created_by",
            "total_donated",
            "remaining_amount",
            "funding_percentage",
            "is_goal_reached",
            "exceeded_amount",
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

    def _get_total_donated(self, obj):
        total = obj.donations.filter(status="completed").aggregate(
            total=Sum("amount")
        )["total"]
        return total or 0

    def get_total_donated(self, obj):
        return self._get_total_donated(obj)

    def get_remaining_amount(self, obj):
        remaining = obj.target_amount - self._get_total_donated(obj)
        return remaining if remaining > 0 else 0

    def get_funding_percentage(self, obj):
        if obj.target_amount <= 0:
            return 0
        return round((self._get_total_donated(obj) / obj.target_amount) * 100, 2)

    def get_is_goal_reached(self, obj):
        return self._get_total_donated(obj) >= obj.target_amount and obj.target_amount > 0

    def get_exceeded_amount(self, obj):
        exceeded = self._get_total_donated(obj) - obj.target_amount
        return exceeded if exceeded > 0 else 0