"""
Audit profiles and configurable thresholds.

The old engine hard-coded "20-30 articles", "800 words", "45-75 readability",
etc. inside the checkers. Those numbers are heuristics, not Google policy, and
they fit an editorial blog far better than a SaaS utility or a docs site.

Profiles bundle sensible threshold sets; individual keys can be overridden from
the CLI, an MCP call, or a JSON config file. A report always records the
profile and effective thresholds so a score can be reproduced.
"""

from copy import deepcopy
from typing import Any, Dict, Optional, Tuple

DEFAULT_PROFILE = "blog"

# Editorial blog / magazine defaults. These deliberately preserve the
# engine's historical scoring behaviour (25 posts PASS, 15 borderline,
# 800-word PASS / 600-word acceptable, etc.).
BLOG_THRESHOLDS: Dict[str, Any] = {
    "min_articles": 25,
    "borderline_articles": 15,
    "recommended_articles": 30,
    "min_avg_words": 800,
    "acceptable_avg_words": 600,
    "recommended_avg_words": 1200,
    "readability_min": 45.0,
    "readability_max": 75.0,
    "primary_source_ratio": 0.5,
    "freshness_ratio": 0.6,
    "template_duplication_ratio": 0.5,
    "approval_score": 85.0,
    "risk_score": 65.0,
}

# Interactive tool / SaaS defaults (formerly the hidden `is_web_app` branch).
SAAS_THRESHOLDS: Dict[str, Any] = {
    **BLOG_THRESHOLDS,
    "min_articles": 4,
    "borderline_articles": 2,
    "recommended_articles": 6,
    "min_avg_words": 400,
    "acceptable_avg_words": 300,
    "recommended_avg_words": 800,
}

# Documentation / knowledge-base defaults: fewer, but still substantial,
# articles; concise technical prose is acceptable.
DOCS_THRESHOLDS: Dict[str, Any] = {
    **BLOG_THRESHOLDS,
    "min_articles": 12,
    "borderline_articles": 6,
    "recommended_articles": 20,
    "min_avg_words": 600,
    "acceptable_avg_words": 400,
    "recommended_avg_words": 1000,
}

PROFILES: Dict[str, Dict[str, Any]] = {
    "blog": {
        "description": "Editorial blog / magazine (legacy defaults; auto-relaxes for detected web apps)",
        "thresholds": BLOG_THRESHOLDS,
        # Preserved for backwards compatibility: a detected interactive app
        # keeps the historical relaxed thresholds unless --profile is given.
        "web_app_thresholds": SAAS_THRESHOLDS,
        "auto_web_app": True,
    },
    "saas": {
        "description": "SaaS / interactive utility website",
        "thresholds": SAAS_THRESHOLDS,
        "auto_web_app": False,
    },
    "docs": {
        "description": "Documentation site / knowledge base",
        "thresholds": DOCS_THRESHOLDS,
        "auto_web_app": False,
    },
}

INT_KEYS = {
    "min_articles", "borderline_articles", "recommended_articles",
    "min_avg_words", "acceptable_avg_words", "recommended_avg_words",
}
RATIO_KEYS = {
    "primary_source_ratio", "freshness_ratio", "template_duplication_ratio",
}
SCORE_KEYS = {"approval_score", "risk_score"}
READABILITY_KEYS = {"readability_min", "readability_max"}
THRESHOLD_KEYS = INT_KEYS | RATIO_KEYS | SCORE_KEYS | READABILITY_KEYS


def _coerce(key: str, value: Any) -> Any:
    """Validate and normalize a threshold value."""
    if isinstance(value, bool):
        raise ValueError(f"'{key}' must be a number, not a boolean")
    try:
        number = int(value) if key in INT_KEYS else float(value)
    except (TypeError, ValueError):
        raise ValueError(f"'{key}' must be {'an integer' if key in INT_KEYS else 'a number'}, got {value!r}") from None

    if key in INT_KEYS and number < 0:
        raise ValueError(f"'{key}' cannot be negative")
    if key in RATIO_KEYS and not 0.0 <= number <= 1.0:
        raise ValueError(f"'{key}' must be between 0 and 1")
    if key in SCORE_KEYS | READABILITY_KEYS and not 0.0 <= number <= 100.0:
        raise ValueError(f"'{key}' must be between 0 and 100")
    return number


