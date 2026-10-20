# Building the tower gateway – step by step

This guide builds the DIY gateway (assembly type 1 in [components.md](components.md)) from a bare Pico W to a working box on the tower. Along the way it sets up the handheld and the gate node, because a gateway with nothing to hear can't be tested. Each stage ends with a check, so you know it works before you move on. The **Learn** notes explain what is going on underneath. Skip them if you only want it working.

What you will have at the end: two boards in one box at the top of the tower.

- **The tower radio** (Pico H + Waveshare LoRa board) runs **Meshtastic**. It's part of the mesh: it hears every node, relays for them and decrypts the private channel.
- **The gateway brain** (your Pico W) runs **your MicroPython code**. It reads what the radio hears over three wires, logs it, and pushes alerts to your phone over the house WiFi.

```
 GATE-01 ─┐                       ┌──────────── tower box ────────────┐
 handheld ─┼── LoRa mesh 915 MHz ─▶ │ Pico H + Waveshare  (Meshtastic)  │
 (later:   │                      │        │ UART, 3 wires             │
 woods)  ──┘                      │ Pico W  (MicroPython brain)       │
                                  └────────┬──────────────────────────┘
                                           │ WiFi, 11 m
                                     house router ──▶ ntfy ──▶ your phone
```

**Learn – why two boards?** Meshtastic handles the mesh: relaying, encryption, ACKs, retries and duplicate removal. It's mature C++ firmware, and you don't want to rewrite it. Your Pico W handles what's specific to this farm: what counts as an alert, cooldowns, logging and pushing to your phone. Your code stays small and in Python. You never have to touch Meshtastic's code until the gate needs a custom sensor module.

---

## Stage 0 – Gather parts and tools

| ✓ | Part | Used for | Needed by stage |
| --- | --- | --- | --- |
| ☐ | Raspberry Pi Pico W (owned) | Gateway brain | 2 |
| ☐ | Pico H + Waveshare Pico-LoRa-SX1262 (868M/915M) + antenna | Tower radio | 6 |
| ☐ | Heltec V3 bundle, 915 MHz (board, battery, case, antenna) | Handheld | 8 |
| ☐ | 4 jumper wires, female-female (Kepler kit) | UART link + power between the two boards | 9 |
| ☐ | Second Pico H + Waveshare board + antenna | Gate node | 11 |
| ☐ | PIR module (Kepler kit) + 3 jumper wires | Gate node | 11 |
| ☐ | USB micro-B **data** cables (2), USB-C data cable (1) | Programming | 2, 6, 8 |
| ☐ | IP65 box, outdoor antenna + pigtail, lightning arrestor, power | Tower install | 13 |

**Order now:** both Pico H + Waveshare sets and the Heltec bundle. Stages 1–5 need only the Pico W, so they fill the wait. Order the tower-install parts after the range test (Stage 12), since its result may change the antenna choice.

