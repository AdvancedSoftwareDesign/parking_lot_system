from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render, redirect
from django.views.decorators.cache import never_cache


def get_role_url(user):
    """Return the home page URL name for the user's group."""
    if user.groups.filter(name="Employee").exists():
        return "employee_home"

    if user.groups.filter(name="Security Guard").exists():
        return "guard_home"

    if user.groups.filter(name="Parking Administrator").exists():
        return "admin_home"

    return None


def login_view(request):
    if request.user.is_authenticated:
        role_url = get_role_url(request.user)

        if role_url:
            return redirect(role_url)

        # Clear the session for an authenticated user without a role.
        logout(request)

    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)

        if form.is_valid():
            user = form.get_user()
            role_url = get_role_url(user)

            if role_url:
                login(request, user)
                return redirect(role_url)

            return render(
                request,
                "accounts/access_denied.html",
                status=403,
            )
    else:
        form = AuthenticationForm()

    return render(request, "accounts/login.html", {"form": form})


def role_home(request, group_name, title):
    if not request.user.groups.filter(name=group_name).exists():
        return render(
            request,
            "accounts/access_denied.html",
            status=403,
        )

    return render(
        request,
        "accounts/role_home.html",
        {"role_title": title},
    )


@never_cache
@login_required(login_url="login")
def employee_home(request):
    return role_home(request, "Employee", "Employee Home")


@never_cache
@login_required(login_url="login")
def guard_home(request):
    return role_home(request, "Security Guard", "Security Guard Home")


@never_cache
@login_required(login_url="login")
def admin_home(request):
    return role_home(
        request,
        "Parking Administrator",
        "Parking Administrator Home",
    )
