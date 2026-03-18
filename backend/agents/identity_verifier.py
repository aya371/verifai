from anthropic import Anthropic
from config import config
from backend.utils.logger import logger
from typing import Dict, List
from ddgs import DDGS
import re
import requests
import base64
import json


PLATFORMS = [
    {"name": "Twitter/X",   "icon": "X",  "color": "#1DA1F2", "site": "twitter.com OR site:x.com"},
    {"name": "Facebook",    "icon": "F",  "color": "#1877F2", "site": "facebook.com"},
    {"name": "Instagram",   "icon": "IG", "color": "#E1306C", "site": "instagram.com"},
    {"name": "LinkedIn",    "icon": "in", "color": "#0A66C2", "site": "linkedin.com"},
    {"name": "TikTok",      "icon": "TT", "color": "#FF0050", "site": "tiktok.com"},
    {"name": "YouTube",     "icon": "YT", "color": "#FF0000", "site": "youtube.com"},
    {"name": "GitHub",      "icon": "GH", "color": "#6e40c9", "site": "github.com"},
    {"name": "Bayt",        "icon": "B",  "color": "#FF6B00", "site": "bayt.com"},
    {"name": "Wikipedia",   "icon": "W",  "color": "#888888", "site": "wikipedia.org"},
    {"name": "News",        "icon": "N",  "color": "#00b894", "site": "news"},
]


