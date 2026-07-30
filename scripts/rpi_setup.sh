#!/usr/bin/env bash
# One-time device/config setup for the Raspberry Pi companion computer.
#
# This script does NOT install packages - see the "Manual installs" list
# printed at the end (or docs/rpi_manual_installs.md) for what to apt
# install yourself first. This only handles config that isn't a package
# install: enabling the UART for Pixhawk telemetry, freeing it from the
# Linux serial console, and enabling the pigpiod service.
#
# Target OS: Ubuntu Server 22.04 LTS (arm64) on the Raspberry Pi.
#
# Run as the regular user (not root); the script uses sudo where needed.

set -euo pipefail

if [[ "$(id -u)" -eq 0 ]]; then
  echo "Run this as your normal user, not root (it uses sudo internally)." >&2
  exit 1
fi

echo "== Enabling the UART for Pixhawk telemetry =="
if ! grep -q "^enable_uart=1" /boot/firmware/config.txt 2>/dev/null; then
  echo "enable_uart=1" | sudo tee -a /boot/firmware/config.txt
fi
# Disable the serial console so the UART is free for MAVLink instead.
sudo systemctl disable --now serial-getty@ttyAMA0.service 2>/dev/null || true
sudo raspi-config nonint do_serial_hw 0 2>/dev/null || true

echo "== Enabling pigpiod (requires the pigpio package - see manual installs below) =="
sudo systemctl enable --now pigpiod

echo
echo "Done. Log out/in (or reboot) so the UART and pigpio group changes take effect."
echo
echo "== Manual installs still needed (if not already done) =="
echo "  sudo apt install -y python3-colcon-common-extensions python3-rosdep"
echo "  sudo apt install -y ros-humble-mavros ros-humble-mavros-extras"
echo "  sudo bash /opt/ros/humble/share/mavros/scripts/install_geographiclib_datasets.sh"
echo "  sudo apt install -y python3-gpiozero python3-pigpio pigpio"
echo "  sudo rosdep init  # ok if it errors saying it's already initialized"
echo "  rosdep update"
echo
echo "Then: colcon build the workspace in ros2_ws/, and source install/setup.bash."
