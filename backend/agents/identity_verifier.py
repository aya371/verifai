from anthropic import Anthropic
from config import config
from backend.utils.logger import logger
from typing import Dict, List, Optional
from ddgs import DDGS
import re
import requests as http_requests
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

    # ── Wikipedia API (primary source — zero hallucination) ────────────
    def _fetch_wikipedia(self, name: str) -> Dict:
        """Fetch structured data from Wikipedia API — factual, cited, grounded"""
        try:
            # Search Wikipedia for the person
            search_url = "https://en.wikipedia.org/w/api.php"
            search_params = {
                "action": "query",
                "list": "search",
                "srsearch": name,
                "srlimit": 3,
                "format": "json"
            }
            search_resp = http_requests.get(search_url, params=search_params, timeout=5)
            search_data = search_resp.json()
            results = search_data.get("query", {}).get("search", [])

            if not results:
                return {"found": False, "source": "Wikipedia", "data": ""}

            # Get the first result's page ID
            page_id = results[0].get("pageid")
            title   = results[0].get("title", "")

            # Fetch full extract
            extract_params = {
                "action": "query",
                "pageids": page_id,
                "prop": "extracts|categories|links",
                "exintro": True,
                "explaintext": True,
                "exsectionformat": "plain",
                "pllimit": 20,
                "format": "json"
            }
            extract_resp = http_requests.get(search_url, params=extract_params, timeout=5)
            extract_data = extract_resp.json()
            pages = extract_data.get("query", {}).get("pages", {})
            page  = pages.get(str(page_id), {})
            extract = page.get("extract", "")

            if not extract or len(extract) < 50:
                return {"found": False, "source": "Wikipedia", "data": ""}

            # Check name relevance — make sure this is actually about the right person
            name_parts = name.lower().split()
            extract_lower = extract.lower()
            if not any(part in extract_lower for part in name_parts if len(part) > 2):
                return {"found": False, "source": "Wikipedia", "data": ""}

            logger.info(f"Wikipedia found: {title} ({len(extract)} chars)")
            return {
                "found": True,
                "source": "Wikipedia",
                "title": title,
                "url": f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}",
                "data": extract[:4000],
                "page_id": page_id
            }

        except Exception as e:
            logger.warning(f"Wikipedia fetch failed: {e}")
            return {"found": False, "source": "Wikipedia", "data": ""}

    def _fetch_wikidata(self, name: str) -> Dict:
        """Fetch structured facts from Wikidata (birth date, nationality, occupation)"""
        try:
            url = "https://www.wikidata.org/w/api.php"
            params = {
                "action": "wbsearchentities",
                "search": name,
                "language": "en",
                "limit": 1,
                "format": "json",
                "type": "item"
            }
            resp = http_requests.get(url, params=params, timeout=5)
            data = resp.json()
            results = data.get("search", [])
            if not results:
                return {}

            entity = results[0]
            return {
                "id":          entity.get("id", ""),
                "label":       entity.get("label", ""),
                "description": entity.get("description", ""),
                "url":         entity.get("url", ""),
            }
        except Exception as e:
            logger.warning(f"Wikidata fetch failed: {e}")
            return {}

    def verify_by_name(self, name: str, extra_context: str = "") -> Dict:
        """Full profile verification — Wikipedia first, then web supplements"""
        logger.info(f"Full verification for: {name}")

        sources_used = []
        all_info_parts = []

        # ── Layer 1: Wikipedia (most reliable) ────────────────────────
        wiki = self._fetch_wikipedia(name)
        if wiki.get("found"):
            all_info_parts.append(f"[WIKIPEDIA - VERIFIED SOURCE]\n{wiki['data']}")
            sources_used.append(wiki.get("url", ""))
            logger.info("Wikipedia data found and loaded")

        # ── Layer 2: Wikidata structured facts ─────────────────────────
        wikidata = self._fetch_wikidata(name)
        if wikidata.get("description"):
            all_info_parts.append(f"[WIKIDATA]\nDescription: {wikidata['description']}")

        # ── Layer 3: DuckDuckGo web search (supplement only) ───────────
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(
                    f'"{name}" {extra_context} biography profile',
                    max_results=5
                ))
            for r in results:
                url   = r.get("href", "")
                title = r.get("title", "")
                body  = r.get("body", "")[:400]
                # Only use if name appears in result
                if any(p in (title + body).lower() for p in name.lower().split() if len(p) > 2):
                    all_info_parts.append(f"[WEB: {url}]\nTitle: {title}\n{body}")
                    if url and url not in sources_used:
                        sources_used.append(url)
        except Exception as e:
            logger.warning(f"Web search failed: {e}")

        # ── Layer 4: News search ───────────────────────────────────────
        try:
            with DDGS() as ddgs:
                news = list(ddgs.text(f'"{name}" news controversy', max_results=3))
            for r in news:
                body = r.get("body", "")[:300]
                if any(p in body.lower() for p in name.lower().split() if len(p) > 2):
                    all_info_parts.append(f"[NEWS: {r.get('href','')}]\n{r.get('title','')}: {body}")
        except Exception:
            pass

        web_info   = "\n\n---\n\n".join(all_info_parts)
        photo_url  = self._find_photo(name)
        has_wiki   = wiki.get("found", False)
        profile    = self._analyze_profile_strict(name, web_info, extra_context, has_wiki)

        return self._build_result(profile, photo_url, web_info,
                                   input_type="name", input_value=name)

    def _analyze_profile_strict(self, name: str, web_info: str,
                                 extra: str = "", has_wikipedia: bool = False) -> Dict:
        """
        Strict analysis — Claude is forbidden from inventing anything.
        Every field must come from the provided sources.
        """
        wiki_instruction = (
            "The information includes a WIKIPEDIA article which is a verified, "
            "cited source. Prioritize Wikipedia data over web snippets."
            if has_wikipedia else
            "No Wikipedia article was found. Be extra conservative — only report "
            "what is clearly stated in the sources. If uncertain, say 'Not confirmed'."
        )

        prompt = f"""You are a strict identity verification system. Your job is to extract ONLY facts that are explicitly stated in the sources below.

STRICT RULES:
1. NEVER invent, assume, or extrapolate any information
2. If a field is not found in the sources, use exactly: "Not found in available sources"
3. Only include social links that appear as actual URLs in the sources
4. Only include affiliations explicitly named in the sources
5. Do not combine partial information to create new claims
6. Confidence score must reflect how much was actually found (not how famous the person is)

{wiki_instruction}

PERSON BEING VERIFIED: {name}
ADDITIONAL CONTEXT: {extra if extra else "None"}

SOURCES (use ONLY these):
{web_info[:4000]}

Return ONLY this JSON (no extra text):
{{
    "score": 0-100,
    "persona_type": "Politician/Journalist/Celebrity/Business/Academic/Unknown",
    "risk_level": "Low/Medium/High/Critical/Unknown",
    "summary": "2-3 sentences from sources only, or 'Insufficient information found'",
    "bio": "Detailed paragraph from sources only, or 'No biography found in available sources'",
    "social_links": ["only URLs explicitly found in sources"],
    "affiliations": ["only organizations explicitly named in sources"],
    "red_flags": ["only actual concerns explicitly mentioned in sources"],
    "positive_signals": ["only actual positive facts explicitly in sources"],
    "controversies": ["only actual controversies explicitly mentioned"],
    "recommendations": ["practical advice for user about this identity"],
    "interesting_fact": "one specific fact from sources, or empty string if none found",
    "data_quality": "HIGH (Wikipedia found) / MEDIUM (web only) / LOW (minimal data)"
}}"""

        try:
            msg = self.client.messages.create(
                model=config.CLAUDE_MODEL,
                max_tokens=900,
                temperature=0,
                messages=[{"role": "user", "content": prompt}]
            )
            response = msg.content[0].text.strip()
            if response.startswith("```json"): response = response[7:]
            if response.endswith("```"):       response = response[:-3]
            result = json.loads(response.strip())

            # Post-process: if no Wikipedia and score > 70, cap at 65
            if not has_wikipedia and result.get("score", 0) > 70:
                result["score"] = 65
                logger.info("Score capped at 65 (no Wikipedia source)")

            return result

        except Exception as e:
            logger.error(f"Profile analysis failed: {e}")
            return {
                "score": 0, "persona_type": "Unknown", "risk_level": "Unknown",
                "summary": "Analysis unavailable due to an error.",
                "bio": "Not found in available sources",
                "social_links": [], "affiliations": [], "red_flags": [],
                "positive_signals": [], "controversies": [], "recommendations": [],
                "interesting_fact": "", "data_quality": "LOW"
            }

    def search_across_platforms(self, name: str) -> List[Dict]:
        """Search across platforms with strict name validation"""
        logger.info(f"Searching platforms for: {name}")
        found_profiles = []

        name_lower = name.lower().strip()
        name_parts = [p for p in name_lower.split() if len(p) > 2]

        def is_match(title: str, body: str, url: str) -> bool:
            combined = (title + " " + body + " " + url).lower()
            if name_lower in combined:
                return True
            if len(name_parts) >= 2:
                return all(p in combined for p in name_parts)
            return name_lower in title.lower()

        # First check Wikipedia
        wiki = self._fetch_wikipedia(name)
        if wiki.get("found"):
            found_profiles.append({
                "platform": "Wikipedia",
                "icon": "W",
                "color": "#888888",
                "url": wiki.get("url", ""),
                "title": wiki.get("title", name),
                "snippet": wiki.get("data", "")[:200],
            })

        for platform in PLATFORMS:
            if platform["name"] == "Wikipedia":
                continue
            try:
                query = f'"{name}" site:{platform["site"]}'
                with DDGS() as ddgs:
                    results = list(ddgs.text(query, max_results=3))
                for result in results:
                    url   = result.get("href", "")
                    title = result.get("title", "")
                    body  = result.get("body", "")
                    if not url or len(body) < 20:
                        continue
                    if not is_match(title, body, url):
                        continue
                    found_profiles.append({
                        "platform": platform["name"],
                        "icon":     platform["icon"],
                        "color":    platform["color"],
                        "url":      url,
                        "title":    title,
                        "snippet":  body[:200],
                    })
                    break
            except Exception as e:
                logger.warning(f"Search failed for {platform['name']}: {e}")

        logger.info(f"Found {len(found_profiles)} verified profiles")
        return found_profiles

    def _claude_identify_person(self, name: str) -> Dict:
        try:
            msg = self.client.messages.create(
                model=config.CLAUDE_MODEL,
                max_tokens=300,
                temperature=0,
                messages=[{"role": "user", "content": f"""What do you know about "{name}"?
Respond ONLY with JSON:
{{"identified":true/false,"full_name":"","description":"","known_urls":[],"known_platforms":[],"nationality":""}}"""}]
            )
            response = msg.content[0].text.strip()
            if response.startswith("```json"): response = response[7:]
            if response.endswith("```"):       response = response[:-3]
            return json.loads(response.strip())
        except Exception:
            return {"identified": False, "full_name": name, "description": "",
                    "known_urls": [], "known_platforms": [], "nationality": ""}

    def _claude_validate_results(self, name: str, results: List[Dict], known_info: Dict) -> List[Dict]:
        if not results:
            return []
        results_text = ""
        for i, r in enumerate(results):
            results_text += f"\n[{i}] Platform: {r['platform']}\nTitle: {r['title']}\nURL: {r['url']}\nSnippet: {r['snippet'][:150]}\n"
        try:
            msg = self.client.messages.create(
                model=config.CLAUDE_MODEL,
                max_tokens=200,
                temperature=0,
                messages=[{"role": "user", "content": f"""For "{name}", which of these results are actually about this person?
{results_text}
Return ONLY a JSON array of valid indices, e.g. [0, 2]:"""}]
            )
            response = msg.content[0].text.strip()
            if response.startswith("```json"): response = response[7:]
            if response.endswith("```"):       response = response[:-3]
            valid_indices = json.loads(response.strip())
            return [results[i] for i in valid_indices if i < len(results)]
        except Exception:
            name_lower = name.lower()
            name_parts = [p for p in name_lower.split() if len(p) > 2]
            return [r for r in results if
                    name_lower in (r["title"] + r["snippet"] + r["url"]).lower() or
                    all(p in (r["title"] + r["snippet"]).lower() for p in name_parts)]

    def search_candidates(self, name: str) -> List[Dict]:
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
                messages=[{"role": "user", "content": f"""Given these results for "{name}", identify up to 4 DIFFERENT real people.

{chr(10).join(snippets[:6])}

Return ONLY JSON array:
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

    def verify_by_photo(self, image_bytes: bytes, image_type: str = "image/jpeg") -> Dict:
        logger.info("Verifying by photo...")
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

        result = self.verify_by_name(identified_name)
        result["identified_name"] = identified_name
        result["identification"]  = identification
        result["input_type"]      = "photo"
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
            "data_quality":     profile.get("data_quality", "MEDIUM"),
            "checks":           {"profile": profile},
            "input_type":       input_type,
            "input_value":      input_value,
        }
