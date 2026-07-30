# Safety checklist

Heavy-lift multirotors carry more kinetic energy and more consequence per
failure than a small hobby quad, and this project adds a payload that can
fall on something. Go slow.

## Design choices already baked into this repo
- **Flight control is never touched by the payload-release feature.** The
  Raspberry Pi reads MAVROS telemetry (RC channels, state, battery) and
  drives the release motor over its own GPIO to the L293N - it never sends
  anything back to the Pixhawk. A Pi crash, a bad launch file, or a bug in
  `payload_release` cannot affect flight control; the pilot's FlySky link to
  the Pixhawk is completely separate (see `docs/wiring.md`).
- **RC link loss forces a close pulse**, not open (`release_node.py`,
  `_periodic`). Losing telemetry can never itself cause a release.
- **Debounced switch input.** The release channel must hold past threshold
  for `debounce_sec` (default 0.2s) before actuating, so a noisy channel or
  a brief switch flick during arming/mode changes can't trigger it.
- **Timed pulses, not held position.** Unlike a servo, the L293N-driven
  motor has no position feedback - `open_duration_sec`/`close_duration_sec`
  (default 1s each) control how long it runs before stopping. This assumes
  a mechanical hard stop at both ends of travel; get that duration and the
  hard stop right on the bench, since a too-long pulse runs the motor
  against the stop for longer than necessary, and a too-short one may not
  fully release the payload.

## Ground testing, in this order
1. Props off, mechanism off the aircraft if possible. Bench-test the
   release motor via the `~/drop` and `~/reset` services, confirming it
   drives fully open and fully closed against its hard stops without
   binding or stalling audibly.
2. Props off. Mount the mechanism, launch `full_system.launch.py`, and flip
   the FlySky release switch. Confirm `~payload_release_node/state` toggles
   and the motor runs both directions through the real RC path (transmitter
   -> receiver -> Pixhawk -> MAVROS -> release node).
3. Props off. Kill the RPi telemetry connection mid-test (unplug the
   TELEM2/USB link) with the latch open, and confirm the watchdog forces a
   close pulse within `rc_timeout_sec`.
4. Props off. Full RC range check in QGroundControl's Radio Setup page -
   every channel including the release switch should read clean min/max
   with no overlap with other channels.
5. Props on, tethered/restrained. Verify arming, mode switching, and RC
   response before any free flight.
6. Free flight, empty (no payload), before ever adding weight.
7. Free flight with the actual payload, starting light and working up to
   the target weight, re-checking hover throttle and handling at each step
   (see `docs/px4_params_heavy_lift.md`).

## Standing rules
- Never fly over people or vehicles when carrying a droppable payload,
  regardless of how well the release mechanism has been bench-tested.
- Set a geofence and RTL/battery failsafes before any flight with a
  payload aboard - a heavy aircraft has less power margin than it did
  empty.
- Re-verify the release mechanism (steps 1-3 above) after any change to the
  motor mounting, linkage, pulse durations, or `payload_release` code -
  mechanical latches drift and code changes can regress the
  debounce/watchdog/timing behavior.
- Keep a hard mechanical safety (e.g. a pin or tie securing the latch)
  during transport and setup, removed only immediately before flight.
