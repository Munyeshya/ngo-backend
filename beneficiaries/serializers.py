from rest_framework import serializers
from .models import *


class BeneficiaryImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = BeneficiaryImage
        fields = [
            "id",
            "image",
            "caption",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class BeneficiarySerializer(serializers.ModelSerializer):
    images = BeneficiaryImageSerializer(many=True, read_only=True)
    project_title = serializers.CharField(source="project.title", read_only=True)

    class Meta:
        model = Beneficiary
        fields = [
            "id",
            "project",
            "project_title",
            "name",
            "description",
            "is_active",
            "images",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class BeneficiaryImageCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = BeneficiaryImage
        fields = [
            "id",
            "beneficiary",
            "image",
            "caption",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]