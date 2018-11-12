import pycom
import machine
import ujson
import time
from machine import SD

pycom.heartbeat(False)

if pycom.heartbeat_on_boot():
    pycom.heartbeat_on_boot(False)

if pycom.wifi_on_boot():  # get the wifi on boot flag
    pycom.wifi_on_boot(False)   # disable WiFi on boot

print("\n\nBooting Albis Sensor")

with open("config.json", 'r') as cf:
    conf = ujson.loads(cf.read())
    if machine.wake_reason()[0] == 0:
        pycom.nvs_set('loraSaved', 0) # reset for next test
        import binascii
        from network import LoRa
        print("MAC ID: {}".format(binascii.hexlify(LoRa().mac())))
        from lib import wifi
        pycom.rgbled(0x204c70)
        wifi.connect(conf)
        pycom.heartbeat(False)
        pycom.rgbled(0x000000)

    time.sleep_ms(500)

machine.main('main.py')
