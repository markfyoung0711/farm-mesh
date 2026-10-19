# Tiny text console: scrolling lines on the Heltec V3's 128x64 OLED, and print() on every board.
# The OLED needs the ssd1306 driver: mip.install("ssd1306")

import time

from machine import I2C, Pin

import board

COLS = 16  # 8 px font on 128 px
ROWS = 8


class Screen:
    def __init__(self):
        self.oled = None
        self.lines = []
        if not board.OLED:
            return
        try:
            import ssd1306

            Pin(board.OLED["vext"], Pin.OUT, value=0)
            rst = Pin(board.OLED["reset"], Pin.OUT, value=0)
            time.sleep_ms(20)
            rst.value(1)
            i2c = I2C(0, sda=Pin(board.OLED["sda"]), scl=Pin(board.OLED["scl"]), freq=400_000)
            self.oled = ssd1306.SSD1306_I2C(128, 64, i2c)
        except Exception as e:
            print("no OLED:", repr(e))

    def show(self, text, short=None):
        """Print text; put short (or text) on the OLED as a new bottom line."""
        print(text)
        if not self.oled:
            return
        self.lines.append((short or text)[:COLS])
        self.lines = self.lines[-ROWS:]
        self.oled.fill(0)
        for i, line in enumerate(self.lines):
            self.oled.text(line, 0, i * 8)
        self.oled.show()
