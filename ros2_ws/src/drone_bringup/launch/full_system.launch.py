"""Bring up the whole companion-computer stack: MAVROS + payload release +
telemetry logging."""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource


def generate_launch_description():
    bringup_share = get_package_share_directory('drone_bringup')
    mavros_launch = os.path.join(bringup_share, 'launch', 'mavros_pixhawk.launch.py')
    telemetry_launch = os.path.join(bringup_share, 'launch', 'telemetry_logger.launch.py')
    payload_launch = os.path.join(
        get_package_share_directory('payload_release'), 'launch', 'payload_release.launch.py'
    )

    return LaunchDescription([
        IncludeLaunchDescription(PythonLaunchDescriptionSource(mavros_launch)),
        IncludeLaunchDescription(PythonLaunchDescriptionSource(telemetry_launch)),
        IncludeLaunchDescription(PythonLaunchDescriptionSource(payload_launch)),
    ])
