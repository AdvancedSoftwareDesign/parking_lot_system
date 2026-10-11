from django.urls import path
from . import api_views

urlpatterns = [
    path("login/", api_views.api_login, name="api_login"),
    path("me/", api_views.api_me, name="api_me"),
    path("logout/", api_views.api_logout, name="api_logout"),
    path("employee/", api_views.api_employee, name="api_employee"),
    path("guard/", api_views.api_guard, name="api_guard"),
    path("admin/", api_views.api_admin, name="api_admin"),
]
