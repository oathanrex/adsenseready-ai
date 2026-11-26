"""Tests for audit profiles and configurable heuristic thresholds."""

import json

import pytest

from src.auditor import AdSenseAuditor
from src.checkers.content_eeat import ContentEEATChecker
from src.cli import build_profile_config
from src.profiles import (
    PROFILES,
    load_config,
    parse_threshold_pairs,
    resolve_thresholds,
)
from src.reporter import AuditReporter
from src.mcp_server import TOOLS
from tests.mock_sites.sample_data import READY_SITE_HTML


def test_profiles_have_distinct_heuristics():
    assert set(PROFILES) == {"blog", "saas", "docs"}
    blog = resolve_thresholds("blog")
    saas = resolve_thresholds("saas")
    docs = resolve_thresholds("docs")

    assert (blog["min_articles"], blog["min_avg_words"]) == (25, 800)
    assert (saas["min_articles"], saas["min_avg_words"]) == (4, 400)
    assert (docs["min_articles"], docs["min_avg_words"]) == (12, 600)
    # The default blog profile still auto-relaxes for detected web apps.
    assert blog["auto_web_app"] is True
    assert blog["web_app"]["min_articles"] == 4
    assert saas["auto_web_app"] is False


def test_threshold_validation_and_web_app_specific_overrides():
    resolved = resolve_thresholds("blog", {
        "min_articles": 10,
        "approval_score": 90,
        "web_app_min_articles": 3,
    })
    assert resolved["min_articles"] == 10
    assert resolved["web_app"]["min_articles"] == 3  # app-only key wins
    assert resolved["approval_score"] == 90
    assert resolved["web_app"]["approval_score"] == 90  # plain key applies to both

    with pytest.raises(ValueError, match="Unknown profile"):
        resolve_thresholds("unknown")
    with pytest.raises(ValueError, match="Unknown threshold"):
        resolve_thresholds("blog", {"magic_number": 7})
    with pytest.raises(ValueError, match="between 0 and 1"):
        resolve_thresholds("blog", {"freshness_ratio": 5})
    with pytest.raises(ValueError, match="cannot exceed"):
        resolve_thresholds("blog", {"min_avg_words": 100, "acceptable_avg_words": 500})
    with pytest.raises(ValueError, match="KEY=VALUE"):
        parse_threshold_pairs(["min_articles"])


def test_config_and_cli_precedence(tmp_path):
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps({
        "profile": "docs",
        "thresholds": {"min_articles": 11, "approval_score": 88},
    }), encoding="utf-8")

    profile, overrides = load_config(str(config_path))
    assert profile == "docs"
    assert overrides["min_articles"] == 11

    class Args:
        config = str(config_path)
        profile = None
        threshold = ["min_articles=7", "min_avg_words=450"]

    assert build_profile_config(Args()) == (
        "docs", {"min_articles": "7", "approval_score": 88, "min_avg_words": "450"}
    )

    Args.profile = "saas"  # explicit CLI flag beats config profile
    assert build_profile_config(Args())[0] == "saas"


def test_content_checker_uses_profile_thresholds():
    articles = [f"https://example.com/post-{i}" for i in range(10)]
    empty_pages = {}

    blog_check = ContentEEATChecker({}).run(articles, empty_pages)
    assert {c.id: c for c in blog_check.checks}["minimum_article_count"].status.value == "FAIL"

    custom_rules = {"thresholds": resolve_thresholds("blog", {"min_articles": 10, "borderline_articles": 5})}
    custom_check = ContentEEATChecker(custom_rules).run(articles, empty_pages)
    assert {c.id: c for c in custom_check.checks}["minimum_article_count"].status.value == "PASS"

    saas_rules = {"thresholds": resolve_thresholds("saas")}
    saas_check = ContentEEATChecker(saas_rules).run(articles, empty_pages)
    assert {c.id: c for c in saas_check.checks}["minimum_article_count"].status.value == "PASS"

    # 500-word article: acceptable for saas (400 min), failing for blog (600 floor).
    body = " ".join(["substance"] * 500)
    pages = {"https://example.com/post-1": f"<html><body><main><p>{body}</p></main></body></html>"}
    sample = list(pages)
    blog_words = {c.id: c for c in ContentEEATChecker({}).run(sample, pages).checks}
    saas_words = {c.id: c for c in ContentEEATChecker(saas_rules).run(sample, pages).checks}
    assert blog_words["average_word_count"].status.value == "FAIL"
    assert saas_words["average_word_count"].status.value == "PASS"


def test_mcp_audit_tool_exposes_profile_options():
    schema = next(t for t in TOOLS if t["name"] == "audit_website")["inputSchema"]["properties"]
    assert set(schema["profile"]["enum"]) == {"blog", "saas", "docs"}
    assert schema["thresholds"]["type"] == "object"
    assert schema["strict"]["type"] == "boolean"


def test_auditor_carries_profile_and_honors_strict_cutoff():
    auditor = AdSenseAuditor(profile="saas", thresholds={"min_articles": 7})
    assert auditor.thresholds["profile"] == "saas"
    assert auditor.thresholds["web_app"]["min_articles"] == 7

    report = auditor.audit_site("https://demotechjournal.com", mock_html=READY_SITE_HTML)
    assert report.profile == "saas"
    assert json.loads(AuditReporter.to_json(report))["thresholds"]["profile"] == "saas"

    baseline = AdSenseAuditor().audit_site("https://demotechjournal.com", mock_html=READY_SITE_HTML)
    strict = AdSenseAuditor(strict=True).audit_site("https://demotechjournal.com", mock_html=READY_SITE_HTML)
    assert 65 <= baseline.normalized_score < 92
    assert baseline.verdict == "APPROVED_READY"
    assert strict.verdict == "AT_RISK"
    assert strict.thresholds["approval_score"] == 92.0
