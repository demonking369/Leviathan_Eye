/* ═══ Leviathan_Eye — CesiumJS Globe Engine ═══ */

const API = window.location.origin;
let allBases = [], conflictsData = [], nuclearData = [];
let allSats = [], satEntities = [], satFilter = 'ALL';
let entities = {}, conflictEntities = [], nukeEntities = [];
let activeFilters = new Set();
let selectedBase = null;
let viewer, detailViewer;
let countryFilter = null;

/* ═══ INIT CESIUM ═══ */
async function init() {
    phase('Creating 3D globe...');
    viewer = new Cesium.Viewer('cesiumContainer', {
        animation: false, timeline: false, fullscreenButton: false,
        vrButton: false, geocoder: false, homeButton: false,
        infoBox: false, selectionIndicator: false, navigationHelpButton: false,
        baseLayerPicker: false, sceneModePicker: false,
        terrainProvider: undefined,
        skyBox: new Cesium.SkyBox({
            sources: {
                positiveX: 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=',
                negativeX: 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=',
                positiveY: 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=',
                negativeY: 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=',
                positiveZ: 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=',
                negativeZ: 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII='
            }
        }), // Black skybox
        skyAtmosphere: new Cesium.SkyAtmosphere(),
        orderIndependentTranslucency: false,
        contextOptions: { webgl: { alpha: false } },
        requestRenderMode: false,
        maximumRenderTimeChange: Infinity
    });
    viewer.scene.backgroundColor = Cesium.Color.fromCssColorString('#060810');
    viewer.scene.globe.enableLighting = false; // Disable darkness on the unlit side
    viewer.scene.globe.baseColor = Cesium.Color.fromCssColorString('#0a1a2a');
    viewer.scene.fog.enabled = true;
    viewer.scene.fog.density = 0.0003;
    viewer.scene.globe.showGroundAtmosphere = false; // Completely removes sunlight scatter shadow

    // viewer.scene.sun = new Cesium.Sun(); // Removed to prevent a visible sun
    // viewer.scene.moon = new Cesium.Moon();

    phase('Adding satellite imagery...');
    try {
        const esri = await Cesium.ArcGisMapServerImageryProvider.fromUrl(
            'https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer'
        );
        viewer.imageryLayers.addImageryProvider(esri);
    } catch (e) {
        console.log('Esri imagery unavailable, using OSM:', e);
        try {
            viewer.imageryLayers.addImageryProvider(new Cesium.OpenStreetMapImageryProvider({
                url: 'https://a.tile.openstreetmap.org/'
            }));
        } catch (e2) { console.log('OSM also failed:', e2); }
    }

    // Apply default theme to the globe imagery
    const layers = viewer.imageryLayers;
    if (layers.length > 0) {
        const baseLayer = layers.get(layers.length - 1);
        baseLayer.brightness = 1.0;
        baseLayer.contrast = 1.0;
        baseLayer.saturation = 1.0;
        baseLayer.gamma = 1.0;
    }

    // Enable continuous clock for satellite orbiting at 10x speed so motion is obvious
    viewer.clock.shouldAnimate = true;
    viewer.clock.multiplier = 10;

    flyToIndia();
    phase('Loading military databases...');
    await loadAllData();
    phase('Building interface...');
    buildUI();
    startClock();

    // Start background live OSINT fetch
    loadLiveBases();

    // Connect cyber attack WebSocket
    connectCyberWS();

    setTimeout(() => {
        document.getElementById('loading').style.opacity = '0';
        setTimeout(() => document.getElementById('loading').style.display = 'none', 400);
    }, 600);

    viewer.scene.postRender.addEventListener(updateHud);
    viewer.camera.moveEnd.addEventListener(onCameraMoveEnd);
    viewer.screenSpaceEventHandler.setInputAction(onLeftClick, Cesium.ScreenSpaceEventType.LEFT_CLICK);
}

function phase(t) { document.getElementById('lphase').textContent = t; }

/* ═══ DATA LOADING ═══ */
async function loadAllData() {
    try {
        const [bRes, cRes, nRes, sRes] = await Promise.all([
            fetch(API + '/bases').then(r => r.json()),
            fetch(API + '/conflicts').then(r => r.json()),
            fetch(API + '/nuclear').then(r => r.json()),
            fetch(API + '/api/v1/satellites/tle').then(r => r.json())
        ]);
        allBases = Array.isArray(bRes) ? bRes : (bRes.data || bRes.bases || []);
        conflictsData = Array.isArray(cRes) ? cRes : (cRes.data || cRes.conflicts || []);
        nuclearData = Array.isArray(nRes) ? nRes : (nRes.data || nRes.nuclear_sites || []);
        allSats = Array.isArray(sRes) ? sRes : (sRes.data || sRes.satellites || []);
    } catch (e) {
        console.error('API fetch error:', e);
        allBases = []; conflictsData = []; nuclearData = []; allSats = [];
    }

    document.getElementById('st-bases').textContent = allBases.length;
    document.getElementById('st-cnfl').textContent = conflictsData.length;
    document.getElementById('st-wars').textContent = conflictsData.filter(c => c.war_status).length;
    document.getElementById('st-nuke').textContent = nuclearData.length;
    document.getElementById('st-sats').textContent = allSats.length;
    document.getElementById('sb-bases').textContent = 'Bases: ' + allBases.length;
    document.getElementById('sb-wars').textContent = 'Wars: ' + conflictsData.filter(c => c.war_status).length;
}

/* ═══ LAYER TOGGLE — LIVE OVERPASS API ═══ */
const typeColors = {
    'air_base': '#ff9933', 'naval_base': '#4488ff', 'military_base': '#ff4444',
    'nuclear': '#ff44ff', 'missile_test': '#ffcc00', 'sigint': '#aa44ff',
    'training': '#00ffcc', 'research': '#00ffcc'
};

/* ── Professional SVG Marker Icons (data URIs) ── */
function makeSvgPin(color, iconChar) {
    const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="32" height="40" viewBox="0 0 32 40">
        <defs><filter id="sh"><feDropShadow dx="0" dy="1" stdDeviation="1.5" flood-opacity=".5"/></filter></defs>
        <path d="M16 39 C16 39 2 22 2 14 A14 14 0 1 1 30 14 C30 22 16 39 16 39Z" fill="${color}" stroke="#111" stroke-width="1.2" filter="url(#sh)"/>
        <circle cx="16" cy="14" r="9" fill="rgba(0,0,0,.3)"/>
        <text x="16" y="18" text-anchor="middle" font-size="14" fill="#fff">${iconChar}</text>
    </svg>`;
    return 'data:image/svg+xml,' + encodeURIComponent(svg);
}

const markerIcons = {
    'air_base': makeSvgPin('#ff9933', '\u2708'),
    'naval_base': makeSvgPin('#4488ff', '\u2693'),
    'military_base': makeSvgPin('#ff4444', '\u2605'),
    'nuclear': makeSvgPin('#ff44ff', '\u2622'),
    'missile_test': makeSvgPin('#ffcc00', '\u25B2'),
    'sigint': makeSvgPin('#aa44ff', '\u25C9'),
    'training': makeSvgPin('#00ffcc', '\u25C6'),
    'research': makeSvgPin('#00ffcc', '\u25C7')
};

/* ── Overpass API query templates per layer type ── */
const overpassQueries = {
    'air_base': `[out:json][timeout:12];(node["military"="airfield"]({bbox});way["military"="airfield"]({bbox});node["aeroway"="aerodrome"]["military"="yes"]({bbox});way["aeroway"="aerodrome"]["military"="yes"]({bbox});node["aeroway"="aerodrome"]["operator:type"="military"]({bbox});way["aeroway"="aerodrome"]["operator:type"="military"]({bbox}););out center 600;`,
    'naval_base': `[out:json][timeout:12];(node["military"="naval_base"]({bbox});way["military"="naval_base"]({bbox});node["landuse"="military"]["name"~"[Nn]aval|[Nn]avy|[Ff]leet"]({bbox});way["landuse"="military"]["name"~"[Nn]aval|[Nn]avy|[Ff]leet"]({bbox}););out center 600;`,
    'military_base': `[out:json][timeout:12];(node["military"="barracks"]({bbox});way["military"="barracks"]({bbox});node["military"="base"]({bbox});way["military"="base"]({bbox});node["landuse"="military"]({bbox});way["landuse"="military"]({bbox}););out center 600;`,
    'nuclear': `[out:json][timeout:12];(node["military"="nuclear_explosion_site"]({bbox});way["power"="generator"]["generator:source"="nuclear"]({bbox});node["power"="generator"]["generator:source"="nuclear"]({bbox});node["military"~"bunker"]["name"~"[Nn]uclear|[Aa]tomic|ICBM"]({bbox}););out center 300;`,
    'missile_test': `[out:json][timeout:12];(node["military"="range"]({bbox});way["military"="range"]({bbox});node["military"="danger_area"]({bbox});way["military"="danger_area"]({bbox});node["military"~"missile|launch"]({bbox}););out center 300;`,
    'sigint': `[out:json][timeout:12];(node["man_made"="surveillance"]["surveillance:type"="SIGINT"]({bbox});node["military"~"office|communications"]({bbox});way["military"~"office|communications"]({bbox});node["man_made"="antenna"]["operator:type"="military"]({bbox}););out center 300;`,
    'training': `[out:json][timeout:12];(node["military"="training_area"]({bbox});way["military"="training_area"]({bbox});node["military"="trench"]({bbox}););out center 300;`
};

/* ── Live data cache per type per viewport hash ── */
let _overpassCache = {};
let _renderedBases = new Set();
let _lastFetchBbox = {};
let _fetchingTypes = new Set();

function toggleLayer(type, el) {
    if (activeFilters.has(type)) {
        activeFilters.delete(type);
        el.classList.remove('on');
        removeEntities(type);
    } else {
        activeFilters.add(type);
        el.classList.add('on');
        fetchAndRenderLive(type);
    }
}

function showBases(type) {
    fetchAndRenderLive(type);
}

function removeEntities(type) {
    if (entities[type]) {
        entities[type].forEach(e => { try { viewer.entities.remove(e); } catch (x) { } });
        entities[type] = [];
    }
    // Clear rendered tracker for this type
    _renderedBases.forEach(id => { if (id.startsWith(type + ':')) _renderedBases.delete(id); });
    updateLayerCount(type, 0);
}

/* ── Core: Fetch from Overpass API + merge local data ── */
async function fetchAndRenderLive(type) {
    if (_fetchingTypes.has(type)) return; // Prevent concurrent fetches for same type

    const rect = viewer.camera.computeViewRectangle();
    if (!rect) return;

    const south = Cesium.Math.toDegrees(rect.south);
    const west = Cesium.Math.toDegrees(rect.west);
    const north = Cesium.Math.toDegrees(rect.north);
    const east = Cesium.Math.toDegrees(rect.east);

    // Check if bbox changed significantly since last fetch
    const bboxKey = `${south.toFixed(1)},${west.toFixed(1)},${north.toFixed(1)},${east.toFixed(1)}`;
    if (_lastFetchBbox[type] === bboxKey && entities[type]?.length > 0) return;
    _lastFetchBbox[type] = bboxKey;

    _fetchingTypes.add(type);
    updateLayerCount(type, '⟳');

    let osmBases = [];
    const queryTemplate = overpassQueries[type];

    if (queryTemplate) {
        const bbox = `${south},${west},${north},${east}`;
        const query = queryTemplate.replace(/\{bbox\}/g, bbox);

        try {
            const res = await fetch('https://overpass-api.de/api/interpreter', {
                method: 'POST',
                body: 'data=' + encodeURIComponent(query),
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
            });
            if (res.ok) {
                const data = await res.json();
                osmBases = (data.elements || []).map(el => {
                    const lat = el.lat || el.center?.lat;
                    const lon = el.lon || el.center?.lon;
                    if (!lat || !lon) return null;
                    const tags = el.tags || {};
                    return {
                        name: tags.name || tags['name:en'] || tags.official_name || `${type.replace(/_/g, ' ')} #${el.id}`,
                        lat, lon,
                        type: type,
                        country: tags['addr:country'] || tags['is_in:country'] || '',
                        status: tags.disused === 'yes' ? 'Disused' : 'Active',
                        desc: tags.description || tags.note || '',
                        source: 'OpenStreetMap',
                        osm_id: el.id,
                        details: {
                            operator: tags.operator || '',
                            established: tags.start_date || '',
                            iata: tags.iata || '',
                            icao: tags.icao || '',
                            website: tags.website || tags['contact:website'] || ''
                        }
                    };
                }).filter(Boolean);
            }
        } catch (e) {
            console.warn(`Overpass fetch failed for ${type}:`, e);
        }
    }

    // Merge with local data (our database acts as supplement)
    const localBases = allBases.filter(b => {
        const matchType = b.type === type || (type === 'training' && b.type === 'research');
        const matchCountry = !countryFilter || b.country === countryFilter;
        if (!matchType || !matchCountry) return false;
        return b.lat >= south && b.lat <= north && b.lon >= west && b.lon <= east;
    });

    // Deduplicate by proximity (within 0.01 degrees ≈ 1km)
    const merged = [...osmBases];
    localBases.forEach(lb => {
        const isDuplicate = merged.some(ob => Math.abs(ob.lat - lb.lat) < 0.01 && Math.abs(ob.lon - lb.lon) < 0.01);
        if (!isDuplicate) merged.push(lb);
    });

    // Render
    const MAX_ENTITIES = 500;
    const subset = merged.slice(0, MAX_ENTITIES);

    // Clear old entities for this type
    if (entities[type]) {
        entities[type].forEach(e => { try { viewer.entities.remove(e); } catch (x) { } });
    }
    entities[type] = [];
    _renderedBases.forEach(id => { if (id.startsWith(type + ':')) _renderedBases.delete(id); });

    // Add new entities with professional markers
    const iconUrl = markerIcons[type] || markerIcons['military_base'];
    subset.forEach(b => {
        const bId = type + ':' + (b.osm_id || b.name + b.lat + b.lon);
        if (_renderedBases.has(bId)) return;
        _renderedBases.add(bId);

        const ent = viewer.entities.add({
            position: Cesium.Cartesian3.fromDegrees(b.lon, b.lat),
            billboard: {
                image: iconUrl,
                width: 24, height: 30,
                verticalOrigin: Cesium.VerticalOrigin.BOTTOM,
                heightReference: Cesium.HeightReference.CLAMP_TO_GROUND,
                scaleByDistance: new Cesium.NearFarScalar(500000, 1.0, 8000000, 0.4)
            },
            label: {
                text: b.name || '', font: '10px monospace',
                fillColor: Cesium.Color.WHITE, outlineColor: Cesium.Color.BLACK, outlineWidth: 2,
                style: Cesium.LabelStyle.FILL_AND_OUTLINE,
                verticalOrigin: Cesium.VerticalOrigin.TOP, pixelOffset: new Cesium.Cartesian2(0, 4),
                distanceDisplayCondition: new Cesium.DistanceDisplayCondition(0, 800000),
                heightReference: Cesium.HeightReference.CLAMP_TO_GROUND,
                scaleByDistance: new Cesium.NearFarScalar(200000, 1.0, 3000000, 0.0)
            },
            properties: { baseData: b, baseType: type }
        });
        ent._baseId = bId;
        entities[type].push(ent);
    });

    // Update allBases with new data for country panel calculations
    const newBases = merged.filter(b => !allBases.some(ab => Math.abs(ab.lat - b.lat) < 0.005 && Math.abs(ab.lon - b.lon) < 0.005));
    allBases.push(...newBases);

    updateLayerCount(type, merged.length);
    _fetchingTypes.delete(type);

    // Update total bases count in HUD
    document.getElementById('st-bases').textContent = '~' + allBases.length;
    document.getElementById('sb-bases').textContent = 'Bases: ~' + allBases.length;
}

