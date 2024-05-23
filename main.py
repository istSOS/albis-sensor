# Copyright (C) 2024 Daniele Strigaro IST-SUPSI (www.supsi.ch/ist)
#
# This file is part of Albis.
#
# Albis is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Albis is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Albis.  If not, see <https://www.gnu.org/licenses/>.

import time
import pycom
import os
from machine import deepsleep, Pin, ADC, pin_sleep_wakeup
from machine import WAKEUP_ALL_LOW, RTC, I2C, SD
from lib.onewire import OneWire, DS18X20
from lib.bme280 import BME280, BME280_I2CADDR
from lib.bh1750fvi import BH1750FVI
from lib.ds3231 import DS3231, EVERY_HOUR, EVERY_MINUTE
from settings import *


def read_analog_voltage(pin):
    adc = ADC()
    adc.init(bits=12)
    if pin == "P13":
        apin = adc.channel(pin=pin, attn=ADC.ATTN_2_5DB)
        voltage = apin.voltage()
    else:
        # humidity at 6DB
        apin = adc.channel(pin=pin, attn=ADC.ATTN_6DB)
        voltage = apin.voltage()
    return voltage


# # Turn-on switch to power external modules
# Pin("P11", mode=Pin.OUT, value=0, pull=None)
print("\n********")
print("* Main *")
print("********")

rtc = RTC()
###################
# MAGNETIC WAKE-UP
# SET WAKE UP PIN
wake1 = Pin("P9", mode=Pin.IN)
pin_sleep_wakeup([wake1], WAKEUP_ALL_LOW)
# ###################
# # DS3231 WAKE-UP
# # SET WAKE UP PIN
# wake2 = Pin("P9", mode=Pin.IN)
# machine.pin_sleep_wakeup([wake2], WAKEUP_ALL_LOW)
print("> Check sensors")
##########
# OneWire
# DS18B20 data line connected to pin P3
read_temp = False
ow = OneWire(Pin('P3'))
ow.reset()
time.sleep(0.5)
ow_scan = ow.scan()
time.sleep(0.5)
# print(ow_scan)
if len(ow_scan) >= 1:
    print("\t> DS18b20 - OK")
    read_temp = True
    temp = DS18X20(ow)
else:
    print("\t> DS18b20 - NOT detected")
#########################
# BME280, BH1750, DS3231
# Connected to i2c
# init i2c: SDA -> Pin("P22") | SCL -> Pin("P21")
bme = False
bh = False
ds = False
i2c = I2C(1)
i2c = I2C(1, I2C.MASTER)
i2c = I2C(
    1,
    pins=(
        Pin("P22"),
        Pin("P21")
    )
)
i2c_scanned = i2c.scan()
if len(i2c_scanned) == 0:
    print('\t> I2C - No device detected')
else:
    for addr in i2c_scanned:
        if addr == 35:
            bh = True
            print('\t> BH1750 ({}) - OK'.format(addr))
            light_sensor = BH1750FVI(i2c)
        elif addr == 118:
            bme = True
            print('\t> BME detected ({}) - OK'.format(addr))
            bme_sensor = BME280(address=BME280_I2CADDR, i2c=i2c)
        elif addr == 104:
            ds = True
            print('\t> DS3231 ({}) - OK'.format(addr))
            ds3231 = DS3231(i2c)
        else:
            print('\t> I2C Device addr unknowm ({})'.format(addr))
if not bme:
    print('\t> BME - NOT detected')
if not bh:
    print('\t> BH - NOT detected')
if not ds:
    print('\t> DS3231 - NOT detected')

