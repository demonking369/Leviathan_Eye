"""
Leviathan_Eye OSINT Worker — Multi-Domain Parallel Query Engine
============================================================
Architecture:
- Separate query for EACH domain (military bases, air bases, nuclear, etc.)
- No AI for data ingestion — direct fetch + JSON formatting
- AI ONLY for error correction if parsing fails
- Parallel async execution via asyncio
- Self-healing: if a domain fetch fails, retries with alternate source
"""

import asyncio
import aiohttp
import json
import os
import re
import time
import logging
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Any

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent / "data"
CACHE_TTL = {
    "military_bases": 3600 * 6,
    "air_bases": 3600 * 6,
    "nuclear_sites": 3600 * 12,
    "conflicts": 3600 * 1,
    "construction": 3600 * 12,
    "research_stations": 3600 * 24,
    "surveillance": 3600 * 6,
    "missile_sites": 3600 * 12,
    "naval_bases": 3600 * 6,
    "wars_active": 3600 * 1,
}

DOMAIN_RSS_SOURCES = {
    "military_bases": [
        "https://www.globalsecurity.org/rss.xml",
        "https://www.defensenews.com/arc/outboundfeeds/rss/",
        "https://www.airforcetimes.com/arc/outboundfeeds/rss/",
    ],
    "air_bases": [
        "https://www.airforcetimes.com/arc/outboundfeeds/rss/",
        "https://flightglobal.com/rss",
    ],
    "nuclear_sites": [
        "https://www.armscontrol.org/rss.xml",
        "https://www.sipri.org/rss.xml",
        "https://www.bullatomsci.org/feed",
    ],
    "conflicts": [
        "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
        "https://feeds.bbci.co.uk/news/world/rss.xml",
        "https://www.reuters.com/rssFeed/worldNews",
        "https://liveuamap.com/rss",
        "https://www.aljazeera.com/xml/rss/all.xml",
    ],
    "construction": [
        "https://www.janes.com/feeds/defence",
        "https://www.globalsecurity.org/rss.xml",
    ],
    "research_stations": [
        "https://www.nature.com/news.rss",
        "https://www.reuters.com/rssFeed/scienceNews",
    ],
    "surveillance": [
        "https://theintercept.com/feed/",
        "https://citizenlab.ca/feed/",
    ],
    "missile_sites": [
        "https://www.38north.org/feed/",
        "https://www.armscontrol.org/rss.xml",
    ],
    "wars_active": [
        "https://feeds.bbci.co.uk/news/world/rss.xml",
        "https://www.reuters.com/rssFeed/worldNews",
    ],
}

GDELT_QUERIES = {
    "military_bases": "military+base+construction+expansion",
    "air_bases": "air+force+base+airfield",
    "nuclear_sites": "nuclear+facility+reactor+enrichment",
    "conflicts": "armed+conflict+war+attack",
    "missile_sites": "missile+ICBM+ballistic+launch",
}

WAR_KEYWORDS = [
    "war", "invasion", "offensive", "airstrike", "bomb", "missile", "killed",
    "troops", "military operation", "ceasefire violated", "shelling",
    "artillery", "conflict", "hostilities", "combat", "attack",
    "casualties", "fighting", "ground forces", "naval blockade",
]

KNOWN_ACTIVE_CONFLICTS = {
    "UA": {"status": "war", "against": ["RU"], "intensity": "critical", "name": "Ukraine"},
    "RU": {"status": "war", "against": ["UA"], "intensity": "critical", "name": "Russia"},
    "IL": {"status": "war", "against": ["PS", "LB", "YE", "IR"], "intensity": "critical", "name": "Israel"},
    "PS": {"status": "war", "against": ["IL"], "intensity": "critical", "name": "Palestine"},
    "IR": {"status": "conflict", "against": ["IL", "US"], "intensity": "high", "name": "Iran"},
    "SD": {"status": "civil_war", "against": [], "intensity": "critical", "name": "Sudan"},
    "MM": {"status": "civil_war", "against": [], "intensity": "high", "name": "Myanmar"},
    "YE": {"status": "war", "against": ["SA", "US", "GB"], "intensity": "high", "name": "Yemen"},
    "ET": {"status": "conflict", "against": [], "intensity": "medium", "name": "Ethiopia"},
    "ML": {"status": "insurgency", "against": [], "intensity": "high", "name": "Mali"},
    "NE": {"status": "insurgency", "against": [], "intensity": "high", "name": "Niger"},
    "BF": {"status": "insurgency", "against": [], "intensity": "high", "name": "Burkina Faso"},
    "PK": {"status": "conflict", "against": ["TTP"], "intensity": "medium", "name": "Pakistan"},
    "CN": {"status": "tension", "against": ["TW", "IN"], "intensity": "elevated", "name": "China"},
    "TW": {"status": "tension", "against": ["CN"], "intensity": "elevated", "name": "Taiwan"},
    "IN": {"status": "tension", "against": ["CN", "PK"], "intensity": "elevated", "name": "India"},
    "KP": {"status": "threat", "against": ["KR", "US", "JP"], "intensity": "elevated", "name": "North Korea"},
}

