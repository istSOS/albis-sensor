import pycom
import ujson
import time
import utime
from lib.sensors import Sensors
if conf['deepsleep_shield']:
    from lib.deepsleep import DeepSleep
    ds = DeepSleep()
else:
    from machine import deepsleep

conf = {}

with open("config.json", 'r') as cf:
    conf = ujson.loads(cf.read())

if conf['lora'] is True:
    from lib.loranode import LoraNodeRaw
    lora = LoraNodeRaw(conf['config']['lora'])


if conf['wifi'] is True:
    import lib.urequests as requests

print("Starting main loop..")

# Start monitoring
while(True):

    sensors = Sensors(conf)
    values = []
    obs = sensors.get_obs(conf['read_cnt'])

    if conf['debug']:
        print(obs)

    for ob in conf['observations']:
        if conf["debug"]:
            print(ob[0])
        values.append(
            "{}".format(obs[ob[1]])
        )

    if conf['lora'] is True:

        # Preparing message for lora excluding timestamp
        data = '{};{}'.format(
            conf['sensorid'],
            ",".join(values)
        )

        if conf['debug']:
            print("Sending via Lora")
            print(data)

        try:
            lora.send_msg(data)
        except Exception as e:
            print(str(e))

    # time.sleep(20)


    if conf['wifi'] is True:
        print("Sending via WIFI")

        now = utime.gmtime(utime.time())
        # FORMAT LATEST READ
        data = "{};{}-{:02d}-{:02d}T{:02d}:{:02d}:{:02d}+0000".format(
            conf['sensorid'],
            now[0],
            now[1],
            now[2],
            now[3],
            now[4],
            now[5]
        )

        data = '{},{}'.format(
            data,
            ",".join(values)
        )

        # SEND DATA
        r = requests.post(
            conf['server'],
            data=data
        )

        if conf["debug"]:
            print(r.text)
            if r.text.find("true") > -1:
                print("data succesfully sent")
            else:
                print("error sending data")

    print("Going to sleep")
    if conf['deepsleep_shield']:
        ds.go_to_sleep(conf["deepsleep_seconds"])
    else:
        deepsleep(conf["deepsleep_seconds"]*1000)
    print("Deepsleep ended")
