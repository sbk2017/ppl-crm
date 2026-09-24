from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from crm.models import Lead, DropdownOption
from accounts.models import Profile


class Command(BaseCommand):
    help = "Seed sample data for local testing."

    def handle(self, *args, **options):
        # Dropdowns
        for cat, values in {
            "stage": ["New", "Qualified", "Proposal", "Negotiation", "Closed"],
            "source": ["Website", "Referral", "Cold Call", "Email", "Walk-in"],
        }.items():
            for i, v in enumerate(values):
                DropdownOption.objects.get_or_create(category=cat, value=v, defaults={"sort_order": i})

        # Sales user
        sales, created = User.objects.get_or_create(username="sales1",
            defaults={"first_name": "Sales", "last_name": "One", "email": "sales1@pplcargo.com"})
        if created:
            sales.set_password("Sales123!")
            sales.save()
        Profile.objects.get_or_create(user=sales, defaults={"role": "sales"})

        admin = User.objects.filter(profile__role="admin").first()

        # Leads
        samples = [
            ("Acme Logistics", "Acme LLC", "info@acme.com", "+971500000001", "New", "Website", 5000),
            ("Blue Wave Shipping", "Blue Wave", "ops@bluewave.com", "+971500000002", "Qualified", "Referral", 12000),
            ("Desert Traders", "Desert Traders", "hello@desert.com", "+971500000003", "Proposal", "Email", 8000),
            ("Falcon Freight", "Falcon Freight", "sales@falcon.com", "+971500000004", "Negotiation", "Cold Call", 20000),
            ("Gulf Cargo Co", "Gulf Cargo", "info@gulfcargo.com", "+971500000005", "Closed", "Walk-in", 15000),
        ]
        for name, comp, email, phone, stage, source, value in samples:
            Lead.objects.get_or_create(
                name=name,
                defaults={
                    "company": comp, "email": email, "phone": phone,
                    "stage": stage, "source": source, "value": value,
                    "owner": sales, "created_by": admin or sales, "updated_by": admin or sales,
                    "status": "won" if stage == "Closed" else "open",
                }
            )
        self.stdout.write(self.style.SUCCESS("Sample data seeded."))