/* ── Debounced camera move handler: re-fetch active layers ── */
let _cameraDebounce = null;
function onCameraMoveEnd() {
    clearTimeout(_cameraDebounce);
    _cameraDebounce = setTimeout(() => {
        activeFilters.forEach(type => fetchAndRenderLive(type));
    }, 800);
}

function updateLayerCount(type, count) {
    const map = {
        'air_base': 'lc-airbases', 'naval_base': 'lc-naval', 'military_base': 'lc-military',
        'nuclear': 'lc-nuclear', 'missile_test': 'lc-missile', 'sigint': 'lc-sigint', 'training': 'lc-training'
    };
    const el = document.getElementById(map[type]);
    if (el) {
        if (count === '⟳') {
            el.textContent = '⟳';
        } else {
            // Accumulate and display the total number of unique bases discovered so far for this type
            let totalFound = 0;
            if (type === 'nuclear') {
                totalFound = nuclearData.length;
            } else if (type === 'training') {
                totalFound = allBases.filter(b => b.type === 'training' || b.type === 'research').length;
            } else {
                totalFound = allBases.filter(b => b.type === type).length;
            }
            el.textContent = totalFound > 0 ? totalFound : '—';
        }
    }
}

/* ═══ CONFLICTS ═══ */
function toggleConflicts(el) {
    if (conflictEntities.length) {
        conflictEntities.forEach(e => viewer.entities.remove(e));
        conflictEntities = [];
        el.classList.remove('on');
        document.getElementById('lc-conflicts').textContent = '—';
        return;
    }
    el.classList.add('on');
    conflictsData.forEach(c => {
        if (!c.origin_lat || !c.origin_lon) return;
        const col = c.intensity === 'extreme' ? '#ff1111' : c.intensity === 'critical' ? '#ff4400' : c.intensity === 'high' ? '#ff8800' : '#ffcc00';
        const ent = viewer.entities.add({
            position: Cesium.Cartesian3.fromDegrees(c.target_lon || c.origin_lon, c.target_lat || c.origin_lat),
            point: { pixelSize: 12, color: Cesium.Color.fromCssColorString(col).withAlpha(0.7), outlineColor: Cesium.Color.fromCssColorString(col), outlineWidth: 2 },
            label: { text: c.name, font: 'bold 11px monospace', fillColor: Cesium.Color.fromCssColorString(col), outlineColor: Cesium.Color.BLACK, outlineWidth: 2, style: Cesium.LabelStyle.FILL_AND_OUTLINE, verticalOrigin: Cesium.VerticalOrigin.BOTTOM, pixelOffset: new Cesium.Cartesian2(0, -16) },
            properties: { conflictData: c }
        });
        if (c.origin_lat !== c.target_lat || c.origin_lon !== c.target_lon) {
            const line = viewer.entities.add({
                polyline: { positions: Cesium.Cartesian3.fromDegreesArray([c.origin_lon, c.origin_lat, c.target_lon, c.target_lat]), width: 2, material: new Cesium.PolylineGlowMaterialProperty({ glowPower: 0.2, color: Cesium.Color.fromCssColorString(col).withAlpha(0.5) }), clampToGround: true }
            });
            conflictEntities.push(line);
        }
        conflictEntities.push(ent);
    });
    document.getElementById('lc-conflicts').textContent = conflictsData.length;
}

/* ═══ NUCLEAR ARSENALS ═══ */
function toggleNukeSites(el) {
    if (nukeEntities.length) {
        nukeEntities.forEach(e => viewer.entities.remove(e));
        nukeEntities = [];
        el.classList.remove('on');
        document.getElementById('lc-nukesites').textContent = '—';
        return;
    }
    el.classList.add('on');
    nuclearData.forEach(n => {
        const ent = viewer.entities.add({
            position: Cesium.Cartesian3.fromDegrees(n.lon, n.lat),
            point: { pixelSize: 9, color: Cesium.Color.fromCssColorString('#ff00ff').withAlpha(0.7), outlineColor: Cesium.Color.MAGENTA, outlineWidth: 2 },
            label: { text: '☢ ' + (n.name || ''), font: 'bold 10px monospace', fillColor: Cesium.Color.MAGENTA, outlineColor: Cesium.Color.BLACK, outlineWidth: 2, style: Cesium.LabelStyle.FILL_AND_OUTLINE, verticalOrigin: Cesium.VerticalOrigin.BOTTOM, pixelOffset: new Cesium.Cartesian2(0, -14), distanceDisplayCondition: new Cesium.DistanceDisplayCondition(0, 2500000) },
            properties: { nukeData: n }
        });
        nukeEntities.push(ent);
    });
    document.getElementById('lc-nukesites').textContent = nuclearData.length;
}

/* ═══ CLICK HANDLER ═══ */
function onLeftClick(movement) {
    const pick = viewer.scene.pick(movement.position);
    if (!Cesium.defined(pick) || !pick.id || !pick.id.properties) return;
    const props = pick.id.properties;
    if (props.baseData) {
        const b = props.baseData.getValue ? props.baseData.getValue(Cesium.JulianDate.now()) : props.baseData._value || props.baseData;
        showDetail(b);
    } else if (props.conflictData) {
        const c = props.conflictData.getValue ? props.conflictData.getValue(Cesium.JulianDate.now()) : props.conflictData._value || props.conflictData;
        showConflictDetail(c);
    } else if (props.nukeData) {
        const n = props.nukeData.getValue ? props.nukeData.getValue(Cesium.JulianDate.now()) : props.nukeData._value || props.nukeData;
        showNukeDetail(n);
    } else if (props.satData) {
        const s = props.satData.getValue ? props.satData.getValue(Cesium.JulianDate.now()) : props.satData._value || props.satData;
        const satrec = props.satrec.getValue ? props.satrec.getValue(Cesium.JulianDate.now()) : props.satrec._value || props.satrec;
        const posProp = props.posProp.getValue ? props.posProp.getValue(Cesium.JulianDate.now()) : props.posProp._value || props.posProp;
        showSatDetail(s, satrec, posProp);
    }
}

