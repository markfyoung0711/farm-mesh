# Firmware

The mesh runs **Meshtastic**: stock firmware on every radio, configured from the Meshtastic web or phone app. The only code in this repo is the **gateway brain**, a Pico W running MicroPython. It sits beside the tower radio and turns mesh messages into logged events and phone alerts.

```
GATE-01 (Pico H + Waveshare, Meshtastic, Detection Sensor on the PIR)
        │  LoRa mesh, encrypted private channel
        ▼
TOWER radio (Pico H + Waveshare, Meshtastic, Router role, Serial module in PROTO mode)
        │  UART: GP4/GP5 ⇄ GP1/GP0, 115200 baud
        ▼
Gateway brain (Pico W, MicroPython: firmware/gateway)  ──WiFi──▶  ntfy  ──▶  phone
```

- `gateway/` — the Pico W brain. It reads the radio's serial API (framed protobufs), learns node names from the radio's node list, maps Detection Sensor messages ("Motion detected") to events, and logs to `events.log`. It pushes alerts with a cooldown and alerts when a watched node or the radio itself goes silent.
- `lib/meshproto.py` — just enough of the Meshtastic serial API for MicroPython: frame splitting, a small protobuf reader, and the `want_config` handshake.
- `lib/packet.py` — our 8-byte event format. The gate will use it with Meshtastic's `PRIVATE_APP` port once it has a custom C++ module for vehicle detection. Relays and the tower radio pass it through without decoding it.
- `secrets_example.py` — template for `secrets.py` (WiFi, ntfy topic). `secrets.py` is git-ignored.
- `legacy/` — the earlier point-to-point MicroPython LoRa firmware, kept for reference. Not used.

Per-component pins, tests and status are tracked in [docs/components.md](../docs/components.md).

## Install the gateway brain

Step by step, with explanations: [docs/gateway-build-guide.md](../docs/gateway-build-guide.md). In short:

1. Flash MicroPython (Pico W build) onto the Pico W.
2. Copy `lib/meshproto.py`, `lib/packet.py`, `secrets.py`, `gateway/config.py` and `gateway/main.py` to the Pico W's root.
3. Wire it to the tower radio: radio GP4 → brain GP1, radio GP5 ← brain GP0, GND to GND.
4. On the tower radio, enable the Serial module: mode `PROTO`, TX pin 4, RX pin 5, baud 115200.

## Tests

`pytest tests` runs the packet and serial-API tests on a PC. No hardware needed.
