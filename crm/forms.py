from django import forms
from django.contrib.auth.models import User
from .models import Lead, Activity, DropdownOption


class LeadForm(forms.ModelForm):
    class Meta:
        model = Lead
        fields = ["name", "company", "email", "phone", "status", "stage",
                  "source", "owner", "value", "notes"]
        widgets = {
            "notes": forms.Textarea(attrs={"rows": 3}),
            "stage": forms.TextInput(),
            "source": forms.TextInput(),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["owner"].queryset = User.objects.filter(
            is_active=True, profile__active=True
        ).order_by("username")
        self.fields["owner"].required = False
        # Use dropdown options
        stages = list(DropdownOption.objects.filter(category="stage", active=True).values_list("value", flat=True))
        sources = list(DropdownOption.objects.filter(category="source", active=True).values_list("value", flat=True))
        if stages:
            self.fields["stage"] = forms.ChoiceField(choices=[("", "---------")] + [(s, s) for s in stages], required=False)
        if sources:
            self.fields["source"] = forms.ChoiceField(choices=[("", "---------")] + [(s, s) for s in sources], required=False)


class ActivityForm(forms.ModelForm):
    class Meta:
        model = Activity
        fields = ["activity_type", "subject", "notes", "due_at"]
        widgets = {
            "notes": forms.Textarea(attrs={"rows": 2}),
            "due_at": forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["due_at"].input_formats = ["%Y-%m-%dT%H:%M"]


class DropdownOptionForm(forms.ModelForm):
    class Meta:
        model = DropdownOption
        fields = ["category", "value", "active", "sort_order"]


class ImportForm(forms.Form):
    file = forms.FileField(help_text="Excel (.xlsx) file with columns: name, company, email, phone, stage, source, value, owner_username")