/* ═══ DETAIL PANEL ═══ */
async function showDetail(b) {
    selectedBase = b;
    switchTab('detail', document.getElementById('detail-tab-btn'));
    document.getElementById('det-empty').style.display = 'none';
    document.getElementById('det-content').style.display = 'block';
    document.getElementById('det-title').textContent = b.name || 'Unknown';
    const badge = document.getElementById('det-badge');
    const st = (b.status || 'active').toLowerCase();
    const colors = { active: '#00ff88', construction: '#ffcc00', inactive: '#666', controversial: '#ff8800' };
    badge.style.background = (colors[st] || '#4488ff') + '22';
    badge.style.color = colors[st] || '#4488ff';
    badge.textContent = (b.status || 'ACTIVE').toUpperCase();

    /* Mini satellite view — use Esri static map image */
    const detMapEl = document.getElementById('detail-map');
    if (detMapEl) {
        const zoom = 15;
        const imgUrl = `https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/export?bbox=${b.lon - 0.02},${b.lat - 0.015},${b.lon + 0.02},${b.lat + 0.015}&bboxSR=4326&imageSR=4326&size=400,200&f=image`;
        detMapEl.innerHTML = `<img src="${imgUrl}" style="width:100%;height:100%;object-fit:cover;border-radius:6px" onerror="this.style.display='none'" /><div style="position:absolute;bottom:4px;right:6px;font-size:8px;color:#00d4ff;text-shadow:0 0 3px #000">📍 ${b.lat?.toFixed(3)}°N, ${b.lon?.toFixed(3)}°E</div>`;
        detMapEl.style.position = 'relative';
    }

    /* Live Reverse Geocoding for Missing Country Data */
    let displayCountry = b.country;
    if (b.country === 'Global OSINT' || !b.country) {
        try {
            const rc = await fetch(`https://nominatim.openstreetmap.org/reverse?lat=${b.lat}&lon=${b.lon}&format=json`);
            if (rc.ok) {
                const rcData = await rc.json();
                if (rcData.address && rcData.address.country) {
                    displayCountry = rcData.address.country;
                    b.country = displayCountry; // cache it
                }
            }
        } catch (e) { }
    }

    /* Detail rows */
    const detail = b.details || {};
    let rows = '';
    const addRow = (l, v) => { if (v) rows += `<div class="det-row"><span class="det-lbl">${l}</span><span class="det-val">${v}</span></div>`; };
    addRow('Country', displayCountry);
    addRow('Type', (b.type || '').replace(/_/g, ' ').toUpperCase());
    addRow('Service', b.arm || detail.arm);
    addRow('Role', detail.role);
    addRow('Coordinates', `${b.lat?.toFixed(3)}°N, ${b.lon?.toFixed(3)}°E`);
    addRow('Status', b.status);
    addRow('Description', b.desc);
    if (detail.aircraft && detail.aircraft.length) addRow('Aircraft', detail.aircraft.join(', '));
    if (detail.ships && detail.ships.length) addRow('Ships', detail.ships.join(', '));
    if (detail.weapons_systems && detail.weapons_systems.length) addRow('Weapons', detail.weapons_systems.join(', '));
    addRow('Personnel', detail.personnel_est ? detail.personnel_est.toLocaleString() : null);
    addRow('Established', detail.established);
    addRow('Area', detail.area_sq_km ? detail.area_sq_km + ' km²' : null);
    addRow('Runways', detail.runways);
    addRow('Commander', detail.commander);
    addRow('Notable', detail.notable);

    // Google Earth Link
    addRow('External Link', `<a href="https://earth.google.com/web/search/${b.lat},${b.lon}" target="_blank" style="color:#00d4ff;text-decoration:none">🌍 Open in Google Earth</a>`);
    addRow('Google Maps', `<a href="https://www.google.com/maps/@${b.lat},${b.lon},14z" target="_blank" style="color:#00d4ff;text-decoration:none">📍 View on Google Maps</a>`);

    document.getElementById('det-rows').innerHTML = rows + `
        <div style="margin-top:12px;border-top:1px solid var(--border);padding-top:10px">
            <div style="font-size:9px;color:var(--accent);text-transform:uppercase;letter-spacing:1px;margin-bottom:6px">📡 LIVE OSINT INTELLIGENCE REPORT</div>
            <div id="base-wiki-fetch" style="color:var(--dim);font-size:10px">
                <div style="display:flex;align-items:center;gap:6px">
                    <div style="width:12px;height:12px;border:2px solid var(--accent);border-top-color:transparent;border-radius:50%;animation:spin 1s linear infinite"></div>
                    Scanning Wikipedia, Wikimedia Commons, Wikidata, GeoNames...
                </div>
            </div>
        </div>
        <style>@keyframes spin{to{transform:rotate(360deg)}}</style>
    `;

    /* Fly main camera */
    viewer.camera.flyTo({ destination: Cesium.Cartesian3.fromDegrees(b.lon, b.lat, 120000), duration: 1.5 });

    /* ═══ DEEP MULTI-SOURCE INTERNET RESEARCH ═══ */
    const fetchEl = document.getElementById('base-wiki-fetch');
    if (!fetchEl) return;

    // Build multiple search terms to maximize hit rate
    const baseName = (b.name || '').trim();
    const searchTerms = [
        baseName,
        baseName.replace(/Air Force Station|Air Force Base|AFB|AFS/gi, '').trim(),
        baseName.replace(/Air Base|Naval Base|Military Base|Cantonment|Army Base/gi, '').trim(),
        baseName + ' military',
        baseName + ' ' + (displayCountry || '')
    ].filter(t => t.length > 2);

    let wikiData = null;
    let fullExtract = '';
    let wikiImages = [];
    let wikiTitle = '';
    let wikidataInfo = {};

    // 1) Try Wikipedia summary with multiple terms
    for (const term of searchTerms) {
        try {
            const res = await fetch(`https://en.wikipedia.org/api/rest_v1/page/summary/${encodeURIComponent(term)}`);
            if (res.ok) {
                const data = await res.json();
                if (data.extract && data.extract.length > 50) {
                    wikiData = data;
                    wikiTitle = data.title;
                    break;
                }
            }
        } catch (e) { }
    }

    // 2) Fetch FULL Wikipedia article (longer extract with multiple sections)
    if (wikiTitle) {
        try {
            const fullRes = await fetch(`https://en.wikipedia.org/w/api.php?action=query&titles=${encodeURIComponent(wikiTitle)}&prop=extracts|pageimages|categories|links&exintro=false&exlimit=1&explaintext=true&pithumbsize=800&format=json&origin=*`);
            if (fullRes.ok) {
                const fullData = await fullRes.json();
                const pages = fullData.query?.pages;
                if (pages) {
                    const page = Object.values(pages)[0];
                    if (page.extract) {
                        fullExtract = page.extract;
                    }
                }
            }
        } catch (e) { }
    }

    // 3) Fetch Wikimedia Commons images for this base
    if (wikiTitle) {
        try {
            const imgRes = await fetch(`https://en.wikipedia.org/w/api.php?action=query&titles=${encodeURIComponent(wikiTitle)}&prop=images&format=json&origin=*`);
            if (imgRes.ok) {
                const imgData = await imgRes.json();
                const pages = imgData.query?.pages;
                if (pages) {
                    const page = Object.values(pages)[0];
                    const images = (page.images || [])
                        .filter(img => /\.(jpg|jpeg|png|svg)$/i.test(img.title))
                        .filter(img => !/Commons-logo|Flag_of|Wikidata|Symbol|Icon|Pictogram/i.test(img.title))
                        .slice(0, 6);

                    for (const img of images) {
                        try {
                            const urlRes = await fetch(`https://en.wikipedia.org/w/api.php?action=query&titles=${encodeURIComponent(img.title)}&prop=imageinfo&iiprop=url|extmetadata&iiurlwidth=400&format=json&origin=*`);
                            if (urlRes.ok) {
                                const urlData = await urlRes.json();
                                const p = Object.values(urlData.query?.pages || {})[0];
                                if (p?.imageinfo?.[0]?.thumburl) {
                                    wikiImages.push({
                                        url: p.imageinfo[0].thumburl,
                                        desc: p.imageinfo[0].extmetadata?.ImageDescription?.value?.replace(/<[^>]*>/g, '').substring(0, 80) || img.title.replace('File:', '')
                                    });
                                }
                            }
                        } catch (e) { }
                    }
                }
            }
        } catch (e) { }
    }

    // 4) Try Wikidata for structured info (ICAO, inception, operator)
    if (wikiTitle) {
        try {
            const wdRes = await fetch(`https://en.wikipedia.org/w/api.php?action=query&titles=${encodeURIComponent(wikiTitle)}&prop=pageprops&format=json&origin=*`);
            if (wdRes.ok) {
                const wdData = await wdRes.json();
                const pages = wdData.query?.pages;
                if (pages) {
                    const wdId = Object.values(pages)[0]?.pageprops?.wikibase_item;
                    if (wdId) {
                        const entityRes = await fetch(`https://www.wikidata.org/w/api.php?action=wbgetentities&ids=${wdId}&props=claims|labels&languages=en&format=json&origin=*`);
                        if (entityRes.ok) {
                            const entityData = await entityRes.json();
                            const claims = entityData.entities?.[wdId]?.claims || {};
                            // P571=inception, P137=operator, P239=ICAO, P17=country
                            if (claims.P571?.[0]) {
                                const date = claims.P571[0].mainsnak?.datavalue?.value?.time;
                                if (date) wikidataInfo.inception = date.replace('+', '').substring(0, 10);
                            }
                            if (claims.P239?.[0]) {
                                wikidataInfo.icao = claims.P239[0].mainsnak?.datavalue?.value;
                            }
                        }
                    }
                }
            }
        } catch (e) { }
    }

    // ═══ BUILD THE RICH INTEL REPORT ═══
    let html = '';

    // Images gallery
    const allImages = [];
    if (wikiData?.thumbnail?.source) allImages.push({ url: wikiData.thumbnail.source, desc: 'Primary image' });
    allImages.push(...wikiImages);

    if (allImages.length > 0) {
        html += `<div style="display:flex;gap:4px;overflow-x:auto;margin-bottom:10px;padding-bottom:4px">`;
        allImages.slice(0, 5).forEach(img => {
            html += `<img src="${img.url}" title="${img.desc}" style="height:100px;border-radius:4px;object-fit:cover;min-width:80px;cursor:pointer;border:1px solid var(--border)" onerror="this.style.display='none'" onclick="window.open(this.src,'_blank')">`;
        });
        html += `</div>`;
    }

    // Esri satellite map snippet
    html += `<img src="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/export?bbox=${b.lon - 0.05},${b.lat - 0.03},${b.lon + 0.05},${b.lat + 0.03}&size=400,200&f=image" style="width:100%;border-radius:4px;margin-bottom:10px;border:1px solid var(--border)" onerror="this.style.display='none'">`;

    // Wikidata structured info
    if (wikidataInfo.inception || wikidataInfo.icao) {
        html += `<div style="background:rgba(0,212,255,0.06);border:1px solid rgba(0,212,255,0.15);border-radius:4px;padding:6px;margin-bottom:10px;font-size:10px">`;
        html += `<div style="font-size:8px;color:var(--accent);text-transform:uppercase;margin-bottom:4px">WIKIDATA STRUCTURED INFO</div>`;
        if (wikidataInfo.inception) html += `<div>📅 Established: <b>${wikidataInfo.inception}</b></div>`;
        if (wikidataInfo.icao) html += `<div>✈️ ICAO Code: <b>${wikidataInfo.icao}</b></div>`;
        html += `</div>`;
    }

    // Full article extract
    if (fullExtract && fullExtract.length > 100) {
        // Show full article, split into sections
        const paragraphs = fullExtract.split('\n').filter(p => p.trim().length > 20);
        const sections = [];
        let currentSection = { title: 'Overview', content: [] };

        paragraphs.forEach(p => {
            if (p.length < 60 && p === p.replace(/[a-z]/g, '') || (p.length < 40 && !p.includes('.'))) {
                // Likely a section heading
                if (currentSection.content.length > 0) sections.push(currentSection);
                currentSection = { title: p.trim(), content: [] };
            } else {
                currentSection.content.push(p);
            }
        });
        if (currentSection.content.length > 0) sections.push(currentSection);

        html += `<div style="font-size:9px;color:var(--accent);text-transform:uppercase;letter-spacing:1px;margin-bottom:6px">📖 FULL INTELLIGENCE DOSSIER</div>`;
        sections.slice(0, 8).forEach(s => {
            html += `<div style="margin-bottom:10px">`;
            if (s.title !== 'Overview' || sections.length > 1) {
                html += `<div style="font-size:9px;color:var(--orange);font-weight:700;margin-bottom:3px;text-transform:uppercase">${s.title}</div>`;
            }
            html += `<div style="font-size:10px;color:var(--text);line-height:1.6">${s.content.slice(0, 4).join('<br><br>')}</div>`;
            html += `</div>`;
        });

        // Source link
        html += `<a href="https://en.wikipedia.org/wiki/${encodeURIComponent(wikiTitle)}" target="_blank" style="display:block;color:var(--accent);font-size:9px;margin-top:6px;text-decoration:none">📄 Read full article on Wikipedia →</a>`;
    } else if (wikiData?.extract) {
        html += `<div style="font-size:9px;color:var(--accent);text-transform:uppercase;letter-spacing:1px;margin-bottom:4px">📖 OSINT SUMMARY</div>`;
        html += `<div style="font-size:10px;color:var(--text);line-height:1.6;margin-bottom:8px">${wikiData.extract}</div>`;
        html += `<a href="${wikiData.content_urls?.desktop?.page || '#'}" target="_blank" style="color:var(--accent);font-size:9px;text-decoration:none">📄 Read more on Wikipedia →</a>`;
    } else {
        html += `<div style="font-size:10px;color:var(--dim)"><b>OSINT Signature:</b> Classified/Remote installation. No public intelligence readily available for "${baseName}". This may indicate a restricted or covert facility.</div>`;
    }

    // Nearby places from GeoNames
    try {
        const geoRes = await fetch(`https://secure.geonames.org/findNearbyJSON?lat=${b.lat}&lng=${b.lon}&maxRows=5&radius=50&username=demo&style=FULL`);
        if (geoRes.ok) {
            const geoData = await geoRes.json();
            if (geoData.geonames && geoData.geonames.length > 0) {
                html += `<div style="margin-top:10px;font-size:9px;color:var(--accent);text-transform:uppercase;letter-spacing:1px;margin-bottom:4px">📍 NEARBY LOCATIONS (50km radius)</div>`;
                geoData.geonames.forEach(g => {
                    html += `<div style="font-size:10px;color:var(--dim);margin-bottom:3px">• ${g.name} (${g.fclName || g.fcodeName || ''}) — ${g.distance ? parseFloat(g.distance).toFixed(1) + ' km' : ''}</div>`;
                });
            }
        }
    } catch (e) { }

    fetchEl.innerHTML = html || '<div style="color:var(--dim)">No public intelligence available for this installation.</div>';
}

