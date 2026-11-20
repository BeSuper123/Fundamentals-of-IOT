# IoT Fundamentals Lab 9

C23387203 - Daniel  
C23342083 - Blessing  
C23347781 - Matous

Adapted from https://github.com/BeSuper123/IoT_Fundamentals_Lab8.
One MicroPython program runs as a temperature publisher or subscriber.
The proto2 message carries publisher ID, temperature in Celsius and UTC time.
The subscriber switches the GPIO 16 LED on at 25 C or above, as in Lab 8.
The Pico ADC measures chip temperature, not a calibrated room temperature.

## Quick deployment in Thonny

1. Use the existing MicroPython Pico W setup and working Raspberry Pi Mosquitto broker from Lab 8. Both Picos and the broker must be reachable on the same network. Check the broker's current address with `hostname -I` in the Raspberry Pi terminal.
2. Copy `config.example.py` to `config.py` on your computer. Fill in Wi-Fi details and the broker IP. Keep this file private; `.gitignore` excludes it.
3. First Pico: set `ROLE = "publisher"`, `PUBLISHER_ID = "pico1"`.
4. Second Pico: set `ROLE = "subscriber"`, `PUBLISHER_ID = "pico2"`.
5. In Thonny, save `main.py`, `temperature_upb2.py`, `uprotobuf.py` and that Pico's `config.py` onto each Pico. Retain the existing `umqtt/simple.py` and `umqtt/robust.py` under `/lib/umqtt/` from Lab 8. Stock Pico W MicroPython also needs `ntptime` available.
6. Start the subscriber first, then the publisher. The publisher needs internet/NTP access to set UTC time. If NTP fails it stops instead of sending a false timestamp. Fix internet access and rerun.

The `.proto` file and compiler tools stay on the computer, not the Pico.
Both devices must use exactly the same topic: `temp/pico/protobuf`.
Do not run the Lab 8 text subscriber on this topic: protobuf payloads are binary.
Each Pico has a unique MQTT client ID based on its hardware ID.

## What the code does

`ROLE` chooses the loop. The publisher reads ADC(4), converts voltage to Celsius,
fills a protobuf message and publishes every five seconds. The subscriber parses
the binary payload and reads the generated fields using `.value()`, prints the
publisher/time/temperature and updates the LED. Invalid messages are ignored.
The clock is UTC, not local Irish summer time.

## Library/compiler compatibility

Bundled `uprotobuf.py` is unmodified jazzycamel/micropython-uprotobuf,
upstream blob `61648fc6fa2bdb685eaf44933ff8e62e175494c2`.
See https://github.com/jazzycamel/micropython-uprotobuf and UPROTOBUF-LICENSE.txt.
`tools/uprotobuf_plugin.py` is the original compiler plugin, blob
`9940a669d6d431879cbcad43171f55d1009d4224`.

The generated file is included, so compiling is unnecessary for deployment.
To regenerate on your computer from this folder:

```text
python -m pip install grpcio-tools protobuf
python tools/generate.py
```

The helper uses protoc's descriptor output and passes it into the actual upstream
plugin. This avoids Windows executable-plugin wrapper problems. No custom runtime
or replacement generator is used.

Important quirks: `message Temperature` generates `TemperatureMessage`;
the package must be `protobuf` for this runtime's nested-type registry.
Assign `message.time = clock.serialize()` because the runtime expects bytes for
nested message assignment. Read it back with `message.time.value()`.
Keep publisher IDs at most 64 UTF-8 bytes: the legacy library has limited
length encoding. This is a classroom implementation, not a general-purpose parser.

## Testing

Completed on the computer: generation using the original plugin, Python syntax,
and bidirectional decoding with Google's protobuf implementation for -12.5, 0,
24.99, 25 and 35.5 C, including nested time and publisher ID.
Live Wi-Fi, MQTT, NTP and physical LED operation still require the two Picos.

1. Confirm both consoles show a connection. Subscriber should print `pico1`, a temperature and the UTC time every five seconds.
2. In the publisher's Thonny shell after stopping main.py, run the following (subscriber keeps running):

```python
import main
import config
import umqtt.robust as umqtt
client = umqtt.MQTTClient(b"lab9-manual-test", config.HOSTNAME, port=config.PORT)
client.connect()
client.publish(config.TOPIC, main.encode_temperature(24.0))
# Check LED is off before sending the next message.
client.publish(config.TOPIC, main.encode_temperature(26.0))
# Check LED is on.
client.publish(config.TOPIC, b"invalid")
client.disconnect()
```

3. Verify LED off below 25 C and on at/above 25 C; invalid payload should be ignored without stopping the subscriber. Restart main.py afterward.
4. Swap ROLE on the two Picos and rerun to demonstrate the shared codebase.

For `ECONNRESET` or connection refused, check Mosquitto is listening for LAN
connections and restart it in the Raspberry Pi Linux terminal, not Thonny's `>>>`.
Reuse the working Lab 8 broker configuration. Port 1883 sends plaintext: use this
on the trusted lab network and do not expose the broker to the internet.
Network loss may require restarting the program; automatic Wi-Fi recovery is not implemented.

## Repository/submission

Keep Lab 8 unchanged. This folder is prepared for a separate `IoT_Fundamentals_Lab9`
repository. Only add these files, never the old credential-containing config.
No GitHub repository has been created or uploaded by this package.
The original Lab 9 handout was unavailable; check its exact schema, evidence and
submission requirements before submitting. Requirements here come from the prior chat.
