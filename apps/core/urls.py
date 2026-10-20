from django.urls import path
from .views import initial_check, capacity_status, set_capacity

urlpatterns = [
    path("check/", initial_check, name="initial-check"),
    path("capacity/", capacity_status, name="capacity-status"),
    path("capacity/set/", set_capacity, name="set-capacity"),
]
