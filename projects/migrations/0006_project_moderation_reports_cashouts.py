from decimal import Decimal

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("projects", "0005_project_project_type"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="project",
            name="funding_status",
            field=models.CharField(
                choices=[("open", "Open"), ("frozen", "Frozen")],
                default="open",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="project",
            name="moderation_note",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="project",
            name="moderation_reviewed_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="project",
            name="moderation_reviewed_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="reviewed_projects",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="project",
            name="moderation_status",
            field=models.CharField(
                choices=[
                    ("clear", "Clear"),
                    ("under_review", "Under Review"),
                    ("taken_down", "Taken Down"),
                ],
                default="clear",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="projectupdate",
            name="cashout_amount",
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True),
        ),
        migrations.AddField(
            model_name="projectupdate",
            name="remaining_balance",
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True),
        ),
        migrations.AddField(
            model_name="projectupdate",
            name="update_type",
            field=models.CharField(
                choices=[("general", "General"), ("cashout", "Cashout Activity")],
                default="general",
                max_length=20,
            ),
        ),
        migrations.CreateModel(
            name="ProjectCashout",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("amount", models.DecimalField(decimal_places=2, max_digits=12)),
                ("purpose", models.TextField()),
                ("remaining_balance", models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=12)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("project", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="cashouts", to="projects.project")),
                ("requested_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="project_cashouts", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "db_table": "project_cashouts",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="ProjectReport",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("reason_type", models.CharField(choices=[("misleading_information", "Misleading Information"), ("misuse_of_funds", "Misuse of Funds"), ("inappropriate_content", "Inappropriate Content"), ("fake_project", "Fake Project"), ("duplicate_project", "Duplicate Project"), ("other", "Other")], max_length=40)),
                ("claim_text", models.TextField()),
                ("status", models.CharField(choices=[("open", "Open"), ("reviewed", "Reviewed"), ("dismissed", "Dismissed")], default="open", max_length=20)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("project", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="reports", to="projects.project")),
                ("reported_by", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="project_reports", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "db_table": "project_reports",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddConstraint(
            model_name="projectreport",
            constraint=models.UniqueConstraint(fields=("project", "reported_by", "reason_type"), name="unique_project_report_reason_per_user"),
        ),
    ]
