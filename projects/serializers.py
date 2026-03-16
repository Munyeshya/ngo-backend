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

    class Meta:
        model = Project
        fields = [
            "id",
            "title",
            "description",
            "status",
            "budget",
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