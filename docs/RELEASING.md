# Releasing AdSenseReady-AI

Releases are tag-driven. The workflow in `.github/workflows/publish.yml` creates a
GitHub Release, builds the sdist/wheel, and publishes to PyPI via OIDC Trusted
Publishing — no API token needs to be stored in the repository.

## One-time PyPI setup

1. Create the package account and verify your email on <https://pypi.org>.
2. In PyPI: **Account settings → Publishing → Add a new trusted publisher** with:
   - Owner: `oathanrex`
   - Repository: `adsenseready-ai`
   - Workflow: `publish.yml`
   - Environment: `pypi`
   - Package name: `adsenseready-ai`
3. In GitHub: **Settings → Environments → `pypi`** (create it if missing).
   For extra safety, add required reviewers so a publish needs your approval.

## Cut a release

```bash
# 0. Make sure main is green and version in pyproject.toml matches the policy release
python -m pytest -q

# 1. Tag the current main commit (version follows policies/adsense_rules.json)
git tag -a v2026.11.3 -m "AdSenseReady-AI v2026.11.3"
git push origin v2026.11.3
```

Pushing the tag triggers the workflow:

1. `softprops/action-gh-release` creates a GitHub Release with auto-generated notes.
2. `python -m build` produces `dist/*.whl` and `dist/*.tar.gz`.
3. `pypa/gh-action-pypi-publish` uploads both artifacts to PyPI.

After it finishes:

```bash
pip install adsenseready-ai
adsense-audit https://example.com --profile blog
adsenseready-mcp   # MCP stdio server entry point
```

## Versioning

- The **package version** lives in `pyproject.toml` (currently `2026.11.3`).
- The **policy ruleset version** lives in `policies/adsense_rules.json`.
- Keep them in sync when a release is mostly a policy refresh.
- Tag format is `v<package version>`.

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| Publish step says "The token has no permission" | Trusted publisher not configured, or workflow/environment name mismatch. Re-check the PyPI publisher settings above. |
| Build fails on a new Python | Update `requires-python` and the CI matrix together. |
| Release not created | Tag must start with `v` and be pushed to GitHub (`git push origin v...`). |
