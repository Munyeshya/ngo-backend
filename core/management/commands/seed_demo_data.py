import random
import uuid
from datetime import timedelta
from decimal import Decimal
from io import BytesIO

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from faker import Faker
from PIL import Image, ImageDraw

from beneficiaries.models import Beneficiary, BeneficiaryImage
from donations.models import Donation
from projects.models import (
    Partner,
    Project,
    ProjectInterest,
    ProjectUpdate,
    ProjectUpdateImage,
)

fake = Faker()
User = get_user_model()


class Command(BaseCommand):
    help = "Seed the NGO platform with rich demo data for development and pagination testing."

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true", help="Delete seeded app data before inserting new demo data.")
        parser.add_argument("--staff", type=int, default=6)
        parser.add_argument("--donors", type=int, default=45)
        parser.add_argument("--partners", type=int, default=18)
        parser.add_argument("--projects", type=int, default=32)
        parser.add_argument("--beneficiaries", type=int, default=140)
        parser.add_argument("--donations", type=int, default=280)
        parser.add_argument("--updates", type=int, default=70)
        parser.add_argument("--interests", type=int, default=160)

    @transaction.atomic
    def handle(self, *args, **options):
        if options["reset"]:
            self.reset_data()

        admin = self.create_admin()
        staff_users = self.create_staff_users(options["staff"])
        donor_users = self.create_donor_users(options["donors"])
        partners = self.create_partners(options["partners"])
        projects = self.create_projects(options["projects"], admin, staff_users, partners)
        beneficiaries = self.create_beneficiaries(options["beneficiaries"], projects)
        self.create_beneficiary_images(beneficiaries)
        self.create_donations(options["donations"], projects, donor_users)
        updates = self.create_project_updates(options["updates"], projects, admin, staff_users)
        self.create_project_update_images(updates)
        self.create_project_interests(options["interests"], projects, donor_users)

        self.stdout.write(self.style.SUCCESS("Demo data inserted successfully."))
        self.stdout.write(self.style.SUCCESS('Login password for seeded users: StrongPass123'))

    def reset_data(self):
        self.stdout.write(self.style.WARNING("Resetting seeded app data..."))
        ProjectInterest.objects.all().delete()
        ProjectUpdateImage.objects.all().delete()
        ProjectUpdate.objects.all().delete()
        Donation.objects.all().delete()
        BeneficiaryImage.objects.all().delete()
        Beneficiary.objects.all().delete()
        Project.objects.all().delete()
        Partner.objects.all().delete()

        # Keep superusers if you want; remove non-superusers for cleaner reseed.
        User.objects.filter(is_superuser=False).delete()

    def create_admin(self):
        admin, created = User.objects.get_or_create(
            username="admin_master",
            defaults={
                "email": "admin@ngo.local",
                "role": User.ROLE_ADMIN,
                "is_staff": True,
                "is_superuser": True,
                "is_verified": True,
                "first_name": "System",
                "last_name": "Administrator",
            },
        )
        admin.role = User.ROLE_ADMIN
        admin.is_staff = True
        admin.is_superuser = True
        admin.is_verified = True
        admin.set_password("StrongPass123")
        admin.save()
        return admin

    def create_staff_users(self, count):
        staff_users = []
        first_names = ["Aline", "Jean", "Diane", "Eric", "Merveille", "Patrick", "Sandrine", "Claude", "Pacifique", "Olive"]
        last_names = ["Uwase", "Habimana", "Mukamana", "Niyonsenga", "Iradukunda", "Munyaneza", "Uwimana", "Ntawukuliryayo"]

        for i in range(1, count + 1):
            first_name = random.choice(first_names)
            last_name = random.choice(last_names)
            username = f"staff_{i}"
            email = f"staff{i}@ngo.local"

            user, _ = User.objects.get_or_create(
                username=username,
                defaults={
                    "email": email,
                    "role": User.ROLE_STAFF,
                    "first_name": first_name,
                    "last_name": last_name,
                    "phone_number": self.random_phone(),
                    "is_verified": True,
                },
            )
            user.email = email
            user.role = User.ROLE_STAFF
            user.first_name = first_name
            user.last_name = last_name
            user.phone_number = user.phone_number or self.random_phone()
            user.is_verified = True
            user.set_password("StrongPass123")
            user.save()
            staff_users.append(user)

        return staff_users

    def create_donor_users(self, count):
        donor_users = []
        for i in range(1, count + 1):
            first_name = fake.first_name()
            last_name = fake.last_name()
            username = f"donor_{i}"
            email = f"donor{i}@mail.local"

            user, _ = User.objects.get_or_create(
                username=username,
                defaults={
                    "email": email,
                    "role": User.ROLE_DONOR,
                    "first_name": first_name,
                    "last_name": last_name,
                    "phone_number": self.random_phone(),
                    "is_verified": random.choice([True, False]),
                },
            )
            user.email = email
            user.role = User.ROLE_DONOR
            user.first_name = first_name
            user.last_name = last_name
            user.phone_number = user.phone_number or self.random_phone()
            user.set_password("StrongPass123")
            user.save()
            donor_users.append(user)

        return donor_users

    def create_partners(self, count):
        base_names = [
            "UNICEF Rwanda", "World Vision Rwanda", "Save the Children", "Rwanda Red Cross",
            "UNDP Rwanda", "Compassion International", "WaterAid Rwanda", "Plan International",
            "Caritas Rwanda", "Hope for Communities", "Health Access Initiative", "Bright Futures Foundation",
            "Green Growth Africa", "Future Minds Initiative", "Rural Resilience Network", "Women First Alliance",
            "Food Security Action", "Youth Skills Catalyst", "Community Care Link", "Inclusive Development Hub"
        ]
        partners = []

        for i in range(count):
            name = base_names[i] if i < len(base_names) else f"{fake.company()} Foundation"
            partner, _ = Partner.objects.get_or_create(
                name=name,
                defaults={
                    "website": fake.url(),
                    "description": fake.paragraph(nb_sentences=4),
                    "is_active": random.choice([True, True, True, False]),
                },
            )

            if not partner.logo:
                partner.logo.save(
                    f"partner_{slugify_filename(name)}.jpg",
                    self.generate_image(f"P{i+1}", size=(500, 300)),
                    save=False,
                )

            partner.website = partner.website or fake.url()
            partner.description = partner.description or fake.paragraph(nb_sentences=4)
            partner.save()
            partners.append(partner)

        return partners

    def create_projects(self, count, admin, staff_users, partners):
        project_titles = [
            "Community Health Outreach",
            "Safe Water Access Program",
            "Girls Education Support",
            "Maternal Health Initiative",
            "Youth Skills Development",
            "School Feeding Expansion",
            "Rural Agriculture Strengthening",
            "Disability Inclusion Support",
            "Nutrition Improvement Campaign",
            "Women Economic Empowerment",
            "Emergency Shelter Response",
            "Village Sanitation Program",
            "Digital Literacy for Youth",
            "Climate Resilient Farming",
            "Child Protection Initiative",
            "Mental Health Awareness Drive",
            "Community Savings Support",
            "Early Childhood Learning Program",
        ]
        locations = [
            "Kigali, Rwanda", "Musanze, Rwanda", "Huye, Rwanda", "Rubavu, Rwanda",
            "Nyagatare, Rwanda", "Rusizi, Rwanda", "Rwamagana, Rwanda", "Muhanga, Rwanda"
        ]
        statuses = [
            Project.STATUS_PLANNING,
            Project.STATUS_ACTIVE,
            Project.STATUS_COMPLETED,
            Project.STATUS_ON_HOLD,
        ]
        project_type_map = {
            "Community Health Outreach": Project.TYPE_HEALTH,
            "Safe Water Access Program": Project.TYPE_COMMUNITY_DEVELOPMENT,
            "Girls Education Support": Project.TYPE_EDUCATION,
            "Maternal Health Initiative": Project.TYPE_HEALTH,
            "Youth Skills Development": Project.TYPE_YOUTH_EMPOWERMENT,
            "School Feeding Expansion": Project.TYPE_EDUCATION,
            "Rural Agriculture Strengthening": Project.TYPE_LIVELIHOOD,
            "Disability Inclusion Support": Project.TYPE_COMMUNITY_DEVELOPMENT,
            "Nutrition Improvement Campaign": Project.TYPE_HEALTH,
            "Women Economic Empowerment": Project.TYPE_WOMEN_EMPOWERMENT,
            "Emergency Shelter Response": Project.TYPE_EMERGENCY_RELIEF,
            "Village Sanitation Program": Project.TYPE_COMMUNITY_DEVELOPMENT,
            "Digital Literacy for Youth": Project.TYPE_YOUTH_EMPOWERMENT,
            "Climate Resilient Farming": Project.TYPE_ENVIRONMENT,
            "Child Protection Initiative": Project.TYPE_COMMUNITY_DEVELOPMENT,
            "Mental Health Awareness Drive": Project.TYPE_HEALTH,
            "Community Savings Support": Project.TYPE_LIVELIHOOD,
            "Early Childhood Learning Program": Project.TYPE_EDUCATION,
        }
        projects = []

        for i in range(count):
            title = project_titles[i] if i < len(project_titles) else f"{fake.catch_phrase()} Initiative"
            creator = random.choice([admin] + staff_users * 4)
            start_date = fake.date_between(start_date="-18M", end_date="+2M")
            end_date = start_date + timedelta(days=random.randint(60, 420))
            budget = Decimal(random.randint(500000, 15000000))
            target_amount = budget + Decimal(random.randint(0, 5000000))

            project = Project.objects.create(
                title=title,
                description=fake.paragraph(nb_sentences=6),
                project_type=project_type_map.get(
                    title,
                    random.choice([choice[0] for choice in Project.PROJECT_TYPE_CHOICES]),
                ),
                status=random.choices(
                    statuses,
                    weights=[15, 50, 20, 15],
                    k=1,
                )[0],
                budget=budget,
                target_amount=target_amount,
                start_date=start_date,
                end_date=end_date,
                location=random.choice(locations),
                created_by=creator,
            )

            project.partners.set(random.sample(partners, k=random.randint(1, min(4, len(partners)))))

            project.feature_image.save(
                f"project_{i+1}.jpg",
                self.generate_image(f"PR{i+1}", size=(900, 520)),
                save=False,
            )
            project.save()
            projects.append(project)

        return projects

    def create_beneficiaries(self, count, projects):
        beneficiary_types = [
            "single mother", "elderly caregiver", "school-going child", "youth apprentice",
            "farmer household", "person with disability", "pregnant woman", "refugee family",
            "widowed parent", "small business owner"
        ]
        support_types = [
            "received medical support", "joined nutrition sessions", "benefited from school materials",
            "received livelihood support", "joined skills training", "received hygiene kits",
            "received agricultural inputs", "joined counseling follow-up"
        ]

        beneficiaries = []
        for i in range(count):
            project = random.choice(projects)
            name = fake.name()
            situation = random.choice(beneficiary_types)
            support = random.choice(support_types)
            description = (
                f"{name} is a {situation} under the {project.title} project. "
                f"This beneficiary {support}. {fake.paragraph(nb_sentences=3)}"
            )
            beneficiary = Beneficiary.objects.create(
                project=project,
                name=name,
                description=description,
                is_active=random.choice([True, True, True, False]),
            )
            beneficiaries.append(beneficiary)

        return beneficiaries

    def create_beneficiary_images(self, beneficiaries):
        for beneficiary in random.sample(beneficiaries, k=max(10, len(beneficiaries) // 2)):
            for idx in range(random.randint(1, 3)):
                image = BeneficiaryImage(
                    beneficiary=beneficiary,
                    caption=random.choice(
                        ["Home visit", "Support session", "Field assessment", "Community outreach", "Follow-up visit"]
                    ),
                )
                image.image.save(
                    f"beneficiary_{beneficiary.id}_{idx+1}.jpg",
                    self.generate_image(f"B{beneficiary.id}", size=(720, 480)),
                    save=False,
                )
                image.save()

    def create_donations(self, count, projects, donor_users):
        methods = [
            Donation.PAYMENT_MOMO,
            Donation.PAYMENT_CARD,
            Donation.PAYMENT_BANK,
            Donation.PAYMENT_CASH,
        ]
        statuses = [
            Donation.STATUS_COMPLETED,
            Donation.STATUS_PENDING,
            Donation.STATUS_FAILED,
            Donation.STATUS_CANCELLED,
        ]

        for i in range(count):
            project = random.choice(projects)
            linked_user = random.choice(donor_users) if random.random() < 0.75 else None

            if linked_user:
                donor_name = f"{linked_user.first_name} {linked_user.last_name}".strip() or linked_user.username
                donor_email = linked_user.email
            else:
                donor_name = fake.name()
                donor_email = fake.unique.email()

            Donation.objects.create(
                project=project,
                donor=linked_user,
                donor_name=donor_name,
                donor_email=donor_email,
                amount=Decimal(random.randint(5000, 750000)),
                payment_method=random.choice(methods),
                status=random.choices(statuses, weights=[70, 15, 8, 7], k=1)[0],
                message=random.choice(
                    [
                        "Keep up the great work.",
                        "Glad to support this cause.",
                        "Wishing the project continued success.",
                        "Supporting from our family.",
                        fake.sentence(nb_words=10),
                        None,
                    ]
                ),
                is_anonymous=random.choice([True, False, False]),
                transaction_reference=f"TXN-{timezone.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:10].upper()}",
            )

    def create_project_updates(self, count, projects, admin, staff_users):
        update_heads = [
            "Phase One Completed",
            "Community Outreach Milestone",
            "Supplies Delivered",
            "Midterm Progress Review",
            "Health Session Conducted",
            "Training Round Completed",
            "Expansion to New Area",
            "Impact Follow-Up Summary",
            "Beneficiary Reach Update",
            "Field Team Progress Note",
        ]
        updates = []

        for i in range(count):
            project = random.choice(projects)
            owner = project.created_by if project.created_by and project.created_by.role == User.ROLE_STAFF else admin
            title = random.choice(update_heads)
            update = ProjectUpdate.objects.create(
                project=project,
                title=f"{title} #{i+1}",
                description=fake.paragraph(nb_sentences=5),
                created_by=owner,
            )
            updates.append(update)

        return updates

    def create_project_update_images(self, updates):
        for update in random.sample(updates, k=max(8, len(updates) // 2)):
            for idx in range(random.randint(1, 2)):
                img = ProjectUpdateImage(
                    project_update=update,
                    caption=random.choice(
                        ["Field team activity", "Beneficiary engagement", "Distribution event", "Milestone evidence"]
                    ),
                )
                img.image.save(
                    f"update_{update.id}_{idx+1}.jpg",
                    self.generate_image(f"U{update.id}", size=(900, 520)),
                    save=False,
                )
                img.save()

    def create_project_interests(self, count, projects, donor_users):
        created_pairs = set()

        # First give many real donors interests
        for donor in donor_users:
            for _ in range(random.randint(1, 3)):
                project = random.choice(projects)
                key = (project.id, donor.email)
                if key in created_pairs:
                    continue
                ProjectInterest.objects.create(
                    project=project,
                    user=donor,
                    name=f"{donor.first_name} {donor.last_name}".strip() or donor.username,
                    email=donor.email,
                    is_active=random.choice([True, True, True, False]),
                )
                created_pairs.add(key)

        # Add guest subscriptions
        attempts = 0
        while len(created_pairs) < count and attempts < count * 10:
            attempts += 1
            project = random.choice(projects)
            email = fake.unique.email()
            key = (project.id, email)
            if key in created_pairs:
                continue

            ProjectInterest.objects.create(
                project=project,
                user=None,
                name=fake.name(),
                email=email,
                is_active=random.choice([True, True, False]),
            )
            created_pairs.add(key)

    def random_phone(self):
        return f"07{random.randint(20, 99)}{random.randint(100000, 999999)}"

    def generate_image(self, label, size=(800, 500)):
        image = Image.new(
            "RGB",
            size,
            color=(
                random.randint(30, 180),
                random.randint(60, 200),
                random.randint(30, 180),
            ),
        )
        draw = ImageDraw.Draw(image)
        draw.text((20, 20), label, fill=(255, 255, 255))

        buffer = BytesIO()
        image.save(buffer, format="JPEG", quality=90)
        return ContentFile(buffer.getvalue())


def slugify_filename(value):
    return "".join(ch.lower() if ch.isalnum() else "_" for ch in value).strip("_")
