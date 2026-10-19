# Bring-up test for the gate sensors (docs/components.md, C4–C7).
# Needs gate/config.py and lib/qmc5883l.py on the board:
#   mpremote run firmware/tools/sensor_test.py
# Prints one line every 200 ms. Drive past to pick MAG_THRESHOLD: well above the
# quiet "dev" values, well below what a vehicle gives.

import time

from machine import ADC, I2C, Pin

import config as cfg

pir = Pin(cfg.PIR_PIN, Pin.IN, Pin.PULL_DOWN) if cfg.PIR_PIN is not None else None
reed = Pin(cfg.REED_PIN, Pin.IN, Pin.PULL_UP) if cfg.REED_PIN is not None else None
adc = ADC(cfg.BATTERY_ADC_PIN) if cfg.BATTERY_ADC_PIN is not None else None

mag = None
if cfg.I2C_SDA is not None:
    i2c = I2C(cfg.I2C_ID, sda=Pin(cfg.I2C_SDA), scl=Pin(cfg.I2C_SCL), freq=100_000)
    print("i2c devices:", [hex(a) for a in i2c.scan()], "(QMC5883L is 0xd)")
    try:
        from qmc5883l import QMC5883L

        mag = QMC5883L(i2c)
    except OSError as e:
        print("magnetometer:", e)

baseline = mag.magnitude() if mag else 0.0
peak = 0.0

while True:
    out = []
    if pir:
        out.append("pir %d" % pir.value())
    if mag:
        m = mag.magnitude()
        dev = abs(m - baseline)
        peak = max(peak, dev)
        baseline += (m - baseline) * cfg.MAG_BASELINE_ALPHA
        out.append("mag %6.0f dev %5.0f peak %5.0f thr %d%s" % (
            m, dev, peak, cfg.MAG_THRESHOLD, " VEHICLE" if dev > cfg.MAG_THRESHOLD else ""))
    if reed:
        out.append("gate %s" % ("open" if reed.value() else "shut"))
    if adc:
        out.append("batt %.2f V" % (adc.read_u16() * 3.3 / 65535 * cfg.BATTERY_DIVIDER))
    print(" | ".join(out) or "no sensors configured")
    time.sleep_ms(200)
