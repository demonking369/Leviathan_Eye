"""Leviathan_Eye Backend — FastAPI"""
import asyncio, json, logging, os, time, re
from pathlib import Path
from datetime import datetime
from typing import Optional, Any
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

from ai_pipeline import AIPipeline
from data_manager import DataManager
import osint_worker
import cyber_engine

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

CONFIG_PATH = Path(__file__).parent / "config.json"
DATA_DIR = Path(__file__).parent.parent / "data"

def _dm_load_json(filename: str):
    """Load a raw JSON file from data dir, return [] or {} on missing."""
    p = DATA_DIR / filename
    if not p.exists():
        return []
    try:
        with open(p) as f:
            return json.load(f)
    except Exception:
        return []


def load_config():
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH) as f:
            return json.load(f)
    return {"mode": "no_ai"}

cfg = load_config()
app = FastAPI(title="Leviathan_Eye", version="9.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

ai = AIPipeline()
ai.load_config()
dm = DataManager()
ws_clients: list[WebSocket] = []

@app.on_event("startup")
async def startup_event():
    cyber_engine.start_cyber_engine()

@app.on_event("shutdown")
async def shutdown_event():
    cyber_engine.stop_cyber_engine()

FRONTEND_DIR = Path(__file__).parent.parent / "frontend"

# ─── Frontend Serving ────────────────────────────────────────────────────────
@app.get("/", response_class=FileResponse)
async def serve_frontend():
    return FileResponse(FRONTEND_DIR / "index.html")

@app.get("/app.js", response_class=FileResponse)
async def serve_app_js():
    return FileResponse(FRONTEND_DIR / "app.js")

# Mount frontend static files (css, js, assets if any)
if FRONTEND_DIR.exists():
    app.mount("/frontend", StaticFiles(directory=str(FRONTEND_DIR)), name="frontend")

# ─── Startup ────────────────────────────────────────────────────────────────
@app.on_event("startup")
async def startup():
    # Reload AI config (config.json written by START.bat before server starts)
    ai.load_config()
    try:
        osint_worker.start_scheduler(ai if cfg.get("mode") != "no_ai" else None)
        logger.info("[OK] OSINT scheduler started")
    except Exception as e:
        logger.error(f"[ERR] OSINT scheduler failed: {e}")
    try:
        cyber_engine.start_cyber_engine()
        logger.info("[OK] Cyber engine started")
    except Exception as e:
        logger.error(f"[ERR] Cyber engine failed: {e}")
    logger.info("=" * 50)
    logger.info("  Leviathan_Eye running at http://localhost:8000")
    logger.info("=" * 50)

@app.on_event("shutdown")
async def shutdown():
    osint_worker.stop_scheduler()
    cyber_engine.stop_cyber_engine()

# ─── Health ─────────────────────────────────────────────────────────────────
@app.get("/health")
async def health():
    return {"status": "ok", "version": "9.0", "time": datetime.utcnow().isoformat()}

# ─── Map data endpoints ─────────────────────────────────────────────────────
@app.get("/api/v1/map/bases")
async def get_bases():
    # Try new format first (bases.json), fallback to military_bases.json
    for fname in ["bases.json", "military_bases.json"]:
        path = DATA_DIR / fname
        if path.exists():
            with open(path) as f:
                return json.load(f)
    return []

# Short-path endpoints for the new CesiumJS frontend
@app.get("/bases")
async def get_bases_short():
    for fname in ["bases.json", "military_bases.json"]:
        path = DATA_DIR / fname
        if path.exists():
            with open(path) as f:
                return json.load(f)
    return []

@app.get("/conflicts")
async def get_conflicts_short():
    return _dm_load_json("conflicts.json")

@app.get("/nuclear")
async def get_nuclear_short():
    return _dm_load_json("nuclear_sites.json")

@app.get("/api/v1/map/bases/search")
async def search_bases(q: str = "", country: str = "", type: str = "", status: str = ""):
    path = DATA_DIR / "military_bases.json"
    if not path.exists():
        return []
    with open(path) as f:
        bases = json.load(f)
    results = []
    q_lower = q.lower()
    for b in bases:
        if q_lower and q_lower not in b.get("name","").lower() and q_lower not in b.get("description","").lower() and q_lower not in b.get("country","").lower():
            continue
        if country and b.get("country","") != country.upper():
            continue
        if type and b.get("type","") != type:
            continue
        if status and b.get("status","") != status:
            continue
        results.append(b)
    return results

@app.get("/api/v1/map/conflicts")
async def get_conflicts():
    return _dm_load_json("conflicts.json")

@app.get("/api/v1/map/bri")
async def get_bri():
    return _dm_load_json("bri_routes.json")

@app.get("/api/v1/map/construction")
async def get_construction():
    # Filter bases under construction
    path = DATA_DIR / "military_bases.json"
    if path.exists():
        with open(path) as f:
            all_bases = json.load(f)
        return [b for b in all_bases if b.get("status") == "construction"]
    return _dm_load_json("construction.json")

@app.get("/api/v1/map/chokepoints")
async def get_chokepoints():
    return _dm_load_json("chokepoints.json")

@app.get("/api/v1/map/ports")
async def get_ports():
    return _dm_load_json("ports.json")

@app.get("/api/v1/map/global_routes")
async def get_routes():
    return _dm_load_json("global_routes.json")

@app.get("/api/v1/map/lanes")
async def get_lanes():
    return _dm_load_json("lanes.json")

# ─── Nuclear sites ──────────────────────────────────────────────────────────
@app.get("/api/v1/nuclear/sites")
async def get_nuclear():
    # Try dedicated nuclear_sites.json first
    nuke_path = DATA_DIR / "nuclear_sites.json"
    if nuke_path.exists():
        return _dm_load_json("nuclear_sites.json")
    # Fallback: filter from bases
    for fname in ["bases.json", "military_bases.json"]:
        path = DATA_DIR / fname
        if path.exists():
            with open(path) as f:
                all_bases = json.load(f)
            return [b for b in all_bases if b.get("type") in ("nuclear", "missile_test") or b.get("subtype") in ("nuclear", "missile")]
    return []

# ─── War/Conflict status ─────────────────────────────────────────────────────
@app.get("/api/v1/conflicts/wars")
async def get_war_status():
    return osint_worker.get_war_status()

@app.get("/api/v1/conflicts/active")
async def get_active_conflicts():
    war_status = osint_worker.get_war_status()
    return {
        "critical": {k:v for k,v in war_status.items() if v.get("intensity") == "critical"},
        "high": {k:v for k,v in war_status.items() if v.get("intensity") == "high"},
        "elevated": {k:v for k,v in war_status.items() if v.get("intensity") == "elevated"},
        "medium": {k:v for k,v in war_status.items() if v.get("intensity") == "medium"},
    }

# ─── Surveillance ───────────────────────────────────────────────────────────
@app.get("/api/v1/surveillance/index")
async def get_surveillance():
    return osint_worker.get_all_surveillance()

@app.get("/api/v1/surveillance/{country_code}")
async def get_country_surveillance(country_code: str):
    return osint_worker.get_surveillance_index(country_code)

# ─── OSINT domain endpoints ─────────────────────────────────────────────────
@app.get("/api/v1/osint/{domain}")
async def get_osint_domain(domain: str):
    allowed = ["military_bases","air_bases","nuclear_sites","conflicts","construction",
               "research_stations","surveillance","missile_sites","naval_bases","wars_active"]
    if domain not in allowed:
        return JSONResponse(status_code=400, content={"error": f"Unknown domain. Allowed: {allowed}"})
    return osint_worker.get_domain_data(domain)

@app.post("/api/v1/osint/refresh")
async def trigger_osint_refresh(background_tasks: BackgroundTasks):
    background_tasks.add_task(osint_worker.refresh_all_domains,
                              ai if cfg.get("mode") != "no_ai" else None)
    return {"status": "refresh queued", "domains": list(osint_worker.DOMAIN_RSS_SOURCES.keys())}

@app.post("/api/v1/osint/refresh/{domain}")
async def trigger_domain_refresh(domain: str, background_tasks: BackgroundTasks):
    async def refresh_single():
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                sources = osint_worker.DOMAIN_RSS_SOURCES.get(domain, [])
                items = []
                for url in sources:
                    r = await osint_worker._fetch_rss(session, url, domain)
                    items.extend(r)
                osint_worker._cache_set(f"osint_{domain}", items, 3600)
                logger.info(f"[OSINT] Single domain refresh {domain}: {len(items)} items")
        except Exception as e:
            logger.error(f"[OSINT] Refresh {domain} failed: {e}")
    background_tasks.add_task(refresh_single)
    return {"status": "queued", "domain": domain}

# ─── Natural language search → map highlighting ──────────────────────────────
@app.get("/api/v1/search/bases")
async def nlp_base_search(q: str):
    """NLP search: 'list all military bases in India' → returns matching bases to highlight"""
    path = DATA_DIR / "military_bases.json"
    if not path.exists():
        return {"results": [], "query": q}
    with open(path) as f:
        bases = json.load(f)

    q_lower = q.lower()
    # Country name → code mapping
    COUNTRY_NAMES = {
        "india": "IN", "china": "CN", "pakistan": "PK", "russia": "RU",
        "usa": "US", "united states": "US", "america": "US",
        "uk": "GB", "britain": "GB", "israel": "IL", "iran": "IR",
        "north korea": "KP", "south korea": "KR", "japan": "JP",
        "france": "FR", "germany": "DE", "turkey": "TR", "saudi": "SA",
        "australia": "AU", "uae": "AE",
    }
    # Subtype keywords
    SUBTYPE_KWORDS = {
        "air": "airbase", "airbase": "airbase", "air force": "airbase",
        "naval": "naval", "navy": "naval", "submarine": "submarine",
        "nuclear": "nuclear", "missile": "missile", "army": "army",
        "space": "space", "intel": "intel",
    }

    filter_country = None
    filter_subtype = None
    filter_status = None

    for name, code in COUNTRY_NAMES.items():
        if name in q_lower:
            filter_country = code
            break

    for kw, subtype in SUBTYPE_KWORDS.items():
        if kw in q_lower:
            filter_subtype = subtype
            break

    if "construction" in q_lower or "under construction" in q_lower or "building" in q_lower:
        filter_status = "construction"
    elif "inactive" in q_lower or "abandoned" in q_lower or "closed" in q_lower:
        filter_status = "inactive"
    elif "active" in q_lower:
        filter_status = "active"

    results = []
    for b in bases:
        if filter_country and b.get("country") != filter_country:
            continue
        if filter_subtype and b.get("subtype") != filter_subtype:
            continue
        if filter_status and b.get("status") != filter_status:
            continue
        results.append(b)

    return {
        "query": q,
        "filter_country": filter_country,
        "filter_subtype": filter_subtype,
        "filter_status": filter_status,
        "count": len(results),
        "results": results
    }

# ─── Country intel ──────────────────────────────────────────────────────────
@app.get("/api/v1/country/{iso2}")
async def country_intel(iso2: str):
    code = iso2.upper()
    surveillance = osint_worker.get_surveillance_index(code)
    war = osint_worker.get_war_status()
    conflict_info = war.get(code, {"status": "stable", "intensity": "low"})

    path = DATA_DIR / "military_bases.json"
    bases_count = 0
    if path.exists():
        with open(path) as f:
            all_b = json.load(f)
        bases_count = sum(1 for b in all_b if b.get("country") == code)

    return {
        "iso2": code,
        "surveillance": surveillance,
        "conflict": conflict_info,
        "military_bases_count": bases_count,
        "instability_score": _calc_instability(code, conflict_info, surveillance),
    }

def _calc_instability(code, conflict, surveillance) -> int:
    score = 0
    intensity_map = {"critical": 50, "high": 35, "elevated": 20, "medium": 15, "low": 5}
    score += intensity_map.get(conflict.get("intensity", "low"), 5)
    score += int(surveillance.get("score", 30) * 0.3)
    return min(100, score)

# ─── Satellite TLE ─────────────────────────────────────────────────────────
_tle_cache: dict = {}
_tle_ts: float = 0
TLE_TTL = 7200

CELESTRAK_GROUPS = ["military", "resource", "analyst", "stations"]

SAT_COUNTRY_PATTERNS = {
    "CN": ["YAOGAN", "GAOFEN", "JILIN", "FENGYUN", "TIANHUI", "SJ-", "SHIJIAN", "ZIYUAN", "HAIYANG", "LUOJIA", "BEIDOU"],
    "RU": ["COSMOS 2", "RESURS-", "BARS-M", "KONDOR", "PERSONA", "KANOPUS", "LOTOS-S", "PARUS", "TSELINA", "GLONASS"],
    "IL": ["OFEK", "TECSAR", "OFEQ", "EROS"],
    "IN": ["CARTOSAT", "RISAT", "RESOURCESAT", "OCEANSAT", "EMISAT", "MICROSAT", "GSAT"],
    "US": ["WORLDVIEW", "SKYSAT", "CAPELLA", "HAWK", "GEOEYE", "QUICKBIRD", "IKONOS", "BLACKSKY", "USA-", "NROL-", "GPS", "STARLINK", "IRIDIUM", "SPIRE", "FLOCK", "DOVE"],
    "EU": ["SENTINEL-", "METOP-", "MSG-", "ENVISAT", "ERS-", "PROBA", "GALILEO", "ONEWEB"],
    "JP": ["ALOS", "IGS", "DAICHI", "JERS", "QZS"],
    "KR": ["KOMPSAT", "ARIRANG", "STSAT"],
    "IT": ["COSMO-SKYMED"],
    "DE": ["TERRASAR", "TANDEM-X", "SAR-LUPE", "RAPIDEYE", "ICEYE"],
    "FR": ["HELIOS", "PLEIADES", "SPOT", "SYRACUSE"],
}

SAT_TYPE_PATTERNS = {
    "SAR": ["YAOGAN-", "COSMO-SKYMED", "TERRASAR", "TANDEM-X", "PAZ", "SAR-LUPE", "ICEYE", "CAPELLA-", "SENTINEL-1", "RISAT", "KONDOR", "TECSAR"],
    "OPTICAL": ["WORLDVIEW", "SKYSAT", "GAOFEN", "JILIN-", "PLEIADES", "SPOT", "KOMPSAT", "CARTOSAT", "GEOEYE", "BLACKSKY", "SENTINEL-2", "FLOCK", "DOVE"],
    "SIGINT": ["YAOGAN-30", "LOTOS-S", "BARS-M", "LACROSSE", "ONYX", "TSELINA", "HAWK"],
    "MILITARY": ["COSMOS 2", "USA-", "HELIOS", "IGS", "PERSONA", "NROL-", "PARUS", "SYRACUSE"],
    "EARTH_OBS": ["SENTINEL-3", "SENTINEL-5", "METOP", "RESURS-P", "KANOPUS", "RESOURCESAT", "OCEANSAT", "FENGYUN", "HAIYANG"],
    "COMMS": ["STARLINK", "ONEWEB", "IRIDIUM", "INTELSAT", "SES", "GLOBALSTAR", "GSAT"],
    "NAV": ["GPS", "GLONASS", "BEIDOU", "GALILEO", "QZS"],
    "WEATHER": ["GOES", "NOAA", "CLOUDSAT", "CALIPSO", "SPIRE"]
}

def _sat_classify(name: str) -> tuple[str, str]:
    n = name.upper()
    country = "OTHER"
    for cc, pats in SAT_COUNTRY_PATTERNS.items():
        if any(p in n for p in pats):
            country = cc
            break
    sat_type = "OTHER"
    for t, pats in SAT_TYPE_PATTERNS.items():
        if any(p in n for p in pats):
            sat_type = t
            break
    return country, sat_type

def _parse_tle_block(text: str) -> list[dict]:
    sats = []
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    i = 0
    while i < len(lines):
        if lines[i].startswith("1 ") and i + 1 < len(lines) and lines[i+1].startswith("2 "):
            sats.append({"name": f"SAT-{lines[i][2:7]}", "line1": lines[i], "line2": lines[i+1]})
            i += 2
        elif not lines[i].startswith("1 ") and not lines[i].startswith("2 ") and i + 2 < len(lines) and lines[i+1].startswith("1 ") and lines[i+2].startswith("2 "):
            sats.append({"name": lines[i], "line1": lines[i+1], "line2": lines[i+2]})
            i += 3
        else:
            i += 1
    return sats

async def _fetch_celestrak():
    global _tle_cache, _tle_ts
    if time.time() - _tle_ts < TLE_TTL and _tle_cache:
        return _tle_cache
    sats = []
    seen = set()
    # Celestrak GP data URLs — multiple fallback endpoints
    URLS = [
        "https://celestrak.org/SOCRATES/query.php?CODE=ALL&ALT=0&DIR=1",  # may not work
        "https://celestrak.org/pub/TLE/active.txt",
        "https://celestrak.org/SATCAT/tle/active.txt",
        "https://celestrak.org/SATCAT/tle/military.txt",
        "https://celestrak.org/SATCAT/tle/stations.txt",
    ]
    GP_URLS = [
        "https://celestrak.org/NORAD/elements/stations.txt",
        "https://celestrak.org/NORAD/elements/science.txt",
        "https://celestrak.org/NORAD/elements/resource.txt",
        "https://celestrak.org/NORAD/elements/starlink.txt",
        "https://celestrak.org/NORAD/elements/weather.txt",
        "https://celestrak.org/NORAD/elements/geo.txt",
        "https://celestrak.org/NORAD/elements/amateur.txt",
    ]
    try:
        import httpx
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}) as client:
            for url in GP_URLS:
                try:
                    r = await client.get(url)
                    if r.status_code == 200 and len(r.text) > 100:
                        for s in _parse_tle_block(r.text):
                            norad = s["line1"][2:7].strip()
                            if norad not in seen:
                                seen.add(norad)
                                country, sat_type = _sat_classify(s["name"])
                                sats.append({**s, "norad_id": norad, "country": country, "type": sat_type})
                        if len(sats) > 10000:
                            break  # Soft limit to prevent unmanageable frontend load
                except Exception as e:
                    logger.debug(f"CelesTrak {url} failed: {e}")
    except Exception as e:
        logger.warning(f"Satellite fetch failed: {e}")
    if sats:
        _tle_cache = sats
        _tle_ts = time.time()
    elif _tle_cache:
        pass  # Keep stale cache
    return _tle_cache or sats

