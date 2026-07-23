"""ROS2 node that controls the payload-release servo.

Two independent trigger paths are supported:

1. RC passthrough - a spare FlySky transmitter switch, mapped to an AUX
   channel on the Pixhawk, is read back over MAVROS (`/mavros/rc/in`). This
   lets the pilot release the payload by hand, the same way they fly the
   rest of the aircraft.
2. A `std_srvs/Trigger` service pair (`~/drop`, `~/reset`) for bench testing
   or for a future companion-computer mission node to call.

Safety behaviour:
- If RC data stops arriving (link lost) for longer than `rc_timeout_sec`,
  the node forces the servo closed and stops trusting RC until fresh data
  arrives. A dropped link should never leave the hook open.
- The RC channel needs to hold past the open/close thresholds for
  `debounce_sec` before a state change is actuated, so signal noise near the
  threshold can't chatter the servo.
"""

import time

import rclpy
from rclpy.node import Node
from std_msgs.msg import Bool
from std_srvs.srv import Trigger

from payload_release.servo_driver import PayloadServo

try:
    from mavros_msgs.msg import RCIn
except ImportError:  # pragma: no cover - mavros_msgs not built yet
    RCIn = None


class ReleaseNode(Node):
    def __init__(self):
        super().__init__('payload_release_node')

        self.declare_parameter('gpio_pin', 18)
        self.declare_parameter('closed_angle', 0.0)
        self.declare_parameter('open_angle', 90.0)
        self.declare_parameter('use_pigpio', True)
        self.declare_parameter('rc_channel_index', 6)  # 0-based; channel 7
        self.declare_parameter('rc_open_threshold_us', 1700)
        self.declare_parameter('rc_close_threshold_us', 1300)
        self.declare_parameter('rc_timeout_sec', 1.0)
        self.declare_parameter('debounce_sec', 0.2)

        self._rc_channel_index = self.get_parameter('rc_channel_index').value
        self._open_us = self.get_parameter('rc_open_threshold_us').value
        self._close_us = self.get_parameter('rc_close_threshold_us').value
        self._rc_timeout = self.get_parameter('rc_timeout_sec').value
        self._debounce_sec = self.get_parameter('debounce_sec').value

        self._servo = PayloadServo(
            gpio_pin=self.get_parameter('gpio_pin').value,
            closed_angle=self.get_parameter('closed_angle').value,
            open_angle=self.get_parameter('open_angle').value,
            use_pigpio=self.get_parameter('use_pigpio').value,
        )

        self._is_open = False
        self._last_rc_stamp = None
        self._pending_state = None
        self._pending_since = None

        self._state_pub = self.create_publisher(Bool, '~/state', 10)

        if RCIn is not None:
            self.create_subscription(RCIn, '/mavros/rc/in', self._on_rc, 10)
        else:
            self.get_logger().warn(
                'mavros_msgs not available - RC trigger path disabled, '
                'only the ~/drop and ~/reset services will work.'
            )

        self.create_service(Trigger, '~/drop', self._on_drop_srv)
        self.create_service(Trigger, '~/reset', self._on_reset_srv)

        self.create_timer(0.2, self._watchdog)

        self._publish_state()
        self.get_logger().info('Payload release node ready (latch closed).')

    def _on_rc(self, msg) -> None:
        self._last_rc_stamp = time.monotonic()

        if self._rc_channel_index >= len(msg.channels):
            self.get_logger().warn(
                f'rc_channel_index {self._rc_channel_index} out of range '
                f'for {len(msg.channels)} channels', throttle_duration_sec=5.0
            )
            return

        pwm_us = msg.channels[self._rc_channel_index]

        if pwm_us >= self._open_us:
            desired = True
        elif pwm_us <= self._close_us:
            desired = False
        else:
            self._pending_state = None
            return

        self._debounce_and_apply(desired)

    def _debounce_and_apply(self, desired: bool) -> None:
        now = time.monotonic()
        if desired == self._is_open:
            self._pending_state = None
            return

        if self._pending_state != desired:
            self._pending_state = desired
            self._pending_since = now
            return

        if now - self._pending_since >= self._debounce_sec:
            self._set_state(desired)
            self._pending_state = None

    def _watchdog(self) -> None:
        if self._last_rc_stamp is None:
            return
        age = time.monotonic() - self._last_rc_stamp
        if age > self._rc_timeout and self._is_open:
            self.get_logger().error(
                f'RC link stale for {age:.1f}s - forcing payload latch closed.'
            )
            self._set_state(False)

    def _set_state(self, open_state: bool) -> None:
        if open_state:
            self._servo.open()
            self.get_logger().info('Payload latch OPEN - release triggered.')
        else:
            self._servo.close()
            self.get_logger().info('Payload latch CLOSED.')
        self._is_open = open_state
        self._publish_state()

    def _publish_state(self) -> None:
        msg = Bool()
        msg.data = self._is_open
        self._state_pub.publish(msg)

    def _on_drop_srv(self, request, response):
        self._set_state(True)
        response.success = True
        response.message = 'Payload latch opened.'
        return response

    def _on_reset_srv(self, request, response):
        self._set_state(False)
        response.success = True
        response.message = 'Payload latch closed.'
        return response


def main(args=None):
    rclpy.init(args=args)
    node = ReleaseNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