function showConflictDetail(c) {
    switchTab('detail', document.getElementById('detail-tab-btn'));
    document.getElementById('det-empty').style.display = 'none';
    document.getElementById('det-content').style.display = 'block';
    document.getElementById('det-title').textContent = c.name || 'Unknown Conflict';
    const badge = document.getElementById('det-badge');
    badge.style.background = '#ff111122';
    badge.style.color = '#ff3333';
    badge.textContent = (c.intensity || 'HIGH').toUpperCase();
    let rows = '';
    const addRow = (l, v) => { if (v) rows += `<div class="det-row"><span class="det-lbl">${l}</span><span class="det-val">${v}</span></div>`; };
    addRow('Status', c.status);
    addRow('Parties', (c.parties || []).join(' vs '));
    addRow('Started', c.start_date);
    addRow('Description', c.description);
    addRow('Weapons', c.missile_type);
    addRow('Daily Strikes', c.daily_strikes);
    addRow('Casualties', c.casualties_est);
    addRow('Displaced', c.displaced);
    document.getElementById('det-rows').innerHTML = rows;
}

function showNukeDetail(n) {
    switchTab('detail', document.getElementById('detail-tab-btn'));
    document.getElementById('det-empty').style.display = 'none';
    document.getElementById('det-content').style.display = 'block';
    document.getElementById('det-title').textContent = n.name || 'Nuclear Site';
    const badge = document.getElementById('det-badge');
    badge.style.background = '#ff00ff22';
    badge.style.color = '#ff44ff';
    badge.textContent = '☢ NUCLEAR';
    let rows = '';
    const addRow = (l, v) => { if (v !== undefined && v !== null) rows += `<div class="det-row"><span class="det-lbl">${l}</span><span class="det-val">${v}</span></div>`; };
    addRow('Country', n.country);
    addRow('Type', n.type);
    addRow('Warheads Est.', n.warheads_est);
    addRow('Status', n.status);
    addRow('Description', n.desc);
    document.getElementById('det-rows').innerHTML = rows;
}

/* ═══ SEARCH ═══ */
function doSearch() {
    const q = document.getElementById('si').value.trim().toLowerCase();
    if (!q) return;
    const results = allBases.filter(b =>
        (b.name || '').toLowerCase().includes(q) ||
        (b.country || '').toLowerCase().includes(q) ||
        (b.type || '').toLowerCase().includes(q.replace(/\s+/g, '_')) ||
        (b.desc || '').toLowerCase().includes(q) ||
        (b.arm || '').toLowerCase().includes(q)
    );
    const sr = document.getElementById('sr');
    sr.style.display = 'block';
    if (!results.length) { sr.innerHTML = '<div class="sri" style="color:var(--dim)">No results found</div>'; return; }
    sr.innerHTML = results.slice(0, 30).map(b =>
        `<div class="sri" onclick='searchClick(${JSON.stringify(b.id)})'><span class="srt">${(b.type || '').replace(/_/g, ' ').toUpperCase()}</span>${b.name} <span style="color:var(--dim)">(${b.country})</span></div>`
    ).join('') + (results.length > 30 ? `<div class="sri" style="color:var(--dim)">${results.length - 30} more results...</div>` : '');
}

function searchClick(id) {
    const b = allBases.find(x => x.id === id);
    if (!b) return;
    closeSearch();
    showDetail(b);
}

function closeSearch() { document.getElementById('sr').style.display = 'none'; }

/* ═══ TABS ═══ */
function switchTab(name, btn) {
    document.querySelectorAll('.tb').forEach(t => t.classList.remove('on'));
    document.querySelectorAll('.tc').forEach(t => t.classList.remove('on'));
    if (btn) btn.classList.add('on');
    const tab = document.getElementById('tab-' + name);
    if (tab) tab.classList.add('on');
}

/* ═══ BUILD UI ═══ */
function buildUI() {
    /* Wars list */
    const wl = document.getElementById('warlist');
    wl.innerHTML = conflictsData.map(c => {
        const cls = c.intensity === 'extreme' ? 'critical' : c.intensity === 'critical' ? 'critical' : c.intensity === 'high' ? 'high' : 'medium';
        return `<div class="wi ${cls}" onclick="flyToConflict('${c.id}')"><div class="wn">${c.name}</div><div class="wv">${(c.parties || []).join(' vs ')} · ${c.intensity}</div></div>`;
    }).join('');

    /* Country filter chips */
    const countries = [...new Set(allBases.map(b => b.country))].sort();
    const cf = document.getElementById('country-filters');
    cf.innerHTML = '<button class="sfc on" onclick="filterCountry(null,this)">ALL</button>' +
        countries.map(c => `<button class="sfc" onclick="filterCountry('${c}',this)">${c}</button>`).join('');

    /* News */
    document.getElementById('newslist').innerHTML = [
        { t: 'Russia launches 120+ drones at Ukraine', m: 'AP News · 2h ago' },
        { t: 'China sends 71 PLA jets near Taiwan', m: 'Reuters · 3h ago' },
        { t: 'Iran nuclear talks stalled, breakout imminent', m: 'BBC · 5h ago' },
        { t: 'Houthis attack US carrier group in Red Sea', m: 'CNN · 6h ago' },
        { t: 'India deploys BrahMos at Ladakh LAC', m: 'Times of India · 8h ago' },
        { t: 'North Korea ICBM launched toward Pacific', m: 'NHK · 12h ago' },
        { t: 'Sudan RSF massacres 300 civilians in Darfur', m: 'Al Jazeera · 14h ago' },
        { t: 'NATO scrambles jets over Baltic Sea', m: 'Sky News · 18h ago' },
    ].map(n => `<div class="ni"><div class="nt">${n.t}</div><div class="nm">${n.m}</div></div>`).join('');

    /* OSINT */
    document.getElementById('osint-status').innerHTML = [
        { n: 'Sentinel Hub', s: 'ok' }, { n: 'Overpass Turbo', s: 'ok' },
        { n: 'FIRMS Fire Data', s: 'ok' }, { n: 'ADS-B Exchange', s: 'ok' },
        { n: 'MarineTraffic AIS', s: 'ok' }, { n: 'RadioReference', s: 'ok' }
    ].map(d => `<div style="display:flex;align-items:center;gap:7px;padding:4px 0;font-size:10px"><div class="sdot dg"></div>${d.n}<span style="margin-left:auto;color:var(--green);font-size:9px">●ONLINE</span></div>`).join('');

    /* Military balance */
    runBalance();

    /* Auto-enable air bases */
    toggleLayer('air_base', document.getElementById('lb-airbases'));
}

/* ═══ FLY-TO ═══ */
function flyToIndia() {
    viewer.camera.flyTo({ destination: Cesium.Cartesian3.fromDegrees(78.96, 20.59, 5500000), orientation: { heading: 0, pitch: Cesium.Math.toRadians(-90), roll: 0 }, duration: 2 });
}

function flyToConflict(id) {
    const c = conflictsData.find(x => x.id === id);
    if (!c) return;
    viewer.camera.flyTo({ destination: Cesium.Cartesian3.fromDegrees(c.target_lon || c.origin_lon, c.target_lat || c.origin_lat, 2500000), duration: 1.5 });
}

