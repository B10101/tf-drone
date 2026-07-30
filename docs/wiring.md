# Wiring overview

Three separate links, kept intentionally independent so a failure in one
(e.g. the companion computer crashing) doesn't take down the others.

## 1. FlySky receiver -> Pixhawk (primary manual control)

This link bypasses the Raspberry Pi entirely - the pilot always has direct
control of the aircraft even if the companion computer is off or frozen.

**Your receiver is an iA10B (or similar 8-10ch FlySky receiver), which is
iBUS-only - it does not have an SBUS output** (that's the iA6B, a different
model). This matters because the Pixhawk's dedicated `RC IN` port was
designed for SBUS, and PX4's iBUS support is less universally documented
than its SBUS support. Don't assume it "just works" - verify it, since this
is your primary flight control link.

- Wire: receiver `iBUS` out -> Pixhawk `RC IN`, plus shared ground. Pixhawk
  supplies power to the receiver from that port; don't also power the
  receiver from the RPi.
- Bind the receiver to the transmitter per FlySky's manual, power up the
  Pixhawk, and check QGroundControl's Radio Setup page.
  - **If channels show up and move correctly** - PX4 decoded the iBUS signal
    natively, you're done, no extra hardware needed.
  - **If nothing shows up** - PX4's RC parser on that port didn't recognize
    the iBUS framing. Add a cheap iBUS-to-SBUS (or iBUS-to-PPM) converter
    module between the receiver and the Pixhawk's `RC IN` port; these are
    inexpensive and widely used exactly for FlySky-to-non-iBUS-native flight
    controller compatibility. Re-check Radio Setup after adding it.
- Either way, don't skip verifying every channel moves cleanly (full range,
  no cross-talk between channels) in QGroundControl before doing anything
  else - this is your only manual control link.
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
mode, RC channels) to the Pi, and is what feeds the release switch's
position to `payload_release` (see section 3). If this link drops mid-drop
sequence, the release node's watchdog forces the motor to a close pulse -
see `docs/safety_checklist.md`.

## 3. Raspberry Pi -> L293N -> release motor (active mechanism)

The release actuator is a DC motor driven through an **L293N** H-bridge,
not a hobby servo - it needs digital direction control, not a servo PWM
signal, so this is driven from the Pi's GPIO rather than a Pixhawk AUX
output. (A Pixhawk AUX output was considered first, but an L293N's IN1/IN2
want clean digital logic levels, which a raw servo-style PWM signal doesn't
reliably provide without extra converter hardware - so the Pi does the
decode-and-drive job instead, using the RC switch position it already gets
from MAVROS.)

- **Signal wiring** (default GPIO pins, override via launch arguments):
  - RPi **GPIO23** -> L293N `IN1`
  - RPi **GPIO24** -> L293N `IN2`
  - L293N `ENA` (this channel's enable pin) -> tie **HIGH** (many L293N
    breakout boards ship with a jumper cap on ENA for exactly this - leave
    it on, full speed always). If you want speed control instead, wire ENA
    to a third GPIO pin and set `ena_pin` in the launch args - the default
    `-1` means "not driven from GPIO, tied high externally."
  - RPi GND <-> L293N logic GND (common ground - required even though the
    motor itself is powered separately).
- **Motor power**: L293N `VCC1`/logic supply from the Pi's 3.3V or 5V rail
  is fine (it's just logic level sensing), but `VCC2`/motor supply (`VM`)
  should come from the aircraft's 5-6V BEC/power distribution board, not
  the Pi - the motor can pull well beyond what the Pi's rail is meant to
  source. Common ground between BEC, L293N, and Pi.
- **Mechanical requirement**: the latch mechanism needs a hard stop at both
  open and closed positions. The motor has no position feedback - the node
  actuates it as a timed pulse (`open_duration_sec` / `close_duration_sec`
  in `payload_release.launch.py`, defaulting to 1s each), not a held angle,
  so it relies on the mechanism physically stopping itself at each end
  rather than overshooting. Verify this on the bench before flying.
- Reserve one spare 2-position (or 3-position) switch on the FS-i6/FS-i6X
  transmitter for the release channel (see section 1). Note which AUX
  channel number QGroundControl shows it on - you'll need that index
  (0-based) for `rc_channel_index` in `payload_release.launch.py`.
- See `docs/safety_checklist.md` for the ground-test order - test with
  props off, and with the mechanism off the aircraft first if possible, so
  a mistimed pulse doesn't slam the hard stop under load.

## Power distribution notes for a heavy-lift build

- Motors/ESCs draw from the main flight battery through a power distribution
  board sized for your total current, not through the Pixhawk.
- Pixhawk, the Pi, and the L293N's motor supply (`VM`) should each get power
  from a dedicated 5V-6V BEC rated with headroom above peak draw - don't
  share the ESCs' BEC (if any) for this, ESC BECs are typically undersized
  for motor and companion-computer loads.
- Add a large-enough capacitor or filtered BEC if you see brownout resets
  on the Pi when the motor actuates; this is common on noisy power rails,
  and a DC motor's inrush current is worse than a servo's in this respect.
