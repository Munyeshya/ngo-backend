import secrets
from datetime import timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone


DONOR_CLAIM_TOKEN_LIFETIME = timedelta(hours=1)


def _build_link(base_url, token=None):
    url = (base_url or "").strip()
    if not url:
        return ""
    if token:
        separator = "&" if "?" in url else "?"
        return f"{url}{separator}token={token}"
    return url


def _send_user_email(subject, message, recipient):
    if not recipient:
        return 0

    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[recipient],
        fail_silently=False,
    )
    return 1


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
    claim_url = _build_link(getattr(settings, "FRONTEND_DONOR_CLAIM_URL", ""), token=token)
    token_or_link = claim_url or token

    subject = "Verify your donor account claim"
    message = (
        f"Hello {user.first_name or user.username or 'Donor'},\n\n"
        "We received a request to claim your donor account.\n\n"
        "Use the link or token below to finish creating your password and access your donation history:\n"
        f"{token_or_link}\n\n"
        "This verification token expires in 1 hour.\n"
        "If you did not request this, you can safely ignore this email."
    )

    return _send_user_email(
        subject=subject,
        message=message,
        recipient=user.email,
    )


def send_donor_claim_success_email(user):
    login_url = _build_link(getattr(settings, "FRONTEND_LOGIN_URL", ""))
    login_line = f"\nLogin here: {login_url}\n" if login_url else "\n"
    message = (
        f"Hello {user.first_name or user.username or 'Donor'},\n\n"
        "Your donor account has been verified successfully.\n"
        "You can now log in and view your donation history and project interests."
        f"{login_line}\n"
        "Thank you for supporting our work."
    )
    return _send_user_email(
        subject="Your donor account is ready",
        message=message,
        recipient=user.email,
    )


def send_staff_application_received_email(user):
    message = (
        f"Hello {user.first_name or user.username or 'Applicant'},\n\n"
        "Your staff account application has been received.\n"
        "An administrator will review your request before your account can access project management features.\n\n"
        "What happens next:\n"
        "1. An admin reviews your staff request.\n"
        "2. You receive an email when the account is approved or updated.\n"
        "3. After approval, you can log in and create projects for donations.\n\n"
        "You do not need to take any further action right now."
    )
    return _send_user_email(
        subject="We received your staff application",
        message=message,
        recipient=user.email,
    )


def send_staff_status_email(user):
    login_url = _build_link(getattr(settings, "FRONTEND_LOGIN_URL", ""))
    guide_url = _build_link(getattr(settings, "FRONTEND_STAFF_GUIDE_URL", ""))
    login_line = f"Login here: {login_url}\n" if login_url else ""
    guide_line = f"Getting started guide: {guide_url}\n" if guide_url else ""

    if user.is_active:
        subject = "Your staff account has been approved"
        message = (
            f"Hello {user.first_name or user.username or 'Staff Member'},\n\n"
            "Your staff account has been approved and is now active.\n"
            "You can now sign in and start creating and managing projects.\n\n"
            f"{login_line}"
            f"{guide_line}"
        )
    else:
        subject = "Update on your staff account"
        message = (
            f"Hello {user.first_name or user.username or 'Staff Member'},\n\n"
            "There has been an update to your staff account status.\n"
            "Your staff access is currently inactive. If you believe this is unexpected, please contact an administrator."
        )

    return _send_user_email(
        subject=subject,
        message=message,
        recipient=user.email,
    )