function detZoom() {
    if (!selectedBase) return;
    viewer.camera.flyTo({ destination: Cesium.Cartesian3.fromDegrees(selectedBase.lon, selectedBase.lat, 15000), duration: 1.5 });
}

function detSearch() {
    if (!selectedBase) return;
    document.getElementById('si').value = selectedBase.name;
    doSearch();
}

/* ═══ COUNTRY FILTER ═══ */
function filterCountry(c, btn) {
    countryFilter = c;
    document.querySelectorAll('.sfc').forEach(b => b.classList.remove('on'));
    btn.classList.add('on');
    /* Refresh all active layers */
    activeFilters.forEach(type => { removeEntities(type); showBases(type); });
}

/* ═══ MILITARY BALANCE ═══ */
function runBalance() {
    const a = document.getElementById('bal-a').value;
    const b = document.getElementById('bal-b').value;
    const countA = allBases.filter(x => x.country === a);
    const countB = allBases.filter(x => x.country === b);
    const types = ['air_base', 'naval_base', 'military_base', 'nuclear', 'missile_test'];
    const labels = ['Air Bases', 'Naval', 'Mil/Army', 'Nuclear', 'Missile/Space'];
    let html = '<table style="width:100%;font-size:10px;border-collapse:collapse">';
    html += `<tr style="border-bottom:1px solid var(--border)"><th style="text-align:left;padding:4px;color:var(--dim)">Type</th><th style="text-align:center;padding:4px;color:#00d4ff">${a}</th><th style="text-align:center;padding:4px;color:#ff8800">${b}</th></tr>`;
    types.forEach((t, i) => {
        const ca = countA.filter(x => x.type === t).length;
        const cb = countB.filter(x => x.type === t).length;
        const winner = ca > cb ? '#00ff88' : cb > ca ? '#ff4444' : 'var(--dim)';
        html += `<tr style="border-bottom:1px solid rgba(255,255,255,.03)"><td style="padding:4px;color:var(--dim)">${labels[i]}</td><td style="text-align:center;padding:4px;color:${ca >= cb ? '#00ff88' : '#ff4444'};font-weight:700">${ca}</td><td style="text-align:center;padding:4px;color:${cb >= ca ? '#00ff88' : '#ff4444'};font-weight:700">${cb}</td></tr>`;
    });
    const ta = countA.length, tb = countB.length;
    html += `<tr style="border-top:2px solid var(--border)"><td style="padding:4px;font-weight:700;color:var(--text)">TOTAL</td><td style="text-align:center;padding:4px;font-weight:700;color:#00d4ff">${ta}</td><td style="text-align:center;padding:4px;font-weight:700;color:#ff8800">${tb}</td></tr></table>`;
    document.getElementById('bal-result').innerHTML = html;
}

/* ═══ CLOCK & HUD ═══ */
function startClock() {
    setInterval(() => {
        const now = new Date();
        document.getElementById('clock').textContent = 'UTC ' + now.toISOString().substr(11, 8);
    }, 1000);
}

let fpsFrames = 0, fpsLast = performance.now();
function updateHud() {
    fpsFrames++;
    const now = performance.now();
    if (now - fpsLast >= 1000) {
        document.getElementById('sb-fps').textContent = fpsFrames + ' fps';
        fpsFrames = 0; fpsLast = now;
    }
    try {
        const cam = viewer.camera.positionCartographic;
        if (cam) {
            const lat = Cesium.Math.toDegrees(cam.latitude).toFixed(2);
            const lon = Cesium.Math.toDegrees(cam.longitude).toFixed(2);
            document.getElementById('coord-display').textContent = `${lat}°N ${lon}°E`;

            // Toggle satellites based on zoom altitude
            const isZoomedOut = cam.height > 6000000;
            if (window._lastZoomedOut !== isZoomedOut) {
                window._lastZoomedOut = isZoomedOut;
                if (satEntities) satEntities.forEach(s => s.show = isZoomedOut);
            }
        }
    } catch (e) { }
}

/* ═══ BOOT ═══ */
init();

/* ═══ LIVE OSINT FETCH (30k+ BASES) ═══ */
async function loadLiveBases() {
    try {
        console.log('Fetching live global bases via Overpass API...');
        const query = '[out:json][timeout:25];node["military"="base"];out center;';
        const res = await fetch('https://overpass-api.de/api/interpreter', {
            method: 'POST',
            body: 'data=' + encodeURIComponent(query),
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
        });
        const data = await res.json();

        const overpassBases = data.elements.filter(e => e.lat && e.lon).map(e => ({
            id: 'op_' + e.id,
            name: (e.tags && (e.tags.name || e.tags.name_en || e.tags.description)) || 'Military Installation (OSINT)',
            lat: e.lat,
            lon: e.lon,
            type: 'military_base',
            country: 'Global OSINT',
            status: 'active',
            desc: 'Live fetched from OSINT'
        }));

        // Merge with allBases
        allBases = allBases.concat(overpassBases);
        document.getElementById('sb-bases').textContent = 'Bases: ~' + allBases.length;
        document.getElementById('st-bases').textContent = '~' + allBases.length;

        // Refresh military base layer if it's currently active to display the 30k+ bases
        if (activeFilters.has('military_base')) {
            const btn = document.getElementById('lb-military');
            toggleLayer('military_base', btn); // off
            toggleLayer('military_base', btn); // on
        }
        console.log(`Loaded ${overpassBases.length} live bases. Total: ${allBases.length}`);
    } catch (e) {
        console.error('Failed to load live bases', e);
    }
}

/* ═══ AI CHAT ═══ */
async function sendAIQuery() {
    const input = document.getElementById('ai-input');
    const msg = input.value.trim();
    if (!msg) return;
    input.value = '';

    const msgs = document.getElementById('ai-messages');
    msgs.innerHTML += `<div style="align-self:flex-end;color:#fff;background:rgba(255,255,255,0.1);padding:6px;border-radius:4px;max-width:85%;word-wrap:break-word">${msg}</div>`;
    msgs.scrollTop = msgs.scrollHeight;

    const loadId = 'ai-load-' + Date.now();
    msgs.innerHTML += `<div id="${loadId}" style="align-self:flex-start;color:var(--dim);font-size:10px;">Processing...</div>`;
    msgs.scrollTop = msgs.scrollHeight;

    try {
        const res = await fetch('/api/v1/ai/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: msg, context: `Looking at ${selectedBase ? selectedBase.name : 'globe'}` })
        });
        const data = await res.json();
        document.getElementById(loadId).remove();
        let reply = data.response || 'No response';
        reply = reply.replace(/\*\*(.*?)\*\*/g, '<b>$1</b>').replace(/\n/g, '<br>');
        msgs.innerHTML += `<div style="align-self:flex-start;color:var(--accent);background:rgba(0,212,255,0.05);padding:6px;border-radius:4px;border:1px solid rgba(0,212,255,0.1);max-width:90%;line-height:1.4;word-wrap:break-word">${reply}</div>`;
        msgs.scrollTop = msgs.scrollHeight;
    } catch (e) {
        document.getElementById(loadId).remove();
        msgs.innerHTML += `<div style="align-self:flex-start;color:#ff3333;padding:6px;">Error connecting to AI.</div>`;
    }
}

/* ═══ SATELLITES ═══ */

function getSatPositionProperty(satrec) {
    const property = new Cesium.SampledPositionProperty();
    const now = new Date();
    // Pre-calculate 90 minutes (1 orbit) at 2-minute intervals starting from 10 mins ago
    for (let i = -10; i <= 90; i += 2) {
        const time = new Date(now.getTime() + i * 60000);
        try {
            const positionAndVelocity = satellite.propagate(satrec, time);
            if (positionAndVelocity.position && positionAndVelocity.position.x !== undefined) {
                const gmst = satellite.gstime(time);
                const positionGd = satellite.eciToGeodetic(positionAndVelocity.position, gmst);
                const lon = Cesium.Math.toDegrees(positionGd.longitude);
                const lat = Cesium.Math.toDegrees(positionGd.latitude);
                const alt = positionGd.height * 1000;
                if (!isNaN(lon) && !isNaN(lat) && !isNaN(alt)) {
                    property.addSample(Cesium.JulianDate.fromDate(time), Cesium.Cartesian3.fromDegrees(lon, lat, alt));
                }
            }
        } catch (e) { }
    }
    return property;
}

function toggleSatellites(el) {
    if (satEntities.length > 0) {
        satEntities.forEach(e => viewer.entities.remove(e));
        satEntities = [];
        el.classList.remove('on');
        document.getElementById('lc-sats').textContent = '—';
        if (selectedBase && selectedBase._isSat) {
            viewer.entities.remove(selectedBase._orbitPath);
            selectedBase = null;
        }
        return;
    }
    el.classList.add('on');
    renderSatellites();
}

function filterSats(f, btn) {
    satFilter = f;
    document.querySelectorAll('#sat-filters .sfc').forEach(b => b.classList.remove('on'));
    btn.classList.add('on');
    if (satEntities.length > 0) {
        satEntities.forEach(e => viewer.entities.remove(e));
        satEntities = [];
        renderSatellites();
    }
}

/* Create realistic satellite SVG billboard icon */
function createSatelliteIcon(color) {
    const c = document.createElement('canvas');
    c.width = 32; c.height = 32;
    const ctx = c.getContext('2d');
    // Glow effect
    ctx.shadowColor = color;
    ctx.shadowBlur = 8;
    // Solar panel left
    ctx.fillStyle = '#3355aa';
    ctx.fillRect(2, 12, 10, 8);
    ctx.strokeStyle = '#88bbff';
    ctx.lineWidth = 0.5;
    ctx.strokeRect(2, 12, 10, 8);
    // Solar panel grid lines
    ctx.beginPath(); ctx.moveTo(7, 12); ctx.lineTo(7, 20); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(2, 16); ctx.lineTo(12, 16); ctx.stroke();
    // Body (center)
    ctx.fillStyle = '#cccccc';
    ctx.fillRect(13, 10, 6, 12);
    ctx.strokeStyle = '#ffffff';
    ctx.lineWidth = 0.8;
    ctx.strokeRect(13, 10, 6, 12);
    // Antenna dish
    ctx.beginPath();
    ctx.arc(16, 8, 3, Math.PI, 2 * Math.PI);
    ctx.strokeStyle = '#eeeeee';
    ctx.lineWidth = 1;
    ctx.stroke();
    ctx.beginPath(); ctx.moveTo(16, 8); ctx.lineTo(16, 10); ctx.stroke();
    // Solar panel right
    ctx.fillStyle = '#3355aa';
    ctx.fillRect(20, 12, 10, 8);
    ctx.strokeStyle = '#88bbff';
    ctx.lineWidth = 0.5;
    ctx.strokeRect(20, 12, 10, 8);
    ctx.beginPath(); ctx.moveTo(25, 12); ctx.lineTo(25, 20); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(20, 16); ctx.lineTo(30, 16); ctx.stroke();
    // Status LED
    ctx.fillStyle = color;
    ctx.beginPath(); ctx.arc(16, 16, 1.5, 0, 2 * Math.PI); ctx.fill();
    return c.toDataURL();
}

