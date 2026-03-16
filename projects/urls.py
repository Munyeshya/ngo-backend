from django.urls import path
from .views import *

urlpatterns = [
    path("partners/", PartnerListCreateView.as_view(), name="partner-list-create"),
    path("partners/<int:pk>/", PartnerDetailView.as_view(), name="partner-detail"),
    path("", ProjectListCreateView.as_view(), name="project-list-create"),
    path("<int:pk>/", ProjectDetailView.as_view(), name="project-detail"),
]