from django.urls import path

from apps.core.views.homepage_view import HomepageView
from apps.core.views.initial_check_view import initial_check
from apps.core.views.login_view import LoginView

urlpatterns = [
    path("check/", initial_check, name="initial-check"),
    path("login/", LoginView.as_view()),
    path("home/", HomepageView.as_view()),
]