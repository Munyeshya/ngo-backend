from django.conf import settings
from django.db import models
from django.db.models import Sum
from decimal import Decimal


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
    MODERATION_CLEAR = "clear"
    MODERATION_UNDER_REVIEW = "under_review"
    MODERATION_TAKEN_DOWN = "taken_down"
    MODERATION_STATUS_CHOICES = [
        (MODERATION_CLEAR, "Clear"),
        (MODERATION_UNDER_REVIEW, "Under Review"),
        (MODERATION_TAKEN_DOWN, "Taken Down"),
    ]
    FUNDING_OPEN = "open"
    FUNDING_FROZEN = "frozen"
    FUNDING_STATUS_CHOICES = [
        (FUNDING_OPEN, "Open"),
        (FUNDING_FROZEN, "Frozen"),
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
    moderation_status = models.CharField(
        max_length=20,
        choices=MODERATION_STATUS_CHOICES,
        default=MODERATION_CLEAR,
    )
    funding_status = models.CharField(
        max_length=20,
        choices=FUNDING_STATUS_CHOICES,
        default=FUNDING_OPEN,
    )
    moderation_note = models.TextField(blank=True, null=True)
    moderation_reviewed_at = models.DateTimeField(blank=True, null=True)
    moderation_reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_projects",
    )
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

    def total_completed_donations(self):
        total = self.donations.filter(status="completed").aggregate(total=Sum("amount"))["total"]
        return total or Decimal("0.00")

    def total_cashouts(self):
        total = self.cashouts.aggregate(total=Sum("amount"))["total"]
        return total or Decimal("0.00")

    def available_balance(self):
        return self.total_completed_donations() - self.total_cashouts()

    def can_accept_donations(self):
        return (
            self.moderation_status == self.MODERATION_CLEAR
            and self.funding_status == self.FUNDING_OPEN
        )

    def can_cash_out(self):
        return (
            self.moderation_status == self.MODERATION_CLEAR
            and self.funding_status == self.FUNDING_OPEN
        )

class ProjectUpdate(models.Model):
    TYPE_GENERAL = "general"
    TYPE_CASHOUT = "cashout"
    UPDATE_TYPE_CHOICES = [
        (TYPE_GENERAL, "General"),
        (TYPE_CASHOUT, "Cashout Activity"),
    ]
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="updates"
    )
    update_type = models.CharField(
        max_length=20,
        choices=UPDATE_TYPE_CHOICES,
        default=TYPE_GENERAL,
    )
    title = models.CharField(max_length=255)
    description = models.TextField()
    cashout_amount = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    remaining_balance = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
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


class ProjectReport(models.Model):
    STATUS_OPEN = "open"
    STATUS_REVIEWED = "reviewed"
    STATUS_DISMISSED = "dismissed"
    STATUS_CHOICES = [
        (STATUS_OPEN, "Open"),
        (STATUS_REVIEWED, "Reviewed"),
        (STATUS_DISMISSED, "Dismissed"),
    ]

    REASON_MISLEADING = "misleading_information"
    REASON_FUNDS = "misuse_of_funds"
    REASON_INAPPROPRIATE = "inappropriate_content"
    REASON_FAKE = "fake_project"
    REASON_DUPLICATE = "duplicate_project"
    REASON_OTHER = "other"
    REASON_CHOICES = [
        (REASON_MISLEADING, "Misleading Information"),
        (REASON_FUNDS, "Misuse of Funds"),
        (REASON_INAPPROPRIATE, "Inappropriate Content"),
        (REASON_FAKE, "Fake Project"),
        (REASON_DUPLICATE, "Duplicate Project"),
        (REASON_OTHER, "Other"),
    ]

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="reports",
    )
    reported_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="project_reports",
    )
    reason_type = models.CharField(max_length=40, choices=REASON_CHOICES)
    claim_text = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_OPEN)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "project_reports"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["project", "reported_by", "reason_type"],
                name="unique_project_report_reason_per_user",
            )
        ]

    def __str__(self):
        return f"Report on {self.project.title} by {self.reported_by}"


class ProjectCashout(models.Model):
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="cashouts",
    )
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="project_cashouts",
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    purpose = models.TextField()
    remaining_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "project_cashouts"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Cashout {self.amount} for {self.project.title}"
