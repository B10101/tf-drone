from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('gpio_pin', default_value='18',
                               description='RPi BCM GPIO pin driving the release servo (18 = hardware PWM).'),
        DeclareLaunchArgument('closed_angle', default_value='0.0'),
        DeclareLaunchArgument('open_angle', default_value='90.0'),
        DeclareLaunchArgument('use_pigpio', default_value='true',
                               description='Use the pigpio daemon for jitter-free PWM (recommended). '
                                            'Requires `sudo pigpiod` running.'),
        DeclareLaunchArgument('rc_channel_index', default_value='6',
                               description='0-based index into mavros RCIn.channels for the release switch.'),
        DeclareLaunchArgument('rc_open_threshold_us', default_value='1700'),
        DeclareLaunchArgument('rc_close_threshold_us', default_value='1300'),
        DeclareLaunchArgument('rc_timeout_sec', default_value='1.0'),
        DeclareLaunchArgument('debounce_sec', default_value='0.2'),

        Node(
            package='payload_release',
            executable='release_node',
            name='payload_release_node',
            output='screen',
            parameters=[{
                'gpio_pin': LaunchConfiguration('gpio_pin'),
                'closed_angle': LaunchConfiguration('closed_angle'),
                'open_angle': LaunchConfiguration('open_angle'),
                'use_pigpio': LaunchConfiguration('use_pigpio'),
                'rc_channel_index': LaunchConfiguration('rc_channel_index'),
                'rc_open_threshold_us': LaunchConfiguration('rc_open_threshold_us'),
                'rc_close_threshold_us': LaunchConfiguration('rc_close_threshold_us'),
                'rc_timeout_sec': LaunchConfiguration('rc_timeout_sec'),
                'debounce_sec': LaunchConfiguration('debounce_sec'),
            }],
        ),
    ])
