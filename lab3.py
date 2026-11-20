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
    client, client_address = server.accept()
    client.settimeout(5)
    stream = client.makefile("rb")
    try:
        method, path, version = stream.readline().decode().split()
        length = 0
        while True:
            line = stream.readline()
            if line == b"\r\n":
                break
            if not line:
                raise ValueError("Incomplete headers")
            name, value = line.decode().split(":", 1)
            if name.strip().lower() == "content-length":
                length = int(value)
        status = "200 OK"
        content_type = "text/plain"
        if method == "GET" and path.startswith("/led?brightness="):
            brightness = float(path[len("/led?brightness="):])
            if not 0 <= brightness <= 1:
                raise ValueError("Invalid brightness")
            led.duty_u16(int(brightness * 55000))
            message = "Brightness set to " + str(round(brightness * 100)) + "%"
        elif method == "POST" and path == "/rest/led":
            if length <= 0:
                raise ValueError("Missing JSON body")
            body = b""
            while len(body) < length:
                chunk = stream.read(length - len(body))
                if not chunk:
                    raise ValueError("Incomplete body")
                body += chunk
            data = json.loads(body.decode())
            print('The JSON object is', data)
            if not isinstance(data, dict):
                raise ValueError("Expected a JSON object")
            if "brightness" not in data or "request" not in data:
                raise ValueError("Missing keys")
            if data["request"] is False:
                status = "204 No Content"
                message = ""
            elif data["request"] is True:
                brightness = data["brightness"]
                if type(brightness) not in (int, float):
                    raise ValueError("Brightness must be a number")
                if not 0 <= brightness <= 1:
                    raise ValueError("Invalid brightness")
                led.duty_u16(int(brightness * 55000))
                message = json.dumps({"brightness": brightness, "request": False})
                content_type = "application/json"
            else:
                raise ValueError("request must be true or false")
        else:
            raise ValueError("Invalid route")
    except Exception as error:
        print(error)
        status = "404 Not Found"
        content_type = "text/plain"
        message = "Invalid request"
    try:
        response = (
            "HTTP/1.1 " + status + "\r\n"
            "Content-Type: " + content_type + "\r\n"
            "Content-Length: " + str(len(message.encode())) + "\r\n"
            "Connection: close\r\n\r\n" + message
        )
        client.sendall(response.encode())
    except OSError:
        print("Connection closed")
    finally:
        stream.close()
        client.close()