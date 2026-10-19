# Shopping list – Phase 1 (gate alert)

Everything stays inside one LoRa mesh. The gate node is wireless: its only wires are short runs on its own post to a sensor or the gate's solar battery. Nothing runs from the gate to the tower or the house.

- **DIY:** Pico boards with LoRa HATs, soldered and wired by you.
- **OTS (off the shelf):** prebuilt Meshtastic hardware (RAK WisBlock / WisMesh). Modules snap together with no soldering, and you configure them from the Meshtastic phone app.

Both columns join the same Meshtastic mesh as the Phase 2 woods nodes. Prices are rough US street prices. OTS model names are examples from memory, so check current models before buying.

## Hub (tower)

| Item | DIY | ~Price | OTS | ~Price |
| --- | --- | --- | --- | --- |
| Mesh radio | Pico W (owned) + Waveshare "Pico SX1262 LoRa Node Module" (Pico-LoRa-SX1262), **868M/915M variant, 850–930 MHz**; not the UART "SX1262 LoRa HAT" | $23 (Amazon, Oct 2026) | RAK WisMesh Ethernet/MQTT gateway (PoE). Meshtastic Router role, sends events to the house network over Ethernet | $80–120 |
| Antenna | 915 MHz omni, 2–3 dBi, SMA + u.FL-to-SMA bulkhead pigtail | $15–20 | 915 MHz outdoor omni, 3 dBi fiberglass | $25–50 |
| Surge protection | 915 MHz SMA lightning arrestor + ground wire to the tower | $15 | Same | $15 |
| Enclosure | Light-colored IP65 junction box + cable glands + desiccant | $20 | RAK Unify enclosure (IP65) or the box sold with the gateway | $20–30 |
| Power | 5 V USB supply, PoE splitter (5 V micro-USB), or 10 W panel + battery | $10–40 | PoE injector + outdoor Ethernet run from the house (11 m) | $15–30 |
| Alerts / app | `firmware/hub` → ntfy or Pushover | $0 | MQTT → small service at the house → ntfy, Pushover or Home Assistant | $0 |

## Gate node (wireless)

| Item | DIY | ~Price | OTS | ~Price |
| --- | --- | --- | --- | --- |
| Board + radio | Pico H + same Waveshare Pico SX1262 LoRa Node Module | $28–30 | RAK WisBlock Meshtastic starter kit (RAK19007 base + RAK4631 core) | $30–40 |
| Person / animal | AM312 mini PIR (buy a 3- or 5-pack) | $5 | RAK12006 PIR module, snap-in. Meshtastic's Detection Sensor module sends the alert. | $8–12 |
| Vehicle | GY-271 QMC5883L magnetometer board | $5 | No stock Meshtastic vehicle sensor. Add the same QMC5883L and custom firmware later, or skip it. | $0–5 |
| Gate open (optional) | Outdoor N.O. reed switch on the post, magnet on the gate | $5 | Same reed switch into a WisBlock GPIO. Detection Sensor handles it. | $5 |
| Antenna | 915 MHz omni, 2–3 dBi, SMA + u.FL-to-SMA pigtail | $15–20 | Included in the kit, or upgrade to a 3 dBi outdoor omni | $0–30 |
| Power | 12 V → 5 V waterproof buck converter, **micro-USB output**. For example, PlusRoc 15W DC-DC (B09DGDQ48H), "Micro USB Connector" style. Add an inline 1–2 A fuse. Or a 2 W panel + CN3791 + 18650. | $10–25 | RAK Unify enclosure with built-in solar panel + LiPo or 18650. No wires at all. | $35–50 |
| Enclosure | IP65 junction box + PG7/PG9 glands + desiccant | $20 | Included with the solar Unify enclosure | $0 |
| Mounting | 4×4 treated post (8 ft) 3 ft or more from the metal gate, clamps, UV zip ties | $40 | Same | $40 |
| Wiring supplies | Headers, jumpers, solder, heat shrink | $10 | — | $0 |

## Handheld test node (DIY)

A pocket device with a screen. The PRG button fakes sensor hits, and the screen shows everything the gateway sends. It also serves as the range-walk handheld. See [components.md](components.md), type 3.

**Pick: the "LoRa V3" ESP32-S3 + SX1262 bundle on Amazon, $37 (Oct 2026).** It includes:

- the Heltec V3-style board: ESP32-S3FN8, SX1262, 0.96 in OLED, USB-C, two JST 1.25 battery ports, and a u.FL antenna port
- 915 MHz antennas
- an 1100 mAh protected LiPo, made for this board, so no polarity worries
- a fitted N32 case

Before buying, check that the option says **915 MHz** and that it has a normal return window. Buying the same parts separately runs about $36–47:

| Item | Separately | ~Price |
| --- | --- | --- |
| Heltec WiFi LoRa 32 V3, **915 MHz** version | SX1262 radio, OLED, button, LiPo charger and antenna on one board. Avoid the 433 and 868 MHz versions. | $20–25 |
| 3.7 V LiPo, about 1000 mAh, **JST 1.25 2-pin** | Check the red/black wires match the + and − marks by the Heltec's battery socket. Polarity varies between sellers, and reversing it can kill the board. | $8–10 |
| Heltec V3 case (3D-printed or acrylic) | Search "Heltec V3 case". Check that it fits the battery. | $8–12 |

**Waveshare boards in total: 2,** one each for the gateway and the gate node. The handheld's radio is built in.

## Totals

| | DIY | OTS |
| --- | --- | --- |
| Rough total, gateway + gate node | **$200–275** | **$275–420** |
| Handheld test node | + $37 (bundle) | + $37 (bundle) |
| Skills | Soldering, flashing firmware, wiring sensors | Snapping modules together, Meshtastic app setup, running a small MQTT service |
| Each extra mesh node (Phase 2) | About $40–60 | About $75–110 |

## Tools

- USB data cable: micro-B for the Pico, USB-C for the RAK4631
- Soldering iron (DIY only, if your Pico has no headers)
- Multimeter, for checking buck converter output and battery voltage

## Decisions before ordering

- **DIY or OTS:** they can mix. For example, an OTS gateway on the tower with DIY nodes in the woods works, as long as everything runs Meshtastic.
- **LoRa module (DIY):** the Waveshare HAT is also a supported Meshtastic board for the Pico, so it works with either firmware.
- **Tower power:** mains, PoE or solar. The OTS gateway expects PoE.
- **Vehicle detection:** keep the magnetometer (custom firmware) or rely on PIR plus the gate-open switch.
