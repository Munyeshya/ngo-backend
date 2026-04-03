import random
from datetime import datetime, time, timedelta
from decimal import Decimal

from django.contrib.auth.hashers import make_password
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from faker import Faker

from beneficiaries.models import Beneficiary, BeneficiaryImage
from donations.models import Donation
from projects.models import (
    Partner,
    Project,
    ProjectCashout,
    ProjectInterest,
    ProjectReport,
    ProjectUpdate,
    ProjectUpdateImage,
)
from users.models import StaffApplication, User


fake = Faker()


SVG_COLORS = [
    ("#166534", "#F6F8F4"),
    ("#0F4D27", "#ECFDF3"),
    ("#1D4ED8", "#EFF6FF"),
    ("#9A3412", "#FFF7ED"),
    ("#7C3AED", "#F5F3FF"),
    ("#0F766E", "#F0FDFA"),
    ("#B91C1C", "#FEF2F2"),
    ("#854D0E", "#FEFCE8"),
]

PROJECT_TYPE_TOPICS = {
    Project.TYPE_EDUCATION: [
        "School readiness kits",
        "Community reading circles",
        "Digital learning access",
        "Girls in science coaching",
    ],
    Project.TYPE_HEALTH: [
        "Maternal health outreach",
        "Village nutrition support",
        "Mobile clinic services",
        "Mental wellness sessions",
    ],
    Project.TYPE_LIVELIHOOD: [
        "Small business coaching",
        "Savings group support",
        "Regenerative farming",
        "Vocational skills bootcamp",
    ],
    Project.TYPE_WOMEN_EMPOWERMENT: [
        "Women leadership network",
        "Safe enterprise circles",
        "Income resilience for mothers",
    ],
    Project.TYPE_YOUTH_EMPOWERMENT: [
        "Youth makerspace access",
        "Career pathway labs",
        "Apprenticeship readiness",
    ],
    Project.TYPE_COMMUNITY_DEVELOPMENT: [
        "Water point repair",
        "Disability inclusion hubs",
        "Child protection clubs",
        "Community sanitation upgrades",
    ],
    Project.TYPE_ENVIRONMENT: [
        "Tree restoration campaign",
        "Climate-smart villages",
        "Green school compounds",
    ],
    Project.TYPE_EMERGENCY_RELIEF: [
        "Emergency shelter response",
        "Rapid food relief",
        "Flood recovery support",
    ],
    Project.TYPE_OTHER: [
        "Community innovation pilots",
        "Local resilience support",
        "Inclusive services expansion",
    ],
}

REPORT_REASONS = [
    ProjectReport.REASON_MISLEADING,
    ProjectReport.REASON_FUNDS,
    ProjectReport.REASON_INAPPROPRIATE,
    ProjectReport.REASON_FAKE,
    ProjectReport.REASON_DUPLICATE,
    ProjectReport.REASON_OTHER,
]

PAYMENT_METHODS = [
    Donation.PAYMENT_MOMO,
    Donation.PAYMENT_BANK,
    Donation.PAYMENT_CARD,
    Donation.PAYMENT_CASH,
]


def svg_file(label, bg, fg):
    safe_label = str(label)[:22]
    content = f"""<svg xmlns="http://www.w3.org/2000/svg" width="960" height="640" viewBox="0 0 960 640">
<rect width="960" height="640" fill="{bg}"/>
<circle cx="150" cy="130" r="110" fill="{fg}" opacity="0.14"/>
<circle cx="860" cy="520" r="150" fill="{fg}" opacity="0.12"/>
<text x="80" y="330" fill="{fg}" font-size="48" font-family="Arial, sans-serif" font-weight="700">{safe_label}</text>
</svg>"""
    return ContentFile(content.encode("utf-8"))


def pdf_file(title):
    safe_title = str(title)[:40]
    pdf_bytes = f"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 300 200] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>
