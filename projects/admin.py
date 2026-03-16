from django.contrib import admin
from .models import Project, Partner


@admin.register(Partner)
class PartnerAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "website", "is_active", "created_at")
    list_filter = ("is_active", "created_at")
    search_fields = ("name", "website")
    ordering = ("name",)


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "status",
        "budget",
        "start_date",
        "end_date",
        "location",
        "created_by",
        "created_at",
    )
    list_filter = ("status", "start_date", "end_date", "created_at")
    search_fields = ("title", "description", "location")
    filter_horizontal = ("partners",)
    ordering = ("-created_at",)