# NEW FILE:
# /Users/jordantaylor/PycharmProjects/nearest_port/nearby_ports/port_search.py

from __future__ import annotations

import json
import math
import os
from typing import Any, Dict, Iterable, List, Optional, Tuple, Union

from route_increments import haversine_nm, normalize_longitude

Waypoint = Union[Dict[str, float], Tuple[float, float], List[float]]  # {"lat","lon"} OR (lat,lon)


def _ports_json_path() -> str:
    return os.path.join(os.path.dirname(__file__), "data", "ports.json")


def load_ports(path: Optional[str] = None) -> List[Dict[str, Any]]:
    p = path or _ports_json_path()
    with open(p, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("ports.json must be a JSON list of port objects")
    return data


def _waypoint_latlon(wp: Waypoint) -> Tuple[float, float]:
    if isinstance(wp, dict):
        lat = float(wp["lat"])
        lon = float(wp["lon"])
        return lat, normalize_longitude(lon)
    if isinstance(wp, (tuple, list)) and len(wp) >= 2:
        lat = float(wp[0])
        lon = float(wp[1])
        return lat, normalize_longitude(lon)
    raise ValueError(f"Invalid waypoint: {wp!r}")


def _port_latlon(port: Dict[str, Any]) -> Tuple[float, float]:
    lat = float(port["LATITUDE"])
    lon = normalize_longitude(float(port["LONGITUDE"]))
    return lat, lon


def _bbox_prefilter(
    wp_lat: float, wp_lon: float, port_lat: float, port_lon: float, radius_nm: float
) -> bool:
    # fast reject using degree approximations:
    # 1 deg latitude ~ 60 nm
    dlat_max = radius_nm / 60.0
    if abs(port_lat - wp_lat) > dlat_max:
        return False

    cos_lat = math.cos(math.radians(wp_lat))
    if cos_lat < 1e-12:
        # near poles, skip lon prefilter (still safe)
        return True

    dlon_max = radius_nm / (60.0 * cos_lat)
    # longitude wrap already normalized into [-180,180)
    return abs(port_lon - wp_lon) <= dlon_max


def ports_within_nm(
    waypoint: Waypoint,
    ports: List[Dict[str, Any]],
    radius_nm: float,
    *,
    include_distance: bool = True,
) -> List[Dict[str, Any]]:
    wp_lat, wp_lon = _waypoint_latlon(waypoint)
    radius_nm = float(radius_nm)
    if radius_nm <= 0:
        return []

    hits: List[Dict[str, Any]] = []
    for port in ports:
        p_lat, p_lon = _port_latlon(port)

        if not _bbox_prefilter(wp_lat, wp_lon, p_lat, p_lon, radius_nm):
            continue

        d = haversine_nm(wp_lat, wp_lon, p_lat, p_lon)
        if d <= radius_nm:
            if include_distance:
                out = dict(port)
                out["DISTANCE_NM"] = d
                hits.append(out)
            else:
                hits.append(port)

    # closest first
    if include_distance:
        hits.sort(key=lambda x: float(x.get("DISTANCE_NM", 0.0)))
    return hits


def ports_near_waypoints(
    waypoints: Iterable[Waypoint],
    radius_nm: float,
    *,
    ports_path: Optional[str] = None,
    ports: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    ports_list = ports if ports is not None else load_ports(ports_path)
    results: Dict[str, Any] = {}

    for i, wp in enumerate(waypoints):
        wp_lat, wp_lon = _waypoint_latlon(wp)
        hits = ports_within_nm(
            {"lat": wp_lat, "lon": wp_lon}, ports_list, radius_nm, include_distance=True
        )
        results[str(i)] = {
            "waypoint": {"lat": wp_lat, "lon": wp_lon},
            "ports": hits,
        }

    return {
        "radius_nm": float(radius_nm),
        "waypoint_count": len(list(waypoints)) if hasattr(waypoints, "__len__") else None,
        "results": results,
    }
