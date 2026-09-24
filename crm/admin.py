from django.contrib import admin
from .models import Lead, Activity, DropdownOption

admin.site.register(Lead)
admin.site.register(Activity)
admin.site.register(DropdownOption)
admin.site.site_header = "PPL CRM Administration"