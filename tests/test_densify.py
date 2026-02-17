# FILE: tests/test_densify.py

from route_increments import densify_waypoints_nm, haversine_nm


def test_densify_basic_counts():
    # ~60nm north in latitude (1 degree lat ~ 60nm)
    pts = [(0.0, 0.0), (1.0, 0.0)]
    dense = densify_waypoints_nm(pts, step_nm=10.0, include_end=True)
    assert len(dense) >= 7  # 0,10,20,30,40,50,60-ish + end
    # monotonic-ish distance accumulation (at least not empty and endpoints included)
    assert dense[0] == (0.0, 0.0)
    assert haversine_nm(dense[-1][0], dense[-1][1], 1.0, 0.0) < 1.0
