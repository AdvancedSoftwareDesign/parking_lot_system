from django.urls import path
from .views import initial_check

urlpatterns = [
    path("check/", initial_check, name="initial-check"),
]