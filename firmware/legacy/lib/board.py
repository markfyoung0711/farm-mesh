# Per-board pins, picked from the chip MicroPython is running on.
#   rp2   -> Pico / Pico W + Waveshare Pico-LoRa-SX1262 (gateway, gate node)
#   esp32 -> Heltec WiFi LoRa 32 V3 (handheld test node)

import sys

if sys.platform == "esp32":
    NAME = "Heltec WiFi LoRa 32 V3"
    LORA = {"spi_id": 1, "sck": 9, "mosi": 10, "miso": 11, "cs": 8, "busy": 13, "dio1": 14, "reset": 12}
    LED = 35  # white LED
    BUTTON = 0  # PRG button
    OLED = {"sda": 17, "scl": 18, "reset": 21, "vext": 36}  # Vext low powers the OLED
else:
    NAME = "Pico + Waveshare Pico-LoRa-SX1262"
    # Checked against waveshare.com/wiki/Pico-LoRa-SX1262
    LORA = {"spi_id": 1, "sck": 10, "mosi": 11, "miso": 12, "cs": 3, "busy": 2, "dio1": 20, "reset": 15}
    LED = "LED"
    BUTTON = 14  # Kepler kit button to GND
    OLED = None
