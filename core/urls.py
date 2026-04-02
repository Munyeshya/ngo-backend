from django.urls import path
from .views import HealthCheckView, api_documentation_view

urlpatterns = [
    path("", api_documentation_view, name="api-documentation"),
    path("health/", HealthCheckView.as_view(), name="health-check"),
]
