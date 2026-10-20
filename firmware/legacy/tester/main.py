# TEST-01 handheld tester (Heltec WiFi LoRa 32 V3; also runs on a Pico + Waveshare).
#   - Short press the button (PRG on the Heltec): send a fake MOTION event and wait for the hub's ACK.
#   - Long press (1 s or more): send a fake VEHICLE event.
#   - The rest of the time it listens and shows every packet it hears: gate events, hub ACKs, its own replies.
# Radio is a broadcast medium, so this sees everything any node in range sends.
# Needs lib/*.py on the board, plus ssd1306 for the Heltec's screen.

import time

from machine import Pin

import board
import packet
from radio import make_modem
from screen import Screen

NODE_ID = 99  # TEST-01 in the hub's NODES table
LONG_PRESS_MS = 1000
ACK_TIMEOUT_MS = 600
RETRIES = 3

NAMES = {1: "GATE-01", 99: "TEST-01"}
SHORT = {1: "G1", 99: "T"}  # OLED is 16 characters wide

led = Pin(board.LED, Pin.OUT)
button = Pin(board.BUTTON, Pin.IN, Pin.PULL_UP)
screen = Screen()
modem = make_modem()
seq = time.ticks_ms() & 0xFF


def show(rx, note="", short_note=""):
    p = packet.decode(rx)
    if p is None:
        screen.show("  heard %d foreign bytes  rssi %d" % (len(rx), rx.rssi), "?? %d" % rx.rssi)
        return
    nid = p["node_id"]
    name = NAMES.get(nid, "node-%d" % nid)
    short = SHORT.get(nid, str(nid))
    if p["event_type"] == packet.ACK:
        who, s_who = "HUB -> %s" % name, "H>%s" % short
    else:
        who, s_who = "%s ->" % name, "%s>" % short
    screen.show(
        "  %-17s %-9s seq %3d  rssi %4d snr %5.1f %s" % (who, p["event"], p["seq"], rx.rssi, rx.snr, note),
        "%s %s %d%s" % (s_who, p["event"][:4], rx.rssi, short_note),
    )


def send(event_type):
    global seq
    seq = (seq + 1) & 0xFF
    data = packet.encode(NODE_ID, seq, event_type)
    name = packet.EVENT_NAMES[event_type]
    screen.show("TEST-01 sends %s seq %d" % (name, seq), "SEND %s %d" % (name[:4], seq))
    led.on()
    t0 = time.ticks_ms()
    for attempt in range(1 + RETRIES):
        modem.send(data)
        deadline = time.ticks_add(time.ticks_ms(), ACK_TIMEOUT_MS)
        while time.ticks_diff(deadline, time.ticks_ms()) > 0:
            rx = modem.recv(timeout_ms=max(1, time.ticks_diff(deadline, time.ticks_ms())))
            if not rx or rx.crc_error:
                continue
            if packet.is_ack_for(rx, NODE_ID, seq):
                ms = time.ticks_diff(time.ticks_ms(), t0)
                show(rx, "<- ACK after %d ms, try %d" % (ms, attempt + 1), " OK")
                led.off()
                return
            show(rx)
        screen.show("  no ACK, retrying", "  retry")
    screen.show("  FAILED: hub never ACKed. Is it running, and on the same radio settings?", "NO ACK!")
    led.off()


screen.show("TEST-01 ready on %s. Short press = motion, long press = vehicle." % board.NAME, "TEST-01 ready")
while True:
    if button.value() == 0:
        t = time.ticks_ms()
        while button.value() == 0:
            time.sleep_ms(10)
        held = time.ticks_diff(time.ticks_ms(), t)
        if held > 30:  # ignore contact bounce
            send(packet.VEHICLE if held >= LONG_PRESS_MS else packet.MOTION)
    rx = modem.recv(timeout_ms=50)
    if rx and not rx.crc_error:
        show(rx)
