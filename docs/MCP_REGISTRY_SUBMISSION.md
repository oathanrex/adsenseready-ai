# MCP Registry & Directory Submission Guide

This document contains pre-formatted submission snippets to register **AdSenseReady-AI** with official MCP catalogs and community lists (such as `modelcontextprotocol/servers`, `awesome-mcp-servers`, and PulseMCP).

---

## 1. Submission for `awesome-mcp-servers` / Directory Lists

### Entry Snippet (Markdown Table format)
```markdown
- [AdSenseReady-AI](https://github.com/oathanrex/adsenseready-ai) - Universal MCP server & 360° automated forensic audit engine for Google AdSense compliance, E-E-A-T evaluation, and publisher policy validation.
```

### Categorization
- **Primary Category**: Tools / Web Auditing / SEO
- **Secondary Category**: Publisher Utilities & Compliance

---

## 2. Pull Request Template for MCP Repositories

**PR Title**: `Add AdSenseReady-AI MCP Server`

**PR Body**:
```markdown
### Server Details
- **Name**: AdSenseReady-AI
- **Repository**: https://github.com/oathanrex/adsenseready-ai
- **Description**: 360-degree forensic Google AdSense readiness audit engine and native MCP server for evaluating websites against Google Publisher Policies, E-E-A-T content standards, technical SEO, and ad ergonomics.
- **Author**: [@oathanrex](https://github.com/oathanrex)
- **Runtime**: Python 3.10+ (Zero mandatory external dependencies)
- **License**: MIT

### Exposed Tools
- `audit_website`: Runs the 7-pillar 100-point Google AdSense readiness evaluation on any live URL.
- `explain_rejection`: Pinpoints root causes for common rejection reasons (*"Low Value Content"*, *"Site Under Construction"*, *"Navigation Violations"*) and provides prioritized fixes.
- `expand_thin_content`: Generates an authoritative 1,200+ word E-E-A-T expansion blueprint for thin articles.
- `generate_sample_article`: Autonomously drafts a complete 1,400+ word publication-ready article compliant with Google standards.
- `sync_google_policies`: Pulls latest Google Search Central & AdSense policy updates dynamically.
```

---

## 3. Claude Desktop Configuration Snippet

```json
{
  "mcpServers": {
    "adsenseready": {
      "command": "python",
      "args": ["<PATH_TO_CLONE>/src/mcp_server.py"]
    }
  }
}
```
