import os
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from accounts.models import Profile


class Command(BaseCommand):
    help = "Create or update the initial administrator."

    def handle(self, *args, **options):
        username = os.getenv("ADMIN_EMAIL") or "admin@pplcargo.com"
        email = os.getenv("ADMIN_EMAIL") or "admin@pplcargo.com"
        password = os.getenv("ADMIN_PASSWORD") or "ChangeMe123!"
        name = os.getenv("ADMIN_NAME") or "Administrator"

        user, created = User.objects.get_or_create(
            username=username, defaults={"email": email, "first_name": name}
        )
        user.email = email
        user.first_name = name
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        user.set_password(password)
        user.save()

        profile, _ = Profile.objects.get_or_create(user=user)
        profile.role = Profile.ROLE_ADMIN
        profile.active = True
        profile.save()

        self.stdout.write(self.style.SUCCESS(
            f"{'Created' if created else 'Updated'} admin: {username}"
        ))