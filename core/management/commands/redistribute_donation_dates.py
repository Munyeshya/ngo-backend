from django.core.management.base import BaseCommand
from django.utils import timezone
from faker import Faker

from donations.models import Donation

fake = Faker()


class Command(BaseCommand):
    help = "Redistribute donation dates across the current year for better analytics charts."

    def add_arguments(self, parser):
        parser.add_argument(
            "--year",
            type=int,
            default=timezone.now().year,
            help="Year to spread donation dates across. Defaults to the current year.",
        )

    def handle(self, *args, **options):
        target_year = options["year"]
        updated = 0

        start = timezone.datetime(target_year, 1, 1, 8, 0, 0, tzinfo=timezone.get_current_timezone())
        end = timezone.datetime(target_year, 12, 31, 18, 0, 0, tzinfo=timezone.get_current_timezone())

        queryset = Donation.objects.select_related("project").all().order_by("id")

        for donation in queryset:
            random_date = fake.date_time_between_dates(
                datetime_start=start,
                datetime_end=end,
                tzinfo=timezone.get_current_timezone(),
            )
            Donation.objects.filter(pk=donation.pk).update(donated_at=random_date)
            updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Redistributed donated_at dates for {updated} donation(s) across {target_year}."
            )
        )