// Cache satellite icons by color
const _satIconCache = {};
function getSatIcon(color) {
    if (!_satIconCache[color]) _satIconCache[color] = createSatelliteIcon(color);
    return _satIconCache[color];
}

function renderSatellites() {
    let filtered = allSats;
    if (satFilter !== 'ALL') {
        if (['US', 'CN', 'RU', 'IN', 'FR', 'UK', 'IL'].includes(satFilter)) {
            filtered = allSats.filter(s => s.country === satFilter);
        } else if (['MILITARY', 'OPTICAL', 'SAR', 'SIGINT'].includes(satFilter)) {
            filtered = allSats.filter(s => s.type === satFilter);
        } else {
            filtered = allSats.filter(s => (s.name || '').toUpperCase().includes(satFilter));
        }
    }

    document.getElementById('lc-sats').textContent = 'Loading...';
    let i = 0;
    const batch = 100;
    viewer.clock.shouldAnimate = true;

    function processBatch() {
        if (!satEntities && satFilter === 'ALL') return;
        const end = Math.min(i + batch, filtered.length);
        for (; i < end; i++) {
            const s = filtered[i];
            const satrec = satellite.twoline2satrec(s.line1, s.line2);
            const posProp = getSatPositionProperty(satrec);

            let color = '#00d4ff';
            if (s.type === 'MILITARY' || s.type === 'SIGINT') color = '#ff3333';
            else if (s.type === 'SAR' || s.type === 'OPTICAL') color = '#ffcc00';
            else if (s.country === 'CN') color = '#ff8800';
            else if ((s.name || '').includes('STARLINK')) color = '#aaaaaa';

            const ent = viewer.entities.add({
                position: posProp,
                show: window._lastZoomedOut !== false,
                billboard: {
                    image: getSatIcon(color),
                    width: 18,
                    height: 18,
                    eyeOffset: new Cesium.Cartesian3(0, 0, -100)
                },
                path: {
                    leadTime: 0,
                    trailTime: 600,
                    width: 1,
                    material: Cesium.Color.fromCssColorString(color),
                    resolution: 60
                },
                properties: { satData: s, satrec: satrec, posProp: posProp }
            });
            satEntities.push(ent);
        }
        document.getElementById('lc-sats').textContent = i;
        if (i < filtered.length) {
            requestAnimationFrame(processBatch);
        } else {
            document.getElementById('lc-sats').textContent = satEntities.length;
        }
    }
    processBatch();
}

async function showSatDetail(s, satrec, posProp) {
    selectedBase = { _isSat: true, name: s.name };
    switchTab('detail', document.getElementById('detail-tab-btn'));
    document.getElementById('det-empty').style.display = 'none';
    document.getElementById('det-content').style.display = 'block';
    const cleanName = s.name.replace(/^SAT-/, '');
    document.getElementById('det-title').textContent = cleanName;
    const badge = document.getElementById('det-badge');
    badge.style.background = '#00d4ff22';
    badge.style.color = '#00d4ff';
    badge.textContent = '🛰 ORBITAL TRK';

    // Draw trail arc
    if (selectedBase._orbitPath) viewer.entities.remove(selectedBase._orbitPath);
    selectedBase._orbitPath = viewer.entities.add({
        position: posProp,
        path: {
            leadTime: 0,
            trailTime: 5400, // 90 mins arc
            width: 2,
            material: Cesium.Color.CYAN,
            resolution: 120
        }
    });

    const now = new Date();
    const pv = satellite.propagate(satrec, now);
    let vel = 0, alt = 0, lat = 0, lon = 0;
    if (pv.velocity && pv.position) {
        vel = Math.sqrt(pv.velocity.x ** 2 + pv.velocity.y ** 2 + pv.velocity.z ** 2).toFixed(2);
        const gmst = satellite.gstime(now);
        const geo = satellite.eciToGeodetic(pv.position, gmst);
        alt = geo.height.toFixed(1);
        lat = Cesium.Math.toDegrees(geo.latitude).toFixed(2);
        lon = Cesium.Math.toDegrees(geo.longitude).toFixed(2);
    }

    let rows = '';
    const addRow = (l, v) => { if (v) rows += `<div class="det-row"><span class="det-lbl">${l}</span><span class="det-val">${v}</span></div>`; };
    addRow('NORAD ID', s.norad_id);

    const satCountries = { 'US': 'United States', 'CIS': 'Russia', 'PRC': 'China', 'IN': 'India', 'FR': 'France', 'UK': 'United Kingdom', 'IL': 'Israel', 'EU': 'European Union', 'JP': 'Japan' };
    addRow('Country', satCountries[s.country] || s.country);
    addRow('Class', s.type);
    addRow('Sub-point', `${lat}°N, ${lon}°E`);
    addRow('Live Altitude', alt + ' km');
    addRow('Live Velocity', vel + ' km/s');

    document.getElementById('det-rows').innerHTML = rows + '<div style="color:var(--dim);margin-top:10px;font-size:10px" id="sat-wiki-fetch">Fetching live intelligence payload...</div>';

    try {
        const term = cleanName.replace(/-\d+$/, '').replace(/\d+$/, '').trim();
        const res = await fetch(`https://en.wikipedia.org/api/rest_v1/page/summary/${encodeURIComponent(term)}`);
        if (res.ok) {
            const data = await res.json();
            if (data.extract) {
                document.getElementById('sat-wiki-fetch').innerHTML = `<b>Live Object Summary:</b><br>${data.extract}`;
                return;
            }
        }
        document.getElementById('sat-wiki-fetch').innerHTML = '<b>SIGINT Signature:</b><br>Encrypted military/commercial bus. No unclassified summary available for this payload telemetry.';
    } catch (e) { }
}

/* ═══ CYBER ATTACK ENGINE ═══ */

let cyberAttacks = [];
let cyberFilter = 'ALL';
let cyberArcEntities = [];
let cyberWS = null;
let cyberArcsEnabled = true;

window.toggleCyberArcs = function (btn) {
    cyberArcsEnabled = !cyberArcsEnabled;
    btn.classList.toggle('on', cyberArcsEnabled);
    if (!cyberArcsEnabled) {
        // Clear immediately
        cyberArcEntities.forEach(e => { try { viewer.entities.remove(e); } catch (ex) { } });
        cyberArcEntities = [];
    }
};

function connectCyberWS() {
    const proto = location.protocol === 'https:' ? 'wss' : 'ws';
    const wsUrl = `${proto}://${location.host}/ws/cyber`;
    try {
        cyberWS = new WebSocket(wsUrl);
        cyberWS.onopen = () => {
            console.log('Cyber WS connected');
            const feed = document.getElementById('cyber-feed');
            if (feed) feed.innerHTML = '<div style="color:#00ff88;font-size:9px">🟢 SIGINT feed connected. Monitoring global cyber threats...</div>';
        };
        cyberWS.onmessage = (evt) => {
            try {
                const msg = JSON.parse(evt.data);
                if (msg.type === 'history' && Array.isArray(msg.data)) {
                    cyberAttacks = msg.data;
                    renderCyberFeed();
                    updateCyberStats();
                } else if (msg.type === 'attack') {
                    cyberAttacks.unshift(msg.data);
                    if (cyberAttacks.length > 200) cyberAttacks.pop();
                    renderCyberFeed();
                    updateCyberStats();
                    drawCyberArc(msg.data);
                }
            } catch (e) { }
        };
        cyberWS.onclose = () => {
            console.log('Cyber WS closed, reconnecting in 5s...');
            setTimeout(connectCyberWS, 5000);
        };
        cyberWS.onerror = () => {
            // Fallback: fetch attacks via REST
            fetchCyberREST();
        };
    } catch (e) {
        fetchCyberREST();
    }
}

async function fetchCyberREST() {
    try {
        const res = await fetch(`${API}/api/v1/cyber/attacks?limit=50`);
        if (res.ok) {
            const data = await res.json();
            cyberAttacks = data.attacks || [];
            renderCyberFeed();
            updateCyberStats();
        }
    } catch (e) { console.log('Cyber REST fallback failed:', e); }
    // Fetch stats
    try {
        const res = await fetch(`${API}/api/v1/cyber/stats`);
        if (res.ok) {
            const stats = await res.json();
            if (stats.total_attacks) document.getElementById('cyber-total').textContent = stats.total_attacks;
            if (stats.unique_types) document.getElementById('cyber-types').textContent = stats.unique_types;
            if (stats.unique_countries) document.getElementById('cyber-countries').textContent = stats.unique_countries;
        }
    } catch (e) { }
}

function updateCyberStats() {
    const types = new Set(), countries = new Set();
    cyberAttacks.forEach(a => { types.add(a.type); countries.add(a.tgt_code); countries.add(a.src_code); });
    document.getElementById('cyber-total').textContent = cyberAttacks.length;
    document.getElementById('cyber-types').textContent = types.size;
    document.getElementById('cyber-countries').textContent = countries.size;
}

function renderCyberFeed() {
    const feed = document.getElementById('cyber-feed');
    if (!feed) return;
    let filtered = cyberAttacks;
    if (cyberFilter !== 'ALL') {
        filtered = cyberAttacks.filter(a => a.type === cyberFilter);
    }
    if (filtered.length === 0) {
        feed.innerHTML = '<div style="color:var(--dim)">No attacks matching filter.</div>';
        return;
    }
    const severityColors = { critical: '#ff0044', high: '#ff3333', medium: '#ff8800', low: '#ffcc00' };
    feed.innerHTML = filtered.slice(0, 60).map(a => {
        const atkTime = a.ts ? new Date(a.ts).toLocaleTimeString() : '--';
        const sevColor = severityColors[a.severity] || '#ff8800';
        return `<div style="background:rgba(255,255,255,0.02);border:1px solid rgba(${a.color ? '255,51,51' : '255,255,255'},0.08);border-left:3px solid ${a.color || sevColor};border-radius:4px;padding:6px 8px;margin-bottom:4px;cursor:pointer" onclick="showCyberDetail(${cyberAttacks.indexOf(a)})">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:3px">
                <span style="color:${a.color || sevColor};font-weight:700;font-size:9px">${a.type}</span>
                <span style="color:var(--dim);font-size:8px">${atkTime}</span>
            </div>
            <div style="font-size:9px;color:var(--text)">
                <span style="color:#ff8800">${a.src || '?'}</span>
                <span style="color:var(--dim)"> → </span>
                <span style="color:#00d4ff">${a.tgt || '?'}</span>
            </div>
            <div style="display:flex;gap:6px;margin-top:3px;font-size:8px;color:var(--dim)">
                <span>Port: ${a.port || '—'}</span>
                <span>IP: ${a.ip || '—'}</span>
                <span style="color:${sevColor};text-transform:uppercase;font-weight:600">${a.severity || '—'}</span>
            </div>
        </div>`;
    }).join('');
}

function filterCyber(f, btn) {
    cyberFilter = f;
    document.querySelectorAll('#tab-cyber .sfc').forEach(b => b.classList.remove('on'));
    btn.classList.add('on');
    renderCyberFeed();
}

