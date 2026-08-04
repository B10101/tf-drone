"""Bring up MAVROS talking to the Pixhawk over a serial telemetry link.

Wire the Pixhawk TELEM2 port to the Raspberry Pi (either directly to a UART
on the 40-pin header, or through a USB-to-serial/telemetry radio). Set the
matching PX4 params on the Pixhawk side (see docs/wiring.md):

    MAV_1_CONFIG   = TELEM2
    MAV_1_MODE     = Onboard
    SER_TEL2_BAUD  = 921600 (must match fcu_url below)
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def _launch_setup(context, *args, **kwargs):
    denylist_str = LaunchConfiguration('plugin_denylist').perform(context)
    plugin_denylist = [p.strip() for p in denylist_str.split(',') if p.strip()]

    allowlist_str = LaunchConfiguration('plugin_allowlist').perform(context)
    plugin_allowlist = [p.strip() for p in allowlist_str.split(',') if p.strip()]

    params = {
        'fcu_url': LaunchConfiguration('fcu_url'),
        'gcs_url': LaunchConfiguration('gcs_url'),
        'target_system_id': LaunchConfiguration('target_system_id'),
        'target_component_id': LaunchConfiguration('target_component_id'),
    }
    # An empty list fails ROS2 parameter type validation (can't infer the
    # array's element type from zero elements) - only set these when there's
    # actually something to deny/allow.
    if plugin_denylist:
        params['plugin_denylist'] = plugin_denylist
    if plugin_allowlist:
        params['plugin_allowlist'] = plugin_allowlist

    return [Node(
        package='mavros',
        executable='mavros_node',
        name='mavros',
        output='screen',
        parameters=[params],
    )]


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
        DeclareLaunchArgument(
            'plugin_denylist', default_value='',
            description="Comma-separated MAVROS plugin names to disable, e.g. 'sys_status' - "
                        "workaround for a startup crash on some MAVROS builds (see "
                        "docs/troubleshooting.md). Empty = load all default plugins.",
        ),
        DeclareLaunchArgument(
            'plugin_allowlist', default_value='sys_status,global_position,rc_io',
            description="Comma-separated MAVROS plugin names to exclusively load. Defaults to "
                        "just what this project needs (state/battery, GPS, RC channels) - "
                        "several other plugins (companion_process_status, debug_value, and "
                        "possibly more) hard-crash mavros_node on startup on this MAVROS "
                        "build, see docs/troubleshooting.md. Set to empty ('') to load all "
                        "default plugins instead (will likely crash until upstream fixes it).",
        ),

        OpaqueFunction(function=_launch_setup),
    ])
