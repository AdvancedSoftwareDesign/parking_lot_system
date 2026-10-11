from django.urls import path
from django.shortcuts import render, redirect
from django.contrib.auth.views import (
    LogoutView,
    PasswordResetView,
    PasswordResetDoneView,
    PasswordResetConfirmView,
    PasswordResetCompleteView,
)
from . import views


# Role home pages
path(
    'employee/home/',
    views.employee_home,
    name='employee_home',
),
path(
    'guard/home/',
    views.guard_home,
    name='guard_home',
),
path(
    'parking-admin/home/',
    views.admin_home,
    name='admin_home',
),


def login_success_view(request):
    if not request.user.is_authenticated:
        return redirect('login')

    return render(request, 'accounts/login_success.html')


urlpatterns = [
    # Login
    path('login/', views.login_view, name='login'),

    # Login success
    path('login/success/', login_success_view, name='login_success'),

    # Logout
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),

    # Role home pages
    path('employee/home/', views.employee_home, name='employee_home'),
    path('guard/home/', views.guard_home, name='guard_home'),
    path('parking-admin/home/', views.admin_home, name='admin_home'),

    # Password reset
    path(
        'password-reset/',
        PasswordResetView.as_view(
            template_name='accounts/password_reset.html',
            email_template_name='accounts/password_reset_email.html',
            subject_template_name='accounts/password_reset_subject.txt',
            success_url='/accounts/password-reset/done/',
        ),
        name='password_reset',
    ),
    path(
        'password-reset/done/',
        PasswordResetDoneView.as_view(
            template_name='accounts/password_reset_done.html',
        ),
        name='password_reset_done',
    ),
    path(
        'reset/<uidb64>/<token>/',
        PasswordResetConfirmView.as_view(
            template_name='accounts/password_reset_confirm.html',
            success_url='/accounts/reset/complete/',
        ),
        name='password_reset_confirm',
    ),
    path(
        'reset/complete/',
        PasswordResetCompleteView.as_view(
            template_name='accounts/password_reset_complete.html',
        ),
        name='password_reset_complete',
    ),
]
