"""
AdSenseReady-AI: Master Auditor Orchestrator
"""

import os
import re
import sys
import json
import time
import urllib.request
import urllib.parse
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

import urllib.error

from .models import AuditReport, PillarResult, CheckResult, CheckStatus, Severity


class _NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Disables automatic redirect-following so callers can observe the real
    first-hop status code of a URL (urllib, like most HTTP clients' default
    settings — e.g. `curl -L` — otherwise silently follows 3xx redirects and
    reports the final destination's 200, hiding the fact a redirect happened
    at all)."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None
from .checkers import (
    LegalTrustChecker,
    ContentEEATChecker,
    TechSEOChecker,
    SiteStructureChecker,
    PolicyProhibitedChecker,
    AdLayoutChecker,
    OrganicFootprintChecker,
    CMSDetector,
    WebAppAdSenseEvaluator,
    UniquenessAnalyzer
)

BASE_DIR = Path(__file__).resolve().parent.parent
RULES_PATH = BASE_DIR / "policies" / "adsense_rules.json"


class AdSenseAuditor:
    def __init__(self, rules_path: Optional[Path] = None, user_agent: Optional[str] = None):
        self.rules_path = rules_path or RULES_PATH
        self.rules = self._load_rules()
        self.user_agent = user_agent or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AdSenseReady-AI/2026.11 Crawler"
        self.session_headers = {
            "User-Agent": self.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5"
        }

    def _load_rules(self) -> Dict[str, Any]:
        if self.rules_path.exists():
            with open(self.rules_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"version": "2026.11.0", "pillars": {}}

    def fetch_url(self, url: str, timeout: int = 10) -> Tuple[Optional[str], float, Optional[str]]:
        """Fetches page content, measures response latency, and returns content, latency, and error."""
        start_t = time.time()
        req = urllib.request.Request(url, headers=self.session_headers)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw_bytes = resp.read()
                latency = round(time.time() - start_t, 2)
                # Decode
                try:
                    text = raw_bytes.decode("utf-8")
                except UnicodeDecodeError:
                    text = raw_bytes.decode("latin-1", errors="ignore")
                return text, latency, None
        except Exception as e:
            return None, 0.0, str(e)

    def fetch_status_no_redirect(self, url: str, timeout: int = 8) -> Tuple[Optional[int], Optional[str], Optional[str]]:
        """Returns the REAL first-hop HTTP status code without following any
        redirect, plus the Location header if present. This exists specifically
        to validate sitemap entries: a sitemap should list only final canonical
        URLs. A URL that 301/302-redirects elsewhere still ends up at 200 when
        followed (which is what fetch_url / most crawlers report), which can
        silently hide stale/legacy/non-canonical entries sitting in a sitemap.
        """
        opener = urllib.request.build_opener(_NoRedirectHandler)
        req = urllib.request.Request(url, headers=self.session_headers)
        try:
            with opener.open(req, timeout=timeout) as resp:
                return resp.status, resp.headers.get("Location"), None
        except urllib.error.HTTPError as e:
            # With redirects disabled, a 3xx response surfaces as an HTTPError
            # carrying the real status code — this is the expected path for
            # any sitemap entry that redirects.
            location = e.headers.get("Location") if e.headers else None
            return e.code, location, None
        except Exception as e:
            return None, None, str(e)

    # Link classification used to build the E-E-A-T content-sample pool.
    # Previously only ".jpg"/".png" were excluded from "article_candidates",
    # so on sites whose homepage nav links to CSS files, locale-root pages
    # (e.g. /ar/, /hi/), or a bare "/blog/" index before any real article,
    # the first-6-links sample used for citation/freshness/word-count checks
    # could end up containing ZERO actual articles — silently producing a
    # misleadingly low E-E-A-T score even when every real article page is
    # fully compliant (confirmed live on a Web-App + blog hybrid site).
    _ASSET_EXTENSIONS = (
        ".css", ".js", ".mjs", ".json", ".xml", ".webp", ".svg", ".ico",
        ".woff", ".woff2", ".ttf", ".eot", ".mp4", ".webm", ".mp3",
        ".jpg", ".jpeg", ".png", ".gif", ".pdf", ".zip", ".txt"
    )
    _NON_ARTICLE_PATH_SEGMENTS = ("/category/", "/tag/", "/author/", "/page/", "/feed")
    _BARE_LISTING_NAMES = {"blog", "articles", "guides", "news", "posts", "resources", "updates"}
    _CONTENT_DIR_SEGMENTS = ("/blog/", "/article/", "/articles/", "/post/", "/posts/", "/guide/", "/guides/", "/news/")

    def _is_excluded_from_articles(self, link: str, target_base: str) -> bool:
        """True if `link` should NOT be treated as a candidate article page
        (homepage itself, static assets, bare listing/locale index pages,
        or already-excluded navigational sections)."""
        lower_link = link.lower()
        if link.rstrip("/") == target_base.rstrip("/"):
            return True
        if any(lower_link.endswith(ext) for ext in self._ASSET_EXTENSIONS):
            return True
        if any(seg in lower_link for seg in self._NON_ARTICLE_PATH_SEGMENTS):
            return True
        path_segments = [s for s in urllib.parse.urlparse(link).path.split("/") if s]
        if not path_segments:
            return True
        if len(path_segments) == 1:
            seg0 = path_segments[0].lower()
            if seg0 in self._BARE_LISTING_NAMES:
                return True
            if re.fullmatch(r"[a-z]{2}(-[a-z]{2})?", seg0):
                return True
        return False

    def _article_sort_key(self, link: str) -> tuple:
        """Sort real content-directory URLs (e.g. '/blog/some-slug') ahead of
        other surviving links, so a small sample slice favors actual articles
        over incidental tool/landing pages when both are mixed together."""
        is_content_dir = any(seg in link.lower() for seg in self._CONTENT_DIR_SEGMENTS)
        return (0 if is_content_dir else 1, link)

    def extract_links(self, base_url: str, html: str) -> List[str]:
        """Extracts internal links from HTML."""
        found = set()
        parsed_base = urllib.parse.urlparse(base_url)
        base_domain = parsed_base.netloc.lower()

        hrefs = re.findall(r'href=["\']([^"\'#\s]+)["\']', html, re.IGNORECASE)
        for href in hrefs:
            if href.startswith("javascript:") or href.startswith("mailto:") or href.startswith("tel:"):
                continue
            abs_url = urllib.parse.urljoin(base_url, href)
            parsed = urllib.parse.urlparse(abs_url)
            if parsed.netloc.lower() == base_domain and parsed.scheme in ["http", "https"]:
                # Normalize link
                clean_url = urllib.parse.urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", "", ""))
                found.add(clean_url)
        # IMPORTANT: sort deterministically. Returning list(set(...)) made link order
        # (and therefore which pages land in legal_candidates[:5] / article_candidates[:6]
        # downstream) depend on Python's per-process randomized string hashing, so the
        # exact same site could score differently across runs with zero site changes.
        return sorted(found)

    def audit_site(
        self,
        target_url: str,
        max_crawl_pages: int = 15,
        mock_html: Optional[str] = None,
        mock_articles: Optional[Dict[str, str]] = None
    ) -> AuditReport:
        """Runs the complete 360-degree AdSense Readiness Audit."""
        # Ensure scheme
        if not target_url.startswith("http://") and not target_url.startswith("https://"):
            target_url = "https://" + target_url

        parsed_url = urllib.parse.urlparse(target_url)
        origin = f"{parsed_url.scheme}://{parsed_url.netloc}"
        target_base = target_url.rstrip("/")

        # 1. Fetch Homepage
        if mock_html:
            homepage_html = mock_html
            latency = 0.25
        else:
            homepage_html, latency, err = self.fetch_url(target_url)
            if not homepage_html:
                homepage_html = f"<html><head><title>Offline Analysis</title></head><body>Offline/Error: {err}</body></html>"
                latency = 5.0

        # 2. Extract Internal Links & Sitemaps
        internal_links = self.extract_links(target_url, homepage_html)

        legal_candidates = []
        article_candidates = []

        legal_keywords = ["privacy", "terms", "about", "contact", "disclaimer", "legal", "cookies", "author"]
        for link in internal_links:
            lower_link = link.lower()
            if any(k in lower_link for k in legal_keywords):
                legal_candidates.append(link)
            else:
                if not self._is_excluded_from_articles(link, target_base):
                    article_candidates.append(link)

        # 3. Probe Robots.txt & Sitemap
        robots_txt = None
        sitemap_found = False
        sitemap_url = ""
        ads_txt_content = None
        sitemap_duplicate_count = 0
        sitemap_total_urls = 0
        sitemap_redirect_checked = False
        sitemap_redirect_checked_count = 0
        sitemap_redirect_count = 0
        sitemap_redirect_to_listed_count = 0
        sitemap_redirect_samples: List[str] = []

        if not mock_html:
            target_base = target_url.rstrip("/")
            probe_bases = [target_base] if target_base != origin else [origin]
            if origin not in probe_bases:
                probe_bases.append(origin)

            for b in probe_bases:
                robots_content, _, _ = self.fetch_url(f"{b}/robots.txt", timeout=6)
                if robots_content and "User-agent" in robots_content:
                    robots_txt = robots_content
                    sitemap_match = re.search(r"Sitemap:\s*(\S+)", robots_content, re.IGNORECASE)
                    if sitemap_match:
                        sitemap_found = True
                        sitemap_url = sitemap_match.group(1)
                    break

            if not sitemap_found:
                for b in probe_bases:
                    for s_path in ["/sitemap.xml", "/sitemap_index.xml", "/wp-sitemap.xml"]:
                        s_content, _, _ = self.fetch_url(f"{b}{s_path}", timeout=6)
                        if s_content and ("<urlset" in s_content or "<sitemapindex" in s_content):
                            sitemap_found = True
                            sitemap_url = f"{b}{s_path}"
                            break
                    if sitemap_found:
                        break

            # If sitemap was discovered, extract all <loc> entries into internal_links
            if sitemap_found and sitemap_url:
                s_body, _, _ = self.fetch_url(sitemap_url, timeout=6)
                if s_body:
                    loc_matches = [m.strip() for m in re.findall(r"<loc>([^<]+)</loc>", s_body, re.IGNORECASE) if m.strip()]
                    sitemap_total_urls = len(loc_matches)
                    sitemap_duplicate_count = sitemap_total_urls - len(set(loc_matches))
                    for clean_loc in loc_matches:
                        if clean_loc not in internal_links:
                            internal_links.append(clean_loc)

                    # Sitemap Canonical/Redirect Integrity: a sitemap should list ONLY
                    # final canonical URLs. Checking with fetch_url() alone (which
                    # follows redirects, like `curl -L`) would make a stale/legacy
                    # URL that 301s elsewhere look like a perfectly healthy 200 —
                    # exactly the defect class that hid 7 dead sitemap entries on a
                    # real audited site in production. Sample URLs (capped for
                    # runtime) and check their REAL first-hop status.
                    unique_sitemap_urls = list(dict.fromkeys(loc_matches))
                    sitemap_url_norm_set = {u.rstrip("/") for u in unique_sitemap_urls}
                    MAX_REDIRECT_CHECKS = 40
                    sample_pool = unique_sitemap_urls
                    if len(sample_pool) > MAX_REDIRECT_CHECKS:
                        step = max(1, len(sample_pool) // MAX_REDIRECT_CHECKS)
                        sample_pool = sample_pool[::step][:MAX_REDIRECT_CHECKS]

                    sitemap_redirect_checked = True
                    for u in sample_pool:
                        status, location, _err = self.fetch_status_no_redirect(u, timeout=6)
                        sitemap_redirect_checked_count += 1
                        if status is not None and 300 <= status < 400:
                            sitemap_redirect_count += 1
                            target = location or "(no Location header)"
                            target_abs = urllib.parse.urljoin(u, target) if location else target
                            is_dup = target_abs.rstrip("/") in sitemap_url_norm_set
                            if is_dup:
                                sitemap_redirect_to_listed_count += 1
                            if len(sitemap_redirect_samples) < 6:
                                tag = " [target ALSO separately listed in sitemap]" if is_dup else ""
                                sitemap_redirect_samples.append(f"{u} -> HTTP {status} -> {target_abs}{tag}")

            # Fetch ads.txt (independent of robots.txt / sitemap outcome)
            for b in probe_bases:
                ads_body, _, _ = self.fetch_url(f"{b}/ads.txt", timeout=6)
                if ads_body and ("DIRECT" in ads_body.upper() or "RESELLER" in ads_body.upper()):
                    ads_txt_content = ads_body
                    break

            # Re-categorize legal and article candidates with discovered sitemap links
            for link in internal_links:
                lower_link = link.lower()
                if any(k in lower_link for k in legal_keywords):
                    if link not in legal_candidates:
                        legal_candidates.append(link)
                else:
                    if not self._is_excluded_from_articles(link, target_base):
                        if link not in article_candidates and not link.rstrip("/").endswith("/guides"):
                            article_candidates.append(link)

            # Favor real content-directory URLs (e.g. '/blog/some-slug') over
            # incidental tool/landing pages so the small [:6] sample used for
            # E-E-A-T checks (citations, freshness, word count) actually
            # reflects the site's long-form articles rather than whatever
            # happened to appear first in homepage nav order.
            article_candidates = sorted(article_candidates, key=self._article_sort_key)
        else:
            robots_txt = "User-agent: *\nAllow: /\nUser-agent: Mediapartners-Google\nAllow: /"
            sitemap_found = True
            sitemap_url = f"{origin}/sitemap.xml"

        # 4. Crawl Sample Legal Pages & Articles
        crawled_pages = {"homepage": homepage_html}

        if target_url.startswith("http") and (legal_candidates or article_candidates):
            for l_url in legal_candidates[:5]:
                content, _, _ = self.fetch_url(l_url, timeout=6)
                if content:
                    crawled_pages[l_url] = content

            sample_articles = {}
            for a_url in article_candidates[:6]:
                content, _, _ = self.fetch_url(a_url, timeout=6)
                if content:
                    sample_articles[a_url] = content
                    crawled_pages[a_url] = content
        else:
            if mock_articles:
                article_candidates = list(mock_articles.keys())
                sample_articles = mock_articles
            else:
                # If mock_html is provided without explicit mock_articles, synthesize candidates
                article_candidates = [f"{origin}/post-{i}" for i in range(1, 26)]
                sample_articles = {f"{origin}/post-{i}": homepage_html for i in range(1, 6)}

        # 4.5 Detect Web App Nature early
        total_home_words = len(re.sub(r"<[^>]+>", " ", homepage_html).split())
        is_app = WebAppAdSenseEvaluator.is_interactive_app(homepage_html, total_home_words)

        # 5. Execute 7-Pillar Checkers
        p1 = LegalTrustChecker(self.rules).run(target_url, homepage_html, crawled_pages)
        p2 = ContentEEATChecker(self.rules).run(article_candidates, sample_articles, is_web_app=is_app)
        p3 = TechSEOChecker(self.rules).run(
            target_url, homepage_html, robots_txt, sitemap_found, sitemap_url, latency,
            ads_txt=ads_txt_content,
            sitemap_duplicate_count=sitemap_duplicate_count,
            sitemap_total_urls=sitemap_total_urls,
            ads_txt_checked=not bool(mock_html),
            sitemap_redirect_checked=sitemap_redirect_checked,
            sitemap_redirect_checked_count=sitemap_redirect_checked_count,
            sitemap_redirect_count=sitemap_redirect_count,
            sitemap_redirect_to_listed_count=sitemap_redirect_to_listed_count,
            sitemap_redirect_samples=sitemap_redirect_samples
        )
        p4 = SiteStructureChecker(self.rules).run(
            homepage_html, crawled_pages, internal_links,
            fetcher=self.fetch_url
        )
        p5 = PolicyProhibitedChecker(self.rules).run(homepage_html, crawled_pages, target_url=target_url)
        p6 = AdLayoutChecker(self.rules).run(homepage_html)
        p7 = OrganicFootprintChecker(self.rules).run(homepage_html)

        pillars = {
            "legal_trust": p1,
            "content_eeat": p2,
            "technical_seo": p3,
            "site_navigation_ux": p4,
            "google_publisher_policy": p5,
            "ad_layout_readiness": p6,
            "organic_footprint": p7
        }

        # 6. Detect CMS Platform & Web App Nature
        cms_data = CMSDetector.detect(homepage_html)
        # Evidence-based filter: drop the generic AdSense meta-tag tip if that tag
        # is already present in the fetched HTML (previously this tip was shown
        # unconditionally regardless of whether the site already had it).
        has_adsense_meta = bool(re.search(r'<meta[^>]+name=["\']google-adsense-account["\']', homepage_html, re.IGNORECASE))
        if has_adsense_meta and cms_data.get("customized_tips"):
            cms_data["customized_tips"] = [
                t for t in cms_data["customized_tips"] if "google-adsense-account" not in t
            ]
        
        # Check if site is an interactive web app / SaaS utility
        web_app_data = None
        if is_app:
            web_app_data = WebAppAdSenseEvaluator.evaluate_app(target_url, homepage_html, internal_links)

        # 7. Lexical Diversity & Uniqueness Analysis
        all_text = " ".join(re.sub(r"<[^>]+>", " ", h).strip() for h in crawled_pages.values())
        lexical_data = UniquenessAnalyzer.evaluate(all_text)

        # 8. Aggregate Composite Scores
        # IMPORTANT FIX: this used to be a flat sum of every check's raw points
        # across all pillars, completely ignoring `pillar.weight`. The README
        # advertises "Legal & Trust 20%, Content/EEAT 25%, ..." but that
        # percentage was never actually applied anywhere in the scoring math —
        # a pillar's real influence on the headline score depended purely on
        # how many points its individual checks happened to add up to, which
        # also meant every time a new check was added to a pillar, ALL of that
        # pillar's other checks had to be manually re-scored to keep the total
        # matching its stated weight (fragile and easy to silently break).
        # Fix: normalize each pillar to its own percentage first, then combine
        # using its declared weight, so the stated 7-pillar weighting is real.
        total_weight = sum(p.weight for p in pillars.values()) or 100.0
        weighted_points = sum(p.percentage * p.weight for p in pillars.values()) / 100.0
        total_score = round(weighted_points, 2)
        max_possible = round(total_weight, 2)
        normalized_score = round((total_score / max_possible) * 100, 1) if max_possible > 0 else 0

        # Gather Blockers & High Severity Issues
        all_blockers = []
        action_plan = []
        for pillar in pillars.values():
            for c in pillar.checks:
                if c.status == CheckStatus.FAIL and c.severity == Severity.BLOCKER:
                    all_blockers.append(c)
                    action_plan.append(f"[CRITICAL BLOCKER] {c.name}: {c.fix_recommendation or c.details}")
                elif c.status in [CheckStatus.FAIL, CheckStatus.WARNING] and c.severity == Severity.HIGH:
                    action_plan.append(f"[HIGH PRIORITY] {c.name}: {c.fix_recommendation or c.details}")
                elif c.status == CheckStatus.WARNING:
                    action_plan.append(f"[RECOMMENDED] {c.name}: {c.fix_recommendation or c.details}")

        # Add Web App specific guidance if applicable
        if web_app_data:
            action_plan.append(f"[WEB APP ROADMAP] Utility App Detected: Add a dedicated /how-it-works or /guide page with 800+ words to pass AdSense without changing your UI.")

        # Add CMS specific tips
        if cms_data.get("customized_tips"):
            for tip in cms_data["customized_tips"][:2]:
                action_plan.append(f"[{cms_data['cms']} OPTIMIZATION] {tip}")

        # Verdict Logic
        if len(all_blockers) == 0 and normalized_score >= 85.0:
            verdict = "APPROVED_READY"
            summary_verdict = "10/10 READY FOR ADSENSE APPROVAL (High Confidence)"
        elif len(all_blockers) == 0 and normalized_score >= 65.0:
            verdict = "AT_RISK"
            summary_verdict = "AT RISK - POLISH REQUIRED (Moderate Confidence)"
        else:
            verdict = "REJECTION_GUARANTEED"
            summary_verdict = f"REJECTION RISK - {len(all_blockers)} CRITICAL BLOCKER(S) DETECTED"

        return AuditReport(
            target_url=target_url,
            timestamp=datetime.utcnow().isoformat() + "Z",
            policy_version=self.rules.get("version", "2026.11.1"),
            total_score=total_score,
            max_possible=max_possible,
            verdict=verdict,
            summary_verdict=summary_verdict,
            pillars=pillars,
            all_blockers=all_blockers,
            action_plan=action_plan,
            cms_info=cms_data,
            web_app_eval=web_app_data,
            lexical_eval=lexical_data
        )
