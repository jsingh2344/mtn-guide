import os

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import BaseCommand

from mountains.models import ContentSection, ImportedPhoto, Peak, SourceRecord


class Command(BaseCommand):
    help = "Create an optional env-driven admin user and optionally import SummitPost data."

    def add_arguments(self, parser):
        parser.add_argument("--import-data", action="store_true")

    def handle(self, *args, **options):
        self.create_admin_from_env()

        if options["import_data"]:
            self.stdout.write("IMPORT: starting Wyoming SummitPost import")
            call_command("scrape_summitpost_wyoming")
            self.stdout.write("IMPORT: starting Peru SummitPost import")
            call_command("scrape_summitpost_peru")

        self.print_summary()

    def create_admin_from_env(self):
        username = os.environ.get("DJANGO_SUPERUSER_USERNAME", "").strip()
        email = os.environ.get("DJANGO_SUPERUSER_EMAIL", "").strip()
        password = os.environ.get("DJANGO_SUPERUSER_PASSWORD", "").strip()

        if not username or not password:
            self.stdout.write("ADMIN: DJANGO_SUPERUSER_USERNAME/PASSWORD not set; skipping admin bootstrap")
            return

        User = get_user_model()
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                "email": email,
                "is_staff": True,
                "is_superuser": True,
            },
        )
        if created:
            user.set_password(password)
            user.save()
            self.stdout.write(self.style.SUCCESS(f"ADMIN: created superuser {username}"))
        else:
            changed = False
            if not user.is_staff or not user.is_superuser:
                user.is_staff = True
                user.is_superuser = True
                changed = True
            if email and user.email != email:
                user.email = email
                changed = True
            if changed:
                user.save()
            self.stdout.write(f"ADMIN: superuser {username} already exists")

    def print_summary(self):
        self.stdout.write(
            "SUMMARY: "
            f"peaks={Peak.objects.count()} "
            f"summitpost_sources={SourceRecord.objects.filter(source_type='summitpost').count()} "
            f"sections={ContentSection.objects.count()} "
            f"photos={ImportedPhoto.objects.count()}"
        )
