# Phase 1 firmware (MicroPython)

Three boards, one LoRa link: two Picos with Waveshare radios, and a Heltec V3 handheld.

- `hub/` — Pico W at the top of the tower. It receives packets, ACKs them, drops duplicates, logs them to `events.log`, pushes alerts over the house WiFi, and alerts when a node goes silent.
- `gate/` — Pico at GATE-01. Sensors: an AM312 PIR, a QMC5883L magnetometer and an optional reed switch. WiFi stays off.
- `tester/` — TEST-01 handheld tester for the Heltec WiFi LoRa 32 V3 (it also runs on a Pico + Waveshare). Short-press PRG fakes a motion event, a long press fakes a vehicle, and the OLED shows every packet it hears, including the hub's ACKs. Copy `lib/*.py` and `tester/main.py`, then `mip install ssd1306`.
- `lib/` — shared files: per-board pins (`board.py`), the 8-byte packet format, SX1262 radio setup, the OLED console and the magnetometer driver.
- `tools/` — bring-up tests: `radio_test.py` (ping/pong range test with RSSI and SNR) and `sensor_test.py` (live PIR, magnetometer, reed and battery readings).

Per-component pins, tests and status are tracked in [docs/components.md](../docs/components.md).

## Wiring (gate)

| Part | Pico pin |
| --- | --- |
| LoRa HAT (Waveshare Pico-LoRa-SX1262) | Plugs on. SPI1 on GP10/11/12, CS GP3, BUSY GP2, DIO1 GP20, RESET GP15 |
| AM312 OUT | GP16 (VCC 3V3, GND) |
| QMC5883L SDA / SCL | GP4 / GP5 (VCC 3V3, GND) |
| Reed switch (optional) | GP17 to GND, then set `REED_PIN = 17` |

Pins for each board type live in `lib/board.py`. For a bare SPI module such as the E22-900M22S, edit the rp2 profile there.

## Flash

1. Flash MicroPython onto each board: the Pico W build for the hub, the Pico build for the gate.
2. Install the LoRa driver on each board, using `mpremote` (`pip install mpremote`). The hub needs WiFi for this, or copy the packages over from a PC.
   ```
   mpremote mip install lora-sync lora-sx126x
   ```
3. Hub:
   ```
   cp firmware/secrets_example.py firmware/secrets.py   # fill in WiFi and ntfy topic
   mpremote cp firmware/lib/*.py firmware/secrets.py :
   mpremote cp firmware/hub/config.py firmware/hub/main.py :
   ```
4. Gate:
   ```
   mpremote cp firmware/lib/*.py :
   mpremote cp firmware/gate/config.py firmware/gate/main.py :
   ```
5. Subscribe to your ntfy topic in the ntfy phone app. You should get a "Hub online" alert, and the gate's boot packet should appear in `mpremote repl` output and in `events.log`.

## Tune on site

- `MAG_THRESHOLD`: watch the magnitude with the REPL while driving past, then set the threshold well above the quiet noise.
- `TCXO_MV` in `lib/radio.py`: if the radio fails to initialize, try `None` or the module's datasheet value.
- RSSI and SNR are logged with every event. Check them before you lock the mounting.

## Tests

`pytest tests` runs the packet tests on a PC. No hardware needed.