function showCyberDetail(idx) {
    const a = cyberAttacks[idx];
    if (!a) return;
    switchTab('detail', document.getElementById('detail-tab-btn'));
    document.getElementById('det-empty').style.display = 'none';
    document.getElementById('det-content').style.display = 'block';
    document.getElementById('det-title').textContent = `${a.type} Attack`;
    const badge = document.getElementById('det-badge');
    const sevColors = { critical: '#ff0044', high: '#ff3333', medium: '#ff8800', low: '#ffcc00' };
    badge.style.background = (sevColors[a.severity] || '#ff8800') + '22';
    badge.style.color = sevColors[a.severity] || '#ff8800';
    badge.textContent = (a.severity || 'HIGH').toUpperCase();

    const detMap = document.getElementById('detail-map');
    if (detMap) detMap.innerHTML = '';

    let rows = '';
    const addRow = (l, v) => { if (v) rows += `<div class="det-row"><span class="det-lbl">${l}</span><span class="det-val">${v}</span></div>`; };
    addRow('Attack ID', a.id);
    addRow('Type', a.type);
    addRow('Source', `${a.src} (${a.src_code})`);
    addRow('Target', `${a.tgt} (${a.tgt_code})`);
    addRow('Source IP', a.ip);
    addRow('Port', a.port);
    addRow('Payload', a.payload_kb ? a.payload_kb + ' KB' : null);
    addRow('Severity', a.severity?.toUpperCase());
    addRow('Timestamp', a.ts ? new Date(a.ts).toLocaleString() : null);
    document.getElementById('det-rows').innerHTML = rows;

    // Fly camera to show the attack arc
    if (a.src_lat && a.tgt_lat) {
        const midLat = (a.src_lat + a.tgt_lat) / 2;
        const midLng = (a.src_lng + a.tgt_lng) / 2;
        viewer.camera.flyTo({
            destination: Cesium.Cartesian3.fromDegrees(midLng, midLat, 8000000),
            duration: 1.5
        });
    }
}

function drawCyberArc(atk) {
    if (!cyberArcsEnabled || !atk.src_lat || !atk.tgt_lat || !viewer) return;

    // Create animated arc between source and target
    const positions = [];
    const steps = 40;
    for (let i = 0; i <= steps; i++) {
        const t = i / steps;
        const lat = atk.src_lat + (atk.tgt_lat - atk.src_lat) * t;
        const lng = atk.src_lng + (atk.tgt_lng - atk.src_lng) * t;
        const alt = Math.sin(t * Math.PI) * 800000; // Arc height
        positions.push(Cesium.Cartesian3.fromDegrees(lng, lat, alt));
    }

    const color = Cesium.Color.fromCssColorString(atk.color || '#ff3333');

    const ent = viewer.entities.add({
        polyline: {
            positions: positions,
            width: 2,
            material: color,
            arcType: Cesium.ArcType.NONE
        }
    });
    cyberArcEntities.push(ent);

    // Auto-remove after 12 seconds to prevent clutter
    setTimeout(() => {
        try { viewer.entities.remove(ent); } catch (e) { }
        cyberArcEntities = cyberArcEntities.filter(e2 => e2 !== ent);
    }, 12000);
}

/* ═══════════════════════════════════════════════════════════════════════
   BOTTOM DASHBOARD — Live News / Live Webcams / AI Insights
   ═══════════════════════════════════════════════════════════════════════ */

let _dashOpen = false;
window.toggleDashPanel = function () {
    const dp = document.getElementById('dash-panel');
    const btn = document.getElementById('dash-toggle-btn');
    _dashOpen = !_dashOpen;
    dp.classList.toggle('open', _dashOpen);
    btn.textContent = _dashOpen ? '▼ CLOSE DASHBOARD' : '▲ LIVE DASHBOARD';

    // Lazy-load iframes only when opened for the first time
    if (_dashOpen && !dp._loaded) {
        dp._loaded = true;
        loadAIInsights();
    }
};

/* --- News Channel Switching --- */
const newsChannels = {
    'BLOOMBERG': { type: 'channel', id: 'UCIALMKvObZNtJ68-rmLjXhA' },
    'SKYNEWS': { type: 'channel', id: 'UCoMdktPbSTixAyNGwb-UYkQ' },
    'CNN': { type: 'channel', id: 'UCupvZG-5ko_eiXAupbDfxWw' },
    'AL JAZEERA': { type: 'channel', id: 'UCNye-wNBqNL5ZzHSJj3l8Bg' },
    'FRANCE24': { type: 'channel', id: 'UCQfwfsi5VrQ8yKZ-UWmAEFg' },
    'DW NEWS': { type: 'channel', id: 'UCknLrEdhRCp1aegoMqRaCZg' },
    'WION': { type: 'channel', id: 'UC_gUM8rL-Lrg6O3adPW9K1g' }
};

function getYTLiveUrl(entry) {
    if (entry.type === 'channel') return `https://www.youtube.com/embed/live_stream?channel=${entry.id}&autoplay=1&mute=1`;
    return `https://www.youtube.com/embed/${entry.id}?autoplay=1&mute=1`;
}

document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('#dash-panel .news .sub-tabs .stb').forEach(btn => {
        btn.addEventListener('click', function () {
            document.querySelectorAll('#dash-panel .news .sub-tabs .stb').forEach(b => b.classList.remove('on'));
            this.classList.add('on');
            const channel = this.textContent.trim();
            const entry = newsChannels[channel];
            if (entry) {
                document.getElementById('news-iframe').src = getYTLiveUrl(entry);
            }
        });
    });
});

/* --- Webcam Region Switching --- */
const webcamRegions = {
    hotspots: [
        { label: '📍 AL JAZEERA LIVE', ch: 'UCNye-wNBqNL5ZzHSJj3l8Bg' },
        { label: '📍 SKY NEWS LIVE', ch: 'UCoMdktPbSTixAyNGwb-UYkQ' },
        { label: '📍 FRANCE 24 LIVE', ch: 'UCQfwfsi5VrQ8yKZ-UWmAEFg' },
        { label: '📍 DW NEWS LIVE', ch: 'UCknLrEdhRCp1aegoMqRaCZg' }
    ],
    europe: [
        { label: '📍 EURONEWS', ch: 'UCW2QcKZiU8aUGg4yxCIditg' },
        { label: '📍 DW NEWS', ch: 'UCknLrEdhRCp1aegoMqRaCZg' },
        { label: '📍 SKY NEWS', ch: 'UCoMdktPbSTixAyNGwb-UYkQ' },
        { label: '📍 FRANCE 24', ch: 'UCQfwfsi5VrQ8yKZ-UWmAEFg' }
    ],
    americas: [
        { label: '📍 NBC NEWS', ch: 'UCeY0bbntWzzVIaj2z3QigXg' },
        { label: '📍 ABC NEWS', ch: 'UCBi2mrWuNuyYy4gbM6fU18Q' },
        { label: '📍 CBS NEWS', ch: 'UC8p1vwvWtl6T73JiExfWs1g' },
        { label: '📍 FOX 5 DC', ch: 'UCpSPfiFG8_2SjuxghKMjcEQ' }
    ],
    asia: [
        { label: '📍 WION', ch: 'UC_gUM8rL-Lrg6O3adPW9K1g' },
        { label: '📍 CNA', ch: 'UCo8bcnLyZH8tBIH9V1mLgqQ' },
        { label: '📍 NHK WORLD', ch: 'UCPLJplhkId70VXq7n4rBwTw' },
        { label: '📍 AL JAZEERA', ch: 'UCNye-wNBqNL5ZzHSJj3l8Bg' }
    ],
    space: [
        { label: '📍 NASA TV', ch: 'UCLA_DiR1FfKNvjuUpBHmylQ' },
        { label: '📍 SPACE X', ch: 'UCtI0Hodo5o5dUb67FeUjDeA' },
        { label: '📍 ESA', ch: 'UCIBaDdAbGlFDeS33shmlD0A' },
        { label: '📍 TMRO SPACE', ch: 'UCDZkgB6BmPo75d0l0AeiGMg' }
    ]
};

window.setWebcamRegion = function (region) {
    const cams = webcamRegions[region] || webcamRegions.hotspots;
    const grid = document.getElementById('webcam-grid');
    grid.innerHTML = cams.map(c => `
        <div>
            <div class="vid-label">${c.label}</div>
            <iframe src="https://www.youtube.com/embed/live_stream?channel=${c.ch}&autoplay=1&mute=1" allow="autoplay;encrypted-media" loading="lazy"></iframe>
        </div>
    `).join('');

    // Toggle button states
    document.querySelectorAll('#dash-panel .webcams .sub-tabs .stb').forEach(b => {
        b.classList.toggle('on', b.textContent.trim().toLowerCase() === region);
    });
};

/* --- AI Insights Feed --- */
async function loadAIInsights() {
    try {
        const res = await fetch('/api/v1/news/feed');
        if (res.ok) {
            const data = await res.json();
            const items = data.items || data || [];
            if (items.length > 0) {
                // World Brief
                const briefEl = document.getElementById('ai-brief');
                if (briefEl) {
                    const topItems = items.slice(0, 3);
                    briefEl.innerHTML = topItems.map(item =>
                        `<div style="margin-bottom:6px">• ${item.title || item.headline || 'Breaking report'}</div>`
                    ).join('');
                }

                // Live Intel
                const intelEl = document.getElementById('ai-live-intel');
                if (intelEl) {
                    const liveItems = items.slice(3, 8);
                    intelEl.innerHTML = liveItems.map(item =>
                        `<div style="margin-bottom:5px;border-left:2px solid var(--border);padding-left:6px">
                            <span style="color:var(--dim);font-size:8px">${item.source || 'OSINT'}</span><br>
                            ${item.title || item.headline || '—'}
                        </div>`
                    ).join('');
                }
            }
        }
    } catch (e) { }

    // Strategic posture from conflicts
    const postureEl = document.getElementById('ai-posture-list');
    if (postureEl && conflictsData.length > 0) {
        postureEl.innerHTML = conflictsData.slice(0, 5).map(c => {
            const level = c.intensity === 'extreme' || c.intensity === 'critical' ? 'CRIT' : c.intensity === 'high' ? 'HIGH' : 'ELEV';
            const col = level === 'CRIT' ? '#ff3333' : level === 'HIGH' ? '#ff8800' : '#ffcc00';
            return `<div style="display:flex;justify-content:space-between;margin-bottom:5px">
                <span style="color:var(--text)">${c.name}</span>
                <span style="background:${col}22;color:${col};padding:1px 5px;border-radius:3px;font-size:8px">${level}</span>
            </div>`;
        }).join('');
    }
}

/* ═══════════════════════════════════════════════════════════════════════
   COUNTRY INTELLIGENCE PANEL
   ═══════════════════════════════════════════════════════════════════════ */