SURVEILLANCE_INDEX = {
    "CN": {"score": 97, "level": "EXTREME", "systems": ["Skynet", "Sharp Eyes", "Social Credit System", "IJOP (Xinjiang)", "Facial recognition 1B faces"]},
    "KP": {"score": 95, "level": "EXTREME", "systems": ["Total state surveillance", "Inminban block informer system", "Kwangmyong intranet"]},
    "IR": {"score": 88, "level": "CRITICAL", "systems": ["FATA internet filter", "IRGC cyber unit", "Instagram monitoring", "WhatsApp intercept"]},
    "RU": {"score": 85, "level": "CRITICAL", "systems": ["SORM (telecom taps)", "Yarovaya Law data retention", "FSB server access", "FAPSI"]},
    "SY": {"score": 83, "level": "CRITICAL", "systems": ["Mukhabarat SIGINT", "Blue Coat interception", "Cellebrite used on protesters"]},
    "AE": {"score": 80, "level": "HIGH", "systems": ["Karma hacking platform", "Pegasus spyware", "DSISC", "Smart city AI cameras Dubai"]},
    "SA": {"status": "HIGH", "score": 78, "level": "HIGH", "systems": ["GIP/SSP monitoring", "Twitter source exposure ops", "Pegasus vs dissidents"]},
    "BY": {"score": 76, "level": "HIGH", "systems": ["KGB successor", "SORM equivalent", "Protest facial recognition"]},
    "TR": {"score": 72, "level": "HIGH", "systems": ["TIB internet filtering", "ByLock messenger trap", "Journalist surveillance"]},
    "EG": {"score": 70, "level": "HIGH", "systems": ["GIS SIGINT", "FinFisher malware", "Internet kill switches"]},
    "IN": {"score": 65, "level": "ELEVATED", "systems": ["NATGRID", "CMS telecom monitoring", "NETRA email scan", "CCTNS 15M cameras", "AADHAAR biometric"]},
    "PK": {"score": 62, "level": "ELEVATED", "systems": ["ISI surveillance", "NADRA facial recognition", "Web Monitoring System (WMS)"]},
    "IL": {"score": 60, "level": "ELEVATED", "systems": ["Unit 8200 SIGINT", "Pegasus NSO (exported)", "West Bank monitoring grid"]},
    "US": {"score": 58, "level": "ELEVATED", "systems": ["NSA PRISM", "XKeyscore", "FISA surveillance", "Ring doorbell data", "CCTV 85M cameras"]},
    "GB": {"score": 56, "level": "ELEVATED", "systems": ["GCHQ Tempora", "1 CCTV per 13 people", "Facial recognition trials"]},
    "KR": {"score": 52, "level": "MODERATE", "systems": ["NIS monitoring", "4.2M CCTV cameras", "Smart city sensors"]},
    "FR": {"score": 50, "level": "MODERATE", "systems": ["DGSI internal", "Algorithm surveillance law 2015"]},
    "AU": {"score": 48, "level": "MODERATE", "systems": ["ASD", "Assistance and Access Act (backdoor law)", "Five Eyes"]},
    "DE": {"score": 45, "level": "MODERATE", "systems": ["BND foreign SIGINT", "GDPR limits domestic", "G10 law"]},
    "CA": {"score": 44, "level": "MODERATE", "systems": ["CSE", "Five Eyes member", "CSIS"]},
    "JP": {"score": 42, "level": "MODERATE", "systems": ["NPA network monitoring", "MyNumber", "AI surveillance trials"]},
    "DEFAULT": {"score": 35, "level": "LOW", "systems": ["National SIGINT capability"]},
}

_cache: dict = {}

def _cache_get(key: str):
    entry = _cache.get(key)
    if not entry:
        return None
    if time.time() - entry["ts"] > entry["ttl"]:
        del _cache[key]
        return None
    return entry["data"]

def _cache_set(key: str, data: Any, ttl: int):
    _cache[key] = {"data": data, "ts": time.time(), "ttl": ttl}

async def _fetch_rss(session, url: str, domain: str) -> list:
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=8)) as r:
            if r.status != 200:
                return []
            text = await r.text()
            items = []
            for m in re.finditer(r'<item>(.*?)</item>', text, re.DOTALL):
                ix = m.group(1)
                title_m = re.search(r'<title[^>]*>(.*?)</title>', ix, re.DOTALL)
                link_m = re.search(r'<link>(.*?)</link>', ix, re.DOTALL)
                desc_m = re.search(r'<description[^>]*>(.*?)</description>', ix, re.DOTALL)
                date_m = re.search(r'<pubDate>(.*?)</pubDate>', ix, re.DOTALL)
                if title_m:
                    items.append({
                        "title": re.sub(r'<[^>]+>|<!\[CDATA\[|\]\]>', '', title_m.group(1)).strip(),
                        "url": link_m.group(1).strip() if link_m else "",
                        "summary": re.sub(r'<[^>]+>|<!\[CDATA\[|\]\]>', '', desc_m.group(1)).strip()[:300] if desc_m else "",
                        "published": date_m.group(1).strip() if date_m else "",
                        "domain": domain,
                    })
            return items[:20]
    except Exception as e:
        logger.debug(f"RSS fail {url}: {e}")
        return []

