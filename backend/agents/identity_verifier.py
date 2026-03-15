from anthropic import Anthropic
from config import config
from backend.utils.logger import logger
from typing import Dict, List
import re
import requests

class IdentityVerifier:
    def __init__(self):
        self.client = Anthropic(api_key=config.ANTHROPIC_API_KEY)
        logger.info("IdentityVerifier initialized")

    def verify(self, input_data: Dict) -> Dict:
        """
        Verify identity based on any combination of:
        - name
        - email
        - url (website/social profile)
        - description (free text about the person/org)
        """
        results = {}
        scores = []

        name        = input_data.get("name", "")
        email       = input_data.get("email", "")
        url         = input_data.get("url", "")
        description = input_data.get("description", "")

        if email:
            r = self._check_email(email)
            results["email"] = r
            scores.append(r["score"])

        if url:
            r = self._check_domain(url)
            results["domain"] = r
            scores.append(r["score"])

        # Always run AI profile analysis
        ai_result = self._ai_profile_analysis(name, email, url, description)
        results["profile"] = ai_result
        scores.append(ai_result["score"])

        # Compute overall trust score
        trust_score = round(sum(scores) / len(scores)) if scores else 0

        if trust_score >= 75:
            badge = "VERIFIED"
            badge_color = "#00b894"
        elif trust_score >= 50:
            badge = "UNCERTAIN"
            badge_color = "#fdcb6e"
        else:
            badge = "SUSPICIOUS"
            badge_color = "#e17055"

        return {
            "trust_score": trust_score,
            "badge": badge,
            "badge_color": badge_color,
            "checks": results,
            "red_flags": ai_result.get("red_flags", []),
            "positive_signals": ai_result.get("positive_signals", []),
            "summary": ai_result.get("summary", ""),
            "recommendations": ai_result.get("recommendations", []),
            "input": input_data
        }

    def _check_email(self, email: str) -> Dict:
        """Basic email legitimacy checks"""
        score = 100
        flags = []
        signals = []

        # Format check
        if not re.match(r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$', email):
            score -= 40
            flags.append("Invalid email format")
        else:
            signals.append("Valid email format")

        domain = email.split("@")[-1].lower() if "@" in email else ""

        # Disposable email domains
        disposable = ["mailinator.com", "guerrillamail.com", "tempmail.com",
                      "throwaway.email", "yopmail.com", "sharklasers.com",
                      "trashmail.com", "fakeinbox.com", "maildrop.cc"]
        if domain in disposable:
            score -= 60
            flags.append("Disposable/temporary email provider")
        elif domain in ["gmail.com", "outlook.com", "yahoo.com", "hotmail.com",
                        "icloud.com", "protonmail.com"]:
            signals.append("Known consumer email provider")
        elif domain:
            signals.append(f"Custom domain: {domain}")
            score = min(score + 5, 100)

        # Check for suspicious patterns
        local = email.split("@")[0] if "@" in email else email
        if re.search(r'\d{6,}', local):
            flags.append("Many consecutive digits in username")
            score -= 10
        if len(local) > 30:
            flags.append("Unusually long email username")
            score -= 5

        return {
            "type": "email",
            "value": email,
            "score": max(0, score),
            "flags": flags,
            "signals": signals,
            "label": "Legitimate" if score >= 70 else "Suspicious"
        }

    def _check_domain(self, url: str) -> Dict:
        """Check domain/website credibility"""
        score = 50
        flags = []
        signals = []

        # Clean URL
        domain = url.replace("https://", "").replace("http://", "").split("/")[0].lower()

        # Known trusted domains
        trusted = ["wikipedia.org", "reuters.com", "bbc.com", "bbc.co.uk",
                   "apnews.com", "theguardian.com", "nytimes.com", "aljazeera.com",
                   "cnn.com", "npr.org", "bloomberg.com", "forbes.com",
                   "linkedin.com", "twitter.com", "x.com", "github.com"]

        if any(t in domain for t in trusted):
            score = 90
            signals.append("Well-known trusted domain")
        else:
            # Try to fetch headers
            try:
                resp = requests.head(f"https://{domain}", timeout=4,
                                     headers={"User-Agent": "Mozilla/5.0"}, allow_redirects=True)
                if resp.status_code == 200:
                    signals.append("Domain is reachable")
                    score += 15
                    if "https" in url:
                        signals.append("Uses HTTPS")
                        score += 10
                    age_hint = resp.headers.get("last-modified", "")
                    if age_hint:
                        signals.append("Has content history")
                        score += 5
                else:
                    flags.append(f"Domain returned status {resp.status_code}")
                    score -= 10
            except Exception:
                flags.append("Domain unreachable or blocked")
                score -= 20

        # Suspicious TLDs
        suspicious_tlds = [".xyz", ".top", ".click", ".info", ".tk", ".ml"]
        if any(domain.endswith(t) for t in suspicious_tlds):
            flags.append("Suspicious top-level domain")
            score -= 20

        return {
            "type": "domain",
            "value": domain,
            "score": max(0, min(100, score)),
            "flags": flags,
            "signals": signals,
            "label": "Trusted" if score >= 70 else ("Uncertain" if score >= 40 else "Suspicious")
        }

    def _ai_profile_analysis(self, name: str, email: str, url: str, description: str) -> Dict:
        """Use Claude to analyze the full profile"""
        import json

        context = []
        if name:        context.append(f"Name: {name}")
        if email:       context.append(f"Email: {email}")
        if url:         context.append(f"URL/Profile: {url}")
        if description: context.append(f"Description: {description}")

        if not context:
            return {
                "score": 50,
                "summary": "No profile data provided",
                "red_flags": [],
                "positive_signals": [],
                "recommendations": ["Provide name, email, or URL for analysis"],
                "persona_type": "Unknown",
                "risk_level": "Unknown"
            }

        prompt = f"""You are an identity verification expert. Analyze this profile and assess its trustworthiness.

PROFILE DATA:
{chr(10).join(context)}

Analyze for:
1. Consistency between provided details
2. Signs of fake/bot/spam identity
3. Professional legitimacy indicators
4. Risk signals (phishing, impersonation, fraud patterns)
5. Overall credibility

Respond ONLY with JSON:
{{
    "score": 0-100,
    "persona_type": "Individual / Organization / Media Outlet / Bot / Unknown",
    "risk_level": "Low / Medium / High / Critical",
    "summary": "2-3 sentence profile assessment",
    "red_flags": ["list of concerns"],
    "positive_signals": ["list of trust indicators"],
    "recommendations": ["actionable advice for the user"],
    "interesting_fact": "One surprising or notable observation about this identity"
}}"""

        try:
            msg = self.client.messages.create(
                model=config.CLAUDE_MODEL,
                max_tokens=600,
                temperature=0,
                messages=[{"role": "user", "content": prompt}]
            )
            response = msg.content[0].text.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.endswith("```"):
                response = response[:-3]
            return json.loads(response.strip())
        except Exception as e:
            logger.error(f"AI profile analysis failed: {e}")
            return {
                "score": 50,
                "summary": "Analysis unavailable",
                "red_flags": [],
                "positive_signals": [],
                "recommendations": [],
                "persona_type": "Unknown",
                "risk_level": "Unknown",
                "interesting_fact": ""
            }
