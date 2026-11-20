import time
import math
import network
import machine
import ubinascii
import umqtt.robust as umqtt
import config
import lcd_config
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


pending_temperature = None


def receive_temperature(topic, payload):
    global pending_temperature
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
        pending_temperature = temperature
        print("{}: {:.2f} C at {:02d}:{:02d}:{:02d}".format(
            publisher_id, temperature, hour, minute, second))
    except Exception as error:
        print("Ignored invalid message:", error)


def temperature_text(temperature):
    if temperature < 16:
        description = "too cold"
    elif temperature > 25:
        description = "too hot"
    else:
        description = "just right"
    return "The temperature is {:.1f} degrees. This is {}.".format(
        temperature, description)


def scroll_temperature(lcd, temperature):
    text = temperature_text(temperature)
    print("Scrolling (MQTT paused):", text)
    lcd.clear()
    for offset in range(0, len(text), 16):
        lcd.setCursor(0, 0)
        lcd.print(text[offset:offset + 16].ljust(16))
        time.sleep(5)
    print("Scrolling finished; resuming MQTT")


def main():
    global pending_temperature
    if config.ROLE not in ("publisher", "subscriber"):
        raise ValueError("ROLE must be publisher or subscriber")
    if not 1 <= len(config.PUBLISHER_ID.encode()) <= 64:
        raise ValueError("PUBLISHER_ID must be 1 to 64 UTF-8 bytes")
    if config.PUBLISH_INTERVAL <= 0:
        raise ValueError("PUBLISH_INTERVAL must be positive")
    connect_wifi()
    if config.ROLE == "publisher":
        import ntptime
        ntptime.settime()
        print("Clock synchronized (UTC)")
    client_id = b"lab10-" + ubinascii.hexlify(machine.unique_id())
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
            from lcd1602 import LCD1602
            i2c = machine.I2C(lcd_config.LCD_I2C_ID,
                              sda=machine.Pin(lcd_config.LCD_SDA_PIN),
                              scl=machine.Pin(lcd_config.LCD_SCL_PIN), freq=100000)
            if lcd_config.LCD_ADDRESS not in i2c.scan():
                raise RuntimeError("LCD not found. Check wiring and LCD_ADDRESS.")
            lcd = LCD1602(i2c, 2, 0, lcd_addr=lcd_config.LCD_ADDRESS)
            lcd.print("Waiting for temp")
            mqtt.subscribe(config.TOPIC)
            last_ping = time.ticks_ms()
            while True:
                mqtt.check_msg()
                if pending_temperature is not None:
                    temperature = pending_temperature
                    pending_temperature = None
                    mqtt.disconnect()
                    scroll_temperature(lcd, temperature)
                    mqtt.connect(clean_session=True)
                    mqtt.subscribe(config.TOPIC)
                    last_ping = time.ticks_ms()
                if time.ticks_diff(time.ticks_ms(), last_ping) >= 30000:
                    mqtt.ping()
                    last_ping = time.ticks_ms()
                time.sleep_ms(100)
    finally:
        try:
            mqtt.disconnect()
        except OSError:
            pass


if __name__ == "__main__":
    main()
