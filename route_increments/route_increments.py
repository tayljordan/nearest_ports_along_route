from __future__ import annotations

import math
from typing import List, Tuple

NM_IN_METERS = 1852.0
EARTH_RADIUS_M = 6371000.0


def normalize_longitude(lon: float) -> float:
    lon = float(lon)
    return (lon + 180.0) % 360.0 - 180.0


def haversine_nm(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = phi2 - phi1
    dlambda = math.radians(lon2 - lon1)

    a = (math.sin(dphi / 2.0) ** 2) + math.cos(phi1) * math.cos(phi2) * (
        math.sin(dlambda / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    meters = EARTH_RADIUS_M * c
    return meters / NM_IN_METERS


def initial_bearing_rad(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dlambda = math.radians(lon2 - lon1)

    y = math.sin(dlambda) * math.cos(phi2)
    x = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(dlambda)
    return math.atan2(y, x)


def destination_point(
    lat: float, lon: float, bearing_rad: float, dist_nm: float
) -> Tuple[float, float]:
    phi1 = math.radians(lat)
    lambda1 = math.radians(lon)
    delta = (dist_nm * NM_IN_METERS) / EARTH_RADIUS_M

    sin_phi2 = math.sin(phi1) * math.cos(delta) + math.cos(phi1) * math.sin(delta) * math.cos(
        bearing_rad
    )
    phi2 = math.asin(sin_phi2)

    y = math.sin(bearing_rad) * math.sin(delta) * math.cos(phi1)
    x = math.cos(delta) - math.sin(phi1) * math.sin(phi2)
    lambda2 = lambda1 + math.atan2(y, x)

    lat2 = math.degrees(phi2)
    lon2 = normalize_longitude(math.degrees(lambda2))
    return lat2, lon2


def densify_waypoints_nm(
    waypoints_latlon: List[Tuple[float, float]],
    step_nm: float = 1.0,
    include_end: bool = True,
) -> List[Tuple[float, float]]:
    if not waypoints_latlon:
        return []

    if len(waypoints_latlon) == 1:
        lat, lon = waypoints_latlon[0]
        return [(float(lat), normalize_longitude(float(lon)))]

    step_nm = float(step_nm)
    if step_nm <= 0:
        raise ValueError("step_nm must be > 0")

    pts = [(float(lat), normalize_longitude(float(lon))) for lat, lon in waypoints_latlon]

    out: List[Tuple[float, float]] = [pts[0]]
    dist_to_next = step_nm
    eps = 1e-9

    for i in range(len(pts) - 1):
        a_lat, a_lon = pts[i]
        b_lat, b_lon = pts[i + 1]

        seg_len = haversine_nm(a_lat, a_lon, b_lat, b_lon)
        if seg_len < eps:
            continue

        cur_lat, cur_lon = a_lat, a_lon
        remaining = seg_len

        while remaining + eps >= dist_to_next:
            brg = initial_bearing_rad(cur_lat, cur_lon, b_lat, b_lon)
            new_lat, new_lon = destination_point(cur_lat, cur_lon, brg, dist_to_next)
            out.append((new_lat, new_lon))

            cur_lat, cur_lon = new_lat, new_lon
            remaining = haversine_nm(cur_lat, cur_lon, b_lat, b_lon)
            dist_to_next = step_nm

            if remaining < eps:
                break

        dist_to_next -= remaining
        if dist_to_next < eps:
            dist_to_next = step_nm

    if include_end:
        end_lat, end_lon = pts[-1]
        if haversine_nm(out[-1][0], out[-1][1], end_lat, end_lon) > 0.0001:
            out.append((end_lat, end_lon))

    return out
