from time import sleep

from gpiozero import AngularServo
from gpiozero.pins.lgpio import LGPIOFactory

SERVO_PIN = 18
ANGLE_REST = 180
ANGLE_TRIGGER = 90
SETTLE_SECONDS = 0.5

_servo: AngularServo | None = None
_factory: LGPIOFactory | None = None


def _init():
    global _servo, _factory
    if _servo is None:
        _factory = LGPIOFactory()
        _servo = AngularServo(
            SERVO_PIN,
            min_angle=0,
            max_angle=180,
            min_pulse_width=0.0005,
            max_pulse_width=0.0024,
            pin_factory=_factory,
        )
        _servo.angle = ANGLE_REST
        sleep(SETTLE_SECONDS)
        _servo.detach()


def rotate():
    """Sweep the servo to the trigger angle and back. Called on each reminder alert."""
    _init()
    _servo.angle = ANGLE_TRIGGER
    sleep(SETTLE_SECONDS)
    _servo.angle = ANGLE_REST
    sleep(SETTLE_SECONDS)
    _servo.detach()