def resolve_thresholds(
    profile: Optional[str] = None,
    overrides: Optional[Dict[str, Any]] = None,
    strict: bool = False,
    strict_score: Optional[float] = None,
) -> Dict[str, Any]:
    """Return a self-contained threshold config for the chosen profile.

    `overrides` keys are plain threshold names (applied to both the primary
    and web-app fallback sets), or `web_app_<name>` to override only the
    legacy auto web-app fallback used by the `blog` profile.
    """
    name = (profile or DEFAULT_PROFILE).strip().lower()
    if name not in PROFILES:
        raise ValueError(
            f"Unknown profile '{profile}'. Choose one of: {', '.join(sorted(PROFILES))}"
        )

    spec = PROFILES[name]
    resolved: Dict[str, Any] = {
        "profile": name,
        "auto_web_app": bool(spec.get("auto_web_app", False)),
        **deepcopy(spec["thresholds"]),
        "web_app": deepcopy(spec.get("web_app_thresholds", spec["thresholds"])),
    }

    if strict:
        score = _coerce("approval_score", strict_score if strict_score is not None else 92.0)
        resolved["approval_score"] = score
        resolved["strict"] = True

    explicit_plain = {str(k).strip() for k in (overrides or {}) if not str(k).startswith("web_app_")}
    explicit_app = {
        str(k).strip()[len("web_app_"):]
        for k in (overrides or {}) if str(k).startswith("web_app_")
    }

    for raw_key, raw_value in (overrides or {}).items():
        key = str(raw_key).strip()
        app_only = key.startswith("web_app_")
        base_key = key[len("web_app_"):] if app_only else key
        if base_key not in THRESHOLD_KEYS:
            raise ValueError(
                f"Unknown threshold '{raw_key}'. Available: {', '.join(sorted(THRESHOLD_KEYS))} "
                "(prefix with web_app_ to override the auto web-app fallback only)"
            )
        value = _coerce(base_key, raw_value)
        if app_only:
            resolved["web_app"][base_key] = value
        else:
            resolved[base_key] = value
            # Keep both sets in sync so an explicit override is never silently
            # ignored on a site that happens to be auto-detected as a web app.
            resolved["web_app"][base_key] = value

    # Lowering a target without also lowering its companion value is common
    # (e.g. --threshold min_articles=10), so clamp the companion automatically.
    # Explicitly contradictory values still raise below.
    def clamp_pairs(config: Dict[str, Any], explicit: set) -> None:
        if "min_articles" in explicit and "borderline_articles" not in explicit:
            config["borderline_articles"] = min(config["borderline_articles"], config["min_articles"])
        if "min_avg_words" in explicit and "acceptable_avg_words" not in explicit:
            config["acceptable_avg_words"] = min(config["acceptable_avg_words"], config["min_avg_words"])
        if "approval_score" in explicit and "risk_score" not in explicit:
            config["risk_score"] = min(config["risk_score"], config["approval_score"])

    clamp_pairs(resolved, explicit_plain)
    clamp_pairs(resolved["web_app"], explicit_plain | explicit_app)

    if resolved["acceptable_avg_words"] > resolved["min_avg_words"]:
        raise ValueError("'acceptable_avg_words' cannot exceed 'min_avg_words'")
    if resolved["borderline_articles"] > resolved["min_articles"]:
        raise ValueError("'borderline_articles' cannot exceed 'min_articles'")
    if resolved["readability_min"] > resolved["readability_max"]:
        raise ValueError("'readability_min' cannot exceed 'readability_max'")
    if resolved["risk_score"] > resolved["approval_score"]:
        raise ValueError("'risk_score' cannot exceed 'approval_score'")
    for label, config in (("web_app", resolved["web_app"]),):
        if config["acceptable_avg_words"] > config["min_avg_words"]:
            raise ValueError(f"'{label}.acceptable_avg_words' cannot exceed '{label}.min_avg_words'")
        if config["borderline_articles"] > config["min_articles"]:
            raise ValueError(f"'{label}.borderline_articles' cannot exceed '{label}.min_articles'")
        if config["risk_score"] > config["approval_score"]:
            raise ValueError(f"'{label}.risk_score' cannot exceed '{label}.approval_score'")
    return resolved


def parse_threshold_pairs(pairs) -> Dict[str, str]:
    """Parse repeatable CLI `KEY=VALUE` strings into an overrides dict."""
    overrides: Dict[str, str] = {}
    for pair in pairs or []:
        if "=" not in pair:
            raise ValueError(f"Invalid threshold '{pair}'. Use KEY=VALUE (e.g. min_articles=10)")
        key, value = pair.split("=", 1)
        overrides[key.strip()] = value.strip()
    return overrides


def load_config(path: str) -> Tuple[Optional[str], Dict[str, Any]]:
    """Load {profile, thresholds} from a JSON file.

    Flat top-level threshold keys are also accepted for convenience.
    """
    import json
    from pathlib import Path

    with open(Path(path), "r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        raise ValueError("Config file must contain a JSON object")

    thresholds = data.get("thresholds", data.get("overrides", {}))
    if not isinstance(thresholds, dict):
        raise ValueError("'thresholds' in config file must be a JSON object")
    thresholds = dict(thresholds)
    for key in THRESHOLD_KEYS:
        top_key = f"web_app_{key}" if key not in thresholds and f"web_app_{key}" in data else key
        if top_key in data:
            thresholds.setdefault(top_key, data[top_key])

    profile = data.get("profile")
    if profile is not None and (not isinstance(profile, str) or profile.strip().lower() not in PROFILES):
        raise ValueError(
            f"Unknown profile '{profile}' in config. Choose one of: {', '.join(sorted(PROFILES))}"
        )
    return profile, thresholds
