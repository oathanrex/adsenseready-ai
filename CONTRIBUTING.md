# Contributing to AdSenseReady-AI

Thank you for your interest in contributing to **AdSenseReady-AI**! We are building the industry standard open-source audit engine and native MCP server to help publishers, indie hackers, and developers achieve 100% Google AdSense approval readiness.

---

## 🎯 How You Can Contribute

1. **New Forensic Checkers**: Add detection heuristics for emerging Google publisher policies (e.g., AI-generated spam patterns, CLS layout shifts, mobile responsiveness).
2. **Policy Updates**: Report or contribute updates to `policies/adsense_rules.json` whenever Google publishes new guidelines in Google Search Central.
3. **AI Agent Integrations**: Enhance agent compatibility prompts or skills for Antigravity, Claude Code, Cursor, Codex, and Gemini.
4. **Bug Reports & Improvements**: File issues for edge cases in HTML parsing, redirects, or CMS detection.

---

## 🛠️ Local Development Setup

1. **Fork and Clone**:
   ```bash
   git clone https://github.com/<your-username>/adsenseready-ai.git
   cd adsenseready-ai
   ```

2. **Set up Environment**:
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On Linux/macOS:
   source venv/bin/activate

   pip install -r requirements.txt
   pip install pytest
   ```

3. **Run the Test Suite**:
   ```bash
   python -m pytest tests/
   ```

4. **Run Sample CLI Audit**:
   ```bash
   python -m src.cli --demo
   ```

---

## 📝 Pull Request Guidelines

- Ensure **all tests pass** before submitting your PR (`python -m pytest tests/`).
- If introducing a new checker module, add it to `src/checkers/` and create corresponding unit tests in `tests/`.
- Use concise, conventional commit messages:
  - `feat(checker): add schema.org publisher verification`
  - `fix(crawler): handle robots.txt redirect loops`
  - `docs: update MCP setup guide for Zed editor`

---

## 💬 Code of Conduct

This project adheres to the [Contributor Covenant](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.
