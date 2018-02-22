# ALBIS Sensor

## Resetting Lopy

https://docs.pycom.io/chapter/toolsandfeatures/bootmodes.html#reset

```python
import os
os.getfree("/flash")
os.mkfs('/flash')

import machine
machine.reset()

```

## Using Atom IDE as normal user

Every time you plug in the device

```bash
sudo chmod 666 /dev/ttyUSB0
```
Or
```bash
sudo chmod 666 /dev/ttyACM0
```

## Led Colors Debugger

Color | Action
----- | -------
<div style="background-color: #ff0000; height: 20px; width: 20px;"></div> | Booting
<div style="background-color: #4286f4; height: 20px; width: 20px;"></div> | Connecting to WIFI
<div style="background-color: #ffa500; height: 20px; width: 20px;"></div> | Measuring
<div style="background-color: #155119; height: 20px; width: 20px;"></div> | Main loop
