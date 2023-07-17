import pycom
from network import WLAN
import machine
import utime

from lib.DS3231 import DS3231
from DS3231 import DS3231
from machine import Pin, I2C

# Pins with pullups on ESP8266: clk=WeMos D3(P0) data=WeMos D4(P2)
# i2c = I2C(-1, Pin(0, Pin.OPEN_DRAIN), Pin(2, Pin.OPEN_DRAIN))
# ds3231 = DS3231(i2c)
# ds3231.get_time()

def connect(conf):
    """
    Execute a wifi connection
    """
    try:
        if conf['debug']:
            print("Connection to wifi started.")
        wlan = WLAN(mode=WLAN.STA)
        rtc = machine.RTC()
        nets = wlan.scan()
        for net in nets:
            # print(net.ssid)
            if net.ssid == conf['config']['wifi']['ssid']:
                if conf['debug']:
                    print(' > network {} found.'.format(net.ssid))
                    print(' > password: {}'.format(
                        conf['config']['wifi']['password']
                    ))
                wlan.connect(
                    net.ssid,
                    auth=(
                        net.sec,
                        conf['config']['wifi']['password']
                    ),
                    timeout=10000
                )
                while not wlan.isconnected():
                    if conf['debug']:
                        print(" > idleing..")
                    machine.idle()  # save power while waiting

                if conf['debug']:
                    print(' > wifi connection succeeded!')

                # setup rtc
                print("Year? {}".format(utime.gmtime(utime.time())[0]))
                while utime.gmtime(utime.time())[0] == 1970:
                    rtc.ntp_sync("0.ch.pool.ntp.org")
                    utime.sleep_ms(2000)
                    if conf['debug']:
                        print('\nRTC Set from NTP to UTC:', rtc.now())
                # Pins with pullups on ESP8266: clk=WeMos D3(P0) data=WeMos D4(P2)
                # i2c = I2C(-1, Pin(0, Pin.OPEN_DRAIN), Pin(2, Pin.OPEN_DRAIN))
                i2c = I2C(1)
                i2c = I2C(1, I2C.MASTER)
                i2c = I2C(
                    1,
                    pins=(
                        conf['pins']['sda'],
                        conf['pins']['scl']
                    )
                )
                i2c_scanned = i2c.scan()
                if 104 in i2c_scanned:
                    print("DS3231 detected")
                    ds3231 = DS3231(i2c)
                    ds3231.save_time()
                    ds3231.get_time(set_rtc=True)
                    print("DS3231 time -->")
                    print(ds3231.get_time())
                    print("Internl RTC time -->")
                    print(rtc.now())
                    print("Time synced")
                    i2c.deinit()
                    Pin(
                        conf['pins']['scl'],
                        mode=Pin.IN
                    )
                    Pin(
                        conf['pins']['sda'],
                        mode=Pin.IN
                    )
                pycom.rgbled(0x23d613)
                utime.sleep_ms(2000)
                break
        if conf['transmission'] != 'wifi':
            wlan.deinit()
    except Exception as we:
        wlan.deinit()
        if conf['debug']:
            print("Wifi connection error: %r" % (we))


def connect_simple(conf):
    """
    Execute a wifi connection
    """
    try:
        if conf['debug']:
            print("Connection to wifi started.")
        wlan = WLAN(mode=WLAN.STA)
        rtc = machine.RTC()
        nets = wlan.scan()
        for net in nets:
            # print(net.ssid)
            if net.ssid == conf['config']['wifi']['ssid']:
                if conf['debug']:
                    print(' > network {} found.'.format(net.ssid))
                    print(' > password: {}'.format(
                        conf['config']['wifi']['password']
                    ))
                wlan.connect(
                    net.ssid,
                    auth=(
                        net.sec,
                        conf['config']['wifi']['password']
                    ),
                    timeout=10000
                )
                while not wlan.isconnected():
                    if conf['debug']:
                        print(" > idleing..")
                    machine.idle()  # save power while waiting

                if conf['debug']:
                    print(' > wifi connection succeeded!')
        return wlan
    except Exception as e:
        raise e
