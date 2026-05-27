import time

from django.core.management.base import BaseCommand
from django.db import IntegrityError
from django.utils import timezone
from django.utils.text import slugify

from mountains.models import ContentSection, ImportedPhoto, Peak, Route, SourceRecord, TripReport
from mountains.services.importers import (
    fetch_source_snapshot,
    parse_summitpost_child_links,
    parse_summitpost_object_list,
    parse_summitpost_photos,
    parse_summitpost_routes,
    parse_summitpost_sections,
    parse_summitpost_state_area_links,
    parse_summitpost_trip_report_titles,
)


COUNTRY_NAME = "Peru"
COUNTRY_URL = "https://www.summitpost.org/country/Peru.html"
LIST_START_URL = "https://www.summitpost.org/sub_country-1-Peru.html"


class Command(BaseCommand):
    help = "Discover and import SummitPost Peru mountain/rock pages."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument("--limit", type=int, default=None)
        parser.add_argument("--target-count", type=int, default=None)
        parser.add_argument("--delay", type=float, default=0.15)

    def handle(self, *args, **options):
        entries = self.discover_entries(
            target_count=options["target_count"],
            delay=options["delay"],
        )
        if options["limit"]:
            entries = entries[: options["limit"]]

        self.stdout.write(f"Discovered {len(entries)} Peru SummitPost entries.")
        if options["dry_run"]:
            for entry in entries[:30]:
                self.stdout.write(f"  {entry['object_id']} {entry['name']} - {entry['url']}")
            if len(entries) > 30:
                self.stdout.write(f"  ... {len(entries) - 30} more")
            return

        imported = 0
        for index, entry in enumerate(entries, start=1):
            self.stdout.write(f"[{index}/{len(entries)}] Importing {entry['name']} ({entry['object_id']})")
            try:
                self.import_entry(entry)
            except Exception as exc:
                self.stderr.write(self.style.ERROR(f"Failed {entry['name']}: {exc}"))
                continue
            imported += 1
            if options["delay"]:
                time.sleep(options["delay"])

        self.stdout.write(self.style.SUCCESS(f"Imported {imported} Peru SummitPost entries."))

    def discover_entries(self, target_count: int | None, delay: float) -> list[dict[str, str]]:
        result = fetch_source_snapshot(LIST_START_URL)
        entries, total = parse_summitpost_object_list(result.body, LIST_START_URL)
        seen_mountains = {entry["object_id"] for entry in entries}
        target = target_count or total
        self.stdout.write(f"Country index page: {len(entries)} entries; target {target or 'unknown'}")

        country = fetch_source_snapshot(COUNTRY_URL)
        area_queue = parse_summitpost_state_area_links(country.body, COUNTRY_URL)
        seen_areas = set()
        area_pages_read = 0

        while area_queue:
            if target and len(entries) >= target:
                break
            area = area_queue.pop(0)
            if area["object_id"] in seen_areas:
                continue
            seen_areas.add(area["object_id"])
            area_pages_read += 1
            if delay:
                time.sleep(delay)

            result = fetch_source_snapshot(area["url"], referer=COUNTRY_URL)
            mountain_links = parse_summitpost_child_links(result.body, area["url"], "Mountains & Rocks")
            child_areas = []
            self.stdout.write(
                f"Area {area_pages_read}: {area['name']} - "
                f"{len(mountain_links)} mountains, {len(child_areas)} child areas"
            )

            for entry in mountain_links:
                if entry["object_id"] in seen_mountains:
                    continue
                seen_mountains.add(entry["object_id"])
                entry["parent"] = area["name"]
                entry["location"] = "Peru, South America"
                entries.append(entry)
                if target and len(entries) >= target:
                    break

        return entries

    def import_entry(self, entry: dict[str, str]) -> Peak:
        peak = self.find_or_create_peak(entry)
        result = fetch_source_snapshot(entry["url"], referer=LIST_START_URL)
        sections = parse_summitpost_sections(result.body)
        photos = parse_summitpost_photos(result.body, entry["url"])
        routes = parse_summitpost_routes(result.body)
        trip_report_titles = parse_summitpost_trip_report_titles(result.body)

        source, _ = SourceRecord.objects.update_or_create(
            peak=peak,
            source_type=SourceRecord.SourceType.SUMMITPOST,
            external_id=entry["object_id"],
            defaults={
                "title": f"{peak.name} : SummitPost",
                "url": entry["url"],
                "last_fetched_at": timezone.now(),
                "raw_snapshot": result.body,
            },
        )

        ContentSection.objects.filter(peak=peak, source=source, is_imported=True).delete()
        ImportedPhoto.objects.filter(peak=peak, source=source, is_imported=True).delete()

        sections_by_title = {}
        for section in sections:
            content_section = ContentSection.objects.create(
                peak=peak,
                source=source,
                section_type=section["section_type"],
                title=section["title"],
                body=section["body"],
                sort_order=section["sort_order"],
                is_imported=True,
                visible_to_public=False,
            )
            sections_by_title[section["title"].lower().strip()] = content_section

        for index, photo in enumerate(photos, start=1):
            ImportedPhoto.objects.create(
                peak=peak,
                section=sections_by_title.get(photo["section_title"].lower().strip()),
                source=source,
                image_url=photo["image_url"],
                source_page_url=photo["source_page_url"],
                alt_text=photo["alt_text"],
                caption=photo["caption"],
                credit=photo["credit"],
                sort_order=index,
                is_imported=True,
                visible_to_public=False,
            )

        existing_route_slugs = set(peak.routes.values_list("slug", flat=True))
        for index, route_data in enumerate(routes, start=1):
            route_slug = slugify(route_data["name"])
            if route_slug in existing_route_slugs:
                continue
            Route.objects.create(
                peak=peak,
                name=route_data["name"],
                slug=route_slug,
                source=source,
                sort_order=100 + index,
            )
            existing_route_slugs.add(route_slug)

        TripReport.objects.filter(peak=peak, source=source, is_imported=True).delete()
        for title in trip_report_titles:
            TripReport.objects.create(
                peak=peak,
                title=title,
                body="Imported SummitPost trip report title. Full trip report import is a later parser step.",
                source=source,
                is_imported=True,
                visible_to_public=False,
            )

        return peak

    def find_or_create_peak(self, entry: dict[str, str]) -> Peak:
        existing_source = SourceRecord.objects.select_related("peak").filter(
            source_type=SourceRecord.SourceType.SUMMITPOST,
            external_id=entry["object_id"],
        ).first()
        if existing_source:
            peak = existing_source.peak
            peak.name = entry["name"]
            peak.country = COUNTRY_NAME
            peak.range_name = peak.range_name or entry["parent"]
            peak.location = peak.location or entry["location"]
            peak.save()
            return peak

        slug = slugify(entry["name"])
        if Peak.objects.filter(slug=slug).exists():
            slug = slugify(f"{entry['name']}-{entry['object_id']}")

        peak = Peak(
            name=entry["name"],
            slug=slug,
            state="",
            country=COUNTRY_NAME,
            range_name=entry["parent"],
            location=entry["location"],
            summary="Imported from SummitPost Peru mountain/rock index.",
            is_public=True,
        )
        try:
            peak.save()
        except IntegrityError:
            peak.slug = slugify(f"{entry['name']}-{entry['object_id']}")
            peak.save()
        return peak