@app.get("/api/v1/satellites/tle")
async def get_satellite_tles(country: str = "", type: str = ""):
    sats = await _fetch_celestrak()
    if country:
        sats = [s for s in sats if s.get("country") == country.upper()]
    if type:
        sats = [s for s in sats if s.get("type") == type.upper()]
    return sats

@app.get("/api/v1/satellites/stats")
async def get_satellite_stats():
    sats = _tle_cache or []
    by_country = {}
    by_type = {}
    for s in sats:
        cc = s.get("country", "OTHER")
        t = s.get("type", "OTHER")
        by_country[cc] = by_country.get(cc, 0) + 1
        by_type[t] = by_type.get(t, 0) + 1
    return {
        "total": len(sats),
        "by_country": by_country,
        "by_type": by_type,
        "cache_age_seconds": int(time.time() - _tle_ts) if _tle_ts else None,
    }

# ─── AI chat ────────────────────────────────────────────────────────────────
@app.post("/api/v1/ai/chat")
async def ai_chat(body: dict):
    msg = body.get("message", "")
    context = body.get("context", "")
    # Collect streaming response into a single string
    import json as _json
    parts = []
    try:
        ctx_dict = {"raw": context} if isinstance(context, str) and context else context or {}
        messages = [{"role": "user", "content": msg}]
        async for chunk in ai.chat_stream(messages, ctx_dict):
            # chunks are SSE strings: data: {...}
            if chunk.startswith("data:"):
                try:
                    ev = _json.loads(chunk[5:].strip())
                    if ev.get("type") in ("content", "thinking_chunk"):
                        parts.append(ev.get("content", ""))
                except Exception:
                    pass
    except Exception as e:
        parts = [f"AI error: {e}"]
    response = "".join(parts) or "AI is not configured or unavailable."
    return {"response": response, "mode": cfg.get("mode", "no_ai")}

