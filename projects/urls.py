from django.urls import path
from .views import *

urlpatterns = [
    path("partners/", PartnerListCreateView.as_view(), name="partner-list-create"),
    path("partners/<int:pk>/", PartnerDetailView.as_view(), name="partner-detail"),
    path("", ProjectListCreateView.as_view(), name="project-list-create"),
    path("<int:pk>/", ProjectDetailView.as_view(), name="project-detail"),
    
    path("updates/", ProjectUpdateListCreateView.as_view(), name="project-update-list-create"),
    path("updates/<int:pk>/", ProjectUpdateDetailView.as_view(), name="project-update-detail"),
    path("updates/images/", ProjectUpdateImageCreateView.as_view(), name="project-update-image-create"),
    path("updates/images/<int:pk>/", ProjectUpdateImageDeleteView.as_view(), name="project-update-image-delete"),

    path("interests/subscribe/", ProjectInterestSubscribeView.as_view(), name="project-interest-subscribe"),
    path("interests/unsubscribe/", ProjectInterestUnsubscribeView.as_view(), name="project-interest-unsubscribe"),
    path("interests/my/", MyProjectInterestsView.as_view(), name="my-project-interests"),
]