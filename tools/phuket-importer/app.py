"""Phuket Importer — local tool that downloads ALL listings, texts and photos from
getyourphuket.com (rent + sale) and indreamsphuket.ru (projects).

It does not change site pages: it only creates folders in imports/.

Zero third-party deps except `requests` (HTML is parsed with the stdlib, the web UI
is served by the stdlib http.server), so the Docker build cannot break on wheels.

Usage:
  python app.py                      # web UI on :8090 (Docker maps it to :8093)
  python app.py crawl getyourphuket  # whole site from the command line
  python app.py crawl indreams
  python app.py crawl https://example.com/ --max-pages 500
  python app.py single https://getyourphuket.com/en/...
"""
import argparse
import datetime as dt
import gzip
import hashlib
import html
import json
import os
import re
import sys
import threading
import time
import traceback
import urllib.parse
import uuid
from collections import Counter, deque
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path, PurePosixPath, PureWindowsPath

import requests

WORKSPACE = Path(os.environ.get("THAIVILLAS_WORKSPACE", "/workspace"))
IMPORTS_DIR = Path(os.environ.get("THAIVILLAS_IMPORTS_DIR", str(WORKSPACE / "imports")))
HOST_WORKSPACE = os.environ.get("THAIVILLAS_HOST_WORKSPACE", "")
TIMEOUT = int(os.environ.get("IMPORTER_TIMEOUT", "60"))
DELAY = float(os.environ.get("IMPORTER_DELAY", "0.25"))  # pause between page requests, seconds
PHOTO_WORKERS = int(os.environ.get("IMPORTER_PHOTO_WORKERS", "6"))

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9,ru;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

SITES = {
    "getyourphuket": {
        "name": "Get Your Phuket (rent + sale)",
        "base": "https://getyourphuket.com",
        "start": ["/en/"],
        "langPrefix": "/en",  # only English pages; turn off with "all languages"
        "propertyUrl": r"/real-estate/(?:rent|sale)/(?:[^/]+/)?object/[^/]+/?$",
        "skipUrl": r"/filter/|/apply/|/favorite/|/search/|/lang/|\.php$",
    },
    "indreams-en": {
        "name": "In Dreams Phuket — English version (same listings as indreamsphuket.ru)",
        "base": "https://indreamsphuket.com",
        "start": ["/"],
        "langPrefix": "",
        "propertyUrl": r"^/(?:sale|rent)/[^/]+/[^/]+/?$|^/project/[^/]+/?$",
        "skipUrl": r"^/search/|^/cdn-img|^/team/|^/privilegeclub",
    },
    "indreams": {
        "name": "In Dreams Phuket (projects)",
        "base": "https://indreamsphuket.ru",
        "start": ["/"],
        "langPrefix": "",
        "propertyUrl": r"^/(?:sale|rent)/[^/]+/[^/]+/?$|^/project/[^/]+/?$",
        "skipUrl": r"^/search/|^/cdn-img|^/team/|^/privilegeclub",
    },
}

# --------------------------------------------------------------------------- DOM

VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr", "param"}
SKIP_TEXT = {"script", "style", "noscript", "svg", "template", "iframe", "head", "select", "button"}
BLOCK = {"p", "div", "section", "article", "li", "ul", "ol", "tr", "table", "h1", "h2", "h3", "h4", "h5", "h6",
         "header", "footer", "main", "aside", "nav", "dl", "dt", "dd", "br", "figure", "figcaption", "blockquote",
         "td", "th", "form", "label", "hr", "pre", "address"}


class Node:
    __slots__ = ("tag", "attrs", "children", "parent", "text")

    def __init__(self, tag, attrs=None, parent=None, text=None):
        self.tag = tag
        self.attrs = attrs or {}
        self.children = []
        self.parent = parent
        self.text = text  # only for "#text" nodes

    def get(self, name, default=""):
        return self.attrs.get(name, default) or default

    def iter(self):
        stack = [self]
        while stack:
            n = stack.pop()
            yield n
            stack.extend(reversed(n.children))

    def find_all(self, *tags):
        tags = set(tags)
        return [n for n in self.iter() if n.tag in tags]

    def find(self, *tags):
        for n in self.iter():
            if n.tag in tags:
                return n
        return None

    def classes(self):
        return (self.get("class") + " " + self.get("id")).lower()

    def remove(self):
        if self.parent and self in self.parent.children:
            self.parent.children.remove(self)
        self.parent = None

    def ancestors(self):
        p = self.parent
        while p:
            yield p
            p = p.parent

    def element_children(self):
        return [c for c in self.children if c.tag != "#text"]


