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
    settings_url = _build_link(getattr(settings, "FRONTEND_STAFF_SETTINGS_URL", ""))
    settings_line = f"Manage your application here: {settings_url}\n\n" if settings_url else ""
    message = (
        f"Hello {user.first_name or user.username or 'Applicant'},\n\n"
        "Your staff account has been created.\n"
        "Before you can create public-facing projects, you need to complete and submit your verification documents.\n\n"
        f"{settings_line}"
        "What happens next:\n"
        "1. Complete your staff verification details and upload the required documents.\n"
        "2. An admin reviews your submission.\n"
        "3. You receive an email if documents need changes or once the application is approved.\n\n"
        "You can already sign in, but project creation stays locked until approval."
    )
    return _send_user_email(
        subject="We received your staff application",
        message=message,
        recipient=user.email,
    )


def send_staff_application_submitted_email(application):
    user = application.user
    message = (
        f"Hello {user.first_name or user.username or 'Applicant'},\n\n"
        "Your staff verification documents have been submitted for review.\n"
        "An administrator will review the documents and contact you if any further changes are required.\n\n"
        "You will receive another email once the review is complete."
    )
    return _send_user_email(
        subject="Your staff documents are under review",
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


def send_staff_application_review_email(application):
    user = application.user
    settings_url = _build_link(getattr(settings, "FRONTEND_STAFF_SETTINGS_URL", ""))
    settings_line = f"\nUpdate your submission here: {settings_url}\n" if settings_url else "\n"
    admin_message = application.admin_message.strip() if application.admin_message else ""
    admin_note_block = f"\nAdmin message:\n{admin_message}\n" if admin_message else ""

    if application.status == application.STATUS_APPROVED:
        subject = "Your staff verification has been approved"
        message = (
            f"Hello {user.first_name or user.username or 'Applicant'},\n\n"
            "Your staff verification has been approved.\n"
            "You can now create and manage projects in the staff portal."
            f"{admin_note_block}"
        )
    elif application.status == application.STATUS_REJECTED:
        subject = "Your staff verification was not approved"
        message = (
            f"Hello {user.first_name or user.username or 'Applicant'},\n\n"
            "Your staff verification application was rejected."
            f"{admin_note_block}"
            f"{settings_line}"
        )
    else:
        subject = "Changes are needed on your staff verification"
        message = (
            f"Hello {user.first_name or user.username or 'Applicant'},\n\n"
            "An admin reviewed your staff verification and requested some changes before approval."
            f"{admin_note_block}"
            "\nPlease review the document notes in your staff settings and upload updated files."
            f"{settings_line}"
        )

    return _send_user_email(
        subject=subject,
        message=message,
        recipient=user.email,
    )
