# Raspberry Pi: manual package installs

`scripts/rpi_setup.sh` only handles device/config setup (enabling the
UART, enabling pigpiod) - it doesn't install packages. Run these yourself
first (skip anything you've already installed):

```bash
# Assumes ROS2 Humble itself is already installed (ROS_DISTRO=humble).
# If not, follow the official ROS2 Humble install docs for Ubuntu 22.04
# arm64 before continuing.

sudo apt update

# Build/dependency tooling
sudo apt install -y python3-colcon-common-extensions python3-rosdep

# MAVROS (talks to the Pixhawk over MAVLink)
sudo apt install -y ros-humble-mavros ros-humble-mavros-extras

# GeographicLib dataset - REQUIRED. On the mavros build tested with this
# repo (2.14.0, Aug 2026), mavros_node hard-crashes on startup
# (std::invalid_argument, "GeographicLib exception: File not readable")
# if this is missing - it's not just a nice-to-have for GPS altitude.
# MAVROS ships a wrapper script for this, but its path has moved between
# versions - if this exact path 404s, `find /opt/ros/humble -iname
# "*geographiclib*"` to locate it, or just skip the wrapper and fetch the
# dataset directly:
#   sudo apt install -y geographiclib-tools
#   sudo geographiclib-get-geoids egm96-5
sudo bash /opt/ros/humble/share/mavros/scripts/install_geographiclib_datasets.sh \
  || (sudo apt install -y geographiclib-tools && sudo geographiclib-get-geoids egm96-5)
# Verify: ls /usr/share/GeographicLib/geoids/ should show egm96-5.pgm

# GPIO/motor control support (payload_release)
sudo apt install -y python3-gpiozero

# rosdep (one-time init, then update)
sudo rosdep init   # ok if it errors saying it's already initialized
rosdep update
```

**About `pigpio`** - deliberately left out above. It's only needed for
jitter-free PWM, which only matters here if you wire `ena_pin` for
variable-speed motor control (the default `ena_pin: -1` ties ENA high
instead - IN1/IN2 are plain digital signals, no PWM involved, so
`pigpio` buys nothing in the default config). It's also been dropped from
some newer Ubuntu/Debian repos since upstream is unmaintained - if
`apt install pigpio` fails with "no installation candidate", that's why.
If you do need it later: `sudo apt install -y python3-pigpio pigpio`, or
build it from source from the archived upstream repo if your distro
doesn't carry it.

**Quick check that everything's present:**
```bash
echo $ROS_DISTRO   # should print: humble
dpkg -l | grep -E "ros-humble-mavros|python3-gpiozero|pigpio"
```

After these are installed, run `./scripts/rpi_setup.sh` for the
remaining device/config steps (UART, pigpiod), then build the workspace -
see the top-level `README.md`.
