from django.contrib import admin
from .models import Donation


@admin.register(Donation)
class DonationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "project",
        "donor_name",
        "donor_email",
        "amount",
        "payment_method",
        "status",
        "is_anonymous",
        "donor",
        "donated_at",
    )
    list_filter = (
        "status",
        "payment_method",
        "is_anonymous",
        "donated_at",
        "project",
    )
    search_fields = (
        "donor_name",
        "donor_email",
        "transaction_reference",
        "project__title",
        "donor__username",
    )
    ordering = ("-donated_at",)