import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "firmware" / "lib"))

import meshproto as mp  # noqa: E402
import packet  # noqa: E402


# Tiny protobuf encoder, for building what a Meshtastic radio would send.
def fv(f, v):
    return mp.enc_varint(f << 3) + mp.enc_varint(v & 0xFFFFFFFFFFFFFFFF)


def fb(f, b):
    return mp.enc_varint(f << 3 | 2) + mp.enc_varint(len(b)) + b


def f32(f, v):
    return mp.enc_varint(f << 3 | 5) + struct.pack("<I", v)


def fflt(f, x):
    return mp.enc_varint(f << 3 | 5) + struct.pack("<f", x)


def mesh_packet(frm, portnum, payload, rssi=-97, snr=6.5):
    data = fv(1, portnum) + fb(2, payload)
    return (f32(1, frm) + f32(2, 0xFFFFFFFF) + fb(4, data) + f32(6, 1234)
            + fflt(8, snr) + fv(9, 2) + fv(12, rssi) + fv(15, 3))


def test_decode_text_packet():
    kind, p = mp.decode_from_radio(fv(1, 7) + fb(2, mesh_packet(0xA1B2C3D4, mp.TEXT_MESSAGE_APP, b"Motion detected")))
    assert kind == "packet"
    assert p["from"] == 0xA1B2C3D4
    assert p["decoded"]["portnum"] == mp.TEXT_MESSAGE_APP
    assert p["decoded"]["payload"] == b"Motion detected"
    assert p["rx_rssi"] == -97
    assert abs(p["rx_snr"] - 6.5) < 1e-6
    assert p["hop_start"] - p["hop_limit"] == 1


def test_private_app_carries_our_packet():
    ours = packet.encode(1, 42, packet.VEHICLE, packet.CLASS_VEHICLE)
    _, p = mp.decode_from_radio(fb(2, mesh_packet(5, mp.PRIVATE_APP, ours)))
    assert packet.decode(p["decoded"]["payload"])["event"] == "vehicle"


def test_node_info_names():
    user = fb(1, b"!a1b2c3d4") + fb(2, b"GATE-01") + fb(3, b"GT01")
    kind, n = mp.decode_from_radio(fb(4, fv(1, 0xA1B2C3D4) + fb(2, user)))
    assert kind == "node_info"
    assert n["num"] == 0xA1B2C3D4 and n["user"]["long_name"] == "GATE-01"


def test_config_complete_and_my_info():
    assert mp.decode_from_radio(fv(7, 99)) == ("config_complete", 99)
    assert mp.decode_from_radio(fb(3, fv(1, 0x1234))) == ("my_info", 0x1234)


def test_framer_splits_and_skips_debug_text():
    a = mp.frame(fv(7, 1))
    b = mp.frame(fv(7, 2))
    stream = b"INFO | boot \x94 noise\n" + a + b"log line\n" + b
    f = mp.Framer()
    got = []
    for i in range(0, len(stream), 5):  # arrives in small UART chunks
        got += f.feed(stream[i:i + 5])
    assert got == [fv(7, 1), fv(7, 2)]


def test_want_config_frame():
    assert mp.want_config(300) == b"\x94\xc3\x00\x03\x18\xac\x02"
