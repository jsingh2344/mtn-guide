# Wyoming Mountain Guide MVP Specification

## Product Goal

Build a semi-private mountain guidebook and tracking website that combines SummitPost written mountain information with Peakbagger-style objective peak statistics, then presents the result in a cleaner, more consistent format.

The initial audience is the site owner, with later use by mountaineers who need route, weather, access, and planning information, plus peakbaggers who want tracking features.

## MVP Scope

- Region: Wyoming
- Peak inclusion rule: 200+ feet of prominence
- Initial test peaks:
  - Grand Teton
  - Mount Moran
  - Gannett Peak
- Initial ingest strategy: start with the three test peaks, refine the parser and matching workflow, then scale to Wyoming 200+ ft prominence peaks
- Primary success criterion: SummitPost information is scraped, attributed, and presented in a clean, consistent guidebook format

## Public And Private Access

During the semi-private phase, not all pages require login.

Public users may see:

- Mountain metadata
- Source links
- Owner-written notes

Logged-in or approved users may see:

- Imported SummitPost-derived written content
- Imported SummitPost trip reports
- User activity and tracking details

If the site becomes public later, imported SummitPost-derived content should remain private or approved-user-only unless reuse terms allow broader publication.

## Source Data

### SummitPost

Use SummitPost for written guidebook-style content, shown as-is where possible.

Imported content should include:

- Overview
- Routes
- Approach
- Red tape / permits
- Camping
- Trip reports
- Photos, if feasible
- Comments, if useful
- External links

SummitPost content must retain prominent attribution and source links.

Imported SummitPost content should be editable inside the app.

### Peakbagger And Survey Sources

Use Peakbagger or appropriate surveying-style sources for objective statistics.

Target fields:

- Elevation
- Prominence
- Range
- Location
- Coordinates
- Peak lists, where available and useful
- Source links

Statistics should come from Peakbagger or surveying sources rather than SummitPost.

## Matching Strategy

SummitPost entries should be matched to Peakbagger entries primarily by coordinates.

Fallback matching may use:

- Name
- Range
- Elevation
- Location
- Manual review

Ambiguous matches should be flagged for human review. The first three test peaks should be used to validate the matching and parsing workflow before scaling.

## Data Storage

Store both:

- Raw source snapshots, for debugging, attribution, and future re-parsing
- Normalized records, for rendering pages and supporting search/filtering

Periodic refreshes are acceptable. The data does not need to update immediately when sources change. A later version may add a manual "refresh this mountain" action.

## Mountain Pages

Mountain pages should feel like a guidebook mixed with a dashboard.

Each mountain page should include:

- Name
- Elevation
- Prominence
- Range
- Location
- Coordinates
- Static map for MVP
- Source links
- Overview
- Approach
- Route options
- Red tape / permits
- Camping
- Photos, if feasible
- Trip reports
- User notes
- User activity summary

The design should sit between Peakbagger and Mountain Project:

- Denser and more data-rich than a marketing site
- Cleaner and more readable than SummitPost
- Desktop-first
- Mobile usable, but not the primary design target for MVP

## Route Pages

Routes should have their own subpages from the beginning.

Each route should support:

- Route name
- Parent mountain
- YDS class
- Snow grade
- Route description
- Source attribution
- Route-specific trip reports
- Route-specific attempts
- Route-specific completion tracking
- Route ratings

The scraper may begin with crude route extraction, but the app should support multiple routes per mountain in the data model from the start.

## Maps

MVP:

- Static map on mountain pages

Future:

- Interactive map
- Topographic tiles
- GPX/KML overlays
- Trailhead markers
- Route lines

OpenStreetMap/topographic tiles are sufficient for now.

## Search And Discovery

Eventually support Peakbagger-like discovery:

- Search by name
- Browse by state, range, or region
- Filter by elevation
- Filter by prominence
- Filter by difficulty
- Filter by list
- Map-based exploration

Duplicate mountain names should be handled well enough to preserve functionality, using location, range, coordinates, and source identifiers.

## Accounts And Social Tracking

User accounts are required for personal tracking features.

Users should be able to:

- Save mountains
- Mark mountains climbed
- Specify which route was climbed
- Track attempts on a route-by-route basis
- Rate routes
- Write their own trip reports

User climbs, attempts, ratings, and trip reports should be visible to other logged-in users.

## Editing

Users should be able to correct or enrich imported data.

Imported SummitPost content is editable, but the app should preserve:

- Original source attribution
- Source URL
- Raw source snapshot
- Edit history, if practical

## Recommended Technical Direction

Django + PostgreSQL is the preferred stack for the MVP because the project is data-heavy, scraper-heavy, account-based, and will benefit from Django admin for manual review.

Suggested components:

- Django web app
- PostgreSQL database
- Django admin for reviewing matches and editing imported content
- Background job system for scraping and periodic refreshes
- Server-rendered pages for the initial guidebook UI
- Static or server-generated map images for MVP

## Core System Areas

### Mountain Database

Canonical models for:

- Peaks
- Routes
- Locations/ranges
- Source records
- Objective statistics
- Imported content sections
- Trip reports
- User attempts
- User climbs
- User ratings

### Importer And Reviewer

Responsible for:

- Fetching SummitPost pages
- Fetching Peakbagger/stat source records
- Storing raw snapshots
- Parsing structured sections
- Matching SummitPost entries to Peakbagger peaks
- Flagging uncertain matches
- Supporting manual approval/rejection

### Guidebook App

Responsible for:

- Mountain pages
- Route pages
- Search and filtering
- Maps
- User notes
- Trip reports
- Peak and route tracking

## MVP Build Sequence

1. Create Django project and core data models.
2. Add user accounts and basic access rules.
3. Build admin screens for peaks, routes, sources, and imported content.
4. Manually seed or import Peakbagger-style data for Grand Teton, Mount Moran, and Gannett Peak.
5. Build SummitPost importer for the three test peaks.
6. Store raw snapshots and parsed content sections.
7. Build mountain detail pages.
8. Build route detail pages.
9. Add static maps.
10. Add save, climbed, attempt, route rating, and trip report features.
11. Review parser quality on the three test peaks.
12. Expand ingestion to Wyoming 200+ ft prominence peaks.

## Open Questions

- Which source should provide the canonical Wyoming 200+ ft prominence peak list?
- Should imported SummitPost photos be displayed directly, proxied, cached, or linked only?
- How much edit history is needed for imported content?
- What is the preferred hosting target after local MVP validation?
- Should the first version use Django templates only, or Django plus a small frontend layer for richer interactions?
