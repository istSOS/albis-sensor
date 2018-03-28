import pycom
import time
from machine import Pin
from machine import I2C
import ujson
from lib.bme280 import *
from bh1750fvi import *
from lib.onewire import DS18X20
from lib.onewire import OneWire

#i2c = I2C(0, I2C.MASTER, baudrate=10000)
i2c = I2C(0, pins=('P9','P10'))

# set temperature on Pin 4
ow1 = OneWire(Pin('P3'))

# set temperature on Pin 3
ow2 = OneWire(Pin('P8'))

time.sleep(2)
# scan for devices on the bus
ow1_scan = ow1.scan()
ow2_scan = ow2.scan()
print('scan devices ow1:', ow1_scan)
print('scan devices ow2:', ow2_scan)


def get_obs(m):
    # MAKE DATA WARMING READINGS

    i2c.init(I2C.MASTER)

    print("i2c: ",i2c.scan())
    time.sleep(0.5)
    bme_sensor = BME280(address=BME280_I2CADDR, i2c=i2c)
    time.sleep(0.5)
    light_sensor = BH1750FVI(i2c, addr=i2c.scan()[0])
    time.sleep(0.5)
    temp1 = DS18X20(ow1)
    time.sleep(0.5)
    temp2 = DS18X20(ow2)
    for i in range(m):
        print("reading values....")
        obs = read(bme_sensor, light_sensor, temp1, temp2)
        print(obs)
        print('{}/{}'.format(i+1, m))
    i2c.deinit()
    Pin('P9', mode=Pin.IN)
    Pin('P10', mode=Pin.IN)
    return obs

def read(bme_sensor, light_sensor, temp1, temp2):
    with open("config.json", 'r') as cf:
        conf = ujson.loads(cf.read())
        if conf['debug']:
            pycom.rgbled(0xffa500)

    obs = {}

    # MPL3115A2 temperature
    obs['internal:temperature'] = bme_sensor.temperature

    # MPL3115A2 pressure in Pa
    obs['internal:pressure'] = bme_sensor.pressure

    # Sensor temperature
    obs['internal:air:humidity'] = bme_sensor.humidity

    # Sensor light
    obs['internal:lux'] = light_sensor.read()

    # Reading from external sensors
    obs['external:water:temperature'] = temp1.read_temp_async()
    temp1.start_conversion()

    obs['external:wall:temperature'] = temp2.read_temp_async()
    temp2.start_conversion()

    return obs
