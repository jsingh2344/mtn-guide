from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.text import slugify


class Peak(models.Model):
    name = models.CharField(max_length=160)
    slug = models.SlugField(max_length=180, unique=True, blank=True)
    state = models.CharField(max_length=80, default="Wyoming")
    country = models.CharField(max_length=80, default="United States")
    range_name = models.CharField(max_length=160, blank=True)
    location = models.CharField(max_length=220, blank=True)
    elevation_ft = models.PositiveIntegerField(null=True, blank=True)
    prominence_ft = models.PositiveIntegerField(null=True, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    summary = models.TextField(blank=True)
    owner_notes = models.TextField(blank=True)
    is_public = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("mountain-detail", kwargs={"slug": self.slug})

    def __str__(self):
        return self.name


class SourceRecord(models.Model):
    class SourceType(models.TextChoices):
        SUMMITPOST = "summitpost", "SummitPost"
        PEAKBAGGER = "peakbagger", "Peakbagger"
        SURVEY = "survey", "Survey source"
        OTHER = "other", "Other"

    peak = models.ForeignKey(Peak, related_name="sources", on_delete=models.CASCADE)
    source_type = models.CharField(max_length=24, choices=SourceType.choices)
    title = models.CharField(max_length=180)
    url = models.URLField()
    external_id = models.CharField(max_length=120, blank=True)
    last_fetched_at = models.DateTimeField(null=True, blank=True)
    raw_snapshot = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["source_type", "title"]

    def __str__(self):
        return f"{self.get_source_type_display()}: {self.title}"


class ContentSection(models.Model):
    class SectionType(models.TextChoices):
        OVERVIEW = "overview", "Overview"
        APPROACH = "approach", "Approach"
        RED_TAPE = "red_tape", "Red tape / permits"
        CAMPING = "camping", "Camping"
        PHOTOS = "photos", "Photos"
        COMMENTS = "comments", "Comments"
        EXTERNAL_LINKS = "external_links", "External links"
        OTHER = "other", "Other"

    peak = models.ForeignKey(Peak, related_name="content_sections", on_delete=models.CASCADE)
    source = models.ForeignKey(SourceRecord, related_name="content_sections", on_delete=models.SET_NULL, null=True, blank=True)
    section_type = models.CharField(max_length=32, choices=SectionType.choices)
    title = models.CharField(max_length=180)
    body = models.TextField()
    sort_order = models.PositiveIntegerField(default=0)
    is_imported = models.BooleanField(default=True)
    visible_to_public = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["sort_order", "title"]

    def __str__(self):
        return f"{self.peak}: {self.title}"


class ImportedPhoto(models.Model):
    peak = models.ForeignKey(Peak, related_name="imported_photos", on_delete=models.CASCADE)
    section = models.ForeignKey(
        ContentSection,
        related_name="photos",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    source = models.ForeignKey(SourceRecord, related_name="imported_photos", on_delete=models.SET_NULL, null=True, blank=True)
    image_url = models.URLField(max_length=600)
    source_page_url = models.URLField(max_length=600, blank=True)
    alt_text = models.CharField(max_length=260, blank=True)
    caption = models.CharField(max_length=500, blank=True)
    credit = models.CharField(max_length=180, blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    is_imported = models.BooleanField(default=True)
    visible_to_public = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["sort_order", "id"]
        unique_together = [("peak", "image_url")]

    def __str__(self):
        return self.caption or self.alt_text or self.image_url


class Route(models.Model):
    peak = models.ForeignKey(Peak, related_name="routes", on_delete=models.CASCADE)
    name = models.CharField(max_length=180)
    slug = models.SlugField(max_length=200, blank=True)
    yds_class = models.CharField(max_length=40, blank=True)
    snow_grade = models.CharField(max_length=80, blank=True)
    description = models.TextField(blank=True)
    source = models.ForeignKey(SourceRecord, related_name="routes", on_delete=models.SET_NULL, null=True, blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["peak", "sort_order", "name"]
        unique_together = [("peak", "slug")]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("route-detail", kwargs={"peak_slug": self.peak.slug, "route_slug": self.slug})

    def __str__(self):
        return f"{self.peak} - {self.name}"


class TripReport(models.Model):
    peak = models.ForeignKey(Peak, related_name="trip_reports", on_delete=models.CASCADE)
    route = models.ForeignKey(Route, related_name="trip_reports", on_delete=models.SET_NULL, null=True, blank=True)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="trip_reports", on_delete=models.SET_NULL, null=True, blank=True)
    source = models.ForeignKey(SourceRecord, related_name="trip_reports", on_delete=models.SET_NULL, null=True, blank=True)
    title = models.CharField(max_length=220)
    body = models.TextField()
    trip_date = models.DateField(null=True, blank=True)
    is_imported = models.BooleanField(default=False)
    visible_to_public = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-trip_date", "-created_at"]

    def __str__(self):
        return self.title


class SavedPeak(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="saved_peaks", on_delete=models.CASCADE)
    peak = models.ForeignKey(Peak, related_name="saved_by", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("user", "peak")]


class RouteAttempt(models.Model):
    class Outcome(models.TextChoices):
        PLANNED = "planned", "Planned"
        ATTEMPTED = "attempted", "Attempted"
        CLIMBED = "climbed", "Climbed"
        TURNED_AROUND = "turned_around", "Turned around"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="route_attempts", on_delete=models.CASCADE)
    peak = models.ForeignKey(Peak, related_name="route_attempts", on_delete=models.CASCADE)
    route = models.ForeignKey(Route, related_name="attempts", on_delete=models.CASCADE)
    outcome = models.CharField(max_length=24, choices=Outcome.choices)
    attempt_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-attempt_date", "-created_at"]

    def __str__(self):
        return f"{self.user} {self.get_outcome_display()} {self.route}"


class RouteRating(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="route_ratings", on_delete=models.CASCADE)
    route = models.ForeignKey(Route, related_name="ratings", on_delete=models.CASCADE)
    score = models.PositiveSmallIntegerField(help_text="1-5")
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("user", "route")]

    def __str__(self):
        return f"{self.route}: {self.score}/5"
