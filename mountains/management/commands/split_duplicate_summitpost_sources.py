from django.core.management.base import BaseCommand
from django.utils.text import slugify

from mountains.models import ContentSection, ImportedPhoto, Peak, Route, SourceRecord, TripReport


class Command(BaseCommand):
    help = "Split peaks that accidentally have multiple SummitPost source object IDs attached."

    def handle(self, *args, **options):
        split_count = 0
        for peak in list(Peak.objects.all()):
            sources = list(
                peak.sources.filter(source_type=SourceRecord.SourceType.SUMMITPOST).order_by("created_at", "id")
            )
            if len(sources) <= 1:
                continue

            keeper = sources[0]
            for source in sources[1:]:
                new_peak = Peak.objects.create(
                    name=peak.name,
                    slug=self.unique_slug(peak.name, source.external_id),
                    state=peak.state,
                    country=peak.country,
                    range_name=peak.range_name,
                    location=peak.location,
                    elevation_ft=peak.elevation_ft,
                    prominence_ft=peak.prominence_ft,
                    latitude=peak.latitude,
                    longitude=peak.longitude,
                    summary=peak.summary,
                    owner_notes=peak.owner_notes,
                    is_public=peak.is_public,
                )
                source.peak = new_peak
                source.save()
                ContentSection.objects.filter(peak=peak, source=source).update(peak=new_peak)
                ImportedPhoto.objects.filter(peak=peak, source=source).update(peak=new_peak)
                TripReport.objects.filter(peak=peak, source=source).update(peak=new_peak)
                Route.objects.filter(peak=peak, source=source).update(peak=new_peak)
                split_count += 1
                self.stdout.write(f"Split {peak.name} source {source.external_id} -> {new_peak.slug}")

            self.stdout.write(f"Kept {peak.name} source {keeper.external_id} on {peak.slug}")

        self.stdout.write(self.style.SUCCESS(f"Split {split_count} duplicate SummitPost source records."))

    def unique_slug(self, name: str, external_id: str) -> str:
        base = slugify(f"{name}-{external_id}")
        slug = base
        index = 2
        while Peak.objects.filter(slug=slug).exists():
            slug = f"{base}-{index}"
            index += 1
        return slug
