# Tower hub settings. WiFi and alert credentials live in secrets.py (git-ignored).

# node_id byte value -> name, matching NODE_ID in each node's config.py and nodes.local.csv
NODES = {
    1: "GATE-01",
    99: "TEST-01",  # bench tester (firmware/tester)
}
QUIET_NODES = {99}  # no "silent" alerts for these; the tester is off most of the time

# Alert service: "ntfy" or "pushover"
ALERT = "ntfy"
NTFY_SERVER = "https://ntfy.sh"

COOLDOWN_MS = 60_000  # per node and event type, on top of the node's own cooldown
HEARTBEAT_MS = 3 * 60 * 60 * 1000  # must match the nodes
MISSED_HEARTBEATS = 2  # alert when a node is silent this many heartbeat periods

LOG_FILE = "events.log"
LOG_MAX_BYTES = 200_000  # rotate to events.old when larger

WATCHDOG_MS = 8000  # RP2040 maximum is about 8.3 s; None to disable
