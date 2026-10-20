# GATE-01 sensor node: PIR + magnetometer (+ optional reed switch) -> LoRa -> tower hub.
# WiFi stays off. Logic follows docs/design.md, "Phase 1".

import random
import time

from machine import ADC, I2C, Pin

import config as cfg
import packet
from radio import make_modem

led = Pin("LED", Pin.OUT)
modem = make_modem()
seq = random.getrandbits(8)


def battery():
    if cfg.BATTERY_ADC_PIN is None:
        return 0
    v = ADC(cfg.BATTERY_ADC_PIN).read_u16() * 3.3 / 65535 * cfg.BATTERY_DIVIDER
    return packet.battery_code(v)


def send(event_type, cls=packet.CLASS_UNKNOWN):
    """Send one event, wait for the hub's ACK, retry with a random backoff. Returns True if ACKed."""
    global seq
    seq = (seq + 1) & 0xFF
    data = packet.encode(cfg.NODE_ID, seq, event_type, cls, battery=battery())
    led.on()
    try:
        for attempt in range(1 + cfg.RETRIES):
            modem.send(data)
            deadline = time.ticks_add(time.ticks_ms(), cfg.ACK_TIMEOUT_MS)
            while time.ticks_diff(deadline, time.ticks_ms()) > 0:
                rx = modem.recv(timeout_ms=max(1, time.ticks_diff(deadline, time.ticks_ms())))
                if rx and packet.is_ack_for(rx, cfg.NODE_ID, seq):
                    print("sent", packet.EVENT_NAMES[event_type], "seq", seq, "rssi", rx.rssi)
                    return True
            time.sleep_ms(random.randint(200, 1500))
        print("no ack", packet.EVENT_NAMES[event_type], "seq", seq)
        return False
    finally:
        led.off()
        modem.standby()


# --- PIR: count rising edges in an IRQ, confirm in the main loop ---
pir_edges = []


def _pir_irq(_pin):
    pir_edges.append(time.ticks_ms())
    if len(pir_edges) > 8:
        pir_edges.pop(0)


pir = None
if cfg.PIR_PIN is not None:
    pir = Pin(cfg.PIR_PIN, Pin.IN, Pin.PULL_DOWN)
    pir.irq(trigger=Pin.IRQ_RISING, handler=_pir_irq)


def pir_confirmed(now):
    recent = [t for t in pir_edges if time.ticks_diff(now, t) < cfg.PIR_CONFIRM_MS]
    if len(recent) >= cfg.PIR_CONFIRM_HITS:
        pir_edges.clear()
        return True
    return False


# --- Magnetometer: deviation from a slow-moving baseline ---
mag = None
if cfg.I2C_SDA is not None:
    try:
        from qmc5883l import QMC5883L

        mag = QMC5883L(I2C(cfg.I2C_ID, sda=Pin(cfg.I2C_SDA), scl=Pin(cfg.I2C_SCL), freq=100_000))
    except OSError as e:
        print("magnetometer disabled:", e)
baseline = mag.magnitude() if mag else 0.0
mag_over = 0


def mag_confirmed():
    global baseline, mag_over
    if not mag or not mag.ready():
        return False
    m = mag.magnitude()
    if abs(m - baseline) > cfg.MAG_THRESHOLD:
        mag_over += 1
        # Track slowly even while over threshold, so a parked vehicle becomes the new baseline.
        baseline += (m - baseline) * cfg.MAG_BASELINE_ALPHA * 0.1
    else:
        mag_over = 0
        baseline += (m - baseline) * cfg.MAG_BASELINE_ALPHA
    if mag_over == cfg.MAG_CONFIRM_SAMPLES:
        return True
    return False


# --- Reed switch: gate opened (closed -> open edge) ---
reed = Pin(cfg.REED_PIN, Pin.IN, Pin.PULL_UP) if cfg.REED_PIN is not None else None
reed_last = reed.value() if reed else 0


def gate_opened():
    global reed_last
    if not reed:
        return False
    v = reed.value()
    opened = v == 1 and reed_last == 0  # switch closed (0) when gate is shut
    reed_last = v
    return opened


# --- Main loop ---
last_sent = {}  # event_type -> ticks_ms


def cooled_down(event_type, now):
    t = last_sent.get(event_type)
    return t is None or time.ticks_diff(now, t) >= cfg.COOLDOWN_MS


def report(event_type, now, cls=packet.CLASS_UNKNOWN):
    if cooled_down(event_type, now):
        last_sent[event_type] = now
        send(event_type, cls)


send(packet.BOOT)
last_heartbeat = time.ticks_ms()
last_vehicle = None
pending_motion = None  # ticks_ms of a confirmed PIR hit waiting to see if it was a vehicle

while True:
    now = time.ticks_ms()

    if mag_confirmed():
        last_vehicle = now
        pending_motion = None
        report(packet.VEHICLE, now, packet.CLASS_VEHICLE)

    if pir and pir_confirmed(now):
        recently_vehicle = last_vehicle is not None and time.ticks_diff(now, last_vehicle) < cfg.VEHICLE_HOLD_MS
        if not recently_vehicle and pending_motion is None:
            pending_motion = now

    # A PIR hit with no magnetometer change means a person or animal.
    if pending_motion is not None and time.ticks_diff(now, pending_motion) >= cfg.VEHICLE_HOLD_MS:
        pending_motion = None
        report(packet.MOTION, now)

    if gate_opened():
        report(packet.GATE_OPEN, now)

    if time.ticks_diff(now, last_heartbeat) >= cfg.HEARTBEAT_MS:
        last_heartbeat = now
        send(packet.HEARTBEAT)

    time.sleep_ms(100)
