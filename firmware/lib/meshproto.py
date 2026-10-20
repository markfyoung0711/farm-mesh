# Minimal Meshtastic serial API: stream framing plus just enough protobuf to read packets.
# Runs on MicroPython (the Pico W gateway brain) and CPython (tests).
#
# Frame: 0x94 0xC3, payload length (2 bytes, big-endian), protobuf bytes.
# The brain sends ToRadio messages; the Meshtastic radio answers with FromRadio messages.
# Field numbers follow meshtastic/protobufs (mesh.proto, portnums.proto).

import struct

START = b"\x94\xc3"
MAX_LEN = 512

# PortNum: what kind of data a packet carries
TEXT_MESSAGE_APP = 1
POSITION_APP = 3
NODEINFO_APP = 4
DETECTION_SENSOR_APP = 10
RANGE_TEST_APP = 66
TELEMETRY_APP = 67
PRIVATE_APP = 256  # our own payloads (firmware/lib/packet.py), e.g. a future gate module


# --- protobuf wire format ---
def _varint(buf, i):
    shift = result = 0
    while True:
        b = buf[i]
        i += 1
        result |= (b & 0x7F) << shift
        if not b & 0x80:
            return result, i
        shift += 7


def enc_varint(v):
    out = bytearray()
    while True:
        b = v & 0x7F
        v >>= 7
        if v:
            out.append(b | 0x80)
        else:
            out.append(b)
            return bytes(out)


def fields(buf):
    """Yield (field_number, value) for one message. Varint/fixed -> int, length-delimited -> bytes."""
    i, n = 0, len(buf)
    while i < n:
        key, i = _varint(buf, i)
        f, wt = key >> 3, key & 7
        if wt == 0:
            v, i = _varint(buf, i)
        elif wt == 1:
            v = int.from_bytes(buf[i:i + 8], "little")
            i += 8
        elif wt == 2:
            ln, i = _varint(buf, i)
            v = bytes(buf[i:i + ln])
            i += ln
        elif wt == 5:
            v = int.from_bytes(buf[i:i + 4], "little")
            i += 4
        else:
            raise ValueError("unsupported wire type %d" % wt)
        yield f, v


def _int32(v):
    return v - (1 << 64) if v >= 1 << 63 else v


def _float(v):
    return struct.unpack("<f", struct.pack("<I", v))[0]


# --- messages we read ---
def decode_data(buf):
    d = {"portnum": 0, "payload": b""}
    for f, v in fields(buf):
        if f == 1:
            d["portnum"] = v
        elif f == 2:
            d["payload"] = v
    return d


def decode_packet(buf):
    """MeshPacket. 'decoded' is None when the packet is on a channel the radio has no key for."""
    p = {"from": 0, "to": 0, "id": 0, "decoded": None,
         "rx_snr": None, "rx_rssi": None, "hop_limit": None, "hop_start": None}
    for f, v in fields(buf):
        if f == 1:
            p["from"] = v
        elif f == 2:
            p["to"] = v
        elif f == 4:
            p["decoded"] = decode_data(v)
        elif f == 6:
            p["id"] = v
        elif f == 8:
            p["rx_snr"] = _float(v)
        elif f == 9:
            p["hop_limit"] = v
        elif f == 12:
            p["rx_rssi"] = _int32(v)
        elif f == 15:
            p["hop_start"] = v
    return p


def decode_user(buf):
    u = {"id": "", "long_name": "", "short_name": ""}
    for f, v in fields(buf):
        if f == 1:
            u["id"] = v.decode()
        elif f == 2:
            u["long_name"] = v.decode()
        elif f == 3:
            u["short_name"] = v.decode()
    return u


def decode_node_info(buf):
    n = {"num": 0, "user": None}
    for f, v in fields(buf):
        if f == 1:
            n["num"] = v
        elif f == 2:
            n["user"] = decode_user(v)
    return n


def decode_from_radio(buf):
    """Return (kind, value) for the parts of FromRadio the gateway uses, else ("other", field)."""
    for f, v in fields(buf):
        if f == 2:
            return "packet", decode_packet(v)
        if f == 3:
            for f2, v2 in fields(v):
                if f2 == 1:
                    return "my_info", v2
            return "my_info", 0
        if f == 4:
            return "node_info", decode_node_info(v)
        if f == 7:
            return "config_complete", v
        if f == 8:
            return "rebooted", v
        if f != 1:  # field 1 is just a sequence id
            return "other", f
    return "other", 0


# --- messages we send ---
def frame(msg):
    return START + bytes([len(msg) >> 8, len(msg) & 0xFF]) + msg


def want_config(nonce):
    """ToRadio.want_config_id: start an API session. The radio replies with its config and node list, then packets."""
    return frame(b"\x18" + enc_varint(nonce))


def heartbeat():
    """ToRadio.heartbeat: keeps the API session alive."""
    return frame(b"\x3a\x00")


class Framer:
    """Collect UART bytes and return complete frame payloads. Debug text between frames is ignored."""

    def __init__(self):
        self.buf = b""

    def feed(self, data):
        b = self.buf + bytes(data)
        out = []
        while True:
            i = b.find(START)
            if i < 0:
                self.buf = b[-1:] if b[-1:] == START[:1] else b""
                return out
            if len(b) < i + 4:
                self.buf = b[i:]
                return out
            ln = (b[i + 2] << 8) | b[i + 3]
            if ln > MAX_LEN:  # false start inside debug text
                b = b[i + 2:]
                continue
            if len(b) < i + 4 + ln:
                self.buf = b[i:]
                return out
            out.append(b[i + 4:i + 4 + ln])
            b = b[i + 4 + ln:]
