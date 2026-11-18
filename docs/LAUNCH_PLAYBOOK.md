# 🚀 AdSenseReady-AI Viral Launch & Popularity Playbook

This playbook contains battle-tested, high-engagement copy and distribution strategies across Hacker News, Reddit, Twitter/X, Product Hunt, and developer communities to drive GitHub stars, forks, and adoption.

---

## 📌 Strategy Overview

1. **Target Audience**:
   - Indie Hackers & Solopreneurs launching niche blogs/tools
   - Webmasters struggling with Google AdSense rejections
   - Developers using Claude Desktop, Cursor, or AI agents
   - SEO practitioners & affiliate marketers
2. **Core Pain Point**:
   Google AdSense rejections are notoriously cryptic (*"Low Value Content"*, *"Site Under Construction"*). Standard SEO tools (Ahrefs, Semrush, Lighthouse) don't check Google Publisher Policies or E-E-A-T depth.
3. **The Hook**:
   *An open-source, zero-dependency audit engine and native MCP server that reverse-engineers Google's 7 approval pillars with live RSS policy sync.*

---

## 1. Hacker News (Show HN)

**Title:**
> Show HN: AdSenseReady-AI – Open-source 360° AdSense audit engine and native MCP server

**Post Content:**
```text
Hey HN,

Over the past few years, getting approved for Google AdSense has become notoriously frustrating. Thousands of indie developers and creators get rejected with vague canned emails: "Low-value content" or "Site behavior: Navigation".

Standard SEO audit tools (Lighthouse, Ahrefs) tell you if your site is fast or has backlinks, but zero tools actually audit against Google's official Publisher Policies, E-E-A-T depth, or ad ergonomics.

To solve this, I built AdSenseReady-AI (MIT license):
https://github.com/oathanrex/adsenseready-ai

Key highlights:
- 7-Pillar Forensic Audit: 100-point calibrated scoring (Legal & Trust, Content E-E-A-T, Technical SEO, Navigation, Prohibited Niches, Ad Ergonomics, Organic Signals).
- Native Model Context Protocol (MCP) Server: Plug it into Claude Desktop or Cursor, and ask: "Audit https://mywebsite.com for AdSense readiness".
- Thin Content Fixer & Autonomous Article Generator: Diagnoses thin articles and outputs 1,200+ word E-E-A-T expansion blueprints.
- Zero mandatory external dependencies: The core engine runs on pure Python standard library.
- Automated Policy Sync: Weekly GitHub Action monitors official Google Search Central and AdSense RSS feeds to keep policy rules 100% evergreen.

You can run an audit in 5 seconds via CLI:
$ git clone https://github.com/oathanrex/adsenseready-ai.git
$ cd adsenseready-ai
$ python -m src.cli https://yourwebsite.com

Or launch the interactive HTML report:
$ python -m src.cli https://yourwebsite.com --format html --output report.html

Would love feedback on additional compliance heuristics or edge cases you've encountered with AdSense reviews!
```

---

## 2. Reddit Posts

### Subreddit: `r/AdSense` & `r/Blogging`
**Title:**
> I got tired of vague "Low Value Content" rejections, so I open-sourced an automated 360° AdSense audit tool & MCP server

**Body:**
```text
If you’ve applied for Google AdSense recently, you know the pain: you wait 2–3 weeks only to get hit with:
"Your site isn't ready: Low-value content".

Google never tells you WHICH articles are thin, WHAT policies you violated, or WHAT trust signals are missing.

I spent months reverse-engineering Google's reviewer guidelines and official publisher policies to build AdSenseReady-AI:
👉 https://github.com/oathanrex/adsenseready-ai

What it does:
1. Audits your site against 7 strict pillars (20+ automated forensic checks).
2. Checks for missing mandatory legal pages (Privacy, Terms, About, Contact, Cookie banners).
3. Evaluates E-E-A-T: author credentials, editorial standards, lexical diversity, and word counts.
4. Generates an interactive visual HTML report showing exactly what to fix before reapplying.
5. Works as a native MCP server for Claude Desktop / Cursor.

It's completely free, 100% open-source (MIT), and has zero mandatory dependencies.

Hope this helps you save weeks of guessing and get approved on your first try!
```

### Subreddit: `r/ClaudeAI` & `r/Cursor`
**Title:**
> Built a Native MCP Server for website auditing & Google AdSense compliance (Open-source)

**Body:**
```text
Hey everyone! I built an open-source MCP server that lets Claude Desktop or Cursor audit websites for Google AdSense approval, E-E-A-T content depth, and publisher policy compliance.

Repo: https://github.com/oathanrex/adsenseready-ai

To use with Claude Desktop:
Add to claude_desktop_config.json:
{
  "mcpServers": {
    "adsenseready": {
      "command": "python",
      "args": ["<PATH>/src/mcp_server.py"]
    }
  }
}

Once connected, you can ask Claude:
- "Audit https://myblog.com and generate a remediation checklist"
- "Explain why AdSense rejected my site for Low Value Content"
- "Expand this thin draft into an E-E-A-T compliant article"

Feedback and PRs are welcomed!
```

---

## 3. Twitter / X Launch Thread

**Tweet 1:**
> Getting approved for Google AdSense in 2026 feels like solving a puzzle with blindfolds on.
> 
> "Low-value content"
> "Site behavior: Navigation"
> 
> To eliminate the guesswork, I built and open-sourced **AdSenseReady-AI**: a 360° forensic audit engine & native MCP server 🎯🧵👇
> 
> [Link to repo: https://github.com/oathanrex/adsenseready-ai]

**Tweet 2:**
> 🔍 Why standard SEO tools fail:
> Ahrefs and Lighthouse test speed and backlinks. None of them check Google Publisher Policies, editorial disclosure rules, or human quality rater standards.
> 
> AdSenseReady-AI scores your site across 7 calibrated pillars (100-point index).

**Tweet 3:**
> 🤖 Native Model Context Protocol (MCP) Server:
> Hook it straight into Claude Desktop or Cursor.
> 
> You can literally prompt:
> *"Audit my site and tell me why AdSense will reject it."*
> 
> Claude will crawl the site, evaluate trust signals, and output a prioritized fix list.

**Tweet 4:**
> ⚡ Zero mandatory dependencies:
> Runs on pure Python standard library.
> Includes automated weekly GitHub Action syncing against official Google RSS policy feeds.
> Generates executive interactive HTML dashboards locally.

**Tweet 5:**
> 100% Free & Open-Source (MIT License).
> 
> ⭐ Star the repo on GitHub:
> https://github.com/oathanrex/adsenseready-ai
> 
> Created by @oathanrex. RTs appreciated! 🙌
