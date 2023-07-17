import pycom
import time
from machine import I2C
from machine import Pin
from machine import ADC
from machine import RTC

# sensor libs
from onewire import OneWire
from onewire import DS18X20
from bme280 import BME280, BME280_I2CADDR
from bh1750fvi import BH1750FVI
from DS3231 import DS3231


class Sensors():

    def __init__(self, conf):
        self.conf = conf
        self.debug = self.conf['debug']

        if self.conf['debug'] is True:
            print("Shield")

        self.BME280 = BME280
        self.BME280_I2CADDR = BME280_I2CADDR
        self.BH1750FVI = BH1750FVI
        self.DS18X20 = DS18X20

        self.i2c = I2C(1)
        self.i2c = I2C(1, I2C.MASTER)

        self.i2c = I2C(
            1,
            pins=(
                conf['pins']['sda'],
                conf['pins']['scl']
            )
        )

        # set temperature on Pin 4
        self.ow1 = OneWire(
            Pin(conf['pins']['temp1'])
        )

        time.sleep(1)
        # scan for devices on the bus
        ow1_scan = self.ow1.scan()

        # set temperature on Pin 3
        self.ow2 = OneWire(
            Pin(conf['pins']['temp2'])
        )

        time.sleep(1)
        # scan for devices on the bus
        ow2_scan = self.ow2.scan()

        if conf["debug"]:
            print('scan devices ow1:', ow1_scan)
            print('scan devices ow2:', ow2_scan)

        # battery pin
        adc = ADC()
        self.batt = adc.channel(attn=1, pin=conf['pins']['batt'])

    def get_obs(self, m):

        obs = {}

        # temperature sensors

        time.sleep(0.5)
        temp1 = self.DS18X20(self.ow1)
        time.sleep(0.5)
        temp2 = self.DS18X20(self.ow2)

        # init i2c
        self.bme = False
        self.bh = False
        self.ds = False

        self.i2c.init(
            I2C.MASTER,
            baudrate=100000,
            pins=(
                self.conf['pins']['sda'],
                self.conf['pins']['scl']
            )
        )

        i2c_scanned = self.i2c.scan()
        print("I2C --> ", i2c_scanned)
        if len(i2c_scanned)==0:
            if self.debug:
                pycom.rgbled(0x4c044c)
                time.sleep(1.5)
                pycom.rgbled(0x7f0000)
                time.sleep(1.5)
                print('I2C --> No device detected')
        else:
            for addr in i2c_scanned:
                if addr == 35:
                    self.bh = True
                    print('I2C --> BME is not detected.')
                    if self.debug:
                        pycom.rgbled(0x4c044c)
                        time.sleep(1.5)
                elif addr == 118:
                    self.bme = True
                    if self.debug:
                        pycom.rgbled(0x7f0000)
                        time.sleep(1.5)
                elif addr == 104:
                    self.ds = True
                    if self.debug:
                        pycom.rgbled(0x7f0000)
                        time.sleep(1.5)
            

        if self.bme:
            bme_sensor = self.BME280(address=self.BME280_I2CADDR, i2c=self.i2c)
            print('I2C --> BME set')
        else:
            print('I2C --> BME is not detected.')
        time.sleep(0.5)
        if self.bh:
            light_sensor = self.BH1750FVI(self.i2c, addr=self.i2c.scan()[0])
            print('I2C --> BH1750 set')
        else:
            print('I2C --> BH1750 is not detected.')
        if self.ds:
            ds3231 = DS3231(self.i2c)
            # ds3231.save_time()
            # ds3231.get_time(set_rtc=True)
            # print("DS3231 time -->")
            # print(ds3231.get_time())
            print('I2C --> DS3231 set')
        else:
            print('I2C --> DS3231 is not detected.')

        if self.ds:
            time_now = ds3231.get_time()
        else:
            rtc = RTC()
            time_now = rtc.now()
        time_ok = False
        for i in range(m):
            print("reading values....")
            
            obs = {
                'internal:temperature': round(float(bme_sensor.temperature), 2) if self.bme else -9999,
                'internal:pressure': round(float(bme_sensor.pressure), 2) if self.bme else -9999,
                'internal:air:humidity': round(float(bme_sensor.humidity), 2) if self.bme else -9999,
                'internal:lux': round(light_sensor.read(), 2) if self.bh else -9999
            }

            rest = time_now[4]%self.conf['frequency']
            timeout = 1
            if not time_ok:
                print('waiting', end='.')
                time_ok = True
                while rest!=0:
                    if timeout>25:
                        print('')
                        break
                    if self.ds:
                        time_now = ds3231.get_time()
                    else:
                        rtc = RTC()
                        time_now = rtc.now()
                    rest = time_now[4]%self.conf['frequency']
                    time.sleep(1)
                    timeout+=1
                    print('.', end='.')
            rounded_minute = time_now[4]-(time_now[4]%self.conf['frequency'])

            print("Rounded_minute {}".format(rounded_minute))
            print("Not rounded_minute {}".format(time_now[4]))
            obs['Time'] = "{}-{}-{}T{}:{}:00+00:00".format(
                time_now[0],
                time_now[1] if len(str(time_now[1])) > 1 else "0{}".format(time_now[1]),
                time_now[2] if len(str(time_now[2])) > 1 else "0{}".format(time_now[2]),
                time_now[3] if len(str(time_now[3])) > 1 else "0{}".format(time_now[3]),
                rounded_minute if len(str(rounded_minute)) > 1 else "0{}".format(rounded_minute)
            )

            obs['external:water:temperature'] = temp1.read_temp_async()
            if obs['external:water:temperature'] is None:
                obs['external:water:temperature'] = -9999
                if self.debug:
                    pycom.rgbled(0xFFFF00)
            else:
                obs['external:water:temperature'] = round(obs['external:water:temperature'], 2)
            time.sleep(1)
            temp1.start_conversion()

            obs['external:wall:temperature'] = temp2.read_temp_async()
            if obs['external:wall:temperature'] is None:
                obs['external:wall:temperature'] = -9999
                if self.debug:
                    pycom.rgbled(0xFFFF00)
                    time.sleep(0.2)
                    pycom.rgbled(0x000000)
            else:
                obs['external:wall:temperature'] = round(obs['external:wall:temperature'], 2)
            time.sleep(1)
            temp2.start_conversion()

            val = self.batt()  # read an analog value
            obs['sensor:battery'] = round(val/940, 2)

        self.i2c.deinit()
        Pin(
            self.conf['pins']['scl'],
            mode=Pin.IN
        )
        Pin(
            self.conf['pins']['sda'],
            mode=Pin.IN
        )

        return obs
