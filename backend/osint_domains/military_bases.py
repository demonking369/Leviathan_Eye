"""
OSINT Domain: Military Bases
Parallel query module. Fetches military base data from multiple open sources.
No AI required for data fetching. AI only called if JSON parsing fails.
"""
import asyncio, json, logging
from typing import List, Dict, Any
import httpx

logger = logging.getLogger("osint.military_bases")

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

OSM_FILTERS = [
    "military=airfield",
    "military=base",
    "military=naval_base",
    "military=barracks",
    "military=missile_site",
    "military=training_area",
    "military=bunker",
    "military=checkpoint",
    "military=range",
    "landuse=military",
]

async def fetch_osm_military(client: httpx.AsyncClient, filter_tag: str) -> List[Dict]:
    query = f"""
    [out:json][timeout:30];
    (
      node[{filter_tag}][name];
      way[{filter_tag}][name];
      relation[{filter_tag}][name];
    );
    out center 500;
    """
    try:
        r = await client.post(OVERPASS_URL, data={"data": query}, timeout=40)
        data = r.json()
        results = []
        for el in data.get("elements", []):
            tags = el.get("tags", {})
            name = tags.get("name") or tags.get("name:en", "")
            if not name or len(name) < 3:
                continue
            lat = el.get("lat") or el.get("center", {}).get("lat")
            lng = el.get("lon") or el.get("center", {}).get("lon")
            if not lat or not lng:
                continue
            results.append({
                "name": name,
                "lat": round(float(lat), 4),
                "lng": round(float(lng), 4),
                "type": tags.get("military", filter_tag.split("=")[1]),
                "nation": tags.get("operator:country", "??").lower()[:2],
                "status": "active",
                "source": "OpenStreetMap/OSINT",
                "confidence": "medium",
                "approximate": True,
                "notes": f"OSM. Operator: {tags.get('operator','unknown')}. Tag: {filter_tag}",
                "tags": [tags.get("military", "base")],
            })
        return results
    except Exception as e:
        logger.warning(f"OSM {filter_tag} failed: {e}")
        return []

async def run_parallel_queries() -> List[Dict]:
    all_results = []
    async with httpx.AsyncClient() as client:
        tasks = [fetch_osm_military(client, f) for f in OSM_FILTERS]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for r in results:
            if isinstance(r, list):
                all_results.extend(r)

    # Deduplicate by name + proximity
    deduped = []
    for item in all_results:
        is_dup = any(
            abs(item["lat"] - e["lat"]) < 0.05 and
            abs(item["lng"] - e["lng"]) < 0.05
            for e in deduped
        )
        if not is_dup:
            deduped.append(item)

    logger.info(f"Military bases: {len(all_results)} raw → {len(deduped)} deduped")
    return deduped
