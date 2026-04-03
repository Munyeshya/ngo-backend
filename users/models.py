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


class StaffApplication(models.Model):
    TYPE_INDIVIDUAL = "individual"
    TYPE_GROUP = "group"
    APPLICANT_TYPE_CHOICES = [
        (TYPE_INDIVIDUAL, "Individual"),
        (TYPE_GROUP, "Group / Organization"),
    ]

    STATUS_DRAFT = "draft"
    STATUS_UNDER_REVIEW = "under_review"
    STATUS_CHANGES_REQUESTED = "changes_requested"
    STATUS_APPROVED = "approved"
    STATUS_REJECTED = "rejected"
    STATUS_CHOICES = [
        (STATUS_DRAFT, "Draft"),
        (STATUS_UNDER_REVIEW, "Under Review"),
        (STATUS_CHANGES_REQUESTED, "Changes Requested"),
        (STATUS_APPROVED, "Approved"),
        (STATUS_REJECTED, "Rejected"),
    ]

    DOC_NOT_REQUIRED = "not_required"
    DOC_PENDING = "pending"
    DOC_APPROVED = "approved"
    DOC_REJECTED = "rejected"
    DOCUMENT_STATUS_CHOICES = [
        (DOC_NOT_REQUIRED, "Not Required"),
        (DOC_PENDING, "Pending Review"),
        (DOC_APPROVED, "Approved"),
        (DOC_REJECTED, "Rejected"),
    ]

    REASON_MISSING = "missing_document"
    REASON_UNCLEAR = "unclear_scan"
    REASON_EXPIRED = "expired_document"
    REASON_MISMATCH = "information_mismatch"
    REASON_UNAUTHORIZED = "unauthorized_representative"
    REASON_OTHER = "other"
    REVIEW_REASON_CHOICES = [
        (REASON_MISSING, "Missing required document"),
        (REASON_UNCLEAR, "Document is unclear or unreadable"),
        (REASON_EXPIRED, "Document appears expired"),
        (REASON_MISMATCH, "Details do not match the application"),
        (REASON_UNAUTHORIZED, "Representative proof is insufficient"),
        (REASON_OTHER, "Other"),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="staff_application",
    )
    applicant_type = models.CharField(
        max_length=20,
        choices=APPLICANT_TYPE_CHOICES,
        default=TYPE_INDIVIDUAL,
    )
    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default=STATUS_DRAFT,
    )

    mission_summary = models.TextField(blank=True)
    location = models.CharField(max_length=255, blank=True)
    organization_name = models.CharField(max_length=255, blank=True)
    registration_number = models.CharField(max_length=120, blank=True)
    representative_name = models.CharField(max_length=255, blank=True)
    representative_id_number = models.CharField(max_length=120, blank=True)
    individual_id_number = models.CharField(max_length=120, blank=True)

    individual_id_document = models.FileField(
        upload_to="users/staff_applications/individual_ids/",
        blank=True,
        null=True,
    )
    group_legal_document = models.FileField(
        upload_to="users/staff_applications/group_documents/",
        blank=True,
        null=True,
    )
    representative_id_document = models.FileField(
        upload_to="users/staff_applications/representative_ids/",
        blank=True,
        null=True,
    )

    individual_id_status = models.CharField(
        max_length=20,
        choices=DOCUMENT_STATUS_CHOICES,
        default=DOC_NOT_REQUIRED,
    )
    group_legal_document_status = models.CharField(
        max_length=20,
        choices=DOCUMENT_STATUS_CHOICES,
        default=DOC_NOT_REQUIRED,
    )
    representative_id_status = models.CharField(
        max_length=20,
        choices=DOCUMENT_STATUS_CHOICES,
        default=DOC_NOT_REQUIRED,
    )

    individual_id_reason = models.CharField(
        max_length=40,
        choices=REVIEW_REASON_CHOICES,
        blank=True,
    )
    group_legal_document_reason = models.CharField(
        max_length=40,
        choices=REVIEW_REASON_CHOICES,
        blank=True,
    )
    representative_id_reason = models.CharField(
        max_length=40,
        choices=REVIEW_REASON_CHOICES,
        blank=True,
    )

    admin_message = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name="reviewed_staff_applications",
        blank=True,
        null=True,
    )
    submitted_at = models.DateTimeField(blank=True, null=True)
    reviewed_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def update_required_document_statuses(self):
        if self.applicant_type == self.TYPE_INDIVIDUAL:
            self.individual_id_status = self.individual_id_status or self.DOC_PENDING
            self.group_legal_document_status = self.DOC_NOT_REQUIRED
            self.group_legal_document_reason = ""
            self.representative_id_status = self.DOC_NOT_REQUIRED
            self.representative_id_reason = ""
        else:
            self.individual_id_status = self.DOC_NOT_REQUIRED
            self.individual_id_reason = ""
            self.group_legal_document_status = self.group_legal_document_status or self.DOC_PENDING
            self.representative_id_status = self.representative_id_status or self.DOC_PENDING

    def required_documents_complete(self):
        if self.applicant_type == self.TYPE_INDIVIDUAL:
            return bool(self.individual_id_number and self.individual_id_document)
        return bool(
            self.organization_name
            and self.registration_number
            and self.representative_name
            and self.representative_id_number
            and self.group_legal_document
            and self.representative_id_document
        )

    def can_create_projects(self):
        return self.status == self.STATUS_APPROVED

    def __str__(self):
        return f"Staff application for {self.user.username}"
