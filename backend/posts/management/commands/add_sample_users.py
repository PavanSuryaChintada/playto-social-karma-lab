"""
Add sample users for local development and testing.
Run: python manage.py add_sample_users
"""
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

User = get_user_model()

SAMPLE_USERS = [
    {"username": "alice", "email": "alice@example.com"},
    {"username": "bob", "email": "bob@example.com"},
    {"username": "carol", "email": "carol@example.com"},
    {"username": "dave", "email": "dave@example.com"},
    {"username": "eve", "email": "eve@example.com"},
]

DEFAULT_PASSWORD = "SamplePass123!"


class Command(BaseCommand):
    help = "Add sample users (password: SamplePass123!)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--password",
            default=DEFAULT_PASSWORD,
            help=f"Password for new users (default: {DEFAULT_PASSWORD})",
        )

    def handle(self, *args, **options):
        password = options["password"]
        for data in SAMPLE_USERS:
            user, created = User.objects.get_or_create(
                username=data["username"],
                defaults={"email": data["email"]},
            )
            if created:
                user.set_password(password)
                user.save()
                self.stdout.write(self.style.SUCCESS(f"Created user: {user.username}"))
            else:
                self.stdout.write(f"User already exists: {user.username}")

        self.stdout.write(
            self.style.SUCCESS(
                f"\nDone. Log in with any username above and password: {password}"
            )
        )
