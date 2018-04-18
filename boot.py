import pycom
import machine
import ujson
import time

print("\n\nBooting Albis Sensor")

if pycom.wifi_on_boot():  # get the wifi on boot flag
    pycom.wifi_on_boot(False)   # disable WiFi on boot

with open("config.json", 'r') as cf:
    conf = ujson.loads(cf.read())
    pycom.heartbeat(False)
    if conf['debug']:
        pycom.rgbled(0xff0000)
    time.sleep_ms(500)
    if conf['wifi'] is True:
        import wifi
        wifi.connect(conf)
        print("Connection done.")

machine.main('main.py')
