# PX4 parameter checklist for a heavy-lift build

These are **not** ready-to-paste values - the correct numbers depend on your
frame (quad/hex/octo), motors, ESCs, props, and all-up weight including
payload. Get them right in QGroundControl's Vehicle Setup, then tune in the
field. Treat this as a checklist of what to touch, not a config file.

## 1. Airframe & outputs
- **Airframe**: QGC Vehicle Setup -> Airframe -> pick the frame class that
  matches your motor count/layout (e.g. Hexa X, Octo X). This sets sane
  defaults for `CA_ROTOR_COUNT`, `CA_ROTORn_*`, and `MAV_TYPE`.
- **ESC/output protocol**: set `PWM_MAIN`/`DSHOT`/whatever your ESCs speak
  under Actuators. Calibrate ESCs (QGC Power Setup) before ever spinning
  props with the frame connected.
- **Battery**: set `BAT1_V_EMPTY`, `BAT1_V_CHARGED`, `BAT1_N_CELLS`, and
  `BAT1_CAPACITY` for your actual pack. Wrong values make battery-percentage
  failsafes lie to you.

## 2. Failsafes (tighten these for a heavy aircraft, don't loosen them)
- `COM_LOW_BAT_ACT` / `BAT_LOW_THR`, `BAT_CRIT_THR`, `BAT_EMERGEN_THR`:
  set with enough margin that RTL can complete before critical - a loaded
  heavy-lift airframe draws more current and has less reserve than it looks
  like on a bench test.
- `COM_RC_LOSS_T`: RC loss timeout - keep short given FlySky is your primary
  control link.
- `COM_OBL_ACT` / `COM_OBL_RC_ACT`: offboard/data-link-loss action - since
  this project doesn't do offboard flight control from the RPi, leave these
  at RTL/Land defaults; MAVROS on the Pi never sends flight commands here.
- `GF_ACTION` + a geofence (QGC Plan view): strongly recommended once you're
  doing free flights with a payload, so a fly-away doesn't end over a
  parking lot.
- `LNDMC_*` (land detector): heavy-lift aircraft often land "softer" on the
  sensed accel/thrust signature; verify the land detector actually declares
  landed on your airframe, or it can complicate disarm-on-land logic.

## 3. Tuning (expect to spend real bench/field time here)
- Confirm thrust-to-weight: hover throttle (`MPC_THR_HOVER`, read back after
  a hover test) should sit comfortably below ~60-65%, giving margin for wind
  and the payload's weight. If hover throttle is much higher, the build is
  underpowered for reliable heavy-lift work.
- Re-run the autotune (or manual PID tuning) **with the payload aboard at
  the weight you'll actually fly**, not empty. Mass changes the whole rate
  response.
- `MPC_XY_VEL_MAX`, `MPC_Z_VEL_MAX`, `MPC_TILTMAX_AIR`: consider capping
  these conservatively for a heavy airframe - aggressive tilt/accel limits
  tuned for a light quad can exceed what a loaded heavy-lift frame can
  actually track.

## 4. Companion computer link (this repo's part)
- `MAV_1_CONFIG = TELEM2`, `MAV_1_MODE = Onboard`, `SER_TEL2_BAUD = 921600`
  (or whichever port/baud you wired per `docs/wiring.md`) - this is the link
  `mavros_pixhawk.launch.py` connects over.
- MAVROS is used read-only here (RC/state/battery telemetry) - the Pi never
  sends flight-mode or actuator commands to the flight controller. It does
  drive the payload-release motor, but that's over the Pi's own GPIO to the
  L293N, not through the Pixhawk at all (see `docs/wiring.md` section 3) -
  so a bug in that code still can't affect flight control, only the
  release mechanism.
- If you later add autonomous mission logic on the Pi (waypoint/offboard
  control), revisit `COM_OBL_ACT`/`COM_OBL_RC_ACT` and add an explicit
  offboard-loss failsafe test before flying it - today nothing here
  triggers those paths.

## 5. Payload release (handled by the Pi, not PX4)
The release motor is driven from the Raspberry Pi's GPIO through an L293N
H-bridge - see `docs/wiring.md` section 3 for the physical wiring and why
it's Pi-driven rather than a Pixhawk AUX output (an L293N wants clean
digital direction pins, not a servo-style PWM signal).

PX4's only role in this feature is decoding the FlySky release switch as an
RC channel (automatic, no config beyond normal RC calibration) - MAVROS on
the Pi reads that channel back and the `payload_release` node does the
rest. There's nothing to configure in QGC's Actuators page for this.

## Before the first flight with a real payload
1. Bench-test the release motor via the `~/drop` and `~/reset` services
   with props off, ideally with the mechanism off the aircraft first so a
   mistimed pulse doesn't slam a hard stop under load.
2. Verify the FlySky release switch actuates the motor through the full RC
   path (transmitter -> receiver -> Pixhawk -> MAVROS -> release node).
3. Pull the RPi's telemetry cable mid-test and confirm the release node's
   watchdog forces a close pulse (see `docs/safety_checklist.md`).
4. Fly empty first, then fly with the payload at increasing weight, checking
   hover throttle and control response each step.
