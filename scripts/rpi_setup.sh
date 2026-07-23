#!/usr/bin/env bash
# One-time setup for the Raspberry Pi companion computer.
#
# Target OS: Ubuntu Server 22.04 LTS (arm64) on the Raspberry Pi.
# ROS2 Humble only ships official binaries for Ubuntu 22.04 - Raspberry Pi OS
# (Debian-based) would mean building ROS2 from source. Flash Ubuntu Server
# 22.04 arm64 with Raspberry Pi Imager instead; it runs fine headless.
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

echo "== Installing ROS2 Humble =="
sudo apt update
sudo apt install -y curl gnupg lsb-release
sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
  -o /usr/share/keyrings/ros-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] \
http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" \
  | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null

sudo apt update
sudo apt install -y ros-humble-ros-base python3-colcon-common-extensions python3-rosdep

echo "== Installing MAVROS and GeographicLib datasets =="
sudo apt install -y ros-humble-mavros ros-humble-mavros-extras
sudo bash /opt/ros/humble/share/mavros/scripts/install_geographiclib_datasets.sh

echo "== Installing servo/GPIO and pigpio support =="
sudo apt install -y python3-gpiozero python3-pigpio pigpio
sudo systemctl enable --now pigpiod

echo "== Initializing rosdep =="
sudo rosdep init 2>/dev/null || true
rosdep update

echo
echo "Done. Log out/in (or reboot) so the UART and pigpio group changes take effect."
echo "Next: colcon build the workspace in ros2_ws/, then source install/setup.bash."
