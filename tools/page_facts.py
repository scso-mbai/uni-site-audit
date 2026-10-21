#!/usr/bin/env python3
"""Collect evidence about one web page for a heuristic evaluation, without a browser.

    python3 tools/page_facts.py https://www.ntu.edu.sg/
    python3 tools/page_facts.py --all [--config config.json] [--date YYYY-MM-DD]

The first form prints one JSON object. The second reads every page in config.json,
writes reports/<date>/raw/<site>-<page>.json and prints a short JSON summary.
Python 3.9+ standard library only.
"""

import argparse
import http.client
import json
import os
import re
import socket
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from html.parser import HTMLParser

USER_AGENT = "MGMT6110-class-audit (educational; weekly)"
AGENT_TOKEN = "mgmt6110-class-audit"
TIMEOUT = 30
MAX_BYTES = 5_000_000
SGT = timezone(timedelta(hours=8))

VAGUE_PHRASES = [
    "click here", "here", "read more", "learn more", "find out more", "more",
    "see more", "view more", "discover more", "more info", "details",
]
HELP_WORDS = re.compile(r"\b(help|faqs?|frequently asked|contact|enquir\w*|ask us)\b", re.I)
SEARCH_WORDS = re.compile(r"search", re.I)
COOKIE_WORDS = re.compile(r"cookie|consent|gdpr|onetrust|cookiebot|cookielaw|cc-banner|privacy-banner", re.I)
CAROUSEL_WORDS = re.compile(r"carousel|slider|swiper|slick", re.I)
BREADCRUMB_WORDS = re.compile(r"breadcrumb", re.I)
PHONE_RE = re.compile(r"(\+65[\s-]?)?\b[3689]\d{3}[\s-]?\d{4}\b")
EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+(\.[\w-]+)+")
POSTCODE_RE = re.compile(r"Singapore\s*\(?\d{6}\)?", re.I)
CHALLENGE_SIGNS = {
    "Imperva Incapsula": ["_Incapsula_Resource", "incap_ses", "Incapsula incident"],
    "Cloudflare": ["cf-browser-verification", "cf_chl_", "challenge-platform", "Just a moment..."],
    "Akamai": ["Reference&#32;&#35;", "akamai-bot", "_abck"],
    "Generic bot check": ["Please enable JavaScript and cookies", "verify you are human", "captcha"],
}
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta",
        "source", "track", "wbr", "param"}


def now_sgt():
    return datetime.now(SGT).replace(microsecond=0)


def clean(text, limit=120):
    text = re.sub(r"\s+", " ", text or "").strip()
    return text if len(text) <= limit else text[: limit - 1] + "…"


# ---------- robots.txt ----------

def parse_robots(body):
    """Return {agent: [(kind, path), ...]} for each user-agent group."""
    groups, current, last_was_agent = {}, [], False
    for raw in body.splitlines():
        line = raw.split("#", 1)[0].strip()
        if ":" not in line:
            continue
        field, value = [p.strip() for p in line.split(":", 1)]
        field = field.lower()
        if field == "user-agent":
            if not last_was_agent:
                current = []
            current.append(value.lower())
            groups.setdefault(value.lower(), [])
            last_was_agent = True
        elif field in ("allow", "disallow"):
            last_was_agent = False
            for agent in current:
                groups[agent].append((field, value))
        else:
            last_was_agent = False
    return groups


def rule_matches(pattern, path):
    if pattern == "":
        return False
    regex = re.escape(pattern).replace(r"\*", ".*")
    if regex.endswith(r"\$"):
        regex = regex[:-2] + "$"
    return re.match(regex, path) is not None


def robots_verdict(groups, path):
    agent = AGENT_TOKEN if AGENT_TOKEN in groups else "*"
    rules = groups.get(agent, [])
    best = None
    for kind, pattern in rules:
        if rule_matches(pattern, path):
            if best is None or len(pattern) > len(best[1]) or (len(pattern) == len(best[1]) and kind == "allow"):
                best = (kind, pattern)
    allowed = best is None or best[0] == "allow"
    return allowed, agent, (f"{best[0].capitalize()}: {best[1]}" if best else None)


