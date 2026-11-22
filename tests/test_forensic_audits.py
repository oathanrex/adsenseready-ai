"""
Forensic Audit Checks Test Suite:
Tests dynamic AdSense injection cloaking detection, deep sitemap 404 dead-end rates,
non-canonical 301 redirects, authorized digital sellers (ads.txt), and header editorial prominence.
"""

import pytest
from src.checkers.ad_layout import AdLayoutChecker
from src.checkers.tech_seo import TechSEOChecker
from src.checkers.site_structure import SiteStructureChecker
from src.models import CheckStatus, Severity


def test_ad_layout_catches_dynamic_injection():
    checker = AdLayoutChecker({})

    # 1. Bad HTML with document.createElement('script') targeting googlesyndication
    bad_html = """
    <html>
    <head><title>Cloaked Ad Site</title></head>
    <body>
        <script>
            var s = document.createElement('script');
            s.src = 'https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-123456';
            document.head.appendChild(s);
        </script>
    </body>
    </html>
    """
    res = checker.run(bad_html)
    check_ids = {c.id: c for c in res.checks}

    assert "adsense_script_implementation" in check_ids
    assert check_ids["adsense_script_implementation"].status == CheckStatus.FAIL
    assert check_ids["adsense_script_implementation"].severity == Severity.BLOCKER
    assert "Dynamic AdSense script injection detected" in check_ids["adsense_script_implementation"].details

    # 2. Clean HTML with static canonical script tag and meta tag
    good_html = """
    <html>
    <head>
        <title>Clean AdSense Site</title>
        <meta name="google-adsense-account" content="ca-pub-1234567890123456">
        <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-1234567890123456" crossorigin="anonymous"></script>
    </head>
    <body>
        <main>
            <h1>Approved AdSense Publisher</h1>
        </main>
    </body>
    </html>
    """
    good_res = checker.run(good_html)
    good_checks = {c.id: c for c in good_res.checks}
    assert good_checks["adsense_script_implementation"].status == CheckStatus.PASS


def test_tech_seo_catches_sitemap_404s_and_redirects():
    checker = TechSEOChecker({})

    # 1. Sitemap with high dead-end rate (> 5%)
    bad_sitemap_health = {
        "sampled_count": 10,
        "dead_404_count": 3,
        "redirect_count": 0
    }
    bad_res = checker.run(
        "https://example.com",
        "<html></html>",
        "User-agent: *\nAllow: /",
        True,
        "https://example.com/sitemap.xml",
        0.5,
        sitemap_health=bad_sitemap_health
    )
    sitemap_check = next(c for c in bad_res.checks if c.id == "sitemap_xml_detected")
    assert sitemap_check.status == CheckStatus.FAIL
    assert sitemap_check.severity == Severity.BLOCKER

    # 2. Sitemap with redirecting URLs
    redirect_health = {
        "sampled_count": 10,
        "dead_404_count": 0,
        "redirect_count": 2
    }
    warn_res = checker.run(
        "https://example.com",
        "<html></html>",
        "User-agent: *\nAllow: /",
        True,
        "https://example.com/sitemap.xml",
        0.5,
        sitemap_health=redirect_health
    )
    sitemap_warn = next(c for c in warn_res.checks if c.id == "sitemap_xml_detected")
    assert sitemap_warn.status == CheckStatus.WARNING

    # 3. Clean sitemap (0 dead, 0 redirects)
    clean_health = {
        "sampled_count": 10,
        "dead_404_count": 0,
        "redirect_count": 0
    }
    clean_res = checker.run(
        "https://example.com",
        "<html></html>",
        "User-agent: *\nAllow: /",
        True,
        "https://example.com/sitemap.xml",
        0.5,
        sitemap_health=clean_health
    )
    sitemap_pass = next(c for c in clean_res.checks if c.id == "sitemap_xml_detected")
    assert sitemap_pass.status == CheckStatus.PASS


def test_tech_seo_ads_txt_validation():
    checker = TechSEOChecker({})

    # 1. Valid ads.txt
    valid_ads = "google.com, pub-7283514433804502, DIRECT, f08c47fec0942fa0\n"
    res = checker.run(
        "https://example.com",
        "<html></html>",
        "User-agent: *\nAllow: /",
        True,
        "https://example.com/sitemap.xml",
        0.3,
        ads_txt=valid_ads
    )
    ads_check = next(c for c in res.checks if c.id == "ads_txt_authorization")
    assert ads_check.status == CheckStatus.PASS

    # 2. Malformed ads.txt
    malformed_ads = "google.com, pub-123456, RESELLER"
    res_malformed = checker.run(
        "https://example.com",
        "<html></html>",
        "User-agent: *\nAllow: /",
        True,
        "https://example.com/sitemap.xml",
        0.3,
        ads_txt=malformed_ads
    )
    ads_check_m = next(c for c in res_malformed.checks if c.id == "ads_txt_authorization")
    assert ads_check_m.status == CheckStatus.WARNING


def test_site_structure_editorial_prominence():
    checker = SiteStructureChecker({})

    # Buried blog in footer only
    buried_html = """
    <html>
    <header>
        <nav><a href="/">Home</a><a href="/tools">Tools</a></nav>
    </header>
    <main><p>Tool content</p></main>
    <footer>
        <a href="/blog">Our Articles</a>
        <a href="/privacy">Privacy</a>
    </footer>
    </html>
    """
    res = checker.run(buried_html, {"homepage": buried_html}, ["https://example.com/blog"])
    check_ids = {c.id: c for c in res.checks}
    assert "editorial_header_prominence" in check_ids
    assert check_ids["editorial_header_prominence"].status == CheckStatus.WARNING

    # Prominent blog in header nav
    prominent_html = """
    <html>
    <header>
        <nav>
            <a href="/">Home</a>
            <a href="/blog">Guides & Research</a>
            <a href="/about">About</a>
        </nav>
    </header>
    <main><p>Tool content</p></main>
    <footer><a href="/privacy">Privacy</a></footer>
    </html>
    """
    res_prominent = checker.run(prominent_html, {"homepage": prominent_html}, ["https://example.com/blog"])
    p_check = next(c for c in res_prominent.checks if c.id == "editorial_header_prominence")
    assert p_check.status == CheckStatus.PASS


def test_tech_seo_json_ld_schema_validation():
    checker = TechSEOChecker({})

    # 1. Broken JSON-LD with unescaped literal quote in title
    broken_html = """
    <html>
    <head>
        <script type="application/ld+json">
        {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": "Passport Photo Size: 2x2", 35x45mm Guide"
        }
        </script>
    </head>
    <body><h1>Test</h1></body>
    </html>
    """
    res_broken = checker.run("https://example.com", broken_html, "User-agent: *\nAllow: /", True, "https://example.com/sitemap.xml", 0.2)
    schema_check = next(c for c in res_broken.checks if c.id == "json_ld_schema_validity")
    assert schema_check.status == CheckStatus.FAIL
    assert schema_check.severity == Severity.HIGH
    assert "Malformed JSON-LD syntax detected" in schema_check.details

    # 2. Clean valid JSON-LD
    clean_html = """
    <html>
    <head>
        <script type="application/ld+json">
        {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": "Passport Photo Size: 2x2 Inch, 35x45mm Guide"
        }
        </script>
    </head>
    <body><h1>Test</h1></body>
    </html>
    """
    res_clean = checker.run("https://example.com", clean_html, "User-agent: *\nAllow: /", True, "https://example.com/sitemap.xml", 0.2)
    schema_check_c = next(c for c in res_clean.checks if c.id == "json_ld_schema_validity")
    assert schema_check_c.status == CheckStatus.PASS
