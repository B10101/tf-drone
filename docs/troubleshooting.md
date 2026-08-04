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

Try, in order:
1. **Update MAVROS** - this may already be fixed in a newer build:
   ```bash
   sudo apt update
   sudo apt upgrade -y ros-humble-mavros ros-humble-mavros-extras
   ```
2. **Deny-list the `sys_status` plugin** as a workaround:
   ```bash
   ros2 launch drone_bringup mavros_pixhawk.launch.py fcu_url:=/dev/ttyACM0 plugin_denylist:=sys_status
   ```
   Caveat: in most MAVROS versions, `sys_status` is also what publishes
   `/mavros/state` and `/mavros/battery` - denylisting it will blank those
   fields out in `telemetry_logger`. GPS and RC-channel data (separate
   plugins) keep working, so the release-switch feature is unaffected -
   this just isn't a full fix, it's an "unblock testing while waiting on
   upstream" workaround.
