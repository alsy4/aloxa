from gpiozero import LED
from time import sleep

led_red = LED(5)
led_green = LED(6)

try:
    while True:
        led_red.on()
        led_green.on()
        sleep(0.5)
        led_red.off()
        led_green.off()
        sleep(0.5)
except KeyboardInterrupt:
    led_red.off()
    led_green.off()

