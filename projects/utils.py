from decimal import Decimal

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.db.models import Sum

from donations.models import Donation
from .email_templates import build_project_update_email_html
from .models import ProjectInterest


def get_project_funding_stats(project):
    total_donated = project.donations.filter(status=Donation.STATUS_COMPLETED).aggregate(
        total=Sum("amount")
    )["total"] or Decimal("0.00")

    target_amount = project.target_amount or Decimal("0.00")

    if target_amount > 0:
        funding_percentage = round((total_donated / target_amount) * 100, 2)
    else:
        funding_percentage = Decimal("0.00")

    remaining_amount = target_amount - total_donated
    if remaining_amount < 0:
        remaining_amount = Decimal("0.00")

    exceeded_amount = total_donated - target_amount
    if exceeded_amount < 0:
        exceeded_amount = Decimal("0.00")

    is_goal_reached = target_amount > 0 and total_donated >= target_amount

    return {
        "total_donated": total_donated,
        "target_amount": target_amount,
        "funding_percentage": funding_percentage,
        "remaining_amount": remaining_amount,
        "exceeded_amount": exceeded_amount,
        "is_goal_reached": is_goal_reached,
    }


def get_project_notification_emails(project):
    donation_emails = list(
        project.donations.filter(
            status=Donation.STATUS_COMPLETED,
            is_anonymous=False,
        )
        .exclude(donor_email__isnull=True)
        .exclude(donor_email__exact="")
        .values_list("donor_email", flat=True)
        .distinct()
    )

    interest_emails = list(
        ProjectInterest.objects.filter(project=project, is_active=True)
        .exclude(email__isnull=True)
        .exclude(email__exact="")
        .values_list("email", flat=True)
        .distinct()
    )

    return sorted(set(donation_emails + interest_emails))


def send_project_update_notifications(project_update):
    project = project_update.project
    recipients = get_project_notification_emails(project)

    if not recipients:
        return 0

    stats = get_project_funding_stats(project)

    subject = f"Update: {project.title} - {project_update.title}"

    html_content = build_project_update_email_html(
        project_title=project.title,
        update_title=project_update.title,
        update_description=project_update.description,
        total_donated=stats["total_donated"],
        target_amount=stats["target_amount"],
        funding_percentage=stats["funding_percentage"],
        remaining_amount=stats["remaining_amount"],
        exceeded_amount=stats["exceeded_amount"],
        is_goal_reached=stats["is_goal_reached"],
    )

    text_content = (
        f"Project Update\n\n"
        f"Project: {project.title}\n"
        f"Update: {project_update.title}\n\n"
        f"{project_update.description}\n\n"
        f"Total donated: {stats['total_donated']}\n"
        f"Target amount: {stats['target_amount']}\n"
        f"Funding percentage: {stats['funding_percentage']}%\n"
        f"Remaining amount: {stats['remaining_amount']}\n"
        f"Exceeded amount: {stats['exceeded_amount']}\n"
    )

    email = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=recipients,
    )
    email.attach_alternative(html_content, "text/html")
    return email.send(fail_silently=False)
