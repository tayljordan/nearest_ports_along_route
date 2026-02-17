from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, Dict, List, Tuple

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from route_creation import searoute_waypoints  # noqa: E402

from .route_increments import densify_waypoints_nm  # noqa: E402


def main() -> None:
    p = argparse.ArgumentParser(
        description="Generate 1nm waypoint increments from route_creation output."
    )
    p.add_argument("--origin-lat", type=float, required=True)
    p.add_argument("--origin-lon", type=float, required=True)
    p.add_argument("--dest-lat", type=float, required=True)
    p.add_argument("--dest-lon", type=float, required=True)
    p.add_argument("--units", type=str, default="naut")
    p.add_argument("--step-nm", type=float, default=1.0)
    p.add_argument("--include-end", action="store_true", default=True)
    p.add_argument("--no-include-end", action="store_false", dest="include_end")
    args = p.parse_args()

    base = searoute_waypoints(
        origin_lat=args.origin_lat,
        origin_lon=args.origin_lon,
        dest_lat=args.dest_lat,
        dest_lon=args.dest_lon,
        units=args.units,
        include_endpoints=True,
        return_lonlat=False,
    )

    pts: List[Tuple[float, float]] = [(float(w["lat"]), float(w["lon"])) for w in base["waypoints"]]
    dense = densify_waypoints_nm(pts, step_nm=args.step_nm, include_end=args.include_end)

    out: Dict[str, Any] = {
        "step_nm": args.step_nm,
        "waypoints": [{"lat": lat, "lon": lon} for lat, lon in dense],
        "count": len(dense),
        "route_length_reported": base.get("length"),
        "route_length_units_reported": base.get("units"),
    }
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
