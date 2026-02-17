# File: searoute_waypoints.py

from __future__ import annotations

from typing import Any, Dict, List, Tuple, Union

Number = Union[int, float]


def _validate_lat_lon(lat: Number, lon: Number, name: str) -> Tuple[float, float]:
    try:
        lat_f = float(lat)
        lon_f = float(lon)
    except (TypeError, ValueError) as e:
        raise ValueError(f"{name} lat/lon must be numeric. Got lat={lat!r}, lon={lon!r}") from e

    if not (-90.0 <= lat_f <= 90.0):
        raise ValueError(f"{name} latitude out of range [-90, 90]: {lat_f}")
    if not (-180.0 <= lon_f <= 180.0):
        raise ValueError(f"{name} longitude out of range [-180, 180]: {lon_f}")

    return lat_f, lon_f


def _get_route_properties(route: Any) -> Dict[str, Any]:
    if hasattr(route, "properties") and isinstance(route.properties, dict):
        return route.properties
    if isinstance(route, dict) and isinstance(route.get("properties"), dict):
        return route["properties"]
    return {}


def _get_route_coordinates(route: Any) -> List[List[float]]:
    coords = None

    # geojson.Feature style: route.geometry.coordinates
    if hasattr(route, "geometry") and route.geometry is not None:
        geom = route.geometry
        if hasattr(geom, "coordinates"):
            coords = geom.coordinates
        elif isinstance(geom, dict):
            coords = geom.get("coordinates")

    # dict style: route["geometry"]["coordinates"]
    if coords is None and isinstance(route, dict):
        geom = route.get("geometry", {})
        if isinstance(geom, dict):
            coords = geom.get("coordinates")

    if not isinstance(coords, list) or not coords:
        raise ValueError("searoute returned no coordinates (unexpected route geometry).")

    if not (isinstance(coords[0], (list, tuple)) and len(coords[0]) >= 2):
        raise ValueError("searoute coordinates are not in expected [lon, lat] list form.")

    return coords  # type: ignore[return-value]


def searoute_waypoints(
    origin_lat: Number,
    origin_lon: Number,
    dest_lat: Number,
    dest_lon: Number,
    *,
    units: str = "km",
    include_endpoints: bool = True,
    return_lonlat: bool = False,
) -> Dict[str, Any]:
    """
    Compute a sea route using searoute and return waypoints.

    Inputs are (lat, lon).
    Searoute expects (lon, lat), so conversion is handled internally.

    Returns:
      {
        "waypoints": [{"lat": .., "lon": ..}, ...]  # or [{"lon":..,"lat":..}, ...] if return_lonlat=True
        "length": <float|None>,
        "units": <str|None>
      }
    """
    o_lat, o_lon = _validate_lat_lon(origin_lat, origin_lon, "origin")
    d_lat, d_lon = _validate_lat_lon(dest_lat, dest_lon, "destination")

    try:
        import searoute as sr
    except Exception as e:
        raise RuntimeError("searoute is not installed. Install with: pip install searoute") from e

    origin = [o_lon, o_lat]
    destination = [d_lon, d_lat]

    route = sr.searoute(origin, destination, units=units, append_orig_dest=include_endpoints)

    # If include_ports is ever used, searoute can return a list of GeoJSON Features.
    if isinstance(route, list):
        if not route:
            raise ValueError("searoute returned an empty list of routes.")
        route = route[0]

    coords = _get_route_coordinates(route)
    props = _get_route_properties(route)

    waypoints: List[Dict[str, float]] = []
    for c in coords:
        lon = float(c[0])
        lat = float(c[1])
        if return_lonlat:
            waypoints.append({"lon": lon, "lat": lat})
        else:
            waypoints.append({"lat": lat, "lon": lon})

    return {
        "waypoints": waypoints,
        "length": props.get("length"),
        "units": props.get("units"),
    }


if __name__ == "__main__":
    # quick sanity test
    out = searoute_waypoints(
        origin_lat=50.064191736659104,
        origin_lon=0.3515625,
        dest_lat=39.36827914916014,
        dest_lon=117.42187500000001,
        units="km",
        include_endpoints=True,
    )
    print(f"waypoints={len(out['waypoints'])} length={out['length']} {out['units']}")
