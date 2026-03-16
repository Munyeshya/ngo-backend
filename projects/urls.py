from django.urls import path
from .views import PartnerListCreateView, ProjectListCreateView

urlpatterns = [
    path("partners/", PartnerListCreateView.as_view(), name="partner-list-create"),
    path("", ProjectListCreateView.as_view(), name="project-list-create"),
]