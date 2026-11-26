"""Guards package metadata and release automation from drifting."""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def test_pyproject_metadata_is_honest_and_current():
    content = (BASE_DIR / "pyproject.toml").read_text(encoding="utf-8")
    assert 'version = "2026.11.3"' in content
    assert "100%" not in content
    assert 'requires-python = ">=3.10"' in content
    assert 'license = "MIT"' in content
    assert 'license-files = ["LICENSE"]' in content
    assert 'packages = ["src", "src.checkers", "policies", "scripts"]' in content
    assert (BASE_DIR / "LICENSE").exists()
    assert (BASE_DIR / "policies/__init__.py").exists()
    assert (BASE_DIR / "scripts/__init__.py").exists()


def test_publish_workflow_uses_trusted_publishing():
    workflow = (BASE_DIR / ".github/workflows/publish.yml").read_text(encoding="utf-8")
    assert 'tags:\n      - "v*"' in workflow
    assert "pypa/gh-action-pypi-publish@release/v1" in workflow
    assert "id-token: write" in workflow
    assert (BASE_DIR / "docs/RELEASING.md").exists()


def test_version_matches_policy_ruleset():
    import json
    rules = json.loads((BASE_DIR / "policies/adsense_rules.json").read_text(encoding="utf-8"))
    pyproject = (BASE_DIR / "pyproject.toml").read_text(encoding="utf-8")
    assert f'version = "{rules["version"]}"' in pyproject
