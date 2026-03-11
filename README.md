# Leviathan_Eye — Global Intelligence Dashboard

A fully local, offline-capable military intelligence dashboard with a real-time 3D globe,
live satellite tracking, conflict zone visualization, cyber threat feeds, AI-powered analysis,
**live news/webcam streaming**, **deep OSINT internet research on click**, and **country-level intelligence panels**.

---

## Feature Highlights (Latest)

### 🎬 Live Dashboard (Bottom Bar)
Click **"▲ LIVE DASHBOARD"** to open a tiled, three-column panel:

| Column | Content |
|---|---|
| **LIVE NEWS** | 24/7 YouTube live streams from 7 networks: Al Jazeera, SkyNews, France 24, DW News, CNN, WION. Channel-based URLs (`live_stream?channel=`) auto-resolve to the current broadcast. |
| **LIVE WEBCAMS** | 2×2 grid, switchable by region: Hotspots, Europe, Americas, Asia, Space. Each tile is a live channel embed. |
| **AI INSIGHTS** | Scrollable sidebar with: World Brief (from backend `/api/v1/news/feed`), AI Strategic Posture (from conflict data), Live Intelligence, Country Instability Index, Strategic Risk Overview, Regional Hotspots, Infrastructure Cascade. |

### 🔍 Deep OSINT Base Research
When clicking any military base, the detail panel performs a **4-source deep internet research pipeline**:

1. **Wikipedia REST API** — Summary + full article with multiple sections
2. **Wikipedia MediaWiki API** — Full plaintext extract broken into section headings (History, Operations, Units, etc.)
3. **Wikimedia Commons** — Up to 5 actual photographs of the base, displayed as a scrollable image gallery
4. **Wikidata Structured Data** — Inception date, ICAO code, and other machine-readable properties
5. **GeoNames** — Nearby locations within 50km radius
6. **Esri ArcGIS** — High-resolution satellite imagery snippet centered on coordinates
7. **External Links** — Google Earth 3D link + Google Maps link

### 🌐 Country Intelligence Panel
Clicking **empty land** on the globe reverse-geocodes the position and slides open a full-width intelligence dossier:

- **Instability Index** (0–100) — Mathematically derived from active conflicts, cyber attacks targeting the country, and military facility density
- **Active Signals** — Badges for conflicts, cyber hits, military facilities
- **Military Activity** — Air bases, naval bases, army/ground facilities, total
- **Top News** — Wikipedia article extract + thumbnail for the country
- **Economic Indicators** — Region, capital, population, area, currency, languages (from REST Countries API)

---

## Installation Guide

### Prerequisites
- Windows OS (for `.bat` runner scripts)
- Python 3.10+ installed and added to your system PATH
- Internet connection (for live OSINT, Overpass API, and Satellite tracking)

### Setup Steps
1. Clone the repository: 
   ```bash
   git clone https://github.com/demonking369/Leviathan_Eye.git
   ```
2. Navigate into the project directory: 
   ```bash
   cd Leviathan_Eye
   ```
3. Install the required Python backend dependencies: 
   ```bash
   pip install -r backend/requirements.txt
   ```

## Usage Guide

1. Double-click the `START.bat` file in the root directory.
2. The ASCII launcher will open. Select your AI mode when prompted (or press Enter for auto-detect).
3. The dashboard will automatically launch in your default web browser at `http://localhost:8000`.
4. **Important**: The backend terminal window must remain open while using the dashboard—it processes live data, WebSocket streams, and OSINT scraping.
5. Use the left sidebar to toggle map layers (e.g., Air Bases, Live Satellites). Note that layers load data purely on-demand to save resources.
6. Click on any physical base or point of interest on the globe to open the Deep OSINT panel for real-time intelligence gathering. Click on empty country land to open the overall Country Intelligence Panel.
7. Click the **"▲ LIVE DASHBOARD"** button at the bottom of the screen to view live news streams, webcams, and AI-generated geopolitical insights.

---

## Architecture Overview

