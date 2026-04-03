from django.conf import settings
from django.db import models


class Partner(models.Model):
    name = models.CharField(max_length=255, unique=True)
    logo = models.ImageField(upload_to="partners/logos/", blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "partners"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Project(models.Model):
    STATUS_PLANNING = "planning"
    STATUS_ACTIVE = "active"
    STATUS_COMPLETED = "completed"
    STATUS_ON_HOLD = "on_hold"
    TYPE_EDUCATION = "education"
    TYPE_HEALTH = "health"
    TYPE_LIVELIHOOD = "livelihood"
    TYPE_WOMEN_EMPOWERMENT = "women_empowerment"
    TYPE_YOUTH_EMPOWERMENT = "youth_empowerment"
    TYPE_COMMUNITY_DEVELOPMENT = "community_development"
    TYPE_ENVIRONMENT = "environment"
    TYPE_EMERGENCY_RELIEF = "emergency_relief"
    TYPE_OTHER = "other"

    STATUS_CHOICES = [
        (STATUS_PLANNING, "Planning"),
        (STATUS_ACTIVE, "Active"),
        (STATUS_COMPLETED, "Completed"),
        (STATUS_ON_HOLD, "On Hold"),
    ]
    PROJECT_TYPE_CHOICES = [
        (TYPE_EDUCATION, "Education"),
        (TYPE_HEALTH, "Health"),
        (TYPE_LIVELIHOOD, "Livelihood"),
        (TYPE_WOMEN_EMPOWERMENT, "Women Empowerment"),
        (TYPE_YOUTH_EMPOWERMENT, "Youth Empowerment"),
        (TYPE_COMMUNITY_DEVELOPMENT, "Community Development"),
        (TYPE_ENVIRONMENT, "Environment"),
        (TYPE_EMERGENCY_RELIEF, "Emergency Relief"),
        (TYPE_OTHER, "Other"),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField()
    project_type = models.CharField(
        max_length=40,
        choices=PROJECT_TYPE_CHOICES,
        default=TYPE_OTHER,
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PLANNING)
    budget = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    target_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    feature_image = models.ImageField(upload_to="projects/features/", blank=True, null=True)
    partners = models.ManyToManyField(Partner, blank=True, related_name="projects")

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_projects"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "projects"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

class ProjectUpdate(models.Model):
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="updates"
    )
    title = models.CharField(max_length=255)
    description = models.TextField()
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="project_updates"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "project_updates"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.project.title} - {self.title}"


class ProjectUpdateImage(models.Model):
    project_update = models.ForeignKey(
        ProjectUpdate,
        on_delete=models.CASCADE,
        related_name="images"
    )
    image = models.ImageField(upload_to="projects/updates/")
    caption = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "project_update_images"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Image for {self.project_update.title}"

class ProjectInterest(models.Model):
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="interests"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="project_interests"
    )
    name = models.CharField(max_length=255, blank=True, null=True)
    email = models.EmailField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "project_interests"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["project", "email"],
                name="unique_project_interest_email"
            )
        ]

    def __str__(self):
        return f"{self.email} interested in {self.project.title}"
