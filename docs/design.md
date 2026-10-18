# Farm Woods Movement Sensor Network – Design Doc

Oct 18, 2026 · @Mark

## Goals and scope

The system reports where movement happens across about 50 acres of woods, using cheap solar LoRa sensor nodes that talk to one hub on the tower.

- Detect and locate deer, hogs, vehicles, dogs and people.
- Cover roughly 450 m × 450 m of woods with 20 to 40 low-cost nodes.
- Run unattended on solar, with no WiFi or internet needed between sensors and hub.
- Expose every detection through one API with location, time, and object type when the device can tell.
- Default device is motion-only. Size or species recognition is an optional upgrade, not a requirement.

A LoRa node reports which sensor saw something, not where the animal stands. Position comes from each node's fixed coordinates and the order in which neighboring nodes fire.

## Phase 1: gate alerts with a Pico W

Phase 1 sends one alert when someone is at the gate or a vehicle drives by, from a single sensor at the gate to a hub on the tower. It does no species identification. The Meshtastic mesh and multi-node tracking below are Phase 2.

| Part | Choice | Notes |
| --- | --- | --- |
| LoRa radio, both ends | SX1262 915 MHz module on the Pico, such as a Waveshare Pico LoRa HAT or an Ebyte E22-900M22S wired over SPI | RadioLib (C++, Arduino-Pico) and MicroPython both have SX126x drivers. Use the 915 MHz US band. |
| Hub board | Pico W (already owned) at the top of the tower | Joins the house WiFi, which is about 11 m away, and sends alerts out. |
| Gate board | A second Pico (plain or W) | WiFi stays off at the gate to save power. |
| Person or animal | AM312 mini PIR (3.3 V, tens of µA), aimed along the approach | Cannot tell a person from a deer. |
| Vehicle | QMC5883L magnetometer on I2C, beside the drive | A car shifts the magnetic field, a person barely does. |
| Gate open | Reed switch, or the gate controller's own open signal through an optocoupler | Do not tap the controller's safety circuits. |
| Alert path | Hub POSTs to ntfy or Pushover, which pushes to your phone | Also logs every event with a time stamp. |

**Logic:**

1. A PIR or magnetometer trigger must repeat within a few seconds before the node sends.
2. The node sends a short packet: node ID, sequence number, event type, battery.
3. The hub replies with an ACK. The node retries up to 3 times after a random delay.
4. The hub drops duplicate sequence numbers, adds the time, logs the event and pushes the alert.
5. A 60 second cooldown per event type keeps a parked truck from flooding the phone.
6. The node sends a heartbeat every few hours, so a dead battery shows up as a fault.

A magnetometer hit means vehicle. A PIR hit with no magnetometer change means person or animal at the gate.

**Gate mounting:** the gate is metal and detunes antennas, so put the node, PIR and antenna on a wood or PVC post 3 ft or more from the gate, with the antenna 6 to 8 ft up. Wood is the better choice. If the gate-open signal is a reed switch, put the switch on the post and the magnet on the gate.

**Gate power:** tap the gate's solar system through a 12 V to 5 V buck converter, or use a 2 W panel and one 18650 cell with a charge board. A Pico draws about a milliamp or more even when quiet, and tens of mA with WiFi on. The gate has sun, so this works, but the shaded Phase 2 nodes will need a lower-power board.

**Range:** the gate is 207 m from the tower. Trees there reach about 50 ft, the same height as the tower, so expect a solid link. Check RSSI and SNR at the hub before locking the mounting.

## Architecture

&#91;embedded content: architecture · sensors, tower hub, Pi, your devices\]

Sensor nodes send small packets over 915 MHz LoRa straight to the radio at the top of the tower, and relay nodes are added only where trees block the signal. The Pi decodes each packet, adds the node's coordinates and a timestamp, and serves the API. Its own WiFi is only for reaching the data from your phone or laptop, and the tower's existing WiFi radio is not involved.

## Site and fixed locations

The hub sits on an existing 50 ft tower, and GATE-01 is the first sensor, about 207 m away. Both positions are known, so neither node needs a GPS fix in service.

