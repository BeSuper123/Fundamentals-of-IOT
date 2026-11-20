from network import WLAN

wifi = WLAN(WLAN.IF_STA)
wifi.active(True)

for (ssid, bssid, channel, rssi, security, hidden) in wifi.scan():
    ssid = ssid.decode('utf-8')
    print(f"found network '{ssid}'")