from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_ADMIN = "admin"
    ROLE_STAFF = "staff"
    ROLE_DONOR = "donor"
    ROLE_VOLUNTEER = "volunteer"

    ROLE_CHOICES = [
        (ROLE_ADMIN, "Admin"),
        (ROLE_STAFF, "Staff"),
        (ROLE_DONOR, "Donor"),
        (ROLE_VOLUNTEER, "Volunteer"),
    ]

    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_STAFF)
    profile_image = models.ImageField(upload_to="users/profiles/", blank=True, null=True)
    is_verified = models.BooleanField(default=False)

    REQUIRED_FIELDS = ["email"]

    def __str__(self):
        return f"{self.username} ({self.role})"