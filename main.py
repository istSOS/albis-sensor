import pycom
import ujson
import time
import utime
import sensors
from machine import deepsleep

conf = {}
with open("config.json", 'r') as cf:
    conf = ujson.loads(cf.read())

if conf['wifi'] is True:
    import lib.urequests as requests

cnt = 0

print("Starting main loop..")

# Start monitoring
while(True):
    now = utime.gmtime(utime.time())
    cnt += 1
    obs = sensors.read()
    print('{}/{}'.format(cnt, conf['read_cnt']))
    # Send data after 20 measurements
    if cnt == conf['read_cnt']:
        if conf['wifi'] is True:
            print("Sending via WIFI")
            data = "{};{}-{:02d}-{:02d}T{:02d}:{:02d}:{:02d}+0000".format(
                conf['sensorid'],
                now[0],
                now[1],
                now[2],
                now[3],
                now[4],
                now[5]
            )
            values = []
            for ob in conf['observations']:
                values.append(
                    "{}".format(obs[ob[1]])
                )
            data = '{},{}'.format(
                data,
                ",".join(values)
            )
            print(data)
            # avoid in the future measurements
            utime.sleep_ms(10000)
            r = requests.post(
                conf['server'],
                data=data
            )
            print(r.text)

    if cnt < conf['read_cnt']:
        # pycom.rgbled(0x155119)
        time.sleep_ms(500)
    else:
        cnt = 0
        deepsleep(conf['deepsleep_seconds']*1800000)
