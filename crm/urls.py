from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),

    path("leads/", views.lead_list, name="lead_list"),
    path("leads/add/", views.lead_add, name="lead_add"),
    path("leads/<int:pk>/", views.lead_detail, name="lead_detail"),
    path("leads/<int:pk>/edit/", views.lead_edit, name="lead_edit"),
    path("leads/<int:pk>/archive/", views.lead_archive, name="lead_archive"),

    path("followups/", views.followup_list, name="followup_list"),
    path("activities/<int:pk>/complete/", views.activity_complete, name="activity_complete"),

    path("reports/", views.reports, name="reports"),

    path("import/", views.import_leads, name="import_leads"),
    path("export/<str:fmt>/", views.export_leads, name="export_leads"),

    path("settings/", views.settings_index, name="settings_index"),
    path("settings/options/<int:pk>/delete/", views.option_delete, name="option_delete"),
    path("settings/backup/", views.backup_create, name="backup_create"),
    path("settings/backups/", views.backup_list, name="backup_list"),
    path("settings/backups/<str:name>/", views.backup_download, name="backup_download"),
]