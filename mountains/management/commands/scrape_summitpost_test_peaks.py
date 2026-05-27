from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.utils.text import slugify

from mountains.models import ContentSection, ImportedPhoto, Peak, Route, SourceRecord, TripReport
from mountains.services.importers import (
    fetch_source_snapshot,
    parse_summitpost_photos,
    parse_summitpost_routes,
    parse_summitpost_sections,
    parse_summitpost_trip_report_titles,
)


SUMMITPOST_URLS = {
    "Grand Teton": "https://www.summitpost.org/grand-teton/150312",
    "Mount Moran": "https://www.summitpost.org/mount-moran/151412",
    "Gannett Peak": "https://www.summitpost.org/gannett-peak/150362",
}


class Command(BaseCommand):
    help = "Fetch and parse SummitPost pages for the three MVP test peaks."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Fetch and parse pages without updating the database.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]

        for peak_name, url in SUMMITPOST_URLS.items():
            try:
                peak = Peak.objects.get(name=peak_name)
            except Peak.DoesNotExist as exc:
                raise CommandError(f"Peak not found. Run seed_test_peaks first: {peak_name}") from exc

            self.stdout.write(f"Fetching {peak_name}: {url}")
            result = fetch_source_snapshot(url)
            sections = parse_summitpost_sections(result.body)
            photos = parse_summitpost_photos(result.body, url)
            routes = parse_summitpost_routes(result.body)
            trip_report_titles = parse_summitpost_trip_report_titles(result.body)

            self.stdout.write(
                f"Parsed {len(sections)} sections, {len(photos)} photos, {len(routes)} route candidates, "
                f"{len(trip_report_titles)} trip report titles."
            )

            if dry_run:
                for section in sections[:8]:
                    self.stdout.write(f"  section: {section['title']} ({section['section_type']})")
                for photo in photos[:8]:
                    label = photo["caption"] or photo["alt_text"] or photo["image_url"]
                    self.stdout.write(f"  photo: {photo['section_title'] or 'Unsectioned'} - {label}")
                for route in routes[:12]:
                    self.stdout.write(f"  route: {route['name']}")
                continue

            source, _ = SourceRecord.objects.update_or_create(
                peak=peak,
                source_type=SourceRecord.SourceType.SUMMITPOST,
                external_id=url.rsplit("/", 1)[-1],
                defaults={
                    "title": f"{peak.name} : SummitPost",
                    "url": url,
                    "last_fetched_at": timezone.now(),
                    "raw_snapshot": result.body,
                },
            )

            ContentSection.objects.filter(
                peak=peak,
                is_imported=True,
                body__startswith="Imported SummitPost",
            ).delete()
            ContentSection.objects.filter(
                peak=peak,
                is_imported=True,
                body__startswith="Imported approach details",
            ).delete()
            ImportedPhoto.objects.filter(peak=peak, source=source, is_imported=True).delete()
            TripReport.objects.filter(
                peak=peak,
                is_imported=True,
                body__startswith="Imported SummitPost trip reports will",
            ).delete()
            SourceRecord.objects.filter(
                peak=peak,
                source_type=SourceRecord.SourceType.SUMMITPOST,
                title__startswith="SummitPost search",
            ).delete()

            ContentSection.objects.filter(peak=peak, source=source, is_imported=True).delete()
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
                section = sections_by_title.get(photo["section_title"].lower().strip())
                ImportedPhoto.objects.create(
                    peak=peak,
                    section=section,
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
                slug = slugify(route_data["name"])
                if slug in existing_route_slugs:
                    continue
                Route.objects.create(
                    peak=peak,
                    name=route_data["name"],
                    slug=slug,
                    source=source,
                    sort_order=100 + index,
                )
                existing_route_slugs.add(slug)

            for title in trip_report_titles:
                TripReport.objects.update_or_create(
                    peak=peak,
                    title=title,
                    is_imported=True,
                    defaults={
                        "body": "Imported SummitPost trip report title. Full trip report import is a later parser step.",
                        "source": source,
                        "visible_to_public": False,
                    },
                )

            self.stdout.write(self.style.SUCCESS(f"Imported SummitPost content for {peak.name}"))
