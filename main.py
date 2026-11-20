import time
import math
import network
import machine
import ubinascii
import umqtt.robust as umqtt
import config
from temperature_upb2 import TimeMessage, TemperatureMessage


def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(config.WIFI_SSID, config.WIFI_PASSWORD)
    for attempt in range(30):
        if wlan.isconnected():
            print("Connected to Wi-Fi:", wlan.ifconfig()[0])
            return wlan
        time.sleep(1)
    raise RuntimeError("Wi-Fi connection failed. Check config.py.")


def encode_temperature(temperature):
    now = time.localtime()
    clock = TimeMessage()
    clock.hour = now[3]
    clock.minute = now[4]
    clock.second = now[5]
    message = TemperatureMessage()
    message.publisher_id = config.PUBLISHER_ID
    message.temperature = temperature
    message.time = clock.serialize()
    return message.serialize()


def receive_temperature(topic, payload):
    if topic != config.TOPIC:
        return
    try:
        message = TemperatureMessage()
        if not message.parse(payload):
            raise ValueError("Missing required fields")
        temperature = message.temperature.value()
        publisher_id = message.publisher_id.value()
        clock = message.time.value()
        hour = clock.hour.value()
        minute = clock.minute.value()
        second = clock.second.value()
        if (not publisher_id or not math.isfinite(temperature)
                or not 0 <= hour < 24 or not 0 <= minute < 60
                or not 0 <= second < 60):
            raise ValueError("Invalid temperature message")
        led.value(temperature >= config.THRESHOLD)
        print("{}: {:.2f} C at {:02d}:{:02d}:{:02d}".format(
            publisher_id, temperature, hour, minute, second))
    except Exception as error:
        print("Ignored invalid message:", error)


def main():
    global led
    if config.ROLE not in ("publisher", "subscriber"):
        raise ValueError("ROLE must be publisher or subscriber")
    if not 1 <= len(config.PUBLISHER_ID.encode()) <= 64:
        raise ValueError("PUBLISHER_ID must be 1 to 64 UTF-8 bytes")
    if config.PUBLISH_INTERVAL <= 0:
        raise ValueError("PUBLISH_INTERVAL must be positive")
    led = machine.Pin(config.LED_PIN, machine.Pin.OUT)
    connect_wifi()
    if config.ROLE == "publisher":
        import ntptime
        ntptime.settime()
        print("Clock synchronized (UTC)")
    client_id = b"lab9-" + ubinascii.hexlify(machine.unique_id())
    mqtt = umqtt.MQTTClient(client_id=client_id,
                            server=config.HOSTNAME, port=config.PORT,
                            keepalive=60)
    mqtt.set_callback(receive_temperature)
    mqtt.connect()
    print("Connected as", config.ROLE)
    try:
        if config.ROLE == "publisher":
            sensor = machine.ADC(4)
            while True:
                reading = sensor.read_u16() * (3.3 / 65535)
                temperature = 27 - (reading - 0.706) / 0.001721
                mqtt.publish(config.TOPIC, encode_temperature(temperature))
                print("Published:", round(temperature, 2), "C")
                time.sleep(config.PUBLISH_INTERVAL)
        else:
            mqtt.subscribe(config.TOPIC)
            last_ping = time.ticks_ms()
            while True:
                mqtt.check_msg()
                if time.ticks_diff(time.ticks_ms(), last_ping) >= 30000:
                    mqtt.ping()
                    last_ping = time.ticks_ms()
                time.sleep_ms(100)
    finally:
        led.off()
        try:
            mqtt.disconnect()
        except OSError:
            pass


if __name__ == "__main__":
    main()
