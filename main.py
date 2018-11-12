import pycom
import ujson
import time
import utime
from machine import Pin, deepsleep
import os
from machine import deepsleep
from lib.sensors import Sensors
from lib.loranode import LoraNode

conf = {}

with open("config.json", 'r') as cf:
    conf = ujson.loads(cf.read())

print("Starting main loop..")

cnt = 0
# Start monitoring
while(True):
    machine.idle()
    msg = ""

    sensors = Sensors(conf)
    values = []
    obs = sensors.get_obs(conf['read_cnt'])

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

    print("Sending via Lora")
    print(data)

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


    try:
        if conf['debug'] is True:
            pycom.rgbled(0xff0000)
        lora = LoraNode(conf)
        lora.send_msg(data)
    except Exception as e:
        print(str(e))

    if conf['debug'] is True:
        pycom.rgbled(0x000000)
        cnt += 1
        print("Sleep: %s" % cnt)
        time.sleep(conf["deepsleep_seconds"])
    else:
        print("Going to sleep")

        deepsleep(conf["deepsleep_seconds"]*1000)

        print("Deepsleep ended")