| Point | Role | Offset from tower |
| --- | --- | --- |
| Tower | Hub, origin (0, 0) | 0 |
| GATE-01 | Sensor node 1 | 150 m N, 142 m W (207 m, bearing about 317°) |

Real latitude and longitude live in `nodes.local.csv`, which is git-ignored and never committed. Copy `nodes.example.csv` to start one.

- Treat the tower as (0, 0) and convert every node to meters east and north. At this latitude, 0.001° of latitude is about 111 m and 0.001° of longitude is about 94 m.
- The tower already carries a WiFi radio. That radio is not part of the sensor network.
- A 50 ft (15 m) antenna may sit at or below the treetops, since East Texas pines and hardwoods often reach 60 to 80 ft. The gate is well within range. The far edges of the woods are the real test.
- Trees at the gate reach about 50 ft, so the tower antenna sits at about treetop height there, and the gate has sun for solar. Open item: tower power, and the layout of the woods relative to the tower.

Other known points:

| Point | Offset from tower |
| --- | --- |
| House, wired to the tower radio | about 4 m N, 10 m W (11 m) |
| Second WiFi radio | about 2 m S, 140 m W |

The tower's WiFi radio serves another property and is hardwired to the house, so a server at the house can reach the hub over the existing network. The second WiFi radio sits about 153 m due south of the gate.

## Hardware

Every node is a LoRa board plus a sensor and a solar pack. Only the hub needs a computer. The capability tier says how much to trust a node's object type.

| Tier | `capability` | Sensor | What it reports |
| --- | --- | --- | --- |
| 1 (default) | `motion_only` | PIR, aimed low | Something moved here |
| 2 | `size_class` | mmWave radar (LD2410 / LD2450) or dual-height PIR | Small, medium or large; speed |
| 3 | `vehicle` | Magnetometer or geophone | Vehicle or not |
| 4 | `camera_classifier` | ESP32-S3-CAM or Pi Zero 2 with a small model | Species or person label plus confidence |
| 5 | `gate_switch` | Reed switch on the latch | Open or closed |

**Node boards:** Heltec, LilyGO or RAK, $20 to $35 each. A basic detection node is about $40 to $60 complete. A camera node is $80 to $150.

**Hub:** a Raspberry Pi (Zero 2 W or 4) with a USB Meshtastic node, running the decoder, SQLite and the API. The Pi's own WiFi serves your phone or laptop, or acts as an access point at the farm. The tower's existing WiFi radio is not needed. A LoRa HAT on the Pi is an alternative, but takes more setup.

**Antennas:**

- Mount the hub's 915 MHz omni antenna at the very top of the tower, 3 ft or more from the WiFi radio and clear of tower steel.
- Use a few dBi of gain at most. High-gain antennas flatten the pattern.
- Keep coax short. Put the radio or the whole Pi in a light-colored weatherproof box at the top and run only power down.
- Ground the mast and add surge protection.
- Sensor antennas go 6 to 8 ft up, upright, away from metal.

**GATE-01:** reed switch on the latch, magnetometer beside the drive, PIR along the approach. Open gate plus magnetometer means a vehicle entering. PIR alone means a person or animal. Open gate with no vehicle means someone on foot. Open item: gate type (metal, wood, chain-link; single or double swing).

## Power and solar

Shade, not load, limits solar here. Sleeping nodes draw only a few hundred microamps, but canopy cuts panel output to roughly 10 to 20% of rating, and winter is worse. Size batteries for 5 to 7 days with no sun.

| Node type | Radio mode | Average draw | Panel | Battery |
| --- | --- | --- | --- | --- |
| Sleeping sensor | Client Mute, deep sleep | 0.2 to 0.5 mA | 1 to 2 W | 1× 18650 |
| Camera classifier | Wake on trigger | 1 to 5 mA | 3 to 5 W | 2× 18650 |
| Router / backbone | Always listening | 10 to 40 mA | 3 to 6 W | 2× 18650 or LiFePO4 |
| Tower hub | Always on | 50+ mA (Pi: 1 to 3 W) | Tower power or 10 W+ | Large pack |