def fetch_robots(origin):
    url = origin + "/robots.txt"
    info = {"url": url, "status": None, "rules_read": False, "note": ""}
    try:
        status, _, headers, body, _ = http_get(url)
        info["status"] = status
        text = body.decode("utf-8", "replace")
        if status >= 500:
            info["note"] = "robots.txt gave a server error, so every page on this host is treated as disallowed."
            return info, None
        if status >= 400:
            info["note"] = "No robots.txt (client error), so no rules apply."
            return info, {}
        if "<html" in text[:2000].lower():
            info["note"] = "robots.txt answered with an HTML page, not a rules file, so no rules apply."
            return info, {}
        info["rules_read"] = True
        return info, parse_robots(text)
    except FetchError as exc:
        info["status"] = exc.status
        info["error"] = exc.kind
        info["note"] = f"robots.txt could not be read ({exc}), so no page on this host is fetched."
        return info, None


# ---------- HTTP ----------

class FetchError(Exception):
    def __init__(self, kind, message, status=None, headers=None):
        super().__init__(message)
        self.kind, self.status, self.headers = kind, status, headers or {}


def http_get(url, retry_pause=15):
    try:
        return http_get_once(url)
    except FetchError as exc:
        if exc.kind != "timeout" or not retry_pause:
            raise
        time.sleep(retry_pause)
        try:
            return http_get_once(url)
        except FetchError as again:
            again.args = (str(again) + " (tried twice, 15 seconds apart)",)
            raise again


