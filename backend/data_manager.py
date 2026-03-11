import json
import logging
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

log = logging.getLogger("Leviathan_Eye.data")

DATA_DIR = Path(__file__).parent.parent / "data"

VALID_TYPES = {
    "bases":          "military_bases",
    "conflicts":      "conflict_zones",
    "construction":   "construction_sites",
    "bri_routes":     "bri_routes",
    "chokepoints":    "chokepoints",
    "ports":          "strategic_ports",
    "lanes":          "shipping_lanes",
}

_cache: Dict[str, Dict] = {}


def _path(store: str) -> Path:
    return DATA_DIR / f"{store}.json"


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load(store: str) -> Dict:
    if store in _cache:
        return _cache[store]
    p = _path(store)
    if not p.exists():
        raise FileNotFoundError(f"Data file not found: {p}")
    with open(p) as f:
        doc = json.load(f)
    _cache[store] = doc
    return doc


def _flush(store: str) -> None:
    doc = _cache.get(store)
    if not doc:
        return
    p = _path(store)
    backup = p.with_suffix(".json.bak")
    if p.exists():
        shutil.copy2(p, backup)
    doc["last_updated"] = _now()
    with open(p, "w") as f:
        json.dump(doc, f, indent=2)
    log.info(f"[DataManager] Saved {store}.json ({len(doc['data'])} records)")


class DataManager:
    def get(self, store: str) -> List[Dict]:
        return _load(store)["data"]

    def get_doc(self, store: str) -> Dict:
        return _load(store)

    def filter(self, store: str, **kwargs) -> List[Dict]:
        items = self.get(store)
        for key, val in kwargs.items():
            items = [i for i in items if str(i.get(key, "")).lower() == str(val).lower()]
        return items

    def find(self, store: str, id: str) -> Optional[Dict]:
        return next((i for i in self.get(store) if i.get("id") == id), None)

    def upsert(self, store: str, record: Dict) -> Dict:
        if "id" not in record:
            raise ValueError("Record must have an 'id' field")
        doc = _load(store)
        idx = next((i for i, x in enumerate(doc["data"]) if x.get("id") == record["id"]), None)
        record["last_updated"] = _now()
        if idx is not None:
            doc["data"][idx] = record
            log.info(f"[DataManager] Updated {store}/{record['id']}")
        else:
            doc["data"].append(record)
            log.info(f"[DataManager] Inserted {store}/{record['id']}")
        _flush(store)
        return record

    def remove(self, store: str, id: str) -> bool:
        doc = _load(store)
        before = len(doc["data"])
        doc["data"] = [x for x in doc["data"] if x.get("id") != id]
        if len(doc["data"]) < before:
            _flush(store)
            log.info(f"[DataManager] Removed {store}/{id}")
            return True
        return False

    def save(self, store: str) -> None:
        _flush(store)

    def invalidate(self, store: str) -> None:
        _cache.pop(store, None)

    def stats(self) -> Dict:
        out = {}
        for s in VALID_TYPES:
            try:
                doc = _load(s)
                out[s] = {"count": len(doc["data"]), "last_updated": doc.get("last_updated")}
            except Exception as e:
                out[s] = {"error": str(e)}
        return out

    def apply_ai_patch(self, patch: Dict) -> Dict:
        results = {"upserted": [], "removed": [], "errors": []}
        store = patch.get("store")
        if store not in VALID_TYPES:
            results["errors"].append(f"Unknown store: {store}")
            return results
        for record in patch.get("upsert", []):
            try:
                self.upsert(store, record)
                results["upserted"].append(record["id"])
            except Exception as e:
                results["errors"].append(f"upsert {record.get('id')}: {e}")
        for rid in patch.get("remove", []):
            try:
                ok = self.remove(store, rid)
                if ok:
                    results["removed"].append(rid)
            except Exception as e:
                results["errors"].append(f"remove {rid}: {e}")
        return results


dm = DataManager()
