# Bring-up and range test for the LoRa radios (docs/components.md, C2 and the handheld).
# Needs lib/*.py on the board. Run on both boards:
#   mpremote run firmware/tools/radio_test.py
# Set ROLE: "pong" on the tower board, "ping" on the one you carry (the Heltec handheld) or mount at the gate.
# Ping shows RSSI/SNR both ways (on the Heltec's screen too); the LED blinks on every reply. Use it for the range walk.

import time

from machine import Pin

import board
from radio import LORA_CFG, TCXO_MV, make_modem
from screen import Screen

ROLE = "ping"
INTERVAL_MS = 2000

led = Pin(board.LED, Pin.OUT)
screen = Screen()

try:
    modem = make_modem()
except Exception as e:
    screen.show("radio init failed: %r" % e, "RADIO FAIL")
    print("check the board is seated, then try TCXO_MV = 1700, 3300 or None (now %s)" % TCXO_MV)
    raise SystemExit

screen.show("radio ok on %s: %d kHz SF%d BW%s, role %s" % (board.NAME, LORA_CFG["freq_khz"], LORA_CFG["sf"], LORA_CFG["bw"], ROLE),
            "radio ok %s" % ROLE)

if ROLE == "pong":
    while True:
        rx = modem.recv(timeout_ms=5000)
        if rx and not rx.crc_error and bytes(rx).startswith(b"PING"):
            # Reply with how well we heard them, so ping sees both directions.
            modem.send(("PONG%s %d %.1f" % (bytes(rx[4:]).decode(), rx.rssi, rx.snr)).encode())
            led.toggle()
            screen.show("pong %s rssi %d snr %.1f" % (bytes(rx), rx.rssi, rx.snr), "pong %d %.1f" % (rx.rssi, rx.snr))
else:
    n = sent = got = 0
    while True:
        n += 1
        sent += 1
        modem.send(("PING%d" % n).encode())
        rx = modem.recv(timeout_ms=1000)
        if rx and not rx.crc_error and bytes(rx).startswith(b"PONG"):
            got += 1
            led.on()
            parts = bytes(rx[4:]).split()
            screen.show("#%d  them->us rssi %d snr %.1f | us->them rssi %s snr %s | %d/%d ok" % (
                n, rx.rssi, rx.snr, parts[1].decode(), parts[2].decode(), got, sent),
                "%d/%d %d %.0f" % (got, sent, rx.rssi, rx.snr))
            time.sleep_ms(100)
            led.off()
        else:
            screen.show("#%d  no reply | %d/%d ok" % (n, got, sent), "%d/%d no reply" % (got, sent))
        time.sleep_ms(INTERVAL_MS)
