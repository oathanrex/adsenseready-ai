"""
Pillar 3: Technical Crawlability, Sitemap Integrity & Ads.txt Verification Checker
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
        ads_txt: Optional[str] = None,
        sitemap_health: Optional[Dict[str, Any]] = None
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
                score=4.0,
                max_score=4.0,
                details="Site is served over secure HTTPS protocol.",
                doc_url="https://developers.google.com/search/docs/crawling-indexing/https"
            ))
            pillar.earned_score += 4.0
        else:
            pillar.checks.append(CheckResult(
                id="ssl_https_enforcement",
                name="HTTPS / SSL Encryption",
                status=CheckStatus.FAIL,
                severity=Severity.BLOCKER,
                score=0.0,
                max_score=4.0,
                details="Site is not enforcing HTTPS. AdSense requires SSL across all monetized domains.",
                fix_recommendation="Install an SSL certificate (e.g. Let's Encrypt or Cloudflare) and enforce HTTPS redirect.",
                doc_url="https://developers.google.com/search/docs/crawling-indexing/https"
            ))
        pillar.max_score += 4.0

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
                    max_score=4.0,
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
                    score=0.5,
                    max_score=4.0,
                    details="Robots.txt disallows all crawlers ('User-agent: * Disallow: /') without an exemption for AdSense.",
                    fix_recommendation="Update robots.txt to allow Googlebot and Mediapartners-Google to crawl public content.",
                    doc_url="https://support.google.com/adsense/answer/10532"
                ))
                pillar.earned_score += 0.5
            else:
                pillar.checks.append(CheckResult(
                    id="robots_txt_accessibility",
                    name="Robots.txt AdSense Crawler Access",
                    status=CheckStatus.PASS,
                    severity=Severity.BLOCKER,
                    score=4.0,
                    max_score=4.0,
                    details="Robots.txt allows Googlebot and Mediapartners-Google.",
                    doc_url="https://support.google.com/adsense/answer/10532"
                ))
                pillar.earned_score += 4.0
        else:
            pillar.checks.append(CheckResult(
                id="robots_txt_accessibility",
                name="Robots.txt AdSense Crawler Access",
                status=CheckStatus.WARNING,
                severity=Severity.MEDIUM,
                score=2.5,
                max_score=4.0,
                details="No robots.txt detected (defaults to allow-all, but explicit robots.txt is recommended).",
                fix_recommendation="Create a clean /robots.txt declaring sitemap and permitting Mediapartners-Google.",
                doc_url="https://support.google.com/adsense/answer/10532"
            ))
            pillar.earned_score += 2.5
        pillar.max_score += 4.0

        # 3. XML Sitemap Detected & Deep Health Check
        if sitemap_found:
            # Check sitemap health if provided
            if sitemap_health:
                dead_404_count = sitemap_health.get("dead_404_count", 0)
                sampled_count = sitemap_health.get("sampled_count", 0)
                redirect_count = sitemap_health.get("redirect_count", 0)
                dead_rate = (dead_404_count / sampled_count) if sampled_count > 0 else 0.0

                if dead_rate > 0.05:  # Over 5% dead links in sitemap is a critical blocker
                    pillar.checks.append(CheckResult(
                        id="sitemap_xml_detected",
                        name="XML Sitemap & Zero-404 Integrity",
                        status=CheckStatus.FAIL,
                        severity=Severity.BLOCKER,
                        score=1.0,
                        max_score=4.0,
                        details=f"CRITICAL BLOCKER: Sitemap contains high dead-end rate ({dead_404_count}/{sampled_count} tested URLs returned 404). Google AdSense automated raters classify high sitemap 404 rates as 'Site Under Construction / Incomplete Navigation'.",
                        fix_recommendation="Prune all non-existent or dead URLs from sitemap.xml immediately so 100% of sitemap URLs return HTTP 200.",
                        doc_url="https://developers.google.com/search/docs/crawling-indexing/sitemaps/overview"
                    ))
                    pillar.earned_score += 1.0
                elif redirect_count > 0:
                    pillar.checks.append(CheckResult(
                        id="sitemap_xml_detected",
                        name="XML Sitemap & Zero-404 Integrity",
                        status=CheckStatus.WARNING,
                        severity=Severity.MEDIUM,
                        score=3.0,
                        max_score=4.0,
                        details=f"Sitemap detected with {redirect_count} non-canonical redirecting URLs. Best practice is to list only direct 200 canonical URLs (e.g. trailing slashes).",
                        fix_recommendation="Remove 301-redirecting duplicate URLs from sitemap.xml and keep only final canonical versions.",
                        doc_url="https://developers.google.com/search/docs/crawling-indexing/sitemaps/overview"
                    ))
                    pillar.earned_score += 3.0
                else:
                    pillar.checks.append(CheckResult(
                        id="sitemap_xml_detected",
                        name="XML Sitemap & Zero-404 Integrity",
                        status=CheckStatus.PASS,
                        severity=Severity.HIGH,
                        score=4.0,
                        max_score=4.0,
                        details=f"Valid XML sitemap detected at {sitemap_url} with 0% dead-link error rate across sampled entries.",
                        doc_url="https://developers.google.com/search/docs/crawling-indexing/sitemaps/overview"
                    ))
                    pillar.earned_score += 4.0
            else:
                pillar.checks.append(CheckResult(
                    id="sitemap_xml_detected",
                    name="XML Sitemap Detection",
                    status=CheckStatus.PASS,
                    severity=Severity.HIGH,
                    score=4.0,
                    max_score=4.0,
                    details=f"Valid XML sitemap detected at {sitemap_url}.",
                    doc_url="https://developers.google.com/search/docs/crawling-indexing/sitemaps/overview"
                ))
                pillar.earned_score += 4.0
        else:
            pillar.checks.append(CheckResult(
                id="sitemap_xml_detected",
                name="XML Sitemap Detection",
                status=CheckStatus.FAIL,
                severity=Severity.HIGH,
                score=0.0,
                max_score=4.0,
                details="No XML sitemap found at /sitemap.xml or referenced in robots.txt.",
                fix_recommendation="Generate and submit an XML sitemap (e.g. sitemap.xml) and add 'Sitemap: https://yourdomain.com/sitemap.xml' to robots.txt.",
                doc_url="https://developers.google.com/search/docs/crawling-indexing/sitemaps/overview"
            ))
        pillar.max_score += 4.0

        # 4. Ads.txt Authorized Digital Sellers Check
        if ads_txt is not None:
            is_valid_ads_txt = bool(re.search(r"google\.com,\s*pub-\d+,\s*direct,\s*f08c47fec0942fa0", ads_txt, re.IGNORECASE))
            has_pub_id = bool(re.search(r"pub-\d+", ads_txt))

            if is_valid_ads_txt:
                pillar.checks.append(CheckResult(
                    id="ads_txt_authorization",
                    name="Authorized Digital Sellers (ads.txt)",
                    status=CheckStatus.PASS,
                    severity=Severity.HIGH,
                    score=3.0,
                    max_score=3.0,
                    details="Valid ads.txt record found with official Google DIRECT authorized seller syntax.",
                    doc_url="https://support.google.com/adsense/answer/7532444"
                ))
                pillar.earned_score += 3.0
            elif has_pub_id:
                pillar.checks.append(CheckResult(
                    id="ads_txt_authorization",
                    name="Authorized Digital Sellers (ads.txt)",
                    status=CheckStatus.WARNING,
                    severity=Severity.MEDIUM,
                    score=1.5,
                    max_score=3.0,
                    details="ads.txt exists with a publisher ID but lacks exact Google standard syntax ('google.com, pub-XXXXXXXXXX, DIRECT, f08c47fec0942fa0').",
                    fix_recommendation="Format your ads.txt line exactly as: google.com, pub-XXXXXXXXXXXXXXXX, DIRECT, f08c47fec0942fa0",
                    doc_url="https://support.google.com/adsense/answer/7532444"
                ))
                pillar.earned_score += 1.5
            else:
                pillar.checks.append(CheckResult(
                    id="ads_txt_authorization",
                    name="Authorized Digital Sellers (ads.txt)",
                    status=CheckStatus.WARNING,
                    severity=Severity.MEDIUM,
                    score=1.0,
                    max_score=3.0,
                    details="ads.txt file found at /ads.txt but does not contain a Google AdSense publisher record.",
                    fix_recommendation="Add 'google.com, pub-YOUR_PUB_ID, DIRECT, f08c47fec0942fa0' to your ads.txt file.",
                    doc_url="https://support.google.com/adsense/answer/7532444"
                ))
                pillar.earned_score += 1.0
        else:
            pillar.checks.append(CheckResult(
                id="ads_txt_authorization",
                name="Authorized Digital Sellers (ads.txt)",
                status=CheckStatus.WARNING,
                severity=Severity.MEDIUM,
                score=1.5,
                max_score=3.0,
                details="No ads.txt file detected at /ads.txt. (Required once your AdSense account is approved to prevent revenue loss).",
                fix_recommendation="Place an ads.txt file at the root of your domain with your AdSense publisher ID.",
                doc_url="https://support.google.com/adsense/answer/7532444"
            ))
            pillar.earned_score += 1.5
        pillar.max_score += 3.0

        # 5. Mobile Responsive Viewport
        has_viewport = bool(re.search(r'<meta[^>]+name=["\']viewport["\'][^>]+content=["\'][^"\']*width=device-width', homepage_html, re.IGNORECASE))
        if has_viewport:
            pillar.checks.append(CheckResult(
                id="mobile_responsive_viewport",
                name="Mobile-Responsive Viewport Meta",
                status=CheckStatus.PASS,
                severity=Severity.HIGH,
                score=3.0,
                max_score=3.0,
                details="Responsive viewport meta tag configured correctly.",
                doc_url="https://developers.google.com/search/docs/appearance/mobile-sites"
            ))
            pillar.earned_score += 3.0
        else:
            pillar.checks.append(CheckResult(
                id="mobile_responsive_viewport",
                name="Mobile-Responsive Viewport Meta",
                status=CheckStatus.FAIL,
                severity=Severity.HIGH,
                score=0.0,
                max_score=3.0,
                details="Missing responsive viewport meta tag (<meta name='viewport' content='width=device-width, initial-scale=1.0'>).",
                fix_recommendation="Add mobile viewport meta tag in the <head> of all pages.",
                doc_url="https://developers.google.com/search/docs/appearance/mobile-sites"
            ))
        pillar.max_score += 3.0

        # 6. JSON-LD Structured Data Schema Validation
        json_ld_matches = re.findall(r'<script type=[\'"]application/ld\+json[\'"]>(.*?)</script>', homepage_html, re.DOTALL)
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
                    details=f"Malformed JSON-LD syntax detected ({'; '.join(schema_errors)}). Often caused by unescaped quotes in titles/descriptions (e.g. 2x2\" instead of 2x2 Inch).",
                    fix_recommendation="Ensure all JSON-LD strings are properly escaped or replace literal double quotes with 'Inch' or HTML entities.",
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
        else:
            pillar.checks.append(CheckResult(
                id="json_ld_schema_validity",
                name="JSON-LD Structured Data Syntax Integrity",
                status=CheckStatus.PASS,
                severity=Severity.MEDIUM,
                score=1.5,
                max_score=2.0,
                details="No JSON-LD schema detected on homepage.",
                doc_url="https://developers.google.com/search/docs/appearance/structured-data/intro-structured-data"
            ))
            pillar.earned_score += 1.5
        pillar.max_score += 2.0

        return pillar
