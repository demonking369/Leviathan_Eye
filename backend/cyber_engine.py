"""Leviathan_Eye — Cyber Attack Simulation Engine
Simulates realistic cyber threat data: attack types, source/target countries,
IPs, ports, severity. Streams via WebSocket to frontend.
"""
import asyncio, random, time, math
from typing import Optional

# ── Country database (weighted by real-world attack volumes) ──────────────────
COUNTRIES = [
    {"code": "CN", "name": "China",          "lat": 35,   "lng": 105,   "w": 100},
    {"code": "RU", "name": "Russia",         "lat": 60,   "lng": 100,   "w": 90},
    {"code": "US", "name": "United States",  "lat": 38,   "lng": -97,   "w": 80},
    {"code": "KP", "name": "North Korea",    "lat": 40,   "lng": 127,   "w": 65},
    {"code": "IR", "name": "Iran",           "lat": 32,   "lng": 53,    "w": 60},
    {"code": "IN", "name": "India",          "lat": 20,   "lng": 77,    "w": 45},
    {"code": "BR", "name": "Brazil",         "lat": -10,  "lng": -55,   "w": 38},
    {"code": "UA", "name": "Ukraine",        "lat": 48,   "lng": 31,    "w": 35},
    {"code": "DE", "name": "Germany",        "lat": 51,   "lng": 9,     "w": 35},
    {"code": "GB", "name": "United Kingdom", "lat": 55,   "lng": -3,    "w": 30},
    {"code": "NL", "name": "Netherlands",    "lat": 52,   "lng": 5,     "w": 30},
    {"code": "VN", "name": "Vietnam",        "lat": 14,   "lng": 108,   "w": 28},
    {"code": "PK", "name": "Pakistan",       "lat": 30,   "lng": 70,    "w": 25},
    {"code": "ID", "name": "Indonesia",      "lat": -5,   "lng": 120,   "w": 22},
    {"code": "FR", "name": "France",         "lat": 46,   "lng": 2,     "w": 22},
    {"code": "JP", "name": "Japan",          "lat": 36,   "lng": 138,   "w": 20},
    {"code": "KR", "name": "South Korea",    "lat": 36,   "lng": 128,   "w": 20},
    {"code": "TR", "name": "Turkey",         "lat": 39,   "lng": 35,    "w": 18},
    {"code": "TW", "name": "Taiwan",         "lat": 23.5, "lng": 121,   "w": 18},
    {"code": "SG", "name": "Singapore",      "lat": 1.3,  "lng": 103.8, "w": 16},
    {"code": "AU", "name": "Australia",      "lat": -25,  "lng": 133,   "w": 15},
    {"code": "CA", "name": "Canada",         "lat": 60,   "lng": -95,   "w": 15},
    {"code": "IL", "name": "Israel",         "lat": 31,   "lng": 34,    "w": 14},
    {"code": "SA", "name": "Saudi Arabia",   "lat": 25,   "lng": 45,    "w": 12},
    {"code": "MX", "name": "Mexico",         "lat": 23,   "lng": -102,  "w": 12},
    {"code": "PL", "name": "Poland",         "lat": 52,   "lng": 20,    "w": 10},
    {"code": "RO", "name": "Romania",        "lat": 46,   "lng": 25,    "w": 10},
    {"code": "NG", "name": "Nigeria",        "lat": 10,   "lng": 8,     "w": 9},
    {"code": "ZA", "name": "South Africa",   "lat": -30,  "lng": 25,    "w": 9},
    {"code": "AR", "name": "Argentina",      "lat": -34,  "lng": -64,   "w": 8},
    {"code": "EG", "name": "Egypt",          "lat": 26,   "lng": 30,    "w": 8},
    {"code": "IT", "name": "Italy",          "lat": 42,   "lng": 12,    "w": 8},
    {"code": "ES", "name": "Spain",          "lat": 40,   "lng": -4,    "w": 7},
    {"code": "SE", "name": "Sweden",         "lat": 60,   "lng": 15,    "w": 7},
    {"code": "CH", "name": "Switzerland",    "lat": 47,   "lng": 8,     "w": 7},
    {"code": "BE", "name": "Belgium",        "lat": 50,   "lng": 4,     "w": 6},
    {"code": "CZ", "name": "Czechia",        "lat": 50,   "lng": 15,    "w": 5},
    {"code": "HU", "name": "Hungary",        "lat": 47,   "lng": 20,    "w": 5},
    {"code": "UA", "name": "Ukraine",        "lat": 48,   "lng": 31,    "w": 35},
    {"code": "BY", "name": "Belarus",        "lat": 53,   "lng": 28,    "w": 14},
]

