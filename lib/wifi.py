import pycom
from network import WLAN
import machine
import utime


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
                    rtc.ntp_sync("metasntp13.admin.ch")
                    utime.sleep_ms(2000)
                    if conf['debug']:
                        print('\nRTC Set from NTP to UTC:', rtc.now())
                pycom.rgbled(0x23d613)
                utime.sleep_ms(2000)
                break
        wlan.deinit()
    except Exception as we:
        wlan.deinit()
        if conf['debug']:
            print("Wifi connection error: %r" % (we))