**Software (free):**
- **Thonny** for the Pico W (you have it; update it from thonny.org if it's old)
- **Chrome or Edge**, for the Meshtastic web flasher and web client. They use Web Serial, which Firefox doesn't support.
- The **Meshtastic** app and the **ntfy** app on your phone

> **Why Thonny on Windows and not WSL?** WSL can't see USB devices without extra setup (`usbipd-win`). Thonny on Windows sees the Pico immediately and opens the project files straight from `\\wsl$\Ubuntu\home\markfyoung\farm-mesh`.

---

## Stage 1 – Headers

The **Pico H** comes with headers. Check your **Pico W**: if it has no pins underneath, solder on two 20-pin headers.

1. Push the headers into a breadboard, long legs down, and lay the Pico W on top.
2. Solder one corner pin on each side, check the board sits flat, then do the rest. Each joint should be a small shiny cone.
3. Check that no solder bridges join neighboring pins.

✅ **Check:** every joint is shiny and the board sits square.

---

## Stage 2 – MicroPython on the Pico W

> **Used this Pico before?** In the Thonny Shell, run `import os; os.uname()`. If the version is more than about a year old, or the machine line doesn't say **Pico W**, reflash. Copy off any old programs you want first.

1. Download the latest **Pico W** `.uf2` from https://micropython.org/download/RPI_PICO_W/.
2. **Hold BOOTSEL**, plug the Pico W into the PC, then release. A drive called **RPI-RP2** appears.
3. Drag the `.uf2` onto it. The drive disappears, which means the flash worked.
4. In Thonny: **Tools → Options → Interpreter → MicroPython (Raspberry Pi Pico)**, port set to auto-detect.

✅ **Check:** the Shell shows `>>>`. Type `from machine import Pin; Pin("LED", Pin.OUT).on()` and the green LED lights.

**Learn:** `>>>` is the REPL. What you type runs *on the Pico*, not on your PC.

---

## Stage 3 – WiFi from the Pico W

```python
import network, time
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect("YOUR-WIFI-NAME", "YOUR-WIFI-PASSWORD")
for i in range(20):
    if wlan.isconnected(): break
    time.sleep(0.5)
print(wlan.isconnected(), wlan.ifconfig(), "signal", wlan.status("rssi"))
```

✅ **Check:** `True`, an IP address, and a signal number.

**Learn:** the Pico W only does **2.4 GHz** WiFi. Signal is in dBm: closer to 0 is stronger. On the bench expect −40 to −60, and at the tower top −75 or better is fine.

---

## Stage 4 – Phone alerts (ntfy)

ntfy is a free push-notification service. Anything that can send a web request to `ntfy.sh/<topic>` makes every phone subscribed to that topic buzz.

1. Pick a **long, unguessable topic**, for example `farm-gate-q7m2x9vk`. Anyone who knows the name can read the alerts.
2. In the ntfy phone app, tap **+** and subscribe to it.
3. Test from WSL: `curl -d "Hello from the farm" ntfy.sh/farm-gate-q7m2x9vk`
4. Test from the Pico W (WiFi connected as in Stage 3):

```python
import requests
r = requests.post("https://ntfy.sh/farm-gate-q7m2x9vk", data="Hello from the Pico", headers={"Title": "Test"})
print(r.status_code); r.close()
```

✅ **Check:** both buzzes arrive, and the Pico prints `200`.

---

## Stage 5 – Install the gateway brain (no radio yet)

1. In WSL:
   ```bash
   cd ~/farm-mesh
   cp firmware/secrets_example.py firmware/secrets.py
   code firmware/secrets.py      # WiFi name, password, ntfy topic
   ```
2. **For bench work, turn off the watchdog:** in `firmware/gateway/config.py`, set `WATCHDOG_MS = None`.
3. In Thonny's **View → Files**, browse the top pane to `\\wsl$\Ubuntu\home\markfyoung\farm-mesh\firmware` and upload these to the Pico W's root (`/`):
   - `lib/meshproto.py`, `lib/packet.py`
   - `secrets.py`
   - `gateway/config.py`, `gateway/main.py`
4. Press **Ctrl-D** (soft reboot). You'll see `wifi 192.168.x.x`, and your phone gets **"Gateway online"**.

**Learn:**
- `main.py` runs automatically at every power-up. That's how the gateway starts on the tower with no PC attached.
- **The watchdog** reboots the Pico if the code freezes. That's good on a tower, annoying on the bench, because once running it can't be stopped. The escape hatch: the LED is lit for 3 s after power-up, and holding **BOOTSEL** during that time skips startup. Don't hold it *while plugging in*, because that enters flash mode (Stage 2).
- With no radio attached, the brain sends a **"Tower radio silent"** alert after about 30 minutes. That's the radio health check working. Ignore it for now.

✅ **Check:** "Gateway online" arrived.

---

## Stage 6 – Build and flash the tower radio

1. **Screw the antenna onto the Waveshare board first.**
   > ⚠️ A LoRa radio that transmits with no antenna can destroy itself. Antenna on before power on, every time.
2. Press the Waveshare board onto the **Pico H**, matching the USB outline printed on it to the Pico's USB end.
3. Open https://flasher.meshtastic.org in Chrome or Edge. Choose the **Raspberry Pi Pico** target (the build for the Pico + Waveshare SX1262), pick the latest **stable** firmware, and download the `.uf2`.
4. Hold **BOOTSEL** on the Pico H, plug it in, release, and drag the `.uf2` onto **RPI-RP2**.

**Learn – SPI:** Meshtastic talks to the SX1262 chip over SPI, a 4-wire bus: clock GP10, data out GP11, data in GP12, chip select GP3, plus BUSY GP2, DIO1 GP20 (the "packet arrived" signal) and RESET GP15. The Pico build of Meshtastic already knows the Waveshare pinout, which is why there's nothing to configure here.

✅ **Check:** the drive disappears and the Pico H's LED starts blinking.

---

## Stage 7 – Configure the tower radio (and create your private channel)

The Pico has no Bluetooth, so configure it over USB with the **web client**.

1. Open https://client.meshtastic.org in Chrome or Edge. Click **New connection → Serial**, and pick the Pico H's port.
2. Set these (menu names may differ slightly between versions), and **save** after each page:

| Where | Setting | Value | Why |
| --- | --- | --- | --- |
| Config → LoRa | Region | **US** | Legal 915 MHz band. Nothing transmits until this is set. |
| Config → LoRa | Modem preset | **Medium Fast** | Plenty for 450 m of woods, with short airtime. **Every node must match.** |
| Config → Device | Role | **Router** | Always listening and relaying, which is right for a high, powered site |
| Config → User | Long / short name | **TOWER / TWR** | How it appears on the mesh |
| Channels → Primary | Name | **farm** | Your private channel |
| Channels → Primary | Key (PSK) | **Generate** a new random key, 256-bit | Encrypts everything on the mesh |

3. On the Channels page, find the **QR code / share URL**. You'll use it to put the handheld and the gate on the same channel.

**Learn – channels and keys:** every packet is encrypted with the channel key. Nodes with a different key hear only noise, which is why replacing the default public key matters: with the default, anyone's Meshtastic device could read your alerts or fake one. The **modem preset** bundles the radio settings (spreading factor, bandwidth, coding rate). Faster presets mean shorter packets but less range.

✅ **Check:** after a reboot, the web client shows TOWER, region US, Medium Fast, and channel "farm".

---

## Stage 8 – Set up the handheld (Heltec V3)

1. **Antenna on.** Plug in the battery (the bundle's battery matches the socket).
2. Connect it by USB-C. Open https://flasher.meshtastic.org, choose **Heltec V3**, pick the same stable version, and click **Flash**. If Windows shows no COM port, install the **Silicon Labs CP210x** driver.
3. On your phone, open the **Meshtastic** app and pair with the Heltec over Bluetooth. The PIN shows on the Heltec's screen.
4. In the app, set: Region **US**, preset **Medium Fast**, role **Client**, names **TEST-01 / TST1**.
5. Join the channel: in the app, scan the QR code from Stage 7 (Channels → **Add / scan QR**). Choose **replace** so "farm" becomes the primary channel.
6. Send a message on the "farm" channel: `hello tower`.

✅ **Check:** the message appears in the web client connected to TOWER, and TOWER appears in the app's node list with an SNR value.

**Learn – reading signal numbers:**

| RSSI (dBm) | SNR (dB) | Meaning |
| --- | --- | --- |
| −30 to −90 | above +5 | Excellent (bench) |
| −90 to −110 | 0 to +5 | Good. What you want at the gate. |
| −110 to −120 | −5 to 0 | Marginal |
| below −120 | below −7 | At the edge |

SNR matters more than RSSI. LoRa can decode signals *below* the noise floor, which is why a negative SNR can still work.

---

## Stage 9 – Wire the brain to the tower radio

1. **Unplug both boards.**
2. Connect four jumper wires:

| Tower radio (Pico H) | Wire to | Gateway brain (Pico W) | What it carries |
| --- | --- | --- | --- |
| GP4, physical pin 6 (UART1 TX) | → | GP1, pin 2 (UART0 RX) | Radio → brain data |
| GP5, physical pin 7 (UART1 RX) | ← | GP0, pin 1 (UART0 TX) | Brain → radio data |
| GND, pin 3 | — | GND, pin 3 | Common ground (required) |
| VBUS, pin 40 | → | VSYS, pin 39 | Powers the Pico W from the radio's USB supply |

   **Reaching the pins under the Waveshare board:** the Waveshare board carries all 40 Pico pins through, in the same positions. Clip the jumpers onto its header pins if they're exposed. Otherwise, solder short wires to the Pico H's pads before you stack the boards. Check against the pin labels, not by counting by eye.

   **TX always goes to RX.** Each side's "transmit" must land on the other side's "receive". With two TX pins connected, nothing gets through.

3. Plug the **Pico H** into USB. Both boards power up from it. Connect the web client to TOWER again (Serial). Under **Module Config → Serial**, set:

| Setting | Value |
| --- | --- |
| Enabled | on |
| Mode | **PROTO** |
| RX pin | **5** |
| TX pin | **4** |
| Baud | **115200** |
| Echo | off |

   Save. The radio reboots.

4. Plug the Pico W into the PC as well (it's safe with both powered: the Pico W has a diode between USB and VSYS). In Thonny, press **Ctrl-D**.

✅ **Check:** the Thonny Shell prints `radio session up, 2 nodes known` (TOWER and TEST-01).

**Learn – what PROTO mode does:** it makes the radio's spare UART speak the same protocol the phone app uses over Bluetooth. The brain opens a session by sending `want_config`. The radio answers with its settings and node list (that's where the names come from), then forwards every packet it hears. Each message is a small frame: `0x94 0xC3`, a 2-byte length, then a **protobuf** (a compact binary format). `firmware/lib/meshproto.py` decodes just the fields we need.

---

## Stage 10 – End-to-end test with the handheld

1. In the Meshtastic app, send `test 1` on the "farm" channel.
2. Your phone gets an ntfy alert: **"TEST-01: text – test 1"**.
3. In Thonny, double-click `events.log` on the Pico W:
   ```
   2026-10-25T18:02:11Z,GATEWAY,boot,,,,
   2026-10-25T18:03:40Z,TEST-01,text,-41,9.8,0,test 1
   ```
   The columns are time (UTC), node, event, RSSI, SNR, hops and detail.
4. Send `test 2` within 60 s. It's logged, but there's no second alert, because the cooldown is working.

**Learn – the full path of one message:** phone app → Bluetooth → Heltec → encrypted LoRa packet → TOWER decrypts → UART frame → Pico W decodes → logs → HTTPS to ntfy → your phone. Each hop is one of the stages you just built.

✅ **Check:** the alert arrived, and the log line shows RSSI and SNR.

Update [components.md](components.md): the gateway and handheld parts → `bench tested`.

---

## Stage 11 – Gate node on the bench

1. Antenna on, Waveshare onto the second Pico H, then flash Meshtastic (as in Stage 6).
2. Configure it with the web client (Stage 7 settings), except: role **Client**, names **GATE-01 / GT01**, and join the "farm" channel with the same key. Enter the key from Stage 7, or import the share URL.
3. Wire the Kepler kit PIR: **VCC → VBUS (pin 40)**, **OUT → GP16 (pin 21)**, **GND → pin 38**. On the PIR, turn the delay knob all the way down and set the jumper to **L**.
4. Under **Module Config → Detection Sensor**, set:

| Setting | Value |
| --- | --- |
| Enabled | on |
| Name | **Motion** (the brain maps "Motion detected" to a motion alert; see `DETECTION_NAMES` in `config.py`) |
| Monitor pin | **16** |
| Trigger | **Logic high** (PIR output goes high on motion) |
| Use pull-up | off |
| Minimum broadcast seconds | **60** (cooldown at the source, which saves airtime) |
| State broadcast seconds | 0 |

5. Save, then wave at the PIR.

✅ **Check:** your phone gets **"GATE-01: motion – Person or animal at the gate"**, and the handheld's app shows the "Motion detected" message.

**Learn:** the Detection Sensor module watches one GPIO pin and sends a text message when it changes. It's the simplest way to put a sensor on the mesh without writing code. Vehicle detection (the magnetometer) and the gate-open switch need more than one pin and some logic, so they'll come with a custom C++ module later, using our 8-byte packet on Meshtastic's `PRIVATE_APP` port. The brain already understands those packets.

---

## Stage 12 – Range test at the site

1. Power TOWER as high as you can safely: on the tower, or at least on a ladder near it. A USB power bank is fine.
2. Walk to the gate with the handheld. Hold it 6–8 ft up, near where the gate post will go (3 ft or more from the metal gate).
3. In the app, open TOWER in the node list and run **Traceroute**. It reports the SNR for each hop. Also send a few messages and watch for the delivery checkmark.

| Result | Action |
| --- | --- |
| Traceroute works, SNR above 0 | Done. Pick the spot with the best SNR. |
| Some messages fail, SNR −5 to 0 | Raise the gate antenna. Try **Medium Slow** or **Long Fast** on *every* node. |
| Nothing gets through | Check that the tower antenna is vertical and clear of steel. Then consider a relay node. Meshtastic handles relaying with no code. |

4. While you're up there, check the Pico W's WiFi signal at the tower top (Stage 3 snippet). −75 dBm or better is fine.

✅ **Check:** reliable messages from the gate spot.

---

## Stage 13 – Box and tower install

**Box**
1. A light-colored IP65 box, since dark boxes cook in Texas sun. Mount both boards on standoffs or foam tape, wired as in Stage 9, and add a desiccant pack.
2. Fit the antenna on top through an **SMA bulkhead**, with the u.FL pigtail inside to the Waveshare board. Run power in through a **cable gland** on the bottom, with a **drip loop** in the cable below the box.
3. Power goes into the **Pico H's** micro-USB. The Pico W gets power through the VBUS→VSYS wire.

**Tower**
1. **Safety first:** use a harness and a second person on the ground. No climbing in wind or storms.
2. Antenna vertical at the top, **3 ft or more from the existing WiFi radio**, and clear of the tower legs.
3. Put the **lightning arrestor** inline, with its ground wire to the tower ground.
4. Before you close the box: set `WATCHDOG_MS = 8000` in `config.py` on the Pico W, power-cycle, and wait for "Gateway online".

✅ **Check:** "Gateway online" arrives after the box is closed, and a wave at the gate PIR alerts your phone.

---

## Stage 14 – Watch it for a week

- **Meshtastic nodes report telemetry every 30 minutes** by default, so the brain always knows who is alive. If GATE-01 is silent for 2 hours, you get **"GATE-01 silent"**.
- If the UART link or the tower radio dies, you get **"Tower radio silent"**.
- **False alarms:** aim the PIR lower and away from sunlit leaves, or raise the minimum broadcast seconds.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| No RPI-RP2 drive | Power-only USB cable, or BOOTSEL released too early | Another cable. Hold BOOTSEL *while* plugging in. |
| Web client can't connect | Firefox, or Thonny holding the port | Use Chrome or Edge. Close Thonny's connection to that board. |
| Handheld and TOWER don't see each other | Region not set, presets differ, or keys differ | Region US, the same preset and the same "farm" key on both |
| Brain never prints `radio session up` | TX/RX not crossed, no common GND, Serial module off, or wrong pins or baud | Recheck the Stage 9 table: GP4→GP1, GP5←GP0, GND, PROTO, 115200 |
| Brain sees packets but names show as `!a1b2c3d4` | The radio hasn't heard that node's name yet | Wait a few minutes. Nodes broadcast their names periodically. |
| Stop in Thonny doesn't stop the brain | Watchdog running | Set `WATCHDOG_MS = None`, or hold BOOTSEL while the LED is lit at power-up |
| No motion alert, but the app shows "Motion detected" | Sensor name doesn't match | The Detection Sensor name must start with a key in `DETECTION_NAMES` ("Motion") |
| Log times are 2000-01-01 | NTP failed at boot | Check internet access. It re-syncs every 6 hours. |

---

## Where to go next

- **The custom gate module (C++):** magnetometer vehicle detection plus the gate-open switch, sending our 8-byte packet on `PRIVATE_APP`. The logic is already written in Python in `firmware/legacy/gate/main.py`, ready to port.
- **A status web page on the Pico W** (the `microdot` library): recent events and each node's last-heard time. It's a first step toward the online monitor.
- **Battery and signal per node:** decode `TELEMETRY_APP` packets in `meshproto.py`, a good protobuf exercise.
