"""
Pillar 7: Organic Search Footprint & Domain Maturity Checker
"""

import re
from typing import Dict, Any
from ..models import PillarResult, CheckResult, CheckStatus, Severity


class OrganicFootprintChecker:
    def __init__(self, rules: Dict[str, Any]):
        self.rules = rules.get("pillars", {}).get("organic_footprint", {})
        self.weight = self.rules.get("weight", 5)

    def run(self, homepage_html: str) -> PillarResult:
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

        return pillar
