# GATE-01 settings

NODE_ID = 1  # must match the hub's NODES table

# Sensor pins. Set a pin to None if that sensor is not fitted.
PIR_PIN = 16  # AM312 output
I2C_ID = 0  # QMC5883L on I2C0
I2C_SDA = 4
I2C_SCL = 5
REED_PIN = None  # gate-open switch to GND, internal pull-up; e.g. 17
BATTERY_ADC_PIN = None  # e.g. 26 with a divider on the 18650; None when on gate solar via buck
BATTERY_DIVIDER = 2.0  # V_batt / V_adc

# Detection
PIR_CONFIRM_HITS = 2  # rising edges needed ...
PIR_CONFIRM_MS = 4000  # ... within this window
MAG_THRESHOLD = 150  # counts of field change that mean "vehicle"; tune on site
MAG_CONFIRM_SAMPLES = 3  # consecutive samples over threshold
MAG_BASELINE_ALPHA = 0.01  # slow drift tracking for temperature and the parked state
VEHICLE_HOLD_MS = 3000  # wait this long after a PIR hit for the magnetometer to call it a vehicle
COOLDOWN_MS = 60_000  # per event type

# Radio
ACK_TIMEOUT_MS = 600
RETRIES = 3
HEARTBEAT_MS = 3 * 60 * 60 * 1000
