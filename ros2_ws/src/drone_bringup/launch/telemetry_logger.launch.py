from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('rate_hz', default_value='1.0',
                               description='How often to log a telemetry summary line.'),

        Node(
            package='drone_bringup',
            executable='telemetry_logger',
            name='telemetry_logger',
            output='screen',
            parameters=[{
                'rate_hz': LaunchConfiguration('rate_hz'),
            }],
        ),
    ])
