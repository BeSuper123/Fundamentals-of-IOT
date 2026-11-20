import network
import socket
import time
import json
from machine import ADC
import cryptolib

key = b"1234567890123456"
iv = b"abcdefghijklmnop"
ssid = "Blessing’s iPhone"
password = "abcdefgh"
server_ip = "172.20.10.3"
server_port = 5000
temp_sensor = ADC(4)
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(ssid, password)
print("Connecting to Wi-Fi...")

while not wlan.isconnected():
    time.sleep(1)

print("Connected!")
print("IP address:", wlan.ifconfig()[0])

def read_temp():
    value = temp_sensor.read_u16()
    voltage = value * (3.3 / 65536)
    temperature = 27 - (voltage - 0.706) / 0.001721
    return temperature

while True:
    try:
        temperature = read_temp()
        message = json.dumps({"temperature": round(temperature, 2)})
        data = message.encode()
        padding = 16 - len(data) % 16
        data += bytes([padding]) * padding
        iv = bytes([time.ticks_us() >> (i % 4 * 8) & 255 for i in range(16)])
        cipher = cryptolib.aes(key, 2, iv)
        encrypted = cipher.encrypt(data)
        print('ciphertext', encrypted)
        client = socket.socket()
        try:
            client.connect((server_ip, server_port))
            client.sendall(iv + encrypted)
        finally:
            client.close()

        print("Temperature:", temperature)
        print("Encrypted data sent")
    except Exception as error:
        print("Error:", error)

    time.sleep(2)