@app.get("/api/v1/ai/status")
async def ai_status():
    return {"mode": cfg.get("mode"), "model": cfg.get("model",""), "ready": True}

# ─── News ───────────────────────────────────────────────────────────────────
@app.get("/api/v1/news/feed")
async def news_feed():
    items = osint_worker.get_domain_data("conflicts")
    items += osint_worker.get_domain_data("military_bases")
    return {"items": items[:50], "count": len(items)}

@app.get("/api/v1/news/breaking")
async def breaking_news():
    items = osint_worker.get_domain_data("wars_active")
    return {"items": items[:20]}

@app.get("/api/v1/data/stats")
async def data_stats():
    path = DATA_DIR / "military_bases.json"
    base_count = 0
    if path.exists():
        with open(path) as f:
            base_count = len(json.load(f))
    return {
        "military_bases": base_count,
        "conflicts": len(_dm_load_json("conflicts.json")),
        "war_countries": len(osint_worker.get_war_status()),
        "surveillance_countries": len(osint_worker.get_all_surveillance()),
        "osint_domains": len(osint_worker.DOMAIN_RSS_SOURCES),
    }

@app.get("/api/v1/countries/all")
async def all_countries():
    war = osint_worker.get_war_status()
    surv = osint_worker.get_all_surveillance()
    combined = {}
    for cc in set(list(war.keys()) + list(surv.keys())):
        combined[cc] = {
            "conflict": war.get(cc, {"status": "stable"}),
            "surveillance": surv.get(cc, surv["DEFAULT"]),
        }
    return combined

