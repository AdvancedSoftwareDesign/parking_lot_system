from django.contrib import admin
from django.urls import path, include


urlpatterns = [
    path('admin/', admin.site.urls),
    path("api/accounts/", include("apps.accounts.api_urls")),
    path("api/", include("apps.core.urls")),
]
