from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .forms import UserCreateForm, UserEditForm


def admin_required(view_func):
    return user_passes_test(lambda u: u.is_authenticated and u.profile.is_admin)(view_func)


@login_required
@admin_required
def user_list(request):
    users = User.objects.select_related("profile").order_by("username")
    return render(request, "users/list.html", {"users": users})


@login_required
@admin_required
def user_create(request):
    if request.method == "POST":
        form = UserCreateForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "User created.")
            return redirect("user_list")
    else:
        form = UserCreateForm()
    return render(request, "users/form.html", {"form": form, "title": "Add User"})


@login_required
@admin_required
def user_edit(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == "POST":
        form = UserEditForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "User updated.")
            return redirect("user_list")
    else:
        form = UserEditForm(instance=user)
    return render(request, "users/form.html", {"form": form, "title": f"Edit {user.username}"})