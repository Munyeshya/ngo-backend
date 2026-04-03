from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, StaffApplication


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    model = User

    list_display = ("id", "username", "email", "role", "staff_application_status", "is_verified", "is_staff", "is_active")
    list_filter = ("role", "is_verified", "is_staff", "is_active")
    search_fields = ("username", "email", "phone_number")
    ordering = ("id",)

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name", "email", "phone_number", "profile_image")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
        ("Additional Info", {"fields": ("role", "is_verified")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("username", "email", "phone_number", "profile_image", "role", "is_verified", "password1", "password2"),
        }),
    )

    def staff_application_status(self, obj):
        application = getattr(obj, "staff_application", None)
        return application.status if application else "-"

    staff_application_status.short_description = "Staff Application"


@admin.register(StaffApplication)
class StaffApplicationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "applicant_type",
        "status",
        "individual_id_status",
        "group_legal_document_status",
        "representative_id_status",
        "reviewed_by",
        "updated_at",
    )
    list_filter = (
        "applicant_type",
        "status",
        "individual_id_status",
        "group_legal_document_status",
        "representative_id_status",
    )
    search_fields = (
        "user__username",
        "user__email",
        "organization_name",
        "representative_name",
        "individual_id_number",
        "registration_number",
    )
    autocomplete_fields = ("user", "reviewed_by")
    readonly_fields = ("submitted_at", "reviewed_at", "created_at", "updated_at")
