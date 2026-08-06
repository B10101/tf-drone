"""ROS2 node that logs Pixhawk telemetry (via MAVROS) to the terminal.

Subscribes to state, battery, GPS, altitude, RC, and motor-output MAVROS
topics, and logs one formatted summary line at a fixed rate (`rate_hz`,
default 1Hz) rather than reacting to every message - several of these
topics publish fast enough that per-message logging would just flood the
terminal.

Note on `motor_out`: this project's ESCs (Hobbywing SkyWalker V2) have no
telemetry return wire, so there is no measured RPM/current/temperature to
read. `/mavros/rc/out` is PX4's *commanded* PWM output to each motor, not
confirmation the motor is actually spinning at that speed - it's useful for
seeing what PX4 is telling the ESCs to do, not a substitute for real ESC
telemetry. If real feedback is ever needed, that requires different ESCs
(e.g. Hobbywing's CAN-bus XRotor/Platinum Pro line, or any BLHeli32/KISS/
bidirectional-DShot ESC) - a hardware change, not something fixable here.
"""

import math

import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data

from mavros_msgs.msg import RCIn, RCOut, State
from sensor_msgs.msg import BatteryState, NavSatFix
from std_msgs.msg import Float64


class TelemetryLogger(Node):
    def __init__(self):
        super().__init__('telemetry_logger')

        self.declare_parameter('rate_hz', 1.0)

        self._state = None
        self._battery = None
        self._gps = None
        self._rel_alt = None
        self._rc = None
        self._motor_out = None

        self.create_subscription(State, '/mavros/state', self._on_state, 10)
        self.create_subscription(
            BatteryState, '/mavros/battery', self._on_battery, qos_profile_sensor_data)
        self.create_subscription(
            NavSatFix, '/mavros/global_position/global', self._on_gps, qos_profile_sensor_data)
        self.create_subscription(
            Float64, '/mavros/global_position/rel_alt', self._on_rel_alt, qos_profile_sensor_data)
        self.create_subscription(
            RCIn, '/mavros/rc/in', self._on_rc, qos_profile_sensor_data)
        self.create_subscription(
            RCOut, '/mavros/rc/out', self._on_motor_out, qos_profile_sensor_data)

        rate_hz = self.get_parameter('rate_hz').value
        self.create_timer(1.0 / rate_hz, self._log_summary)

    def _on_state(self, msg):
        self._state = msg

    def _on_battery(self, msg):
        self._battery = msg

    def _on_gps(self, msg):
        self._gps = msg

    def _on_rel_alt(self, msg):
        self._rel_alt = msg.data

    def _on_rc(self, msg):
        self._rc = msg

    def _on_motor_out(self, msg):
        self._motor_out = msg

    def _log_summary(self):
        parts = [self._state_str(), self._battery_str(), self._gps_str(),
                 self._alt_str(), self._rc_str(), self._motor_out_str()]
        self.get_logger().info(' | '.join(parts))

    def _state_str(self):
        if self._state is None:
            return 'state=waiting...'
        return (f'conn={self._state.connected} armed={self._state.armed} '
                f'mode={self._state.mode}')

    def _battery_str(self):
        if self._battery is None:
            return 'batt=waiting...'
        pct = self._battery.percentage
        if pct is not None and not math.isnan(pct) and pct >= 0:
            pct_str = f'{pct * 100:.0f}%'
        else:
            pct_str = '?'
        return f'batt={self._battery.voltage:.2f}V ({pct_str})'

    def _gps_str(self):
        if self._gps is None:
            return 'gps=waiting...'
        fix_ok = self._gps.status.status >= 0
        return (f"gps={'fix' if fix_ok else 'no-fix'} "
                f'lat={self._gps.latitude:.6f} lon={self._gps.longitude:.6f}')

    def _alt_str(self):
        if self._rel_alt is None:
            return 'alt=waiting...'
        return f'alt={self._rel_alt:.1f}m'

    def _rc_str(self):
        if self._rc is None or not self._rc.channels:
            return 'rc=waiting...'
        return f'rc_ch1={self._rc.channels[0]}us rssi={self._rc.rssi}'

    def _motor_out_str(self):
        # "Commanded" PWM to each motor, not measured feedback - see the
        # module docstring. SkyWalker V2 ESCs have no telemetry return.
        if self._motor_out is None or not self._motor_out.channels:
            return 'motor_out=waiting...'
        values = ','.join(str(v) for v in self._motor_out.channels)
        return f'motor_out(cmd)=[{values}]us'


def main(args=None):
    rclpy.init(args=args)
    node = TelemetryLogger()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
