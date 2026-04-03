from django.contrib import admin
from .models import (
    Project,
    Partner,
    ProjectUpdate,
    ProjectUpdateImage,
    ProjectInterest,
    ProjectReport,
    ProjectCashout,
)


@admin.register(Partner)
class PartnerAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "website", "is_active", "created_at")
    list_filter = ("is_active", "created_at")
    search_fields = ("name", "website")
    ordering = ("name",)


class ProjectUpdateImageInline(admin.TabularInline):
    model = ProjectUpdateImage
    extra = 1


@admin.register(ProjectUpdate)
class ProjectUpdateAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "project", "update_type", "cashout_amount", "created_by", "created_at")
    list_filter = ("project", "update_type", "created_at")
    search_fields = ("title", "description", "project__title")
    ordering = ("-created_at",)
    inlines = [ProjectUpdateImageInline]


@admin.register(ProjectUpdateImage)
class ProjectUpdateImageAdmin(admin.ModelAdmin):
    list_display = ("id", "project_update", "caption", "created_at")
    search_fields = ("project_update__title", "caption")
    ordering = ("-created_at",)


@admin.register(ProjectInterest)
class ProjectInterestAdmin(admin.ModelAdmin):
    list_display = ("id", "project", "email", "user", "is_active", "created_at")
    list_filter = ("is_active", "created_at", "project")
    search_fields = ("email", "name", "project__title", "user__username")
    ordering = ("-created_at",)


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "created_by",
        "status",
        "moderation_status",
        "funding_status",
        "budget",
        "target_amount",
        "start_date",
        "end_date",
        "location",
        "created_at",
    )
    list_filter = ("status", "moderation_status", "funding_status", "created_by", "start_date", "end_date", "created_at")
    search_fields = ("title", "description", "location", "created_by__username", "created_by__email")
    filter_horizontal = ("partners",)
    ordering = ("-created_at",)
    autocomplete_fields = ("created_by",)
    readonly_fields = ("created_at", "updated_at")
    fields = (
        "title",
        "description",
        "status",
        "moderation_status",
        "funding_status",
        "moderation_note",
        "moderation_reviewed_by",
        "moderation_reviewed_at",
        "budget",
        "target_amount",
        "start_date",
        "end_date",
        "location",
        "feature_image",
        "partners",
        "created_by",
        "created_at",
        "updated_at",
    )


@admin.register(ProjectReport)
class ProjectReportAdmin(admin.ModelAdmin):
    list_display = ("id", "project", "reported_by", "reason_type", "status", "created_at")
    list_filter = ("reason_type", "status", "created_at")
    search_fields = ("project__title", "reported_by__username", "reported_by__email", "claim_text")
    ordering = ("-created_at",)


@admin.register(ProjectCashout)
class ProjectCashoutAdmin(admin.ModelAdmin):
    list_display = ("id", "project", "requested_by", "amount", "remaining_balance", "created_at")
    list_filter = ("created_at", "project")
    search_fields = ("project__title", "requested_by__username", "requested_by__email", "purpose")
    ordering = ("-created_at",)
