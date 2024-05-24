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

import pycom
from network import WLAN, Bluetooth
import machine
import time
from network import Server
import time
from machine import PWRON_RESET, WDT_RESET, DEEPSLEEP_RESET, WAKEUP_ALL_LOW
from machine import PWRON_WAKE, PIN_WAKE, RTC_WAKE, pin_sleep_wakeup
from machine import Pin, RTC, SD, I2C
from lib.ds3231 import DS3231
from settings import *
import os
import ujson
# from datetime import datetime
import utime


def parse_iso8601_datetime(iso_datetime):
    # Divide la stringa in data/ora e timezone
    date_str, time_str = iso_datetime.split("T")
    year = int(date_str[0:4])
    month = int(date_str[5:7])
    day = int(date_str[8:10])
    hour = int(time_str[0:2])
    minute = int(time_str[3:5])
    second = int(time_str[7:9])
    timestamp_no_timezone = utime.mktime(
        (year, month, day, hour, minute, second, 0, 0))
    return timestamp_no_timezone


#################
# BOOTING TASKS #
#################
print("")
print("####################")
print("# Albis Sensor 2.0 #")
print("####################")
###################
# MAGNETIC WAKE-UP
# SET WAKE UP PIN
wake1 = Pin("P9", mode=Pin.IN)
pin_sleep_wakeup([wake1], WAKEUP_ALL_LOW)
print("********")
print("* BOOT *")
print("********")
####################
# POWER MANAGEMENT
# Turn-on switch to power external modules
Pin("P11", mode=Pin.OUT, value=1, pull=None)
# disable unsued services to save power
# WiFi
pycom.wifi_on_boot(False)
wlan = WLAN()
wlan.deinit()
# Bluetooth
bluetooth = Bluetooth()
bluetooth.deinit()
# server FTP
server = Server()
server.deinit()
# Turn-off heartbeat
if pycom.heartbeat() == True:
    pycom.heartbeat(False)
# init I2C
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
print("> Checking DS3231")
# CLOCK
# init RTC
rtc = RTC()
rtc.init()
# checking ds3231
ds = False
if len(i2c_scanned) == 0:
    print('\t> I2C No device detected')
else:
    for addr in i2c_scanned:
        if addr == 104:
            ds = True
            print('\t> DS3231 detected. ADDR {}'.format(addr))
            ds3231 = DS3231(i2c)
# Turn-on switch to power external modules
# Pin("P11", mode=Pin.OUT, value=1, pull=None)
# GET DATETIME
if ds:
    datetime_now = ds3231.get_time(set_rtc=True)
    print("> Setting time from DS3231")
else:
    print("> Setting time from internal RTC")
    datetime_now = rtc.now()

print("\t> Datetime is: {}".format(datetime_now))
dt = "{}-{}-{}T{}:{}:00+00:00".format(
    datetime_now[0],
    datetime_now[1] if len(
        str(datetime_now[1])) > 1 else "0{}".format(datetime_now[1]),
    datetime_now[2] if len(
        str(datetime_now[2])) > 1 else "0{}".format(datetime_now[2]),
    datetime_now[3] if len(
        str(datetime_now[3])) > 1 else "0{}".format(datetime_now[3]),
    datetime_now[4] if len(
        str(datetime_now[4])) > 1 else "0{}".format(datetime_now[4])
)
# READ CUSTOM CONFIGURATION FROM SD CARD config.json
print("> Read custom conf from SD")
try:
    sd = SD()
    print('\t> SD card initialized')
    os.mount(sd, '/sd')
    for item in os.listdir('/sd'):
        if item == "config.json":
            with open("/sd/config.json", 'r') as cf:
                conf = ujson.loads(cf.read())
                if "WIFI_SSID" in conf.keys():
                    WIFI_SSID = conf["WIFI_SSID"]
                if "WIFI_PWD" in conf.keys():
                    WIFI_PWD = conf["WIFI_PWD"]
                if "FTP_USER" in conf.keys():
                    FTP_USER = conf["FTP_USER"]
                if "FTP_PASSWORD" in conf.keys():
                    FTP_PASSWORD = conf["FTP_PASSWORD"]
                if "FREQUENCY" in conf.keys():
                    try:
                        if int(conf["FREQUENCY"]) in [MIN_10, MIN_30, MIN_60]:
                            FREQUENCY = conf["FREQUENCY"]
                        else:
                            print(
                                '''\t> Frquency not supported.
                                Supported values are: 10, 30 or 60.
                                Using default values (60).''')
                    except:
                        pass
                if "START_DATE" in conf.keys():
                    START_DATE = conf["START_DATE"]
                print('\t> Settings SUCCESSFULLY overwritten')
    os.umount('/sd')
    sd.deinit()
    print('\t> SD card unmounted')
except Exception as e:
    print("\t> Can't read SD.\n\t> Default configuration will be used.")