```
Leviathan_Eye/
├── START.bat                    Pure ASCII launcher — selects AI model, opens browser
├── README.md                    This file
├── data/
│   ├── military_bases.json      190 verified military bases (all branches)
│   ├── conflicts.json           Active conflict zones with intensity ratings
│   ├── war_status.json          Real-time war status per country code
│   ├── nuclear_sites.json       Nuclear & missile sites
│   ├── construction.json        Under-construction military facilities
│   ├── bri_routes.json          China's Belt & Road Initiative infrastructure
│   ├── chokepoints.json         Maritime chokepoints with threat data
│   ├── surveillance.json        Global surveillance index scores
│   ├── ports.json               Strategic ports
│   └── osint_cache/             Cached OSINT domain feeds
├── backend/
│   ├── run_backend.bat          Safe launcher — keeps window open on crash
│   ├── main.py                  FastAPI server: all REST + WebSocket endpoints
│   ├── ai_pipeline.py           LeviathanPipeline + AIPipeline alias (local LLM)
│   ├── data_manager.py          JSON data access layer
│   ├── osint_worker.py          10-domain parallel OSINT scraper
│   ├── cyber_engine.py          Live cyber attack simulation + WS broadcast
│   ├── conflict_detector.py     Conflict intensity tracking
│   └── requirements.txt
└── frontend/
    ├── index.html               App shell, includes CesiumJS
    ├── app.js                   ~1000 lines: main 3D engine and logic
    ├── build_data.py            Script to expand default military data to 500+ bases
```

---

## Globe Architecture — CesiumJS Engine

The 3D globe is now powered entirely by **CesiumJS**, replacing the previous dual Leaflet/Three.js architecture. This provides a unified seamless 3D-to-2D zooming experience without any "mode switching" artifacts.

### Visual Styling

- **ESRI World Imagery:** The globe uses high-resolution realistic satellite imagery from ESRI (with an OpenStreetMap fallback).
- **Full Illumination:** The `enableLighting` setting is purposefully set to `false`. This removes the directional sunlight effects, meaning there is no "dark side" of the Earth. The entire globe is fully lit and clearly visible at all times, making geopolitical analysis much easier without wrestling with simulated time-of-day shadows.
- **Holographic Toggles:** The globe supports visual layers for tracking active data points (satellites, conflicts, missile arcs) built directly into Cesium entity collections.

---

## Globe Simulation Mechanism & Complexity

Simulating a high-fidelity 3D globe like Google Earth is a mathematically and computationally intensive task. **Leviathan_Eye** achieves this through several nested layers of complexity:

### 1. The WGS84 Ellipsoid
Unlike many games that use a simple sphere, this dashboard uses the **WGS84 ellipsoid model**—the same standard used by GPS. Every point on the map is calculated based on the Earth’s actual equatorial bulge, mapping 2D Lat/Lon coordinates into a 3D Cartesian space (X, Y, Z) in real-time.

### 2. Multi-Resolution Tiling & Level of Detail (LoD)
To prevent the application from crashing while trying to load the entire world's imagery at once, we use a **Quadtree Tiling System**. 
- As you zoom in, the engine dynamically calculates which specific "tiles" of the Earth are visible and fetches higher-resolution versions of only those tiles.
- Distant tiles are simplified or rendered at extremely low resolution to save memory. 

### 3. Precision Management (The "Jitter" Problem)
Rendering objects millions of meters away from the origin in standard 32-bit floating point math leads to "jittery" movement. This project uses **Relative-to-Center (RTC) rendering** and double-precision math on the GPU to ensure that even at 100km altitude or 1km altitude, the labels and markers remain perfectly stable.

### 4. Asynchronous Data Orchestration
The complexity spikes when combining static 3D layers with **Live Overpass API** fetches and **SGP4 Satellite Propagation**. The engine must constantly recalculate the positions of thousands of moving satellites while simultaneously managing the geometric occlusions of the Earth's horizon (depth testing), all while maintaining 60 frames per second.

---

## Live Internet Fetching (Demand-Driven)

### Design Philosophy

NOTHING loads onto the globe until the user explicitly requests it. Furthermore, military facilities are now fetched in real-time straight from the **OpenStreetMap Overpass API** based on the user's exact 3D camera viewport. 

1. User toggles "Air Bases" layer.
2. The current visible globe coordinates (Bounding Box) are calculated.
3. An Overpass API query fetches all active `/military=airfield` nodes within those coordinates.
4. Data is instantly merged with the local database for maximum accuracy.
5. Rendered using professional, depth-tested SVG billboard markers (✈, ⚓, ★, ☢) instead of simple dots.

### Why This Architecture Excels

