[![CI](https://github.com/tayljordan/nearest_port_along_route/actions/workflows/ci.yml/badge.svg)](https://github.com/tayljordan/nearest_port_along_route/actions/workflows/ci.yml)
[![Ruff](https://img.shields.io/badge/code%20style-ruff-261230.svg)](https://github.com/astral-sh/ruff)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)


# nearest-port

Searoute.py waypoint generation + 1 NM route densification + “ports within N nautical miles” lookup along a route.

This repo stitches together three small packages:

* **route_creation**: calls `searoute` and returns route waypoints
* **route_increments**: densifies a route to fixed nautical-mile increments (default 1 NM)
* **nearby_ports**: loads `nearby_ports/data/ports.json` and finds ports within a radius (NM) of each waypoint

Important: `searoute` is intended for visualization realism, not navigation.

---

## Project layout

```
nearest_port/
  pyproject.toml
  README.md
  LICENSE
  MANIFEST.in
  .gitignore
  app.py
  route_creation/
    __init__.py
    route_creation.py
  route_increments/
    __init__.py
    __main__.py
    route_increments.py
  nearby_ports/
    __init__.py
    port_search.py
    data/
      ports.json
  tests/
    test_smoke_imports.py
    test_densify.py
    test_ports_data_ships.py
```

---

## Requirements

* Python >= 3.10
* `searoute` (installed automatically)
* Optional dev tools: `pytest`, `ruff`

---

## Install

Create and activate your virtual environment, then install editable with dev deps:

```bash
cd /Users/jordantaylor/PycharmProjects/nearest_port
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

---

## Quick verification

```bash
pytest
ruff check .
```

---

## Core usage

### 1) Create a route (searoute waypoints)

Inputs are `(lat, lon)`.

```python
from route_creation import searoute_waypoints

base = searoute_waypoints(
    origin_lat=35.3174,
    origin_lon=-11.3857,
    dest_lat=35.4607,
    dest_lon=19.9195,
    units="naut",
    include_endpoints=True,
    return_lonlat=False,  # returns [{"lat","lon"}]
)

print(base["length"], base["units"])
print(len(base["waypoints"]))
```

Returns:

```json
{
  "waypoints": [{"lat": 0.0, "lon": 0.0}],
  "length": 1658.01,
  "units": "naut"
}
```

---

### 2) Densify to 1 NM increments

```python
from route_increments import densify_waypoints_nm

pts = [(w["lat"], w["lon"]) for w in base["waypoints"]]
dense = densify_waypoints_nm(pts, step_nm=1.0, include_end=True)

print(len(dense))  # ~ route_length_nm + endpoints
```

---

### 3) Find ports within N NM of a waypoint

```python
from nearby_ports import load_ports, ports_within_nm

ports = load_ports()  # loads nearby_ports/data/ports.json
hits = ports_within_nm({"lat": dense[0][0], "lon": dense[0][1]}, ports, radius_nm=50.0)

print(hits[:3])  # includes DISTANCE_NM and sorted nearest-first
```

---

### 4) Find ports within N NM along an entire route (union across all waypoints)

This collects unique ports that fall within the radius of any waypoint, and records the nearest waypoint.

```python
from nearby_ports import load_ports, ports_within_nm
from route_creation import searoute_waypoints
from route_increments import densify_waypoints_nm

origin_lat, origin_lon = 35.3174, -11.3857
dest_lat, dest_lon = 35.4607, 19.9195

base = searoute_waypoints(
    origin_lat=origin_lat,
    origin_lon=origin_lon,
    dest_lat=dest_lat,
    dest_lon=dest_lon,
    units="naut",
    include_endpoints=True,
    return_lonlat=False,
)

pts = [(w["lat"], w["lon"]) for w in base["waypoints"]]
dense = densify_waypoints_nm(pts, step_nm=1.0, include_end=True)

ports = load_ports()

radius_nm = 200.0
found = {}

for i, (lat, lon) in enumerate(dense):
    hits = ports_within_nm({"lat": lat, "lon": lon}, ports, radius_nm, include_distance=True)
    for p in hits:
        key = (
            f'{p.get("CITY","")}|{p.get("STATE","")}|{p.get("COUNTRY","")}|'
            f'{float(p["LATITUDE"]):.6f}|{float(p["LONGITUDE"]):.6f}'
        )
        d = float(p.get("DISTANCE_NM", 1e18))
        if (key not in found) or (d < float(found[key].get("DISTANCE_NM", 1e18))):
            outp = dict(p)
            outp["NEAREST_WAYPOINT_INDEX"] = i
            outp["NEAREST_WAYPOINT"] = {"lat": float(lat), "lon": float(lon)}
            found[key] = outp

ports_list = sorted(found.values(), key=lambda x: float(x.get("DISTANCE_NM", 1e18)))

print("ports_count:", len(ports_list))
print(ports_list[:5])
```

---

## CLI usage (route densification)

`route_increments` is runnable as a module:

```bash
python -m route_increments \
  --origin-lat 50.0641917 --origin-lon 0.3515625 \
  --dest-lat 39.3682791 --dest-lon 117.421875 \
  --step-nm 1
```

Outputs JSON containing densified waypoints.

---

## Ports dataset (`ports.json`)

Location:

* `nearby_ports/data/ports.json`

Format:

```json
[
  {
    "CITY": "Aabenraa",
    "STATE": "South Denmark",
    "COUNTRY": "Denmark",
    "LATITUDE": 55.04,
    "LONGITUDE": 9.42
  }
]
```

Packaging:

* Included via `pyproject.toml` `[tool.setuptools.package-data]`
* Included in sdist via `MANIFEST.in`

So `load_ports()` works both in editable installs and in installed wheels.

---

## Development

Install dev deps:

```bash
python -m pip install -e ".[dev]"
```

Run formatting + lint:

```bash
ruff check . --fix
ruff format .
```

Run tests:

```bash
pytest
```

---

## Notes / caveats

* `searoute` routes are for visualization realism, not operational navigation.
* 1 NM densification uses great-circle math (haversine + forward geodesic approximation on a sphere).
* Performance: scanning every port for every waypoint is O(W*P). If you later need speed, add spatial indexing (k-d tree / R-tree) or prefilter by bounding boxes per segment.

---

## License

MIT (see `LICENSE`)