- **Controller:** use an MPPT or CN3791-style board with a low-voltage cutoff, such as RAK WisBlock solar kits or a T-Beam. Cheap game cam chargers may not carry a continuous load.
- **Voltage match:** check the game cam charger's output (6 V or 12 V) against the charge board's input. Use a buck converter if they differ.
- **Cold charging:** Li-ion must not charge below 0 °C (32 °F). LiFePO4 tolerates heat and cold better.
- **Heat:** use white or light enclosures and keep them out of direct summer sun.
- **Panel placement:** face south, tilt about 30°, and put each panel in a gap in the canopy or on a short pole above brush. Wipe off dust and pollen twice a year.
- **Wildlife:** mount gear 5 to 6 ft up, run wiring in conduit or cable ties, and use sealed glands. Hogs rub and chew, and squirrels go after wiring.
- **Hub on solar only:** the Pi is the largest draw in the system. If the tower has mains or PoE, use it. Otherwise a Zero 2 W with a 20 to 30 W panel and a good battery works.

## Mesh and radio configuration

Use Meshtastic with the tower hub as the main listener. Most sensors should reach the tower directly, so relay nodes are needed only where the canopy blocks the signal.

- **Tower hub:** Router role, always on.
- **Sensor nodes:** Client Mute. They wake on motion, transmit and sleep, and never relay, which keeps battery life at months.
- **Backbone relays (5 to 8, only if needed):** Router role, high in trees or on poles with larger solar. Place them where the range walk shows dead spots.
- **Preset:** Short/Fast or Medium/Fast. At 450 m across, Long/Slow only wastes airtime.
- **Locked position:** enter each node's coordinates as a fixed position, then turn the GPS off. This saves power and stops a drifting fix from moving the node on the map. Accuracy from a phone at a clearing beats a canopy fix, which can be off by 5 to 15 m.
- **Detection Sensor module:** Meshtastic's built-in GPIO trigger can send events. A custom firmware that sends the compact packet in the API section is the alternative.
- **Mesh traffic:** routers flood messages, which is fine for sparse event traffic. Keep nodes from chattering. If the mesh is outgrown, options are a custom RadioLib mesh or a LoRaWAN star with a gateway at the tower.

**Placement:** do not use a uniform grid. PIRs see only 10 to 15 m. Put nodes where movement is funneled: game trails, creek crossings, fence gaps, roads, two-tracks, feeders and field edges. Fill in with a loose 60 to 80 m grid. Position then comes from sequences, such as node 7, then 12, then 13 meaning something moving northeast along the creek.

## Packet format and API

The API message carries location, time and object type, but the node sends none of that. Nodes send a tiny packet over LoRa, and the hub service adds coordinates and time from its node table.

**Over the air (about 8 bytes):**

| Field | Size | Meaning |
| --- | --- | --- |
| node\_id | 2 bytes | Which sensor |
| seq | 1 byte | Sequence counter, for dedup |
| event\_type | 1 byte | motion, gate, vehicle, heartbeat |
| class | 1 byte | Object class (0 = unknown) |
| confidence | 1 byte | 0 to 100 |
| count | 1 byte | Number of objects, if known |
| battery | 1 byte | Voltage code, so health rides along |

**On the hub:** a Python service reads packets from the USB radio with the Meshtastic library, drops repeated (node\_id, seq) pairs, looks up the node's fixed coordinates, stamps the receive time, and stores the event in SQLite. Node coordinates load from `nodes.local.csv`. Time comes from the hub, so nodes need no clock sync. Moving a sensor means editing one table row.

**API message, motion-only node:**

```json
{
  "id": "evt_000123",
  "time": "2026-10-18T21:42:07Z",
  "node_id": "GATE-01",
  "location": { "lat": 30.00135000, "lon": -95.00151000 },
  "event": "detection",
  "object_type": "unknown",
  "size_class": null,
  "confidence": null,
  "count": null,
  "capability": "motion_only",
  "signal": { "rssi": -98, "snr": 6.5, "hops": 0 },
  "battery_v": 3.92
}
```

