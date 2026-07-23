# Safety checklist

Heavy-lift multirotors carry more kinetic energy and more consequence per
failure than a small hobby quad, and this project adds a payload that can
fall on something. Go slow.

## Design choices already baked into this repo
- **Flight control is never touched by the companion computer.** The
  Raspberry Pi only reads MAVROS telemetry (RC channels, state, battery) and
  drives an independent servo GPIO pin. A Pi crash, a bad launch file, or a
  MAVROS bug cannot command the aircraft to move - the pilot's FlySky link
  to the Pixhawk is completely separate (see `docs/wiring.md`).
- **RC link loss forces the payload latch closed**, not open
  (`payload_release/release_node.py`, `_watchdog`). Losing telemetry can
  never itself cause a release.
- **Debounced switch input.** The release channel must hold past threshold
  for `debounce_sec` (default 0.2s) before actuating, so a noisy channel or
  a brief switch flick during arming/mode changes can't trigger it.

## Ground testing, in this order
1. Props off. Power up Pixhawk + RPi, launch `full_system.launch.py`, and
   flip the FlySky release switch. Confirm `~payload_release_node/state`
   toggles and the servo moves both directions.
2. Props off. Kill the RPi telemetry connection mid-test (unplug the
   TELEM2/USB link) with the latch open, and confirm it force-closes within
   `rc_timeout_sec`.
3. Props off. Full RC range check in QGroundControl's Radio Setup page -
   every channel including the release switch should read clean min/max
   with no overlap with other channels.
4. Props on, tethered/restrained. Verify arming, mode switching, and RC
   response before any free flight.
5. Free flight, empty (no payload), before ever adding weight.
6. Free flight with the actual payload, starting light and working up to
   the target weight, re-checking hover throttle and handling at each step
   (see `docs/px4_params_heavy_lift.md`).

## Standing rules
- Never fly over people or vehicles when carrying a droppable payload,
  regardless of how well the release mechanism has been bench-tested.
- Set a geofence and RTL/battery failsafes before any flight with a
  payload aboard - a heavy aircraft has less power margin than it did
  empty.
- Re-verify the release mechanism (step 1-2 above) after any change to the
  servo mounting, linkage, or `payload_release` code - mechanical latches
  drift and code changes can regress the debounce/watchdog behavior.
- Keep a hard mechanical safety (e.g. a pin or tie securing the latch)
  during transport and setup, removed only immediately before flight.
