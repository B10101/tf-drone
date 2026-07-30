"""GPIO driver for the L293N-driven payload release motor.

The L293N is an H-bridge: IN1/IN2 pick direction, ENA enables/speed-controls
the output. Unlike a servo, a DC motor has no absolute position feedback -
there is no angle to hold. Actuation is timed: run the motor for a fixed
duration, then stop, relying on a mechanical hard stop at each end of travel
so a pulse issued when already at that end is harmless. Timing the pulse is
the release node's job; this class only starts and stops the motor.
"""

from gpiozero import Motor


class PayloadMotor:
    def __init__(
        self,
        in1_pin: int,
        in2_pin: int,
        ena_pin: int = -1,
        speed: float = 1.0,
        use_pigpio: bool = False,
    ):
        """ena_pin=-1 means ENA is tied high externally (e.g. the L293N
        breakout's own jumper) and isn't driven from a GPIO pin at all.
        """
        pin_factory = None
        if use_pigpio:
            from gpiozero.pins.pigpio import PiGPIOFactory

            pin_factory = PiGPIOFactory()

        self._motor = Motor(
            forward=in1_pin,
            backward=in2_pin,
            enable=(ena_pin if ena_pin >= 0 else None),
            pin_factory=pin_factory,
        )
        self._speed = speed
        self.stop()

    def run_open(self) -> None:
        self._motor.forward(self._speed)

    def run_close(self) -> None:
        self._motor.backward(self._speed)

    def stop(self) -> None:
        self._motor.stop()