Loading every military base in the world at startup would destroy frame rates and clutter the screen. By utilizing **viewport-bounded internet queries** alongside a static local database of critical priority targets, the application maintains a perfect 60fps frame budget.
- Startup = 0 API rendering calls
- Only facilities you are actively looking at are fetched and drawn
- Panning/Zooming triggers a debounced background refresh to continuously populate the map
- Right-panel layer statistics use an **Accumulative Counter**: as you pan the globe, new bases discovered from the internet are continuously added to your session's memory, causing the sidebar numbers to grow incrementally without ever losing previously discovered targets.

### Layer State Machine

```javascript
var L = {
  bases:       {active:false, loaded:false, objects:[]},
  airbases:    {active:false, loaded:false, objects:[]},
  naval:       {active:false, loaded:false, objects:[]},
  nuclear:     {active:false, loaded:false, objects:[]},
  construction:{active:false, loaded:false, objects:[]},
  conflicts:   {active:false, loaded:false, objects:[]},
  arcs:        {active:false, loaded:false, objects:[]},
  chokepoints: {active:false, loaded:false, objects:[]},
  satellites:  {active:false, loaded:false, satrecs:[], instMesh:null, batchIdx:0},
  surveillance:{active:false, loaded:false, objects:[]},
  bri:         {active:false, loaded:false, objects:[]},
};
```

Each layer also has a `loading` CSS animation (a scanning line at the bottom of the button)
that plays while the API call is in progress.

---

## Satellite Tracking — Live Orbital Propagation

### Real-Time SGP4 in CesiumJS

The live satellites layer fetches current TLE (Two-Line Element) sets for up to 2,500 active satellites globally.

CesiumJS tracks these paths using a `SampledPositionProperty`. The `satellite.js` library is used purely to process the TLE logic, and Cesium automatically extrapolates the data into a perfectly smooth orbit path in real-time. 

### Satellite Zoom Constraints

If thousands of satellites are shown simultaneously, it clutters the interface when zooming in to view ground troops. 

**Zoom Altitude Culling:** Satellites are bound mathematically to the camera's altitude. 
- `camera.height > 6,000,000 meters` = ALL satellites visible.
- `camera.height < 6,000,000 meters` = ALL satellites immediately hidden.

This ensures the user sees the larger strategic picture when zoomed out, while maintaining a perfectly clean tactical map when zoomed in on a specific country.

---

## Cyber Attack System

### Off By Default

The cyber layer is COMPLETELY disabled at startup. The WebSocket is not created,
no fallback timer runs, nothing is drawn on the globe.

**Why:** The previous version auto-started cyber immediately, flooding the log and
dominating the globe visuals before the user even saw the map.

### Activation Flow

```
User clicks "LIVE CYBER ATTACKS" button
    ↓
CY.on = true
    ↓
connectCyberWS() attempts WebSocket to /ws/cyber
    ↓ (success)          ↓ (fail — backend offline)
Live attacks via WS    startFallback() — local simulation
    ↓                       ↓
addCyberArc()           same path
    ↓
cyberGrp Three.js arcs
    ↓
cyberLog() — right panel log
cyberStats() — bar chart update
```

### Arc Animation System

Each cyber arc has three animation phases:

```
Phase 1: TRAVEL (duration: 1800-2400ms)
    - Active line segment grows from source to destination
    - Head particle moves along the Bezier curve
    - Faint trail shows the full arc path

Phase 2: BLIP (duration: 1200ms)
    - Impact ring expands at destination (scale 1 → 8)
    - All elements fade out
    - Opacity transitions from 1 → 0

Phase 3: DONE
    - All Three.js objects removed from scene
    - geometry.dispose() + material.dispose() called
    - Arc entry removed from CY.arcs array
```

### Bezier Curve Arc Formula

```javascript
var from = ll2v(atk.src_lat, atk.src_lng, EARTH_R * 1.01);
var to   = ll2v(atk.tgt_lat, atk.tgt_lng, EARTH_R * 1.01);
var mid  = from.clone().add(to).multiplyScalar(0.5);
// Lift midpoint above globe proportional to arc distance
mid.normalize().multiplyScalar(EARTH_R + dist * 0.55 + 0.05);
var curve = new THREE.QuadraticBezierCurve3(from, mid, to);
```

Arcs curve upward in 3D space — longer arcs have higher peaks.

---

## Scaling Methods Applied

Based on the goal of ensuring ultra-high framerates even with massive datasets (e.g. 30,000+ OSINT military bases globally), the dashboard implements robust scaling techniques:

### 1. Viewport-Based Culling at 30k Scale
The application connects to live OSINT feeds (Overpass API / OpenStreetMap node networks) extracting upward of 30,000 live military bases globally.

