"""
conflict_detector.py — Auto-detect countries at war / elevated tension
from GDELT, news feeds, and pre-seeded conflict database.
No AI required: pure rule-based keyword scoring.
"""
import asyncio
import aiohttp
import json
import re
import time
from pathlib import Path
from collections import defaultdict

# ── Country code lookups ──────────────────────────────────────────────────────
COUNTRY_KEYWORDS = {
    "UA": ["ukraine","ukrainian","kyiv","kharkiv","zaporizhzhia","kherson","donetsk","mariupol","zelensky"],
    "RU": ["russia","russian","kremlin","putin","moscow","wagner","rvsn","vpk"],
    "IL": ["israel","israeli","idf","netanyahu","tel aviv","haifa"],
    "PS": ["gaza","hamas","palestin","west bank","rafah","khan younis"],
    "IR": ["iran","iranian","irgc","tehran","khamenei"],
    "LB": ["hezbollah","lebanon","lebanese","beirut"],
    "SY": ["syria","syrian","damascus","aleppo","idlib"],
    "YE": ["houthi","yemen","yemeni","sanaa","aden"],
    "SD": ["sudan","sudanese","rsf","khartoum","darfur"],
    "MM": ["myanmar","burma","burmese","junta","nld"],
    "KP": ["north korea","dprk","pyongyang","kim jong"],
    "TW": ["taiwan","taipei","roc"],
    "CN": ["china","chinese","pla","beijing","xi jinping"],
    "AF": ["afghanistan","afghan","taliban","kabul"],
    "PK": ["pakistan","pakistani","islamabad"],
    "IN": ["india","indian","new delhi","modi"],
    "ET": ["ethiopia","ethiopian","tigray","amhara","fano"],
    "SO": ["somalia","al-shabaab","mogadishu"],
    "CD": ["congo","drc","m23","kinshasa"],
    "ML": ["mali","malian","bamako"],
    "BF": ["burkina","faso","ouagadougou"],
    "NE": ["niger","nigerien","niamey"],
}

WAR_KEYWORDS = [
    "airstrike","missile","bomb","explosion","attack","offensive","counteroffensive",
    "troops","invasion","shelling","artillery","drone strike","killed","casualties",
    "military operation","launch","rocket","warplane","fighter jet","naval vessel",
    "combat","frontline","breakthrough","retreat","siege","occupation",
]

SEVERITY_BUMP = {
    "nuclear": 50, "icbm": 40, "ballistic missile": 35, "chemical weapon": 40,
    "nuke": 50, "war": 20, "invasion": 25, "genocide": 30,
    "killed hundreds": 20, "massive attack": 15, "carpet bomb": 30,
}

class ConflictDetector:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.country_scores: dict[str, float] = defaultdict(float)
        self.war_status: dict[str, dict] = {}
        self.last_update = 0
        self.update_interval = 900  # 15 min
        
        # Load seeded conflicts as baseline
        try:
            with open(self.data_dir / "conflicts.json") as f:
                conflicts = json.load(f)
            for c in conflicts:
                for country in c.get("countries", []):
                    sev = {"critical": 90, "high": 70, "medium": 50, "low": 30}.get(c.get("severity","medium"), 40)
                    if c.get("status") == "active_war":
                        sev = max(sev, 80)
                    self.war_status[country] = {
                        "status": c.get("status","elevated"),
                        "score": sev,
                        "conflict_id": c["id"],
                        "conflict_name": c["name"],
                        "severity": c.get("severity","medium"),
                    }
        except Exception:
            pass

    async def fetch_gdelt_tension(self, session: aiohttp.ClientSession) -> list[dict]:
        """Fetch GDELT event counts for conflict countries."""
        results = []
        queries = [
            ("ukraine war frontline attack", "UA"),
            ("russia military offensive shelling", "RU"),
            ("israel hamas airstrike", "IL"),
            ("gaza attack killed civilians", "PS"),
            ("iran missile drone attack", "IR"),
            ("hezbollah rocket strike", "LB"),
            ("houthi yemen attack red sea", "YE"),
            ("north korea missile test", "KP"),
            ("taiwan strait military exercise china", "TW"),
            ("sudan rsf attack khartoum", "SD"),
            ("myanmar junta airstrike", "MM"),
        ]
        base_url = "https://api.gdeltproject.org/api/v2/doc/doc"
        for q, country in queries:
            try:
                params = {
                    "query": q,
                    "mode": "artlist",
                    "maxrecords": "10",
                    "format": "json",
                    "timespan": "6h",
                    "sort": "datedesc",
                }
                async with session.get(base_url, params=params, timeout=aiohttp.ClientTimeout(total=8)) as resp:
                    if resp.status == 200:
                        data = await resp.json(content_type=None)
                        articles = data.get("articles", []) or []
                        results.append({"country": country, "count": len(articles), "query": q})
            except Exception:
                pass
        return results

    def score_article(self, text: str) -> float:
        """Score a piece of text for war/conflict intensity."""
        text_lower = text.lower()
        score = 0.0
        for kw in WAR_KEYWORDS:
            if kw in text_lower:
                score += 5
        for kw, bump in SEVERITY_BUMP.items():
            if kw in text_lower:
                score += bump
        return min(score, 100)

    async def update(self) -> dict[str, dict]:
        """Update war status from live GDELT data."""
        now = time.time()
        if now - self.last_update < self.update_interval:
            return self.war_status
        
        async with aiohttp.ClientSession() as session:
            gdelt_results = await self.fetch_gdelt_tension(session)
        
        # Boost scores based on article counts
        for result in gdelt_results:
            country = result["country"]
            count = result["count"]
            if count >= 8:
                boost = 30
            elif count >= 5:
                boost = 20
            elif count >= 2:
                boost = 10
            else:
                boost = 0
            
            if country in self.war_status:
                self.war_status[country]["score"] = min(100, self.war_status[country]["score"] + boost * 0.1)
            elif boost > 10:
                self.war_status[country] = {
                    "status": "elevated",
                    "score": min(100, 40 + boost),
                    "conflict_id": f"auto_{country}",
                    "conflict_name": f"Auto-detected conflict {country}",
                    "severity": "medium" if boost < 20 else "high",
                }
        
        self.last_update = now
        return self.war_status

    def get_status(self, country: str) -> dict:
        return self.war_status.get(country, {"status": "normal", "score": 0, "severity": "low"})

    def get_all_war_countries(self) -> list[str]:
        return [c for c, s in self.war_status.items() if s.get("status") in ("active_war", "elevated", "conflict")]

    def get_critical_countries(self) -> list[str]:
        return [c for c, s in self.war_status.items() if s.get("severity") == "critical" or s.get("score", 0) >= 80]

    def to_dict(self) -> dict:
        return {
            "war_status": self.war_status,
            "critical": self.get_critical_countries(),
            "elevated": self.get_all_war_countries(),
            "last_update": self.last_update,
        }

# Singleton
_detector: ConflictDetector | None = None

def get_detector(data_dir: str = "data") -> ConflictDetector:
    global _detector
    if _detector is None:
        _detector = ConflictDetector(data_dir)
    return _detector
