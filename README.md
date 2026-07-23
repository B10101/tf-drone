# Heavy-lift drone - companion computer software

PX4 flight stack on a Pixhawk (1.4 hardware), FlySky RC as the primary
manual control link, and a Raspberry Pi as a companion computer for
features beyond core flight control - starting with a servo-actuated
payload release.

## Architecture

```
FlySky transmitter --SBUS--> Pixhawk (PX4) <--MAVLink (TELEM2)--> Raspberry Pi
                                  |                                    |
                             motors/ESCs                    ROS2: mavros + payload_release
                                                                        |
                                                              release servo (GPIO18)
```

Two independent links, by design (see `docs/wiring.md` for the reasoning):
- **FlySky -> Pixhawk**: direct manual control, doesn't depend on the Pi at all.
- **Pixhawk <-> Pi (MAVLink/MAVROS)**: telemetry in, and the payload-release
  feature. The Pi never sends flight commands - if this link or the Pi
  itself dies, the aircraft keeps flying normally under RC control.

## Layout

- `ros2_ws/src/payload_release/` - ROS2 package: servo driver + node that
  releases the payload either from a spare FlySky switch (read back via
  MAVROS RC passthrough) or a `std_srvs/Trigger` service, with a link-loss
  watchdog that fails closed.
- `ros2_ws/src/drone_bringup/` - launch files that start MAVROS pointed at
  the Pixhawk, and a combined launch bringing up the whole stack.
- `scripts/rpi_setup.sh` - one-time Raspberry Pi provisioning (ROS2 Humble,
  MAVROS, pigpio, UART enablement).
- `docs/wiring.md` - physical wiring for all three links (RC, telemetry,
  servo) and power distribution notes.
- `docs/px4_params_heavy_lift.md` - PX4 parameter checklist to review for a
  heavy-lift airframe (not paste-in values - these depend on your build).
- `docs/safety_checklist.md` - test order and standing safety rules, given
  this aircraft carries and drops a payload.

## Getting started

1. **Wire it up** - `docs/wiring.md`.
2. **Configure PX4** - work through `docs/px4_params_heavy_lift.md` in
   QGroundControl before connecting the companion computer.
3. **Provision the Pi** - flash Ubuntu Server 22.04 (arm64), then:
   ```
   ./scripts/rpi_setup.sh
   ```
4. **Build the workspace** on the Pi:
   ```
   cd ros2_ws
   rosdep install --from-paths src --ignore-src -r -y
   colcon build --symlink-install
   source install/setup.bash
   ```
5. **Bring up the stack**:
   ```
   ros2 launch drone_bringup full_system.launch.py
   ```
   Adjust `fcu_url`, `rc_channel_index`, and the servo angles/pin via launch
   arguments to match your wiring - see the argument descriptions in
   `ros2_ws/src/drone_bringup/launch/mavros_pixhawk.launch.py` and
   `ros2_ws/src/payload_release/launch/payload_release.launch.py`.
6. **Test before flying** - follow `docs/safety_checklist.md` in order,
   props off first.

## Manual payload trigger (bench testing)

```
ros2 service call /payload_release_node/drop std_srvs/srv/Trigger {}
ros2 service call /payload_release_node/reset std_srvs/srv/Trigger {}
```

## Status / what's not here yet

This is a real-hardware scaffold, not a simulated one - there's no PX4
SITL/Gazebo setup in this repo. It also doesn't include any autonomous
mission logic (waypoint following, offboard control) - the Pi currently
only *observes* MAVROS telemetry and controls the release servo. Add
mission logic as a separate node later if needed, and re-read
`docs/px4_params_heavy_lift.md` section 4 first, since that changes the
"Pi never commands the aircraft" safety property this scaffold currently
relies on.
