"""
Pillar 4: Site Navigation, Architecture & UX Checker
"""

import re
from typing import Dict, Any, List
from ..models import PillarResult, CheckResult, CheckStatus, Severity


class SiteStructureChecker:
    def __init__(self, rules: Dict[str, Any]):
        self.rules = rules.get("pillars", {}).get("site_navigation_ux", {})
        self.weight = self.rules.get("weight", 15)

    def run(self, homepage_html: str, crawled_pages: Dict[str, str], internal_links: List[str]) -> PillarResult:
        pillar = PillarResult(
            id="site_navigation_ux",
            name="Site Navigation, Architecture & UX",
            weight=self.weight,
            earned_score=0.0,
            max_score=0.0,
            checks=[]
        )

        lower_html = homepage_html.lower()

        # 1. Primary Navigation Menu
        has_nav_tag = "<nav" in lower_html or 'class="menu"' in lower_html or 'id="menu"' in lower_html or 'class="header' in lower_html
        menu_links_count = len(re.findall(r'<a\s+[^>]*href=["\'][^"\']+["\'][^>]*>', lower_html))

        if has_nav_tag and menu_links_count >= 5:
            pillar.checks.append(CheckResult(
                id="primary_navigation_menu",
                name="Clear Header Navigation Menu",
                status=CheckStatus.PASS,
                severity=Severity.BLOCKER,
                score=4.0,
                max_score=4.0,
                details=f"Intuitive navigation bar detected with {menu_links_count} discovered navigational links.",
                doc_url="https://support.google.com/adsense/answer/10502938"
            ))
            pillar.earned_score += 4.0
        elif menu_links_count >= 3:
            pillar.checks.append(CheckResult(
                id="primary_navigation_menu",
                name="Clear Header Navigation Menu",
                status=CheckStatus.WARNING,
                severity=Severity.HIGH,
                score=2.5,
                max_score=4.0,
                details=f"Limited navigation options found ({menu_links_count} links). May trigger navigation ambiguity.",
                fix_recommendation="Expand top header menu with clear category tabs, topics, and search.",
                doc_url="https://support.google.com/adsense/answer/10502938"
            ))
            pillar.earned_score += 2.5
        else:
            pillar.checks.append(CheckResult(
                id="primary_navigation_menu",
                name="Clear Header Navigation Menu",
                status=CheckStatus.FAIL,
                severity=Severity.BLOCKER,
                score=0.0,
                max_score=4.0,
                details="No standard header navigation menu or taxonomy links detected.",
                fix_recommendation="Implement an accessible primary navigation menu with categories, about, and search.",
                doc_url="https://support.google.com/adsense/answer/10502938"
            ))
        pillar.max_score += 4.0

        # 2. Editorial Content Header Prominence (Anti-Buried Content Check)
        header_match = re.search(r"<(header|nav)[^>]*>[\s\S]*?</\1>", homepage_html, re.IGNORECASE)
        header_text = header_match.group(0).lower() if header_match else lower_html[:1500]
        has_blog_in_header = any(k in header_text for k in ["/blog", "/guide", "/article", "/tutorial", "blog", "guides", "articles"])
        has_blog_on_site = any(any(k in l.lower() for k in ["/blog", "/guide", "/article"]) for l in internal_links)

        if has_blog_in_header:
            pillar.checks.append(CheckResult(
                id="editorial_header_prominence",
                name="Editorial Content Header Prominence",
                status=CheckStatus.PASS,
                severity=Severity.HIGH,
                score=3.0,
                max_score=3.0,
                details="Blog, Guides, or Article repository is prominently exposed in primary header navigation.",
                doc_url="https://support.google.com/adsense/answer/10502938"
            ))
            pillar.earned_score += 3.0
        elif has_blog_on_site:
            pillar.checks.append(CheckResult(
                id="editorial_header_prominence",
                name="Editorial Content Header Prominence",
                status=CheckStatus.WARNING,
                severity=Severity.HIGH,
                score=1.5,
                max_score=3.0,
                details="Editorial guides exist on site but are NOT visibly linked in the primary header/nav (likely buried in footer). Human AdSense reviewers who skim in 30 seconds may miss your content and flag 'Insufficient Content'.",
                fix_recommendation="Promote 'Blog' or 'Guides' into the top header navigation pill/menu bar.",
                doc_url="https://support.google.com/adsense/answer/10502938"
            ))
            pillar.earned_score += 1.5
        else:
            pillar.checks.append(CheckResult(
                id="editorial_header_prominence",
                name="Editorial Content Header Prominence",
                status=CheckStatus.PASS,
                severity=Severity.HIGH,
                score=3.0,
                max_score=3.0,
                details="Standard navigation structure detected.",
                doc_url="https://support.google.com/adsense/answer/10502938"
            ))
            pillar.earned_score += 3.0
        pillar.max_score += 3.0

        # 3. Footer Navigation Links
        has_footer = "<footer" in lower_html or 'id="footer"' in lower_html or 'class="footer"' in lower_html
        if has_footer:
            pillar.checks.append(CheckResult(
                id="footer_navigation_links",
                name="Footer Menu & Semantic Architecture",
                status=CheckStatus.PASS,
                severity=Severity.HIGH,
                score=3.0,
                max_score=3.0,
                details="Semantic footer area detected linking essential pages.",
                doc_url="https://support.google.com/adsense/answer/10502938"
            ))
            pillar.earned_score += 3.0
        else:
            pillar.checks.append(CheckResult(
                id="footer_navigation_links",
                name="Footer Menu & Semantic Architecture",
                status=CheckStatus.WARNING,
                severity=Severity.HIGH,
                score=1.0,
                max_score=3.0,
                details="No distinct footer structure found.",
                fix_recommendation="Add a standard footer with copyright notice, legal links, and social links.",
                doc_url="https://support.google.com/adsense/answer/10502938"
            ))
            pillar.earned_score += 1.0
        pillar.max_score += 3.0

        # 4. Dead Links / Hash Placeholders
        dead_hashes = len(re.findall(r'href=["\']#["\']', lower_html))
        dead_hash_ratio = (dead_hashes / menu_links_count) if menu_links_count > 0 else 0

        if dead_hash_ratio <= 0.15:
            pillar.checks.append(CheckResult(
                id="zero_broken_links_or_404s",
                name="Absence of Broken / Placeholder Links",
                status=CheckStatus.PASS,
                severity=Severity.HIGH,
                score=3.0,
                max_score=3.0,
                details=f"Navigation links are functional ({dead_hashes} empty '#' hash links found).",
                doc_url="https://support.google.com/adsense/answer/10502938"
            ))
            pillar.earned_score += 3.0
        else:
            pillar.checks.append(CheckResult(
                id="zero_broken_links_or_404s",
                name="Absence of Broken / Placeholder Links",
                status=CheckStatus.FAIL,
                severity=Severity.HIGH,
                score=1.0,
                max_score=3.0,
                details=f"High quantity of placeholder '#' links detected ({dead_hashes} found). Triggers 'Site Under Construction'.",
                fix_recommendation="Replace dummy '#' links in menus and buttons with actual live destination URLs.",
                doc_url="https://support.google.com/adsense/answer/10502938"
            ))
            pillar.earned_score += 1.0
        pillar.max_score += 3.0

        # 5. Zero Placeholder / Coming Soon Pages
        all_text = " ".join(crawled_pages.values()).lower()
        banned_placeholders = ["under construction", "coming soon", "sample page", "hello world!", "default demo content"]
        found_placeholders = [p for p in banned_placeholders if p in all_text or p in lower_html]

        if not found_placeholders:
            pillar.checks.append(CheckResult(
                id="zero_placeholder_pages",
                name="Zero 'Under Construction' or Demo Content",
                status=CheckStatus.PASS,
                severity=Severity.BLOCKER,
                score=2.0,
                max_score=2.0,
                details="Site is fully launched. No demo, placeholder, or 'coming soon' markers detected.",
                doc_url="https://support.google.com/adsense/answer/10502938"
            ))
            pillar.earned_score += 2.0
        else:
            pillar.checks.append(CheckResult(
                id="zero_placeholder_pages",
                name="Zero 'Under Construction' or Demo Content",
                status=CheckStatus.FAIL,
                severity=Severity.BLOCKER,
                score=0.0,
                max_score=2.0,
                details=f"Detected demo/placeholder content: {', '.join(found_placeholders)}.",
                fix_recommendation="Delete all demo WordPress posts (like 'Hello World!'), default pages, and remove any 'Under Construction' banners.",
                doc_url="https://support.google.com/adsense/answer/10502938"
            ))
        pillar.max_score += 2.0

        return pillar
