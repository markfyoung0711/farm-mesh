# SX1262 setup on top of micropython-lib's lora driver.
# Install once per board: mpremote mip install lora-sync lora-sx126x

from machine import SPI, Pin
from lora import SX1262

import board

# Pins come from board.py (Waveshare on a Pico, or the Heltec V3).
PINS = board.LORA

# Both ends must match. US 915 MHz band; SF7/125 kHz is plenty for 207 m.
LORA_CFG = {
    "freq_khz": 915000,
    "sf": 7,
    "bw": "125",
    "coding_rate": 5,
    "preamble_len": 12,
    "output_power": 14,  # dBm; raise toward 22 if the link is weak
    "crc_en": True,
}

# TCXO voltage. 1800 mV for both the Waveshare board and the Heltec V3.
# If init fails with an oscillator/timeout error, this is the first thing to check.
TCXO_MV = 1800


def make_modem():
    spi = SPI(
        PINS["spi_id"], baudrate=2_000_000, polarity=0, phase=0,
        sck=Pin(PINS["sck"]), mosi=Pin(PINS["mosi"]), miso=Pin(PINS["miso"]),
    )
    return SX1262(
        spi=spi,
        cs=Pin(PINS["cs"]),
        busy=Pin(PINS["busy"]),
        dio1=Pin(PINS["dio1"]),
        reset=Pin(PINS["reset"]),
        dio2_rf_sw=True,
        dio3_tcxo_millivolts=TCXO_MV,
        lora_cfg=LORA_CFG,
    )
