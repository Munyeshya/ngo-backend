from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import User


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
            user.is_active = False
            user.is_verified = False
        user.set_password(password)
        user.save()
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "phone_number",
            "profile_image",
            "role",
            "is_verified",
            "is_active",
            "date_joined",
        ]


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["username"] = user.username
        token["email"] = user.email
        token["role"] = user.role
        return token

    def validate(self, attrs):
        username = attrs.get(self.username_field)
        user = User.objects.filter(**{self.username_field: username}).first()
        if user and user.role == User.ROLE_STAFF and not user.is_active:
            raise AuthenticationFailed("Your staff account is pending admin approval.")

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
