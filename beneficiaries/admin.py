from django.contrib import admin
from .models import Beneficiary, BeneficiaryImage


class BeneficiaryImageInline(admin.TabularInline):
    model = BeneficiaryImage
    extra = 1


@admin.register(Beneficiary)
class BeneficiaryAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "project", "is_active", "created_at")
    list_filter = ("is_active", "project", "created_at")
    search_fields = ("name", "description", "project__title")
    ordering = ("-created_at",)
    inlines = [BeneficiaryImageInline]


@admin.register(BeneficiaryImage)
class BeneficiaryImageAdmin(admin.ModelAdmin):
    list_display = ("id", "beneficiary", "caption", "created_at")
    search_fields = ("beneficiary__name", "caption")
    ordering = ("-created_at",)