from django.urls import path
from .views import *

urlpatterns = [
    path("", BeneficiaryListCreateView.as_view(), name="beneficiary-list-create"),
    path("<int:pk>/", BeneficiaryDetailView.as_view(), name="beneficiary-detail"),
    path("images/", BeneficiaryImageCreateView.as_view(), name="beneficiary-image-create"),
    path("images/<int:pk>/", BeneficiaryImageDeleteView.as_view(), name="beneficiary-image-delete"),
]