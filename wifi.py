import pycom
from network import WLAN
import machine
import utime


def connect(conf):
    """
    Execute a wifi connection
    """
    if conf['debug']:
        pycom.rgbled(0x4286f4)
    wlan = WLAN(mode=WLAN.STA)
    rtc = machine.RTC()
    nets = wlan.scan()
    for net in nets:
        if conf['debug']:
            print(net.ssid)
        if net.ssid == conf['config']['wifi']['ssid']:
            print('Network found!')
            wlan.connect(
                net.ssid,
                auth=(
                    net.sec,
                    conf['config']['wifi']['password']
                ),
                timeout=5000
            )
            while not wlan.isconnected():
                print(".", end="")
                machine.idle()  # save power while waiting
            print('WLAN connection succeeded!')
            # setup rtc
            rtc.ntp_sync("metasntp13.admin.ch")
            utime.sleep_ms(2000)
            print('\nRTC Set from NTP to UTC:', rtc.now())
            # utime.timezone(3600)
            # print(
            #     'Adjusted from UTC to EST timezone',
            #     utime.localtime(),
            #     '\n'
            # )
            break