def http_get_once(url):
    req = urllib.request.Request(url, headers={
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,text/plain;q=0.9,*/*;q=0.5",
        "Accept-Language": "en",
    })
    start = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            body = resp.read(MAX_BYTES + 1)
            ms = round((time.monotonic() - start) * 1000)
            return resp.status, resp.geturl(), dict(resp.headers.items()), body[:MAX_BYTES], ms
    except urllib.error.HTTPError as exc:
        ms = round((time.monotonic() - start) * 1000)
        headers = dict(exc.headers.items()) if exc.headers else {}
        try:
            body = exc.read(MAX_BYTES)
        except Exception:
            body = b""
        if exc.code == 403 and headers_get(headers, "x-deny-reason") == "host_not_allowed":
            raise FetchError("blocked_by_routine_network",
                             "the routine's network settings do not allow this host", 403, headers)
        return exc.code, exc.geturl() or url, headers, body, ms
    except (OSError, http.client.HTTPException, ValueError) as exc:
        reason = getattr(exc, "reason", exc)
        if isinstance(reason, (TimeoutError, socket.timeout)) or "timed out" in str(reason).lower():
            raise FetchError("timeout", f"no answer within {TIMEOUT} seconds")
        raise FetchError("network_error", str(reason) or type(exc).__name__)


def headers_get(headers, name):
    for key, value in headers.items():
        if key.lower() == name:
            return value
    return None


def decode(body, headers):
    ctype = headers_get(headers, "content-type") or ""
    match = re.search(r"charset=([\w-]+)", ctype, re.I)
    for enc in ([match.group(1)] if match else []) + ["utf-8"]:
        try:
            return body.decode(enc)
        except (LookupError, UnicodeDecodeError):
            continue
    return body.decode("utf-8", "replace")


# ---------- HTML evidence ----------

class Evidence(HTMLParser):
    def __init__(self, page_url):
        super().__init__(convert_charrefs=True)
        self.page_url = page_url
        self.host = urllib.parse.urlparse(page_url).netloc.lower()
        self.lang = None
        self.title = ""
        self.meta = {}
        self.h1, self.h2, self.h3_count = [], [], 0
        self.navs = []
        self.nav_landmarks = 0
        self.nav_region = None
        self.li_depth_in_nav = 0
        self.footer_region = None
        self.footer_seen = False
        self.footer_text = []
        self.footer_mailto = self.footer_tel = 0
        self.main = self.header = False
        self.links = []
        self.current_link = None
        self.images = {"total": 0, "missing_alt": 0, "empty_alt": 0}
        self.forms = 0
        self.search = {"form": False, "input": False, "toggle": False}
        self.breadcrumb_signs = set()
        self.label_for = set()
        self.label_depth = 0
        self.inputs = []
        self.scripts = {"total": 0, "external": 0, "third_party_hosts": set()}
        self.cookie_hints = set()
        self.carousel_hints = 0
        self.autoplay_media = 0
        self.aria_current = 0
        self.words = 0
        self.skip = None
        self.capture = None
        self.buffer = []
        self.ignore_depth = 0

    def handle_starttag(self, tag, attrs):
        a = {k.lower(): (v or "") for k, v in attrs}
        cls_id = (a.get("class", "") + " " + a.get("id", "")).strip()
        role = a.get("role", "").lower()

        if tag == "html":
            self.lang = a.get("lang") or a.get("xml:lang") or None
        if tag in ("script", "style", "noscript", "template"):
            self.ignore_depth += 1
        if tag == "title" and not self.title:
            self.capture, self.buffer = "title", []
        if tag == "meta":
            name = (a.get("name") or a.get("property") or "").lower()
            if name in ("viewport", "description", "robots"):
                self.meta[name] = a.get("content", "")
        if tag in ("h1", "h2"):
            self.capture, self.buffer = tag, []
        if tag == "h3":
            self.h3_count += 1
        if tag == "nav" or role == "navigation":
            self.nav_landmarks += 1
        if self.nav_region and tag == self.nav_region[0]:
            self.nav_region[1] += 1
        elif not self.nav_region and (tag == "nav" or role == "navigation") and tag not in VOID:
            self.nav_region = [tag, 1]
            self.navs.append({"label": clean(a.get("aria-label", ""), 60) or None,
                              "links": 0, "top_level_links": []})
            self.li_depth_in_nav = 0
        if tag == "li" and self.nav_region:
            self.li_depth_in_nav += 1
        if self.footer_region and tag == self.footer_region[0]:
            self.footer_region[1] += 1
        elif not self.footer_region and (tag == "footer" or role == "contentinfo") and tag not in VOID:
            self.footer_region = [tag, 1]
            self.footer_seen = True
        if tag == "main" or role == "main":
            self.main = True
        if tag == "header" or role == "banner":
            self.header = True
        if tag == "form":
            self.forms += 1
            if role == "search" or SEARCH_WORDS.search(a.get("action", "") + " " + cls_id):
                self.search["form"] = True
        if role == "search":
            self.search["form"] = True
        if tag == "label":
            self.label_depth += 1
            if a.get("for"):
                self.label_for.add(a["for"])
        if tag in ("input", "select", "textarea"):
            itype = a.get("type", "text").lower() if tag == "input" else tag
            if itype not in ("hidden", "submit", "button", "image", "reset"):
                self.inputs.append({
                    "type": itype,
                    "id": a.get("id"),
                    "in_label": self.label_depth > 0,
                    "aria": bool(a.get("aria-label") or a.get("aria-labelledby") or a.get("title")),
                    "placeholder_only": bool(a.get("placeholder")),
                })
            hay = " ".join([itype, a.get("name", ""), cls_id, a.get("placeholder", ""), a.get("aria-label", "")])
            if itype == "search" or a.get("name", "").lower() in ("q", "query", "s", "search", "keyword", "keywords") \
                    or SEARCH_WORDS.search(hay):
                self.search["input"] = True
        if tag in ("button", "a") and SEARCH_WORDS.search(a.get("aria-label", "") + " " + cls_id + " " + a.get("title", "")):
            self.search["toggle"] = True
        if tag == "img":
            self.images["total"] += 1
            if "alt" not in a:
                if not (role == "presentation" or a.get("aria-hidden") == "true"):
                    self.images["missing_alt"] += 1
            elif a["alt"].strip() == "":
                self.images["empty_alt"] += 1
            if self.current_link is not None and a.get("alt"):
                self.current_link["text"].append(a["alt"])
        if tag == "a" and "href" in a:
            if self.current_link is not None:
                self.close_link()
            self.current_link = {"href": a["href"], "text": [], "aria": a.get("aria-label") or a.get("title") or "",
                                 "nav_top": bool(self.nav_region) and self.li_depth_in_nav <= 1,
                                 "in_nav": bool(self.nav_region), "in_footer": bool(self.footer_region)}
            if a["href"].lower().startswith("mailto:") and self.footer_region:
                self.footer_mailto += 1
            if a["href"].lower().startswith("tel:") and self.footer_region:
                self.footer_tel += 1
        if tag == "script":
            self.scripts["total"] += 1
            src = a.get("src")
            if src:
                self.scripts["external"] += 1
                host = urllib.parse.urlparse(urllib.parse.urljoin(self.page_url, src)).netloc.lower()
                if host and host != self.host:
                    self.scripts["third_party_hosts"].add(host)
                if COOKIE_WORDS.search(src):
                    self.cookie_hints.add(f"script from {host or 'same site'} mentions consent or cookies")
        if a.get("itemtype", "").endswith("BreadcrumbList"):
            self.breadcrumb_signs.add("schema.org BreadcrumbList markup")
        if BREADCRUMB_WORDS.search(a.get("aria-label", "")):
            self.breadcrumb_signs.add("aria-label mentions breadcrumb")
        if BREADCRUMB_WORDS.search(cls_id):
            self.breadcrumb_signs.add("class or id mentions breadcrumb")
        if COOKIE_WORDS.search(cls_id):
            self.cookie_hints.add("an element's class or id mentions cookies or consent")
        if CAROUSEL_WORDS.search(cls_id):
            self.carousel_hints += 1
        if tag in ("video", "audio") and "autoplay" in a:
            self.autoplay_media += 1
        if "aria-current" in a:
            self.aria_current += 1

    def close_link(self):
        link = self.current_link
        text = clean(" ".join(link["text"])) or clean(link["aria"])
        self.links.append({"href": link["href"], "text": text, "nav_top": link["nav_top"],
                           "in_nav": link["in_nav"], "in_footer": link["in_footer"]})
        if self.navs and link["in_nav"]:
            self.navs[-1]["links"] += 1
            if link["nav_top"] and text and len(self.navs[-1]["top_level_links"]) < 25:
                self.navs[-1]["top_level_links"].append(text)
        if self.skip is None and link["href"].startswith("#") and "skip" in text.lower():
            self.skip = {"text": text, "position_among_links": len(self.links)}
        self.current_link = None

    def handle_endtag(self, tag):
        if tag in ("script", "style", "noscript", "template") and self.ignore_depth:
            self.ignore_depth -= 1
        if self.capture == tag and tag in ("title", "h1", "h2"):
            text = clean("".join(self.buffer), 160)
            if tag == "title":
                self.title = text
            elif text:
                getattr(self, tag).append(text)
            self.capture = None
        if tag == "a" and self.current_link is not None:
            self.close_link()
        if tag == "li" and self.nav_region and self.li_depth_in_nav:
            self.li_depth_in_nav -= 1
        if self.nav_region and tag == self.nav_region[0]:
            self.nav_region[1] -= 1
            if self.nav_region[1] == 0:
                self.nav_region = None
        if self.footer_region and tag == self.footer_region[0]:
            self.footer_region[1] -= 1
            if self.footer_region[1] == 0:
                self.footer_region = None
        if tag == "label" and self.label_depth:
            self.label_depth -= 1

    def handle_data(self, data):
        if self.capture:
            self.buffer.append(data)
        if self.ignore_depth:
            return
        if self.current_link is not None:
            self.current_link["text"].append(data)
        self.words += len(data.split())
        if self.footer_region:
            self.footer_text.append(data)

    def result(self, raw_html):
        unlabelled = [i for i in self.inputs
                     if not i["in_label"] and not i["aria"] and not (i["id"] and i["id"] in self.label_for)]
        vague = {}
        for link in self.links:
            t = re.sub(r"[^\w\s]", "", link["text"].lower()).strip()
            if t in VAGUE_PHRASES:
                vague[t] = vague.get(t, 0) + 1
        empty_links = sum(1 for link in self.links if not link["text"])
        help_links = []
        for link in self.links:
            if HELP_WORDS.search(link["text"]) and len(link["text"].split()) <= 5 \
                    and link["text"] not in help_links and len(help_links) < 8:
                help_links.append(link["text"])
        home_paths = {"/", "", "/index.html", "/home"}
        home_links = 0
        for link in self.links:
            parsed = urllib.parse.urlparse(urllib.parse.urljoin(self.page_url, link["href"]))
            if parsed.netloc.lower() == self.host and parsed.path in home_paths and not parsed.fragment:
                home_links += 1
        footer = " ".join(self.footer_text)
        if "BreadcrumbList" in raw_html:
            self.breadcrumb_signs.add("BreadcrumbList structured data")
        if re.search(r"we use cookies|use of cookies|cookie (policy|settings|preferences)", raw_html, re.I):
            self.cookie_hints.add("page text mentions cookies")
        return {
            "title": self.title or None,
            "title_length": len(self.title),
            "lang": self.lang,
            "meta_viewport": self.meta.get("viewport"),
            "meta_description_present": bool(self.meta.get("description")),
            "meta_robots": self.meta.get("robots"),
            "visible_word_count": self.words,
            "landmarks": {"header": self.header, "main": self.main, "footer": self.footer_seen},
            "headings": {"h1_count": len(self.h1), "h1": self.h1[:10],
                         "h2_count": len(self.h2), "h2": self.h2[:30], "h3_count": self.h3_count},
            "navigation": {
                "landmark_count": self.nav_landmarks,
                "landmarks": [{"label": n["label"], "links": n["links"],
                               "top_level_link_count": len(n["top_level_links"]),
                               "top_level_links": n["top_level_links"]} for n in self.navs[:6]],
                "aria_current_count": self.aria_current,
                "home_links": home_links,
            },
            "search": {"search_form": self.search["form"], "search_input": self.search["input"],
                       "search_button_or_toggle": self.search["toggle"]},
            "breadcrumbs": {"present": bool(self.breadcrumb_signs), "signs": sorted(self.breadcrumb_signs)},
            "images": dict(self.images),
            "links": {"total": len(self.links), "empty_text": empty_links,
                      "vague_text_total": sum(vague.values()), "vague_text_by_phrase": vague},
            "forms": {"forms": self.forms, "inputs": len(self.inputs),
                      "inputs_without_label": len(unlabelled),
                      "unlabelled_with_placeholder_only": sum(1 for i in unlabelled if i["placeholder_only"]),
                      "unlabelled_types": sorted({i["type"] for i in unlabelled})},
            "skip_link": {"present": self.skip is not None, **(self.skip or {})},
            "footer_contact": {
                "footer_found": self.footer_seen,
                "phone_pattern": bool(PHONE_RE.search(footer)) or self.footer_tel > 0,
                "email_pattern": bool(EMAIL_RE.search(footer)) or self.footer_mailto > 0,
                "postal_address_pattern": bool(POSTCODE_RE.search(footer)),
            },
            "cookie_banner_hints": sorted(self.cookie_hints),
            "scripts": {"total": self.scripts["total"], "external": self.scripts["external"],
                        "third_party_hosts": sorted(self.scripts["third_party_hosts"])[:25]},
            "help_faq_contact_links": help_links,
            "carousel_or_slider_hints": self.carousel_hints,
            "autoplay_media": self.autoplay_media,
        }


def challenge_check(html, words):
    signs = []
    for vendor, markers in CHALLENGE_SIGNS.items():
        for marker in markers:
            if marker.lower() in html.lower():
                signs.append((vendor, marker))
    if signs and words < 40:
        return {"vendor": signs[0][0], "signs": sorted({m for _, m in signs}), "visible_words": words}
    return None


# ---------- one page ----------

ROBOTS_CACHE = {}


def page_facts(url, site=None, page=None):
    out = {"url": url, "site": site, "page": page, "fetched_at": now_sgt().isoformat(),
           "user_agent": USER_AGENT, "outcome": None, "outcome_note": "", "robots": None,
           "http": None, "challenge": None, "facts": None}
    parsed = urllib.parse.urlparse(url)
    origin = f"{parsed.scheme}://{parsed.netloc}"
    if origin not in ROBOTS_CACHE:
        ROBOTS_CACHE[origin] = fetch_robots(origin)
    info, groups = ROBOTS_CACHE[origin]
    robots = dict(info)
    path = (parsed.path or "/") + (("?" + parsed.query) if parsed.query else "")
    if groups is None:
        robots.update({"allowed": False, "group_used": None, "matched_rule": None})
        kind = robots.get("error") or "skipped_by_robots"
        note = robots["note"]
        if kind == "blocked_by_routine_network":
            note += f" Add {parsed.netloc} under Custom network access in the routine's settings."
        out.update(robots=robots, outcome=kind, outcome_note=note)
        return out
    allowed, group, rule = robots_verdict(groups, path)
    robots.update({"allowed": allowed, "group_used": group if groups else None, "matched_rule": rule})
    out["robots"] = robots
    if not allowed:
        out.update(outcome="skipped_by_robots",
                   outcome_note=f"robots.txt disallows {path} for user-agent '{group}' ({rule}); the page was not fetched.")
        return out

    try:
        status, final_url, headers, body, ms = http_get(url)
    except FetchError as exc:
        out.update(outcome=exc.kind, outcome_note=str(exc))
        if exc.kind == "blocked_by_routine_network":
            out["outcome_note"] += f"; add {parsed.netloc} under Custom network access in the routine's settings."
        return out

    ctype = headers_get(headers, "content-type") or ""
    out["http"] = {"status": status, "final_url": final_url, "redirected": final_url.rstrip("/") != url.rstrip("/"),
                   "response_ms": ms, "bytes": len(body), "content_type": ctype or None,
                   "content_language_header": headers_get(headers, "content-language"),
                   "server_header": headers_get(headers, "server")}
    if status >= 400:
        out.update(outcome="http_error", outcome_note=f"the server answered HTTP {status}.")
        return out
    if "html" not in ctype.lower():
        out.update(outcome="not_html", outcome_note=f"the answer was {ctype or 'of unknown type'}, not an HTML page.")
        return out

    html = decode(body, headers)
    parser = Evidence(final_url)
    try:
        parser.feed(html)
        parser.close()
    except Exception as exc:
        out.update(outcome="parse_error", outcome_note=f"the HTML could not be read: {exc}")
        return out
    challenge = challenge_check(html, parser.words)
    if challenge:
        out.update(outcome="bot_check_page", challenge=challenge,
                   outcome_note=(f"the site answered with a bot-check page from {challenge['vendor']} "
                                 f"({len(body)} bytes, {parser.words} visible words) instead of its content. "
                                 "The audit does not try to get past it."))
        return out
    out.update(outcome="ok", outcome_note="fetched and read.", facts=parser.result(html))
    return out


# ---------- all pages in config.json ----------

def run_all(config_path, date):
    with open(config_path, encoding="utf-8") as fh:
        config = json.load(fh)
    global TIMEOUT
    TIMEOUT = int(config.get("timeout_seconds", TIMEOUT))
    pause = float(config.get("pause_seconds_between_requests", 3))
    base = os.path.dirname(os.path.abspath(config_path))
    raw_dir = os.path.join(base, config.get("report_folder", "reports"), date, "raw")
    os.makedirs(raw_dir, exist_ok=True)
    summary, last_host = [], None
    for site in config["sites"]:
        for page in site["pages"]:
            host = urllib.parse.urlparse(page["url"]).netloc
            if host == last_host:
                time.sleep(pause)
            last_host = host
            facts = page_facts(page["url"], site["key"], page["key"])
            path = os.path.join(raw_dir, f"{site['key']}-{page['key']}.json")
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(facts, fh, indent=2, ensure_ascii=False)
                fh.write("\n")
            http = facts["http"] or {}
            summary.append({"site": site["key"], "page": page["key"], "url": page["url"],
                            "outcome": facts["outcome"], "status": http.get("status"),
                            "response_ms": http.get("response_ms"),
                            "file": os.path.relpath(path, base)})
    return summary


def main():
    ap = argparse.ArgumentParser(description="Collect usability evidence from a page's HTML.")
    ap.add_argument("url", nargs="?")
    ap.add_argument("--site")
    ap.add_argument("--page")
    ap.add_argument("--all", action="store_true", help="fetch every page listed in config.json")
    ap.add_argument("--config", default="config.json")
    ap.add_argument("--date", default=now_sgt().date().isoformat())
    args = ap.parse_args()
    if args.all:
        print(json.dumps(run_all(args.config, args.date), indent=2, ensure_ascii=False))
    elif args.url:
        print(json.dumps(page_facts(args.url, args.site, args.page), indent=2, ensure_ascii=False))
    else:
        ap.error("give a URL or --all")


if __name__ == "__main__":
    main()
