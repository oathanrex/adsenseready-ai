<div align="center">

# 🎯 AdSenseReady-AI
### Find the exact Google AdSense readiness gaps reviewers look for — before you reapply

[![CI Test Suite](https://github.com/oathanrex/adsenseready-ai/actions/workflows/test.yml/badge.svg)](https://github.com/oathanrex/adsenseready-ai/actions/workflows/test.yml)
[![Python Versions](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-blue.svg)](https://www.python.org/)
[![Model Context Protocol](https://img.shields.io/badge/MCP-Compatible-purple.svg)](https://modelcontextprotocol.io/)
[![Google Policies](https://img.shields.io/badge/Google%20Policy%20Sync-Live%20v2026.11.3-success.svg)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Curated by Oathan Rex](https://img.shields.io/badge/Author-Oathan%20Rex-0d6e52.svg)](https://github.com/oathanrex)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://github.com/oathanrex/adsenseready-ai/blob/main/CONTRIBUTING.md)
[![GitHub Stars](https://img.shields.io/github/stars/oathanrex/adsenseready-ai?style=social)](https://github.com/oathanrex/adsenseready-ai/stargazers)

*Catch common **"Low Value Content"**, **"Site Under Construction"**, and **"Policy Violation"** blockers across 7 weighted pillars.*  
> **Note:** AdSenseReady-AI is a **diagnostic aid**, not an official Google tool or approval guarantee.

[30-Second Quick Start](#-30-second-quick-start) • [Why Not Lighthouse?](#-why-not-just-lighthouse) • [7-Pillar Matrix](#-the-7-pillar-audit-matrix) • [MCP Server](#-model-context-protocol-mcp-integration) • [Proof](#-verified-proof)

---

</div>

## ⚡ 30-Second Quick Start

```bash
git clone https://github.com/oathanrex/adsenseready-ai.git && cd adsenseready-ai
pip install -r requirements.txt
python -m src.cli https://your-site.com --profile blog
python -m src.cli https://your-site.com --format html --output report.html
```

**Sample Output (live audit):**
```text
Score: 98.7/100 · APPROVED_READY · 0 blockers
⚠ certified_cmp_presence: No Google-certified TCF v2.2 CMP detected (EEA/UK/CH)
```

---

## 🔍 Why Not Just Lighthouse?

| Tool | What It Checks | AdSense Policy & E-E-A-T? |
| :--- | :--- | :---: |
| **Lighthouse** | Performance, Core Web Vitals, a11y | ❌ |
| **Ahrefs / Semrush** | Backlinks, keywords, crawl errors | ❌ |
| **AdSenseReady-AI** | Legal/privacy disclosures, `ads.txt`, `data-ad-slot`, TCF CMP, `hreflang`↔`noindex`, doorway patterns, E-E-A-T & profile thresholds (`blog` / `saas` / `docs`) | ✅ |

---

## 👥 Who Is This For?

- **Bloggers & Publishers:** Catch missing policy disclosures, thin pages, and `noindex`/`hreflang` conflicts before reapplying.
- **Agencies:** Batch-audit client sites via JSON output (`--format json`) and HTML reports.
- **AI Agents (Claude / Cursor):** Run `audit_website` directly from your IDE via the built-in MCP server.
- **Developers:** Gate deployments in CI with `--strict`, `--profile saas`, and custom `--threshold` rules.

---

## ✅ Verified Proof

- **Test Suite:** **30/30 tests passing** in CI (`python -m pytest -q`).
- **Live Audits Verified:**
  - `perspectivefix.app` (`--crawl-depth 15`): **98.7 / 100**, `0` blockers, accurately flagged missing `certified_cmp_presence`.
  - `python.org` (`--crawl-depth 5`): **74.8 / 100**, zero crashes, flagged expected generic gaps (no `ads.txt`, no AdSense script).

## 🌟 Overview & Problem Solved

Every year, millions of webmasters, bloggers, and indie hackers receive automated rejection emails from Google AdSense stating:
> *"Your site isn't ready to show ads. We found some policy violations: Low-value content / Site behavior: Navigation."*

Google's review system uses a combination of **automated ML classifiers** and **human quality raters**. Standard SEO audit tools (Ahrefs, Semrush, Lighthouse) only check generic technical scores — **none of them evaluate Google's exact publisher compliance rules**.

**AdSenseReady-AI** bridges this gap:
- Reverse-engineers Google's 7 approval pillars into a weighted 100-point calibrated index.
- Detects **instant blockers** before you waste weeks waiting for rejection emails.
- **Low-Value Content Eliminator:** Diagnoses thin articles (<600 words), detects missing structural elements (FAQs, comparison tables, author bios), and generates a 1,200+ word expansion blueprint.
- Generates a prioritized, step-by-step remediation action plan with exact fixes.
- **Evergreen Policy Sync:** Probes Google's official Search Central RSS feeds and AdSense Help documentation, automatically updating rules via GitHub Actions.

---

## 🏛️ The 7-Pillar Audit Matrix

| Pillar | Weight | Key Google Requirements & Checks |
| :--- | :---: | :--- |
| **1. Legal & Trust Foundation** | 20% | Mandatory Privacy Policy with explicit Google/DoubleClick DART cookie disclosure & opt-out links (`aboutads.info`), Terms of Service, Human About Us page, and working Contact Us form/email. |
| **2. Content Depth & E-E-A-T** | 25% | Min 25-30+ original articles, 700-1200+ avg word count, Flesch Reading Ease analysis, zero generic AI boilerplate (*"In conclusion...", "As an AI language model..."*), H1/H2 hierarchy, named author attribution. |
| **3. Technical SEO & Crawlability** | 15% | SSL/HTTPS enforced everywhere, clean `robots.txt` explicitly allowing `User-agent: Mediapartners-Google`, valid XML sitemap, mobile responsive viewport. |
| **4. Site Navigation & UX** | 15% | Intuitive primary menu, semantic footer, zero dead/placeholder links (`href="#"`), zero 'Under Construction' or demo posts ('Hello World'). |
| **5. Google Publisher Policies** | 15% | Zero prohibited niche content (warez, torrents, cracks, betting, hacking, adult), zero deceptive download triggers or fake CTA buttons. |
| **6. Ad Layout & Ergonomics** | 5% | Content superiority (content visible above fold), CLS layout shift prevention, zero intrusive popups/interstitials blocking reading. |
| **7. Organic Footprint & Signals** | 5% | Canonical tags configured, robots allowing `index, follow`, Schema.org structured data (Article/Organization). |

---

## 🚀 Quick Start & Installation

### 1. Installation
Clone the repository and install optional rich dependencies:
```bash
git clone https://github.com/oathanrex/adsenseready-ai.git
cd adsenseready-ai
pip install -r requirements.txt
```
*(Zero mandatory dependencies: The core audit engine runs on pure Python standard library out of the box!)*

### 2. Run a Live Audit via CLI
```bash
# Terminal colored display
python -m src.cli https://mytechblog.com

# Generate Standalone Interactive HTML Executive Dashboard
python -m src.cli https://mytechblog.com --format html --output adsense_report.html

# Generate Markdown Report
python -m src.cli https://mytechblog.com --format markdown --output report.md

# Generate Structured JSON for CI/CD Pipelines
python -m src.cli https://mytechblog.com --format json --output report.json
```

### 2b. Profiles & Configurable Thresholds

Article-volume, word-count, readability, citation, freshness and verdict cutoffs are
**heuristics, not official Google policy**. Pick a profile that matches the site, or
override individual values. Every report records the profile and effective thresholds.

| Profile | Best for | Article target | Avg words (pass / acceptable) |
|---------|----------|----------------|-------------------------------|
| `blog` (default) | Editorial blogs, magazines | 25+ (15 borderline) | 800 / 600 |
| `saas` | Interactive tools, web apps | 4+ (2 borderline) | 400 / 300 |
| `docs` | Documentation, knowledge bases | 12+ (6 borderline) | 600 / 400 |

The default `blog` profile keeps the historical behavior of auto-relaxing these
thresholds when an interactive web app is detected; `--profile saas` forces the
utility-app thresholds regardless of detection.

```bash
# Force the SaaS profile
python -m src.cli https://my-tool.com --profile saas

# Override individual heuristics (repeatable)
python -m src.cli https://myblog.com --threshold min_articles=10 --threshold min_avg_words=500

# Load a saved config (see policies/thresholds.example.json)
python -m src.cli https://docs.example.com --config policies/thresholds.example.json

# Require the strict approval cutoff from adsense_rules.json (default 92)
python -m src.cli https://myblog.com --strict
```

Available keys: `min_articles`, `borderline_articles`, `recommended_articles`,
`min_avg_words`, `acceptable_avg_words`, `recommended_avg_words`,
`readability_min`, `readability_max`, `primary_source_ratio`, `freshness_ratio`,
`template_duplication_ratio`, `approval_score`, `risk_score`. Prefix any key with
`web_app_` to change only the legacy auto-detected web-app fallback.

MCP clients can pass `profile`, `thresholds` and `strict` to `audit_website`; the
web studio has a profile selector.

### 3. Eliminate Low-Value Content & Expand Articles
```bash
# Diagnose thin content and generate a 1200+ word expansion blueprint
python -m src.cli --fix-content "https://mytechblog.com/my-short-article" --topic "Article Topic" --author "Editorial Team"
```

### 4. Launch Local Web Studio
```bash
python -m src.cli --serve 8080
# Open http://localhost:8080 in your browser for instant GUI auditing
```

### 4. Run Built-In Benchmark Demo
```bash
python -m src.cli --demo
```

---

## 🔌 Model Context Protocol (MCP) Integration

AdSenseReady-AI includes a production-grade **MCP Server** (`src/mcp_server.py`) conforming to the official Model Context Protocol JSON-RPC standard.

### Connect with Claude Desktop / Cursor
Add the following snippet to your MCP settings file:
- **Claude Desktop:** `%APPDATA%\Claude\claude_desktop_config.json` (Windows) or `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS)
- **Cursor Settings:** `Cursor Settings -> Features -> MCP -> Add New MCP Server`

```json
{
  "mcpServers": {
    "adsenseready": {
      "command": "python",
      "args": ["<PATH_TO_REPO>/src/mcp_server.py"]
    }
  }
}
```

Now you can instruct your AI assistant in plain English:
> *"Audit https://myblog.com for Google AdSense readiness."*  
> *"Explain why AdSense rejected my application for 'Low Value Content' and tell me how to fix it."*

---

## 🤖 Universal Cross-AI Compatibility

| AI Assistant | Integration Method | Configuration File |
| :--- | :--- | :--- |
| **Antigravity / Gemini CLI** | Built-in Agent Skill | [`SKILL.md`](./SKILL.md) |
| **Claude Code** | Native CLI instructions | [`CLAUDE.md`](./CLAUDE.md) |
| **Cursor IDE** | Project & Directory Rules | [`.cursorrules`](./.cursorrules) & [`.cursor/rules/`](./.cursor/rules/adsense-readiness.mdc) |
| **ChatGPT / Custom GPT** | 1-Click Instructions | [`prompts/chatgpt_custom_gpt.md`](./prompts/chatgpt_custom_gpt.md) |
| **Terminal / Bash / Python** | Standalone Executable | `python -m src.cli` |

---

## 🔄 Dynamic Self-Updating Policy Engine

Google continuously modifies Search Essentials, spam algorithms, and consent management guidelines. AdSenseReady-AI keeps your rules evergreen:

```bash
python scripts/sync_policies.py
```

- **Live RSS Monitoring:** Probes Google Search Central and Google Ads official RSS feeds, extracting latest announcements.
- **Policy Versioning:** Updates `policies/adsense_rules.json` and records changelogs in `policies/changelog.json`.
- **Automated GitHub Action:** [`.github/workflows/policy-sync.yml`](./.github/workflows/policy-sync.yml) runs weekly on cron (`0 0 * * 0`) and automatically creates a Pull Request when Google updates policy documentation.

---

## 🧪 Testing & Verification

Run the full automated test suite (30/30 tests passing):
```bash
python -m pytest tests/
```

---

## 🤝 Contributing

Contributions, feedback, and new policy heuristics are welcomed!
Please read our [Contributing Guidelines](CONTRIBUTING.md) to get started.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingChecker`)
3. Commit your Changes (`git commit -m 'feat: add new trust signal check'`)
4. Push to the Branch (`git push origin feature/AmazingChecker`)
5. Open a Pull Request

---

## 📄 License & Credits

Created and curated by **[Oathan Rex](https://github.com/oathanrex)** under the **MIT License**.  
Explore more production tools and AI engineering playbooks in **[The Developer Vault](https://github.com/oathanrex/developer-vault)**.