class IdentityVerifier:
    def __init__(self):
        self.client = Anthropic(api_key=config.ANTHROPIC_API_KEY)
        logger.info("IdentityVerifier initialized")

    def search_across_platforms(self, name: str) -> List[Dict]:
        """
        Step 1: Ask Claude what it knows about this person + their official profiles
        Step 2: Search DuckDuckGo for each platform with exact name in quotes
        Step 3: Ask Claude to validate each result â€” is this actually the right person?
        """
        logger.info(f"Searching across platforms for: {name}")

        # â”€â”€ Step 1: Claude pre-identifies the person â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        known_profiles = self._claude_identify_person(name)
        logger.info(f"Claude identified: {known_profiles.get('identified', False)}")

        # â”€â”€ Step 2: Search each platform â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        raw_results = []
        for platform in PLATFORMS:
            try:
                if platform["site"] == "news":
                    query = f'"{name}" biography profile news'
                else:
                    query = f'"{name}" site:{platform["site"]}'

                with DDGS() as ddgs:
                    results = list(ddgs.text(query, max_results=3))

                for result in results:
                    url   = result.get("href", "")
                    title = result.get("title", "")
                    body  = result.get("body", "")
                    if not url or len(body) < 20:
                        continue
                    raw_results.append({
                        "platform": platform["name"],
                        "icon":     platform["icon"],
                        "color":    platform["color"],
                        "url":      url,
                        "title":    title,
                        "snippet":  body[:300],
                    })
                    break
            except Exception as e:
                logger.warning(f"Search failed for {platform['name']}: {e}")

        if not raw_results:
            return []

        # â”€â”€ Step 3: Claude validates each result â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        validated = self._claude_validate_results(name, raw_results, known_profiles)
        logger.info(f"Validated {len(validated)} profiles out of {len(raw_results)}")
        return validated

    def _claude_identify_person(self, name: str) -> Dict:
        """Ask Claude what it knows about this person"""
        try:
            msg = self.client.messages.create(
                model=config.CLAUDE_MODEL,
                max_tokens=400,
                temperature=0,
                messages=[{"role": "user", "content": f"""What do you know about a person named "{name}"?

If this is a known public figure, provide their official profile URLs.
If unknown, say so.

Respond ONLY with JSON:
{{
    "identified": true/false,
    "full_name": "exact name if known",
    "description": "brief description or empty",
    "known_urls": ["list of verified official profile URLs if any"],
    "known_platforms": ["platforms they are known to be on"],
    "nationality": "country if known"
}}"""}]
            )
            response = msg.content[0].text.strip()
            if response.startswith("```json"): response = response[7:]
            if response.endswith("```"):       response = response[:-3]
            return json.loads(response.strip())
        except Exception as e:
            logger.warning(f"Claude pre-identification failed: {e}")
            return {"identified": False, "full_name": name, "description": "",
                    "known_urls": [], "known_platforms": [], "nationality": ""}

    def _claude_validate_results(self, name: str, results: List[Dict], known_info: Dict) -> List[Dict]:
        """Ask Claude to validate which results are actually for the right person"""
        if not results:
            return []

        results_text = ""
        for i, r in enumerate(results):
            results_text += f"\n[{i}] Platform: {r['platform']}\nTitle: {r['title']}\nURL: {r['url']}\nSnippet: {r['snippet'][:150]}\n"

        try:
            msg = self.client.messages.create(
                model=config.CLAUDE_MODEL,
                max_tokens=400,
                temperature=0,
                messages=[{"role": "user", "content": f"""I searched for "{name}" across social media platforms and got these results.

WHAT WE KNOW ABOUT THIS PERSON:
{json.dumps(known_info, indent=2)}

SEARCH RESULTS:
{results_text}

For each result, determine if it is ACTUALLY about "{name}" or a different person.
Be strict â€” only approve results where the title/snippet clearly refers to "{name}".

Respond ONLY with a JSON array of indices that are valid (e.g. [0, 2, 4]):"""}]
            )
            response = msg.content[0].text.strip()
            if response.startswith("```json"): response = response[7:]
            if response.endswith("```"):       response = response[:-3]
            valid_indices = json.loads(response.strip())
            return [results[i] for i in valid_indices if i < len(results)]
        except Exception as e:
            logger.warning(f"Claude validation failed: {e}")
            # Fallback: basic name filter
            name_lower = name.lower()
            name_parts = [p for p in name_lower.split() if len(p) > 2]
            validated = []
            for r in results:
                combined = (r["title"] + " " + r["snippet"] + " " + r["url"]).lower()
                if name_lower in combined or all(p in combined for p in name_parts):
                    validated.append(r)
            return validated

    def search_candidates(self, name: str) -> List[Dict]:
        """Search for multiple people with the same name"""
        logger.info(f"Searching candidates for: {name}")
        try:
            snippets = []
            with DDGS() as ddgs:
                results = list(ddgs.text(f"{name} who is biography profile", max_results=8))
            for r in results:
                snippets.append(f"{r.get('title','')} - {r.get('body','')[:150]}")

            msg = self.client.messages.create(
                model=config.CLAUDE_MODEL,
                max_tokens=600,
                temperature=0,
                messages=[{"role": "user", "content": f"""Given these search results for "{name}", identify up to 4 DIFFERENT real people with this name.

SEARCH RESULTS:
{chr(10).join(snippets[:6])}

For each distinct person, return:
- full_name, role, country, known_for, search_query (for finding their photo)

Respond ONLY with JSON array:
[{{"full_name":"...","role":"...","country":"...","known_for":"...","search_query":"..."}}]"""}]
            )
            response = msg.content[0].text.strip()
            if response.startswith("```json"): response = response[7:]
            if response.endswith("```"):       response = response[:-3]
            candidates = json.loads(response.strip())

            for c in candidates:
                try:
                    with DDGS() as ddgs:
                        imgs = list(ddgs.images(c.get("search_query", c["full_name"]), max_results=1))
                    c["photo_url"] = imgs[0].get("image", "") if imgs else ""
                except Exception:
                    c["photo_url"] = ""

            return candidates
        except Exception as e:
            logger.error(f"Candidate search failed: {e}")
            return [{"full_name": name, "role": "Unknown", "country": "",
                     "known_for": "Could not find info", "search_query": name, "photo_url": ""}]

    def verify_by_name(self, name: str, extra_context: str = "") -> Dict:
        """Full profile verification"""
        logger.info(f"Full verification for: {name}")
        snippets = []
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(f'"{name}" {extra_context} biography profile', max_results=6))
            for r in results:
                snippets.append(f"Title: {r.get('title','')}\n{r.get('body','')[:300]}")
        except Exception as e:
            logger.warning(f"Web search failed: {e}")

        try:
            with DDGS() as ddgs:
                news = list(ddgs.text(f'"{name}" news controversy', max_results=3))
            for r in news:
                snippets.append(f"[NEWS] {r.get('title','')}: {r.get('body','')[:200]}")
        except Exception:
            pass

        web_info  = "\n\n".join(snippets[:7])
        photo_url = self._find_photo(name)
        profile   = self._analyze_profile_from_text(name, web_info, extra_context)
        return self._build_result(profile, photo_url, web_info, input_type="name", input_value=name)

    def verify_by_photo(self, image_bytes: bytes, image_type: str = "image/jpeg") -> Dict:
        """Identify person from photo using Claude Vision"""
        logger.info("Verifying identity by photo...")
        identification = self._identify_from_photo(image_bytes, image_type)
        identified_name = identification.get("name", "")

        if not identified_name or identified_name == "Unknown":
            return {
                "trust_score": 0, "badge": "UNIDENTIFIED", "badge_color": "#636e72",
                "summary": "Could not identify the person in the photo.",
                "identified_name": "", "photo_url": "", "bio": "",
                "social_links": [], "affiliations": [], "red_flags": ["Person could not be identified"],
                "positive_signals": [], "controversies": [], "recommendations": [],
                "checks": {}, "input_type": "photo", "identification": identification
            }

        web_info = ""
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(f'"{identified_name}" biography', max_results=5))
            web_info = "\n".join([r.get("body","")[:200] for r in results])
        except Exception:
            pass

        photo_url = self._find_photo(identified_name)
        profile   = self._analyze_profile_from_text(identified_name, web_info, identification.get("description",""))
        result    = self._build_result(profile, photo_url, web_info, input_type="photo", input_value=identified_name)
        result["identified_name"] = identified_name
        result["identification"]  = identification
        return result

    def verify(self, input_data: Dict) -> Dict:
        name = input_data.get("name", "")
        return self.verify_by_name(name, input_data.get("description", ""))

    def _find_photo(self, name: str) -> str:
        try:
            with DDGS() as ddgs:
                results = list(ddgs.images(f"{name} official portrait photo", max_results=3))
            if results:
                return results[0].get("image", "")
        except Exception:
            pass
        return ""

    def _identify_from_photo(self, image_bytes: bytes, image_type: str) -> Dict:
        try:
            b64 = base64.standard_b64encode(image_bytes).decode("utf-8")
            msg = self.client.messages.create(
                model="claude-sonnet-4-5",
                max_tokens=400,
                messages=[{"role": "user", "content": [
                    {"type": "image", "source": {"type": "base64", "media_type": image_type, "data": b64}},
                    {"type": "text", "text": (
                        "Identify this person if they are a public figure. "
                        "Respond ONLY with JSON:\n"
                        '{"name":"Full name or Unknown","confidence":0-100,'
                        '"description":"brief description","likely_role":"role","context_clues":[]}'
                    )}
                ]}]
            )
            response = msg.content[0].text.strip()
            if response.startswith("```json"): response = response[7:]
            if response.endswith("```"):       response = response[:-3]
            return json.loads(response.strip())
        except Exception as e:
            logger.error(f"Photo ID failed: {e}")
            return {"name": "Unknown", "confidence": 0, "description": "",
                    "likely_role": "Unknown", "context_clues": []}

    def _analyze_profile_from_text(self, name: str, web_info: str, extra: str = "") -> Dict:
        prompt = f"""You are an identity verification expert. Analyze ONLY the information provided.
DO NOT invent anything not present in the sources below.
If something is not found, say "Not found in available sources".

PERSON: {name}
EXTRA CONTEXT: {extra}

WEB INFORMATION:
{web_info[:3000]}

Respond ONLY with JSON:
{{
    "score": 0-100,
    "persona_type": "Politician/Journalist/Celebrity/Business/Academic/Unknown",
    "risk_level": "Low/Medium/High/Critical",
    "summary": "2-3 sentence bio based ONLY on found info",
    "bio": "Detailed paragraph based ONLY on found info",
    "social_links": ["only URLs actually found in search results"],
    "affiliations": ["only organizations actually mentioned"],
    "red_flags": ["only actual concerns found"],
    "positive_signals": ["only actual positive info found"],
    "controversies": ["only actual controversies found"],
    "recommendations": ["advice for user"],
    "interesting_fact": "one notable fact from the results"
}}"""

        try:
            msg = self.client.messages.create(
                model=config.CLAUDE_MODEL,
                max_tokens=800,
                temperature=0,
                messages=[{"role": "user", "content": prompt}]
            )
            response = msg.content[0].text.strip()
            if response.startswith("```json"): response = response[7:]
            if response.endswith("```"):       response = response[:-3]
            return json.loads(response.strip())
        except Exception as e:
            logger.error(f"Profile analysis failed: {e}")
            return {
                "score": 50, "persona_type": "Unknown", "risk_level": "Unknown",
                "summary": "Analysis unavailable", "bio": "",
                "social_links": [], "affiliations": [], "red_flags": [],
                "positive_signals": [], "controversies": [], "recommendations": [],
                "interesting_fact": ""
            }

    def _build_result(self, profile: Dict, photo_url: str, web_info: str,
                      input_type: str, input_value: str) -> Dict:
        score = profile.get("score", 50)
        if score >= 75:   badge, badge_color = "VERIFIED",   "#00b894"
        elif score >= 50: badge, badge_color = "UNCERTAIN",  "#fdcb6e"
        else:             badge, badge_color = "SUSPICIOUS", "#e17055"
        return {
            "trust_score":      score,
            "badge":            badge,
            "badge_color":      badge_color,
            "summary":          profile.get("summary", ""),
            "bio":              profile.get("bio", ""),
            "photo_url":        photo_url,
            "persona_type":     profile.get("persona_type", "Unknown"),
            "risk_level":       profile.get("risk_level", "Unknown"),
            "social_links":     profile.get("social_links", []),
            "affiliations":     profile.get("affiliations", []),
            "red_flags":        profile.get("red_flags", []),
            "positive_signals": profile.get("positive_signals", []),
            "controversies":    profile.get("controversies", []),
            "recommendations":  profile.get("recommendations", []),
            "interesting_fact": profile.get("interesting_fact", ""),
            "checks":           {"profile": profile},
            "input_type":       input_type,
            "input_value":      input_value,
        }

