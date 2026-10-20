# farm-mesh

A low-cost, solar-powered LoRa sensor grid that reports movement across the whole farm and acreage — deer, hogs, dogs, people and vehicles — to a single hub on the 50 ft tower. Every detection comes out of one API with location, time and, when the sensor can tell, object type.

See [docs/design.md](docs/design.md) for the full design.

## Goal

Monitor the entire property from one hub:

- Cover roughly 50 acres (about 450 m × 450 m) of woods and fields with 20 to 40 cheap nodes.
- Run unattended on solar, with no WiFi or internet needed between sensors and hub.
- Locate movement from each node's fixed coordinates and the order in which neighboring nodes fire.
- Start motion-only, and add size, vehicle or camera-based species detection where it pays off.
- Watch it all from an online monitor — phone app or workstation dashboard — with live events, a map, alerts and node health.

## Subgoals

### 1. Front gate alert (current)

A Meshtastic mesh with one sensor node at the front gate and a gateway at the top of the tower, 207 m apart.

- **Gate node:** a Pico H with a Waveshare SX1262 LoRa board running Meshtastic. Its Detection Sensor watches a PIR aimed along the approach. It's mounted on a wood post away from the metal gate and powered from the gate's solar system.
- **Tower gateway:** two boards in one box. A Meshtastic radio (Pico H + Waveshare, Router role) hears and relays for the mesh. Beside it, a Pico W runs our MicroPython brain: it reads the radio over UART, logs each event, and pushes an alert to a phone (ntfy or Pushover) over the house WiFi.
- **Handheld:** a Heltec V3 running Meshtastic with the phone app, for range walks and test messages.
- **Outcome:** a phone alert when a person or animal is at the gate, and an alert when any node goes silent.
- **Next:** a custom Meshtastic C++ module on the gate for vehicle detection (magnetometer) and the gate-open switch.

### 2. Mesh grows from the tower

More Meshtastic nodes join the same encrypted channel, and relays are added only where the canopy blocks the signal. Later, a Raspberry Pi at the house takes over from the Pico W brain for heavier work: node coordinates, SQLite, the API and an MQTT feed.

### 3. Pilot in the woods

A range walk to find dead spots, then 3 or 4 sleeping sensor nodes on the busiest trail and creek crossing. Log battery voltage for two weeks to confirm shaded nodes stay charged.

### 4. Full grid

Scale to 20 to 40 nodes placed on trails, crossings, fence gaps and field edges, add relays only where the canopy blocks the signal, and add camera nodes at chokepoints for species labels. Group detections into tracks with heading and speed.

### 5. Online monitor

An app or workstation dashboard, reachable from anywhere, built on the hub's API and MQTT feed:

- Live event feed and push alerts (gate, vehicle, large group at night).
- Map of nodes and recent detections and tracks.
- Node health: last heard, battery, signal strength, faults.
- Event history with search by node, time and object type.

It starts as simple phone alerts in subgoal 1 and grows into a full dashboard (Grafana, Node-RED or a Leaflet map) once the Raspberry Pi joins in subgoal 2.

## Repository

- `docs/design.md` — design doc: hardware, power, radio configuration, packet format and API
- `docs/gateway-build-guide.md` — step-by-step build of the tower gateway (Meshtastic radio + Pico W brain), with explanations
- `docs/components.md` — Phase 1 component design: pins, code, bring-up tests and status for each part
- `docs/shopping-list.md` — parts for Phase 1 (gate alert)
- `firmware/` — MicroPython gateway brain for the Pico W. The radios run stock Meshtastic. See [firmware/README.md](firmware/README.md).
- `tests/` — PC-side tests for the packet format and the Meshtastic serial API
- `nodes.example.csv` — template for node coordinates. Copy it to `nodes.local.csv` (git-ignored) for real locations.