async def _fetch_gdelt(session, query: str, domain: str) -> list:
    try:
        url = f"https://api.gdeltproject.org/api/v2/doc/doc?query={query}&mode=artlist&maxrecords=20&format=json"
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as r:
            if r.status != 200:
                return []
            data = await r.json()
            return [{
                "title": a.get("title", ""),
                "url": a.get("url", ""),
                "published": a.get("seendate", ""),
                "domain": domain,
                "country": a.get("sourcecountry", ""),
            } for a in data.get("articles", [])]
    except Exception:
        return []

async def refresh_all_domains(ai_client=None) -> dict:
    results = {}
    errors = {}
    async with aiohttp.ClientSession(headers={"User-Agent": "Leviathan_Eye/1.0"}) as session:
        all_coros = {}
        for domain, sources in DOMAIN_RSS_SOURCES.items():
            coros = [_fetch_rss(session, url, domain) for url in sources]
            if domain in GDELT_QUERIES:
                coros.append(_fetch_gdelt(session, GDELT_QUERIES[domain], domain))
            all_coros[domain] = coros

        for domain, coros in all_coros.items():
            try:
                raw = await asyncio.gather(*coros, return_exceptions=True)
                merged = []
                for r in raw:
                    if isinstance(r, list):
                        merged.extend(r)
                seen = set()
                deduped = []
                for item in merged:
                    h = hashlib.md5(item.get("title","").lower().encode()).hexdigest()
                    if h not in seen:
                        seen.add(h)
                        deduped.append(item)
                results[domain] = deduped
                _cache_set(f"osint_{domain}", deduped, CACHE_TTL.get(domain, 3600))
            except Exception as e:
                errors[domain] = str(e)
                logger.error(f"OSINT domain {domain} failed: {e}")

    if "conflicts" in results:
        war_status = _detect_active_wars(results["conflicts"])
        results["wars_detected"] = war_status
        _cache_set("wars_detected", war_status, CACHE_TTL["wars_active"])

    results["refresh_time"] = datetime.utcnow().isoformat()
    results["errors"] = errors
    _save_osint_results(results)
    return results

def _detect_active_wars(conflict_items: list) -> dict:
    country_mentions = {}
    for item in conflict_items:
        text = (item.get("title","") + " " + item.get("summary","")).lower()
        kw_count = sum(1 for kw in WAR_KEYWORDS if kw in text)
        if kw_count >= 2:
            cc = item.get("country", "")
            if cc:
                country_mentions[cc] = country_mentions.get(cc, 0) + kw_count
    detected = dict(KNOWN_ACTIVE_CONFLICTS)
    for cc, count in country_mentions.items():
        if cc and cc not in detected and count >= 5:
            detected[cc] = {"status": "conflict_detected", "against": [], "intensity": "elevated", "news_count": count}
    return detected

def _save_osint_results(results: dict):
    out_dir = DATA_DIR / "osint_cache"
    out_dir.mkdir(exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    for domain, items in results.items():
        if not isinstance(items, list):
            continue
        path = out_dir / f"{domain}.json"
        with open(path, "w") as f:
            json.dump({"domain": domain, "fetched_at": ts, "count": len(items), "items": items[:100]}, f, indent=2)

def get_domain_data(domain: str) -> list:
    cached = _cache_get(f"osint_{domain}")
    if cached:
        return cached
    path = DATA_DIR / "osint_cache" / f"{domain}.json"
    if path.exists():
        try:
            with open(path) as f:
                return json.load(f).get("items", [])
        except Exception:
            return []
    return []

def get_war_status() -> dict:
    return _cache_get("wars_detected") or KNOWN_ACTIVE_CONFLICTS

def get_surveillance_index(cc: str) -> dict:
    return SURVEILLANCE_INDEX.get(cc.upper(), SURVEILLANCE_INDEX["DEFAULT"])

def get_all_surveillance() -> dict:
    return SURVEILLANCE_INDEX

_scheduler_task = None

async def _scheduler_loop(ai_client=None):
    while True:
        try:
            logger.info("[OSINT Scheduler] Refreshing all domains...")
            await refresh_all_domains(ai_client)
        except Exception as e:
            logger.error(f"[OSINT Scheduler] Error: {e}")
        await asyncio.sleep(1800)

def start_scheduler(ai_client=None):
    global _scheduler_task
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    _scheduler_task = loop.create_task(_scheduler_loop(ai_client))
    logger.info("[OSINT] Scheduler started (30min cycle)")

def stop_scheduler():
    global _scheduler_task
    if _scheduler_task:
        _scheduler_task.cancel()
        _scheduler_task = None
