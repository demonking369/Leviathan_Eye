# Leviathan_Eye Data Schema v1.0

All data files live in `data/`. Each is valid JSON. Python programs load them via `data_manager.py`.

---

## bases.json

```json
{
  "schema_version": "1.0",
  "type": "military_bases",
  "last_updated": "<ISO-8601>",
  "sources": ["OSINT", "Satellite", "DoD", "CSIS", "FAS"],
  "data": [
    {
      "id":           "us01",
      "name":         "Andersen AFB",
      "lat":          13.583,
      "lng":          144.930,
      "type":         "airbase",
      "nation":       "us",
      "status":       "active",
      "personnel":    6000,
      "notes":        "Freetext OSINT notes.",
      "source":       "DoD",
      "last_verified":"2024-01-01",
      "confidence":   "high",
      "tags":         ["bomber", "strategic", "pacific"]
    }
  ]
}
```

### Field Definitions

| Field | Type | Values |
|---|---|---|
| id | string | Unique. Format: `{nation}{sequential}` |
| name | string | Common English name |
| lat / lng | float | WGS84 decimal degrees |
| type | string | `airbase` `naval` `submarine` `missile` `nuclear` `radar` `logistics` `drone` |
| nation | string | ISO2 lowercase: `us` `ru` `cn` `kp` `ir` `in` `il` `gb` `fr` `sa` `ae` `pk` `ua` `nato` |
| status | string | `active` `construction` `suspected` `decommissioned` `standby` |
| personnel | int | Estimated personnel, 0 if unknown |
| notes | string | Plain text OSINT notes |
| source | string | Primary source citation |
| last_verified | string | ISO-8601 date |
| confidence | string | `high` `medium` `low` |
| tags | array[string] | Free-form capability/context tags |

---

## conflicts.json

```json
{
  "schema_version": "1.0",
  "type": "conflict_zones",
  "last_updated": "<ISO-8601>",
  "data": [
    {
      "id":          "cf01",
      "name":        "Ukraine-Russia War",
      "lat":         48.5,
      "lng":         35.5,
      "radius":      300000,
      "type":        "major_war",
      "threat":      "critical",
      "started":     "2022-02-24",
      "description": "Freetext.",
      "parties":     ["Russia", "Ukraine"],
      "casualties":  "est. 500K+",
      "source":      "ACLED 2024",
      "last_updated":"2024-01-01"
    }
  ]
}
```

### type values
`major_war` `active` `frozen` `proxy` `civil_war` `terrorism` `tensions`

### threat values
`critical` `warning` `info`

---

## construction.json

```json
{
  "schema_version": "1.0",
  "type": "construction_sites",
  "last_updated": "<ISO-8601>",
  "data": [
    {
      "id":          "cs01",
      "name":        "Ream Naval Base Expansion",
      "lat":         10.533,
      "lng":         103.667,
      "nation":      "cn",
      "type":        "naval_construction",
      "status":      "construction",
      "confidence":  "high",
      "description": "Freetext.",
      "source":      "Satellite 2024",
      "last_updated":"2024-01-01"
    }
  ]
}
```

---

## bri_routes.json

```json
{
  "schema_version": "1.0",
  "type": "bri_routes",
  "last_updated": "<ISO-8601>",
  "data": [
    {
      "name":        "Maritime Silk Road",
      "type":        "maritime_bri",
      "color":       "#ff6644",
      "coords":      [[22, 114], [1.3, 103.8]],
      "description": "Freetext.",
      "ports":       ["Shanghai", "Singapore"]
    }
  ]
}
```

### type values
`maritime_bri` `land_bri` `cable_bri` `arctic_bri`

---

## chokepoints.json / ports.json / lanes.json

Structures follow similar `{schema_version, type, last_updated, data:[...]}` envelope.
See inline field comments in each file.

---

## Access from Python

```python
from data_manager import DataManager
dm = DataManager()

bases     = dm.get("bases")           # list[dict]
conflicts = dm.get("conflicts")
bases_cn  = dm.filter("bases", nation="cn")
bases_cn  = dm.filter("bases", status="construction")

dm.upsert("bases", record)            # add or update by id
dm.remove("bases", id="cs_auto_001")  # delete by id
dm.save("bases")                      # flush to disk
```
