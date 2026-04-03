from django.contrib import admin
from .models import (
    Project,
    Partner,
    ProjectUpdate,
    ProjectUpdateImage,
    ProjectInterest,
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
    list_display = ("id", "title", "project", "created_by", "created_at")
    list_filter = ("project", "created_at")
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
        "budget",
        "target_amount",
        "start_date",
        "end_date",
        "location",
        "created_at",
    )
    list_filter = ("status", "created_by", "start_date", "end_date", "created_at")
    search_fields = ("title", "description", "location", "created_by__username", "created_by__email")
    filter_horizontal = ("partners",)
    ordering = ("-created_at",)
    autocomplete_fields = ("created_by",)
    readonly_fields = ("created_at", "updated_at")
    fields = (
        "title",
        "description",
        "status",
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
