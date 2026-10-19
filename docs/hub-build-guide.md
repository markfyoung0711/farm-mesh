# Building the tower hub on a Pico W – step by step

This guide builds the DIY tower hub (components C1, C2a, C9–C13 in [components.md](components.md)) from a bare Pico W to a working box on the tower. Each stage ends with a check, so you know it works before you move on. The **Learn** notes explain what is going on underneath. Skip them if you only want it working.

What you will have at the end: a Pico W at the top of the tower that hears the gate node over LoRa, answers it, logs every event, and pushes an alert to your phone over the house WiFi.

```
 GATE-01 ──LoRa 915 MHz, 207 m──▶ [ Pico W + SX1262 ] ──WiFi, 11 m──▶ house router ──▶ internet ──▶ ntfy ──▶ your phone
                                    top of the tower
```

---

## Stage 0 – Gather parts and tools

**Hub parts**

| ✓ | Part | Notes |
| --- | --- | --- |
| ☐ | Raspberry Pi Pico W | You own it. Check whether it has pins (headers) sticking out underneath. |
| ☐ | Waveshare Pico-LoRa-SX1262, **868M/915M** version | The Pico-sized board, not the UART HAT for full-size Pis |
| ☐ | Antenna for the LoRa board | One usually comes in the box. Never transmit without an antenna attached (see Stage 5). |
| ☐ | USB micro-B **data** cable | Some cheap cables are power-only, and the Pico won't show up on those |
| ☐ | 2× 20-pin male headers | Only if your Pico W has no pins |

**When you need each part**

| Before stage | You need | Order it |
| --- | --- | --- |
| 1–4 | Just the Pico W, a USB cable and a PC | Already have them |
| **5** | **1× Waveshare Pico-LoRa-SX1262** (868M/915M) + its antenna | **Now.** Stages 1–4 take an evening, so order before you start. |
| **8** | **Heltec WiFi LoRa 32 V3 (915 MHz)** handheld + LiPo + case, and a **2nd Waveshare Pico-LoRa-SX1262** + Pico H for the gate node | **Now, in the same order.** Stage 8 is the first time two radios talk. The handheld can stand in for the gate until the gate is built. |
| 11 | Gate sensors: QMC5883L magnetometer (the PIR, reed switch, button and jumpers come from the Kepler kit) | Before you finish Stage 8 |
| 12 | 2× USB power banks (you may already have them), a pole or tape for the gate antenna | Before the site visit |
| 13 | IP65 box, cable glands, desiccant, u.FL-to-SMA pigtail, 915 MHz outdoor antenna, lightning arrestor + ground wire, hub power (C9) | Once the range test passes, since its result may change the antenna choice |

The gate's buck converter and post are on the gate build, not this guide. See [shopping-list.md](shopping-list.md) for links and prices.

**Tools**

- A Windows PC (you have one with WSL)
- A soldering iron and solder, only if you need to add headers
- A multimeter (useful, not required until Stage 9)

**Software (free)**

- **Thonny**, a beginner-friendly Python editor that talks to the Pico: https://thonny.org. Install the Windows version. It includes its own Python.
- The **ntfy** app on your phone (iOS or Android)

> **Why Thonny and not WSL?** WSL can't see USB devices without extra setup (`usbipd-win`). Thonny runs on Windows and sees the Pico immediately. You can still edit the files in VS Code, since Thonny opens them straight from WSL at `\\wsl$\Ubuntu\home\markfyoung\farm-mesh`.

---

## Stage 1 – Headers (skip if your Pico W already has pins)

1. Push the two headers into a breadboard, long legs down, spaced so the Pico sits on top of them.
2. Lay the Pico W on top, with the pins through its edge holes.
3. Solder one corner pin on each side, check that the Pico sits flat, then solder the rest. Each joint should be a small shiny cone, not a ball.
4. Check that no solder bridges join neighboring pins.

**Learn:** the LoRa board connects to the Pico through these 40 pins. A bad joint on a pin like GP10 (the SPI clock) gives errors like "radio not responding" that look like software bugs.

✅ **Check:** the Pico sits square on the breadboard and every joint is shiny.

---

## Stage 2 – Put MicroPython on the Pico W

