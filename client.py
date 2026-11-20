import requests

url = "http://172.20.10.10/rest/led"
data = {"brightness": 0.2, "request": True}
response = requests.post(url, json=data, timeout=10)
print("Status:", response.status_code)
print("Reply:", response.text)
response.close()