endobj
4 0 obj
<< /Length 71 >>
stream
BT
/F1 16 Tf
36 120 Td
({safe_title}) Tj
ET
endstream
endobj
5 0 obj
<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>
endobj
xref
0 6
0000000000 65535 f 
0000000010 00000 n 
0000000063 00000 n 
0000000122 00000 n 
0000000248 00000 n 
0000000368 00000 n 
trailer
<< /Size 6 /Root 1 0 R >>
startxref
438
%%EOF
""".encode("utf-8")
    return ContentFile(pdf_bytes)


class Command(BaseCommand):
    help = "Purge app data and reseed a diverse demo dataset with realistic dates and platform states."

    def add_arguments(self, parser):
        parser.add_argument("--seed", type=int, default=20260403, help="Random seed for repeatable demo data.")
        parser.add_argument("--donors", type=int, default=24, help="Number of donor accounts to create.")
        parser.add_argument("--staff", type=int, default=8, help="Number of staff accounts to create.")
        parser.add_argument("--partners", type=int, default=10, help="Number of partner records to create.")
        parser.add_argument("--projects", type=int, default=18, help="Number of projects to create.")

    def handle(self, *args, **options):
        seed = options["seed"]
        random.seed(seed)
        Faker.seed(seed)
        fake.seed_instance(seed)
        self.now = timezone.now()
        self.stdout.write(self.style.WARNING("Resetting demo data while preserving superusers..."))

        with transaction.atomic():
            self._purge_existing_data()
            superusers = list(User.objects.filter(is_superuser=True).order_by("id"))
            for admin in superusers:
                updates = []
                if admin.role != User.ROLE_ADMIN:
                    admin.role = User.ROLE_ADMIN
                    updates.append("role")
                if not admin.is_active:
                    admin.is_active = True
                    updates.append("is_active")
                if not admin.is_verified:
                    admin.is_verified = True
                    updates.append("is_verified")
                if updates:
                    admin.save(update_fields=updates)

            donors = self._create_donors(options["donors"])
            staff_pool = self._create_staff(options["staff"], superusers[0] if superusers else None)
            partners = self._create_partners(options["partners"])
            projects = self._create_projects(options["projects"], partners, staff_pool["approved"], superusers[0] if superusers else None)
            self._create_beneficiaries(projects)
            self._create_project_interests(projects, donors)
            self._create_donations(projects, donors)
            self._create_cashouts_and_updates(projects)
            self._create_reports(projects, donors, superusers[0] if superusers else None)

        self.stdout.write(self.style.SUCCESS("Demo data reset completed successfully."))
        self.stdout.write(self.style.SUCCESS("Suggested logins after reset:"))
        self.stdout.write("  - superuser accounts remain unchanged")
        self.stdout.write("  - donor password: DemoPass123!")
        self.stdout.write("  - staff password: DemoPass123!")

    def _purge_existing_data(self):
        ProjectReport.objects.all().delete()
        ProjectCashout.objects.all().delete()
        ProjectInterest.objects.all().delete()
        ProjectUpdateImage.objects.all().delete()
        ProjectUpdate.objects.all().delete()
        BeneficiaryImage.objects.all().delete()
        Beneficiary.objects.all().delete()
        Donation.objects.all().delete()
        Project.objects.all().delete()
        Partner.objects.all().delete()
        StaffApplication.objects.exclude(user__is_superuser=True).delete()
        User.objects.filter(is_superuser=False).delete()

    def _create_donors(self, count):
        donors = []
        claimable_count = max(4, count // 4)

        for index in range(count):
            first_name = fake.first_name()
            last_name = fake.last_name()
            username = fake.unique.user_name()[:150]
            email = fake.unique.email()
            donor = User.objects.create(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name,
                phone_number=fake.phone_number()[:20],
                role=User.ROLE_DONOR,
                is_active=True,
                is_verified=index % 5 != 0,
                password=make_password("DemoPass123!"),
            )
            if index < 6:
                bg, fg = random.choice(SVG_COLORS)
                donor.profile_image.save(
                    f"donor-profile-{donor.id}.svg",
                    svg_file(f"{first_name} {last_name}", bg, fg),
                    save=True,
                )
            donors.append(donor)

        for donor in random.sample(donors, k=min(claimable_count, len(donors))):
            donor.set_unusable_password()
            donor.donor_claim_token = fake.uuid4()
            donor.donor_claim_token_expires_at = self.now + timedelta(hours=random.randint(2, 48))
            donor.is_verified = False
            donor.save(update_fields=["password", "donor_claim_token", "donor_claim_token_expires_at", "is_verified"])

        return donors

    def _create_staff(self, count, reviewer):
        approved_target = max(4, count // 2)
        remaining = max(0, count - approved_target)
        under_review_target = max(1, remaining // 2)
        changes_target = 1 if remaining > 1 else 0
        rejected_target = 1 if remaining > 2 else 0
        draft_target = max(0, remaining - under_review_target - changes_target - rejected_target)

        buckets = (
            [StaffApplication.STATUS_APPROVED] * approved_target
            + [StaffApplication.STATUS_UNDER_REVIEW] * under_review_target
            + [StaffApplication.STATUS_CHANGES_REQUESTED] * changes_target
            + [StaffApplication.STATUS_REJECTED] * rejected_target
            + [StaffApplication.STATUS_DRAFT] * draft_target
        )

        approved_staff = []

        for status in buckets[:count]:
            first_name = fake.first_name()
            last_name = fake.last_name()
            staff_user = User.objects.create(
                username=fake.unique.user_name()[:150],
                email=fake.unique.email(),
                first_name=first_name,
                last_name=last_name,
                phone_number=fake.phone_number()[:20],
                role=User.ROLE_STAFF,
                is_active=True,
                is_verified=status == StaffApplication.STATUS_APPROVED,
                password=make_password("DemoPass123!"),
            )
            bg, fg = random.choice(SVG_COLORS)
            if random.random() > 0.35:
                staff_user.profile_image.save(
                    f"staff-profile-{staff_user.id}.svg",
                    svg_file(f"{first_name} {last_name}", bg, fg),
                    save=True,
                )

            applicant_type = random.choice([StaffApplication.TYPE_INDIVIDUAL, StaffApplication.TYPE_GROUP])
            application = StaffApplication.objects.create(
                user=staff_user,
                applicant_type=applicant_type,
                status=status,
                mission_summary=fake.paragraph(nb_sentences=4),
                location=f"{fake.city()}, Rwanda",
                organization_name=fake.company() if applicant_type == StaffApplication.TYPE_GROUP else "",
                registration_number=fake.bothify(text="ORG-#####") if applicant_type == StaffApplication.TYPE_GROUP else "",
                representative_name=fake.name() if applicant_type == StaffApplication.TYPE_GROUP else "",
                representative_id_number=fake.bothify(text="12###########") if applicant_type == StaffApplication.TYPE_GROUP else "",
                individual_id_number=fake.bothify(text="12###########") if applicant_type == StaffApplication.TYPE_INDIVIDUAL else "",
                admin_message="" if status in [StaffApplication.STATUS_DRAFT, StaffApplication.STATUS_UNDER_REVIEW] else fake.sentence(),
                reviewed_by=reviewer if status in [StaffApplication.STATUS_APPROVED, StaffApplication.STATUS_CHANGES_REQUESTED, StaffApplication.STATUS_REJECTED] else None,
                submitted_at=self._random_dt(self.now - timedelta(days=150), self.now - timedelta(days=5)),
                reviewed_at=self._random_dt(self.now - timedelta(days=45), self.now - timedelta(days=1))
                if status in [StaffApplication.STATUS_APPROVED, StaffApplication.STATUS_CHANGES_REQUESTED, StaffApplication.STATUS_REJECTED]
                else None,
            )

            if applicant_type == StaffApplication.TYPE_INDIVIDUAL:
                application.individual_id_document.save(
                    f"staff-app-{staff_user.id}-individual-id.pdf",
                    pdf_file(f"Individual ID {staff_user.username}"),
                    save=False,
                )
                application.individual_id_status = (
                    StaffApplication.DOC_APPROVED
                    if status == StaffApplication.STATUS_APPROVED
                    else StaffApplication.DOC_REJECTED
                    if status in [StaffApplication.STATUS_CHANGES_REQUESTED, StaffApplication.STATUS_REJECTED]
                    else StaffApplication.DOC_PENDING
                )
                application.individual_id_reason = (
                    "" if application.individual_id_status != StaffApplication.DOC_REJECTED else random.choice(
                        [StaffApplication.REASON_UNCLEAR, StaffApplication.REASON_MISMATCH, StaffApplication.REASON_OTHER]
                    )
                )
                application.group_legal_document_status = StaffApplication.DOC_NOT_REQUIRED
                application.representative_id_status = StaffApplication.DOC_NOT_REQUIRED
            else:
                application.group_legal_document.save(
                    f"staff-app-{staff_user.id}-group-legal.pdf",
                    pdf_file(f"Group Legal Doc {staff_user.username}"),
                    save=False,
                )
                application.representative_id_document.save(
                    f"staff-app-{staff_user.id}-representative-id.pdf",
                    pdf_file(f"Representative ID {staff_user.username}"),
                    save=False,
                )
                doc_status = (
                    StaffApplication.DOC_APPROVED
                    if status == StaffApplication.STATUS_APPROVED
                    else StaffApplication.DOC_REJECTED
                    if status in [StaffApplication.STATUS_CHANGES_REQUESTED, StaffApplication.STATUS_REJECTED]
                    else StaffApplication.DOC_PENDING
                )
                application.group_legal_document_status = doc_status
                application.representative_id_status = doc_status
                if doc_status == StaffApplication.DOC_REJECTED:
                    application.group_legal_document_reason = random.choice(
                        [StaffApplication.REASON_MISSING, StaffApplication.REASON_UNAUTHORIZED, StaffApplication.REASON_OTHER]
                    )
                    application.representative_id_reason = random.choice(
                        [StaffApplication.REASON_UNCLEAR, StaffApplication.REASON_EXPIRED, StaffApplication.REASON_OTHER]
                    )
                application.individual_id_status = StaffApplication.DOC_NOT_REQUIRED

            application.save()

            if status == StaffApplication.STATUS_APPROVED:
                approved_staff.append(staff_user)

        return {"approved": approved_staff}

    def _create_partners(self, count):
        partners = []
        themes = ["Foundation", "Alliance", "Collective", "Network", "Initiative", "Trust"]

        for index in range(count):
            name = f"{fake.city()} {random.choice(themes)}"
            partner = Partner.objects.create(
                name=f"{name} {index + 1}",
                website=fake.url(),
                description=fake.paragraph(nb_sentences=3),
                is_active=index % 5 != 0,
            )
            bg, fg = random.choice(SVG_COLORS)
            partner.logo.save(f"partner-{partner.id}.svg", svg_file(partner.name, bg, fg), save=True)
            partners.append(partner)

        return partners

    def _create_projects(self, count, partners, approved_staff, reviewer):
        projects = []
        project_types = [choice[0] for choice in Project.PROJECT_TYPE_CHOICES]
        statuses = [
            Project.STATUS_ACTIVE,
            Project.STATUS_ACTIVE,
            Project.STATUS_ACTIVE,
            Project.STATUS_PLANNING,
            Project.STATUS_COMPLETED,
            Project.STATUS_ON_HOLD,
        ]
        moderation_patterns = [
            (Project.MODERATION_CLEAR, Project.FUNDING_OPEN),
            (Project.MODERATION_UNDER_REVIEW, Project.FUNDING_OPEN),
            (Project.MODERATION_CLEAR, Project.FUNDING_FROZEN),
            (Project.MODERATION_TAKEN_DOWN, Project.FUNDING_FROZEN),
        ]

        for index in range(count):
            project_type = project_types[index % len(project_types)]
            topic = random.choice(PROJECT_TYPE_TOPICS[project_type])
            owner = approved_staff[index % len(approved_staff)]
            status = statuses[index % len(statuses)]
            moderation_status, funding_status = moderation_patterns[index % len(moderation_patterns)]
            if status == Project.STATUS_COMPLETED:
                moderation_status, funding_status = Project.MODERATION_CLEAR, Project.FUNDING_OPEN

            start_date = self._random_date(self.now.date() - timedelta(days=420), self.now.date() - timedelta(days=20))
            end_date = None
            if status == Project.STATUS_COMPLETED:
                min_end = start_date + timedelta(days=30)
                max_end = min(self.now.date() - timedelta(days=1), start_date + timedelta(days=220))
                if min_end <= max_end:
                    end_date = self._random_date(min_end, max_end)

            budget = Decimal(random.randint(4_000_000, 42_000_000))
            target = budget - Decimal(random.randint(0, max(1, int(budget // 5))))
            project = Project.objects.create(
                title=f"{topic} Program {index + 1}",
                description=fake.paragraph(nb_sentences=6),
                project_type=project_type,
                status=status,
                moderation_status=moderation_status,
                funding_status=funding_status,
                moderation_note=(
                    fake.sentence()
                    if moderation_status != Project.MODERATION_CLEAR or funding_status != Project.FUNDING_OPEN
                    else ""
                ),
                moderation_reviewed_at=(
                    self._random_dt(self.now - timedelta(days=60), self.now - timedelta(days=1))
                    if moderation_status != Project.MODERATION_CLEAR or funding_status != Project.FUNDING_OPEN
                    else None
                ),
                moderation_reviewed_by=reviewer if reviewer and (moderation_status != Project.MODERATION_CLEAR or funding_status != Project.FUNDING_OPEN) else None,
                budget=budget,
                target_amount=target,
                start_date=start_date,
                end_date=end_date,
                location=f"{fake.city()}, {fake.country()}",
                created_by=owner,
            )
            bg, fg = random.choice(SVG_COLORS)
            project.feature_image.save(f"project-{project.id}.svg", svg_file(project.title, bg, fg), save=True)
            chosen_partners = random.sample(partners, k=random.randint(1, min(3, len(partners))))
            project.partners.set(chosen_partners)
            Project.objects.filter(pk=project.pk).update(
                created_at=self._random_dt(self.now - timedelta(days=360), self.now - timedelta(days=25)),
                updated_at=self._random_dt(self.now - timedelta(days=40), self.now),
            )
            project.refresh_from_db()
            projects.append(project)

        return projects

    def _create_beneficiaries(self, projects):
        for project in projects:
            count = random.randint(2, 5)
            for index in range(count):
                beneficiary = Beneficiary.objects.create(
                    project=project,
                    name=fake.name(),
                    description=fake.paragraph(nb_sentences=3),
                    is_active=index % 4 != 0,
                )
                created_at = self._random_dt(
                    self._date_to_dt(project.start_date),
                    self.now - timedelta(days=2),
                )
                Beneficiary.objects.filter(pk=beneficiary.pk).update(
                    created_at=created_at,
                    updated_at=min(self.now, created_at + timedelta(days=random.randint(0, 45))),
                )
                if random.random() > 0.25:
                    for image_index in range(random.randint(1, 2)):
                        bg, fg = random.choice(SVG_COLORS)
                        image = BeneficiaryImage.objects.create(
                            beneficiary=beneficiary,
                            caption=f"Story image {image_index + 1}",
                        )
                        image.image.save(
                            f"beneficiary-{beneficiary.id}-{image_index + 1}.svg",
                            svg_file(beneficiary.name, bg, fg),
                            save=True,
                        )
                        BeneficiaryImage.objects.filter(pk=image.pk).update(
                            created_at=min(self.now, created_at + timedelta(days=image_index + 1))
                        )

    def _create_project_interests(self, projects, donors):
        for project in random.sample(projects, k=min(len(projects), max(6, len(projects) // 2))):
            for donor in random.sample(donors, k=min(len(donors), random.randint(2, 5))):
                ProjectInterest.objects.get_or_create(
                    project=project,
                    email=donor.email,
                    defaults={
                        "user": donor,
                        "name": f"{donor.first_name} {donor.last_name}".strip() or donor.username,
                        "is_active": random.random() > 0.2,
                    },
                )

    def _create_donations(self, projects, donors):
        for project in projects:
            donation_total = random.randint(5, 12)
            donor_choices = random.sample(donors, k=min(len(donors), donation_total))

            for index in range(donation_total):
                linked_donor = donor_choices[index % len(donor_choices)] if donor_choices and random.random() > 0.25 else None
                donor_name = (
                    f"{linked_donor.first_name} {linked_donor.last_name}".strip()
                    if linked_donor and (linked_donor.first_name or linked_donor.last_name)
                    else linked_donor.username
                    if linked_donor
                    else fake.name()
                )
                donor_email = linked_donor.email if linked_donor else fake.unique.email()
                status = random.choices(
                    [Donation.STATUS_COMPLETED, Donation.STATUS_PENDING, Donation.STATUS_FAILED, Donation.STATUS_CANCELLED],
                    weights=[8, 1, 1, 1],
                    k=1,
                )[0]
                donation = Donation.objects.create(
                    project=project,
                    donor=linked_donor,
                    donor_name=donor_name,
                    donor_email=donor_email,
                    amount=Decimal(random.randint(25_000, 900_000)),
                    payment_method=random.choice(PAYMENT_METHODS),
                    status=status,
                    message=fake.sentence() if random.random() > 0.35 else "",
                    is_anonymous=random.random() > 0.72,
                    transaction_reference=fake.unique.bothify(text="TXN-########"),
                )

                start_dt = self._date_to_dt(project.start_date)
                end_dt = self.now if not project.end_date else min(self.now, self._date_to_dt(project.end_date, latest=True) + timedelta(days=10))
                donated_at = self._random_dt(start_dt, end_dt)
                Donation.objects.filter(pk=donation.pk).update(
                    donated_at=donated_at,
                    updated_at=min(self.now, donated_at + timedelta(days=random.randint(0, 12))),
                )

    def _create_cashouts_and_updates(self, projects):
        for project in projects:
            general_updates_count = random.randint(1, 4)
            for index in range(general_updates_count):
                created_at = self._random_dt(self._date_to_dt(project.start_date), self.now - timedelta(days=1))
                update = ProjectUpdate.objects.create(
                    project=project,
                    update_type=ProjectUpdate.TYPE_GENERAL,
                    title=fake.sentence(nb_words=5).rstrip("."),
                    description=fake.paragraph(nb_sentences=4),
                    created_by=project.created_by,
                )
                ProjectUpdate.objects.filter(pk=update.pk).update(
                    created_at=created_at,
                    updated_at=min(self.now, created_at + timedelta(days=random.randint(0, 25))),
                )
                if random.random() > 0.35:
                    bg, fg = random.choice(SVG_COLORS)
                    image = ProjectUpdateImage.objects.create(
                        project_update=update,
                        caption="Field activity",
                    )
                    image.image.save(
                        f"project-update-{update.id}.svg",
                        svg_file(update.title, bg, fg),
                        save=True,
                    )

            if project.can_cash_out() and project.total_completed_donations() >= Decimal("150000.00"):
                cashout_rounds = random.randint(1, 3)
                remaining = project.total_completed_donations()
                for round_index in range(cashout_rounds):
                    if remaining < Decimal("50000.00"):
                        break
                    amount = min(
                        remaining - Decimal(random.randint(20_000, 60_000)),
                        Decimal(random.randint(40_000, 280_000)),
                    )
                    amount = max(amount, Decimal("40000.00"))
                    amount = amount.quantize(Decimal("1.00"))
                    if amount > remaining:
                        amount = remaining
                    remaining -= amount
                    created_at = self._random_dt(self._date_to_dt(project.start_date), self.now - timedelta(hours=12))
                    cashout = ProjectCashout.objects.create(
                        project=project,
                        requested_by=project.created_by,
                        amount=amount,
                        purpose=fake.paragraph(nb_sentences=2),
                        remaining_balance=max(project.total_completed_donations() - project.total_cashouts() - amount, Decimal("0.00")),
                    )
                    ProjectCashout.objects.filter(pk=cashout.pk).update(created_at=created_at)
                    update = ProjectUpdate.objects.create(
                        project=project,
                        update_type=ProjectUpdate.TYPE_CASHOUT,
                        title=f"Cashout activity {round_index + 1}",
                        description=f"Funds were released for: {cashout.purpose}",
                        cashout_amount=amount,
                        remaining_balance=max(project.total_completed_donations() - project.total_cashouts(), Decimal("0.00")),
                        created_by=project.created_by,
                    )
                    ProjectUpdate.objects.filter(pk=update.pk).update(
                        created_at=min(self.now, created_at + timedelta(minutes=30)),
                        updated_at=min(self.now, created_at + timedelta(hours=1)),
                    )

    def _create_reports(self, projects, donors, reviewer):
        reported_projects = random.sample(projects, k=min(len(projects), max(5, len(projects) // 3)))

        for project in reported_projects:
            reporters = random.sample(donors, k=min(len(donors), random.randint(2, 5)))
            for reporter in reporters:
                reason = random.choice(REPORT_REASONS)
                report = ProjectReport.objects.create(
                    project=project,
                    reported_by=reporter,
                    reason_type=reason,
                    claim_text=fake.paragraph(nb_sentences=2),
                    status=ProjectReport.STATUS_OPEN
                    if project.moderation_status == Project.MODERATION_UNDER_REVIEW
                    else random.choice([ProjectReport.STATUS_REVIEWED, ProjectReport.STATUS_DISMISSED]),
                )
                created_at = self._random_dt(self.now - timedelta(days=75), self.now - timedelta(days=1))
                ProjectReport.objects.filter(pk=report.pk).update(
                    created_at=created_at,
                    updated_at=min(self.now, created_at + timedelta(days=random.randint(0, 10))),
                )

            if project.moderation_status != Project.MODERATION_UNDER_REVIEW:
                project.moderation_reviewed_by = reviewer
                project.moderation_reviewed_at = self._random_dt(self.now - timedelta(days=30), self.now)
                if not project.moderation_note:
                    project.moderation_note = fake.sentence()
                project.save(update_fields=["moderation_reviewed_by", "moderation_reviewed_at", "moderation_note"])

    def _random_date(self, start_date, end_date):
        if start_date >= end_date:
            return start_date
        span = (end_date - start_date).days
        return start_date + timedelta(days=random.randint(0, span))

    def _date_to_dt(self, value, latest=False):
        current_tz = timezone.get_current_timezone()
        clock = time(18, 0) if latest else time(9, 0)
        return timezone.make_aware(datetime.combine(value, clock), current_tz)

    def _random_dt(self, start_dt, end_dt):
        if start_dt >= end_dt:
            return start_dt
        return fake.date_time_between_dates(
            datetime_start=start_dt,
            datetime_end=end_dt,
            tzinfo=timezone.get_current_timezone(),
        )
