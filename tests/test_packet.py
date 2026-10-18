import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "firmware" / "lib"))

import packet  # noqa: E402


def test_round_trip():
    data = packet.encode(1, 300, packet.VEHICLE, packet.CLASS_VEHICLE, 94, 1, packet.battery_code(3.92))
    assert len(data) == packet.SIZE
    p = packet.decode(data)
    assert p["node_id"] == 1
    assert p["seq"] == 300 & 0xFF
    assert p["event"] == "vehicle"
    assert p["class"] == "vehicle"
    assert p["confidence"] == 94
    assert abs(p["battery_v"] - 3.92) < 0.01


def test_unmeasured_fields_are_none():
    p = packet.decode(packet.encode(1, 0, packet.MOTION))
    assert p["class"] == "unknown"
    assert p["confidence"] is None and p["count"] is None and p["battery_v"] is None


def test_rejects_foreign_packets():
    assert packet.decode(b"hello") is None
    assert packet.decode(bytes([0, 1, 0, 99, 0, 0, 0, 0])) is None


def test_ack_matches_only_its_packet():
    a = packet.ack(1, 42)
    assert packet.is_ack_for(a, 1, 42)
    assert not packet.is_ack_for(a, 1, 43)
    assert not packet.is_ack_for(a, 2, 42)
    assert not packet.is_ack_for(packet.encode(1, 42, packet.MOTION), 1, 42)
