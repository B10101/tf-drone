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
sudo bash /opt/ros/humble/share/mavros/scripts/install_geographiclib_datasets.sh

# GPIO/motor control support (payload_release)
sudo apt install -y python3-gpiozero python3-pigpio pigpio

# rosdep (one-time init, then update)
sudo rosdep init   # ok if it errors saying it's already initialized
rosdep update
```

**Quick check that everything's present:**
```bash
echo $ROS_DISTRO   # should print: humble
dpkg -l | grep -E "ros-humble-mavros|python3-gpiozero|pigpio"
```

After these are installed, run `./scripts/rpi_setup.sh` for the
remaining device/config steps (UART, pigpiod), then build the workspace -
see the top-level `README.md`.
