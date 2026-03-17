from django.db import models
from projects.models import Project


class Beneficiary(models.Model):
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="beneficiaries"
    )
    name = models.CharField(max_length=255)
    description = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "beneficiaries"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


class BeneficiaryImage(models.Model):
    beneficiary = models.ForeignKey(
        Beneficiary,
        on_delete=models.CASCADE,
        related_name="images"
    )
    image = models.ImageField(upload_to="beneficiaries/images/")
    caption = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "beneficiary_images"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Image for {self.beneficiary.name}"