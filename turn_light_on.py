from machine import Pin, ADC, PWM
import time

led = PWM(Pin(16))
led.freq(1000)
adc = ADC(0)

while True:
    potentiometer_value = adc.read_u16()
    brightness = potentiometer_value / 65535
    pwm_value = int(brightness * 55000)
    led.duty_u16(pwm_value)
    print("Potentiometer:", potentiometer_value)
    print("Brightness:", round(brightness, 2))
    time.sleep(0.1)