Loading 30k entities into Cesium causes extreme lag. To solve this, **we implemented a live Camera Frustum Bounds Check**.
- Every time the camera finishes moving (`camera.moveEnd`), the engine computes the Lat/Lon `computeViewRectangle()`.
- The dataset is filtered, and **only bases physically inside your current computer screen bounds** are loaded into the rendering engine, up to a hard cap (MAX_ENTITIES = 400).
- As you pan the map, off-screen markers are destroyed, and new markers stream in seamlessly.
- **This reduces rendering load by over 98%**, completely eliminating lag.

### 2. Distance Display Conditions
Cesium automatically checks camera distance. Even when bases *are* inside the camera view, they are completely disabled at excessive zoom ranges (`DistanceDisplayCondition(0, 1200000)`) preventing massive z-fighting overlap when looking at a country region from space.

### 3. Continuous Integration
All logic relies on passive background memory caches. The intense 30k base query occurs once in the background upon launch and combines with local sets. Subsequent filtering occurs near-instantaneously purely within browser RAM.

### 4. WebSocket Streaming
Cyber attacks stream via WebSocket (`/ws/cyber`), reducing HTTP polling overhead entirely. Local arc generation builds and destroys primitive line elements natively in loop.

---

## Backend Endpoints Reference

```
GET  /                              Serves frontend/index.html
GET  /api/v1/map/bases              All military bases (190 entries)
GET  /api/v1/map/bases/search       NLP search: ?q=india+naval
GET  /api/v1/map/conflicts          Conflict zones
GET  /api/v1/map/bri                Belt & Road Initiative routes
GET  /api/v1/map/construction       Under-construction military sites
GET  /api/v1/map/chokepoints        Maritime chokepoints
GET  /api/v1/map/ports              Strategic ports
GET  /api/v1/map/global_routes      Global shipping routes
GET  /api/v1/map/lanes              Sea lanes
GET  /api/v1/nuclear/sites          Nuclear + missile sites
GET  /api/v1/conflicts/wars         War status per country
GET  /api/v1/conflicts/active       Active conflicts by intensity
GET  /api/v1/surveillance/index     Global surveillance scores
GET  /api/v1/surveillance/{cc}      Per-country surveillance detail
GET  /api/v1/osint/{domain}         OSINT domain data
POST /api/v1/osint/refresh          Trigger full OSINT refresh
POST /api/v1/osint/refresh/{domain} Refresh single domain
GET  /api/v1/search/bases?q=        NLP base search
GET  /api/v1/satellites/tle         Satellite TLE data (via httpx from Celestrak)
GET  /api/v1/satellites/stats       Satellite statistics
POST /api/v1/ai/chat                AI chat endpoint (SSE stream collector)
GET  /api/v1/ai/status              AI pipeline status
GET  /api/v1/news/feed              Aggregated news feed
GET  /api/v1/news/breaking          Breaking news items
GET  /api/v1/data/stats             Dashboard stats summary
GET  /api/v1/countries/all          All country data combined
GET  /api/v1/cyber/attacks          Recent cyber attacks (ring buffer)
GET  /api/v1/cyber/stats            Cyber attack statistics
GET  /health                        Health check
WS   /ws/news                       Live news WebSocket
WS   /ws/intel                      War status WebSocket (30s interval)
WS   /ws/cyber                      Live cyber attacks WebSocket
```

---

## Left Sidebar — Full Panel Guide

### Database Overview (always visible)
Shows total counts from the backend: military bases, conflicts, war zones, OSINT feeds.
Loaded from `/api/v1/data/stats` on startup — no globe objects created.

### LIVE CYBER ATTACKS Button
- **OFF by default** — does not consume any resources
- Click to activate: connects WebSocket or starts local simulation fallback
- When active: green pulsing dot, attack count shown, arcs appear on globe
- Click again to deactivate: arcs cleared, WebSocket kept alive but ignored
- Full statistics in the right panel CYBER tab

### Map Layers (click to load)
Each layer loads independently on first click. A scanning animation plays during load.

