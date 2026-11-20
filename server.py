import socket
import json
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

key = b"1234567890123456"
server = socket.socket()
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind(("0.0.0.0", 5000))
server.listen(1)
print("Waiting for Pico...")

while True:
    connection, address = server.accept()
    try:
        encrypted_data = b""
        while True:
            data = connection.recv(1024)
            if not data:
                break

            encrypted_data += data
        iv = encrypted_data[:16]
        ciphertext = encrypted_data[16:]
        cipher = AES.new(key, AES.MODE_CBC, iv)
        decrypted = unpad(cipher.decrypt(ciphertext), 16)
        message = json.loads(decrypted.decode())
        print("Received from:", address)
        print("Temperature:", message["temperature"])
    except Exception as error:
        print("Error:", error)
    finally:
        connection.close()