# ── Attack type definitions ──────────────────────────────────────────────────
ATTACK_TYPES = [
    {"name": "DDoS",          "color": "#ff3333", "port": 80,   "severity": "critical"},
    {"name": "SQL Injection", "color": "#33ff88", "port": 3306, "severity": "high"},
    {"name": "SSH Brute",     "color": "#4488ff", "port": 22,   "severity": "medium"},
    {"name": "Malware",       "color": "#ff33ff", "port": 443,  "severity": "critical"},
    {"name": "Phishing",      "color": "#ffff33", "port": 25,   "severity": "medium"},
    {"name": "Ransomware",    "color": "#ff9933", "port": 445,  "severity": "critical"},
    {"name": "Botnet",        "color": "#33ffff", "port": 8080, "severity": "high"},
    {"name": "Exploit",       "color": "#ff3399", "port": 80,   "severity": "high"},
    {"name": "Zero-Day",      "color": "#ff0066", "port": 443,  "severity": "critical"},
    {"name": "Port Scan",     "color": "#99ff33", "port": 0,    "severity": "low"},
    {"name": "XSS",           "color": "#ff6688", "port": 443,  "severity": "medium"},
    {"name": "MITM",          "color": "#ffaa44", "port": 8443, "severity": "high"},
]

TOTAL_WEIGHT = sum(c["w"] for c in COUNTRIES)
_attack_id  = 0
_attacks    = []   # ring buffer, max 200

def _weighted_country():
    r = random.random() * TOTAL_WEIGHT
    for c in COUNTRIES:
        if r < c["w"]:
            return c
        r -= c["w"]
    return COUNTRIES[0]

def _jitter(val, spread=3.0):
    return val + (random.random() * 2 - 1) * spread

def _random_ip():
    return f"{random.randint(1,254)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"

def generate_attack() -> dict:
    global _attack_id
    _attack_id += 1

    src = _weighted_country()
    tgt = _weighted_country()
    # Ensure different countries
    while tgt["code"] == src["code"]:
        tgt = _weighted_country()

    atk = random.choice(ATTACK_TYPES)

    return {
        "id":            f"CA{_attack_id:06d}",
        "ts":            int(time.time() * 1000),
        "src":           src["name"],
        "src_code":      src["code"],
        "src_lat":       _jitter(src["lat"]),
        "src_lng":       _jitter(src["lng"]),
        "tgt":           tgt["name"],
        "tgt_code":      tgt["code"],
        "tgt_lat":       _jitter(tgt["lat"]),
        "tgt_lng":       _jitter(tgt["lng"]),
        "type":          atk["name"],
        "color":         atk["color"],
        "port":          atk["port"],
        "severity":      atk["severity"],
        "ip":            _random_ip(),
        "payload_kb":    round(random.uniform(0.1, 9999), 1),
    }

# ── In-memory ring buffer ─────────────────────────────────────────────────────
def record_attack(atk: dict):
    _attacks.append(atk)
    if len(_attacks) > 200:
        _attacks.pop(0)

def get_recent_attacks(limit=50) -> list:
    return list(reversed(_attacks[-limit:]))

def get_stats() -> dict:
    if not _attacks:
        return {"top_attackers": [], "top_targets": [], "top_types": [], "total": 0}

    src_counts: dict[str, int] = {}
    tgt_counts: dict[str, int] = {}
    type_counts: dict[str, dict] = {}

    for a in _attacks:
        src_counts[a["src"]] = src_counts.get(a["src"], 0) + 1
        tgt_counts[a["tgt"]] = tgt_counts.get(a["tgt"], 0) + 1
        tc = type_counts.setdefault(a["type"], {"count": 0, "color": a["color"]})
        tc["count"] += 1

    top_src = sorted(src_counts.items(), key=lambda x: -x[1])[:5]
    top_tgt = sorted(tgt_counts.items(), key=lambda x: -x[1])[:5]
    top_typ = sorted(type_counts.items(), key=lambda x: -x[1]["count"])[:6]

    return {
        "total":         len(_attacks),
        "top_attackers": [{"name": k, "count": v} for k, v in top_src],
        "top_targets":   [{"name": k, "count": v} for k, v in top_tgt],
        "top_types":     [{"name": k, "count": v["count"], "color": v["color"]} for k, v in top_typ],
    }

# ── Background simulation loop ────────────────────────────────────────────────
_sim_task: Optional[asyncio.Task] = None
_ws_clients: list = []   # WebSocket objects registered by main.py

def register_ws(ws):
    _ws_clients.append(ws)

def unregister_ws(ws):
    if ws in _ws_clients:
        _ws_clients.remove(ws)

async def _sim_loop():
    while True:
        atk = generate_attack()
        record_attack(atk)
        # Broadcast to all connected cyber WS clients
        dead = []
        for ws in list(_ws_clients):
            try:
                await ws.send_json({"type": "attack", "data": atk})
            except Exception:
                dead.append(ws)
        for ws in dead:
            unregister_ws(ws)
        # Random interval 80ms – 900ms (realistic burst feel)
        await asyncio.sleep(random.uniform(0.08, 0.9))

def start_cyber_engine():
    global _sim_task
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    _sim_task = loop.create_task(_sim_loop())

def stop_cyber_engine():
    global _sim_task
    if _sim_task:
        _sim_task.cancel()
        _sim_task = None