| Layer | Source | Globe Objects | Count |
|---|---|---|---|
| Military Bases | `/api/v1/map/bases` (army subtype) | Sphere markers | ~80 |
| Air Bases | Same endpoint, airbase subtype | Sphere markers | ~85 |
| Naval Bases | Same endpoint, naval subtype | Sphere markers | ~35 |
| Nuclear/Missile | Same endpoint, nuclear/missile | Purple sphere markers | ~24 |
| Under Construction | Same endpoint, construction status | Yellow diamond markers | varies |
| Conflict Zones | Built-in data (no API) | Pulsing rings + center dots | 13 |
| Missile/Strike Arcs | Built-in data (no API) | Bezier curve lines + arrows | 11 |
| Maritime Chokepoints | Built-in data (no API) | Diamond markers | 8 |
| Live Satellites | `/api/v1/satellites/tle` | InstancedMesh (1 draw call) | up to 2500 |
| Surveillance Heat | Built-in data (no API) | Transparent spheres | 10 |
| BRI Routes | `/api/v1/map/bri` or built-in | Line segments | 5+ |

### Active Conflicts
Loaded from `/api/v1/conflicts/wars`. Sorted by intensity: critical → high → elevated → medium.
Clicking a country flies the camera to that region.

### Surveillance Index
Shows top surveillance states by score (0-100 scale).
Visual bar chart. China (97), North Korea (95) top the list.

### Satellite Filter
Filters the InstancedMesh display without re-fetching TLE data.
Filtered-out satellites are scaled to (0,0,0) — invisible but not deleted.

---

## Right Panel — Tabs

### NEWS Tab
Aggregated from OSINT domains via `/api/v1/news/feed`. Refreshes every 2 minutes.
Clicking an item opens the source URL.

### INTEL Tab
OSINT domain status from `/api/v1/data/stats`.
Shows total counts for all intelligence categories.
"Refresh All OSINT Domains" button triggers a full scrape.

### CYBER Tab
Live statistics when cyber layer is active:
- Active attacks in last 5 seconds
- Session total
- Top attack source countries (bar chart)
- Top targeted countries (bar chart)
- Top attack vectors (bar chart, color-coded per attack type)
- Live rolling log (last 60 attacks)

### AI Tab
Chat interface to the local LLM via `/api/v1/ai/chat`.
Context includes current camera position (approximate lat/lng).
Press Enter or click the send button.

---

## Controls

| Control | Action |
|---|---|
| Drag globe | Rotate (smooth interpolation) |
| Scroll wheel | Zoom in/out |
| Click marker | Show popup with details |
| Click popup "Focus" | Fly camera to that location |
| IN button | Reset to India view |
| + / - buttons | Zoom in / out |
| R button | Toggle auto-rotation |
| 3D button | Toggle camera tilt |
| Sidebar toggle (◀/▶) | Show/hide left sidebar |
| Search bar | NLP search across all bases |

---

## Known Issues & Status

### Backend Traceback on Shutdown (NOT a crash)
When you press Ctrl+C to stop the backend, you will see:
```
asyncio.exceptions.CancelledError
```
This is **normal Python asyncio behavior** when a WebSocket coroutine is interrupted
by a signal. It does not indicate any problem. The backend was running fine.

### TLE Satellite Data Requires Internet
`/api/v1/satellites/tle` fetches from Celestrak (`celestrak.org/SATCAT/TLE`) via `httpx`.
If the backend machine has no internet access, satellite layer returns empty.
The layer will show "0 (no TLE)" in the count. All other layers work fully offline.

### OSINT News Requires Internet
OSINT domain scraping in `osint_worker.py` fetches from live RSS feeds.
Offline mode: the news tab shows "Backend offline — news unavailable".
All globe layers (bases, conflicts, arcs, etc.) are fully offline — they use local JSON data.

---

## Performance Targets

| Metric | Target | How Achieved |
|---|---|---|
| Startup to globe visible | < 200ms | Canvas texture, no API calls |
| Layer load time | < 500ms | Single fetch + batch render |
| Satellite rendering at 2000 sats | 60fps | InstancedMesh (1 draw call) |
| Cyber arc rendering | 60fps | Managed arc pool, dispose on complete |
| DOM updates | < 5ms/frame | Only update stat counters every 2s |
| Memory | < 300MB | Per-layer object pools, dispose on hide |

---

## Development Notes

### Python Dependencies
```
fastapi
uvicorn
httpx
aiohttp
feedparser
```
Install: `pip install -r requirements.txt`

### Frontend Dependencies (CDN, no npm)
- `CesiumJS` — 3D Earth rendering engine
- `satellite.js` — SGP4 orbital mechanics

---

*Leviathan_Eye — Built for intelligence analysts, security researchers, and geopolitical monitoring.*
*All data is sourced from publicly available OSINT, official government records, and open databases.*