MicroPython is a small Python that runs directly on the chip. You install it once.

> **Already used this Pico before?** Check what's on it. In the Thonny Shell, run `import os; os.uname()`. If the version is older than about a year, or the machine line doesn't say **Pico W**, reflash with the steps below. The LoRa driver needs a recent MicroPython. Reflashing replaces the firmware, but files you saved on the Pico usually survive. Copy anything you care about off it first anyway.

1. Download the latest **Pico W** firmware (`.uf2` file) from https://micropython.org/download/RPI_PICO_W/. The plain-Pico build is different and has no WiFi.
2. **Hold down the white BOOTSEL button** on the Pico W, plug the USB cable into the PC, then let go.
3. A USB drive named **RPI-RP2** appears in File Explorer.
4. Drag the `.uf2` file onto it. The drive disappears by itself. That means the flash worked.
5. Open Thonny, then go to **Tools → Options → Interpreter**. Choose **MicroPython (Raspberry Pi Pico)** and set the port to "Try to detect automatically". Click OK.
6. The Shell pane at the bottom shows something like `MicroPython v1.2x on ...; Raspberry Pi Pico W with RP2040` and a `>>>` prompt.

**Learn:** that `>>>` is the **REPL** (Read-Eval-Print Loop). You are typing Python that runs *on the Pico*, not on your PC.

✅ **Check:** type these into the Shell one line at a time:

```python
from machine import Pin
led = Pin("LED", Pin.OUT)
led.on()
led.off()
```

The small green LED next to the USB port turns on, then off. You are now controlling hardware.

---

## Stage 3 – Connect the Pico W to your WiFi

Do this before adding the LoRa board, so there's only one new thing at a time.

1. In the Thonny Shell:

```python
import network, time
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect("YOUR-WIFI-NAME", "YOUR-WIFI-PASSWORD")
for i in range(20):
    if wlan.isconnected(): break
    time.sleep(0.5)
print(wlan.isconnected(), wlan.ifconfig())
print("signal", wlan.status("rssi"), "dBm")
```

2. You should see `True ('192.168.x.x', ...)` and a signal number.

**Learn:**
- The Pico W only does **2.4 GHz** WiFi. If your router has separate 2.4 and 5 GHz network names, use the 2.4 GHz one.
- `rssi` is signal strength in dBm. It's always negative, and closer to 0 is stronger. On the bench, expect −40 to −60. At the top of the tower, −75 or better is comfortable.

