# FILE: tests/test_ports_data_ships.py

from nearby_ports import load_ports


def test_ports_json_loads():
    ports = load_ports()
    assert isinstance(ports, list)
    assert len(ports) > 0
    p0 = ports[0]
    assert "CITY" in p0 and "COUNTRY" in p0 and "LATITUDE" in p0 and "LONGITUDE" in p0
