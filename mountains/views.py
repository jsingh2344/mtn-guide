from django.db.models import Avg, Count
from django.views.generic import DetailView, ListView

from .models import Peak, Route


class MountainListView(ListView):
    model = Peak
    context_object_name = "peaks"
    template_name = "mountains/mountain_list.html"
    paginate_by = 50

    def get_queryset(self):
        queryset = (
            Peak.objects.filter(is_public=True)
            .annotate(route_count=Count("routes"))
            .order_by("name")
        )
        query = self.request.GET.get("q", "").strip()
        if query:
            queryset = queryset.filter(name__icontains=query)
        return queryset


class MountainDetailView(DetailView):
    model = Peak
    context_object_name = "peak"
    template_name = "mountains/mountain_detail.html"

    def get_queryset(self):
        return Peak.objects.prefetch_related("sources", "content_sections__photos", "routes", "trip_reports", "imported_photos")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        sections = self.object.content_sections.all()
        reports = self.object.trip_reports.select_related("route", "author", "source")
        if not self.request.user.is_authenticated:
            sections = sections.filter(visible_to_public=True)
            reports = reports.filter(visible_to_public=True)
        context["sections"] = sections
        context["trip_reports"] = reports[:8]
        photos = self.object.imported_photos.select_related("section", "source")
        if not self.request.user.is_authenticated:
            photos = photos.filter(visible_to_public=True)
        context["photos"] = photos
        context["unsectioned_photos"] = photos.filter(section__isnull=True)
        context["hero_photo"] = photos.first()
        context["saved"] = (
            self.request.user.is_authenticated
            and self.object.saved_by.filter(user=self.request.user).exists()
        )
        return context


class RouteDetailView(DetailView):
    model = Route
    context_object_name = "route"
    template_name = "mountains/route_detail.html"
    slug_url_kwarg = "route_slug"

    def get_queryset(self):
        return (
            Route.objects.filter(peak__slug=self.kwargs["peak_slug"])
            .select_related("peak", "source")
            .prefetch_related("trip_reports", "attempts", "ratings")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["average_rating"] = self.object.ratings.aggregate(value=Avg("score"))["value"]
        context["attempts"] = self.object.attempts.select_related("user")[:12]
        reports = self.object.trip_reports.select_related("author", "source")
        if not self.request.user.is_authenticated:
            reports = reports.filter(visible_to_public=True)
        context["trip_reports"] = reports
        return context

# Create your views here.
