# Wiring overview

Three separate links, kept intentionally independent so a failure in one
(e.g. the companion computer crashing) doesn't take down the others.

## 1. FlySky receiver -> Pixhawk (primary manual control)

This link bypasses the Raspberry Pi entirely - the pilot always has direct
control of the aircraft even if the companion computer is off or frozen.

- Use a FlySky receiver with an SBUS output (e.g. FS-iA6B, FS-iA10B). SBUS is
  a single inverted-serial wire carrying all channels, which matches the
  Pixhawk's dedicated `RC IN` (SBUS) port and needs no PPM encoder.
- Wire: receiver `SBUS/iBUS` out -> Pixhawk `RC IN`, plus shared ground.
  Pixhawk supplies power to the receiver from that port; don't also power
  the receiver from the RPi.
- PX4 side: no special param needed for standard SBUS - `RC_INPUT_PROTO`
  auto-detects it. Bind the receiver to the transmitter per FlySky's manual,
  then verify all channels move correctly in QGroundControl's Radio Setup
  page before anything else.
- Reserve one spare 2-position (or 3-position) switch on the FS-i6/FS-i6X
  transmitter for the payload release channel. Note which AUX channel number
  QGroundControl shows it on - you'll need that index (0-based) for
  `rc_channel_index` in `payload_release.launch.py`.

## 2. Pixhawk <-> Raspberry Pi (MAVLink telemetry)

Two options, pick one:

**A. Direct UART (simplest, no extra hardware)**
- Pixhawk `TELEM2` -> RPi GPIO UART (pins 8/TXD and 10/RXD on the 40-pin
  header), cross-connected: Pixhawk TX -> RPi RXD, Pixhawk RX -> RPi TXD,
  plus a shared ground. Both sides are already 3.3V logic - no level shifter
  needed.
- `scripts/rpi_setup.sh` enables the UART and frees it from the Linux serial
  console.
- PX4 params: `MAV_1_CONFIG = TELEM2`, `MAV_1_MODE = Onboard`,
  `SER_TEL2_BAUD = 921600`. Match `921600` in `mavros_pixhawk.launch.py`'s
  `fcu_url` (`/dev/ttyAMA0:921600`).

**B. USB telemetry radio or USB-serial adapter**
- Plug into any RPi USB port, appears as `/dev/ttyUSB0`. Use this if you'd
  rather keep the option of an off-board telemetry radio for a ground
  station later.
- Set `fcu_url` to `/dev/ttyUSB0:<baud>` matching the adapter/radio's baud
  rate (57600 is the common default for 3DR-style radios).

Either way this is a MAVLink link carrying vehicle state (GPS, battery,
mode, RC channels) to the Pi and accepting commands back - it is not a
flight-critical link. If it drops, the aircraft keeps flying under
FlySky/Pixhawk control; only companion-computer features (payload release
via RC passthrough monitoring, telemetry logging, etc.) are affected. The
release node's watchdog (see `docs/safety_checklist.md`) forces the payload
latch closed if this link goes stale.

## 3. Raspberry Pi -> release servo

- Servo signal: RPi **GPIO18** (physical pin 12) - a hardware PWM-capable
  pin, which matters for a servo holding a latch under vibration.
- Servo power: run the servo off the aircraft's 5-6V BEC/power distribution
  board, **not** the RPi's 5V pin. A loaded servo can pull several amps
  momentarily, which will brown out the Pi.
- Common ground: RPi GND, servo GND, and BEC GND must all tie together, even
  though the servo isn't powered by the Pi.
- Run `pigpiod` (installed and enabled by `scripts/rpi_setup.sh`) so
  `payload_release`'s `use_pigpio:=true` gets jitter-free timing instead of
  gpiozero's default software PWM.

## Power distribution notes for a heavy-lift build

- Motors/ESCs draw from the main flight battery through a power distribution
  board sized for your total current, not through the Pixhawk.
- Pixhawk, RPi, and the release servo should run off a dedicated 5V BEC
  rated with headroom above your peak servo + Pi draw - don't share the
  ESCs' BEC (if any) for this, ESC BECs are typically undersized for a Pi
  plus companion peripherals.
- Add a large-enough capacitor or filtered BEC if you see brownout resets
  on the Pi when the servo actuates; this is common on noisy power rails.
