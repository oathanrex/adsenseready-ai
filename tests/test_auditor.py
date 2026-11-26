"""
Unit and Integration Tests for AdSenseReady-AI
"""

import pytest
import json
from pathlib import Path
from src.auditor import AdSenseAuditor
from src.reporter import AuditReporter
from tests.mock_sites.sample_data import READY_SITE_HTML, REJECTED_SITE_HTML

BASE_DIR = Path(__file__).resolve().parent.parent


def test_policy_json_validity():
    """Verify that policies/adsense_rules.json is well-formed and contains all 7 pillars."""
    rules_file = BASE_DIR / "policies" / "adsense_rules.json"
    assert rules_file.exists(), "adsense_rules.json must exist"

    with open(rules_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert "pillars" in data
    pillars = data["pillars"]
    assert "legal_trust" in pillars
    assert "content_eeat" in pillars
    assert "technical_seo" in pillars
    assert "site_navigation_ux" in pillars
    assert "google_publisher_policy" in pillars
    assert "ad_layout_readiness" in pillars
    assert "organic_footprint" in pillars


def test_ready_site_approval():
    """Test that a compliant website achieves high score with 0 blockers."""
    auditor = AdSenseAuditor()
    report = auditor.audit_site("https://demotechjournal.com", mock_html=READY_SITE_HTML)

    assert report.total_score > 0
    assert report.normalized_score >= 80.0
    assert len(report.all_blockers) == 0, f"Compliant site should have 0 blockers, found: {[b.name for b in report.all_blockers]}"
    assert report.verdict == "APPROVED_READY"

    # Verify markdown generation
    md = AuditReporter.to_markdown(report)
    assert "# 🎯 Google AdSense Readiness Audit Report" in md
    assert "APPROVED_READY" in md or "READY FOR ADSENSE APPROVAL" in md

    # Verify JSON output
    js = AuditReporter.to_json(report)
    parsed = json.loads(js)
    assert parsed["verdict"] == "APPROVED_READY"


def test_rejected_site_flags_blockers():
    """Test that a non-compliant spam/piracy site triggers multiple critical blockers."""
    auditor = AdSenseAuditor()
    report = auditor.audit_site("https://badspamsite.com", mock_html=REJECTED_SITE_HTML)

    assert len(report.all_blockers) > 0, "Non-compliant site must trigger blockers"
    blocker_ids = [b.id for b in report.all_blockers]

    # Must catch prohibited niche, fake download buttons, noindex, and placeholder text
    assert "banned_niche_detection" in blocker_ids
    assert "deceptive_ui_buttons" in blocker_ids
    assert "search_console_indexing_signals" in blocker_ids
    assert "zero_placeholder_pages" in blocker_ids

    assert report.verdict == "REJECTION_GUARANTEED"


def test_ad_slot_and_certified_cmp_checks():
    """Verify AdLayoutChecker flags missing data-ad-slot and uncertified custom CMP."""
    from src.checkers.ad_layout import AdLayoutChecker

    checker = AdLayoutChecker({})
    html_missing_slot = '''
    <html><head>
    <script>gtag('consent', 'default', {ad_storage: 'denied'});</script>
    <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-123"></script>
    </head><body><main>
    <ins class="adsbygoogle" style="display:block" data-ad-client="ca-pub-123"></ins>
    </main></body></html>
    '''
    res = checker.run(html_missing_slot)
    by_id = {c.id: c for c in res.checks}
    assert by_id["ad_slot_completeness"].status.value == "WARNING"
    assert by_id["certified_cmp_presence"].status.value == "WARNING"

    html_complete = '''
    <html><head>
    <script>gtag('consent', 'default', {ad_storage: 'denied'});</script>
    <script src="https://fundingchoicesmessages.google.com/i/pub-123"></script>
    <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-123"></script>
    </head><body><main>
    <ins class="adsbygoogle" style="display:block" data-ad-client="ca-pub-123" data-ad-slot="9876543210"></ins>
    </main></body></html>
    '''
    res_ok = checker.run(html_complete)
    by_id_ok = {c.id: c for c in res_ok.checks}
    assert by_id_ok["ad_slot_completeness"].status.value == "PASS"
    assert by_id_ok["certified_cmp_presence"].status.value == "PASS"


def test_template_duplication_and_methodology_checks():
    """Verify ContentEEATChecker catches templated pages and LegalTrustChecker checks methodology."""
    from src.checkers.content_eeat import ContentEEATChecker
    from src.checkers.legal_trust import LegalTrustChecker

    eeat = ContentEEATChecker({})
    shared = " ".join([f"word{i}" for i in range(60)])
    dup_pages = {
        "https://example.com/tool-a": f"<html><body><main><p>{shared} alpha</p></main></body></html>",
        "https://example.com/tool-b": f"<html><body><main><p>{shared} beta</p></main></body></html>",
        "https://example.com/tool-c": f"<html><body><main><p>{shared} gamma</p></main></body></html>",
    }
    res_eeat = eeat.run(list(dup_pages.keys()), dup_pages, is_web_app=True)
    by_id = {c.id: c for c in res_eeat.checks}
    assert by_id["template_duplication_risk"].status.value == "WARNING"

    trust = LegalTrustChecker({})
    res_trust = trust.run(
        "https://example.com",
        "<html><body><a href='/about'>About</a></body></html>",
        {"https://example.com/about": "<html><body><h1>About</h1><p>Our testing methodology and editorial policy are verified first-hand.</p></body></html>"}
    )
    trust_by_id = {c.id: c for c in res_trust.checks}
    assert trust_by_id["editorial_methodology_eeat"].status.value == "PASS"


def test_hreflang_noindex_canonical_and_doorway_checks():
    """Verify hreflang<->noindex, X-Robots-Tag, canonical trailing slash, and doorway URL pattern checks."""
    from src.checkers.organic_footprint import OrganicFootprintChecker
    from src.checkers.tech_seo import TechSEOChecker

    org = OrganicFootprintChecker({})
    html_conflict = '''
    <html><head>
      <link rel="canonical" href="https://example.com/" />
      <link rel="alternate" hreflang="x-default" href="https://example.com/" />
      <link rel="alternate" hreflang="es" href="https://example.com/es/" />
    </head><body></body></html>
    '''
    res_org = org.run(
        html_conflict,
        base_url="https://example.com",
        crawled_pages={"https://example.com/es/": "<html><head><meta name='robots' content='noindex, follow'></head></html>"},
        page_headers={"https://example.com/es/": {"X-Robots-Tag": "noindex, follow"}}
    )
    org_by_id = {c.id: c for c in res_org.checks}
    assert org_by_id["canonical_slash_host_consistency"].status.value == "PASS"  # both normalize path '/'
    assert org_by_id["hreflang_integrity"].status.value == "FAIL"
    assert org_by_id["multi_page_noindex_audit"].status.value == "WARNING"

    res_mismatch = org.run(
        "<html><head><link rel='canonical' href='https://example.com/tool/' /></head></html>",
        base_url="https://example.com/tool"
    )
    assert {c.id: c for c in res_mismatch.checks}["canonical_slash_host_consistency"].status.value == "WARNING"

    tech = TechSEOChecker({})
    res_tech = tech.run(
        "https://example.com",
        "<html><head><meta name='viewport' content='width=device-width'></head></html>",
        "User-agent: *\nAllow: /",
        True,
        "https://example.com/sitemap.xml",
        0.1,
        sitemap_urls=[
            "https://example.com/compress-20kb",
            "https://example.com/compress-50kb",
            "https://example.com/compress-100kb",
            "https://example.com/compress-200kb",
        ]
    )
    tech_by_id = {c.id: c for c in res_tech.checks}
    assert tech_by_id["doorway_url_pattern_risk"].status.value == "WARNING"


