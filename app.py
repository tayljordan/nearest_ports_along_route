# FIX 1: app.py (sort imports + remove unused Tuple)

from __future__ import annotations

import json
import os
from typing import Any, Dict

from nearby_ports import load_ports, ports_within_nm
from route_creation import searoute_waypoints
from route_increments import densify_waypoints_nm


def ports_within_radius_along_route(
    origin_lat: float,
    origin_lon: float,
    dest_lat: float,
    dest_lon: float,
    radius_nm: float = 200.0,
    step_nm: float = 1.0,
) -> Dict[str, Any]:
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
    dense = densify_waypoints_nm(pts, step_nm=step_nm, include_end=True)

    ports = load_ports()

    found: Dict[str, Dict[str, Any]] = {}
    for i, (lat, lon) in enumerate(dense):
        hits = ports_within_nm({"lat": lat, "lon": lon}, ports, radius_nm, include_distance=True)
        for p in hits:
            key = (
                f"{p.get('CITY', '')}|{p.get('STATE', '')}|{p.get('COUNTRY', '')}|"
                f"{float(p['LATITUDE']):.6f}|{float(p['LONGITUDE']):.6f}"
            )
            d = float(p.get("DISTANCE_NM", 1e18))
            if (key not in found) or (d < float(found[key].get("DISTANCE_NM", 1e18))):
                outp = dict(p)
                outp["NEAREST_WAYPOINT_INDEX"] = i
                outp["NEAREST_WAYPOINT"] = {"lat": float(lat), "lon": float(lon)}
                found[key] = outp

    ports_list = sorted(found.values(), key=lambda x: float(x.get("DISTANCE_NM", 1e18)))

    return {
        "origin": {"lat": float(origin_lat), "lon": float(origin_lon)},
        "destination": {"lat": float(dest_lat), "lon": float(dest_lon)},
        "radius_nm": float(radius_nm),
        "step_nm": float(step_nm),
        "route_length_reported": base.get("length"),
        "route_length_units_reported": base.get("units"),
        "waypoint_count": len(dense),
        "ports_count": len(ports_list),
        "ports": ports_list,
    }


if __name__ == "__main__":
    result = ports_within_radius_along_route(
        origin_lat=35.3174,
        origin_lon=-11.3857,
        dest_lat=35.4607,
        dest_lon=19.9195,
        radius_nm=200.0,
        step_nm=1.0,
    )

    print(json.dumps(result, indent=2))

    out_path = os.path.join(os.path.dirname(__file__), "ports_within_200nm_route.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    print(f"Wrote: {out_path}")
