from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0004_user_donor_claim_token_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="StaffApplication",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("applicant_type", models.CharField(choices=[("individual", "Individual"), ("group", "Group / Organization")], default="individual", max_length=20)),
                ("status", models.CharField(choices=[("draft", "Draft"), ("under_review", "Under Review"), ("changes_requested", "Changes Requested"), ("approved", "Approved"), ("rejected", "Rejected")], default="draft", max_length=30)),
                ("mission_summary", models.TextField(blank=True)),
                ("location", models.CharField(blank=True, max_length=255)),
                ("organization_name", models.CharField(blank=True, max_length=255)),
                ("registration_number", models.CharField(blank=True, max_length=120)),
                ("representative_name", models.CharField(blank=True, max_length=255)),
                ("representative_id_number", models.CharField(blank=True, max_length=120)),
                ("individual_id_number", models.CharField(blank=True, max_length=120)),
                ("individual_id_document", models.FileField(blank=True, null=True, upload_to="users/staff_applications/individual_ids/")),
                ("group_legal_document", models.FileField(blank=True, null=True, upload_to="users/staff_applications/group_documents/")),
                ("representative_id_document", models.FileField(blank=True, null=True, upload_to="users/staff_applications/representative_ids/")),
                ("individual_id_status", models.CharField(choices=[("not_required", "Not Required"), ("pending", "Pending Review"), ("approved", "Approved"), ("rejected", "Rejected")], default="not_required", max_length=20)),
                ("group_legal_document_status", models.CharField(choices=[("not_required", "Not Required"), ("pending", "Pending Review"), ("approved", "Approved"), ("rejected", "Rejected")], default="not_required", max_length=20)),
                ("representative_id_status", models.CharField(choices=[("not_required", "Not Required"), ("pending", "Pending Review"), ("approved", "Approved"), ("rejected", "Rejected")], default="not_required", max_length=20)),
                ("individual_id_reason", models.CharField(blank=True, choices=[("missing_document", "Missing required document"), ("unclear_scan", "Document is unclear or unreadable"), ("expired_document", "Document appears expired"), ("information_mismatch", "Details do not match the application"), ("unauthorized_representative", "Representative proof is insufficient"), ("other", "Other")], max_length=40)),
                ("group_legal_document_reason", models.CharField(blank=True, choices=[("missing_document", "Missing required document"), ("unclear_scan", "Document is unclear or unreadable"), ("expired_document", "Document appears expired"), ("information_mismatch", "Details do not match the application"), ("unauthorized_representative", "Representative proof is insufficient"), ("other", "Other")], max_length=40)),
                ("representative_id_reason", models.CharField(blank=True, choices=[("missing_document", "Missing required document"), ("unclear_scan", "Document is unclear or unreadable"), ("expired_document", "Document appears expired"), ("information_mismatch", "Details do not match the application"), ("unauthorized_representative", "Representative proof is insufficient"), ("other", "Other")], max_length=40)),
                ("admin_message", models.TextField(blank=True)),
                ("submitted_at", models.DateTimeField(blank=True, null=True)),
                ("reviewed_at", models.DateTimeField(blank=True, null=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("reviewed_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="reviewed_staff_applications", to=settings.AUTH_USER_MODEL)),
                ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="staff_application", to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
