import pycom
import time
from machine import I2C
from machine import Pin
from machine import ADC
import ujson



class Sensors():

    def __init__(self, conf):
        self.conf = conf

        if conf['board'] == 'shield':
            from onewire import OneWire
            from onewire import DS18X20
            from bme280 import BME280, BME280_I2CADDR
            from bh1750fvi import BH1750FVI

            self.BME280 = BME280
            self.BME280_I2CADDR = BME280_I2CADDR
            self.BH1750FVI = BH1750FVI
            self.DS18X20 = DS18X20

            #i2c = I2C(0, I2C.MASTER, baudrate=10000)
            self.i2c = I2C(
                0,
                pins=(
                    conf['type']['shield']['scl'],
                    conf['type']['shield']['sda']
                )
            )

            # set temperature on Pin 4
            self.ow1 = OneWire(
                Pin(conf['type']['shield']['temp1'])
            )

            # set temperature on Pin 3
            self.ow2 = OneWire(
                Pin(conf['type']['shield']['temp2'])
            )

            time.sleep(2)
            # scan for devices on the bus
            ow1_scan = self.ow1.scan()
            ow2_scan = self.ow2.scan()

            if conf["debug"]:
                print('scan devices ow1:', ow1_scan)
                print('scan devices ow2:', ow2_scan)

            # battery pin
            adc = ADC()
            self.batt = adc.channel(attn=1, pin=conf['type']['shield']['batt'])

        elif conf['board'] == 'shield':
            from pysense import Pysense
            from LIS2HH12 import LIS2HH12
            from SI7006A20 import SI7006A20
            from LTR329ALS01 import LTR329ALS01
            from MPL3115A2 import MPL3115A2, ALTITUDE, PRESSURE
            from onewire import DS18X20
            from onewire import OneWire

            # pysense sensors
            self.py = Pysense()

            # Returns height in meters. Mode may also be set to PRESSURE,
            # returning a value in Pascals
            self.mp = MPL3115A2(py, mode=ALTITUDE)
            self.mpp = MPL3115A2(py, mode=PRESSURE)
            self.si = SI7006A20(py)
            self.lt = LTR329ALS01(py)
            self.li = LIS2HH12(py)

    def get_obs(self, m):

        if self.conf['board'] == 'shield':

            self.i2c.init(I2C.MASTER)

            if self.conf["debug"]:
                print("i2c: ", self.i2c.scan())

            time.sleep(0.5)
            bme_sensor = self.BME280(address=self.BME280_I2CADDR, i2c=self.i2c)
            time.sleep(0.5)
            light_sensor = self.BH1750FVI(self.i2c, addr=self.i2c.scan()[0])

            time.sleep(0.5)
            temp1 = self.DS18X20(self.ow1)
            time.sleep(0.5)
            temp2 = self.DS18X20(self.ow2)
            for i in range(m):
                print("reading values....")
                obs = self.read(bme_sensor, light_sensor, temp1, temp2)
                print(obs)
                print('{}/{}'.format(i+1, m))
            self.i2c.deinit()
            Pin(
                self.conf['type']['shield']['scl'],
                mode=Pin.IN
            )
            Pin(
                self.conf['type']['shield']['sda'],
                mode=Pin.IN
            )
        elif self.conf['pysense']:
            for i in range(m):
                print("reading values....")
                obs = self.read( None, None,
                    temp1, temp2,
                    self.mp, self.mpp,
                    lt
                )
                print(obs)
                print('{}/{}'.format(i+1, m))
        return obs

    def read(
        self,
        bme_sensor=None,
        light_sensor=None,
        temp1=None, temp2=None,
        mp=None, mpp=None,
        lt=None):

        if self.conf['debug']:
            pycom.rgbled(0xffa500)

        obs = {}

        # MPL3115A2 or BME280 temperature
        if bme_sensor:
            obs['internal:temperature'] = bme_sensor.temperature
        else:
            obs['internal:temperature'] = mp.temperature()

        # MPL3115A2 or BME280 pressure in Pa

        if bme_sensor:
            obs['internal:pressure'] = bme_sensor.pressure
        else:
            obs['internal:pressure'] = mpp.pressure()


        # Pysense or BME280 humidity
        if bme_sensor:
            obs['internal:air:humidity'] = bme_sensor.humidity
        else:
            obs['internal:air:humidity'] = si.humidity()

        # Sensor light
        # Sensor temperature

        if light_sensor:
            obs['internal:lux'] = light_sensor.read()
        else:
            light = lt.light()
            obs['internal:lux:blue'] = light[0]
            obs['internal:lux:red'] = light[1]

        # Reading from external sensors
        obs['external:water:temperature'] = temp1.read_temp_async()

        # while (obs['external:water:temperature'] == 85):
        #    obs['external:water:temperature'] = temp1.read_temp_async()

        time.sleep(1)
        temp1.start_conversion()

        obs['external:wall:temperature'] = temp2.read_temp_async()
        # while (obs['external:wall:temperature'] == 85):
        #    obs['external:wall:temperature'] = temp1.read_temp_async()

        time.sleep(1)
        temp2.start_conversion()

        # battery voltage
        # obs['sensor:battery'] = self.py.read_battery_voltage()

        val = self.batt()                 # read an analog value
        obs['sensor:battery'] = val/1000

        return obs
