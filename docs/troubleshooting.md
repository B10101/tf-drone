# Troubleshooting

Real issues hit while bringing this up on actual Raspberry Pi + Pixhawk
hardware, and what fixed them.

## `gpiozero.exc.BadPinFactory: Unable to load any default pin factory!`
Every pin factory (lgpio, native, pigpio, ...) fails, including `native`
being unable to open `/dev/gpiomem`/`/dev/mem`. On a real Pi (not a Pi 5),
this is almost always a permissions issue - Ubuntu Server doesn't ship the
udev rule that makes `/dev/gpiochip0` accessible to a non-root user the way
Raspberry Pi OS does.

Fix:
```bash
sudo groupadd -f gpio
sudo usermod -aG gpio $USER
echo 'SUBSYSTEM=="gpio", KERNEL=="gpiochip*", GROUP="gpio", MODE="0660"' | sudo tee /etc/udev/rules.d/99-gpio.rules
sudo udevadm control --reload-rules
sudo udevadm trigger
sudo reboot   # group membership needs a fresh session
```
Verify after reboot: `groups` should list `gpio`, and
`ls -l /dev/gpiochip0` should show group `gpio`.

(On a Pi 5 specifically, this same error can instead mean the installed
`lgpio` is too old to know about the Pi 5's RP1 GPIO chip - that needs a
newer `lgpio`, not a permissions fix.)

## `apt install pigpio` -> "has no installation candidate"
`pigpio` has been dropped from some newer Ubuntu/Debian repos (upstream is
unmaintained). It's not needed for this project's default config anyway -
see the note in `docs/rpi_manual_installs.md`. Just skip it unless you're
wiring `ena_pin` for variable-speed motor control.

## MAVROS: `terminate called ... GeographicLib exception: File not readable`
`mavros_node` hard-crashes on startup (not just a warning) if the
GeographicLib geoid dataset isn't installed. Fix:
```bash
sudo apt install -y geographiclib-tools
sudo geographiclib-get-geoids egm96-5
ls /usr/share/GeographicLib/geoids/   # should show egm96-5.pgm
```

## USB link to the Pixhawk: permission denied on `/dev/ttyACM0`
Same class of issue as GPIO above - your user needs to be in the
`dialout` group:
```bash
sudo usermod -aG dialout $USER
sudo reboot
```
To find the right device path in the first place: `dmesg | tail -20`
right after plugging in, or use the persistent path in
`ls /dev/serial/by-id/` instead of `/dev/ttyACM0` if you want it stable
across reboots/port changes.

## MAVROS: `invalid allocator` / `CompanionProcessStatus` crash on startup
```
create_subscription() called for existing topic name rt/mavros/mavros/status
with incompatible type mavros_msgs::msg::dds_::CompanionProcessStatus_
...
terminate called after throwing an instance of 'rclcpp::exceptions::RCLError'
```
This happens *after* the serial link to the Pixhawk successfully connects
(you'll see `link[1000] detected remote address 1.1` just before it) - so
it's not a wiring/config problem on your end. It's a MAVROS-internal bug
where a companion-process-status topic gets registered twice with
conflicting types; see the similar (though not identical - that one's on
the composable-node path, MAVROS 2.8.0) report at
[mavlink/mavros#1977](https://github.com/mavlink/mavros/issues/1977).

Confirmed on this setup: it's **not** caused by another ROS node running
concurrently (e.g. a separate `cerebro_bridge` node also connected to this
Pi) - the crash reproduces identically with everything else stopped, and
happens purely inside the single `mavros_node` process. It's deterministic
on every startup with this MAVROS build (2.14.0, built 2026-06-08).

It's also **not limited to one plugin** - `companion_process_status` was
the first to crash it, but deny-listing that just moved the identical crash
to `debug_value` next. Both publish+subscribe on a self-referential topic
name (`mavros/mavros/status`, `mavros/mavros/send`), which is the pattern
that seems to trigger it - there may be more affected plugins further down
the list that we never reached.

**Resolved** by switching from deny-listing (whack-a-mole, unknown how many
broken plugins exist) to an **allowlist** of only the plugins this project
actually needs. This is now the default in `mavros_pixhawk.launch.py` -
`plugin_allowlist` defaults to `sys_status,global_position,rc_io`, so
`mavros_node` never attempts to load any of the broken plugins in the first
place. Confirmed working: MAVROS connects cleanly
(`CON: Got HEARTBEAT, connected. FCU: PX4 Autopilot`), state/battery/GPS/RC
all populate in `telemetry_logger`.

You'll still see `VER: autopilot version service timeout` /
`command plugin service call failed!` a few times right after connecting -
that's harmless, just the (intentionally excluded) `command` plugin not
being there to answer a version-check service call. MAVROS retries a few
times, falls back to default capabilities, and moves on; doesn't affect
telemetry or payload release.

If you need a plugin beyond these three later (e.g. `command` for
arming/mode control, if you add autonomous mission logic on the Pi down
the line), add it to `plugin_allowlist` and test it in isolation first -
it may or may not be one of the plugins that crashes on this build.

Still worth trying periodically, since this all looks like an upstream
packaging bug that should get fixed eventually:
```bash
sudo apt update
sudo apt upgrade -y ros-humble-mavros ros-humble-mavros-extras
```
If a fixed build ever lands, `plugin_allowlist` can be cleared back to `''`
to load MAVROS's full default plugin set again.

## `telemetry_logger`/`payload_release` show `rc=waiting...` even though RC is definitely connected
If MAVROS is connected (`conn=True`) and you've confirmed RC actually works
(e.g. you can throttle motors with it), but `/mavros/rc/in` never populates
in our nodes, it's a QoS mismatch, not a wiring/connection problem. MAVROS
publishes high-rate topics like RC channels with best-effort
(`SensorDataQoS`) - a subscriber requesting the ROS2 default `RELIABLE`
QoS can't receive from a best-effort publisher, and it fails *silently*
(no error, just zero messages received).

Fixed in this repo by subscribing to `RCIn` with `qos_profile_sensor_data`
(best-effort) in both `release_node.py` and `telemetry_logger.py`, matching
what was already done for battery/GPS. If you add any other MAVROS
subscription later and it silently never receives anything despite the
topic clearly being published, check this first.
