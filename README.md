# ALBIS Sensor
This repository contains the source code to operate the Albis sensor v2.0. The Albis sensor has been designed to measure environmental parameters such as water and air temperature, light intensity in terms of Lux, and air humidity in harsh environments like catch basins. The goal is to monitor micro-ecosystems that promote the growth of the Aedes Albopictus mosquitoes.

## How to flash the code into LoPy4

Requirements:

- LoPy4 (https://docs.pycom.io/datasheets/development/lopy4/) (unfortunately no more available)
- SUPSI / TecInvent PCB board with prommaing port or a PyCom development board
- USB FTDI cable (https://www.digikey.fr/fr/products/detail/ftdi-future-technology-devices-international-ltd/TTL-232R-5V/2003493)
- PC
- Thonny or VSCODE

Follow the steps below:

1. Plug the LoPy4 to the board
2. Connect the USB-FTDI cable between the board and the PC
3. Clone the repository using the command:
```
git clone https://github.com/istSOS/albis-sensor.git -b albis_v2
```
4. Go into the created folder:
```
cd albis_v2
```
5. Open the code editor such as VsCode or Thonny and upload only the following files and folder into the device:
- boot.py
- main.py
- settings.py
- lib/
6. Done

**N.B. The LoPy4 firmware version should be >= 1.20.2.rc6**