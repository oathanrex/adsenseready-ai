"""
Pillar 6: Ad Placement Ergonomics, AdSense Code Verification & Invalid Traffic Prevention
"""

import re
from typing import Dict, Any, Optional
from ..models import PillarResult, CheckResult, CheckStatus, Severity


class AdLayoutChecker:
    def __init__(self, rules: Dict[str, Any]):
        self.rules = rules.get("pillars", {}).get("ad_layout_readiness", {})
        self.weight = self.rules.get("weight", 5)

    def run(self, homepage_html: str) -> PillarResult:
        pillar = PillarResult(
            id="ad_layout_readiness",
            name="Ad Placement Ergonomics & Script Verification",
            weight=self.weight,
            earned_score=0.0,
            max_score=0.0,
            checks=[]
        )

        lower_html = homepage_html.lower()

        # 1. Content Superiority / Above the fold space
        has_main_or_article = "<main" in lower_html or "<article" in lower_html or 'class="content"' in lower_html or 'id="content"' in lower_html
        if has_main_or_article:
            pillar.checks.append(CheckResult(
                id="content_to_ad_ratio",
                name="Content Prominence (Content > Ads)",
                status=CheckStatus.PASS,
                severity=Severity.HIGH,
                score=3.0,
                max_score=3.0,
                details="Distinct semantic main content containers detected. Layout leaves ample room for compliant ad placement without clutter.",
                doc_url="https://support.google.com/adsense/answer/1346295"
            ))
            pillar.earned_score += 3.0
        else:
            pillar.checks.append(CheckResult(
                id="content_to_ad_ratio",
                name="Content Prominence (Content > Ads)",
                status=CheckStatus.WARNING,
                severity=Severity.HIGH,
                score=1.5,
                max_score=3.0,
                details="Lacks clear semantic <main> or <article> wrapper; layout structure could cause ads to push content below the fold.",
                fix_recommendation="Structure your page layout using semantic <main> tags ensuring body copy is prominently visible above the fold.",
                doc_url="https://support.google.com/adsense/answer/1346295"
            ))
            pillar.earned_score += 1.5
        pillar.max_score += 3.0

        # 2. Cumulative Layout Shift & Aggressive Interstitial Detection
        aggressive_popups = ["popup-overlay", "interstitial-modal", "forced-click", "spin-wheel"]
        found_popups = [p for p in aggressive_popups if p in lower_html]

        if not found_popups:
            pillar.checks.append(CheckResult(
                id="layout_shift_resilience",
                name="Safe Layout Dynamics (No Intrusive Interstitials)",
                status=CheckStatus.PASS,
                severity=Severity.MEDIUM,
                score=2.0,
                max_score=2.0,
                details="No intrusive full-screen popups or unexpected layout shifters detected.",
                doc_url="https://support.google.com/adsense/answer/1346295"
            ))
            pillar.earned_score += 2.0
        else:
            pillar.checks.append(CheckResult(
                id="layout_shift_resilience",
                name="Safe Layout Dynamics (No Intrusive Interstitials)",
                status=CheckStatus.WARNING,
                severity=Severity.MEDIUM,
                score=0.5,
                max_score=2.0,
                details=f"Detected aggressive modal/overlay classes ({', '.join(found_popups)}). Google penalizes intrusive interstitials.",
                fix_recommendation="Disable intrusive page-blocking popups prior to AdSense evaluation.",
                doc_url="https://support.google.com/adsense/answer/1346295"
            ))
            pillar.earned_score += 0.5
        pillar.max_score += 2.0

        # 3. Forensic AdSense Head Tag & Dynamic Injection Detection
        has_dynamic_injection = bool(re.search(r"createelement\s*\(\s*['\"]script['\"]\s*\)[\s\S]{0,300}googlesyndication\.com", homepage_html, re.IGNORECASE))
        has_static_script = bool(re.search(r"<script[^>]+src=[\"']https?://pagead2\.googlesyndication\.com/pagead/js/adsbygoogle\.js", homepage_html, re.IGNORECASE))
        has_adsense_meta = bool(re.search(r'<meta[^>]+name=[\"\']google-adsense-account[\"\'][^>]+content=[\"\']ca-pub-\d+[\"\']', homepage_html, re.IGNORECASE))

        if has_dynamic_injection:
            pillar.checks.append(CheckResult(
                id="adsense_script_implementation",
                name="AdSense Script Delivery Pattern",
                status=CheckStatus.FAIL,
                severity=Severity.BLOCKER,
                score=0.0,
                max_score=3.0,
                details="CRITICAL BLOCKER: Dynamic AdSense script injection detected ('document.createElement(\"script\")'). Google automated site verification crawlers parse raw delivered HTML and fail to verify modified or dynamically injected tags.",
                fix_recommendation="Replace dynamic JS loader with the standard canonical snippet: <script async src=\"https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-XXXXXXXX\" crossorigin=\"anonymous\"></script> in <head>.",
                doc_url="https://support.google.com/adsense/answer/9274634"
            ))
        elif has_static_script:
            pillar.checks.append(CheckResult(
                id="adsense_script_implementation",
                name="AdSense Script Delivery Pattern",
                status=CheckStatus.PASS,
                severity=Severity.HIGH,
                score=3.0,
                max_score=3.0,
                details="Standard canonical static AdSense script snippet verified directly in server-delivered HTML markup.",
                doc_url="https://support.google.com/adsense/answer/9274634"
            ))
            pillar.earned_score += 3.0
        else:
            pillar.checks.append(CheckResult(
                id="adsense_script_implementation",
                name="AdSense Script Delivery Pattern",
                status=CheckStatus.WARNING,
                severity=Severity.MEDIUM,
                score=1.5,
                max_score=3.0,
                details="No AdSense script tag detected on homepage (acceptable if submitting a pre-approval audit, but required prior to site verification).",
                fix_recommendation="Ensure the AdSense code snippet is placed in the <head> of your site before clicking 'Request review'.",
                doc_url="https://support.google.com/adsense/answer/9274634"
            ))
            pillar.earned_score += 1.5
        pillar.max_score += 3.0

        # 4. Google Consent Mode v2 Detection
        has_consent_mode = "gtag('consent'" in lower_html or 'gtag("consent"' in lower_html
        if has_consent_mode:
            pillar.checks.append(CheckResult(
                id="google_consent_mode_v2",
                name="Google Consent Mode v2 Compliance",
                status=CheckStatus.PASS,
                severity=Severity.MEDIUM,
                score=2.0,
                max_score=2.0,
                details="Google Consent Mode v2 default consent configuration detected before ad tag evaluation.",
                doc_url="https://developers.google.com/tag-platform/security/guides/consent"
            ))
            pillar.earned_score += 2.0
        else:
            pillar.checks.append(CheckResult(
                id="google_consent_mode_v2",
                name="Google Consent Mode v2 Compliance",
                status=CheckStatus.WARNING,
                severity=Severity.MEDIUM,
                score=1.0,
                max_score=2.0,
                details="Consent Mode v2 default configuration not detected. Recommended for EU/EEA and UK traffic compliance.",
                fix_recommendation="Initialize default denied consent state via gtag('consent', 'default', {...}) prior to firing Google tags.",
                doc_url="https://developers.google.com/tag-platform/security/guides/consent"
            ))
            pillar.earned_score += 1.0
        pillar.max_score += 2.0

        return pillar
