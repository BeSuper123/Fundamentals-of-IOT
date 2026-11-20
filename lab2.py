import network
import socket
import time
import json
from machine import Pin, PWM

ssid = "Blessing’s iPhone"
password = "abcdefgh"
led = PWM(Pin(15))
led.freq(1000)
led.duty_u16(0)
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(ssid, password)

print("Connecting to Wi-Fi...")

while not wlan.isconnected():
    print("Waiting for connection...")
    time.sleep(1)

ip_address = wlan.ifconfig()[0]
print("Connected!")
print("IP address:", ip_address)

address = socket.getaddrinfo("0.0.0.0", 80)[0][-1]
server = socket.socket()
server.bind(address)
server.listen(1)

print("Server running")
print("http://" + ip_address + "/led?brightness=0.5")

while True:
    client = None
    try:
        client, client_address = server.accept()
        request = client.recv(1024).decode()
        print(request)
        valid_request = False
        if request.startswith("GET "):
            first_line = request.split("\r\n")[0]
            prefix = "GET /led?brightness="
            if first_line.startswith(prefix):
                end = first_line.find(" HTTP/")
                if end != -1:
                    brightness_text = first_line[len(prefix):end]
                    try:
                        brightness = float(brightness_text)
                        if 0 <= brightness <= 1:
                            pwm_value = int(brightness * 55000)
                            led.duty_u16(pwm_value)
                            valid_request = True
                            message = ("Brightness set to " + str(round(brightness * 100)) + "%")
                    except ValueError:
                        pass

        if valid_request:
            response = ("HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nConnection: close\r\n\r\n" + message)
        else:
            response = ("HTTP/1.1 404 Not Found\r\nContent-Type: text/plain\r\nConnection: close\r\n\r\n404 - Invalid request")

        client.sendall(response.encode())

    except Exception as error:
        print("Error:", error)

    finally:
        if client is not None:
            client.close()