print('\t> Frequency: {}min'.format(FREQUENCY))
pycom.nvs_set("dt", dt)
pycom.nvs_set("freq", FREQUENCY)
######################
# BOOTING MOTIVATION
print("> Boot motivation")
first_power_on = True
if machine.reset_cause() == DEEPSLEEP_RESET:
    first_power_on = False
    if machine.wake_reason()[0] == PIN_WAKE:
        print("\t> Is alarm occurred?: {}".format(ds3231.alarm1.__call__()))
        if not ds3231.alarm1.__call__():
            print("\t> Coming from deepsleep because of MAGNETIC Pin wake-up")
            ds3231.alarm1.enable(False)
            try:
                sd = SD()
                print('\t> SD card initialized')
                os.mount(sd, '/sd')
                print("\t> Opening a WiFi hotspot to access SD files")
                # init WiFi AP
                wlan = WLAN()
                wlan.init(mode=WLAN.AP, ssid=WIFI_SSID,
                          auth=(WLAN.WPA2, WIFI_PWD))
                # init FTP server
                server = Server(login=(FTP_USER, FTP_PASSWORD), timeout=60)
                server.timeout(300)
                server.timeout()
                server.isrunning()
                # wait 5 minutes before resetting the device
                c = 0
                print("\t> Connection opened", end="")
                # pycom.rgbled(0x007f00)
                pycom.rgbled(0x00FF)
                while c < 300:
                    print(".", end="")
                    time.sleep(1)
                    c += 1
                print("")
                print("\t> WiFi hotspot closed", end="")
                pycom.rgbled(0x7f0000)
                wlan.deinit()
                server.deinit()
                os.umount('/sd')
                sd.deinit()
                print('\t> SD card unmounted')
                machine.reset()
            except:
                print("\t> Can't read SD.")
                print("\t> Re-starting...")
                pycom.rgbled(0x7f0000)  # red
                time.sleep(10)
                machine.reset()
        else:
            ds3231.alarm1.enable(False)
        print("\t> Coming from deepsleep because of EXTERNAL RTC wake-up")
    elif machine.wake_reason()[0] == RTC_WAKE:
        print("\t> Coming from deepsleep because of RTC wake-up")
    elif machine.wake_reason()[0] == PWRON_WAKE:
        print("\t> Coming from deepsleep because of PWRON_WAKE")
    else:
        print("\t> Coming from deepsleep")
elif machine.reset_cause() == PWRON_RESET:
    if not first_power_on:
        pycom.rgbled(0x00FF)
    print("\t> Device powered On")
elif machine.reset_cause() == WDT_RESET:
    first_power_on = False
    print("\t> Waked-up from WDT reset")
else:
    print("\t> Other")

print("> Checking datetime")
if first_power_on or datetime_now[0] < 2024:
    pycom.rgbled(0x7f7f00)
    print("\t> RTC need to be synced")
    # init WiFi STA
    wlan = WLAN(mode=WLAN.STA)
    print("\t> Checking {} WIFI".format(WIFI_SSID), end='')
    not_synced = True
    while datetime_now[0] < 2024 or not_synced:
        nets = wlan.scan()
        print(".", end='')
        for net in nets:
            if net.ssid == WIFI_SSID:
                try:
                    if WIFI_PWD:
                        wlan.connect(
                            timeout=60000,
                            ssid=WIFI_SSID,
                            auth=(WLAN.WPA2, WIFI_PWD)
                        )
                    else:
                        wlan.connect(
                            WIFI_SSID,
                            timeout=60000
                        )
                    while not wlan.isconnected():
                        machine.idle()  # save power while waiting
                    print('\t> WLAN connection succeeded!')
                    print("\t> Syncing RTC through internet WiFi using NTP")
                    rtc.ntp_sync("pool.ntp.org")
                    while not rtc.synced():
                        pass  # save power while waiting
                    time.sleep(0.2)
                    if ds:
                        ds3231.set_time()
                        datetime_now = ds3231.get_time()
                        print("\t> Setting time from DS3231")
                    else:
                        datetime_now = rtc.now()
                    print("\t> Datetime is: {}".format(datetime_now))
                    dt = "{}-{}-{}T{}:{}:00+00:00".format(
                        datetime_now[0],
                        datetime_now[1] if len(
                            str(datetime_now[1])) > 1 else "0{}".format(
                                datetime_now[1]),
                        datetime_now[2] if len(
                            str(datetime_now[2])) > 1 else "0{}".format(
                                datetime_now[2]),
                        datetime_now[3] if len(
                            str(datetime_now[3])) > 1 else "0{}".format(
                                datetime_now[3]),
                        datetime_now[4] if len(
                            str(datetime_now[4])) > 1 else "0{}".format(
                                datetime_now[4])
                    )
                    pycom.nvs_erase("dt")
                    pycom.nvs_set("dt", dt)
                    not_synced = False
                except Exception as e:
                    print("Error: {}".format(str(e)))
                    pass
        time.sleep(2)
    wlan.deinit()
    pycom.rgbled(0x007f00)

# Turn-off heartbeat
if pycom.heartbeat() == True:
    pycom.heartbeat(False)
print("\t> RTC is synced")

machine.main('main.py')
