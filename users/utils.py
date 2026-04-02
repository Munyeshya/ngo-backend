import secrets
from datetime import timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone


DONOR_CLAIM_TOKEN_LIFETIME = timedelta(hours=1)


def issue_donor_claim_token(user):
    token = secrets.token_urlsafe(32)
    user.donor_claim_token = token
    user.donor_claim_token_expires_at = timezone.now() + DONOR_CLAIM_TOKEN_LIFETIME
    user.save(update_fields=["donor_claim_token", "donor_claim_token_expires_at"])
    return token


def clear_donor_claim_token(user):
    user.donor_claim_token = None
    user.donor_claim_token_expires_at = None
    user.save(update_fields=["donor_claim_token", "donor_claim_token_expires_at"])


def send_donor_claim_email(user, token):
    frontend_claim_url = getattr(settings, "FRONTEND_DONOR_CLAIM_URL", "").strip()
    if frontend_claim_url:
        claim_url = f"{frontend_claim_url}?token={token}"
    else:
        claim_url = token

    subject = "Verify your donor account claim"
    message = (
        "You requested to claim your donor account.\n\n"
        f"Use this verification token or link to continue:\n{claim_url}\n\n"
        "This token expires in 1 hour. If you did not request this, you can ignore this email."
    )

    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )
