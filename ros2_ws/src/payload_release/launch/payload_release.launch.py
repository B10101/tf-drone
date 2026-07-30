from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('in1_pin', default_value='23',
                               description='RPi BCM GPIO pin -> L293N IN1.'),
        DeclareLaunchArgument('in2_pin', default_value='24',
                               description='RPi BCM GPIO pin -> L293N IN2.'),
        DeclareLaunchArgument('ena_pin', default_value='-1',
                               description='RPi BCM GPIO pin -> L293N ENA, or -1 if ENA is '
                                            'tied high externally (e.g. the board\'s own jumper).'),
        DeclareLaunchArgument('speed', default_value='1.0',
                               description='Motor speed 0.0-1.0, only meaningful if ena_pin is set.'),
        DeclareLaunchArgument('open_duration_sec', default_value='1.0',
                               description='How long to run the motor forward to release the payload.'),
        DeclareLaunchArgument('close_duration_sec', default_value='1.0',
                               description='How long to run the motor backward to reset the latch.'),
        DeclareLaunchArgument('use_pigpio', default_value='false',
                               description='Use the pigpio daemon for the ENA PWM pin (only relevant '
                                            'if ena_pin is set). Requires `sudo pigpiod` running.'),
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
                'in1_pin': LaunchConfiguration('in1_pin'),
                'in2_pin': LaunchConfiguration('in2_pin'),
                'ena_pin': LaunchConfiguration('ena_pin'),
                'speed': LaunchConfiguration('speed'),
                'open_duration_sec': LaunchConfiguration('open_duration_sec'),
                'close_duration_sec': LaunchConfiguration('close_duration_sec'),
                'use_pigpio': LaunchConfiguration('use_pigpio'),
                'rc_channel_index': LaunchConfiguration('rc_channel_index'),
                'rc_open_threshold_us': LaunchConfiguration('rc_open_threshold_us'),
                'rc_close_threshold_us': LaunchConfiguration('rc_close_threshold_us'),
                'rc_timeout_sec': LaunchConfiguration('rc_timeout_sec'),
                'debounce_sec': LaunchConfiguration('debounce_sec'),
            }],
        ),
    ])