The coordinates above are placeholders. A node with size or species recognition sends the same schema with the optional fields filled, for example `"object_type": "hog"`, `"size_class": "medium"`, `"confidence": 0.94`, `"count": 4`, `"capability": "camera_classifier"`. The schema never changes between device types. `capability` tells the reader how far to trust `object_type`.

**Object vocabulary (fixed list, fits one byte):** `unknown`, `small_animal`, `deer`, `hog`, `canine`, `person`, `vehicle`, `bird`, `other`. Tier 2 nodes report only `size_small`, `size_medium` or `size_large`, never a species they cannot tell apart.

**Endpoints:**

- `GET /events?since=` for raw detections
- `GET /nodes` for node table, last heard, battery and signal
- `GET /tracks` for grouped movement
- MQTT topic `farm/events/<node_id>` for live subscribers

**Tracks and health:** the hub groups detections from neighboring nodes within a time window into one `track_id` with estimated heading and speed. Each node sends a heartbeat every few hours with battery and signal. A silent node shows as a fault, not as "nothing happening."

## Detection and classification

Motion nodes tell you something is there. Species identification needs a camera. Vehicles are the easiest target, and dogs and hogs the hardest without imaging.

| Target | Cheap method | Reliability |
| --- | --- | --- |
| Vehicles | Magnetometer or geophone | Good |
| Large vs small animals | mmWave radar or dual-height PIR (size and speed) | Moderate |
| Hogs vs deer | Group size, dwell time and time of night, plus camera | Poor without a camera |
| People vs animals | Camera with on-device AI | Needs a camera |
| Dogs | Camera | Poor without imaging |

The approach is detection nodes everywhere, plus camera nodes at chokepoints. A camera node classifies locally (for example MegaDetector or YOLO on an ESP32-S3-CAM or a Pi Zero 2) and sends only the label over LoRa, such as "hog ×4, 94%". Photos stay on an SD card. When a PIR chain fires, the hub can flag "large group, nighttime, fast" so you know which camera to check.

**False trigger control:**

- Require two triggers within a few seconds before transmitting.
- Enforce a 30 to 60 second cooldown so a lingering animal does not flood the channel.
- Aim PIRs low and away from open sky and sunlit foliage. Wind-blown brush and sun-heated leaves are the main false sources.
- Mount antennas high. Dense foliage cuts LoRa range, so test before fixing spacing.

## Pilot, costs and open questions

Start with a pilot of 5 or 6 nodes before buying 30. A starter system with 20 detection nodes, 4 camera nodes and the hub lands around $1,500 to $2,000.

**Pilot steps:**

1. Mount the Router node and antenna at the top of the tower, with the Pi wired to it.
2. Build GATE-01 with its fixed coordinates, reed switch, magnetometer and PIR, and check link quality (RSSI and SNR) back to the tower.
3. Walk a battery node through the woods with its antenna at 6 to 8 ft and mark where the signal drops. Those spots get relays.
4. Add 3 or 4 sleeping sensor nodes on the busiest trail and creek crossing.
5. Log battery voltage from each node for two weeks to see which spots stay charged in the shade.
6. Write the hub service and API, then add the dashboard (Node-RED or Grafana, or a Leaflet map).

**Risks:**

- Canopy may cut range below what the tower antenna can reach.
- Shaded panels may not keep nodes charged through winter.
- PIR false triggers from heat and wind.
- Hogs and squirrels damaging gear.
- SD card corruption on the hub, so use an SSD or read-only mode and a hardware watchdog.

**Open questions:**

- [x] Tree height near the gate: up to 50 ft, with sun for solar.
- [x] Gate: solar-powered metal gate. Antenna and electronics go on a wood post.
- [x] Tower WiFi: serves another property and is hardwired to the house, so the Pico W hub can join the house network.
- [x] Priority: track everything cheaply, starting with a gate and vehicle alert.
- [ ] Tower power: mains, PoE splitter or solar for the hub?
- [ ] Does the gate controller expose a dry-contact or limit-switch signal for gate open?
- [ ] Which LoRa module for the Pico: HAT or SPI module?
- [ ] Alert path: ntfy, Pushover or text message?
- [ ] Layout and terrain of the woods relative to the tower, for Phase 2.
