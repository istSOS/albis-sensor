import pycom
import time
from machine import Pin
# from machine import RTC
# from machine import deepsleep
from pysense import Pysense
from LIS2HH12 import LIS2HH12
from SI7006A20 import SI7006A20
from LTR329ALS01 import LTR329ALS01
from MPL3115A2 import MPL3115A2, ALTITUDE, PRESSURE
from lib.onewire import DS18X20
from lib.onewire import OneWire

# pysense sensors
py = Pysense()

# Returns height in meters. Mode may also be set to PRESSURE,
# returning a value in Pascals
mp = MPL3115A2(py, mode=ALTITUDE)
mpp = MPL3115A2(py, mode=PRESSURE)
si = SI7006A20(py)
lt = LTR329ALS01(py)
li = LIS2HH12(py)

# set temperature on Pin 4
ow1 = OneWire(Pin('P4'))

# scan for devices on the bus
print('scan devices:', ow1.scan())

# set temperature on Pin 8
ow2 = OneWire(Pin('P8'))
print('scan devices:', ow2.scan())

time.sleep(1)
temp1 = DS18X20(ow1)

time.sleep(1)
temp2 = DS18X20(ow2)


def read():
    # pycom.rgbled(0xffa500)

    obs = {
        "": None,
        "": None
    }
    # MPL3115A2 temperature
    obs['internal:temperature'] = mp.temperature()

    # MPL3115A2 altitude
    obs['internal:altitude'] = mp.altitude()

    # MPL3115A2 pressure in Pa
    obs['internal:pressure'] = mpp.pressure()

    # MPL3115A2 temperature
    obs['internal:air:temperature'] = si.temperature()

    # Sensor temperature
    obs['internal:air:humidity'] = si.humidity()

    # Sensor temperature
    light = lt.light()
    obs['internal:lux:blue'] = light[0]
    obs['internal:lux:red'] = light[1]

    # Sensor acceleration
    obs['sensor:acceleration'] = li.acceleration()

    # Sensor roll
    obs['sensor:roll'] = li.roll()

    # Sensor pitch
    obs['sensor:pitch'] = li.pitch()

    # Sensor pitch
    obs['sensor:battery'] = py.read_battery_voltage()

    # Reading from external sensors

    obs['external:water:temperature'] = temp1.read_temp_async()
    time.sleep(1)
    temp1.start_conversion()
    time.sleep(1)

    obs['external:wall:temperature'] = temp2.read_temp_async()
    time.sleep(1)
    temp2.start_conversion()
    time.sleep(1)

    return obs
