import random

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from faker import Faker


fake = Faker()
User = get_user_model()


class Command(BaseCommand):
    help = "Create pending staff applications for admin review."

    def add_arguments(self, parser):
        parser.add_argument(
            "--count",
            type=int,
            default=6,
            help="Number of pending staff applications to create.",
        )

    def handle(self, *args, **options):
        count = max(options["count"], 0)
        created = 0

        for _ in range(count):
            first_name = fake.first_name()
            last_name = fake.last_name()
            username = self._unique_username(first_name, last_name)
            email = self._unique_email(first_name, last_name)

            user = User.objects.create(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name,
                phone_number=self._random_phone(),
                role=User.ROLE_STAFF,
                is_active=False,
                is_verified=False,
                is_staff=False,
            )
            user.set_password("StrongPass123")
            user.save(update_fields=["password"])
            created += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Created {created} pending staff application(s). Default password: StrongPass123"
            )
        )

    def _unique_username(self, first_name, last_name):
        base = f"{first_name}.{last_name}".lower().replace(" ", "")
        candidate = f"{base}.{random.randint(100, 999)}"
        while User.objects.filter(username=candidate).exists():
            candidate = f"{base}.{random.randint(100, 999)}"
        return candidate

    def _unique_email(self, first_name, last_name):
        base = f"{first_name}.{last_name}".lower().replace(" ", "")
        candidate = f"{base}.{random.randint(100, 999)}@staff-app.local"
        while User.objects.filter(email=candidate).exists():
            candidate = f"{base}.{random.randint(100, 999)}@staff-app.local"
        return candidate

    def _random_phone(self):
        return f"07{random.randint(20, 99)}{random.randint(100000, 999999)}"
