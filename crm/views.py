import csv
from datetime import datetime, timedelta
from pathlib import Path
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Count, Q, Sum
from django.http import HttpResponse, FileResponse, Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.conf import settings

from .models import Lead, Activity, DropdownOption
from .forms import LeadForm, ActivityForm, DropdownOptionForm, ImportForm
from .utils import export_leads_xlsx, import_leads_xlsx, create_backup
from accounts.views import admin_required


def sales_only_or_admin(qs, user):
    """Return queryset scoped to the user's role."""
    if user.profile.is_admin:
        return qs
    return qs.filter(Q(owner=user) | Q(created_by=user))


# ---------- Dashboard ----------
@login_required
def dashboard(request):
    leads = sales_only_or_admin(Lead.objects.filter(archived=False), request.user)
    now = timezone.now()
    today_end = now.replace(hour=23, minute=59, second=59)

    total = leads.count()
    open_leads = leads.filter(status="open").count()
    won = leads.filter(status="won").count()
    lost = leads.filter(status="lost").count()
    conversion = round((won / (won + lost) * 100), 1) if (won + lost) else 0

    activities = Activity.objects.filter(
        lead__in=leads, completed=False, due_at__isnull=False
    )
    overdue = activities.filter(due_at__lt=now).count()
    due_today = activities.filter(due_at__gte=now, due_at__lte=today_end).count()
    meetings = activities.filter(activity_type="meeting", due_at__gte=now).count()

    by_stage = list(leads.values("stage").annotate(c=Count("id")).order_by("-c"))
    by_source = list(leads.values("source").annotate(c=Count("id")).order_by("-c"))
    by_owner = list(
        leads.values("owner__username").annotate(c=Count("id")).order_by("-c")
    )

    context = {
        "total": total, "open_leads": open_leads, "won": won, "lost": lost,
        "conversion": conversion, "overdue": overdue, "due_today": due_today,
        "meetings": meetings,
        "by_stage": by_stage, "by_source": by_source, "by_owner": by_owner,
    }
    return render(request, "dashboard.html", context)


# ---------- Leads ----------
@login_required
def lead_list(request):
    qs = sales_only_or_admin(Lead.objects.filter(archived=False), request.user)
    q = request.GET.get("q", "").strip()
    status = request.GET.get("status", "")
    stage = request.GET.get("stage", "")
    source = request.GET.get("source", "")
    owner = request.GET.get("owner", "")
    country = request.GET.get("country", "")   # NEW
    city = request.GET.get("city", "")         # NEW

    if q:
        qs = qs.filter(
            Q(name__icontains=q) | Q(company__icontains=q) |
            Q(email__icontains=q) | Q(phone__icontains=q) |
            Q(country__icontains=q) | Q(city__icontains=q)      # include in search
        )
    if status:  qs = qs.filter(status=status)
    if stage:   qs = qs.filter(stage=stage)
    if source:  qs = qs.filter(source=source)
    if owner:   qs = qs.filter(owner_id=owner)
    if country: qs = qs.filter(country=country)                 # NEW
    if city:    qs = qs.filter(city=city)                       # NEW

    # Distinct values for the dropdowns
    countries = (Lead.objects.filter(archived=False)
                 .exclude(country="")
                 .values_list("country", flat=True)
                 .distinct().order_by("country"))
    cities = (Lead.objects.filter(archived=False)
              .exclude(city="")
              .values_list("city", flat=True)
              .distinct().order_by("city"))

    return render(request, "leads/list.html", {
        "leads": qs,
        "q": q, "status": status, "stage": stage, "source": source, "owner": owner,
        "country": country, "city": city,                        # NEW
        "countries": countries, "cities": cities,                # NEW
        "stages": DropdownOption.objects.filter(category="stage", active=True),
        "sources": DropdownOption.objects.filter(category="source", active=True),
        "owners": User.objects.filter(is_active=True, profile__active=True),
    })

