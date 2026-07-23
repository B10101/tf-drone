"""GPIO/PWM driver for the payload-release servo.

Uses gpiozero so the signal source (native RPi PWM vs. pigpio daemon) is
swappable without touching the release node. pigpio is strongly recommended
on a flying vehicle: gpiozero's default software PWM can jitter under load,
which makes a servo twitch or drift out of its latched position.
"""

from gpiozero import AngularServo


class PayloadServo:
    """Wraps a single servo used to actuate a payload latch/hook."""

    def __init__(
        self,
        gpio_pin: int,
        closed_angle: float,
        open_angle: float,
        min_pulse_width: float = 0.0005,
        max_pulse_width: float = 0.0025,
        use_pigpio: bool = True,
    ):
        pin_factory = None
        if use_pigpio:
            from gpiozero.pins.pigpio import PiGPIOFactory

            pin_factory = PiGPIOFactory()

        self._servo = AngularServo(
            gpio_pin,
            min_angle=-90,
            max_angle=90,
            min_pulse_width=min_pulse_width,
            max_pulse_width=max_pulse_width,
            pin_factory=pin_factory,
        )
        self._closed_angle = closed_angle
        self._open_angle = open_angle
        self.close()

    def open(self) -> None:
        self._servo.angle = self._open_angle

    def close(self) -> None:
        self._servo.angle = self._closed_angle

    def detach(self) -> None:
        """Stop sending a PWM signal (servo goes limp)."""
        self._servo.detach()
