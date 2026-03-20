from django.conf import settings
from django.db import models
from projects.models import Project


class Donation(models.Model):
    STATUS_PENDING = "pending"
    STATUS_COMPLETED = "completed"
    STATUS_FAILED = "failed"
    STATUS_CANCELLED = "cancelled"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_COMPLETED, "Completed"),
        (STATUS_FAILED, "Failed"),
        (STATUS_CANCELLED, "Cancelled"),
    ]

    PAYMENT_CASH = "cash"
    PAYMENT_BANK = "bank"
    PAYMENT_MOMO = "momo"
    PAYMENT_CARD = "card"

    PAYMENT_METHOD_CHOICES = [
        (PAYMENT_CASH, "Cash"),
        (PAYMENT_BANK, "Bank"),
        (PAYMENT_MOMO, "Mobile Money"),
        (PAYMENT_CARD, "Card"),
    ]

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="donations"
    )
    donor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="donations"
    )
    donor_name = models.CharField(max_length=255)
    donor_email = models.EmailField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    message = models.TextField(blank=True, null=True)
    is_anonymous = models.BooleanField(default=False)
    transaction_reference = models.CharField(max_length=255, blank=True, null=True, unique=True)
    donated_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "donations"
        ordering = ["-donated_at"]

    def __str__(self):
        return f"{self.donor_name} - {self.amount} to {self.project.title}"