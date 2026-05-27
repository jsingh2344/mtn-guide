from django.urls import path

from .views import MountainDetailView, MountainListView, RouteDetailView

urlpatterns = [
    path("", MountainListView.as_view(), name="mountain-list"),
    path("mountains/<slug:slug>/", MountainDetailView.as_view(), name="mountain-detail"),
    path("mountains/<slug:peak_slug>/routes/<slug:route_slug>/", RouteDetailView.as_view(), name="route-detail"),
]
