from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.utils import timezone
from .models import User, StaffApplication


class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "phone_number",
            "profile_image",
            "role",
            "password",
        ]

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate_role(self, value):
        valid_roles = [choice[0] for choice in User.ROLE_CHOICES]
        if value not in valid_roles:
            raise serializers.ValidationError("Invalid role selected.")
        return value

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("A user with this username already exists.")
        return value

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        if user.role == User.ROLE_STAFF:
            user.is_active = True
            user.is_verified = False
        user.set_password(password)
        user.save()
        if user.role == User.ROLE_STAFF:
            StaffApplication.objects.get_or_create(user=user)
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    staff_application_status = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "phone_number",
            "profile_image",
            "first_name",
            "last_name",
            "role",
            "is_verified",
            "is_active",
            "date_joined",
            "staff_application_status",
        ]

    def get_staff_application_status(self, obj):
        if obj.role != User.ROLE_STAFF:
            return None
        application = getattr(obj, "staff_application", None)
        return application.status if application else None


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["username"] = user.username
        token["email"] = user.email
        token["role"] = user.role
        return token

    def validate(self, attrs):
        data = super().validate(attrs)

        data["user"] = {
            "id": self.user.id,
            "username": self.user.username,
            "email": self.user.email,
            "phone_number": self.user.phone_number,
            "profile_image": self.user.profile_image.url if self.user.profile_image else None,
            "role": self.user.role,
            "is_verified": self.user.is_verified,
        }

        return data


class AdminUserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "phone_number",
            "profile_image",
            "role",
            "is_verified",
            "is_active",
            "first_name",
            "last_name",
        ]

    def validate_email(self, value):
        user_id = self.instance.id if self.instance else None
        if User.objects.exclude(id=user_id).filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate_username(self, value):
        user_id = self.instance.id if self.instance else None
        if User.objects.exclude(id=user_id).filter(username=value).exists():
            raise serializers.ValidationError("A user with this username already exists.")
        return value

    def validate_role(self, value):
        if value == User.ROLE_ADMIN:
            raise serializers.ValidationError("Admin accounts cannot be created through public registration.")
        if value not in [User.ROLE_STAFF, User.ROLE_DONOR]:
            raise serializers.ValidationError("Invalid role selected.")
        return value


class SelfUserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "phone_number",
            "profile_image",
            "first_name",
            "last_name",
        ]

    def validate_email(self, value):
        user_id = self.instance.id if self.instance else None
        if User.objects.exclude(id=user_id).filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate_username(self, value):
        user_id = self.instance.id if self.instance else None
        if User.objects.exclude(id=user_id).filter(username=value).exists():
            raise serializers.ValidationError("A user with this username already exists.")
        return value

class DonorClaimRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate(self, attrs):
        email = attrs["email"]
        user = User.objects.filter(email=email, role=User.ROLE_DONOR).first()
        attrs["user"] = user
        return attrs


class DonorClaimVerifySerializer(serializers.Serializer):
    token = serializers.CharField()
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True, min_length=8)

    def validate(self, attrs):
        if attrs["password"] != attrs["confirm_password"]:
            raise serializers.ValidationError(
                {"confirm_password": "Passwords do not match."}
            )

        token = attrs["token"]
        user = User.objects.filter(
            donor_claim_token=token,
            role=User.ROLE_DONOR,
        ).first()

        if not user or not user.donor_claim_token_is_valid(token):
            raise serializers.ValidationError(
                {"token": "This donor claim token is invalid or expired."}
            )

        attrs["user"] = user
        return attrs

    def save(self, **kwargs):
        user = self.validated_data["user"]
        password = self.validated_data["password"]

        user.set_password(password)
        user.is_verified = True
        user.donor_claim_token = None
        user.donor_claim_token_expires_at = None
        user.save()

        return user


