from django.contrib import admin

from .models import (
    ContentSection,
    ImportedPhoto,
    Peak,
    Route,
    RouteAttempt,
    RouteRating,
    SavedPeak,
    SourceRecord,
    TripReport,
)


class SourceRecordInline(admin.TabularInline):
    model = SourceRecord
    extra = 0
    fields = ("source_type", "title", "url", "external_id", "last_fetched_at")


class ContentSectionInline(admin.StackedInline):
    model = ContentSection
    extra = 0
    fields = ("section_type", "title", "body", "sort_order", "is_imported", "visible_to_public", "source")


class ImportedPhotoInline(admin.TabularInline):
    model = ImportedPhoto
    extra = 0
    fields = ("image_url", "caption", "credit", "section", "sort_order", "visible_to_public")


class RouteInline(admin.TabularInline):
    model = Route
    extra = 0
    fields = ("name", "slug", "yds_class", "snow_grade", "sort_order", "source")


@admin.register(Peak)
class PeakAdmin(admin.ModelAdmin):
    list_display = ("name", "range_name", "elevation_ft", "prominence_ft", "location", "is_public")
    list_filter = ("state", "range_name", "is_public")
    search_fields = ("name", "range_name", "location")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [SourceRecordInline, RouteInline, ContentSectionInline, ImportedPhotoInline]


@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    list_display = ("name", "peak", "yds_class", "snow_grade")
    list_filter = ("peak", "yds_class", "snow_grade")
    search_fields = ("name", "peak__name", "description")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(SourceRecord)
class SourceRecordAdmin(admin.ModelAdmin):
    list_display = ("title", "peak", "source_type", "last_fetched_at")
    list_filter = ("source_type",)
    search_fields = ("title", "url", "peak__name", "external_id")


@admin.register(ContentSection)
class ContentSectionAdmin(admin.ModelAdmin):
    list_display = ("title", "peak", "section_type", "is_imported", "visible_to_public")
    list_filter = ("section_type", "is_imported", "visible_to_public")
    search_fields = ("title", "body", "peak__name")


@admin.register(ImportedPhoto)
class ImportedPhotoAdmin(admin.ModelAdmin):
    list_display = ("peak", "section", "caption", "credit", "visible_to_public")
    list_filter = ("visible_to_public", "is_imported", "peak")
    search_fields = ("caption", "credit", "alt_text", "image_url", "peak__name", "section__title")


@admin.register(TripReport)
class TripReportAdmin(admin.ModelAdmin):
    list_display = ("title", "peak", "route", "author", "trip_date", "is_imported", "visible_to_public")
    list_filter = ("is_imported", "visible_to_public", "peak")
    search_fields = ("title", "body", "peak__name", "route__name")


admin.site.register(SavedPeak)
admin.site.register(RouteAttempt)
admin.site.register(RouteRating)
