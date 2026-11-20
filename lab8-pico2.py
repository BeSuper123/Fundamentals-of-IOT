import math
import network
import time
from machine import Pin
import umqtt.robust as umqtt
from config import WIFI_SSID, WIFI_PASSWORD, HOSTNAME

PORT = 1883
TOPIC = "temp/pico"
TEMPERATURE_THRESHOLD = 25

led = Pin("LED", Pin.OUT)
led.value(0)


def callback(topic, message):
    if topic != TOPIC:
        return

    try:
        temperature = float(message.decode())
        if not math.isfinite(temperature):
            raise ValueError("Temperature must be finite")
    except (ValueError, UnicodeError):
        print("Invalid temperature:", message)
        return

    led.value(1 if temperature >= TEMPERATURE_THRESHOLD else 0)
    print("Received temperature:", temperature, "C; LED:", led.value())


wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(WIFI_SSID, WIFI_PASSWORD)

for attempt in range(30):
    if wlan.isconnected():
        break
    print("Connecting to Wi-Fi...")
    time.sleep(1)
else:
    raise RuntimeError("Wi-Fi connection failed. Check the hotspot and config.py.")

print("Connected to Wi-Fi:", wlan.ifconfig()[0])

mqtt = umqtt.MQTTClient(
    client_id = "subscribe",
    server = HOSTNAME.encode(),
    port = PORT,
    keepalive = 60
)
mqtt.set_callback(callback)
# Preserve the subscription when umqtt.robust reconnects.
mqtt.connect(clean_session=False)
mqtt.subscribe(TOPIC)
print("Subscribed to temp/pico")

last_ping = time.ticks_ms()
try:
    while True:
        mqtt.check_msg()
        if time.ticks_diff(time.ticks_ms(), last_ping) >= 30000:
            mqtt.ping()
            last_ping = time.ticks_ms()
        time.sleep(0.1)
finally:
    led.value(0)
    try:
        mqtt.disconnect()
    except OSError:
        pass