class StaffApplicationSerializer(serializers.ModelSerializer):
    user = UserProfileSerializer(read_only=True)

    class Meta:
        model = StaffApplication
        fields = [
            "id",
            "user",
            "applicant_type",
            "status",
            "mission_summary",
            "location",
            "organization_name",
            "registration_number",
            "representative_name",
            "representative_id_number",
            "individual_id_number",
            "individual_id_document",
            "group_legal_document",
            "representative_id_document",
            "individual_id_status",
            "group_legal_document_status",
            "representative_id_status",
            "individual_id_reason",
            "group_legal_document_reason",
            "representative_id_reason",
            "admin_message",
            "submitted_at",
            "reviewed_at",
            "updated_at",
            "created_at",
        ]
        read_only_fields = [
            "status",
            "individual_id_status",
            "group_legal_document_status",
            "representative_id_status",
            "individual_id_reason",
            "group_legal_document_reason",
            "representative_id_reason",
            "admin_message",
            "submitted_at",
            "reviewed_at",
            "updated_at",
            "created_at",
        ]

    def validate(self, attrs):
        applicant_type = attrs.get("applicant_type", getattr(self.instance, "applicant_type", StaffApplication.TYPE_INDIVIDUAL))

        if applicant_type == StaffApplication.TYPE_INDIVIDUAL:
            individual_id_number = attrs.get("individual_id_number", getattr(self.instance, "individual_id_number", ""))
            individual_id_document = attrs.get("individual_id_document", getattr(self.instance, "individual_id_document", None))
            if not individual_id_number:
                raise serializers.ValidationError({"individual_id_number": "ID number is required for individual applicants."})
            if not individual_id_document:
                raise serializers.ValidationError({"individual_id_document": "ID document is required for individual applicants."})
        else:
            required_fields = {
                "organization_name": "Organization or group name is required.",
                "registration_number": "Registration number is required.",
                "representative_name": "Representative name is required.",
                "representative_id_number": "Representative ID number is required.",
            }
            for field_name, message in required_fields.items():
                value = attrs.get(field_name, getattr(self.instance, field_name, ""))
                if not value:
                    raise serializers.ValidationError({field_name: message})

            group_legal_document = attrs.get("group_legal_document", getattr(self.instance, "group_legal_document", None))
            representative_id_document = attrs.get("representative_id_document", getattr(self.instance, "representative_id_document", None))
            if not group_legal_document:
                raise serializers.ValidationError({"group_legal_document": "Legal document is required for group applicants."})
            if not representative_id_document:
                raise serializers.ValidationError({"representative_id_document": "Representative ID document is required."})

        return attrs

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        previous_status = instance.status
        instance.update_required_document_statuses()
        if instance.required_documents_complete():
            instance.status = StaffApplication.STATUS_UNDER_REVIEW
            if previous_status != StaffApplication.STATUS_APPROVED:
                instance.reviewed_at = None
                instance.reviewed_by = None
            if not instance.submitted_at:
                instance.submitted_at = timezone.now()
        else:
            instance.status = StaffApplication.STATUS_DRAFT

        if instance.status == StaffApplication.STATUS_UNDER_REVIEW:
            if instance.applicant_type == StaffApplication.TYPE_INDIVIDUAL:
                instance.individual_id_status = StaffApplication.DOC_PENDING
                instance.individual_id_reason = ""
            else:
                instance.group_legal_document_status = StaffApplication.DOC_PENDING
                instance.group_legal_document_reason = ""
                instance.representative_id_status = StaffApplication.DOC_PENDING
                instance.representative_id_reason = ""

        instance.save()
        return instance


class StaffApplicationReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = StaffApplication
        fields = [
            "status",
            "individual_id_status",
            "group_legal_document_status",
            "representative_id_status",
            "individual_id_reason",
            "group_legal_document_reason",
            "representative_id_reason",
            "admin_message",
        ]

    def validate(self, attrs):
        instance = self.instance
        applicant_type = instance.applicant_type
        status = attrs.get("status", instance.status)

        document_statuses = {
            "individual": attrs.get("individual_id_status", instance.individual_id_status),
            "group": attrs.get("group_legal_document_status", instance.group_legal_document_status),
            "representative": attrs.get("representative_id_status", instance.representative_id_status),
        }

        if applicant_type == StaffApplication.TYPE_INDIVIDUAL:
            if (
                status == StaffApplication.STATUS_APPROVED
                and document_statuses["individual"] == StaffApplication.DOC_REJECTED
            ):
                raise serializers.ValidationError({"individual_id_status": "The individual ID document must be approved before approving the application."})
        else:
            if status == StaffApplication.STATUS_APPROVED:
                if document_statuses["group"] == StaffApplication.DOC_REJECTED:
                    raise serializers.ValidationError({"group_legal_document_status": "The legal document must be approved before approving the application."})
                if document_statuses["representative"] == StaffApplication.DOC_REJECTED:
                    raise serializers.ValidationError({"representative_id_status": "The representative ID document must be approved before approving the application."})

        return attrs

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if instance.status == StaffApplication.STATUS_APPROVED:
            if instance.applicant_type == StaffApplication.TYPE_INDIVIDUAL:
                instance.individual_id_status = StaffApplication.DOC_APPROVED
                instance.individual_id_reason = ""
            else:
                instance.group_legal_document_status = StaffApplication.DOC_APPROVED
                instance.group_legal_document_reason = ""
                instance.representative_id_status = StaffApplication.DOC_APPROVED
                instance.representative_id_reason = ""

        if instance.status != StaffApplication.STATUS_APPROVED:
            rejected_docs = [
                instance.individual_id_status == StaffApplication.DOC_REJECTED,
                instance.group_legal_document_status == StaffApplication.DOC_REJECTED,
                instance.representative_id_status == StaffApplication.DOC_REJECTED,
            ]
            if any(rejected_docs) and instance.status != StaffApplication.STATUS_REJECTED:
                instance.status = StaffApplication.STATUS_CHANGES_REQUESTED

        instance.reviewed_at = timezone.now()
        instance.save()
        return instance
