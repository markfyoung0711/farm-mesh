# Minimal QMC5883L magnetometer driver (GY-271 boards).

import struct

ADDR = 0x0D
REG_DATA = 0x00
REG_STATUS = 0x06
REG_CTRL1 = 0x09
REG_SET_RESET = 0x0B

# OSR 512, range 8 G, 10 Hz, continuous mode
CTRL1_CONTINUOUS = 0b00_01_00_01


class QMC5883L:
    def __init__(self, i2c, addr=ADDR):
        self.i2c = i2c
        self.addr = addr
        if addr not in i2c.scan():
            raise OSError("QMC5883L not found at 0x%02x" % addr)
        i2c.writeto_mem(addr, REG_SET_RESET, b"\x01")
        i2c.writeto_mem(addr, REG_CTRL1, bytes([CTRL1_CONTINUOUS]))

    def ready(self):
        return self.i2c.readfrom_mem(self.addr, REG_STATUS, 1)[0] & 0x01

    def read(self):
        """Raw (x, y, z) counts."""
        return struct.unpack("<hhh", self.i2c.readfrom_mem(self.addr, REG_DATA, 6))

    def magnitude(self):
        x, y, z = self.read()
        return (x * x + y * y + z * z) ** 0.5
