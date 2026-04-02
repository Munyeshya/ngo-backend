from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    ROLE_ADMIN = "admin"
    ROLE_STAFF = "staff"
    ROLE_DONOR = "donor"

    ROLE_CHOICES = [
        (ROLE_ADMIN, "Admin"),
        (ROLE_STAFF, "Staff"),
        (ROLE_DONOR, "Donor"),
    ]

    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    profile_image = models.ImageField(upload_to="users/profiles/", blank=True, null=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_STAFF)
    is_verified = models.BooleanField(default=False)
    donor_claim_token = models.CharField(max_length=128, blank=True, null=True, unique=True)
    donor_claim_token_expires_at = models.DateTimeField(blank=True, null=True)

    REQUIRED_FIELDS = ["email"]

    def donor_claim_token_is_valid(self, token):
        return bool(
            self.donor_claim_token
            and self.donor_claim_token == token
            and self.donor_claim_token_expires_at
            and self.donor_claim_token_expires_at >= timezone.now()
        )

    def __str__(self):
        return f"{self.username} ({self.role})"
