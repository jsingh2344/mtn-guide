import re
from dataclasses import dataclass
from html import unescape
from html.parser import HTMLParser
from urllib.parse import urljoin
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class FetchResult:
    url: str
    body: str


def fetch_source_snapshot(url: str, timeout: int = 20, referer: str = "") -> FetchResult:
    headers = {
        "User-Agent": "Mozilla/5.0 WyomingMountainGuide/0.1",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    if referer:
        headers["Referer"] = referer
    request = Request(url, headers=headers)
    with urlopen(request, timeout=timeout) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return FetchResult(url=url, body=response.read().decode(charset, errors="replace"))


def strip_tags(value: str) -> str:
    return " ".join(re.sub(r"<[^>]+>", " ", unescape(value)).split())


def parse_summitpost_object_list(html: str, base_url: str) -> tuple[list[dict[str, str]], int | None]:
    total_match = re.search(r"Viewing:\s*\d+-\d+\s+of\s+(\d+)", html)
    total = int(total_match.group(1)) if total_match else None
    entries: list[dict[str, str]] = []

    for match in re.finditer(r'<div class="item" object-id="(?P<object_id>\d+)">(?P<body>.*?)</li>', html, re.S):
        body = match.group("body")
        title_match = re.search(
            r'<a href="(?P<href>[^"]+)">\s*<h3 class="item-name">(?P<name>.*?)</h3>',
            body,
            re.S,
        )
        if not title_match:
            continue
        parent_match = re.search(r"Parent:\s*<a[^>]*>(?P<parent>.*?)</a>", body, re.S)
        location_match = re.search(r'<span class="location-label">\s*(?P<location>.*?)\s*</span>', body, re.S)
        image_match = re.search(r"<li[^>]+background-image:\s*url\('(?P<image>[^']+)'\)", match.group(0), re.S)
        entries.append(
            {
                "object_id": match.group("object_id"),
                "name": strip_tags(title_match.group("name")),
                "url": urljoin(base_url, unescape(title_match.group("href"))),
                "parent": strip_tags(parent_match.group("parent")) if parent_match else "",
                "location": strip_tags(location_match.group("location")) if location_match else "",
                "thumbnail_url": image_match.group("image") if image_match else "",
            }
        )

    return entries, total


def parse_summitpost_pagination_urls(html: str, base_url: str) -> list[str]:
    urls = []
    for href in re.findall(r'href="([^"]*object_list\.php[^"]*)"', html):
        url = urljoin(base_url, unescape(href))
        if url not in urls:
            urls.append(url)
    return urls


def parse_summitpost_state_area_links(html: str, base_url: str) -> list[dict[str, str]]:
    links: list[dict[str, str]] = []
    for match in re.finditer(
        r"/object_list\.php\?parent_id=(?P<object_id>\d+)(?:&amp;|&)object_type=1[^>]*>(?P<name>.*?)</a>\s*\((?P<count>\d+)\)",
        html,
        re.S,
    ):
        name = strip_tags(match.group("name"))
        object_id = match.group("object_id")
        links.append(
            {
                "object_id": object_id,
                "name": name,
                "url": urljoin(base_url, f"/{slugify_for_url(name)}/{object_id}"),
                "count": match.group("count"),
            }
        )
    return links


def parse_summitpost_child_links(html: str, base_url: str, category_label: str) -> list[dict[str, str]]:
    category_index = html.find(category_label)
    if category_index == -1:
        return []
    next_head = html.find('<div class="head">', category_index + len(category_label))
    segment = html[category_index:next_head if next_head != -1 else len(html)]
    links: list[dict[str, str]] = []
    for href, object_id, name in re.findall(r"<a href=['\"](?P<href>/[^'\"]+/(?P<object_id>\d+))['\"]>(?P<name>.*?)</a>", segment, re.S):
        if href.startswith("/object_list.php"):
            continue
        links.append(
            {
                "object_id": object_id,
                "name": strip_tags(name),
                "url": urljoin(base_url, href),
            }
        )
    return links


def slugify_for_url(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


class SummitPostTextParser(HTMLParser):
    block_tags = {
        "article",
        "aside",
        "blockquote",
        "br",
        "dd",
        "div",
        "dl",
        "dt",
        "figcaption",
        "footer",
        "h1",
        "h2",
        "h3",
        "h4",
        "header",
        "li",
        "main",
        "ol",
        "p",
        "section",
        "table",
        "td",
        "th",
        "tr",
        "ul",
    }
    ignored_tags = {"script", "style", "noscript", "svg"}
    heading_tags = {"h1", "h2", "h3", "h4"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.lines: list[str] = []
        self.current: list[str] = []
        self.ignored_depth = 0
        self.heading_tag = ""

    def handle_starttag(self, tag: str, attrs):
        if tag in self.ignored_tags:
            self.ignored_depth += 1
            return
        if tag in self.block_tags:
            self._flush()
        if tag in self.heading_tags:
            self.heading_tag = tag

    def handle_endtag(self, tag: str):
        if tag in self.ignored_tags and self.ignored_depth:
            self.ignored_depth -= 1
            return
        if tag in self.block_tags:
            self._flush()
        if tag == self.heading_tag:
            self.heading_tag = ""

    def handle_data(self, data: str):
        if self.ignored_depth:
            return
        text = " ".join(data.split())
        if not text:
            return
        if self.heading_tag:
            level = int(self.heading_tag[1])
            self.current.append(f"{'#' * level} {text}")
        else:
            self.current.append(text)

    def get_lines(self) -> list[str]:
        self._flush()
        return [line for line in self.lines if line]

    def _flush(self):
        if not self.current:
            return
        line = " ".join(self.current).strip()
        self.current = []
        if not line:
            return
        if not self.lines or self.lines[-1] != line:
            self.lines.append(line)


def html_to_lines(html: str) -> list[str]:
    parser = SummitPostTextParser()
    parser.feed(html)
    return parser.get_lines()


class SummitPostPhotoParser(HTMLParser):
    ignored_tags = {"script", "style", "noscript", "svg"}
    heading_tags = {"h2", "h3"}

    def __init__(self, base_url: str):
        super().__init__(convert_charrefs=True)
        self.base_url = base_url
        self.ignored_depth = 0
        self.heading_tag = ""
        self.heading_parts: list[str] = []
        self.current_heading = ""
        self.photos: list[dict[str, str]] = []

    def handle_starttag(self, tag: str, attrs):
        if tag in self.ignored_tags:
            self.ignored_depth += 1
            return
        if self.ignored_depth:
            return
        if tag in self.heading_tags:
            self.heading_tag = tag
            self.heading_parts = []
            return
        if tag == "img":
            attr_map = dict(attrs)
            image_url = attr_map.get("data-src") or attr_map.get("src") or ""
            if not self._is_content_image(image_url):
                return
            self.photos.append(
                {
                    "section_title": self.current_heading,
                    "image_url": urljoin(self.base_url, image_url),
                    "source_page_url": urljoin(self.base_url, attr_map.get("data-href") or ""),
                    "alt_text": unescape(attr_map.get("alt") or attr_map.get("title") or "").strip(),
                    "caption": "",
                    "credit": "",
                }
            )

    def handle_endtag(self, tag: str):
        if tag in self.ignored_tags and self.ignored_depth:
            self.ignored_depth -= 1
            return
        if tag == self.heading_tag:
            self.current_heading = " ".join(self.heading_parts).strip()
            self.heading_tag = ""
            self.heading_parts = []

    def handle_data(self, data: str):
        if self.ignored_depth:
            return
        text = " ".join(data.split()).strip()
        if not text:
            return
        if self.heading_tag:
            self.heading_parts.append(text)
            return
        if not self.photos:
            return
        latest = self.photos[-1]
        if latest["credit"]:
            return
        if len(text) > 180:
            return
        lowered = text.lower()
        if "photo by" in lowered or "photo credit" in lowered or "photo and editing by" in lowered:
            latest["credit"] = text

    def _is_content_image(self, image_url: str) -> bool:
        if not image_url:
            return False
        blocked = (
            "/styles/",
            "/responsive/images/icon-",
            "adpushup",
            "facebook",
            "doubleclick",
        )
        if any(marker in image_url for marker in blocked):
            return False
        if "images-sp.summitpost.org" in image_url and ("w-75" in image_url or "w-100" in image_url):
            return False
        return image_url.lower().endswith((".jpg", ".jpeg", ".png", ".webp")) or "images-sp.summitpost.org" in image_url


def parse_summitpost_photos(html: str, base_url: str) -> list[dict[str, str]]:
    parser = SummitPostPhotoParser(base_url)
    parser.feed(html)
    seen: set[str] = set()
    photos: list[dict[str, str]] = []
    for photo in parser.photos:
        if photo["image_url"] in seen:
            continue
        seen.add(photo["image_url"])
        if not photo["caption"] and photo["alt_text"]:
            photo["caption"] = photo["alt_text"]
        photos.append(photo)
    return photos


SECTION_TYPE_BY_TITLE = {
    "overview": "overview",
    "getting there": "approach",
    "standard approaches": "approach",
    "driving directions": "approach",
    "red tape": "red_tape",
    "camping": "camping",
    "images": "photos",
    "external links": "external_links",
    "additions and corrections": "comments",
    "comments": "comments",
}


def parse_summitpost_sections(html: str) -> list[dict[str, str | int]]:
    lines = html_to_lines(html)
    sections: list[dict[str, str | int]] = []
    current_title = ""
    current_level = 0
    current_body: list[str] = []
    current_order = 0

    def push_section():
        nonlocal current_body, current_order
        body = "\n\n".join(current_body).strip()
        if not current_title:
            current_body = []
            return
        if not body:
            current_body = []
            return
        key = current_title.lower().replace("&", "and").strip()
        sections.append(
            {
                "title": current_title,
                "section_type": SECTION_TYPE_BY_TITLE.get(key, "other"),
                "body": body,
                "sort_order": current_order,
            }
        )
        current_body = []

    for line in lines:
        if line.startswith("## "):
            push_section()
            current_order += 10
            current_title = line[3:].strip()
            current_level = 2
        elif line.startswith("### "):
            current_body.append(line)
        elif line.startswith("# "):
            continue
        else:
            current_body.append(line)
    push_section()

    return sections


def parse_summitpost_routes(html: str) -> list[dict[str, str]]:
    lines = html_to_lines(html)
    route_names: list[str] = []
    in_routes = False
    route_limit = 30

    route_header = re.compile(r"^\d+\s+routes?$", re.IGNORECASE)
    stop_header = re.compile(r"^\d+\s+(trip reports?|images?|climber)", re.IGNORECASE)
    for line in lines:
        normalized = line.lower().strip()
        match = route_header.match(line.strip())
        if match:
            in_routes = True
            route_limit = int(line.strip().split()[0])
            continue
        if in_routes and stop_header.match(line.strip()):
            break
        if not in_routes:
            continue
        if len(line) > 120 or line.startswith("#"):
            continue
        if line not in route_names and 1 <= len(line.split()) <= 12:
            route_names.append(line)
        if len(route_names) >= route_limit:
            break

    return [{"name": name} for name in route_names[:route_limit]]


def parse_summitpost_trip_report_titles(html: str) -> list[str]:
    lines = html_to_lines(html)
    titles: list[str] = []
    in_reports = False
    report_limit = 60

    report_header = re.compile(r"^\d+\s+trip reports?$", re.IGNORECASE)
    stop_header = re.compile(r"^\d+\s+(comments?|images?|routes?)", re.IGNORECASE)
    for line in lines:
        normalized = line.lower().strip()
        match = report_header.match(line.strip())
        if match:
            in_reports = True
            report_limit = int(line.strip().split()[0])
            continue
        if in_reports and stop_header.match(line.strip()):
            break
        if not in_reports:
            continue
        if line.startswith("#") or len(line) > 140:
            continue
        if line not in titles and 1 <= len(line.split()) <= 16:
            titles.append(line)
        if len(titles) >= report_limit:
            break

    return titles[:report_limit]
