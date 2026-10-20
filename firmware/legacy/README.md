# Legacy: point-to-point MicroPython LoRa firmware

This was the first Phase 1 design. A Pico W hub and a Pico gate node talked directly over raw LoRa with our 8-byte packets and ACKs, and a Heltec V3 handheld acted as tester. The project switched to Meshtastic for relaying, encryption and the app, so none of this is used. It's kept for reference: the gate's PIR and magnetometer logic in `gate/main.py` is the starting point for the future Meshtastic C++ gate module.

These files won't run from here as they are. They expect `radio.py`, `board.py` and `packet.py` next to them on the board.
