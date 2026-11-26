"""
Pillar 7: Organic Search Footprint & Domain Maturity Checker
"""

import re
from urllib.parse import urlparse
from typing import Dict, Any, Optional, List
from ..models import PillarResult, CheckResult, CheckStatus, Severity


class OrganicFootprintChecker:
    def __init__(self, rules: Dict[str, Any]):
        self.rules = rules.get("pillars", {}).get("organic_footprint", {})
        self.weight = self.rules.get("weight", 5)

    @staticmethod
    def _has_noindex(html: str, headers: Optional[Dict[str, str]] = None) -> bool:
        if headers:
            for k, v in headers.items():
                if k.lower() == "x-robots-tag" and "noindex" in str(v).lower():
                    return True
        return bool(re.search(r'<meta[^>]+name=["\'](?:robots|googlebot)["\'][^>]*content=["\'][^"\']*noindex', html, re.I)) or \
               bool(re.search(r'<meta[^>]+content=["\'][^"\']*noindex[^"\']*["\'][^>]*name=["\'](?:robots|googlebot)["\']', html, re.I))

    def run(
        self,
        homepage_html: str,
        base_url: str = "",
        crawled_pages: Optional[Dict[str, str]] = None,
        page_headers: Optional[Dict[str, Dict[str, str]]] = None
    ) -> PillarResult:
        pillar = PillarResult(
            id="organic_footprint",
            name="Organic Search Footprint & Domain Maturity",
            weight=self.weight,
            earned_score=0.0,
            max_score=0.0,
            checks=[]
        )

        lower_html = homepage_html.lower()

        # 1. Canonical Tag & Search Indexability
        has_canonical = bool(re.search(r'<link[^>]+rel=["\']canonical["\']', lower_html))
        is_noindex = bool(re.search(r'<meta[^>]+content=["\'][^"\']*noindex[^"\']*["\']', lower_html))

        if is_noindex:
            pillar.checks.append(CheckResult(
                id="search_console_indexing_signals",
                name="Search Indexing & Canonical Directives",
                status=CheckStatus.FAIL,
                severity=Severity.BLOCKER,
                score=0.0,
                max_score=3.0,
                details="CRITICAL BLOCKER: Site contains 'noindex' meta tag. Google cannot index or evaluate the website.",
                fix_recommendation="Remove 'noindex' directive from meta tags or CMS SEO settings.",
                doc_url="https://developers.google.com/search/docs/crawling-indexing/block-indexing"
            ))
        elif has_canonical:
            pillar.checks.append(CheckResult(
                id="search_console_indexing_signals",
                name="Search Indexing & Canonical Directives",
                status=CheckStatus.PASS,
                severity=Severity.HIGH,
                score=3.0,
                max_score=3.0,
                details="Canonical URLs specified and indexation permitted.",
                doc_url="https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls"
            ))
            pillar.earned_score += 3.0
        else:
            pillar.checks.append(CheckResult(
                id="search_console_indexing_signals",
                name="Search Indexing & Canonical Directives",
                status=CheckStatus.WARNING,
                severity=Severity.MEDIUM,
                score=1.5,
                max_score=3.0,
                details="No canonical link tag found. Indexable, but duplicate content risk exists.",
                fix_recommendation="Add self-referencing <link rel='canonical' href='...'> to all pages.",
                doc_url="https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls"
            ))
            pillar.earned_score += 1.5
        pillar.max_score += 3.0

        # 2. Schema.org / Structured Data — actually PARSE each JSON-LD block, not just
        # check for the substring "application/ld+json". A page can contain that
        # substring while the JSON itself is malformed (e.g. an article title with an
        # unescaped double-quote breaks the whole block), which Google's Rich Results
        # parser will silently reject. A pure substring check can never catch that.
        ld_json_blocks = re.findall(
            r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
            homepage_html, re.IGNORECASE | re.DOTALL
        )
        has_itemscope = "itemscope" in lower_html

        if ld_json_blocks:
            import json as _json
            malformed = []
            for idx, block in enumerate(ld_json_blocks):
                try:
                    _json.loads(block.strip())
                except Exception as e:
                    malformed.append(f"block #{idx + 1}: {e}")

            if not malformed:
                pillar.checks.append(CheckResult(
                    id="structured_data_breadcrumbs",
                    name="Schema.org Structured Data & Rich Snippets",
                    status=CheckStatus.PASS,
                    severity=Severity.MEDIUM,
                    score=2.0,
                    max_score=2.0,
                    details=f"{len(ld_json_blocks)} JSON-LD block(s) found and all parsed as valid JSON.",
                    doc_url="https://developers.google.com/search/docs/appearance/structured-data/intro-structured-data"
                ))
                pillar.earned_score += 2.0
            else:
                pillar.checks.append(CheckResult(
                    id="structured_data_breadcrumbs",
                    name="Schema.org Structured Data & Rich Snippets",
                    status=CheckStatus.FAIL,
                    severity=Severity.HIGH,
                    score=0.3,
                    max_score=2.0,
                    details=f"{len(malformed)} of {len(ld_json_blocks)} JSON-LD block(s) are MALFORMED and will be silently rejected by Google's structured data parser: {'; '.join(malformed[:3])}.",
                    fix_recommendation="Properly JSON-escape any dynamic/interpolated values (titles, descriptions) injected into JSON-LD — unescaped quotes or control characters are the most common cause.",
                    doc_url="https://developers.google.com/search/docs/appearance/structured-data/intro-structured-data"
                ))
                pillar.earned_score += 0.3
        elif has_itemscope:
            pillar.checks.append(CheckResult(
                id="structured_data_breadcrumbs",
                name="Schema.org Structured Data & Rich Snippets",
                status=CheckStatus.PASS,
                severity=Severity.MEDIUM,
                score=1.6,
                max_score=2.0,
                details="Microdata (itemscope) structured data detected (no JSON-LD present).",
                doc_url="https://developers.google.com/search/docs/appearance/structured-data/intro-structured-data"
            ))
            pillar.earned_score += 1.6
        else:
            pillar.checks.append(CheckResult(
                id="structured_data_breadcrumbs",
                name="Schema.org Structured Data & Rich Snippets",
                status=CheckStatus.WARNING,
                severity=Severity.LOW,
                score=1.0,
                max_score=2.0,
                details="No Schema.org JSON-LD found (strongly recommended for modern E-E-A-T entity recognition).",
                fix_recommendation="Implement JSON-LD Schema (WebSite, Organization, Article, BreadcrumbList).",
                doc_url="https://developers.google.com/search/docs/appearance/structured-data/intro-structured-data"
            ))
            pillar.earned_score += 1.0
        pillar.max_score += 2.0

        # 3. Canonical Trailing-Slash & Host Consistency
        canon_match = re.search(r'<link\b[^>]*rel=["\']canonical["\'][^>]*href=["\']([^"\']+)["\']', homepage_html, re.I)
        if not canon_match:
            canon_match = re.search(r'<link\b[^>]*href=["\']([^"\']+)["\'][^>]*rel=["\']canonical["\']', homepage_html, re.I)
        if canon_match and base_url:
            canon_u = urlparse(canon_match.group(1).strip())
            base_u = urlparse(base_url.strip())
            host_mismatch = canon_u.netloc and base_u.netloc and canon_u.netloc.lower() != base_u.netloc.lower()
            slash_mismatch = (canon_u.path or "/") != (base_u.path or "/")
            if host_mismatch or slash_mismatch:
                pillar.checks.append(CheckResult(
                    id="canonical_slash_host_consistency",
                    name="Canonical URL Host & Trailing-Slash Consistency",
                    status=CheckStatus.WARNING,
                    severity=Severity.MEDIUM,
                    score=0.5,
                    max_score=2.0,
                    details=f"Fetched URL ({base_url}) differs from declared canonical ({canon_match.group(1)}).",
                    fix_recommendation="Ensure self-referencing canonical URLs match the exact served host and trailing-slash convention.",
                    doc_url="https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls"
                ))
                pillar.earned_score += 0.5
            else:
                pillar.checks.append(CheckResult(
                    id="canonical_slash_host_consistency",
                    name="Canonical URL Host & Trailing-Slash Consistency",
                    status=CheckStatus.PASS,
                    severity=Severity.MEDIUM,
                    score=2.0,
                    max_score=2.0,
                    details="Declared canonical URL matches the served host and trailing-slash path.",
                    doc_url="https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls"
                ))
                pillar.earned_score += 2.0
            pillar.max_score += 2.0

        # 4. Hreflang Integrity & Hreflang <-> Noindex Conflict Check
        hreflang_links = re.findall(
            r'<link\b[^>]*rel=["\']alternate["\'][^>]*hreflang=["\']([^"\']+)["\'][^>]*href=["\']([^"\']+)["\']',
            homepage_html, re.I
        )
        if hreflang_links:
            langs = [h[0].lower() for h in hreflang_links]
            has_x_default = "x-default" in langs
            noindex_conflicts: List[str] = []
            if crawled_pages:
                for lang, target_href in hreflang_links:
                    page_html = crawled_pages.get(target_href) or crawled_pages.get(target_href.rstrip("/")) or crawled_pages.get(target_href + "/")
                    hdrs = (page_headers or {}).get(target_href)
                    if page_html and self._has_noindex(page_html, hdrs):
                        noindex_conflicts.append(f"{lang} -> {target_href}")

            if noindex_conflicts:
                pillar.checks.append(CheckResult(
                    id="hreflang_integrity",
                    name="Hreflang Integrity & Noindex Conflict Check",
                    status=CheckStatus.FAIL,
                    severity=Severity.HIGH,
                    score=0.0,
                    max_score=2.0,
                    details=f"Hreflang points to {len(noindex_conflicts)} noindex target(s): {', '.join(noindex_conflicts[:3])}. Google warns against hreflang targeting non-indexable URLs.",
                    fix_recommendation="Remove hreflang <link> tags pointing to noindex pages, or make those localized pages indexable.",
                    doc_url="https://developers.google.com/search/docs/specialty/international/localized-versions"
                ))
            elif not has_x_default:
                pillar.checks.append(CheckResult(
                    id="hreflang_integrity",
                    name="Hreflang Integrity & Noindex Conflict Check",
                    status=CheckStatus.WARNING,
                    severity=Severity.LOW,
                    score=1.2,
                    max_score=2.0,
                    details=f"Found {len(hreflang_links)} hreflang tags without an 'x-default' fallback.",
                    fix_recommendation="Add <link rel='alternate' hreflang='x-default' href='...'> for unmatched locales.",
                    doc_url="https://developers.google.com/search/docs/specialty/international/localized-versions"
                ))
                pillar.earned_score += 1.2
            else:
                pillar.checks.append(CheckResult(
                    id="hreflang_integrity",
                    name="Hreflang Integrity & Noindex Conflict Check",
                    status=CheckStatus.PASS,
                    severity=Severity.MEDIUM,
                    score=2.0,
                    max_score=2.0,
                    details=f"Valid hreflang configuration ({len(hreflang_links)} tags including x-default, 0 noindex conflicts).",
                    doc_url="https://developers.google.com/search/docs/specialty/international/localized-versions"
                ))
                pillar.earned_score += 2.0
            pillar.max_score += 2.0

        # 5. Multi-Page & HTTP X-Robots-Tag Noindex Audit
        if crawled_pages or page_headers:
            noindex_pages = []
            for p_url, p_html in (crawled_pages or {}).items():
                hdrs = (page_headers or {}).get(p_url)
                if self._has_noindex(p_html, hdrs):
                    noindex_pages.append(p_url)
            if noindex_pages:
                pillar.checks.append(CheckResult(
                    id="multi_page_noindex_audit",
                    name="Inner Page & X-Robots-Tag Indexability Audit",
                    status=CheckStatus.WARNING,
                    severity=Severity.MEDIUM,
                    score=1.0,
                    max_score=2.0,
                    details=f"Detected 'noindex' (meta or X-Robots-Tag) on {len(noindex_pages)} sampled inner URL(s): {', '.join(noindex_pages[:3])}. Ensure intentional consolidation (not accidental de-indexing).",
                    doc_url="https://developers.google.com/search/docs/crawling-indexing/block-indexing"
                ))
                pillar.earned_score += 1.0
            else:
                pillar.checks.append(CheckResult(
                    id="multi_page_noindex_audit",
                    name="Inner Page & X-Robots-Tag Indexability Audit",
                    status=CheckStatus.PASS,
                    severity=Severity.MEDIUM,
                    score=2.0,
                    max_score=2.0,
                    details="No unexpected noindex meta tags or X-Robots-Tag headers detected on sampled inner pages.",
                    doc_url="https://developers.google.com/search/docs/crawling-indexing/block-indexing"
                ))
                pillar.earned_score += 2.0
            pillar.max_score += 2.0

        return pillar
