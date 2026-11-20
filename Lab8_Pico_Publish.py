import network
import time
from machine import ADC
import umqtt.robust as umqtt
from config import WIFI_SSID, WIFI_PASSWORD, HOSTNAME

PORT = 1883
TOPIC = b"temp/pico"

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
    client_id = b"publish",
    server = HOSTNAME.encode(),
    port = PORT,
    keepalive = 60
)
mqtt.connect()
print("Connected to MQTT broker")

sensor = ADC(4)
conversion_factor = 3.3 / 65535

try:
    while True:
        # Convert the internal sensor voltage to degrees Celsius.
        reading = sensor.read_u16() * conversion_factor
        temp = 27 - (reading - 0.706) / 0.001721
        mqtt.publish(TOPIC, str(temp).encode())
        print("Published temperature:", round(temp, 2), "C")
        time.sleep(5)
finally:
    try:
        mqtt.disconnect()
    except OSError:
        pass
