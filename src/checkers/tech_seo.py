"""
Pillar 3: Technical Crawlability & Web Health Checker
"""

import re
import json
from typing import Dict, Any, Optional
from ..models import PillarResult, CheckResult, CheckStatus, Severity


class TechSEOChecker:
    def __init__(self, rules: Dict[str, Any]):
        self.rules = rules.get("pillars", {}).get("technical_seo", {})
        self.weight = self.rules.get("weight", 15)

    def run(
        self,
        base_url: str,
        homepage_html: str,
        robots_txt: Optional[str],
        sitemap_found: bool,
        sitemap_url: str,
        latency_seconds: float,
        sitemap_health: Optional[Dict[str, Any]] = None,
        ads_txt: Optional[str] = None,
        sitemap_duplicate_count: int = 0,
        sitemap_total_urls: int = 0,
        ads_txt_checked: bool = True,
        sitemap_redirect_checked: bool = False,
        sitemap_redirect_checked_count: int = 0,
        sitemap_redirect_count: int = 0,
        sitemap_redirect_to_listed_count: int = 0,
        sitemap_redirect_samples: Optional[list] = None
    ) -> PillarResult:
        pillar = PillarResult(
            id="technical_seo",
            name="Technical Crawlability & Web Health",
            weight=self.weight,
            earned_score=0.0,
            max_score=0.0,
            checks=[]
        )

        # 1. HTTPS / SSL Enforcement
        is_https = base_url.lower().startswith("https://")
        if is_https:
            pillar.checks.append(CheckResult(
                id="ssl_https_enforcement",
                name="HTTPS / SSL Encryption",
                status=CheckStatus.PASS,
                severity=Severity.BLOCKER,
                score=2.5,
                max_score=2.5,
                details="Site is served over secure HTTPS protocol.",
                doc_url="https://developers.google.com/search/docs/crawling-indexing/https"
            ))
            pillar.earned_score += 2.5
        else:
            pillar.checks.append(CheckResult(
                id="ssl_https_enforcement",
                name="HTTPS / SSL Encryption",
                status=CheckStatus.FAIL,
                severity=Severity.BLOCKER,
                score=0.0,
                max_score=2.5,
                details="Site is not enforcing HTTPS. AdSense requires SSL across all monetized domains.",
                fix_recommendation="Install an SSL certificate (e.g. Let's Encrypt or Cloudflare) and enforce HTTPS redirect.",
                doc_url="https://developers.google.com/search/docs/crawling-indexing/https"
            ))
        pillar.max_score += 2.5

        # 2. Robots.txt crawlability
        if robots_txt is not None:
            robots_lower = robots_txt.lower()
            allows_mediapartners = bool(re.search(r"user-agent:\s*mediapartners-google\s*[\r\n]+\s*allow:\s*/(?:\s|$)", robots_lower))
            blocks_mediapartners = bool(re.search(r"user-agent:\s*mediapartners-google\s*[\r\n]+\s*disallow:\s*/(?:\s|$)", robots_lower))
            blocks_all = bool(re.search(r"user-agent:\s*\*\s*[\r\n]+\s*disallow:\s*/(?:\s|$)", robots_lower)) and not allows_mediapartners

            if blocks_mediapartners:
                pillar.checks.append(CheckResult(
                    id="robots_txt_accessibility",
                    name="Robots.txt AdSense Crawler Access",
                    status=CheckStatus.FAIL,
                    severity=Severity.BLOCKER,
                    score=0.0,
                    max_score=2.5,
                    details="CRITICAL BLOCKER: Robots.txt explicitly disallows 'Mediapartners-Google' crawler.",
                    fix_recommendation="Remove disallow rule for User-agent: Mediapartners-Google in robots.txt immediately.",
                    doc_url="https://support.google.com/adsense/answer/10532"
                ))
            elif blocks_all:
                pillar.checks.append(CheckResult(
                    id="robots_txt_accessibility",
                    name="Robots.txt AdSense Crawler Access",
                    status=CheckStatus.FAIL,
                    severity=Severity.BLOCKER,
                    score=0.3,
                    max_score=2.5,
                    details="Robots.txt disallows all crawlers ('User-agent: * Disallow: /') without an exemption for AdSense.",
                    fix_recommendation="Update robots.txt to allow Googlebot and Mediapartners-Google to crawl public content.",
                    doc_url="https://support.google.com/adsense/answer/10532"
                ))
                pillar.earned_score += 0.3
            else:
                pillar.checks.append(CheckResult(
                    id="robots_txt_accessibility",
                    name="Robots.txt AdSense Crawler Access",
                    status=CheckStatus.PASS,
                    severity=Severity.BLOCKER,
                    score=2.5,
                    max_score=2.5,
                    details="Robots.txt allows Googlebot and Mediapartners-Google.",
                    doc_url="https://support.google.com/adsense/answer/10532"
                ))
                pillar.earned_score += 2.5
        else:
            pillar.checks.append(CheckResult(
                id="robots_txt_accessibility",
                name="Robots.txt AdSense Crawler Access",
                status=CheckStatus.WARNING,
                severity=Severity.MEDIUM,
                score=1.5,
                max_score=2.5,
                details="No robots.txt detected (defaults to allow-all, but explicit robots.txt is recommended).",
                fix_recommendation="Create a clean /robots.txt declaring sitemap and permitting Mediapartners-Google.",
                doc_url="https://support.google.com/adsense/answer/10532"
            ))
            pillar.earned_score += 1.5
        pillar.max_score += 2.5

        # 3. XML Sitemap Detected (and validated for internal duplicate <loc> entries & health)
        if sitemap_found:
            if sitemap_health:
                dead_404_count = sitemap_health.get("dead_404_count", 0)
                sampled_count = sitemap_health.get("sampled_count", 0)
                redirect_count = sitemap_health.get("redirect_count", 0)
                dead_rate = (dead_404_count / sampled_count) if sampled_count > 0 else 0.0

                if dead_rate > 0.05:
                    pillar.checks.append(CheckResult(
                        id="sitemap_xml_detected",
                        name="XML Sitemap Detection & Integrity",
                        status=CheckStatus.FAIL,
                        severity=Severity.BLOCKER,
                        score=0.5,
                        max_score=2.5,
                        details=f"CRITICAL BLOCKER: Sitemap contains high dead-end rate ({dead_404_count}/{sampled_count} tested URLs returned 404).",
                        fix_recommendation="Prune dead URLs from sitemap.xml immediately.",
                        doc_url="https://developers.google.com/search/docs/crawling-indexing/sitemaps/overview"
                    ))
                    pillar.earned_score += 0.5
                elif redirect_count > 0:
                    pillar.checks.append(CheckResult(
                        id="sitemap_xml_detected",
                        name="XML Sitemap Detection & Integrity",
                        status=CheckStatus.WARNING,
                        severity=Severity.MEDIUM,
                        score=1.5,
                        max_score=2.5,
                        details=f"Sitemap detected with {redirect_count} non-canonical redirecting URLs.",
                        fix_recommendation="Remove 301-redirecting duplicate URLs from sitemap.xml.",
                        doc_url="https://developers.google.com/search/docs/crawling-indexing/sitemaps/overview"
                    ))
                    pillar.earned_score += 1.5
                else:
                    pillar.checks.append(CheckResult(
                        id="sitemap_xml_detected",
                        name="XML Sitemap Detection & Integrity",
                        status=CheckStatus.PASS,
                        severity=Severity.HIGH,
                        score=2.5,
                        max_score=2.5,
                        details=f"Valid XML sitemap detected at {sitemap_url} with 0% dead-link error rate across sampled entries.",
                        doc_url="https://developers.google.com/search/docs/crawling-indexing/sitemaps/overview"
                    ))
                    pillar.earned_score += 2.5
            else:
                dup_ratio = (sitemap_duplicate_count / sitemap_total_urls) if sitemap_total_urls > 0 else 0.0
                if sitemap_duplicate_count == 0:
                    pillar.checks.append(CheckResult(
                        id="sitemap_xml_detected",
                        name="XML Sitemap Detection & Integrity",
                        status=CheckStatus.PASS,
                        severity=Severity.HIGH,
                        score=2.5,
                        max_score=2.5,
                        details=f"Valid XML sitemap detected at {sitemap_url} ({sitemap_total_urls} URLs, no duplicate <loc> entries).",
                        doc_url="https://developers.google.com/search/docs/crawling-indexing/sitemaps/overview"
                    ))
                    pillar.earned_score += 2.5
                elif dup_ratio <= 0.05:
                    pillar.checks.append(CheckResult(
                        id="sitemap_xml_detected",
                        name="XML Sitemap Detection & Integrity",
                        status=CheckStatus.WARNING,
                        severity=Severity.MEDIUM,
                        score=1.8,
                        max_score=2.5,
                        details=f"Sitemap at {sitemap_url} found with {sitemap_duplicate_count} duplicate <loc> entries out of {sitemap_total_urls} ({dup_ratio*100:.1f}%).",
                        fix_recommendation="De-duplicate <loc> entries in the sitemap; repeated URLs waste crawl budget and can look like low-effort automation to reviewers.",
                        doc_url="https://developers.google.com/search/docs/crawling-indexing/sitemaps/overview"
                    ))
                    pillar.earned_score += 1.8
                else:
                    pillar.checks.append(CheckResult(
                        id="sitemap_xml_detected",
                        name="XML Sitemap Detection & Integrity",
                        status=CheckStatus.FAIL,
                        severity=Severity.HIGH,
                        score=0.5,
                        max_score=2.5,
                        details=f"Sitemap at {sitemap_url} has significant duplication: {sitemap_duplicate_count} of {sitemap_total_urls} <loc> entries ({dup_ratio*100:.1f}%) are repeats.",
                        fix_recommendation="Regenerate the sitemap so each canonical URL appears exactly once; heavy duplication suggests a templating or pagination bug.",
                        doc_url="https://developers.google.com/search/docs/crawling-indexing/sitemaps/overview"
                    ))
                    pillar.earned_score += 0.5
        else:
            pillar.checks.append(CheckResult(
                id="sitemap_xml_detected",
                name="XML Sitemap Detection & Integrity",
                status=CheckStatus.FAIL,
                severity=Severity.HIGH,
                score=0.0,
                max_score=2.5,
                details="No XML sitemap found at /sitemap.xml or referenced in robots.txt.",
                fix_recommendation="Generate and submit an XML sitemap (e.g. sitemap.xml) and add 'Sitemap: https://yourdomain.com/sitemap.xml' to robots.txt.",
                doc_url="https://developers.google.com/search/docs/crawling-indexing/sitemaps/overview"
            ))
        pillar.max_score += 2.5

        # 4. Mobile Responsive Viewport
        has_viewport = bool(re.search(r'<meta[^>]+name=["\']viewport["\'][^>]+content=["\'][^"\']*width=device-width', homepage_html, re.IGNORECASE))
        if has_viewport:
            pillar.checks.append(CheckResult(
                id="mobile_responsive_viewport",
                name="Mobile-Responsive Viewport Meta",
                status=CheckStatus.PASS,
                severity=Severity.HIGH,
                score=1.5,
                max_score=1.5,
                details="Responsive viewport meta tag configured correctly.",
                doc_url="https://developers.google.com/search/docs/appearance/mobile-sites"
            ))
            pillar.earned_score += 1.5
        else:
            pillar.checks.append(CheckResult(
                id="mobile_responsive_viewport",
                name="Mobile-Responsive Viewport Meta",
                status=CheckStatus.FAIL,
                severity=Severity.HIGH,
                score=0.0,
                max_score=1.5,
                details="Missing responsive viewport meta tag (<meta name='viewport' content='width=device-width, initial-scale=1.0'>).",
                fix_recommendation="Add mobile viewport meta tag in the <head> of all pages.",
                doc_url="https://developers.google.com/search/docs/appearance/mobile-sites"
            ))
        pillar.max_score += 1.5

        # 5. AdSense Script Implementation: static tag vs. client-side-only injection
        # A server-rendered <script src=".../adsbygoogle.js...">  tag is reliably
        # visible to any crawler/reviewer that reads raw HTML. If the ad script is
        # only ever added via JS (document.createElement('script')) after page load,
        # a raw-HTML fetch will never find it, which is the pattern most likely to
        # cause "no ads detected" / inconsistent review outcomes.
        static_script_pattern = re.search(
            r'<script[^>]+src=["\'][^"\']*pagead2\.googlesyndication\.com/pagead/js/adsbygoogle\.js[^"\']*["\']',
            homepage_html, re.IGNORECASE
        )
        has_adsbygoogle_mention = "adsbygoogle" in homepage_html.lower()
        has_create_element_pattern = bool(re.search(r'createElement\(\s*["\']script["\']\s*\)', homepage_html, re.IGNORECASE))

        if static_script_pattern:
            pillar.checks.append(CheckResult(
                id="adsense_script_implementation",
                name="AdSense Script: Static vs. Dynamic Injection",
                status=CheckStatus.PASS,
                severity=Severity.BLOCKER,
                score=3.5,
                max_score=3.5,
                details="A static <script src='.../adsbygoogle.js'> tag is present in the server-rendered HTML, reliably visible to crawlers and reviewers.",
                doc_url="https://support.google.com/adsense/answer/9183362"
            ))
            pillar.earned_score += 3.5
        elif has_adsbygoogle_mention and has_create_element_pattern:
            pillar.checks.append(CheckResult(
                id="adsense_script_implementation",
                name="AdSense Script: Static vs. Dynamic Injection",
                status=CheckStatus.WARNING,
                severity=Severity.HIGH,
                score=1.3,
                max_score=3.5,
                details="The AdSense script appears to be injected dynamically via JavaScript (document.createElement) rather than as a static <script> tag. A plain HTML fetch finds no ad script at all, which can produce inconsistent detection by AdSense's review crawler.",
                fix_recommendation="Add a static <script async src='https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-XXXX' crossorigin='anonymous'></script> tag directly in server-rendered <head> HTML instead of (or in addition to) injecting it via JS.",
                doc_url="https://support.google.com/adsense/answer/9183362"
            ))
            pillar.earned_score += 1.3
        elif has_adsbygoogle_mention:
            pillar.checks.append(CheckResult(
                id="adsense_script_implementation",
                name="AdSense Script: Static vs. Dynamic Injection",
                status=CheckStatus.WARNING,
                severity=Severity.MEDIUM,
                score=1.8,
                max_score=3.5,
                details="References to 'adsbygoogle' were found in the HTML, but no standard static <script src> tag pattern was matched. Manually verify the ad script loads reliably without requiring client-side JS execution.",
                fix_recommendation="Confirm AdSense script is implemented as a static tag server-side, not only via a JS bundle.",
                doc_url="https://support.google.com/adsense/answer/9183362"
            ))
            pillar.earned_score += 1.8
        else:
            pillar.checks.append(CheckResult(
                id="adsense_script_implementation",
                name="AdSense Script: Static vs. Dynamic Injection",
                status=CheckStatus.FAIL,
                severity=Severity.BLOCKER,
                score=0.0,
                max_score=3.5,
                details="No AdSense script ('adsbygoogle') reference found anywhere in the fetched homepage HTML.",
                fix_recommendation="Add the AdSense auto-ads or manual ad-unit script as a static <script> tag in the page <head>.",
                doc_url="https://support.google.com/adsense/answer/9183362"
            ))
        pillar.max_score += 3.5

        # 6. AdSense Site Verification Meta Tag (evidence-based, not a blanket tip)
        has_adsense_meta = bool(re.search(
            r'<meta[^>]+name=["\']google-adsense-account["\'][^>]+content=["\']ca-pub-\d+["\']',
            homepage_html, re.IGNORECASE
        ))
        if has_adsense_meta:
            pillar.checks.append(CheckResult(
                id="adsense_verification_meta_tag",
                name="AdSense Account Verification Meta Tag",
                status=CheckStatus.PASS,
                severity=Severity.LOW,
                score=0.5,
                max_score=0.5,
                details="<meta name='google-adsense-account' content='ca-pub-...'> detected in <head>.",
                doc_url="https://support.google.com/adsense/answer/9189839"
            ))
            pillar.earned_score += 0.5
        else:
            pillar.checks.append(CheckResult(
                id="adsense_verification_meta_tag",
                name="AdSense Account Verification Meta Tag",
                status=CheckStatus.WARNING,
                severity=Severity.LOW,
                score=0.0,
                max_score=0.5,
                details="No <meta name='google-adsense-account'> verification tag found.",
                fix_recommendation="Add <meta name='google-adsense-account' content='ca-pub-XXXXXXXXXXXXXXXX'> to <head> for ownership verification (optional if already verified via the ads.txt + script method).",
                doc_url="https://support.google.com/adsense/answer/9189839"
            ))
        pillar.max_score += 0.5

        # 7. ads.txt Presence & Format Validation
        if ads_txt:
            pub_id_match = re.search(r'google\.com\s*,\s*(pub-\d+)\s*,\s*(DIRECT|RESELLER)', ads_txt, re.IGNORECASE)
            if pub_id_match:
                pillar.checks.append(CheckResult(
                    id="ads_txt_validation",
                    name="ads.txt Authorized Sellers Record",
                    status=CheckStatus.PASS,
                    severity=Severity.HIGH,
                    score=2.0,
                    max_score=2.0,
                    details=f"Valid ads.txt entry found declaring 'google.com, {pub_id_match.group(1)}, {pub_id_match.group(2).upper()}'.",
                    doc_url="https://support.google.com/adsense/answer/7532444"
                ))
                pillar.earned_score += 2.0
            else:
                pillar.checks.append(CheckResult(
                    id="ads_txt_validation",
                    name="ads.txt Authorized Sellers Record",
                    status=CheckStatus.WARNING,
                    severity=Severity.MEDIUM,
                    score=0.7,
                    max_score=2.0,
                    details="An ads.txt file exists but no well-formed 'google.com, pub-XXXXXXXXXXXXXXXX, DIRECT' line was found.",
                    fix_recommendation="Add the exact line Google provides in your AdSense account under Sites > ads.txt to your ads.txt file.",
                    doc_url="https://support.google.com/adsense/answer/7532444"
                ))
                pillar.earned_score += 0.7
            pillar.max_score += 2.0
        elif not ads_txt_checked:
            # Offline/mock audit: we never made a real network request for ads.txt,
            # so it would be misleading to score this as a FAIL. Report it as skipped
            # and excluded from the denominator entirely.
            pillar.checks.append(CheckResult(
                id="ads_txt_validation",
                name="ads.txt Authorized Sellers Record",
                status=CheckStatus.SKIPPED,
                severity=Severity.HIGH,
                score=0.0,
                max_score=0.0,
                details="ads.txt was not checked (offline/mock audit mode — no live HTTP fetch performed).",
                doc_url="https://support.google.com/adsense/answer/7532444"
            ))
        else:
            pillar.checks.append(CheckResult(
                id="ads_txt_validation",
                name="ads.txt Authorized Sellers Record",
                status=CheckStatus.FAIL,
                severity=Severity.HIGH,
                score=0.0,
                max_score=2.0,
                details="No valid ads.txt file found at the site root.",
                fix_recommendation="Publish /ads.txt at your domain root containing 'google.com, pub-XXXXXXXXXXXXXXXX, DIRECT, f08c47fec0942fa0' (get your exact pub ID from AdSense > Sites).",
                doc_url="https://support.google.com/adsense/answer/7532444"
            ))
            pillar.max_score += 2.0

        # 8. Sitemap Canonical / Redirect Integrity
        # A sitemap must list ONLY final canonical URLs. Checking sitemap health
        # with a redirect-following fetch (like `curl -L`, or this tool's own
        # fetch_url()) makes a stale/legacy URL that 301s elsewhere look like a
        # perfectly healthy 200 — hiding dead/duplicate entries from both this
        # tool and from whoever reads its report. This check uses a REAL
        # first-hop (non-redirect-following) status check on a sample of the
        # sitemap's URLs.
        samples = sitemap_redirect_samples or []
        if not sitemap_found:
            pass  # Already penalized by check #3 above; nothing to add here.
        elif not sitemap_redirect_checked:
            pillar.checks.append(CheckResult(
                id="sitemap_canonical_redirect_integrity",
                name="Sitemap Canonical / Redirect Integrity",
                status=CheckStatus.SKIPPED,
                severity=Severity.MEDIUM,
                score=0.0,
                max_score=0.0,
                details="Not checked (offline/mock audit mode — no live HTTP fetch performed).",
                doc_url="https://developers.google.com/search/docs/crawling-indexing/sitemaps/overview"
            ))
        elif sitemap_redirect_checked_count == 0:
            pillar.checks.append(CheckResult(
                id="sitemap_canonical_redirect_integrity",
                name="Sitemap Canonical / Redirect Integrity",
                status=CheckStatus.SKIPPED,
                severity=Severity.MEDIUM,
                score=0.0,
                max_score=0.0,
                details="Sitemap was found but contained no <loc> entries to sample.",
                doc_url="https://developers.google.com/search/docs/crawling-indexing/sitemaps/overview"
            ))
        elif sitemap_redirect_count == 0:
            pillar.checks.append(CheckResult(
                id="sitemap_canonical_redirect_integrity",
                name="Sitemap Canonical / Redirect Integrity",
                status=CheckStatus.PASS,
                severity=Severity.HIGH,
                score=3.0,
                max_score=3.0,
                details=f"All {sitemap_redirect_checked_count} sampled sitemap URLs returned a direct HTTP 200 on the first hop (0 redirects).",
                doc_url="https://developers.google.com/search/docs/crawling-indexing/sitemaps/overview"
            ))
            pillar.earned_score += 3.0
        else:
            redirect_ratio = sitemap_redirect_count / sitemap_redirect_checked_count
            examples = "; ".join(samples[:3]) if samples else "n/a"
            if sitemap_redirect_to_listed_count > 0:
                # Worst case: the sitemap lists a URL AND (separately) the exact
                # page it redirects to — literal duplicate entries in disguise.
                pillar.checks.append(CheckResult(
                    id="sitemap_canonical_redirect_integrity",
                    name="Sitemap Canonical / Redirect Integrity",
                    status=CheckStatus.FAIL,
                    severity=Severity.HIGH,
                    score=0.3,
                    max_score=3.0,
                    details=f"{sitemap_redirect_count}/{sitemap_redirect_checked_count} sampled sitemap URLs are redirects (not direct 200s); {sitemap_redirect_to_listed_count} of those redirect to a URL that is ALSO separately listed in the sitemap (true duplicate-via-redirect). Examples: {examples}.",
                    fix_recommendation="Remove non-canonical/legacy URLs from the sitemap entirely and list only their final canonical destination once.",
                    doc_url="https://developers.google.com/search/docs/crawling-indexing/sitemaps/overview"
                ))
                pillar.earned_score += 0.3
            elif redirect_ratio <= 0.1:
                pillar.checks.append(CheckResult(
                    id="sitemap_canonical_redirect_integrity",
                    name="Sitemap Canonical / Redirect Integrity",
                    status=CheckStatus.WARNING,
                    severity=Severity.MEDIUM,
                    score=2.0,
                    max_score=3.0,
                    details=f"{sitemap_redirect_count}/{sitemap_redirect_checked_count} sampled sitemap URLs are redirects rather than direct 200s. Examples: {examples}.",
                    fix_recommendation="Replace redirecting sitemap entries with their final canonical URL.",
                    doc_url="https://developers.google.com/search/docs/crawling-indexing/sitemaps/overview"
                ))
                pillar.earned_score += 2.0
            else:
                pillar.checks.append(CheckResult(
                    id="sitemap_canonical_redirect_integrity",
                    name="Sitemap Canonical / Redirect Integrity",
                    status=CheckStatus.FAIL,
                    severity=Severity.HIGH,
                    score=0.5,
                    max_score=3.0,
                    details=f"{sitemap_redirect_count}/{sitemap_redirect_checked_count} sampled sitemap URLs ({redirect_ratio*100:.0f}%) are redirects, not direct 200s. Examples: {examples}.",
                    fix_recommendation="Audit the full sitemap for stale/legacy URLs and remove any entry that is not a direct-200 canonical page.",
                    doc_url="https://developers.google.com/search/docs/crawling-indexing/sitemaps/overview"
                ))
                pillar.earned_score += 0.5
        if sitemap_found and sitemap_redirect_checked and sitemap_redirect_checked_count > 0:
            pillar.max_score += 3.0

        # 9. AdSense-Supported Primary Language
        # Source of truth: https://support.google.com/adsense/answer/9727 — Google
        # Publisher Policies explicitly prohibit placing ad code on pages whose
        # primary content language isn't on this list, regardless of how good the
        # content otherwise is. This checks the page's declared <html lang="...">.
        ADSENSE_SUPPORTED_LANGS = {
            "ar", "bn", "bg", "ca", "zh", "zh-cn", "zh-hans", "zh-tw", "zh-hant",
            "hr", "cs", "da", "nl", "en", "et", "fil", "tl", "fi", "fr", "de", "el",
            "gu", "he", "iw", "hi", "hu", "id", "in", "it", "ja", "kn", "ko", "lv",
            "lt", "ms", "ml", "mr", "no", "nb", "nn", "pl", "pt", "pa", "ro", "ru",
            "sr", "sk", "sl", "es", "sv", "ta", "te", "th", "tr", "uk", "ur", "vi"
        }
        lang_match = re.search(r'<html[^>]+lang=["\']([a-zA-Z-]+)["\']', homepage_html, re.IGNORECASE)
        if lang_match:
            declared_lang = lang_match.group(1).strip().lower()
            primary_subtag = declared_lang.split("-")[0]
            is_supported = declared_lang in ADSENSE_SUPPORTED_LANGS or primary_subtag in ADSENSE_SUPPORTED_LANGS
            if is_supported:
                pillar.checks.append(CheckResult(
                    id="adsense_supported_language",
                    name="AdSense-Supported Primary Language",
                    status=CheckStatus.PASS,
                    severity=Severity.HIGH,
                    score=1.0,
                    max_score=1.0,
                    details=f"Declared page language '{declared_lang}' is on Google's AdSense-supported language list.",
                    doc_url="https://support.google.com/adsense/answer/9727"
                ))
                pillar.earned_score += 1.0
            else:
                pillar.checks.append(CheckResult(
                    id="adsense_supported_language",
                    name="AdSense-Supported Primary Language",
                    status=CheckStatus.FAIL,
                    severity=Severity.HIGH,
                    score=0.0,
                    max_score=1.0,
                    details=f"Declared page language '{declared_lang}' does NOT appear on Google's official AdSense-supported language list.",
                    fix_recommendation="Google Publisher Policies explicitly prohibit ad serving on pages whose primary language isn't supported — verify against the live list at the doc_url before monetizing this URL. (Note: on multi-language sites this only reflects the ONE URL that was audited; check each locale separately.)",
                    doc_url="https://support.google.com/adsense/answer/9727"
                ))
            pillar.max_score += 1.0

        # 10. Mixed Content (insecure HTTP resources loaded on an HTTPS page)
        if base_url.lower().startswith("https://"):
            insecure_refs = re.findall(r'(?:src|href)=["\']http://(?!localhost)[^"\']+["\']', homepage_html, re.IGNORECASE)
            if not insecure_refs:
                pillar.checks.append(CheckResult(
                    id="mixed_content_check",
                    name="Mixed Content (Insecure Resources on HTTPS Page)",
                    status=CheckStatus.PASS,
                    severity=Severity.MEDIUM,
                    score=1.0,
                    max_score=1.0,
                    details="No insecure (http://) resource references found on this HTTPS page.",
                    doc_url="https://developers.google.com/search/docs/crawling-indexing/https"
                ))
                pillar.earned_score += 1.0
            else:
                pillar.checks.append(CheckResult(
                    id="mixed_content_check",
                    name="Mixed Content (Insecure Resources on HTTPS Page)",
                    status=CheckStatus.WARNING,
                    severity=Severity.MEDIUM,
                    score=0.3,
                    max_score=1.0,
                    details=f"Found {len(insecure_refs)} insecure http:// resource reference(s) on an HTTPS page (mixed content), which browsers may block and which can degrade trust/UX signals.",
                    fix_recommendation="Update all asset references (images, scripts, stylesheets) to https:// or protocol-relative URLs.",
                    doc_url="https://developers.google.com/search/docs/crawling-indexing/https"
                ))
                pillar.earned_score += 0.3
            pillar.max_score += 1.0

        # 11. Malware / Hacked-Site Injection Signals
        # Source: blogpros.com and multiple publisher forums report AdSense's
        # review process scans for compromised-site indicators; Google Search
        # Central's malware/hacked-content spam policy
        # (https://developers.google.com/search/docs/essentials/spam-policies)
        # also treats these as spam/safety signals independent of AdSense itself.
        suspicious_patterns = [
            r'eval\(\s*(?:atob|unescape|String\.fromCharCode)\s*\(',
            r'document\.write\(\s*unescape\(',
            r'<iframe[^>]+style=["\'][^"\']*display:\s*none[^"\']*["\']',
            r'<iframe[^>]+width=["\']?0["\']?[^>]*height=["\']?0["\']?',
            r'\\x[0-9a-fA-F]{2}\\x[0-9a-fA-F]{2}\\x[0-9a-fA-F]{2}\\x[0-9a-fA-F]{2}\\x[0-9a-fA-F]{2}\\x[0-9a-fA-F]{2}'
        ]
        found_suspicious = [p for p in suspicious_patterns if re.search(p, homepage_html, re.IGNORECASE)]
        if not found_suspicious:
            pillar.checks.append(CheckResult(
                id="malware_injection_signal_check",
                name="Malware / Hacked-Site Injection Signals",
                status=CheckStatus.PASS,
                severity=Severity.HIGH,
                score=1.0,
                max_score=1.0,
                details="No obfuscated-script, hidden-iframe, or other common hacked-site injection patterns detected on the homepage.",
                doc_url="https://developers.google.com/search/docs/essentials/spam-policies"
            ))
            pillar.earned_score += 1.0
        else:
            pillar.checks.append(CheckResult(
                id="malware_injection_signal_check",
                name="Malware / Hacked-Site Injection Signals",
                status=CheckStatus.FAIL,
                severity=Severity.BLOCKER,
                score=0.0,
                max_score=1.0,
                details=f"Detected {len(found_suspicious)} pattern(s) commonly associated with hacked/compromised sites (obfuscated eval/unescape calls, hidden 0x0 iframes).",
                fix_recommendation="Scan the site for injected malware/spam scripts and clean the compromise before applying for AdSense — hacked-site signals are treated as a safety blocker.",
                doc_url="https://developers.google.com/search/docs/essentials/spam-policies"
            ))
        pillar.max_score += 1.0

        # Ads.txt Authorized Digital Sellers Check
        if ads_txt is not None:
            is_valid_ads_txt = bool(re.search(r"google\.com,\s*pub-\d+,\s*direct,\s*f08c47fec0942fa0", ads_txt, re.IGNORECASE))
            has_pub_id = bool(re.search(r"pub-\d+", ads_txt))

            if is_valid_ads_txt:
                pillar.checks.append(CheckResult(
                    id="ads_txt_authorization",
                    name="Authorized Digital Sellers (ads.txt)",
                    status=CheckStatus.PASS,
                    severity=Severity.MEDIUM,
                    score=2.0,
                    max_score=2.0,
                    details="Valid ads.txt verified with Google publisher ID and mandatory AdSense authorization string.",
                    doc_url="https://support.google.com/adsense/answer/7532444"
                ))
                pillar.earned_score += 2.0
            elif has_pub_id:
                pillar.checks.append(CheckResult(
                    id="ads_txt_authorization",
                    name="Authorized Digital Sellers (ads.txt)",
                    status=CheckStatus.WARNING,
                    severity=Severity.MEDIUM,
                    score=1.0,
                    max_score=2.0,
                    details="Publisher ID found in ads.txt, but missing the standard AdSense authorization record: google.com, pub-XXXXXXXXXXXXXXXX, DIRECT, f08c47fec0942fa0.",
                    fix_recommendation="Ensure your entry exactly matches: google.com, pub-XXXXXXXXXXXXXXXX, DIRECT, f08c47fec0942fa0",
                    doc_url="https://support.google.com/adsense/answer/7532444"
                ))
                pillar.earned_score += 1.0
            else:
                pillar.checks.append(CheckResult(
                    id="ads_txt_authorization",
                    name="Authorized Digital Sellers (ads.txt)",
                    status=CheckStatus.WARNING,
                    severity=Severity.LOW,
                    score=0.5,
                    max_score=2.0,
                    details="ads.txt file present but missing Google AdSense pub-ID specification.",
                    fix_recommendation="Add your Google AdSense pub ID line to ads.txt.",
                    doc_url="https://support.google.com/adsense/answer/7532444"
                ))
                pillar.earned_score += 0.5
            pillar.max_score += 2.0

        # JSON-LD Structured Data Schema Validation
        json_ld_matches = re.findall(r'<script\b[^>]*type=["\']application/ld\+json["\'][^>]*>([\s\S]*?)</script>', homepage_html, re.IGNORECASE)
        if json_ld_matches:
            schema_errors = []
            for idx, raw_json in enumerate(json_ld_matches):
                try:
                    json.loads(raw_json)
                except Exception as e:
                    schema_errors.append(f"Block #{idx+1}: {str(e)}")

            if schema_errors:
                pillar.checks.append(CheckResult(
                    id="json_ld_schema_validity",
                    name="JSON-LD Structured Data Syntax Integrity",
                    status=CheckStatus.FAIL,
                    severity=Severity.HIGH,
                    score=0.0,
                    max_score=2.0,
                    details=f"Malformed JSON-LD syntax detected ({'; '.join(schema_errors)}).",
                    fix_recommendation="Ensure all JSON-LD strings are properly escaped.",
                    doc_url="https://developers.google.com/search/docs/appearance/structured-data/intro-structured-data"
                ))
            else:
                pillar.checks.append(CheckResult(
                    id="json_ld_schema_validity",
                    name="JSON-LD Structured Data Syntax Integrity",
                    status=CheckStatus.PASS,
                    severity=Severity.HIGH,
                    score=2.0,
                    max_score=2.0,
                    details=f"All {len(json_ld_matches)} JSON-LD structured data blocks parsed cleanly with valid schema syntax.",
                    doc_url="https://developers.google.com/search/docs/appearance/structured-data/intro-structured-data"
                ))
                pillar.earned_score += 2.0
            pillar.max_score += 2.0

        return pillar
