# Tower hub (Pico W): LoRa -> ACK, dedup, log, push alert over the house WiFi.
# Logic follows docs/design.md, "Phase 1".

import os
import sys
import time

import network
import ntptime
import requests
import rp2
from machine import WDT, Pin

import config as cfg
import packet
import secrets
from radio import make_modem

# Escape hatch: a running watchdog can't be stopped, so Ctrl-C alone just leads to a reset.
# Press and hold BOOTSEL while the LED is lit (first 3 s after power-up) to drop to the REPL instead.
led = Pin("LED", Pin.OUT)
led.on()
for _ in range(30):
    if rp2.bootsel_button():
        led.off()
        print("BOOTSEL held: hub not started")
        sys.exit()
    time.sleep_ms(100)
led.off()

wdt = WDT(timeout=cfg.WATCHDOG_MS) if cfg.WATCHDOG_MS else None


def feed():
    if wdt:
        wdt.feed()


# --- WiFi and time ---
wlan = network.WLAN(network.STA_IF)


def wifi_up():
    if wlan.isconnected():
        return True
    wlan.active(True)
    wlan.connect(secrets.WIFI_SSID, secrets.WIFI_PASSWORD)
    for _ in range(30):
        feed()
        if wlan.isconnected():
            print("wifi", wlan.ifconfig()[0])
            return True
        time.sleep(0.5)
    print("wifi failed")
    return False


def sync_time():
    try:
        ntptime.settime()
    except OSError as e:
        print("ntp failed:", e)


def iso_now():
    t = time.gmtime()
    return "%04d-%02d-%02dT%02d:%02d:%02dZ" % t[:6]


# --- Alerts ---
def urlencode(s):
    return "".join(c if c.isalpha() or c.isdigit() or c in "-._~" else "%%%02X" % b
                   for c, b in ((chr(b), b) for b in str(s).encode()))


def push(title, message, priority=3, tags="warning"):
    feed()
    if not wifi_up():
        return
    try:
        if cfg.ALERT == "pushover":
            r = requests.post(
                "https://api.pushover.net/1/messages.json",
                data="token=%s&user=%s&title=%s&message=%s&priority=%d" % (
                    secrets.PUSHOVER_TOKEN, secrets.PUSHOVER_USER,
                    urlencode(title), urlencode(message), max(-2, min(1, priority - 3))),
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=5,
            )
        else:
            r = requests.post(
                "%s/%s" % (cfg.NTFY_SERVER, secrets.NTFY_TOPIC),
                data=message,
                headers={"Title": title, "Priority": str(priority), "Tags": tags},
                timeout=5,
            )
        r.close()
    except Exception as e:
        print("push failed:", e)
    feed()


ALERTS = {
    # event -> (message, priority, ntfy tags)
    "vehicle": ("Vehicle at the gate", 4, "car"),
    "motion": ("Person or animal at the gate", 3, "walking"),
    "gate": ("Gate opened", 4, "door"),
}


# --- Log ---
def log(line):
    try:
        if os.stat(cfg.LOG_FILE)[6] > cfg.LOG_MAX_BYTES:
            os.rename(cfg.LOG_FILE, "events.old")
    except OSError:
        pass
    with open(cfg.LOG_FILE, "a") as f:
        f.write(line + "\n")


# --- Main loop ---
modem = make_modem()
last_seq = {}  # node_id -> last seq seen
last_alert = {}  # (node_id, event) -> ticks_ms
last_heard = {}  # node_id -> ticks_ms
fault_sent = set()


def handle(rx):
    p = packet.decode(rx)
    if p is None or p["event_type"] == packet.ACK:
        return
    node_id = p["node_id"]
    name = cfg.NODES.get(node_id, "node-%d" % node_id)

    # ACK first and fast; the node is waiting.
    modem.send(packet.ack(node_id, p["seq"]))

    now = time.ticks_ms()
    last_heard[node_id] = now
    if node_id in fault_sent:
        fault_sent.discard(node_id)
        push("%s back online" % name, "Heard from %s again" % name, 3, "white_check_mark")

    # A retry whose ACK was lost arrives with the same seq. A reboot resets seq, so BOOT always passes.
    if last_seq.get(node_id) == p["seq"] and p["event_type"] != packet.BOOT:
        return
    last_seq[node_id] = p["seq"]

    log("%s,%s,%s,%d,%s,%s,%.1f" % (
        iso_now(), name, p["event"], p["seq"], p["battery_v"] or "", rx.rssi, rx.snr))
    print(name, p["event"], "rssi", rx.rssi, "snr", rx.snr)

    alert = ALERTS.get(p["event"])
    if alert is None:
        return
    key = (node_id, p["event"])
    t = last_alert.get(key)
    if t is not None and time.ticks_diff(now, t) < cfg.COOLDOWN_MS:
        return
    last_alert[key] = now
    msg, priority, tags = alert
    push("%s: %s" % (name, p["event"]), "%s (%s, RSSI %d)" % (msg, iso_now(), rx.rssi), priority, tags)


def check_silent_nodes():
    limit = cfg.HEARTBEAT_MS * cfg.MISSED_HEARTBEATS
    now = time.ticks_ms()
    for node_id, name in cfg.NODES.items():
        if node_id in cfg.QUIET_NODES:
            continue
        t = last_heard.setdefault(node_id, now)  # start the clock at hub boot
        if node_id not in fault_sent and time.ticks_diff(now, t) > limit:
            fault_sent.add(node_id)
            log("%s,%s,fault,,,," % (iso_now(), name))
            push("%s silent" % name, "No packets from %s in %d h. Check battery and antenna." % (
                name, limit // 3_600_000), 4, "rotating_light")


wifi_up()
sync_time()
log("%s,HUB,boot,,,," % iso_now())
push("Hub online", "Tower hub started", 2, "satellite")
last_ntp = time.ticks_ms()

while True:
    feed()
    rx = modem.recv(timeout_ms=2000)
    if rx and not rx.crc_error:
        handle(rx)
    check_silent_nodes()
    if time.ticks_diff(time.ticks_ms(), last_ntp) > 6 * 3_600_000:
        last_ntp = time.ticks_ms()
        if wifi_up():
            sync_time()