while True:
    print("> Reading values....")
    t_vals = []
    h_vals = []
    t_ds18b20 = []
    l_bh = []
    t_bme = []
    h_bme = []
    p_bme = []
    for i in range(5):
        try:
            t_val = ((read_analog_voltage("P13"))*165/3300)-39.996
            h_val = ((read_analog_voltage("P14"))/3300)*100
            t_vals.append(t_val)
            h_vals.append(h_val)
        except:
            pass
        time.sleep(0.5)
        if read_temp:
            t = temp.read_temp_async()
            time.sleep(1)
            temp.start_conversion()
            time.sleep(1)
            try:
                float(t)
                if t >= 85:
                    t = -999
                else:
                    t_ds18b20.append(t)
            except:
                t = -999
        if bme:
            t_bme.append(float(bme_sensor.temperature))
            p_bme(float(bme_sensor.pressure))
            h_bme(float(bme_sensor.humidity))
        if bh:
            l_bh.append(float(light_sensor.read()))

    time.sleep(1)
    ds18b20 = round(sum(t_ds18b20)/len(t_ds18b20),
                    2) if len(t_ds18b20) > 0 else -999
    t9601_t = round(sum(t_vals)/len(t_vals), 2) if len(t_vals) > 0 else -999
    t9601_h = round(sum(h_vals)/len(h_vals), 2) if len(h_vals) > 0 else -999
    bme_t = round(sum(t_bme)/len(t_bme), 2) if len(t_bme) > 0 else -999
    bme_h = round(sum(h_bme)/len(h_bme), 2) if len(h_bme) > 0 else -999
    bme_p = round(sum(p_bme)/len(p_bme), 2) if len(p_bme) > 0 else -999
    bh_l = round(sum(l_bh)/len(l_bh), 2) if len(l_bh) > 0 else -999
    dt = pycom.nvs_get("dt")
    pycom.nvs_erase("dt")
    print("\t> {}".format(dt))
    row = "{}".format(dt)
    if read_temp:
        print("\t> DS18b20: {}°C".format(ds18b20))
    print("\t> t9601: {}°C".format(t9601_t))
    print("\t> t9601: {}%".format(t9601_h))
    if bh:
        print("\t> BH1750: {}lux".format(bh_l))
    row = "{},{}".format(row, ds18b20)
    row = "{},{}".format(row, t9601_t)
    row = "{},{}".format(row, t9601_h)
    row = "{},{}".format(row, bh_l)
    if bme:
        print("\t> BME280: {}°C".format(bme_t))
        print("\t> BME280: {}%".format(bme_h))
        print("\t> BME280: {}hPa".format(bme_p))
        row = "{},{}".format(row, bme_t)
        row = "{},{}".format(row, bme_h)
        row = "{},{}".format(row, bme_p)
    adc = ADC()
    apinBV = adc.channel(pin='P16', attn=adc.ATTN_2_5DB)
    batt = apinBV()/958
    v_batt = round(batt, 2)

    row = "{},{}".format(row, v_batt)
    print("\t> {}".format(row))
    print('> Save data to SD')
    try:
        sd = SD()
        print('\t> SD card initialized')
        os.mount(sd, '/sd')
        print('\t> SD card mounted')
        # check the content
        file_name = "data.csv"

        file_path = '/sd/{}'.format(file_name)
        mode = 'w'
        for item in os.listdir('/sd'):
            if item == file_name:
                mode = 'a'

        # try some standard file operations
        with open(file_path, mode) as f:
            f.write('{}\n'.format(row))
            f.close()
        os.umount('/sd')
        sd.deinit()
        print('\t> SD card unmounted')
        print('\t> Data saved')
    except Exception as e:
        print('\t> No SD card inserted')
        print('\t> Data NOT saved')
        print("\t> {}".format(str(e)))
    print("> Setting alarm for wake-up")
    print("\t> Calculating datetime for next RTC DS3231 alarm interrupt")
    freq = int(pycom.nvs_get("freq"))
    pycom.nvs_erase("freq")
    min = 0
    if freq % 60 == 0:
        min = 0
    elif freq % 30 == 0:
        min = int(dt[14:16])+30
        if min >= 30:
            min = 0
        else:
            min = 30
    elif freq % 10 == 0:
        min = int(dt[14:16])+10
        if min >= 60:
            min = 0
        else:
            dec = int(dt[14])+1
            min = int("{}0".format(dec))
    print("\t> Alarm set at minute {}".format(min))
    if ds:
        ds3231.alarm1.set(EVERY_HOUR, min=min, sec=00)
        ds3231.alarm1.clear()
        print("> Going to sleep deeply...")
        Pin("P11", mode=Pin.OUT, value=0, pull=None)
        deepsleep(240*60*1000)
    else:
        print("> Going to sleep deeply using internal RTC...")
        Pin("P11", mode=Pin.OUT, value=0, pull=None)
        deepsleep(freq*60*1000)
