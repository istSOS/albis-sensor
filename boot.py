import pycom
import machine
import ujson
import time

print("\n\nBooting Albis Sensor")
pycom.heartbeat(False)
# pycom.rgbled(0xff0000)
time.sleep_ms(500)

with open("config.json", 'r') as cf:
    conf = ujson.loads(cf.read())
    if conf['wifi'] is True:
        import wifi
        wifi.connect(conf['config']['wifi'])
        print("Connection done.")

machine.main('main.py')
