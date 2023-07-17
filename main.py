import pycom
import ujson
import time
import utime
from machine import Pin, deepsleep, I2C
import os
from lib.sensors import Sensors
from lib.loranode import LoraNode
from lib.DS3231 import DS3231
import urequests

 # 70B3D5499BFEEC11 AL004 sostituto
 # 70B3D5499FE29231 AL006 sostituto
 # 70B3D5499D41AAB2 AL001 sostituto

# check time
from machine import Timer
import time

chrono = Timer.Chrono()

chrono.start()

conf = {}

with open("config.json", 'r') as cf:
    conf = ujson.loads(cf.read())
wlan = None
if conf['transmission']=='wifi':
    from network import WLAN
    wlan = WLAN(mode=WLAN.STA)
    if wlan.isconnected():
        print("WiFi connected")


print("Starting main loop..")

cnt = 0
# Start monitoring
while(True):
    machine.idle()
    msg = ""

    sensors = Sensors(conf)
    values = []
    obs = sensors.get_obs(conf['read_cnt'])
    print(obs)
    for ob in conf['observations']:
        if ob[1] in obs:
            if conf["debug"]:
                print('{} = {}'.format(
                    ob[0], obs[ob[1]]
                ))
            values.append(
                "{}".format(obs[ob[1]])
            )

    msg = ",".join(values)

    data = msg

    print("Sending data")
    print(data)

    try:
        if conf['debug'] is True:
            pycom.rgbled(0xff0000)
        if conf['transmission']=='lora':
            print("Sending using LoRa")
            lora = LoraNode(conf)
            stats = lora.send_msg(data, chrono)
            print(stats)
        elif conf['transmission']=='wifi':
            # from lib import wifi
            # pycom.rgbled(0x204c70)
            # wifi.connect(conf)
            if not wlan.isconnected():
                from lib import wifi
                pycom.rgbled(0x204c70)
                wlan = wifi.connect(conf)
            if wlan.isconnected():
                try:
                    res = urequests.get(
                        "http://istsos.org/istsos/wa/istsos/services/maxdemo/procedures/{}".format(conf['name']),
                    )
                    proc = res.json()
                    res.close()
                    aid = proc['data']['assignedSensorId']
                    url = 'http://istsos.org/istsos/wa/istsos/services/maxdemo/operations/fastinsert'
                    res = urequests.post(
                        url,
                        headers={
                            "Content-Type": "application/json",
                            "Accept": "application/json"
                        },
                        data="{};{}".format(aid, str(data))
                    )
                    res.close()
                except Exception as e:
                    print("Error during data transmission.")
        else:
            print("No transmission set.")
    except Exception as e:
        print(str(e))

    if conf['sd']:
        # write data on SD card
        try:
            sd = SD()
            print('SD card initialized')
            print('Saving data...')
            os.mount(sd, '/sd')
            if conf['debug']:
                print('SD card mounted')
            # check the content
            file_name = conf['config']['sd']['file_name']

            file_path = '/sd/{}'.format(file_name)
            mode = 'w'
            for item in os.listdir('/sd'):
                if item == file_name:
                    mode = 'a'

            # try some standard file operations
            with open(file_path, mode) as f:
                if conf['transmission']=='lora':
                    f.write('{},{},{}\n'.format(stats['prob'], stats['stats'], data))
                    f.close()
                else:
                    f.write('{}\n'.format(data))
                    f.close()

            os.unmount('/sd')
            if conf['debug']:
                print('SD card unmounted')
            print('Data saved')
        except Exception as e:
            print('No SD card inserted')
            print('Data NOT saved')
            print(str(e))

    if conf['debug'] is True:
        pycom.rgbled(0x000000)
        cnt += 1
        print("Sleep counter: %s" % cnt)
        time.sleep(60)
    else:
        print("Going to sleep")
        if conf['frequency']:
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
                time_now = ds3231.get_time(set_rtc=True)

                time_minute = time_now[4]
                last_seconds = 60 - time_now[5]
                seconds_to_sleep = ((conf['frequency'] - (time_now[4]%conf['frequency'])) * 60) - time_now[5]
                if seconds_to_sleep < 5:
                    seconds_to_sleep = 5
                print("I will wake up in: {} secs".format(seconds_to_sleep))
                deepsleep(
                    seconds_to_sleep*1000
                )
        else:
            secs_passed = chrono.read() + 4
            chrono.stop()
            chrono.reset()
            if secs_passed < conf["deepsleep_seconds"]:
                deepsleep(
                    (conf["deepsleep_seconds"]-int(secs_passed))*1000
                )
            else:
                deepsleep(1*1000)
            print("Deepsleep ended")
