# Gateway brain (Pico W): reads the Meshtastic tower radio over UART, logs events, pushes phone alerts.
# The radio (Pico H + Waveshare running Meshtastic) handles the mesh: relaying, encryption, ACKs and dedup.
# Logic follows docs/design.md, "Phase 1".

import os
import sys
import time

import network
import ntptime
import requests
import rp2
from machine import UART, WDT, Pin

import config as cfg
import meshproto as mp
import packet
import secrets

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
    "text": (None, 3, "speech_balloon"),  # message is the text itself
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


# --- Radio link ---
uart = UART(cfg.UART_ID, baudrate=cfg.UART_BAUD, tx=Pin(cfg.UART_TX), rx=Pin(cfg.UART_RX), rxbuf=2048)
framer = mp.Framer()
names = {}  # node number -> long name, from the radio's node list
my_num = None  # the tower radio's own node number
last_from_radio = time.ticks_ms()
last_heartbeat = time.ticks_ms()
last_session = time.ticks_ms()


def start_session():
    """Ask the radio for its config and node list; packets follow."""
    global last_session
    last_session = time.ticks_ms()
    uart.write(mp.want_config(last_session & 0xFFFF))


def name_of(num):
    return names.get(num) or "!%08x" % num


def classify(p):
    """Return (event, detail) for a decoded mesh packet, or (None, None) to ignore it."""
    d = p["decoded"]
    port, payload = d["portnum"], d["payload"]
    if port == mp.PRIVATE_APP:
        ours = packet.decode(payload)
        return (ours["event"], "") if ours else (None, None)
    if port in (mp.TEXT_MESSAGE_APP, mp.DETECTION_SENSOR_APP):
        try:
            text = payload.decode().replace("\a", "").strip()
        except UnicodeError:
            return None, None
        # Detection Sensor: "<sensor name> detected"
        for sensor, event in cfg.DETECTION_NAMES.items():
            if text.startswith(sensor) and "detected" in text:
                return event, text
        if port == mp.TEXT_MESSAGE_APP and cfg.ALERT_TEXT_MESSAGES:
            return "text", text
        return None, None
    if port == mp.NODEINFO_APP:
        u = mp.decode_user(payload)
        if u["long_name"]:
            names[p["from"]] = u["long_name"]
    return None, None  # position, telemetry, etc.: only counts as "heard"


# --- Main loop ---
last_alert = {}  # (name, event) -> ticks_ms
last_heard = {}  # name -> ticks_ms
fault_sent = set()


def handle_packet(p):
    if p["from"] == my_num or p["decoded"] is None:
        return  # our own echo, or a channel we have no key for
    now = time.ticks_ms()
    event, detail = classify(p)
    name = name_of(p["from"])
    last_heard[name] = now
    if name in fault_sent:
        fault_sent.discard(name)
        push("%s back online" % name, "Heard from %s again" % name, 3, "white_check_mark")
    if event is None:
        return

    rssi, snr = p["rx_rssi"], p["rx_snr"]
    hops = p["hop_start"] - p["hop_limit"] if p["hop_start"] is not None and p["hop_limit"] is not None else ""
    log("%s,%s,%s,%s,%s,%s,%s" % (
        iso_now(), name, event, rssi if rssi is not None else "", "%.1f" % snr if snr is not None else "",
        hops, detail.replace(",", " ")))
    print(name, event, detail, "rssi", rssi, "snr", snr, "hops", hops)

    alert = ALERTS.get(event)
    if alert is None:
        return
    key = (name, event)
    t = last_alert.get(key)
    if t is not None and time.ticks_diff(now, t) < cfg.COOLDOWN_MS:
        return
    last_alert[key] = now
    msg, priority, tags = alert
    info = [iso_now()]
    if hops:
        info.append("%s hop(s)" % hops)
    elif rssi is not None:
        info.append("RSSI %d" % rssi)
    push("%s: %s" % (name, event), "%s (%s)" % (msg or detail, ", ".join(info)), priority, tags)


def handle_frame(buf):
    global my_num, last_from_radio
    last_from_radio = time.ticks_ms()
    try:
        kind, v = mp.decode_from_radio(buf)
    except (ValueError, IndexError) as e:
        print("bad frame:", e)
        return
    if kind == "packet":
        handle_packet(v)
    elif kind == "node_info" and v["user"]:
        names[v["num"]] = v["user"]["long_name"]
    elif kind == "my_info":
        my_num = v
    elif kind == "config_complete":
        print("radio session up, %d nodes known" % len(names))
    elif kind == "rebooted":
        start_session()


def check_silent_nodes():
    now = time.ticks_ms()
    for name in cfg.WATCH_NODES:
        t = last_heard.setdefault(name, now)  # start the clock at gateway boot
        if name not in fault_sent and time.ticks_diff(now, t) > cfg.SILENT_MS:
            fault_sent.add(name)
            log("%s,%s,fault,,,," % (iso_now(), name))
            push("%s silent" % name, "Nothing from %s in %d h. Check its power and antenna." % (
                name, cfg.SILENT_MS // 3_600_000), 4, "rotating_light")


def check_radio():
    global last_heartbeat
    now = time.ticks_ms()
    if time.ticks_diff(now, last_heartbeat) > cfg.HEARTBEAT_MS:
        last_heartbeat = now
        uart.write(mp.heartbeat())
    quiet = time.ticks_diff(now, last_from_radio)
    if quiet > cfg.RADIO_CHECK_MS and time.ticks_diff(now, last_session) > 60_000:
        # A healthy radio answers a new handshake with its config straight away.
        if quiet > cfg.RADIO_CHECK_MS + 60_000 and "radio" not in fault_sent:
            fault_sent.add("radio")
            log("%s,RADIO,fault,,,," % iso_now())
            push("Tower radio silent", "No data from the Meshtastic radio over UART. Check its power and wiring.",
                 4, "rotating_light")
        start_session()
    elif quiet < cfg.RADIO_CHECK_MS and "radio" in fault_sent:
        fault_sent.discard("radio")
        push("Tower radio back", "The Meshtastic radio is talking again", 3, "white_check_mark")


wifi_up()
sync_time()
log("%s,GATEWAY,boot,,,," % iso_now())
start_session()
push("Gateway online", "Tower gateway started", 2, "satellite")
last_ntp = time.ticks_ms()

while True:
    feed()
    data = uart.read()
    if data:
        for buf in framer.feed(data):
            handle_frame(buf)
    else:
        time.sleep_ms(20)
    check_silent_nodes()
    check_radio()
    if time.ticks_diff(time.ticks_ms(), last_ntp) > 6 * 3_600_000:
        last_ntp = time.ticks_ms()
        if wifi_up():
            sync_time()