const countryFlags = {
    'India': '🇮🇳', 'China': '🇨🇳', 'Russia': '🇷🇺', 'United States': '🇺🇸',
    'Pakistan': '🇵🇰', 'Israel': '🇮🇱', 'Iran': '🇮🇷', 'Turkey': '🇹🇷',
    'France': '🇫🇷', 'Germany': '🇩🇪', 'Ukraine': '🇺🇦', 'Japan': '🇯🇵',
    'South Korea': '🇰🇷', 'North Korea': '🇰🇵', 'United Kingdom': '🇬🇧',
    'Saudi Arabia': '🇸🇦', 'Brazil': '🇧🇷', 'Australia': '🇦🇺',
    'Canada': '🇨🇦', 'Italy': '🇮🇹', 'Egypt': '🇪🇬', 'Indonesia': '🇮🇩',
    'Mexico': '🇲🇽', 'Nigeria': '🇳🇬', 'South Africa': '🇿🇦',
    'Taiwan': '🇹🇼', 'Thailand': '🇹🇭', 'Vietnam': '🇻🇳', 'Myanmar': '🇲🇲',
    'Syria': '🇸🇾', 'Iraq': '🇮🇶', 'Afghanistan': '🇦🇫', 'Yemen': '🇾🇪',
    'Sudan': '🇸🇩', 'Libya': '🇱🇾', 'Somalia': '🇸🇴', 'Ethiopia': '🇪🇹',
    'Poland': '🇵🇱', 'Spain': '🇪🇸', 'Netherlands': '🇳🇱', 'Belgium': '🇧🇪',
    'Sweden': '🇸🇪', 'Norway': '🇳🇴', 'Finland': '🇫🇮', 'Greece': '🇬🇷'
};

window.closeCountryPanel = function () {
    document.getElementById('country-panel').classList.remove('open');
};

async function openCountryPanel(countryName, countryCode) {
    const panel = document.getElementById('country-panel');
    panel.classList.add('open');

    // Header
    document.getElementById('cp-flag').textContent = countryFlags[countryName] || '🌐';
    document.getElementById('cp-name').textContent = countryName;
    document.getElementById('cp-sub').textContent = `${countryCode || '—'} • Country Intelligence`;
    document.getElementById('cp-updated').textContent = `Updated ${new Date().toLocaleString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}`;

    // Calculate Instability Index from our data
    let unrest = 10, conflict = 0, security = 20, info = 8;

    // Check if country has active conflicts
    const activeConflicts = conflictsData.filter(c => {
        const parties = (c.parties || []).join(' ').toLowerCase();
        return parties.includes(countryName.toLowerCase()) || (c.name || '').toLowerCase().includes(countryName.toLowerCase());
    });

    if (activeConflicts.length > 0) {
        conflict = Math.min(50, activeConflicts.length * 20);
        unrest = Math.min(50, 25 + activeConflicts.length * 10);
    }

    // Check military bases in country
    const basesInCountry = allBases.filter(b =>
        (b.country || '').toLowerCase().includes(countryName.toLowerCase())
    );
    security = Math.min(50, Math.max(10, basesInCountry.length));

    // Check cyber attacks targeting this country
    const cyberHits = cyberAttacks.filter(a =>
        (a.tgt || '').toLowerCase().includes(countryName.toLowerCase()) ||
        (a.tgt_code || '').toLowerCase() === (countryCode || '').toLowerCase()
    );
    info = Math.min(50, cyberHits.length * 2 + 5);

    const total = Math.min(100, Math.round(unrest + conflict + security / 2 + info / 2));
    const trend = conflict > 20 ? '↑ volatile' : conflict > 0 ? '→ elevated' : '→ stable';
    const scoreColor = total > 70 ? '#ff3333' : total > 40 ? '#ff8800' : '#ffcc00';

    document.getElementById('cp-score').innerHTML = `<span style="color:${scoreColor}">${total}</span><span class="max">/100</span>`;
    document.getElementById('cp-trend').textContent = trend;

    document.getElementById('cp-unrest').style.width = (unrest * 2) + '%';
    document.getElementById('cp-unrest-val').textContent = unrest;
    document.getElementById('cp-conflict').style.width = (conflict * 2) + '%';
    document.getElementById('cp-conflict-val').textContent = conflict;
    document.getElementById('cp-security').style.width = (security * 2) + '%';
    document.getElementById('cp-security-val').textContent = security;
    document.getElementById('cp-info').style.width = (info * 2) + '%';
    document.getElementById('cp-info-val').textContent = info;

    // Active Signals
    const signals = [];
    if (activeConflicts.length > 0) signals.push(`<span style="background:rgba(255,51,51,0.2);color:#ff3333;padding:2px 6px;border-radius:3px;font-size:9px">⚔ ${activeConflicts.length} Conflicts</span>`);
    if (cyberHits.length > 0) signals.push(`<span style="background:rgba(170,68,255,0.2);color:#aa44ff;padding:2px 6px;border-radius:3px;font-size:9px">💀 ${cyberHits.length} Cyber Attacks</span>`);
    if (basesInCountry.length > 10) signals.push(`<span style="background:rgba(0,212,255,0.2);color:#00d4ff;padding:2px 6px;border-radius:3px;font-size:9px">🏗 ${basesInCountry.length} Mil. Facilities</span>`);
    document.getElementById('cp-signals').innerHTML = signals.length > 0 ? signals.join(' ') : '<span style="color:var(--dim);font-size:10px">No recent high-severity signals.</span>';

    // Military Activity
    const milEl = document.getElementById('cp-military');
    const airBases = basesInCountry.filter(b => b.type === 'air_base').length;
    const navalBases = basesInCountry.filter(b => b.type === 'naval_base').length;
    const armyBases = basesInCountry.filter(b => b.type === 'military_base').length;
    milEl.innerHTML = `
        <div style="display:flex;justify-content:space-between;margin-bottom:5px"><span>Air Bases</span><span style="color:var(--text)">${airBases}</span></div>
        <div style="display:flex;justify-content:space-between;margin-bottom:5px"><span>Naval Bases</span><span style="color:var(--text)">${navalBases}</span></div>
        <div style="display:flex;justify-content:space-between;margin-bottom:5px"><span>Army / Ground</span><span style="color:var(--text)">${armyBases}</span></div>
        <div style="display:flex;justify-content:space-between;margin-bottom:5px"><span>Total Facilities</span><span style="color:var(--accent)">${basesInCountry.length}</span></div>
        <div style="margin-top:8px;color:var(--dim);font-size:9px">${basesInCountry.length > 0 ? `Nearest base: ${basesInCountry[0].name}` : 'No nearby bases in database.'}</div>
    `;

    // Top News for country (from Wikipedia current events)
    const newsEl = document.getElementById('cp-news');
    newsEl.innerHTML = '<span style="color:var(--dim)">Fetching...</span>';
    try {
        const nRes = await fetch(`https://en.wikipedia.org/api/rest_v1/page/summary/${encodeURIComponent(countryName)}`);
        if (nRes.ok) {
            const nd = await nRes.json();
            newsEl.innerHTML = `
                <div style="border:1px solid var(--border);border-radius:4px;padding:8px;margin-bottom:6px">
                    <div style="display:flex;gap:4px;margin-bottom:4px">
                        <span style="background:rgba(255,255,255,0.06);padding:1px 5px;border-radius:3px;font-size:8px;color:var(--dim)">Wiki</span>
                    </div>
                    <div style="color:var(--text);font-size:10px;line-height:1.5">${(nd.extract || '').substring(0, 300)}...</div>
                </div>
                ${nd.thumbnail ? `<img src="${nd.thumbnail.source}" style="width:100%;border-radius:4px;margin-top:4px;max-height:120px;object-fit:cover">` : ''}
            `;
        }
    } catch (e) {
        newsEl.innerHTML = '<span style="color:var(--dim)">Unable to fetch news.</span>';
    }

    // Economic indicators (from rest countries API)
    const econEl = document.getElementById('cp-econ');
    econEl.innerHTML = '<span style="color:var(--dim)">Loading...</span>';
    try {
        const eRes = await fetch(`https://restcountries.com/v3.1/name/${encodeURIComponent(countryName)}?fields=name,population,region,subregion,capital,currencies,languages,area`);
        if (eRes.ok) {
            const eData = await eRes.json();
            const c = eData[0];
            const cur = c.currencies ? Object.values(c.currencies).map(x => `${x.name} (${x.symbol || ''})`).join(', ') : '—';
            const langs = c.languages ? Object.values(c.languages).slice(0, 3).join(', ') : '—';
            econEl.innerHTML = `
                <div style="border:1px solid var(--border);border-radius:4px;padding:8px;margin-bottom:6px">
                    <div style="font-weight:700;color:var(--text);margin-bottom:4px">General Info</div>
                    <div>Region: ${c.region || '—'} / ${c.subregion || '—'}</div>
                    <div>Capital: ${(c.capital || []).join(', ') || '—'}</div>
                    <div>Population: ${c.population ? c.population.toLocaleString() : '—'}</div>
                    <div>Area: ${c.area ? c.area.toLocaleString() + ' km²' : '—'}</div>
                </div>
                <div style="border:1px solid var(--border);border-radius:4px;padding:8px">
                    <div style="font-weight:700;color:var(--text);margin-bottom:4px">Currency</div>
                    <div>${cur}</div>
                    <div style="margin-top:4px;font-weight:700;color:var(--text)">Languages</div>
                    <div>${langs}</div>
                </div>
            `;
        }
    } catch (e) {
        econEl.innerHTML = '<span style="color:var(--dim)">Unable to load economic data.</span>';
    }
}

// Intercept globe clicks on empty land to open country panel
const origOnLeftClick = onLeftClick;
function enhancedOnLeftClick(movement) {
    const pick = viewer.scene.pick(movement.position);

    // If we picked an entity or primitive with data, use the original handler
    if (Cesium.defined(pick)) {
        const id = pick.id;
        if (id && id.properties) {
            return origOnLeftClick(movement);
        }
        // Primitive with .id.properties (PointPrimitive/Label)
        if (id && id.properties && (id.properties.baseData || id.properties.satData || id.properties.conflictData || id.properties.nukeData)) {
            return origOnLeftClick(movement);
        }
    }

    // Otherwise try to resolve clicked position to a country via Nominatim
    const cartesian = viewer.camera.pickEllipsoid(movement.position, viewer.scene.globe.ellipsoid);
    if (!cartesian) return;

    const cartographic = Cesium.Cartographic.fromCartesian(cartesian);
    const lat = Cesium.Math.toDegrees(cartographic.latitude);
    const lon = Cesium.Math.toDegrees(cartographic.longitude);

    // Reverse geocode
    fetch(`https://nominatim.openstreetmap.org/reverse?lat=${lat}&lon=${lon}&format=json&zoom=3`)
        .then(r => r.json())
        .then(data => {
            if (data.address && data.address.country) {
                openCountryPanel(data.address.country, data.address.country_code?.toUpperCase());
            }
        })
        .catch(() => { });
}

// Replace the click handler
viewer.screenSpaceEventHandler.removeInputAction(Cesium.ScreenSpaceEventType.LEFT_CLICK);
viewer.screenSpaceEventHandler.setInputAction(enhancedOnLeftClick, Cesium.ScreenSpaceEventType.LEFT_CLICK);
