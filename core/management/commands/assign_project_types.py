from django.core.management.base import BaseCommand
from faker import Faker

from projects.models import Project

fake = Faker()


TYPE_KEYWORDS = {
    Project.TYPE_EDUCATION: [
        "education",
        "school",
        "student",
        "learning",
        "literacy",
        "childhood",
    ],
    Project.TYPE_HEALTH: [
        "health",
        "medical",
        "nutrition",
        "mental",
        "clinic",
        "maternal",
    ],
    Project.TYPE_LIVELIHOOD: [
        "livelihood",
        "agriculture",
        "farming",
        "savings",
        "business",
        "skills",
    ],
    Project.TYPE_WOMEN_EMPOWERMENT: [
        "women",
        "girl",
        "maternal",
    ],
    Project.TYPE_YOUTH_EMPOWERMENT: [
        "youth",
        "young",
        "digital literacy",
        "skills",
        "apprentice",
    ],
    Project.TYPE_COMMUNITY_DEVELOPMENT: [
        "community",
        "water",
        "sanitation",
        "child protection",
        "disability",
        "village",
    ],
    Project.TYPE_ENVIRONMENT: [
        "environment",
        "climate",
        "green",
        "tree",
        "resilient",
    ],
    Project.TYPE_EMERGENCY_RELIEF: [
        "emergency",
        "relief",
        "shelter",
        "response",
    ],
}


class Command(BaseCommand):
    help = "Assign project types to existing projects using keyword matching and Faker-backed randomness."

    def add_arguments(self, parser):
        parser.add_argument(
            "--overwrite",
            action="store_true",
            help="Reassign project types even if a project already has one.",
        )

    def handle(self, *args, **options):
        overwrite = options["overwrite"]
        updated = 0

        choices = [choice[0] for choice in Project.PROJECT_TYPE_CHOICES]

        queryset = Project.objects.all()
        if not overwrite:
            queryset = queryset.filter(project_type=Project.TYPE_OTHER)

        for project in queryset:
            haystack = f"{project.title} {project.description}".lower()
            assigned_type = None

            for project_type, keywords in TYPE_KEYWORDS.items():
                if any(keyword in haystack for keyword in keywords):
                    assigned_type = project_type
                    break

            if not assigned_type:
                assigned_type = fake.random_element(
                    elements=[
                        Project.TYPE_EDUCATION,
                        Project.TYPE_HEALTH,
                        Project.TYPE_LIVELIHOOD,
                        Project.TYPE_COMMUNITY_DEVELOPMENT,
                        Project.TYPE_YOUTH_EMPOWERMENT,
                        Project.TYPE_WOMEN_EMPOWERMENT,
                        Project.TYPE_ENVIRONMENT,
                        Project.TYPE_EMERGENCY_RELIEF,
                        Project.TYPE_OTHER,
                    ]
                )

            if assigned_type not in choices:
                assigned_type = Project.TYPE_OTHER

            project.project_type = assigned_type
            project.save(update_fields=["project_type"])
            updated += 1

        self.stdout.write(
            self.style.SUCCESS(f"Assigned project types for {updated} project(s).")
        )
