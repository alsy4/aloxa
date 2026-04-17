"""Test script for TowerPro SG90 servo motor on GPIO 23 (Pin 16)."""

from gpiozero import Servo
from gpiozero.pins.lgpio import LGPIOFactory
from time import sleep

SERVO1_GPIO = 17
SERVO2_GPIO = 27

factory = LGPIOFactory()
servo1 = Servo(SERVO1_GPIO, pin_factory=factory)
servo2 = Servo(SERVO2_GPIO, pin_factory=factory)


# try:
#     print("Moving to MIN position (-90°)")
#     servo.min()
#     sleep(1)

#     print("Moving to MAX position (+90°)")
#     servo.max()
#     sleep(1)

#     print("Sweeping back to MID")
#     servo.mid()
#     sleep(1)

#     print("\nDone! Servo test passed.")
# except KeyboardInterrupt:
#     print("\nTest interrupted.")
# finally:
#     servo.close()

try:
        while True:
            print("Servo1: MIN, Servo2: MIN")
            servo1.min()
            servo2.max()
            sleep(1)
            print("Servo1: MAX, Servo2: MAX")
            servo1.max()
            servo2.min()
            sleep(1)
except KeyboardInterrupt:
    print("\nTest interrupted.")
finally:
    servo1.close()
    servo2.close()