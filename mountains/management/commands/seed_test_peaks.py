from django.core.management.base import BaseCommand

from mountains.models import ContentSection, Peak, Route, SourceRecord, TripReport


TEST_PEAKS = [
    {
        "name": "Grand Teton",
        "range_name": "Teton Range",
        "location": "Grand Teton National Park",
        "elevation_ft": 13775,
        "prominence_ft": 6530,
        "latitude": 43.741200,
        "longitude": -110.802400,
        "summary": "The central test case for the guide: a major alpine objective with many route, access, and trip-report records to normalize.",
        "routes": [
            ("Owen-Spalding Route", "Class 5.4", "Seasonal snow", "The standard route placeholder. Imported text will replace this once the SummitPost parser is connected."),
            ("Upper Exum Ridge", "Class 5.5", "Seasonal snow", "Classic ridge route placeholder for route-page testing."),
        ],
    },
    {
        "name": "Mount Moran",
        "range_name": "Teton Range",
        "location": "Grand Teton National Park",
        "elevation_ft": 12610,
        "prominence_ft": 2420,
        "latitude": 43.835000,
        "longitude": -110.776700,
        "summary": "A large Teton objective useful for testing access notes, route variation, and approach-heavy guide content.",
        "routes": [
            ("CMC Route", "Class 5.5", "Seasonal snow", "Placeholder for the major Mount Moran route until imported source content is parsed."),
        ],
    },
    {
        "name": "Gannett Peak",
        "range_name": "Wind River Range",
        "location": "Fremont / Sublette County high point",
        "elevation_ft": 13810,
        "prominence_ft": 7076,
        "latitude": 43.184200,
        "longitude": -109.654200,
        "summary": "Wyoming high point and the long-approach test case for expedition-style access, glacier, and snow-route content.",
        "routes": [
            ("Gooseneck Glacier Route", "Class 3", "Snow climb", "Placeholder for the common Gannett route until imported source content is parsed."),
        ],
    },
]


class Command(BaseCommand):
    help = "Seed the three MVP test peaks and skeletal routes."

    def handle(self, *args, **options):
        for peak_data in TEST_PEAKS:
            routes = peak_data.pop("routes")
            peak, _ = Peak.objects.update_or_create(
                name=peak_data["name"],
                defaults=peak_data,
            )

            summitpost, _ = SourceRecord.objects.update_or_create(
                peak=peak,
                source_type=SourceRecord.SourceType.SUMMITPOST,
                title=f"SummitPost search for {peak.name}",
                defaults={
                    "url": f"https://www.summitpost.org/search?q={peak.name.replace(' ', '%20')}",
                    "raw_snapshot": "",
                },
            )
            SourceRecord.objects.update_or_create(
                peak=peak,
                source_type=SourceRecord.SourceType.PEAKBAGGER,
                title=f"Peakbagger search for {peak.name}",
                defaults={
                    "url": f"https://www.peakbagger.com/search.aspx?tid=R&ss={peak.name.replace(' ', '%20')}",
                    "raw_snapshot": "",
                },
            )

            ContentSection.objects.update_or_create(
                peak=peak,
                section_type=ContentSection.SectionType.OVERVIEW,
                title="Overview",
                defaults={
                    "body": "Imported SummitPost overview text will appear here as-is after the scraper is connected.",
                    "source": summitpost,
                    "sort_order": 10,
                    "is_imported": True,
                    "visible_to_public": False,
                },
            )
            ContentSection.objects.update_or_create(
                peak=peak,
                section_type=ContentSection.SectionType.APPROACH,
                title="Approach",
                defaults={
                    "body": "Imported approach details will appear here.",
                    "source": summitpost,
                    "sort_order": 20,
                    "is_imported": True,
                    "visible_to_public": False,
                },
            )

            for index, (name, yds_class, snow_grade, description) in enumerate(routes, start=1):
                route, _ = Route.objects.update_or_create(
                    peak=peak,
                    name=name,
                    defaults={
                        "yds_class": yds_class,
                        "snow_grade": snow_grade,
                        "description": description,
                        "source": summitpost,
                        "sort_order": index,
                    },
                )
                TripReport.objects.update_or_create(
                    peak=peak,
                    route=route,
                    title=f"Imported trip reports for {route.name}",
                    defaults={
                        "body": "Imported SummitPost trip reports will be attached here once the parser is connected.",
                        "source": summitpost,
                        "is_imported": True,
                        "visible_to_public": False,
                    },
                )

            self.stdout.write(self.style.SUCCESS(f"Seeded {peak.name}"))