class TreeBuilder(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node("#document")
        self.cur = self.root

    def handle_starttag(self, tag, attrs):
        node = Node(tag, {k: (v if v is not None else "") for k, v in attrs}, self.cur)
        self.cur.children.append(node)
        if tag not in VOID:
            self.cur = node

    def handle_startendtag(self, tag, attrs):
        node = Node(tag, {k: (v if v is not None else "") for k, v in attrs}, self.cur)
        self.cur.children.append(node)

    def handle_endtag(self, tag):
        n = self.cur
        while n is not None and n.tag != tag:
            n = n.parent
        if n is not None and n.parent is not None:  # tolerate broken markup: ignore unmatched end tags
            self.cur = n.parent

    def handle_data(self, data):
        if data:
            self.cur.children.append(Node("#text", parent=self.cur, text=data))


def parse_html(content):
    b = TreeBuilder()
    try:
        b.feed(content)
        b.close()
    except Exception:
        pass
    return b.root


def node_text(node, stop=None):
    """Readable text with line breaks for block elements. `stop(node)` -> True cuts the walk."""
    out = []
    state = {"stopped": False}

    def walk(n):
        if state["stopped"]:
            return
        if n.tag == "#text":
            out.append(n.text)
            return
        if n.tag in SKIP_TEXT:
            return
        if stop and stop(n):
            state["stopped"] = True
            return
        block = n.tag in BLOCK
        if block:
            out.append("\n")
        for c in n.children:
            walk(c)
        if block:
            out.append("\n")

    walk(node)
    text = "".join(out).replace(" ", " ")
    lines = [re.sub(r"[ \t\r\f\v]+", " ", ln).strip() for ln in text.split("\n")]
    res, prev_blank = [], False
    for ln in lines:
        if not ln:
            if not prev_blank and res:
                res.append("")
            prev_blank = True
            continue
        res.append(ln)
        prev_blank = False
    return "\n".join(res).strip()


def short_text(node, limit=300):
    t = re.sub(r"\s+", " ", node_text(node)).strip()
    return t[:limit]


# --------------------------------------------------------------------------- helpers

def now_iso():
    return dt.datetime.now(dt.timezone.utc).isoformat()


TRANSLIT = str.maketrans({
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "e", "ж": "zh", "з": "z", "и": "i", "й": "y",
    "к": "k", "л": "l", "м": "m", "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u", "ф": "f",
    "х": "kh", "ц": "ts", "ч": "ch", "ш": "sh", "щ": "sch", "ъ": "", "ы": "y", "ь": "", "э": "e", "ю": "yu", "я": "ya",
})


def slugify(value, fallback="item"):
    value = html.unescape(value or "").lower().translate(TRANSLIT)
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    return value[:90].strip("-") or fallback


def host_path(path):
    if not HOST_WORKSPACE:
        return str(path)
    try:
        rel = Path(path).relative_to(WORKSPACE)
    except ValueError:
        return str(path)
    cls = PureWindowsPath if re.match(r"^[A-Za-z]:[\\/]", HOST_WORKSPACE) else PurePosixPath
    return str(cls(HOST_WORKSPACE, *rel.parts))


def same_site(url, base):
    a = urllib.parse.urlparse(url).netloc.lower().removeprefix("www.")
    b = urllib.parse.urlparse(base).netloc.lower().removeprefix("www.")
    return a == b


def dedupe(seq):
    seen, out = set(), []
    for x in seq:
        k = json.dumps(x, sort_keys=True, ensure_ascii=False) if isinstance(x, (dict, list)) else x
        if k not in seen:
            seen.add(k)
            out.append(x)
    return out


# --------------------------------------------------------------------------- HTTP

class CachedResponse:
    def __init__(self, url, text, ctype):
        self.url, self.text, self.headers, self.status_code = url, text, {"content-type": ctype}, 200
        self.content = text.encode("utf-8")


class Fetcher:
    def __init__(self):
        self.s = requests.Session()
        self.s.headers.update(HEADERS)
        self.last = 0.0
        self.lock = threading.Lock()

    def get(self, url, binary=False, referer=None, polite=True):
        cache = os.environ.get("IMPORTER_CACHE")
        cfile = None
        if cache and not binary:
            cfile = Path(cache) / (hashlib.sha1(url.encode()).hexdigest() + ".json")
            if cfile.exists():
                try:
                    c = json.loads(cfile.read_text(encoding="utf-8"))
                    return CachedResponse(c["url"], c["text"], c["ctype"])
                except Exception:
                    pass
        resp = self._get(url, binary, referer, polite)
        if cfile is not None:
            cfile.parent.mkdir(parents=True, exist_ok=True)
            cfile.write_text(json.dumps({"url": resp.url, "text": resp.text, "ctype": resp.headers.get("content-type", "")}), encoding="utf-8")
        return resp

    def _get(self, url, binary=False, referer=None, polite=True):
        last_error = None
        for attempt in range(3):
            try:
                if polite:
                    with self.lock:
                        wait = DELAY - (time.time() - self.last)
                        if wait > 0:
                            time.sleep(wait)
                        self.last = time.time()
                headers = {"Referer": referer} if referer else {}
                resp = self.s.get(url, timeout=TIMEOUT, allow_redirects=True, headers=headers)
                if resp.status_code in (404, 410):
                    raise FileNotFoundError(f"HTTP {resp.status_code}")
                resp.raise_for_status()
                if binary:
                    return resp
                ctype = resp.headers.get("content-type", "")
                if "charset" not in ctype.lower() and not url.endswith(".gz"):
                    m = re.search(rb'<meta[^>]+charset=["\']?([\w-]+)', resp.content[:4000], re.I)
                    resp.encoding = m.group(1).decode() if m else (resp.apparent_encoding or "utf-8")
                text = resp.text
                if re.search(r"Vercel Security Checkpoint|Just a moment\.\.\.|cf-browser-verification|Attention Required! \| Cloudflare", text[:5000]):
                    raise RuntimeError("anti-bot checkpoint returned instead of the page (open the site in a browser once, then retry later)")
                return resp
            except FileNotFoundError:
                raise
            except Exception as exc:
                last_error = exc
                time.sleep(1.5 * (attempt + 1))
        raise RuntimeError(f"failed to download {url}: {last_error}")


# --------------------------------------------------------------------------- discovery

SKIP_EXT = re.compile(r"\.(?:jpe?g|png|gif|webp|avif|svg|ico|bmp|tiff?|css|js|mjs|map|json|xml|txt|pdf|docx?|xlsx?|pptx?|zip|rar|7z|mp4|mov|webm|mp3|wav|woff2?|ttf|otf|eot)$", re.I)
SKIP_PATH = re.compile(r"/(?:wp-admin|wp-login|wp-json|xmlrpc|feed|comments/feed|cart|checkout|my-account|login|logout|register|cdn-cgi|tag|author|search)(?:/|$)|/print/?$|/amp/?$", re.I)
KEEP_QUERY = {"page", "paged", "p", "pg", "id", "lang", "type", "deal", "category", "cat", "offset", "start", "pagen_1", "pagen_2", "pagen_3", "property", "object", "project"}

PROPERTY_WORDS = (
    "property", "properties", "villa", "villas", "apartment", "apartments", "apartament", "apartamenty", "condo", "condos",
    "realty", "real-estate", "realestate", "estate", "object", "objects", "obekt", "obekty", "listing", "listings",
    "project", "projects", "proekt", "proekty", "complex", "residence", "residences", "rent", "rental", "rentals",
    "arenda", "sale", "for-sale", "buy", "prodazha", "kupit", "catalog", "katalog", "house", "houses", "townhouse",
    "offer", "offers", "unit", "units", "penthouse", "land", "nedvizhimost", "kvartiry", "doma", "villy", "zhk",
)
PROPERTY_SEG_RE = re.compile(r"(?:^|[-_])(?:" + "|".join(re.escape(w) for w in PROPERTY_WORDS) + r")(?:$|[-_])", re.I)


def normalize_url(url, base_url):
    url = html.unescape(url or "").strip()
    if not url or url.startswith(("mailto:", "tel:", "javascript:", "whatsapp:", "viber:", "tg:", "#", "data:")):
        return ""
    url = urllib.parse.urljoin(base_url, url)
    p = urllib.parse.urlparse(url)
    if p.scheme not in ("http", "https"):
        return ""
    q = [(k, v) for k, v in urllib.parse.parse_qsl(p.query, keep_blank_values=False) if k.lower() in KEEP_QUERY]
    path = re.sub(r"/{2,}", "/", p.path or "/")
    return urllib.parse.urlunparse((p.scheme, p.netloc.lower(), path, "", urllib.parse.urlencode(q), ""))


def lang_ok(url, lang_prefix):
    if not lang_prefix:
        return True
    path = urllib.parse.urlparse(url).path
    return path == lang_prefix or path.startswith(lang_prefix.rstrip("/") + "/")


def crawlable(url, base, lang_prefix, skip_re=None):
    if not url or not same_site(url, base):
        return False
    path = urllib.parse.urlparse(url).path
    if skip_re and re.search(skip_re, path):
        return False
    if SKIP_EXT.search(path) or SKIP_PATH.search(path):
        return False
    return lang_ok(url, lang_prefix)


def looks_like_property_url(url, lang_prefix=""):
    path = urllib.parse.urlparse(url).path
    if lang_prefix and path.startswith(lang_prefix):
        path = path[len(lang_prefix.rstrip("/")):]
    segs = [s for s in path.split("/") if s]
    if len(segs) < 2:
        return bool(segs) and bool(re.search(r"\d{2,}", segs[-1])) and bool(PROPERTY_SEG_RE.search(segs[-1]))
    return any(PROPERTY_SEG_RE.search(s) for s in segs[:-1]) or bool(re.search(r"(?:^|[-_])\d{2,}$", segs[-1]))


def parse_sitemap(fetcher, url, out, seen, log, depth=0):
    if url in seen or depth > 4:
        return
    seen.add(url)
    try:
        resp = fetcher.get(url, binary=True)
    except Exception as exc:
        log(f"  sitemap {url}: {exc}")
        return
    data = resp.content
    if url.endswith(".gz") or data[:2] == b"\x1f\x8b":
        try:
            data = gzip.decompress(data)
        except Exception:
            pass
    text = data.decode("utf-8", "replace")
    if "<urlset" not in text and "<sitemapindex" not in text:
        return
    locs = [html.unescape(x).strip() for x in re.findall(r"<loc>\s*(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?\s*</loc>", text, re.S)]
    if "<sitemapindex" in text:
        log(f"  sitemap index {url}: {len(locs)} sitemaps")
        for loc in locs:
            parse_sitemap(fetcher, loc, out, seen, log, depth + 1)
    else:
        log(f"  sitemap {url}: {len(locs)} URLs")
        out.extend(locs)
        # alternate language links (hreflang) inside sitemaps
        out.extend(html.unescape(x) for x in re.findall(r'<xhtml:link[^>]+href=["\']([^"\']+)', text))


def discover_sitemaps(fetcher, base, log):
    candidates = []
    try:
        robots = fetcher.get(urllib.parse.urljoin(base, "/robots.txt")).text
        candidates += re.findall(r"(?im)^\s*sitemap:\s*(\S+)", robots)
    except Exception:
        pass
    candidates += [urllib.parse.urljoin(base, p) for p in ("/sitemap.xml", "/sitemap_index.xml", "/wp-sitemap.xml", "/sitemap-index.xml", "/sitemap.xml.gz")]
    urls, seen = [], set()
    for c in dedupe(candidates):
        parse_sitemap(fetcher, c, urls, seen, log)
    return dedupe(urls)


# --------------------------------------------------------------------------- images

IMG_EXT = re.compile(r"\.(?:jpe?g|png|webp|avif)$", re.I)
IMG_ATTRS = ("src", "data-src", "data-lazy-src", "data-original", "data-lazy", "data-img-zoom-url", "data-full",
             "data-large_image", "data-zoom-image", "data-image", "data-bg", "data-background", "data-img",
             "data-hi-res", "data-fullsrc", "data-big", "data-large", "data-thumb", "data-src-retina", "href", "content",
             "data-content-cover-bg", "data-original-src", "data-orig-file", "data-medium-file", "data-large-file", "poster")
SRCSET_ATTRS = ("srcset", "data-srcset", "data-lazy-srcset")
JUNK_IMG = re.compile(
    r"logo|icon|favicon|sprite|avatar|/flags?/|flag[-_]|placeholder|blank\.|loader|preloader|spinner|emoji|gravatar|"
    r"pixel|1x1|/plugins/|/themes/|arrow|social|whatsapp|telegram|instagram|facebook|youtube-play|payment|"
    r"rating|badge|qr[-_]?code|captcha|tracking|/ads?/|doubleclick|googleads|maps\.googleapis|maps\.gstatic|"
    r"tildacdn\.com/[^ ]*?/(?:arrow|close|lib)", re.I)
URL_IN_TEXT = re.compile(r"""(?:https?:)?(?:\\?/\\?/)[^\s"'<>()\\]+?\.(?:jpe?g|png|webp|avif)(?:\?[^\s"'<>()\\]*)?""", re.I)


def clean_image_url(raw, page_url):
    if not raw:
        return None
    u = html.unescape(raw).strip().strip("'\"")
    u = u.replace("\\/", "/").replace("\\u002F", "/").replace("\\u002f", "/").replace("&amp;", "&")
    if u.startswith("data:") or not u:
        return None
    if u.startswith("//"):
        u = "https:" + u
    u = urllib.parse.urljoin(page_url, u)
    p = urllib.parse.urlparse(u)
    if p.scheme not in ("http", "https"):
        return None
    # Next.js / Nuxt image proxies: /_next/image?url=<original>&w=...
    if p.path.endswith(("/_next/image", "/_ipx", "/image")) and "url=" in p.query:
        inner = urllib.parse.parse_qs(p.query).get("url", [""])[0]
        if inner:
            return clean_image_url(inner, page_url)
    path = urllib.parse.unquote(p.path)
    if not IMG_EXT.search(path) and not re.search(r"(?:format|fm|ext)=(?:jpe?g|png|webp)", p.query, re.I):
        return None
    if JUNK_IMG.search(u):
        return None
    return urllib.parse.urlunparse((p.scheme, p.netloc, p.path, "", p.query, ""))


def original_candidates(url):
    """Best (largest/original) URL first, the URL as seen on the page as fallback."""
    p = urllib.parse.urlparse(url)
    cands = []
    path = p.path
    if "tildacdn" in p.netloc:
        parts = path.split("/")
        if "-" in parts:
            i = parts.index("-")
            path = "/".join(parts[:i] + [parts[-1]])
        cands.append(urllib.parse.urlunparse((p.scheme, "static.tildacdn.com", path, "", "", "")))
    wp = re.sub(r"-\d{2,4}x\d{2,4}(\.(?:jpe?g|png|webp|avif))$", r"\1", path, flags=re.I)
    if wp != path:
        cands.append(urllib.parse.urlunparse((p.scheme, p.netloc, wp, "", "", "")))
    # strip pure resize query params (?w=400&h=300&fit=crop) but keep the as-seen URL as a fallback
    if p.query and re.fullmatch(r"(?:(?:w|h|width|height|q|quality|fit|crop|resize|auto|dpr|fm|format|ver|v|version|itok)=[^&]*&?)+", p.query, re.I):
        cands.append(urllib.parse.urlunparse((p.scheme, p.netloc, p.path, "", "", "")))
    cands.append(url)
    return dedupe(cands)


def variant_size(url):
    path = urllib.parse.unquote(urllib.parse.urlparse(url).path)
    m = re.search(r"/(\d{2,4})_(\d{2,4})_[0-9a-f]+/", path) or re.search(r"_(\d{3,4})X(\d{3,4})_", path, re.I)
    return int(m.group(1)) * int(m.group(2)) if m else 0


def image_key(url):
    best = original_candidates(url)[0]
    p = urllib.parse.urlparse(best)
    path = re.sub(r"/resize_cache/", "/", p.path)
    path = re.sub(r"/\d{2,4}_\d{2,4}_[0-9a-f]+/", "/", path)
    path = re.sub(r"/styles/[^/]+/public/", "/", path)
    key = urllib.parse.unquote(p.netloc.removeprefix("www.") + path).lower()
    key = re.sub(r"-(?:scaled|thumbnail|thumb|small|medium|large|\d{3,4}w?)(\.(?:jpe?g|png|webp|avif))$", r"\1", key)
    return key


def images_in_node(node, page_url):
    found = []
    for n in node.iter():
        if n.tag == "#text":
            continue
        for a in IMG_ATTRS:
            v = n.attrs.get(a)
            if v and (n.tag in ("img", "source", "meta", "link", "a", "video") or a != "href"):
                if a == "href" and n.tag not in ("a", "link"):
                    continue
                if a == "content" and n.tag != "meta":
                    continue
                u = clean_image_url(v, page_url)
                if u:
                    found.append(u)
        for a in SRCSET_ATTRS:
            v = n.attrs.get(a)
            if v:
                best, best_w = None, -1
                for part in v.split(","):
                    bits = part.strip().split()
                    if not bits:
                        continue
                    w = 0
                    if len(bits) > 1:
                        m = re.match(r"(\d+(?:\.\d+)?)", bits[1])
                        w = float(m.group(1)) if m else 0
                    if w >= best_w:
                        best, best_w = bits[0], w
                u = clean_image_url(best, page_url)
                if u:
                    found.append(u)
        style = n.attrs.get("style")
        if style and "url(" in style:
            for m in re.finditer(r"url\(\s*['\"]?([^'\")]+)", style):
                u = clean_image_url(m.group(1), page_url)
                if u:
                    found.append(u)
    return found


def merge_images(urls):
    by_key, order = {}, []
    for u in urls:
        k = image_key(u)
        if k not in by_key:
            by_key[k] = u
            order.append(k)
        elif variant_size(u) > variant_size(by_key[k]) or (not variant_size(u) and not variant_size(by_key[k]) and len(u) > len(by_key[k]) and "resize" not in u):
            by_key[k] = u
    return [by_key[k] for k in order]


# --------------------------------------------------------------------------- extraction

PROPERTY_LD_TYPES = {"realestatelisting", "residence", "apartment", "house", "singlefamilyresidence", "accommodation",
                     "apartmentcomplex", "product", "offer", "lodgingbusiness", "vacationrental", "hotelroom", "suite",
                     "gatedresidencecommunity", "place"}
SIMILAR_RE = re.compile(r"^(?:similar|related|you (?:may|might) (?:also )?like|other (?:properties|villas|projects|objects|offers)|"
                        r"recommended|more (?:properties|villas)|recently viewed|похож|други[ех] (?:объект|вилл|проект|предлож)|"
                        r"смотрите также|вам (?:может|также) понрав|рекомендуем|недавно просмотр)", re.I)
AMENITY_HEAD_RE = re.compile(r"amenit|feature|facilit|equipment|include|infrastructure|удобств|оснащ|особенност|инфраструкт|"
                             r"в (?:вилле|доме|квартире|апартаментах) есть|что есть|включен|преимуществ|услуг", re.I)

PHUKET_AREAS = [
    ("bang-tao", r"bang\s*-?\s*tao|laguna|банг\s*-?\s*тао|бангтао|лагун"), ("surin", r"surin|сурин"),
    ("kamala", r"kamala|камал"), ("patong", r"patong|патонг"), ("karon", r"karon|карон"),
    ("kata-noi", r"kata\s*-?\s*noi|ката\s*-?\s*ной"), ("kata", r"\bkata\b|\bката\b"),
    ("nai-harn", r"nai\s*-?\s*harn|nai\s*-?\s*han\b|най\s*-?\s*харн|найхарн"), ("rawai", r"rawai|равай"),
    ("chalong", r"chalong|чалонг"), ("layan", r"layan|лаян"), ("mai-khao", r"mai\s*-?\s*khao|май\s*-?\s*кхао"),
    ("nai-yang", r"nai\s*-?\s*yang|най\s*-?\s*янг"), ("nai-thon", r"nai\s*-?\s*thon|най\s*-?\s*тон"),
    ("cherng-talay", r"cherng\s*-?\s*talay|choeng\s*thale|черн?г?\s*-?\s*талай|ченг\s*-?\s*талай"),
    ("kathu", r"kathu|кату\b"), ("phuket-town", r"phuket\s*town|old\s*town|пхукет[- ]таун|старый город"),
    ("cape-yamu", r"cape\s*yamu|ямуи?\b|yamu"), ("koh-kaew", r"koh\s*kaew|ко\s*кео"), ("panwa", r"panwa|панва"),
    ("yanui", r"yanui|януй"), ("ao-po", r"ao\s*po|ао\s*по"), ("thalang", r"thalang|таланг"), ("kalim", r"kalim|калим"),
    ("ao-yon", r"ao\s*yon|ао\s*йон"), ("pa-klok", r"pa\s*klok|па\s*клок"), ("kamala-beach", r"kamala beach"),
]

NUM = r"(\d{1,3}(?:[   ,.]\d{3})+(?:[.,]\d+)?|\d+(?:[.,]\d+)?)"
CUR = r"(฿|THB|бат(?:ов|а)?|US\$|\$|USD|€|EUR|₽|руб\.?|RUB|CNY|¥)"
MULT = r"(?:\s*(млн\.?|million|mln|mio|m\b|k\b|тыс\.?))?"
PRICE_RE = re.compile(CUR + r"\s?" + NUM + MULT + r"|" + NUM + MULT + r"\s?" + CUR, re.I)
CUR_MAP = {"฿": "THB", "thb": "THB", "бат": "THB", "батов": "THB", "бата": "THB", "$": "USD", "us$": "USD", "usd": "USD",
           "€": "EUR", "eur": "EUR", "₽": "RUB", "руб": "RUB", "руб.": "RUB", "rub": "RUB", "cny": "CNY", "¥": "CNY"}

SPEC_PATTERNS = {
    "bedrooms": [r"(?:bed\s*rooms?|bedrooms?|спальн\w*|кол-?во спален)\s*[:\-–]?\s*(\d{1,2})\b", r"\b(\d{1,2})\s*(?:-|\s)?(?:bed(?:room)?s?\b|br\b|спал\w*|bdr)"],
    "bathrooms": [r"(?:bath\s*rooms?|bathrooms?|ванн\w*|санузл\w*|с/у)\s*[:\-–]?\s*(\d{1,2})\b", r"\b(\d{1,2})\s*(?:bath(?:room)?s?\b|ванн\w*|санузл\w*)"],
    "guests": [r"(?:guests?|sleeps|max(?:imum)? guests|гост\w*|человек)\s*[:\-–]?\s*(\d{1,2})\b", r"\b(\d{1,2})\s*(?:guests?\b|гост\w*|человек|persons?\b|people\b)"],
    "floors": [r"(?:floors?|storeys?|levels?|этаж(?:ей|ность)?)\s*[:\-–]?\s*(\d{1,2})\b"],
}
AREA_RE = re.compile(r"(\d[\d  ,.]{0,8})\s*(?:m²|m2|sq\.?\s?m\b|sqm|кв\.?\s?м|м²|м2)", re.I)
LAND_RE = re.compile(r"(?:land|plot|участ\w*|земл\w*)[^\n\d]{0,25}(\d[\d  ,.]{0,8})\s*(?:m²|m2|sq\.?\s?m|sqm|кв\.?\s?м|м²|м2|rai|рай|сот\w*)", re.I)
LIVING_RE = re.compile(r"(?:living|built|interior|indoor|internal|total|usable|floor area|size|area|площад\w*(?: дома| виллы| квартиры| жил\w*)?)[^\n\d]{0,25}(\d[\d  ,.]{0,8})\s*(?:m²|m2|sq\.?\s?m|sqm|кв\.?\s?м|м²|м2)", re.I)


def to_number(s):
    s = (s or "").replace(" ", " ").replace(" ", " ").strip()
    if re.search(r"\d[ ,.]\d{3}(?:\D|$)", s) and not re.search(r"[.,]\d{1,2}$", s):
        s = re.sub(r"[ ,.]", "", s)
    else:
        s = s.replace(" ", "").replace(",", ".")
        if s.count(".") > 1:
            s = s.replace(".", "")
    try:
        v = float(s)
        return int(v) if v.is_integer() else v
    except ValueError:
        return None


def extract_prices(lines):
    prices = []
    prev = ""
    for raw_ln in lines:
        ln = prev[-60:] + " \u2502 " + raw_ln if prev and PRICE_RE.search(raw_ln) and not PRICE_RE.search(prev) else raw_ln
        prev = raw_ln
        if len(prices) >= 60:
            break
        for m in PRICE_RE.finditer(ln):
            cur = (m.group(1) or m.group(6) or "").lower().rstrip(".") if (m.group(1) or m.group(6)) else ""
            cur = CUR_MAP.get(cur, CUR_MAP.get(cur + ".", cur.upper()))
            num, mult = (m.group(2), m.group(3)) if m.group(1) else (m.group(4), m.group(5))
            amount = to_number(num)
            if amount is None:
                continue
            mult = (mult or "").lower()
            if mult.startswith(("млн", "million", "mln", "mio")) or mult == "m":
                amount = amount * 1_000_000
            elif mult.startswith(("k", "тыс")):
                amount = amount * 1000
            if amount < 50:
                continue
            ctx = ln[max(0, m.start() - 40): m.end() + 40].lower()
            after = ln[m.end(): m.end() + 30].lower()
            period = None
            for name, rx in (("night", r"night|nightly|/ ?n\b|ноч|сут|day|день|daily"), ("week", r"week|недел"),
                             ("month", r"month|monthly|/ ?mo\b|мес"), ("year", r"year|yearly|annual|/ ?yr|год")):
                if re.search(rx, after) or re.search(r"(?:per|в|за|/)\s*(?:" + rx + ")", ctx):
                    period = name
                    break
            if not period:
                thb = amount if cur == "THB" else amount * 35 if cur in ("USD", "EUR") else amount * 0.4 if cur == "RUB" else amount
                if re.search(r"sale|price|buy|цена|стоимост|продаж|купить|от\b|from", ctx) and thb >= 1_000_000:
                    period = "sale"
                elif thb >= 2_500_000:
                    period = "sale"
            rng = re.search(NUM + r"\s*[–—-]\s*$", ln[max(0, m.start() - 30): m.start()])
            item = {"amount": amount, "currency": cur, "period": period, "raw": ln[max(0, m.start() - 25): m.end() + 25].strip()}
            if rng and m.group(4):
                low = to_number(rng.group(1))
                if low and low < amount:
                    item["amountFrom"] = low * (amount / to_number(num)) if to_number(num) else low
            prices.append(item)
    return dedupe(prices)


def extract_specs(root):
    specs = []
    for tr in root.find_all("tr"):
        cells = [c for c in tr.element_children() if c.tag in ("td", "th")]
        if len(cells) == 2:
            k, v = short_text(cells[0], 80), short_text(cells[1], 300)
            if k and v:
                specs.append([k.rstrip(":"), v])
    for dl in root.find_all("dl"):
        key = None
        for c in dl.element_children():
            if c.tag == "dt":
                key = short_text(c, 80)
            elif c.tag == "dd" and key:
                specs.append([key.rstrip(":"), short_text(c, 300)])
                key = None
    for n in root.iter():
        if n.tag in ("#text", "tr", "dl", "table", "ul", "ol", "html", "body"):
            continue
        kids = n.element_children()
        if len(kids) != 2 or any(k.find("img", "table", "ul") for k in kids):
            continue
        k, v = short_text(kids[0], 90), short_text(kids[1], 200)
        if not k or not v or len(k) > 60 or len(v) > 160:
            continue
        cls0 = kids[0].classes()
        if k.endswith(":") or re.search(r"label|name|title|key|caption|term|param|prop|char|attr|feature", cls0):
            specs.append([k.rstrip(":").strip(), v])
    text = node_text(root)
    for ln in text.split("\n"):
        m = re.match(r"^([^:\n]{2,45}):\s+(.{1,150})$", ln)
        if m and not re.match(r"https?$", m.group(1).strip(), re.I):
            specs.append([m.group(1).strip(), m.group(2).strip()])
    return dedupe(specs)


def find_number(patterns, texts):
    for rx in patterns:
        for t in texts:
            m = re.search(rx, t, re.I)
            if m:
                v = to_number(m.group(1))
                if v is not None and 0 < v < 100:
                    return v
    return None


def json_ld_blocks(doc):
    blocks = []
    for s in doc.find_all("script"):
        if "ld+json" in s.get("type").lower():
            raw = "".join(c.text or "" for c in s.children).strip()
            try:
                data = json.loads(raw)
            except Exception:
                try:
                    data = json.loads(re.sub(r",\s*([}\]])", r"\1", raw.replace("\n", " ")))
                except Exception:
                    blocks.append({"_raw": raw})
                    continue
            if isinstance(data, dict) and isinstance(data.get("@graph"), list):
                blocks.extend(data["@graph"])
            elif isinstance(data, list):
                blocks.extend(data)
            else:
                blocks.append(data)
    return blocks


def ld_types(block):
    t = block.get("@type") if isinstance(block, dict) else None
    return {x.lower() for x in (t if isinstance(t, list) else [t]) if isinstance(x, str)}


def meta_tags(doc):
    out = {}
    for m in doc.find_all("meta"):
        k = m.get("property") or m.get("name") or m.get("itemprop")
        v = m.get("content")
        if k and v and k.lower() not in out:
            out[k.lower()] = html.unescape(v).strip()
    return out


def find_coords(doc, raw, blocks):
    for b in blocks:
        if isinstance(b, dict) and isinstance(b.get("geo"), dict):
            try:
                return float(b["geo"]["latitude"]), float(b["geo"]["longitude"])
            except Exception:
                pass
    for n in doc.iter():
        a = n.attrs
        for la, lo in (("data-lat", "data-lng"), ("data-lat", "data-lon"), ("data-latitude", "data-longitude"), ("data-lat", "data-long")):
            if a.get(la) and a.get(lo):
                try:
                    return float(a[la]), float(a[lo])
                except ValueError:
                    pass
        if a.get("data-coords") or a.get("data-coordinates"):
            m = re.search(r"(-?\d+\.\d+)\s*[,;]\s*(-?\d+\.\d+)", a.get("data-coords") or a.get("data-coordinates"))
            if m:
                return float(m.group(1)), float(m.group(2))
    pats = [
        r'"lat(?:itude)?"\s*:\s*"?(-?\d{1,2}\.\d{3,})"?\s*,\s*"(?:lng|lon|long|longitude)"\s*:\s*"?(-?\d{1,3}\.\d{3,})',
        r"\blat(?:itude)?\s*:\s*['\"]?(-?\d{1,2}\.\d{3,})['\"]?\s*,\s*(?:lng|lon|long|longitude)\s*:\s*['\"]?(-?\d{1,3}\.\d{3,})",
        r"!3d(-?\d{1,2}\.\d{3,})!4d(-?\d{1,3}\.\d{3,})",
        r"!2d(-?\d{1,3}\.\d{3,})!3d(-?\d{1,2}\.\d{3,})",
        r"google\.[^\"'\s]*?[@=](-?\d{1,2}\.\d{3,}),\s*(-?\d{1,3}\.\d{3,})",
        r"(?:ll|center|q|query|daddr)=(-?\d{1,2}\.\d{3,})(?:,|%2C)\s*(-?\d{1,3}\.\d{3,})",
    ]
    cands = []
    for i, p in enumerate(pats):
        for m in re.finditer(p, raw):
            a, b = float(m.group(1)), float(m.group(2))
            lat, lng = (b, a) if i == 3 else (a, b)
            cands.append((lat, lng))
    for lat, lng in cands:  # prefer Thailand
        if 5 < lat < 21 and 97 < lng < 106:
            return lat, lng
    return cands[0] if cands else (None, None)


def classify_deal(url, title, crumbs, text, prices):
    path = urllib.parse.urlparse(url).path.lower()
    m = re.search(r"/(rent|sale|project)/", path + "/")
    if m:
        return m.group(1)
    hay = " ".join([urllib.parse.unquote(url).lower(), title.lower(), " ".join(crumbs).lower()])
    if re.search(r"project|proekt|проект|complex|комплекс|residence|резиденц|\bzhk\b|\bжк\b|off-?plan|under construction|строящ", hay):
        return "project"
    if re.search(r"sale|for-sale|buy|prodazh|kupit|продаж|купить|покупк", hay):
        return "sale"
    if re.search(r"rent|arend|аренд|снять|holiday|vacation|daily|monthly|long-term", hay):
        return "rent"
    periods = {p.get("period") for p in prices}
    if periods & {"night", "week", "month", "year"}:
        return "rent"
    if "sale" in periods:
        return "sale"
    low = text[:3000].lower()
    if re.search(r"for sale|продаж|freehold|leasehold|ownership|собственност", low):
        return "sale"
    if re.search(r"per night|per month|за ночь|в месяц|аренд", low):
        return "rent"
    return "unknown"


def classify_type(text):
    low = text.lower()
    for name, rx in (("complex", r"\bжк\b|complex|комплекс|condominium|кондоминиум"), ("penthouse", r"penthouse|пентхаус"), ("townhouse", r"townhouse|таунхаус"), ("villa", r"villa|вилл"),
                     ("condo", r"condo|кондо"), ("apartment", r"apartment|апартамент|квартир|flat\b"),
                     ("studio", r"studio|студи"), ("house", r"\bhouse\b|\bдом\b"), ("land", r"\bland\b|plot|участ|земл")):
        if re.search(rx, low):
            return name
    return ""


def find_area(*texts):
    hay = " ".join(t for t in texts if t)
    for slug, rx in PHUKET_AREAS:
        if re.search(rx, hay, re.I):
            return slug
    return ""


def is_similar_heading(n):
    if n.tag in ("h2", "h3", "h4", "h5", "h6") or re.search(r"(?:^|[-_ ])(?:title|heading|header)(?:$|[-_ ])", n.classes()):
        t = short_text(n, 120)
        return bool(t) and len(t) < 80 and bool(SIMILAR_RE.search(t))
    return False


def analyze_page(raw, url, site):
    """Everything we can get from one HTML page. Pure function — no network."""
    doc = parse_html(raw)
    blocks = json_ld_blocks(doc)
    metas = meta_tags(doc)
    title_tag = doc.find("title")
    h1 = doc.find("h1")
    h1_text = short_text(h1, 300) if h1 else ""
    title = h1_text or metas.get("og:title") or (short_text(title_tag, 300) if title_tag else "")
    listing_ld = next((b for b in blocks if isinstance(b, dict) and ld_types(b) & PROPERTY_LD_TYPES and b.get("name")), {})
    if listing_ld.get("name") and not h1_text:
        title = str(listing_ld["name"])
    title = re.sub(r"\s*[|–—-]\s*(?:get your phuket|getyourphuket|in ?dreams.*|индримс.*)$", "", title, flags=re.I).strip()

    # breadcrumbs
    crumbs = []
    for b in blocks:
        if isinstance(b, dict) and "breadcrumblist" in ld_types(b):
            for it in b.get("itemListElement", []) or []:
                if isinstance(it, dict):
                    nm = it.get("name") or (it.get("item") or {}).get("name") if isinstance(it.get("item"), dict) else it.get("name")
                    if nm:
                        crumbs.append(str(nm))
    if not crumbs:
        bc = next((n for n in doc.iter() if n.tag != "#text" and "breadcrumb" in n.classes()), None)
        if bc:
            crumbs = [t for t in (short_text(a, 80) for a in bc.find_all("a", "span", "li")) if t and t not in ("/", "»", ">")]
            crumbs = dedupe(crumbs)

    # links (before we cut anything)
    links = []
    for a in doc.find_all("a", "link", "area"):
        if a.tag == "link" and a.get("rel").lower() not in ("next", "prev", "alternate"):
            continue
        u = normalize_url(a.get("href"), url)
        if u:
            links.append(u)
    # links hidden in scripts / JSON state (SPA sites)
    base = site["base"]
    host = re.escape(urllib.parse.urlparse(base).netloc.removeprefix("www."))
    for m in re.finditer(r"""["'](?:https?:)?(?:\\?/\\?/(?:www\.)?""" + host + r""")?((?:\\?/)[A-Za-z0-9\-._~%/\\]{3,200})["']""", raw):
        path = m.group(1).replace("\\/", "/")
        if path.startswith("//") or SKIP_EXT.search(path):
            continue
        u = normalize_url(path, base)
        if u and looks_like_property_url(u, site.get("langPrefix", "")):
            links.append(u)
    links = dedupe(links)

    # main content root
    body = doc.find("body") or doc
    root = doc.find("main") or doc.find("article") or next((n for n in doc.iter() if n.get("role") == "main"), None)
    if root is None or len(node_text(root)) < 200:
        root = body
        for n in list(root.iter()):
            if n.tag in ("header", "nav", "footer") or (n.tag != "#text" and re.search(r"(?:^|[-_ ])(?:cookie|cookies|popup|modal)(?:$|[-_ ])", n.classes())):
                n.remove()

    # cards linking to OTHER pages (similar listings, menus with pictures) — keep their photos aside
    related_images = []
    page_path = urllib.parse.urlparse(url).path.rstrip("/")
    for a in list(root.find_all("a")):
        href = normalize_url(a.get("href"), url)
        if not href or not same_site(href, base) or SKIP_EXT.search(urllib.parse.urlparse(href).path):
            continue
        if urllib.parse.urlparse(href).path.rstrip("/") == page_path:
            continue
        if a.find("img") or "url(" in "".join(n.get("style") for n in a.iter() if n.tag != "#text"):
            related_images += images_in_node(a, url)
            a.remove()

    # cut everything after a "Similar properties" heading
    order = [n for n in root.iter() if n.tag != "#text"]
    cut_at = next((i for i, n in enumerate(order) if is_similar_heading(n)), None)
    content_nodes_text = node_text(root, stop=is_similar_heading)
    if cut_at is not None:
        stop_node = order[cut_at]
        after = False
        before_imgs, after_imgs = [], []
        for n in root.iter():
            if n is stop_node:
                after = True
            if n.tag == "#text":
                continue
            (after_imgs if after else before_imgs).extend(images_in_node(Node(n.tag, n.attrs), url))
        gallery = before_imgs
        related_images += after_imgs
    else:
        gallery = images_in_node(root, url)

    # images that live only in scripts / JSON (sliders built by JS) — add, chrome filtered later at site level
    script_images = []
    for m in URL_IN_TEXT.finditer(raw):
        u = clean_image_url(m.group(0), url)
        if u:
            script_images.append(u)
    og = [clean_image_url(metas.get(k), url) for k in ("og:image", "og:image:url", "twitter:image")]
    ld_imgs = []
    for b in blocks:
        if isinstance(b, dict) and ld_types(b) & PROPERTY_LD_TYPES:
            im = b.get("image")
            for x in (im if isinstance(im, list) else [im]):
                if isinstance(x, dict):
                    x = x.get("url") or x.get("contentUrl")
                ld_imgs.append(clean_image_url(x, url) if isinstance(x, str) else None)
    related_keys = {image_key(u) for u in related_images}
    main_images = merge_images([u for u in ld_imgs + gallery + og if u])
    main_keys = {image_key(u) for u in main_images}
    extra_images = merge_images([u for u in script_images if image_key(u) not in main_keys and image_key(u) not in related_keys])

    text = content_nodes_text
    lines = [ln for ln in text.split("\n") if ln.strip()]
    specs = extract_specs(root)
    spec_lines = [f"{k}: {v}" for k, v in specs]

    # description: longest coherent paragraphs from the content root
    paras = [ln for ln in lines if len(ln) > 60 and not PRICE_RE.fullmatch(ln)]
    description = listing_ld.get("description") or "\n\n".join(paras) or metas.get("og:description") or metas.get("description", "")

    # amenities: list items under "Amenities / Features / Удобства" headings, else all short <li>
    amenities = []
    for hd in root.iter():
        if hd.tag in ("h2", "h3", "h4", "h5", "strong", "b", "p", "div", "span") and hd.tag != "#text":
            t = short_text(hd, 100)
            if t and len(t) < 60 and AMENITY_HEAD_RE.search(t) and hd.parent:
                sib = hd.parent.children[hd.parent.children.index(hd) + 1:] if hd in hd.parent.children else []
                for s in sib[:4]:
                    for li in s.find_all("li"):
                        lt = short_text(li, 120)
                        if 1 < len(lt) < 100:
                            amenities.append(lt)
    for b in [listing_ld]:
        for f in (b.get("amenityFeature") or []) if isinstance(b, dict) else []:
            if isinstance(f, dict) and f.get("name") and f.get("value") not in (False, "false"):
                amenities.append(str(f["name"]))
    all_li = dedupe(t for t in (short_text(li, 150) for li in root.find_all("li")) if 1 < len(t) < 120)

    prices = extract_prices(spec_lines + lines[:400])
    offers = []
    for b in blocks:
        if isinstance(b, dict):
            off = b.get("offers")
            for o in (off if isinstance(off, list) else [off] if isinstance(off, dict) else []):
                if isinstance(o, dict) and (o.get("price") or o.get("lowPrice")):
                    offers.append(o)
                    prices.insert(0, {"amount": to_number(str(o.get("price") or o.get("lowPrice"))), "currency": o.get("priceCurrency", ""),
                                      "period": None, "raw": json.dumps(o, ensure_ascii=False)[:200]})
    prices = dedupe(prices)

    texts = spec_lines + [title] + lines[:200]
    bedrooms = listing_ld.get("numberOfBedrooms") or listing_ld.get("numberOfRooms") or find_number(SPEC_PATTERNS["bedrooms"], texts)
    bathrooms = listing_ld.get("numberOfBathroomsTotal") or find_number(SPEC_PATTERNS["bathrooms"], texts)
    occ = listing_ld.get("occupancy") if isinstance(listing_ld.get("occupancy"), dict) else {}
    guests = occ.get("maxValue") or find_number(SPEC_PATTERNS["guests"], texts)
    floors = find_number(SPEC_PATTERNS["floors"], spec_lines)
    joined = "\n".join(texts)
    m = LIVING_RE.search(joined) or AREA_RE.search(joined)
    living = to_number(m.group(1)) if m else None
    m = LAND_RE.search(joined)
    land = to_number(m.group(1)) if m else None
    lat, lng = find_coords(doc, raw, blocks)

    videos = dedupe(re.findall(r"(?:https?:)?//(?:www\.)?(?:youtube\.com/(?:embed/|watch\?v=)[\w-]+|youtu\.be/[\w-]+|player\.vimeo\.com/video/\d+|vimeo\.com/\d+)", raw))
    videos = ["https:" + v if v.startswith("//") else v for v in videos]
    videos += dedupe(clean for clean in (urllib.parse.urljoin(url, x) for x in re.findall(r"""["'(]([^"'()\s]+\.(?:mp4|webm|mov))["')]""", raw, re.I)))
    documents = []
    for a in doc.find_all("a"):
        href = a.get("href")
        if href and re.search(r"\.(?:pdf|docx?|xlsx?|pptx?|zip|rar)(?:\?|$)|drive\.google\.com|docs\.google\.com|dropbox\.com|disk\.yandex", href, re.I):
            documents.append({"url": urllib.parse.urljoin(url, html.unescape(href)), "label": short_text(a, 120)})
    documents = dedupe(documents)

    # page classification
    score, reasons = 0, []
    if listing_ld:
        score += 3
        reasons.append("json-ld listing")
    if looks_like_property_url(url, site.get("langPrefix", "")):
        score += 2
        reasons.append("property-like url")
    if bedrooms or living or land:
        score += 1
        reasons.append("rooms/area")
    if prices:
        score += 1
        reasons.append("price")
    if prices and (bedrooms or living or land) and len(main_images) >= 3:
        score += 1
        reasons.append("price + specs + photos")
    if len(main_images) >= 5:
        score += 1
        reasons.append(f"{len(main_images)} images")
    prop_links = [l for l in links if same_site(l, base) and looks_like_property_url(l, site.get("langPrefix", "")) and urllib.parse.urlparse(l).path.rstrip("/") != page_path]
    if len(set(prop_links)) >= 6 and not listing_ld:
        score -= 2
        reasons.append(f"listing page ({len(set(prop_links))} property links)")
    kind = "property" if score >= 3 else "listing" if len(set(prop_links)) >= 6 else "page"
    if site.get("propertyUrl"):  # the site's own URL scheme is authoritative
        kind = "property" if re.search(site["propertyUrl"], urllib.parse.urlparse(url).path) else ("listing" if len(set(prop_links)) >= 6 else "page")

    deal = classify_deal(url, title, crumbs, text, prices)
    ptype = classify_type(" ".join([title, " ".join(crumbs), urllib.parse.unquote(url)])) or classify_type(text[:1500])
    sub_area = find_area(title, " ".join(crumbs), urllib.parse.unquote(url), " ".join(spec_lines)) or find_area(text[:3000])

    return {
        "url": url,
        "kind": kind,
        "score": score,
        "scoreReasons": reasons,
        "title": title,
        "h1": h1_text,
        "metaTitle": short_text(title_tag, 300) if title_tag else "",
        "metaDescription": metas.get("description", ""),
        "breadcrumbs": crumbs,
        "dealType": deal,
        "propertyType": ptype,
        "subArea": sub_area,
        "bedrooms": bedrooms,
        "bathrooms": bathrooms,
        "guests": guests,
        "floors": floors,
        "livingAreaSqm": living,
        "landArea": land,
        "latitude": lat,
        "longitude": lng,
        "prices": prices,
        "offers": offers,
        "specs": specs,
        "amenities": dedupe(amenities),
        "listItems": all_li,
        "description": description,
        "fullText": text,
        "videos": dedupe(videos),
        "documents": documents,
        "images": main_images,
        "extraImages": extra_images,
        "relatedImages": merge_images(related_images),
        "links": links,
        "jsonLd": blocks,
        "meta": metas,
        "jsRendered": bool(re.search(r"__NEXT_DATA__|__NUXT__|window\.__INITIAL_STATE__", raw)) and len(text) < 400,
    }


# --------------------------------------------------------------------------- job

class Job:
    def __init__(self, kind, params):
        self.id = uuid.uuid4().hex[:10]
        self.kind = kind
        self.params = params
        self.status = "running"
        self.lines = []
        self.counters = Counter()
        self.folder = ""
        self.result = None
        self.stop = threading.Event()
        self.started = now_iso()

    def log(self, msg):
        line = f"[{dt.datetime.now().strftime('%H:%M:%S')}] {msg}"
        self.lines.append(line)
        if len(self.lines) > 4000:
            del self.lines[:1000]
        print(line, flush=True)

    def snapshot(self):
        return {"id": self.id, "status": self.status, "counters": dict(self.counters), "folder": self.folder,
                "folderHost": host_path(self.folder) if self.folder else "", "log": self.lines[-300:], "result": self.result}


JOBS = {}


def resolve_site(site_key, custom_url, all_langs):
    if site_key in SITES:
        site = dict(SITES[site_key])
        site["key"] = site_key
    else:
        url = custom_url or site_key
        p = urllib.parse.urlparse(url if "://" in url else "https://" + url)
        site = {"key": slugify(p.netloc), "name": p.netloc, "base": f"{p.scheme}://{p.netloc}", "start": [p.path or "/"], "langPrefix": ""}
    if all_langs:
        site["langPrefix"] = ""
    return site


def download_files(fetcher, items, folder, referer, job, min_size=3000):
    """items: list of {"filename", "candidates": [...]}. Returns (ok, failures)."""
    folder.mkdir(parents=True, exist_ok=True)

    def one(item):
        out = folder / item["filename"]
        if out.exists() and out.stat().st_size >= min_size:
            return item, None, out.stat().st_size
        last = None
        for cand in item["candidates"]:
            if job and job.stop.is_set():
                return item, "stopped", 0
            try:
                resp = fetcher.get(cand, binary=True, referer=referer, polite=False)
                ctype = resp.headers.get("content-type", "")
                if "text/html" in ctype:
                    raise RuntimeError("got HTML instead of a file")
                if len(resp.content) < min_size:
                    raise RuntimeError(f"file too small ({len(resp.content)} bytes)")
                out.write_bytes(shrink(resp.content, out))
                item["downloadedFrom"] = cand
                return item, None, len(resp.content)
            except Exception as exc:
                last = str(exc)
        return item, last, 0

    ok, failures = 0, []
    with ThreadPoolExecutor(max_workers=PHOTO_WORKERS) as pool:
        for item, err, size in pool.map(one, items):
            if err:
                failures.append({"filename": item["filename"], "urls": item["candidates"], "error": err})
            else:
                ok += 1
                item["bytes"] = size
    return ok, failures


MAX_PX = int(os.environ.get("IMPORTER_MAX_PX", "0"))  # e.g. 1920: downscale photos on download (needs Pillow)


def shrink(data, out):
    if not MAX_PX or out.suffix.lower() not in (".jpg", ".jpeg", ".png", ".webp"):
        return data
    try:
        import io
        from PIL import Image
        im = Image.open(io.BytesIO(data))
        if max(im.size) <= MAX_PX and out.suffix.lower() != ".png":
            return data
        im.thumbnail((MAX_PX, MAX_PX))
        buf = io.BytesIO()
        fmt = {".png": "PNG", ".webp": "WEBP"}.get(out.suffix.lower(), "JPEG")
        if fmt == "JPEG" and im.mode not in ("RGB", "L"):
            im = im.convert("RGB")
        im.save(buf, fmt, quality=85, optimize=True)
        return buf.getvalue() if buf.tell() < len(data) else data
    except Exception:
        return data


def ext_of(url, default=".jpg"):
    m = re.search(r"\.(jpe?g|png|webp|avif|pdf|docx?|xlsx?|pptx?|zip|rar|mp4|webm|mov)$", urllib.parse.unquote(urllib.parse.urlparse(url).path), re.I)
    if m:
        return "." + m.group(1).lower().replace("jpeg", "jpg")
    m = re.search(r"(?:format|fm|ext)=(jpe?g|png|webp)", url, re.I)
    return "." + m.group(1).lower().replace("jpeg", "jpg") if m else default


def thaivillas_record(a, photo_files, site):
    prices = a["prices"]

    def pick(period):
        for p in prices:
            if p.get("period") == period and p.get("amount"):
                return p
        return None

    night, month, sale = pick("night"), pick("month"), pick("sale")
    cur = next((p["currency"] for p in (night, month, sale) if p and p.get("currency")), "THB")
    return {
        "name": a["title"],
        "dealType": a["dealType"],
        "propertyType": a["propertyType"],
        "area": "Phuket",
        "areaSlug": "phuket",
        "subAreaSlug": a["subArea"],
        "bedrooms": a["bedrooms"],
        "bathrooms": a["bathrooms"],
        "guests": a["guests"],
        "livingAreaSqm": a["livingAreaSqm"],
        "landArea": a["landArea"],
        "priceNight": night["amount"] if night else None,
        "priceMonth": month["amount"] if month else None,
        "priceSale": sale["amount"] if sale else None,
        "currency": cur,
        "amenities": a["amenities"],
        "latitude": a["latitude"],
        "longitude": a["longitude"],
        "photos": photo_files,
        "source": site["key"],
        "sourceUrl": a["url"],
    }


def save_item(fetcher, a, raw, batch_dir, site, job, chrome_keys, used_slugs, with_photos=True, section="properties"):
    base_slug = slugify(a["title"] or urllib.parse.urlparse(a["url"]).path.strip("/").split("/")[-1],
                        hashlib.sha1(a["url"].encode()).hexdigest()[:10])
    slug = base_slug
    i = 2
    while slug in used_slugs:
        slug = f"{base_slug}-{i}"
        i += 1
    used_slugs.add(slug)
    folder = batch_dir / section / slug
    (folder / "raw").mkdir(parents=True, exist_ok=True)
    (folder / "raw" / "page.html").write_text(raw, encoding="utf-8")

    imgs = [u for u in a["images"] if image_key(u) not in chrome_keys]
    extra = [u for u in a["extraImages"] if image_key(u) not in chrome_keys] if len(a["images"]) < 3 else []
    dropped = [u for u in a["images"] + a["extraImages"] if image_key(u) in chrome_keys]
    photos = [{"index": n + 1, "filename": f"{n + 1:03d}{ext_of(u)}", "url": u, "candidates": original_candidates(u)}
              for n, u in enumerate(imgs + extra)]
    docs = [{"filename": f"{n + 1:02d}-{slugify(d['label'] or 'document', 'document')[:50]}{ext_of(d['url'], '.pdf')}",
             "url": d["url"], "label": d["label"], "candidates": [d["url"]]}
            for n, d in enumerate(x for x in a["documents"] if re.search(r"\.(?:pdf|docx?|xlsx?|pptx?|zip|rar)(?:\?|$)", x["url"], re.I))]

    ok = 0
    failures = []
    with_photos = with_photos and not job.params.get("noPhotos")
    if with_photos and photos:
        ok, failures = download_files(fetcher, photos, folder / "photos", a["url"], job)
    if with_photos and docs:
        d_ok, d_fail = download_files(fetcher, docs, folder / "docs", a["url"], job, min_size=500)
        failures += d_fail
        job.counters["documents"] += d_ok
    photo_files = [f"photos/{p['filename']}" for p in photos if (folder / "photos" / p["filename"]).exists()]

    data = {k: v for k, v in a.items() if k not in ("links",)}
    data.update({
        "site": site["key"],
        "slug": slug,
        "images": imgs,
        "extraImages": extra,
        "siteChromeImagesSkipped": dropped,
        "photos": [{k: v for k, v in p.items() if k != "candidates"} | {"urls": p["candidates"]} for p in photos],
        "documentsDownloaded": [{k: v for k, v in d.items() if k != "candidates"} for d in docs],
        "thaivillas": thaivillas_record(a, photo_files, site) if section == "properties" else None,
        "extractedAt": now_iso(),
    })
    (folder / "property.json" if section == "properties" else folder / "page.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    manifest = {"url": a["url"], "title": a["title"], "kind": a["kind"], "dealType": a["dealType"],
                "photosFound": len(photos), "photosDownloaded": ok, "failures": failures, "extractedAt": now_iso()}
    (folder / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    price_txt = "; ".join(f"{p['amount']:,} {p['currency']}{'/' + p['period'] if p.get('period') and p['period'] != 'sale' else ''}"
                          for p in a["prices"][:6] if isinstance(p.get("amount"), (int, float)))
    readme = (f"# {a['title']}\n\n- Тип сделки: {a['dealType']}\n- Тип объекта: {a['propertyType'] or '—'}\n- Район: {a['subArea'] or '—'}\n"
              f"- Спальни/ванные/гости: {a['bedrooms'] or '—'}/{a['bathrooms'] or '—'}/{a['guests'] or '—'}\n"
              f"- Площадь: {a['livingAreaSqm'] or '—'} м², участок: {a['landArea'] or '—'}\n- Цены: {price_txt or '—'}\n"
              f"- Фото: {ok}/{len(photos)}\n- Источник: {a['url']}\n\n{a['description'][:3000]}\n")
    (folder / "README.md").write_text(readme, encoding="utf-8")
    if with_photos:
        job.counters["photosFound"] += len(photos)
        job.counters["photosDownloaded"] += ok
    job.counters["failures"] += len(failures)
    return data, manifest, folder


def run_crawl(job):
    p = job.params
    site = resolve_site(p.get("site") or "getyourphuket", p.get("url") or "", p.get("allLangs"))
    max_pages = int(p.get("maxPages") or 3000)
    limit = int(p.get("limit") or 0) or None
    page_photos = p.get("pagePhotos", True)
    only = p.get("only") or "all"  # all | rent | sale | project
    fetcher = Fetcher()
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    batch_dir = IMPORTS_DIR / f"{site['key']}-{only}-{stamp}"
    (batch_dir / "raw").mkdir(parents=True, exist_ok=True)
    job.folder = str(batch_dir)
    base = site["base"]
    job.log(f"Site: {site['name']} — {base} (language filter: {site['langPrefix'] or 'none'})")

    # 1) discovery
    queue, seen = deque(), set()

    def push(u, front=False):
        u = normalize_url(u, base)
        if u and u not in seen and crawlable(u, base, site["langPrefix"], site.get("skipUrl")):
            seen.add(u)
            (queue.appendleft if front else queue.append)(u)

    for s in site["start"]:
        push(urllib.parse.urljoin(base, s))
    if p.get("url") and p.get("site") in SITES:
        push(p["url"], front=True)
    job.log("Reading robots.txt and sitemap...")
    sm = discover_sitemaps(fetcher, base, job.log)
    for u in sm:
        push(u, front=looks_like_property_url(normalize_url(u, base), site["langPrefix"]))
    job.counters["sitemapUrls"] = len(sm)
    job.log(f"Sitemap URLs: {len(sm)}; queue: {len(queue)}")

    # 2) crawl + analyze
    analyzed, crawl_log = [], []
    while queue and not job.stop.is_set():
        if len(crawl_log) >= max_pages:
            job.log(f"Page limit reached ({max_pages}). Increase 'max pages' to go further.")
            break
        url = queue.popleft()
        try:
            resp = fetcher.get(url)
        except Exception as exc:
            crawl_log.append({"url": url, "error": str(exc)})
            job.counters["pageErrors"] += 1
            job.log(f"  ! {url}: {exc}")
            continue
        final = normalize_url(resp.url, base) or url
        if "html" not in resp.headers.get("content-type", "html"):
            continue
        if final != url and not crawlable(final, base, site["langPrefix"]):
            crawl_log.append({"url": url, "redirect": final, "skipped": "redirect off-site/lang"})
            continue
        raw = resp.text
        try:
            a = analyze_page(raw, final, site)
        except Exception as exc:
            job.log(f"  ! parse error {final}: {exc}")
            crawl_log.append({"url": final, "error": "parse: " + str(exc)})
            continue
        n = len(crawl_log) + 1
        rawfile = batch_dir / "raw" / f"{n:05d}-{slugify(urllib.parse.urlparse(final).path, 'home')[:60]}.html"
        rawfile.write_text(raw, encoding="utf-8")
        crawl_log.append({"url": final, "kind": a["kind"], "score": a["score"], "reasons": a["scoreReasons"],
                          "dealType": a["dealType"], "title": a["title"], "images": len(a["images"]), "raw": rawfile.name})
        analyzed.append((a, rawfile))
        job.counters["pagesCrawled"] += 1
        job.counters[a["kind"] + "Pages"] += 1
        if a["kind"] == "property":
            job.log(f"  + [{a['dealType']}] {a['title'][:70]} — {len(a['images'])} photos")
        for l in a["links"]:
            push(l, front=looks_like_property_url(l, site["langPrefix"]))
        if n % 25 == 0:
            job.log(f"  ... {n} pages, {job.counters['propertyPages']} properties, queue {len(queue)}")
        if limit and job.counters["propertyPages"] >= limit:
            job.log(f"Property limit reached ({limit}).")
            break
    (batch_dir / "crawl-log.json").write_text(json.dumps(crawl_log, ensure_ascii=False, indent=2), encoding="utf-8")

    # 3) site chrome images (logo, header banners, footer) = present on many pages
    freq = Counter()
    for a, _ in analyzed:
        for k in {image_key(u) for u in a["images"] + a["extraImages"]}:
            freq[k] += 1
    threshold = max(3, int(len(analyzed) * 0.3))
    chrome = {k for k, c in freq.items() if c >= threshold} if len(analyzed) >= 5 else set()
    job.log(f"Crawled {len(analyzed)} pages. Site-wide (logo/header) images skipped: {len(chrome)}")

    # 4) save + download
    props = [(a, r) for a, r in analyzed if a["kind"] == "property" and (only == "all" or a["dealType"] == only)]
    others = [(a, r) for a, r in analyzed if not (a["kind"] == "property" and (only == "all" or a["dealType"] == only))]
    if limit:
        props = props[:limit]
    used, catalog_props, catalog_pages, manifests = set(), [], [], []
    for i, (a, rawfile) in enumerate(props, 1):
        if job.stop.is_set():
            break
        job.log(f"[{i}/{len(props)}] {a['title'][:80]}")
        try:
            data, manifest, folder = save_item(fetcher, a, rawfile.read_text(encoding="utf-8"), batch_dir, site, job, chrome, used)
            data["folder"] = str(folder.relative_to(batch_dir))
            catalog_props.append(data)
            manifests.append(manifest)
            job.counters["propertiesSaved"] += 1
        except Exception as exc:
            job.log(f"  ! {a['url']}: {exc}")
            job.counters["failures"] += 1
    if p.get("savePages", True):
        for a, rawfile in others:
            if job.stop.is_set():
                break
            try:
                data, manifest, folder = save_item(fetcher, a, rawfile.read_text(encoding="utf-8"), batch_dir, site, job, chrome,
                                                   used, with_photos=page_photos, section="pages")
                data["folder"] = str(folder.relative_to(batch_dir))
                data.pop("fullText", None)
                data.pop("jsonLd", None)
                catalog_pages.append(data)
                job.counters["pagesSaved"] += 1
            except Exception as exc:
                job.log(f"  ! page {a['url']}: {exc}")

    catalog = {
        "site": site, "mode": "crawl", "filter": only, "startedAt": job.started, "finishedAt": now_iso(),
        "stoppedByUser": job.stop.is_set(), "counters": dict(job.counters),
        "properties": catalog_props,
        "byDealType": dict(Counter(x["dealType"] for x in catalog_props)),
    }
    (batch_dir / "catalog.json").write_text(json.dumps(catalog, ensure_ascii=False, indent=2), encoding="utf-8")
    (batch_dir / "pages.json").write_text(json.dumps(catalog_pages, ensure_ascii=False, indent=2), encoding="utf-8")
    (batch_dir / "thaivillas-import.json").write_text(
        json.dumps([dict(x["thaivillas"], folder=x["folder"]) for x in catalog_props], ensure_ascii=False, indent=2), encoding="utf-8")
    write_index(batch_dir, catalog_props, catalog_pages, site)
    job.result = {"properties": len(catalog_props), "pages": len(catalog_pages), "byDealType": catalog["byDealType"]}
    job.log(f"Done: {len(catalog_props)} properties, {len(catalog_pages)} other pages, "
            f"photos {job.counters['photosDownloaded']}/{job.counters['photosFound']}. Folder: {host_path(batch_dir)}")


def run_single(job):
    p = job.params
    url = p["url"].strip()
    site = resolve_site(p.get("site") if p.get("site") in SITES and same_site(url, SITES[p["site"]]["base"]) else url, url, True)
    for key, s in SITES.items():
        if same_site(url, s["base"]):
            site = dict(s, key=key, langPrefix="")
    fetcher = Fetcher()
    batch_dir = IMPORTS_DIR / f"{site['key']}-single-{dt.datetime.now().strftime('%Y%m%d-%H%M%S')}"
    batch_dir.mkdir(parents=True, exist_ok=True)
    job.folder = str(batch_dir)
    resp = fetcher.get(url)
    a = analyze_page(resp.text, normalize_url(resp.url, url) or url, site)
    job.log(f"{a['title']} — kind={a['kind']} ({', '.join(a['scoreReasons'])}), deal={a['dealType']}, photos={len(a['images'])}")
    a["kind"] = "property"  # user asked for this page explicitly
    data, manifest, folder = save_item(fetcher, a, resp.text, batch_dir, site, job, set(), set())
    data["folder"] = str(folder.relative_to(batch_dir))
    (batch_dir / "catalog.json").write_text(json.dumps({"mode": "single", "site": site, "properties": [data]}, ensure_ascii=False, indent=2), encoding="utf-8")
    (batch_dir / "thaivillas-import.json").write_text(json.dumps([dict(data["thaivillas"], folder=data["folder"])], ensure_ascii=False, indent=2), encoding="utf-8")
    write_index(batch_dir, [data], [], site)
    job.counters["propertiesSaved"] = 1
    job.result = {"properties": 1, "title": a["title"]}
    job.log(f"Done. Photos {manifest['photosDownloaded']}/{manifest['photosFound']}. Folder: {host_path(folder)}")


def write_index(batch_dir, props, pages, site):
    """A local index.html to eyeball the result (open it in a browser)."""
    esc = lambda s: html.escape(str(s or ""))
    cards = []
    for x in props:
        img = next(iter(x["thaivillas"]["photos"]), "") if x.get("thaivillas") else ""
        tv = x.get("thaivillas") or {}
        price = tv.get("priceSale") or tv.get("priceMonth") or tv.get("priceNight") or ""
        cards.append(f'<a class="c" href="{esc(x["folder"])}/README.md"><div class="i" style="background-image:url(\'{esc(x["folder"])}/{esc(img)}\')"></div>'
                     f'<b>{esc(x["title"])}</b><span>{esc(x["dealType"])} · {esc(x["propertyType"])} · {esc(x["subArea"])}</span>'
                     f'<span>{esc(x.get("bedrooms") or "—")} bd · {len(tv.get("photos") or [])} photos · {esc(price)} {esc(tv.get("currency") if price else "")}</span></a>')
    page_rows = "".join(f'<li><a href="{esc(x["url"])}">{esc(x["title"] or x["url"])}</a> — {esc(x["kind"])}, {len(x.get("images") or [])} img</li>' for x in pages)
    doc = (f'<!doctype html><meta charset="utf-8"><title>{esc(site["name"])} import</title>'
           '<style>body{font:14px system-ui;margin:24px;background:#f6f3ec}.g{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:14px}'
           '.c{background:#fff;border-radius:10px;padding:10px;text-decoration:none;color:#111;display:flex;flex-direction:column;gap:4px}'
           '.i{height:150px;border-radius:8px;background:#ddd center/cover}span{color:#666;font-size:12px}</style>'
           f'<h1>{esc(site["name"])}: {len(props)} objects</h1><div class="g">{"".join(cards)}</div>'
           f'<h2>Other pages ({len(pages)})</h2><ul>{page_rows}</ul>')
    (batch_dir / "index.html").write_text(doc, encoding="utf-8")


def start_job(kind, params, background=True):
    job = Job(kind, params)
    JOBS[job.id] = job

    def target():
        try:
            (run_single if kind == "single" else run_crawl)(job)
            job.status = "stopped" if job.stop.is_set() else "done"
        except Exception as exc:
            job.status = "error"
            job.log("ERROR: " + str(exc))
            job.log(traceback.format_exc())

    if background:
        threading.Thread(target=target, daemon=True).start()
    else:
        target()
    return job


# --------------------------------------------------------------------------- web UI

PAGE = r"""<!doctype html>
<html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Phuket Importer</title>
<style>
:root{--bg:#f3efe6;--panel:#fffdfa;--ink:#14110c;--muted:#70695f;--line:#e2d8c9;--dark:#0d0d0c;--ok:#2f7d32}
*{box-sizing:border-box}body{margin:0;background:var(--bg);font-family:Inter,system-ui,-apple-system,Segoe UI,sans-serif;color:var(--ink)}
main{max-width:1100px;margin:0 auto;padding:30px 16px}.card{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:24px;box-shadow:0 18px 45px rgba(24,18,8,.07)}
h1{font:800 32px/1.1 Georgia,serif;margin:0 0 8px}p{color:var(--muted);line-height:1.5;margin:6px 0}
.grid{display:grid;grid-template-columns:1.3fr 1fr 1fr 1fr;gap:12px}@media(max-width:800px){.grid{grid-template-columns:1fr 1fr}}
label{display:block;font-size:12px;text-transform:uppercase;font-weight:800;margin:16px 0 6px;color:#5e574d}
input,select{width:100%;border:1px solid var(--line);border-radius:8px;padding:12px 13px;font:inherit;background:#fff}
.chk{display:flex;gap:18px;flex-wrap:wrap;margin-top:14px}.chk label{display:flex;gap:7px;align-items:center;text-transform:none;font-weight:600;font-size:14px;margin:0}.chk input{width:auto}
button{border:0;border-radius:999px;background:var(--dark);color:#fff;font-weight:800;padding:12px 18px;cursor:pointer;margin-top:16px}
button.secondary{background:#fff;color:#111;border:1px solid var(--line)}button:disabled{opacity:.5;cursor:not-allowed}.row{display:flex;gap:10px;flex-wrap:wrap}
.summary{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:10px;margin:18px 0}.metric{background:#fff;border:1px solid var(--line);border-radius:8px;padding:12px}.metric b{display:block;font-size:22px}.metric span{font-size:12px;color:var(--muted)}
.log{white-space:pre-wrap;background:#111;color:#dfffbd;border-radius:8px;padding:14px;height:420px;overflow:auto;font:12.5px/1.5 ui-monospace,Consolas,monospace}
.pathbox{background:#111;color:#dfffbd;border-radius:8px;padding:12px;margin-top:12px;font:13px/1.5 ui-monospace,Consolas,monospace;word-break:break-all}.pathbox b{color:#b8f04a}
.status{font-weight:800}.status.done{color:var(--ok)}.status.error{color:#b43d2a}
</style></head>
<body><main><section class="card">
<h1>Phuket Importer</h1>
<p>Скачивает все объекты (аренда, продажа, проекты): тексты, характеристики, цены, координаты, удобства, PDF-презентации и все фото в оригинальном размере. Сайт обходится целиком: sitemap + все внутренние ссылки. Страницы нашего сайта не меняются — результат складывается в папку <code>imports/</code>.</p>
<div class="grid">
 <div><label>Сайт</label><select id="site"><option value="getyourphuket">getyourphuket.com — аренда + продажа</option><option value="indreams">indreamsphuket.ru — наши проекты</option><option value="indreams-en">indreamsphuket.com — то же на английском</option><option value="custom">Другой сайт (URL ниже)</option></select></div>
 <div><label>Что сохранять</label><select id="only"><option value="all">Всё</option><option value="rent">Только аренда</option><option value="sale">Только продажа</option><option value="project">Только проекты</option></select></div>
 <div><label>Макс. страниц обхода</label><input id="maxPages" type="number" min="1" max="50000" value="3000"></div>
 <div><label>Лимит объектов</label><input id="limit" type="number" min="1" placeholder="пусто = все"></div>
</div>
<label>Ссылка (для «одного объекта» или другого сайта)</label>
<input id="url" placeholder="https://getyourphuket.com/en/...">
<div class="chk">
 <label><input type="checkbox" id="savePages" checked> Сохранять и остальные страницы (о компании, районы, статьи)</label>
 <label><input type="checkbox" id="pagePhotos" checked> Качать фото и с остальных страниц</label>
 <label><input type="checkbox" id="allLangs"> Все языковые версии (не только /en/)</label>
</div>
<div class="row"><button id="crawl">Скачать весь сайт</button><button id="one" class="secondary">Скачать один объект по ссылке</button><button id="stop" class="secondary" disabled>Остановить</button><button id="copy" class="secondary" disabled>Скопировать путь</button></div>
<div id="result"></div>
<h3>Лог <span id="st" class="status"></span></h3><div id="log" class="log">Готов.</div>
</section></main>
<script>
const $=id=>document.getElementById(id);let job=null,timer=null,folder='';
const M=[['pagesCrawled','Страниц обойдено'],['propertyPages','Найдено объектов'],['propertiesSaved','Объектов сохранено'],['photosDownloaded','Фото скачано'],['photosFound','Фото найдено'],['documents','PDF/документов'],['pagesSaved','Других страниц'],['failures','Ошибок']];
async function start(kind){
  const body={kind,site:$('site').value==='custom'?($('url').value.trim()):$('site').value,url:$('url').value.trim(),only:$('only').value,
    maxPages:+$('maxPages').value||3000,limit:+$('limit').value||null,savePages:$('savePages').checked,pagePhotos:$('pagePhotos').checked,allLangs:$('allLangs').checked};
  if(kind==='single'&&!body.url){alert('Вставь ссылку на объект');return}
  if($('site').value==='custom'&&!body.url){alert('Вставь адрес сайта');return}
  const r=await fetch('/api/start',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});const d=await r.json();
  if(!r.ok){alert(d.error);return} job=d.id;$('crawl').disabled=$('one').disabled=true;$('stop').disabled=false;poll();timer=setInterval(poll,1500);
}
async function poll(){
  const d=await (await fetch('/api/job/'+job)).json();const c=d.counters||{};
  $('st').textContent=d.status==='running'?'— работает…':d.status==='done'?'— готово':d.status==='stopped'?'— остановлено':'— ошибка';$('st').className='status '+d.status;
  const lg=$('log');const atBottom=lg.scrollTop+lg.clientHeight>=lg.scrollHeight-30;lg.textContent=d.log.join('\n');if(atBottom)lg.scrollTop=lg.scrollHeight;
  folder=d.folderHost||d.folder;$('copy').disabled=!folder;
  $('result').innerHTML='<div class="summary">'+M.map(([k,t])=>`<div class="metric"><span>${t}</span><b>${c[k]||0}</b></div>`).join('')+'</div>'+(folder?`<div class="pathbox"><b>Папка с результатом</b><br>${folder}</div>`:'');
  if(d.status!=='running'){clearInterval(timer);$('crawl').disabled=$('one').disabled=false;$('stop').disabled=true}
}
$('crawl').onclick=()=>start('crawl');$('one').onclick=()=>start('single');
$('stop').onclick=()=>fetch('/api/stop/'+job,{method:'POST'});
$('copy').onclick=()=>{navigator.clipboard.writeText(folder);alert('Путь скопирован: '+folder)};
</script></body></html>"""


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype="application/json; charset=utf-8"):
        data = body if isinstance(body, bytes) else (body if isinstance(body, str) else json.dumps(body, ensure_ascii=False)).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *args):
        pass

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            return self._send(200, PAGE, "text/html; charset=utf-8")
        m = re.match(r"^/api/job/(\w+)$", self.path)
        if m and m.group(1) in JOBS:
            return self._send(200, JOBS[m.group(1)].snapshot())
        self._send(404, {"error": "not found"})

    def do_POST(self):
        length = int(self.headers.get("Content-Length") or 0)
        try:
            body = json.loads(self.rfile.read(length) or b"{}")
        except Exception:
            body = {}
        if self.path == "/api/start":
            if any(j.status == "running" for j in JOBS.values()):
                return self._send(409, {"error": "Уже идёт загрузка — дождись окончания или нажми «Остановить»."})
            kind = body.get("kind") or "crawl"
            if kind == "single" and not body.get("url"):
                return self._send(400, {"error": "Вставь ссылку на объект"})
            job = start_job(kind, body)
            return self._send(200, {"id": job.id})
        m = re.match(r"^/api/stop/(\w+)$", self.path)
        if m and m.group(1) in JOBS:
            JOBS[m.group(1)].stop.set()
            return self._send(200, {"ok": True})
        self._send(404, {"error": "not found"})


