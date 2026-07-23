"""Bring up MAVROS talking to the Pixhawk over a serial telemetry link.

Wire the Pixhawk TELEM2 port to the Raspberry Pi (either directly to a UART
on the 40-pin header, or through a USB-to-serial/telemetry radio). Set the
matching PX4 params on the Pixhawk side (see docs/wiring.md):

    MAV_1_CONFIG   = TELEM2
    MAV_1_MODE     = Onboard
    SER_TEL2_BAUD  = 921600 (must match fcu_url below)
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument(
            'fcu_url', default_value='/dev/ttyAMA0:921600',
            description='MAVLink link to the Pixhawk. Use /dev/ttyUSB0:57600 for a USB telemetry radio.',
        ),
        DeclareLaunchArgument(
            'gcs_url', default_value='',
            description='Optional MAVLink pass-through to a ground station, e.g. udp://@192.168.1.50:14550',
        ),
        DeclareLaunchArgument('target_system_id', default_value='1'),
        DeclareLaunchArgument('target_component_id', default_value='1'),

        Node(
            package='mavros',
            executable='mavros_node',
            name='mavros',
            output='screen',
            parameters=[{
                'fcu_url': LaunchConfiguration('fcu_url'),
                'gcs_url': LaunchConfiguration('gcs_url'),
                'target_system_id': LaunchConfiguration('target_system_id'),
                'target_component_id': LaunchConfiguration('target_component_id'),
            }],
        ),
    ])
