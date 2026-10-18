# Over-the-air packet format (docs/design.md, "Packet format and API").
# 8 bytes: node_id (2, big-endian), seq, event_type, class, confidence, count, battery.
# Runs on MicroPython and CPython.

import struct

FMT = ">HBBBBBB"
SIZE = 8

# event_type
MOTION = 1
GATE_OPEN = 2
VEHICLE = 3
HEARTBEAT = 4
BOOT = 5
ACK = 0x80

EVENT_NAMES = {
    MOTION: "motion",
    GATE_OPEN: "gate",
    VEHICLE: "vehicle",
    HEARTBEAT: "heartbeat",
    BOOT: "boot",
    ACK: "ack",
}

# class: the fixed object vocabulary, then the tier 2 size classes
CLASSES = (
    "unknown", "small_animal", "deer", "hog", "canine",
    "person", "vehicle", "bird", "other",
    "size_small", "size_medium", "size_large",
)
CLASS_UNKNOWN = 0
CLASS_VEHICLE = 6

# battery code: volts * 50, so 0.02 V steps up to 5.1 V. 0 means not measured.
BATTERY_SCALE = 50


def battery_code(volts):
    if volts is None:
        return 0
    return max(0, min(255, int(volts * BATTERY_SCALE + 0.5)))


def battery_volts(code):
    return code / BATTERY_SCALE if code else None


def encode(node_id, seq, event_type, cls=CLASS_UNKNOWN, confidence=0, count=0, battery=0):
    return struct.pack(FMT, node_id, seq & 0xFF, event_type, cls, confidence, count, battery)


def decode(data):
    """Return a dict, or None if the packet is not ours."""
    if len(data) != SIZE:
        return None
    node_id, seq, event_type, cls, confidence, count, battery = struct.unpack(FMT, bytes(data))
    if event_type not in EVENT_NAMES:
        return None
    return {
        "node_id": node_id,
        "seq": seq,
        "event_type": event_type,
        "event": EVENT_NAMES[event_type],
        "class": CLASSES[cls] if cls < len(CLASSES) else "unknown",
        "confidence": confidence or None,
        "count": count or None,
        "battery_v": battery_volts(battery),
    }


def ack(node_id, seq):
    return encode(node_id, seq, ACK)


def is_ack_for(data, node_id, seq):
    p = decode(data)
    return p is not None and p["event_type"] == ACK and p["node_id"] == node_id and p["seq"] == seq
