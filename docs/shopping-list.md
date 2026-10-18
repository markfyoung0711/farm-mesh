# Shopping list – Phase 1 (gate alert)

Covers one gate node and the Pico W hub on the tower. You already own the Pico W. Prices are rough US street prices.

## Electronics

| Qty | Item | For | ~Price |
| --- | --- | --- | --- |
| 1 | Raspberry Pi Pico H (or a second Pico W, for flexibility) | Gate board | $5–7 |
| 2 | Waveshare Pico-LoRa-SX1262 HAT, **915 MHz** version | Radio, one per board | $15–20 each |
| 1 | AM312 mini PIR (buy a 3- or 5-pack, they're cheap) | Person or animal | $5 |
| 1 | GY-271 QMC5883L magnetometer board | Vehicle detection | $5 |
| 1 | Magnetic reed switch, N.O., outdoor-rated (optional) | Gate open | $5 |
| 2 | 915 MHz omni antenna, 2–3 dBi, SMA | Tower and gate | $10–15 each |
| 2 | u.FL (IPEX) to SMA bulkhead pigtail, 10–15 cm | Antenna through enclosure wall | $5 each |
| 1 | 915 MHz SMA lightning arrestor, plus a ground wire to the tower | Tower antenna | $15 |
| 1 | Set of headers, Dupont jumpers, solder, heat shrink | Wiring | $10 |

## Power

| Qty | Item | For | ~Price |
| --- | --- | --- | --- |
| 1 | 12 V to 5 V buck converter, waterproof, 1 A or more | Gate: tap the gate's solar system | $8 |
| or 1 | 2 W 6 V solar panel + CN3791 MPPT board + 18650 cell and holder | Gate: standalone solar instead | $25 |
| 1 | Tower hub power: 5 V USB supply, PoE splitter (5 V micro-USB), or 10 W panel + battery pack | Hub. Open question in the design doc | $10–40 |

## Mounting and weatherproofing

| Qty | Item | For | ~Price |
| --- | --- | --- | --- |
| 2 | Light-colored IP65 junction box, about 150 × 100 × 70 mm | Gate and tower enclosures | $10 each |
| 4–6 | PG7 / PG9 cable glands | Sensor and power cables | $8 per pack |
| 1 | 4×4 treated wood post, 8 ft, plus concrete or post spikes | Gate node post, 3 ft or more from the metal gate | $20 |
| 1 | Small antenna mast or pipe clamp, stainless hose clamps | Antenna at 6–8 ft on the post, and at the tower top | $10 |
| 1 | UV-resistant zip ties, split loom or conduit | Hog and squirrel protection | $10 |
| 1 | Desiccant packs | Inside enclosures | $5 |

## Tools and setup

- USB micro-B data cable (the Pico H uses micro-USB)
- Soldering iron, if your Pico has no headers
- Multimeter, for checking buck converter output and battery voltage

**Rough total:** $175–250, depending on power choice and antennas.

## Decisions before ordering

- **LoRa module:** the firmware defaults to the Waveshare HAT. A bare E22-900M22S works too, but needs wiring and a pin change in `firmware/lib/radio.py`.
- **Tower power:** this decides which power row to buy.
- **Gate-open signal:** check whether the gate controller has a dry-contact output before buying a reed switch.