# ─── WebSocket ───────────────────────────────────────────────────────────────
@app.websocket("/ws/news")
async def ws_news(ws: WebSocket):
    await ws.accept()
    ws_clients.append(ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        ws_clients.remove(ws)

@app.websocket("/ws/intel")
async def ws_intel(ws: WebSocket):
    await ws.accept()
    try:
        while True:
            war_status = osint_worker.get_war_status()
            critical = [k for k, v in war_status.items() if v.get("intensity") == "critical"]
            await ws.send_json({"type": "war_update", "critical_countries": critical, "ts": datetime.utcnow().isoformat()})
            await asyncio.sleep(30)
    except WebSocketDisconnect:
        pass

# ─── Cyber Attack Endpoints ──────────────────────────────────────────────────
@app.get("/api/v1/cyber/attacks")
async def get_cyber_attacks(limit: int = 50):
    return {"attacks": cyber_engine.get_recent_attacks(limit), "ts": datetime.utcnow().isoformat()}

@app.get("/api/v1/cyber/stats")
async def get_cyber_stats():
    return cyber_engine.get_stats()

@app.websocket("/ws/cyber")
async def ws_cyber(ws: WebSocket):
    await ws.accept()
    cyber_engine.register_ws(ws)
    try:
        await ws.send_json({"type": "history", "data": cyber_engine.get_recent_attacks(30)})
        while True:
            try:
                await asyncio.sleep(30)
                await ws.send_json({"type": "ping"})
            except (asyncio.CancelledError, WebSocketDisconnect):
                break
            except Exception:
                break
    except (asyncio.CancelledError, WebSocketDisconnect, Exception):
        pass
    finally:
        cyber_engine.unregister_ws(ws)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