@login_required
def lead_add(request):
    if request.method == "POST":
        form = LeadForm(request.POST, user=request.user)
        if form.is_valid():
            lead = form.save(commit=False)
            lead.created_by = request.user
            lead.updated_by = request.user
            if not lead.owner:
                lead.owner = request.user
            lead.save()
            messages.success(request, "Lead created.")
            return redirect("lead_detail", pk=lead.pk)
    else:
        form = LeadForm(user=request.user)
    return render(request, "leads/form.html", {"form": form, "title": "Add Lead"})


@login_required
def lead_edit(request, pk):
    lead = get_object_or_404(sales_only_or_admin(Lead.objects.all(), request.user), pk=pk)
    if request.method == "POST":
        form = LeadForm(request.POST, instance=lead, user=request.user)
        if form.is_valid():
            lead = form.save(commit=False)
            lead.updated_by = request.user
            lead.save()
            messages.success(request, "Lead updated.")
            return redirect("lead_detail", pk=lead.pk)
    else:
        form = LeadForm(instance=lead, user=request.user)
    return render(request, "leads/form.html", {"form": form, "title": f"Edit {lead.name}"})


@login_required
def lead_detail(request, pk):
    lead = get_object_or_404(sales_only_or_admin(Lead.objects.all(), request.user), pk=pk)
    activities = lead.activities.select_related("created_by")
    if request.method == "POST" and "add_activity" in request.POST:
        aform = ActivityForm(request.POST)
        if aform.is_valid():
            act = aform.save(commit=False)
            act.lead = lead
            act.created_by = request.user
            act.save()
            lead.updated_by = request.user
            lead.save()
            messages.success(request, "Activity added.")
            return redirect("lead_detail", pk=lead.pk)
    else:
        aform = ActivityForm()
    return render(request, "leads/detail.html", {
        "lead": lead, "activities": activities, "aform": aform,
    })


@login_required
def lead_archive(request, pk):
    lead = get_object_or_404(sales_only_or_admin(Lead.objects.all(), request.user), pk=pk)
    if not request.user.profile.is_admin:
        messages.error(request, "Only administrators can archive leads.")
        return redirect("lead_detail", pk=pk)
    lead.archived = True
    lead.save()
    messages.success(request, "Lead archived.")
    return redirect("lead_list")


# ---------- Follow-ups ----------
@login_required
def followup_list(request):
    leads = sales_only_or_admin(Lead.objects.filter(archived=False), request.user)
    activities = Activity.objects.filter(lead__in=leads).select_related("lead", "created_by")
    tab = request.GET.get("tab", "open")
    now = timezone.now()

    if tab == "open":
        activities = activities.filter(completed=False).order_by("due_at")
    elif tab == "overdue":
        activities = activities.filter(completed=False, due_at__lt=now).order_by("due_at")
    elif tab == "today":
        today_end = now.replace(hour=23, minute=59, second=59)
        activities = activities.filter(completed=False, due_at__gte=now, due_at__lte=today_end).order_by("due_at")
    elif tab == "done":
        activities = activities.filter(completed=True).order_by("-completed_at")
    else:
        activities = activities.order_by("-created_at")

    return render(request, "followups/list.html", {"activities": activities, "tab": tab})


@login_required
def activity_complete(request, pk):
    act = get_object_or_404(Activity, pk=pk)
    # scope check
    if not request.user.profile.is_admin and act.lead.owner != request.user and act.lead.created_by != request.user:
        raise Http404
    act.completed = True
    act.completed_at = timezone.now()
    act.save()
    messages.success(request, "Marked complete.")
    return redirect(request.META.get("HTTP_REFERER", "followup_list"))


