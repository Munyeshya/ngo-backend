from django.urls import path
from .views import (
    DonationListCreateView,
    DonationDetailView,
    DonationTypeSupportAnalyticsView,
    MyDonationsView,
)

urlpatterns = [
    path("", DonationListCreateView.as_view(), name="donation-list-create"),
    path("type-support-analytics/", DonationTypeSupportAnalyticsView.as_view(), name="donation-type-support-analytics"),
    path("my/", MyDonationsView.as_view(), name="my-donations"),
    path("<int:pk>/", DonationDetailView.as_view(), name="donation-detail"),
]
