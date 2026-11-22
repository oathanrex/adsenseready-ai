"""
Pillar 5: Google Publisher Policies & Prohibited Niches Checker
"""

import re
from typing import Dict, Any, List
from ..models import PillarResult, CheckResult, CheckStatus, Severity


class PolicyProhibitedChecker:
    def __init__(self, rules: Dict[str, Any]):
        self.rules = rules.get("pillars", {}).get("google_publisher_policy", {})
        self.weight = self.rules.get("weight", 15)

    def run(self, homepage_html: str, crawled_pages: Dict[str, str], target_url: str = "") -> PillarResult:
        pillar = PillarResult(
            id="google_publisher_policy",
            name="Google Publisher Policies & Prohibited Niches",
            weight=self.weight,
            earned_score=0.0,
            max_score=0.0,
            checks=[]
        )

        all_text = (homepage_html + " " + " ".join(crawled_pages.values())).lower()

        # 1. Banned Niches / Illegal Content
        prohibited_terms = [
            "keygen", "warez", "torrent download", "crack download", "mod apk unlimited",
            "casino online", "sports betting odds", "porn", "adult video", "escort service",
            "buy weapons", "counterfeit goods", "hack account", "bypass paywall",
            "free movie streaming full hd", "cracked software", "pirate bay"
        ]

        found_prohibited = [t for t in prohibited_terms if re.search(rf"\b{re.escape(t)}\b", all_text)]

        if not found_prohibited:
            pillar.checks.append(CheckResult(
                id="banned_niche_detection",
                name="Google Prohibited Content Compliance",
                status=CheckStatus.PASS,
                severity=Severity.BLOCKER,
                score=6.0,
                max_score=6.0,
                details="No prohibited niche keywords, pirated links, or policy-violating topics identified.",
                doc_url="https://support.google.com/adsense/answer/10502938"
            ))
            pillar.earned_score += 6.0
        else:
            pillar.checks.append(CheckResult(
                id="banned_niche_detection",
                name="Google Prohibited Content Compliance",
                status=CheckStatus.FAIL,
                severity=Severity.BLOCKER,
                score=0.0,
                max_score=6.0,
                details=f"CRITICAL VIOLATION: Found Google prohibited content signals: {', '.join(found_prohibited)}.",
                fix_recommendation="Completely purge all references, downloads, or discussions of illegal, pirated, adult, or hacking material immediately.",
                doc_url="https://support.google.com/adsense/answer/10502938"
            ))
        pillar.max_score += 6.0

        # 2. Deceptive UI Buttons (Fake download buttons)
        deceptive_patterns = [
            r'<a[^>]+>(?:direct\s+)?download\s+now</a>',
            r'<a[^>]+>play\s+now\s+free</a>',
            r'<button[^>]+>download\s+here</button>',
            r'class=["\'][^"\']*fake-button[^"\']*["\']'
        ]
        found_deceptive = []
        for pattern in deceptive_patterns:
            matches = re.findall(pattern, all_text)
            if matches:
                found_deceptive.extend(matches)

        if not found_deceptive:
            pillar.checks.append(CheckResult(
                id="deceptive_ui_buttons",
                name="Absence of Deceptive 'Download' Triggers",
                status=CheckStatus.PASS,
                severity=Severity.BLOCKER,
                score=5.0,
                max_score=5.0,
                details="No deceptive download triggers or trick-to-click UI designs detected.",
                doc_url="https://support.google.com/adsense/answer/1346295"
            ))
            pillar.earned_score += 5.0
        else:
            pillar.checks.append(CheckResult(
                id="deceptive_ui_buttons",
                name="Absence of Deceptive 'Download' Triggers",
                status=CheckStatus.FAIL,
                severity=Severity.BLOCKER,
                score=1.0,
                max_score=5.0,
                details=f"Identified misleading call-to-action designs that risk being classified as invalid click tricks.",
                fix_recommendation="Ensure all download/play buttons clearly indicate their true action and are separated from future ad placements.",
                doc_url="https://support.google.com/adsense/answer/1346295"
            ))
            pillar.earned_score += 1.0
        pillar.max_score += 5.0

        # 3. Copyright / Piracy Safety
        piracy_flags = ["dmca takedown", "we do not host files on our server", "all links are from third party", "magnet:?xt="]
        found_piracy_disclaimers = [f for f in piracy_flags if f in all_text]

        if not found_piracy_disclaimers:
            pillar.checks.append(CheckResult(
                id="copyright_safe_check",
                name="Copyright & Intellectual Property Safety",
                status=CheckStatus.PASS,
                severity=Severity.BLOCKER,
                score=4.0,
                max_score=4.0,
                details="Clean intellectual property profile. No pirated streaming disclaimers or torrent links detected.",
                doc_url="https://support.google.com/adsense/answer/10502938"
            ))
            pillar.earned_score += 4.0
        else:
            pillar.checks.append(CheckResult(
                id="copyright_safe_check",
                name="Copyright & Intellectual Property Safety",
                status=CheckStatus.FAIL,
                severity=Severity.BLOCKER,
                score=0.0,
                max_score=4.0,
                details="Detected evasive copyright disclaimers (e.g. 'we do not host files'), which Google explicitly flags as pirated content syndication.",
                fix_recommendation="Remove third-party copyrighted embeds or streaming links.",
                doc_url="https://support.google.com/adsense/answer/10502938"
            ))
        pillar.max_score += 4.0

        # 4. Hate Speech, Discrimination & Dangerous Products
        # Source: Google's official "Inappropriate content" policy
        # (support.google.com/adspolicy/answer/6015406) separately prohibits
        # "dangerous or derogatory content" (promotion of discrimination, hatred
        # against protected groups) and "dangerous products or services" (illegal
        # drugs, weapons sales, tobacco sales) as distinct categories from generic
        # piracy/adult content already covered above.
        hate_dangerous_terms = [
            "racial slur", "ethnic cleansing", "hate group", "white supremacy",
            "incites violence against", "promotes discrimination against",
            "buy drugs online", "buy cocaine", "buy heroin", "illegal firearms for sale",
            "untraceable guns", "buy ammunition no license", "order tobacco online",
            "sell endangered species", "human trafficking"
        ]
        found_hate_dangerous = [t for t in hate_dangerous_terms if t in all_text]

        if not found_hate_dangerous:
            pillar.checks.append(CheckResult(
                id="hate_speech_dangerous_products_check",
                name="Hate Speech, Discrimination & Dangerous Products",
                status=CheckStatus.PASS,
                severity=Severity.BLOCKER,
                score=3.0,
                max_score=3.0,
                details="No discriminatory/hate-speech language or dangerous-products (illegal drugs, untraceable weapons, trafficking) signals detected.",
                doc_url="https://support.google.com/adspolicy/answer/6015406"
            ))
            pillar.earned_score += 3.0
        else:
            pillar.checks.append(CheckResult(
                id="hate_speech_dangerous_products_check",
                name="Hate Speech, Discrimination & Dangerous Products",
                status=CheckStatus.FAIL,
                severity=Severity.BLOCKER,
                score=0.0,
                max_score=3.0,
                details=f"CRITICAL VIOLATION: Detected dangerous/derogatory content or dangerous-products signals: {', '.join(found_hate_dangerous)}.",
                fix_recommendation="Remove all discriminatory language and any content facilitating illegal drugs, untraceable weapons, or trafficking immediately — this is a zero-tolerance Google Publisher Policy category.",
                doc_url="https://support.google.com/adspolicy/answer/6015406"
            ))
        pillar.max_score += 3.0

        # 5. Misrepresentation / Clickbait Titles
        # Source: AdSense "Misrepresentative content" policy
        # (support.google.com/adsense/answer/1348688) plus widely-reported blog
        # rejection reason — sensationalist/clickbait headlines are flagged as
        # low-value or deceptive content during manual review.
        title_texts = re.findall(r'<title[^>]*>(.*?)</title>', homepage_html, re.IGNORECASE | re.DOTALL)
        h1_texts = re.findall(r'<h1[^>]*>(.*?)</h1>', homepage_html, re.IGNORECASE | re.DOTALL)
        headline_sample = " ".join(title_texts + h1_texts)
        clean_headline_sample = re.sub(r'<[^>]+>', ' ', headline_sample)

        clickbait_patterns = [
            r"you won'?t believe", r"doctors hate (?:this|him|her)", r"this one (?:weird|simple) trick",
            r"what happened next will", r"number \d+ will (?:shock|surprise) you", r"\bshocking\b.{0,20}\btruth\b"
        ]
        excessive_caps = bool(re.search(r'\b[A-Z]{6,}\b', clean_headline_sample))
        excessive_bang = "!!" in clean_headline_sample
        found_clickbait = [p for p in clickbait_patterns if re.search(p, clean_headline_sample, re.IGNORECASE)]

        if not found_clickbait and not excessive_caps and not excessive_bang:
            pillar.checks.append(CheckResult(
                id="misrepresentation_clickbait_check",
                name="Misrepresentation / Clickbait Headline Patterns",
                status=CheckStatus.PASS,
                severity=Severity.MEDIUM,
                score=2.0,
                max_score=2.0,
                details="Page title/H1 do not exhibit clickbait phrasing, excessive capitalization, or sensationalist patterns.",
                doc_url="https://support.google.com/adsense/answer/1348688"
            ))
            pillar.earned_score += 2.0
        else:
            reasons = found_clickbait + (["excessive ALL-CAPS wording"] if excessive_caps else []) + (["excessive '!!' punctuation"] if excessive_bang else [])
            pillar.checks.append(CheckResult(
                id="misrepresentation_clickbait_check",
                name="Misrepresentation / Clickbait Headline Patterns",
                status=CheckStatus.WARNING,
                severity=Severity.MEDIUM,
                score=0.5,
                max_score=2.0,
                details=f"Headline(s) show sensationalist/clickbait signals: {', '.join(reasons)}.",
                fix_recommendation="Rewrite titles/H1s to accurately represent the content rather than using sensationalist or misleading hooks — commonly cited as an AdSense manual-review rejection trigger.",
                doc_url="https://support.google.com/adsense/answer/1348688"
            ))
            pillar.earned_score += 0.5
        pillar.max_score += 2.0

        # 6. Competing/High-Risk Ad Network Presence
        # Not a documented hard Google policy violation, but widely reported by
        # publisher blogs (e.g. spelloutmarketing.com, blogpros.com) as approval
        # friction, especially for aggressive pop-under/push networks whose
        # behaviors (forced redirects, disruptive pop-ups) overlap with AdSense's
        # own "valuable inventory" and invalid-traffic policies.
        aggressive_networks = {
            "propellerads": "PropellerAds", "adsterra": "Adsterra", "popads.net": "PopAds",
            "exoclick": "ExoClick", "juicyads": "JuicyAds", "popcash": "PopCash",
            "adcash": "Adcash"
        }
        soft_networks = {
            "media.net": "Media.net", "taboola": "Taboola", "outbrain": "Outbrain",
            "infolinks": "Infolinks", "revcontent": "Revcontent", "bidvertiser": "BidVertiser"
        }
        found_aggressive = sorted({label for key, label in aggressive_networks.items() if key in all_text})
        found_soft = sorted({label for key, label in soft_networks.items() if key in all_text})

        if not found_aggressive and not found_soft:
            pillar.checks.append(CheckResult(
                id="competing_ad_network_check",
                name="Competing / High-Risk Ad Network Presence",
                status=CheckStatus.PASS,
                severity=Severity.LOW,
                score=1.0,
                max_score=1.0,
                details="No competing ad-network scripts detected on the homepage.",
                doc_url="https://support.google.com/adsense/answer/1346295"
            ))
            pillar.earned_score += 1.0
        elif found_aggressive:
            pillar.checks.append(CheckResult(
                id="competing_ad_network_check",
                name="Competing / High-Risk Ad Network Presence",
                status=CheckStatus.WARNING,
                severity=Severity.HIGH,
                score=0.2,
                max_score=1.0,
                details=f"Detected aggressive pop-under/push ad network(s) known for disruptive UX: {', '.join(found_aggressive)}. Multiple publisher reports cite these as hurting AdSense approval odds.",
                fix_recommendation="Remove pop-under/push ad networks before applying for (or while running) AdSense — their forced redirects and disruptive ad experience conflict with Google's ad-experience and invalid-traffic policies.",
                doc_url="https://support.google.com/adsense/answer/1346295"
            ))
            pillar.earned_score += 0.2
        else:
            pillar.checks.append(CheckResult(
                id="competing_ad_network_check",
                name="Competing / High-Risk Ad Network Presence",
                status=CheckStatus.WARNING,
                severity=Severity.LOW,
                score=0.6,
                max_score=1.0,
                details=f"Detected other display ad network(s): {', '.join(found_soft)}. Not a policy violation, but several publisher reports note removing competing networks before applying can reduce review friction.",
                fix_recommendation="Consider temporarily removing other ad networks while awaiting AdSense approval, then re-introduce if desired after approval.",
                doc_url="https://support.google.com/adsense/answer/1346295"
            ))
            pillar.earned_score += 0.6
        pillar.max_score += 1.0

        # 7. Own-Domain vs. Free-Subdomain Hosting
        # Source: widely-reported blog rejection cause (e.g. blogpros.com) — sites
        # on shared free subdomains (blogspot.com, wordpress.com, weebly.com, etc.)
        # face much higher AdSense rejection rates than sites on a fully-owned
        # custom domain, and some free-hosting platforms are not eligible at all.
        free_subdomain_hosts = [
            "blogspot.com", "wordpress.com", "weebly.com", "wixsite.com", "webs.com",
            "tripod.com", "angelfire.com", "yolasite.com", "site123.me", "webador.com",
            "jimdofree.com", "ucoz.com", "blogger.com", "000webhostapp.com", "freewebhostmost.com"
        ]
        host_match = re.search(r'^https?://(?:www\.)?([^/]+)', target_url or "", re.IGNORECASE)
        hostname = host_match.group(1).lower() if host_match else ""
        matched_free_host = next((h for h in free_subdomain_hosts if hostname.endswith(h)), None)

        if hostname:
            if not matched_free_host:
                pillar.checks.append(CheckResult(
                    id="own_domain_subdomain_check",
                    name="Own-Domain vs. Free-Subdomain Hosting",
                    status=CheckStatus.PASS,
                    severity=Severity.MEDIUM,
                    score=1.0,
                    max_score=1.0,
                    details=f"Site is hosted on an independently-owned domain ({hostname}), not a shared free-subdomain platform.",
                    doc_url="https://support.google.com/adsense/answer/9724"
                ))
                pillar.earned_score += 1.0
            else:
                pillar.checks.append(CheckResult(
                    id="own_domain_subdomain_check",
                    name="Own-Domain vs. Free-Subdomain Hosting",
                    status=CheckStatus.WARNING,
                    severity=Severity.MEDIUM,
                    score=0.2,
                    max_score=1.0,
                    details=f"Site is hosted on a shared free-subdomain platform ({matched_free_host}). Publisher reports widely note these face materially lower AdSense approval rates.",
                    fix_recommendation="Migrate to a fully self-owned custom domain before applying — this is one of the most commonly cited avoidable AdSense rejection causes.",
                    doc_url="https://support.google.com/adsense/answer/9724"
                ))
                pillar.earned_score += 0.2
            pillar.max_score += 1.0

        return pillar