✅ **Check:** `True` and an IP address. If it says `False`, check the name and password (they're case-sensitive) and the 2.4 GHz network.

---

## Stage 4 – Install the LoRa driver

The Pico is online now, so it can download the driver itself. In the Shell:

```python
import mip
mip.install("lora-sync")
mip.install("lora-sx126x")
```

Each line prints `Installing ...` then `Done`. The files land in `/lib` on the Pico.

✅ **Check:** `from lora import SX1262` returns with no error. If it says `ImportError`, also run `mip.install("lora")` and try again.

**Learn:** `mip` is MicroPython's package installer, a tiny `pip`. The driver comes from **micropython-lib**, the official library collection. It knows how to talk to the SX1262 chip over SPI.

---

## Stage 5 – Attach the LoRa board

1. **Unplug the USB cable.** Never add or remove boards while powered.
2. **Screw the antenna onto the LoRa board first.**
   > ⚠️ A radio that transmits with no antenna attached reflects its power back into the chip and can destroy it. Make this a habit: antenna on before power on, every time.
3. Line up the LoRa board with the Pico W. The board has a USB outline printed on it. Match it to the Pico's USB end, so all 40 pins line up. Press it down evenly.

**Learn – how the two boards talk (SPI):** the Pico and the SX1262 chip use **SPI**, a 4-wire bus:

| Pico pin | Signal | Job |
| --- | --- | --- |
| GP10 | SCK | Clock: the Pico ticks it, one bit moves per tick |
| GP11 | MOSI | Pico → radio data ("Master Out, Slave In") |
| GP12 | MISO | Radio → Pico data |
| GP3 | CS | Chip select: pulled low means "I'm talking to you" |
| GP2 | BUSY | Radio says "wait, I'm still working" |
| GP20 | DIO1 | Radio taps the Pico on the shoulder: "packet arrived" or "send finished" |
| GP15 | RESET | Pico can reboot the radio |

These match the rp2 profile in `firmware/lib/board.py`.

✅ **Check:** plug the USB back in. Thonny reconnects and the `>>>` prompt returns.

---

## Stage 6 – Copy the project's shared files to the Pico

1. In Thonny, turn on **View → Files**. The top pane is your PC, the bottom pane is the Pico ("Raspberry Pi Pico").
2. In the top pane, browse to `\\wsl$\Ubuntu\home\markfyoung\farm-mesh\firmware\lib`.
3. Select `packet.py`, `radio.py` and `qmc5883l.py`, right-click, and choose **Upload to /**.

✅ **Check:** the bottom pane lists `lib/` (the driver from Stage 4), plus `packet.py`, `radio.py` and `qmc5883l.py`.

---

## Stage 7 – First contact with the radio

In the Shell:

```python
from radio import make_modem
m = make_modem()
print("radio ok")
```

- `radio ok` means the Pico and the SX1262 are talking over SPI, and the chip accepted the settings.
- An error that mentions a **timeout**, **BUSY** or **oscillator** means the chip's crystal (the TCXO) isn't starting. Open `radio.py` on the Pico (double-click it in the bottom pane), change `TCXO_MV = 1800` to `1700`, save, then press **Ctrl-D** in the Shell to restart and try again. If that fails, try `3300`, then `None`.
- An `ImportError` means the Stage 4 driver install didn't finish.

Now listen for 10 seconds:

```python
rx = m.recv(timeout_ms=10000)
print(rx)
```

It most likely prints `None`, which is normal: nothing is transmitting yet. You may catch a packet from someone else's 915 MHz device, which shows the receiver works.

**Learn – the radio settings** (`LORA_CFG` in `radio.py`):

| Setting | Value | What it means |
| --- | --- | --- |
| `freq_khz` | 915000 | 915 MHz, the US license-free band. Both ends must match. |
| `sf` | 7 | **Spreading factor**, 7–12. Higher reaches farther but each packet takes longer on air. SF7 is fastest, and 207 m doesn't need more. |
| `bw` | 125 | Bandwidth in kHz. Narrower is more sensitive but slower. 125 is the standard choice. |
| `coding_rate` | 5 | Error-correction overhead (4/5). Higher survives more interference. |
| `output_power` | 14 | Transmit power in dBm (about 25 mW). It goes up to 22 dBm (about 160 mW) if the link is weak. |

At these settings, our 8-byte packet is on air for about 40 ms.

✅ **Check:** `radio ok` printed.

---

## Stage 8 – Set up the handheld and talk to it (needs the Heltec V3)

The handheld (Heltec WiFi LoRa 32 V3) is the second radio. It uses a different chip (an ESP32-S3, not an RP2040), so its setup differs a little from the Pico's.

**8a – Get MicroPython onto the Heltec**

1. **Attach the antenna first** (the same rule as Stage 5). Leave the LiPo unplugged for now.
2. Plug the Heltec into the PC with a USB-C **data** cable. If Windows doesn't show a new COM port in Device Manager, install the **Silicon Labs CP210x** USB driver (the Heltec's USB chip) and replug.
3. In Thonny, go to **Tools → Options → Interpreter**. Choose **MicroPython (ESP32)** and pick the Heltec's COM port.
4. Click **Install or update MicroPython (esptool)** in the same dialog. Choose family **ESP32-S3**, variant **Espressif • ESP32-S3** (the generic build), then click Install. If it can't connect, hold **PRG**, tap **RST**, release PRG, and try again. That puts the chip in download mode.
5. Close the dialog. The Shell shows `MicroPython ... ESP32S3` and `>>>`.

**8b – Driver, files, screen**

1. Connect it to WiFi with the Stage 3 snippet. The ESP32 has WiFi too.
2. Install the drivers, including the screen driver:
   ```python
   import mip
   mip.install("lora-sync")
   mip.install("lora-sx126x")
   mip.install("ssd1306")
   ```
3. Upload `firmware/lib/*.py` to `/`, as in Stage 6. That includes `board.py`, which detects that it's on a Heltec and uses the Heltec's pins automatically.

**Learn:** the Heltec has the same SX1262 radio chip as the Waveshare board, just wired to different pins. `lib/board.py` holds one pin map per board, so all the other code is identical on both.

**8c – Ping/pong between the hub and the handheld**

1. Open `firmware/tools/radio_test.py` in Thonny.
2. **Hub (Pico W):** set `ROLE = "pong"` on line 13. Save it to the Pico as `radio_test.py`, then click **Run** (F5).
3. **Handheld:** in Thonny, pick the Heltec's port (bottom-right corner of the window), leave `ROLE = "ping"`, and run it. With one PC, run the hub from a USB charger instead: save `radio_test.py` to the Pico W as `main.py` so it starts by itself.
4. The handheld prints a line every 2 seconds, and its screen shows a short version (`12/12 -38 10` means replies/sent, RSSI, SNR):

```
#12  them->us rssi -38 snr 9.5 | us->them rssi -40 snr 9.8 | 12/12 ok
```

5. Plug in the LiPo and unplug USB. The handheld keeps running from the battery, so you can walk around with it.

> If you saved `radio_test.py` as `main.py` on the Pico W, delete it from the Pico before Stage 10. Stage 10 uploads the hub's own `main.py`.

**Learn – reading the numbers:**

| RSSI (dBm) | SNR (dB) | Meaning |
| --- | --- | --- |
| −30 to −90 | above +5 | Excellent. Typical on the bench (very loud). |
| −90 to −110 | 0 to +5 | Good. What you hope for at the gate. |
| −110 to −120 | −5 to 0 | Marginal. Expect some lost packets. |
| below −120 | below −7 | At the edge. SF7 stops decoding around −7.5 dB SNR. |

**SNR** (signal-to-noise ratio) matters more than RSSI. LoRa's trick is that it can decode signals *below* the noise floor, which is why SNR can be negative and still work.

✅ **Check:** 10/10 replies on the bench. Leave the ping board running and walk it around the house or yard to get a feel for range.

---

## Stage 9 – Set up phone alerts (ntfy)

1. Pick a **long, unguessable topic name**, for example `farm-gate-` plus random letters: `farm-gate-q7m2x9vk`. Anyone who knows the name can read the alerts. That's ntfy's only security on the free server.
2. On your phone, open the ntfy app, tap **+**, and subscribe to that topic on `ntfy.sh`.
3. Test from WSL:

```bash
curl -d "Hello from the farm" ntfy.sh/farm-gate-q7m2x9vk
```

Your phone buzzes within a second or two.

4. Now test from the Pico (WiFi must be connected, as in Stage 3):

```python
import requests
r = requests.post("https://ntfy.sh/farm-gate-q7m2x9vk", data="Hello from the Pico", headers={"Title": "Test"})
print(r.status_code); r.close()
```

`200` and a phone buzz mean the full alert path works.

**Learn:** the Pico makes a plain HTTPS POST, the same thing a browser does when you submit a form. ntfy's server forwards it to every phone subscribed to that topic.

✅ **Check:** both buzzes arrived.

---

## Stage 10 – Install the hub program

1. In WSL, create your secrets file from the template:

```bash
cd ~/farm-mesh
cp firmware/secrets_example.py firmware/secrets.py
code firmware/secrets.py
```

Fill in `WIFI_SSID`, `WIFI_PASSWORD` and `NTFY_TOPIC`. This file is git-ignored, so it never reaches GitHub.

2. **For bench work, turn off the watchdog:** in `firmware/hub/config.py`, set `WATCHDOG_MS = None`. Turn it back on (`8000`) before the hub goes on the tower.

> **Learn – the watchdog:** a watchdog is a hardware timer that reboots the Pico if the program stops "feeding" it, for example if it freezes. That's great on a tower you can't reach, and annoying on the bench: once it's running, it can't be stopped, so pressing Stop in Thonny just gets you rebooted 8 seconds later. The hub has an escape hatch. The LED lights for the first 3 seconds after power-up, and holding **BOOTSEL** during that time skips startup and leaves you at the REPL. Don't hold BOOTSEL while *plugging in*, because that enters firmware-flash mode instead (Stage 2).

3. Upload to the Pico root (`/`) with Thonny's Files pane:
   - `firmware/secrets.py`
   - `firmware/hub/config.py`
   - `firmware/hub/main.py`

**Learn:** a file named `main.py` runs automatically every time the Pico powers up. That's how the hub starts by itself on the tower with no computer attached.

4. Press **Ctrl-D** in the Shell (soft reboot). You should see:

```
wifi 192.168.x.x
```

Your phone gets **"Hub online – Tower hub started."**

✅ **Check:** the "Hub online" alert arrived.

---

## Stage 10½ – Fake a sensor hit with the handheld

You don't need the gate node yet. The handheld can pretend to be one.

1. Upload `firmware/tester/main.py` to the Heltec as `main.py`, then press **RST** on the Heltec. The screen shows `TEST-01 ready`.
2. **Short press PRG.** The screen shows:
   ```
   SEND moti 43
   H>T ack -41 OK
   ```
   That's your fake motion event, then the hub's ACK. Your phone gets **"TEST-01: motion"**.
3. **Hold PRG for 1 s or more** to send a fake vehicle event. You'll get a "TEST-01: vehicle" alert.
4. Press again within 60 s. You still get the ACK, but no phone alert, because the hub's cooldown is working.
5. Turn the hub off and press PRG. You see `retry` three times, then `NO ACK!`. That's what a lost link looks like.

✅ **Check:** an ACK on the screen and an alert on the phone for each press.

---

## Stage 11 – End-to-end bench test with the gate node

Leave the handheld running. It listens between presses, so it shows the gate's packets (`G1> moti`) and the hub's replies (`H>G1 ack`) as they happen.

1. Set up the gate Pico as in `firmware/README.md` (Flash, step 4): `lib/*.py`, `gate/config.py` and `gate/main.py`.
2. Power both boards on the bench.
3. The hub prints `GATE-01 boot rssi -40 snr 9.5`, which means the gate's startup packet arrived and was ACKed.
4. Wave your hand in front of the gate's PIR, twice within 4 seconds. Wait about 3 seconds (the gate is checking whether the magnetometer calls it a vehicle). Your phone gets **"GATE-01: motion – Person or animal at the gate"**.
5. Move a magnet or steel wrench quickly past the magnetometer. Your phone gets **"GATE-01: vehicle"**.
6. Wave again right away. There's no new alert, because the 60-second cooldown is doing its job.
7. Read the log on the hub. In Thonny, double-click `events.log` in the Pico pane:

```
2026-10-25T18:02:11Z,GATE-01,boot,57,,-41,9.5
2026-10-25T18:03:40Z,GATE-01,motion,58,,-40,9.8
```

The columns are time (UTC), node, event, sequence number, battery, RSSI and SNR.

**Learn – what happened for each packet:**
1. The gate sent 8 bytes: node 1, sequence 58, event "motion".
2. The hub decoded it and immediately sent an ACK back (also 8 bytes).
3. The gate heard the ACK and stopped retrying. Without an ACK, it would retry up to 3 times after random delays, so two retries don't collide again.
4. The hub checked whether it had already seen sequence 58 from node 1. If the ACK got lost, the retry carries the same number and gets dropped, so you don't get double alerts.
5. It stamped the time, wrote the log line and sent the push.

✅ **Check:** motion and vehicle alerts arrived, and the log has matching lines.

Update `components.md`: C1, C2a and C13 → `bench tested`.

---

## Stage 12 – Range test at the real site

Do this before drilling any holes.

1. Load `radio_test.py` back onto both boards: `pong` on the hub, `ping` on the gate board.
2. Get the hub as high as you can safely: on the tower, or at least on a ladder near its base. Power it from a USB power bank.
3. Take the ping board and a power bank to the gate. Hold the antenna 6–8 ft up (tape it to a pole) and watch Thonny on a laptop.
4. Write down the RSSI and SNR, and how many replies out of 20 came back. Try a few spots around the gate, and remember the post must be 3 ft or more from the metal gate.

| Result | Action |
| --- | --- |
| 19–20/20, SNR above 0 | You're done. Pick the spot with the best SNR. |
| 15–18/20 or SNR −5 to 0 | Raise `output_power` to 20 in `radio.py` on both boards, and get the gate antenna higher. |
| Worse | Try `sf` 9 (both ends), and check the hub's antenna is clear of tower steel. |

5. While you're up the tower, check WiFi at the hub's final spot (Stage 3 snippet). −75 dBm or better is fine.

✅ **Check:** 19/20 or better at the chosen gate spot.

---

## Stage 13 – Weatherproof box and tower install

**Box**

1. Use a **light-colored** IP65 box, since dark boxes cook in Texas sun.
2. Drill a hole in the top for the antenna's **SMA bulkhead**. Connect the u.FL pigtail on the inside to the LoRa board, so the antenna screws on outside. Drill one hole in the bottom for a **cable gland** for the USB power cable.
3. Mount the Pico and LoRa board on standoffs or double-sided foam tape. Add a desiccant pack.
4. Loop the power cable down below the gland before it goes up into the box (a **drip loop**), so rain drips off the low point and doesn't follow the cable in.

**Tower**

1. **Safety first:** use a harness and a second person on the ground. Don't climb in wind or storms.
2. Mount the box at the top, with the antenna **vertical**, **3 ft or more from the existing WiFi radio** and clear of the tower's steel legs.
3. Put the **lightning arrestor** inline between the antenna and the box, and run its ground wire to the tower ground.
4. Run power: a USB supply, a PoE splitter or solar (C9, still an open decision).
5. Before closing the box: set `WATCHDOG_MS = 8000` in `config.py` on the Pico, then power-cycle it and check for the "Hub online" alert.

✅ **Check:** "Hub online" arrives after you close the box, and a test wave at the gate alerts your phone.

Update `components.md`: C1, C2a, C10, C11, C12 → `installed`.

---

## Stage 14 – Watch it for a week

- **Every 3 hours** the gate sends a heartbeat. You won't see alerts for heartbeats, but they're logged.
- **If the gate goes silent for 6 hours**, you get **"GATE-01 silent"**. Check the gate's power and antenna.
- **False alarms** (wind, sun on leaves): see "False trigger control" in `design.md`. Aim the PIR lower, or raise `PIR_CONFIRM_HITS`.
- **No vehicle alerts for real vehicles:** lower `MAG_THRESHOLD` (use `sensor_test.py` at the gate to pick the value).

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| No RPI-RP2 drive | Power-only USB cable, or BOOTSEL released too early | Try another cable. Hold BOOTSEL *while* plugging in. |
| Thonny "Couldn't find the device" | Board busy, or wrong port | Unplug and replug, then pick the port bottom-right in Thonny |
| Stop in Thonny doesn't stop the hub | Watchdog is running | Set `WATCHDOG_MS = None`, or hold BOOTSEL while the LED is lit at power-up |
| `ImportError: no module named 'lora'` | Driver not installed | Stage 4 again, including `mip.install("lora")` |
| Radio init timeout or BUSY error | TCXO voltage, or board not seated | Re-seat the board, then try `TCXO_MV` 1700 → 3300 → None |
| `radio ok` but no packets between boards | Settings differ, or wrong band variant | Same `radio.py` on both boards. Check that both boards are the 868M/915M version. |
| WiFi `False` | 5 GHz network, or typo | Use the 2.4 GHz network name. The password is case-sensitive. |
| Push fails (`push failed: ...`) | WiFi dropped, or wrong topic | Hub reconnects on its own. Check `NTFY_TOPIC` in `secrets.py`. |
| Log times are 2000-01-01 | NTP failed at boot | Check internet access. The hub re-syncs every 6 hours. |

---

## Where to go next (more to learn)

- **A status web page on the hub:** the Pico W can serve a small web page (look at the `microdot` library) showing the last 20 events and the gate's last-heard time. That's a first step toward subgoal 5, the online monitor.
- **An OLED screen** on the hub box for local status, using I2C on two spare GPIO pins.
- **Read the driver:** `lib/lora/sx126x.py` on the Pico shows exactly which SPI commands set the frequency and power. It's a good way to learn how radios are configured.
