# Lab 8 MQTT and the Raspberry Pi

## Team members

- TODO: Add each team member's name before submitting.

## How it works

Pico 1 reads its internal temperature sensor once per second and publishes the temperature in Celsius to `temp/pico`. The Raspberry Pi runs the Mosquitto broker, which forwards the messages to Pico 2. Pico 2 converts each message to a number and turns its built-in LED on at 25 degrees Celsius or above, and off below 25. The internal sensor measures chip temperature rather than accurate room temperature.

## Files

- `lab8-pico1.py`: publisher, runs on Pico 1.
- `lab8-pico2.py`: subscriber and LED control, runs on Pico 2.
- `config.example.py`: template for the local `config.py` used by both Picos.
- `mosquitto.conf`: broker configuration, used on the full Raspberry Pi.

The older lab files in this folder are separate exercises and are not needed for Lab 8. Neither Lab 8 program contains HTTP code.

## 1 Set up the Raspberry Pi

Install 64-bit Raspberry Pi OS using Raspberry Pi Imager if needed. Writing an OS image erases the selected SD card, so confirm the device first. Connect the Pi and both Pico W boards to the same hotspot. The hotspot must allow devices to communicate with each other.

Run these commands in the Raspberry Pi terminal:

```sh
sudo apt update
sudo apt dist-upgrade -y
sudo apt install mosquitto mosquitto-clients
```

Copy the supplied `mosquitto.conf` onto the Raspberry Pi. In the directory containing that file, run:

```sh
sudo cp /etc/mosquitto/mosquitto.conf /etc/mosquitto/mosquitto.conf.lab8-backup
sudo cp mosquitto.conf /etc/mosquitto/mosquitto.conf
sudo systemctl enable mosquitto
sudo systemctl restart mosquitto
systemctl status mosquitto
hostname -I
```

Record the Pi's hotspot IPv4 address for `HOSTNAME`. The explicit `listener` line allows connections from the Picos; the brief's three-line example omits it. This configuration allows anonymous, unencrypted MQTT for the isolated lab hotspot only. MQTT itself does not encrypt traffic; production encryption requires TLS.

Reference: https://mosquitto.org/documentation/migrating-to-2-0/

Test the broker in two Raspberry Pi terminals. First:

```sh
mosquitto_sub -h localhost -t temp/pico -v
```

Then in the second:

```sh
mosquitto_pub -h localhost -t temp/pico -m "20"
```

The subscriber should display `temp/pico 20`.

## 2 Prepare both Picos

Use MicroPython on two Wi-Fi capable Pico boards. In Thonny, connect to each board in turn. Connect it to the hotspot, then install the libraries using its MicroPython Shell:

```python
import network
import time
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect("YOUR_HOTSPOT_NAME", "YOUR_HOTSPOT_PASSWORD")
```

Wait for `wlan.isconnected()` to return `True`, then run:

```python
import mip
mip.install("umqtt.simple")
mip.install("umqtt.robust")
```

Alternatively use Thonny's package manager targeting the Pico. Install on both boards, not laptop Python.

Copy `config.example.py` to `config.py`. Fill in the hotspot name, password and Raspberry Pi IPv4 address. Save `config.py` on both Picos. It is excluded from Git to keep the password out of the repository.

Save `lab8-pico2.py` on Pico 2 and run it first. Save `lab8-pico1.py` on Pico 1 and run it. Both must run simultaneously on separate boards. To start automatically, save the appropriate program as `main.py` on each board. Keep the descriptive filenames in the repository.

## 3 Check the behaviour

1. Both boards should print their Wi-Fi IP and broker connection or subscription message.
2. Pico 1 should print one published temperature every second.
3. Pico 2 should print received temperatures and LED states.
4. LED on means temperature >= 25; LED off means temperature < 25.

To test the threshold reliably, stop Pico 1 temporarily so its readings do not overwrite the manual test. Leave Pico 2 running and publish these messages from the Raspberry Pi:

```sh
mosquitto_pub -h localhost -t temp/pico -m "24.9"
mosquitto_pub -h localhost -t temp/pico -m "25"
mosquitto_pub -h localhost -t temp/pico -m "26"
mosquitto_pub -h localhost -t temp/pico -m "20"
```

Observe the LED after each command: off, on, on, off. Restart Pico 1 afterwards for the full temperature demo. An invalid payload such as `hello` should print an error without stopping Pico 2.

If connections fail, check `HOSTNAME`, the shared hotspot, device isolation, and `systemctl status mosquitto`. The broker IP can change after reconnecting. Use `sudo journalctl -u mosquitto -n 30 --no-pager` for broker errors. Automatic broker reconnect does not guarantee recovery after a Wi-Fi outage; reconnect the hotspot and rerun the programs if necessary.

## Submission

Replace the team-name placeholder. Commit the Lab 8 files to your chosen Git repository and submit its link on Brightspace by Friday 13 November 2026. If private, add the lecturer using the email in the brief. The live system also needs an in-person demo.

Hardware setup, MQTT delivery and the physical LED still need verification on the actual devices; local code checks cannot confirm these.
