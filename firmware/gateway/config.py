# Gateway brain (Pico W) settings. WiFi and alert credentials live in secrets.py (git-ignored).

# UART to the Meshtastic tower radio (Pico H + Waveshare). Cross the wires: our TX -> its RX.
UART_ID = 0
UART_TX = 0  # GP0, pin 1
UART_RX = 1  # GP1, pin 2
UART_BAUD = 115200  # must match the radio's Serial module setting

# Node names come from the radio's node list (the "long name" set in the Meshtastic app).
WATCH_NODES = ("GATE-01",)  # alert if one of these goes silent
SILENT_MS = 2 * 60 * 60 * 1000  # Meshtastic nodes report telemetry every 30 min by default

# Detection Sensor messages look like "<sensor name> detected". Map the sensor name to an event.
DETECTION_NAMES = {
    "Motion": "motion",
    "Gate": "gate",
}
ALERT_TEXT_MESSAGES = True  # also push ordinary text messages, e.g. a test sent from the handheld

# Alert service: "ntfy" or "pushover"
ALERT = "ntfy"
NTFY_SERVER = "https://ntfy.sh"
COOLDOWN_MS = 60_000  # per node and event

LOG_FILE = "events.log"
LOG_MAX_BYTES = 200_000  # rotate to events.old when larger

RADIO_CHECK_MS = 30 * 60 * 1000  # re-handshake with the radio if it has sent nothing for this long
HEARTBEAT_MS = 5 * 60 * 1000  # keep the radio's API session alive
WATCHDOG_MS = 8000  # RP2040 maximum is about 8.3 s; None to disable