def main():
    ap = argparse.ArgumentParser(description="Phuket Importer")
    sub = ap.add_subparsers(dest="cmd")
    c = sub.add_parser("crawl", help="download a whole site")
    c.add_argument("site", help="getyourphuket | indreams | https://any-site/")
    c.add_argument("--only", default="all", choices=["all", "rent", "sale", "project"])
    c.add_argument("--max-pages", type=int, default=3000)
    c.add_argument("--limit", type=int, default=0)
    c.add_argument("--all-langs", action="store_true")
    c.add_argument("--no-pages", action="store_true", help="do not save non-listing pages")
    c.add_argument("--no-page-photos", action="store_true")
    c.add_argument("--no-photos", action="store_true", help="record photo URLs only, download nothing")
    s = sub.add_parser("single", help="download one listing page")
    s.add_argument("url")
    sub.add_parser("serve", help="web UI (default)")
    args = ap.parse_args()
    if args.cmd == "crawl":
        params = {"site": args.site if args.site in SITES else args.site, "url": "" if args.site in SITES else args.site,
                  "only": args.only, "maxPages": args.max_pages, "limit": args.limit, "allLangs": args.all_langs,
                  "savePages": not args.no_pages, "pagePhotos": not args.no_page_photos, "noPhotos": args.no_photos}
        job = start_job("crawl", params, background=False)
        sys.exit(0 if job.status == "done" else 1)
    if args.cmd == "single":
        job = start_job("single", {"url": args.url}, background=False)
        sys.exit(0 if job.status == "done" else 1)
    port = int(os.environ.get("PORT", "8090"))
    IMPORTS_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Phuket Importer: http://localhost:{port}  (imports -> {IMPORTS_DIR})", flush=True)
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()


if __name__ == "__main__":
    main()
