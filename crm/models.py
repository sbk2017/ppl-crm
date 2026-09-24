from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class DropdownOption(models.Model):
    """Configurable dropdown values for stages, sources, etc."""
    CATEGORY_CHOICES = [
        ("stage", "Stage"),
        ("source", "Contact Source"),
        ("status", "Status"),
    ]
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    value = models.CharField(max_length=100)
    active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=100)

    class Meta:
        ordering = ["category", "sort_order", "value"]
        unique_together = ("category", "value")

    def __str__(self):
        return f"{self.get_category_display()}: {self.value}"


class Lead(models.Model):
    STATUS_CHOICES = [
        ("open", "Open"),
        ("won", "Closed - Won"),
        ("lost", "Closed - Lost"),
    ]

    # Core fields
    name = models.CharField(max_length=200)
    company = models.CharField(max_length=200, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="open")
    stage = models.CharField(max_length=100, blank=True)
    source = models.CharField(max_length=100, blank=True)

    owner = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="owned_leads"
    )
    value = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notes = models.TextField(blank=True)

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="created_leads")
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="updated_leads")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    archived = models.BooleanField(default=False)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return self.name

    @property
    def next_followup(self):
        return self.activities.filter(completed=False).order_by("due_at").first()


class Activity(models.Model):
    ACTIVITY_TYPES = [
        ("call", "Call"),
        ("email", "Email"),
        ("meeting", "Meeting"),
        ("note", "Note"),
        ("task", "Task"),
    ]

    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name="activities")
    activity_type = models.CharField(max_length=10, choices=ACTIVITY_TYPES, default="note")
    subject = models.CharField(max_length=200)
    notes = models.TextField(blank=True)
    due_at = models.DateTimeField(null=True, blank=True)
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="created_activities")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_activity_type_display()}: {self.subject}"

    @property
    def is_overdue(self):
        return (not self.completed) and self.due_at and self.due_at < timezone.now()