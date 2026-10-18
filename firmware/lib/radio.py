# SX1262 setup on top of micropython-lib's lora driver.
# Install once per board: mpremote mip install lora-sync lora-sx126x

from machine import SPI, Pin
from lora import SX1262

# Waveshare Pico-LoRa-SX1262 HAT pinout. Change these for a bare SPI module (e.g. E22-900M22S).
PINS = {
    "spi_id": 1,
    "sck": 10,
    "mosi": 11,
    "miso": 12,
    "cs": 3,
    "busy": 2,
    "dio1": 20,
    "reset": 15,
}

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

# Set to the module's TCXO voltage if it has one (many SX1262 modules use 1800 mV).
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