# ---------- Reports ----------
@login_required
def reports(request):
    qs = sales_only_or_admin(Lead.objects.filter(archived=False), request.user)

    # New filters
    country = request.GET.get("country", "")
    city    = request.GET.get("city", "")
    if country: qs = qs.filter(country=country)
    if city:    qs = qs.filter(city=city)

    by_status  = list(qs.values("status").annotate(c=Count("id")))
    by_stage   = list(qs.values("stage").annotate(c=Count("id")).order_by("-c"))
    by_source  = list(qs.values("source").annotate(c=Count("id")).order_by("-c"))
    by_owner   = list(qs.values("owner__username").annotate(c=Count("id")).order_by("-c"))
    by_country = list(qs.exclude(country="").values("country").annotate(c=Count("id")).order_by("-c"))
    by_city    = list(qs.exclude(city="").values("city").annotate(c=Count("id")).order_by("-c"))

    total_value = qs.aggregate(s=Sum("value"))["s"] or 0

    countries = (Lead.objects.filter(archived=False)
                 .exclude(country="")
                 .values_list("country", flat=True).distinct().order_by("country"))
    cities = (Lead.objects.filter(archived=False)
              .exclude(city="")
              .values_list("city", flat=True).distinct().order_by("city"))

    return render(request, "reports/index.html", {
        "by_status": by_status,
        "by_stage": by_stage,
        "by_source": by_source,
        "by_owner": by_owner,
        "by_country": by_country,   # NEW
        "by_city": by_city,         # NEW
        "total_value": total_value,
        "country": country, "city": city,
        "countries": countries, "cities": cities,
    })


# ---------- Import / Export ----------
@login_required
@admin_required
def import_leads(request):
    if request.method == "POST":
        form = ImportForm(request.POST, request.FILES)
        if form.is_valid():
            created, skipped = import_leads_xlsx(request.FILES["file"], request.user)
            messages.success(request, f"Imported {created} leads, skipped {skipped}.")
            return redirect("lead_list")
    else:
        form = ImportForm()
    return render(request, "settings/import.html", {"form": form})


@login_required
def export_leads(request, fmt="xlsx"):
    qs = sales_only_or_admin(Lead.objects.filter(archived=False), request.user)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if fmt == "csv":
        resp = HttpResponse(content_type="text/csv")
        resp["Content-Disposition"] = f'attachment; filename="leads_{timestamp}.csv"'
        writer = csv.writer(resp)
        writer.writerow(["ID", "Name", "Company", "Email", "Phone", "Status",
                         "Stage", "Source", "Owner", "Value", "Created At"])
        for l in qs:
            writer.writerow([l.id, l.name, l.company, l.email, l.phone, l.status,
                             l.stage, l.source,
                             l.owner.username if l.owner else "",
                             l.value, l.created_at])
        return resp

    path = settings.DATA_DIR / "exports" / f"leads_{timestamp}.xlsx"
    export_leads_xlsx(qs, path)
    return FileResponse(open(path, "rb"), as_attachment=True, filename=path.name)


# ---------- Settings / Dropdowns ----------
@login_required
@admin_required
def settings_index(request):
    if request.method == "POST":
        form = DropdownOptionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Option added.")
            return redirect("settings_index")
    else:
        form = DropdownOptionForm()
    options = DropdownOption.objects.all()
    return render(request, "settings/index.html", {"form": form, "options": options})


@login_required
@admin_required
def option_delete(request, pk):
    DropdownOption.objects.filter(pk=pk).delete()
    messages.success(request, "Option deleted.")
    return redirect("settings_index")


# ---------- Backup ----------
@login_required
@admin_required
def backup_create(request):
    path = create_backup()
    messages.success(request, f"Backup created: {path.name}")
    return redirect("backup_list")


@login_required
@admin_required
def backup_list(request):
    folder = settings.DATA_DIR / "backups"
    files = sorted(folder.glob("*.zip"), key=lambda p: p.stat().st_mtime, reverse=True)
    return render(request, "settings/backups.html", {"files": files})


@login_required
@admin_required
def backup_download(request, name):
    path = settings.DATA_DIR / "backups" / name
    if not path.exists() or path.suffix != ".zip":
        raise Http404
    return FileResponse(open(path, "rb"), as_attachment=True, filename=name)