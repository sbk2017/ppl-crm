from django import forms
from django.contrib.auth.models import User
from .models import Lead, Activity, DropdownOption


class LeadForm(forms.ModelForm):
    class Meta:
        model = Lead
        fields = [
            "name", "company", "email", "phone",
            "country", "city",                       # NEW
            "status", "stage", "source", "owner",
            "value", "notes",
        ]
        widgets = {
            "notes": forms.Textarea(attrs={"rows": 3}),
            "stage": forms.TextInput(),
            "source": forms.TextInput(),
            "country": forms.TextInput(attrs={"placeholder": "e.g. United Arab Emirates"}),
            "city": forms.TextInput(attrs={"placeholder": "e.g. Dubai"}),
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
        countries = list(DropdownOption.objects.filter(category="country", active=True).values_list("value", flat=True))
        cities    = list(DropdownOption.objects.filter(category="city",    active=True).values_list("value", flat=True))

        if countries:
            self.fields["country"] = forms.ChoiceField(
                choices=[("", "---------")] + [(c, c) for c in countries], required=False)
        if cities:
            self.fields["city"] = forms.ChoiceField(
                choices=[("", "---------")] + [(c, c) for c in cities], required=False)

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