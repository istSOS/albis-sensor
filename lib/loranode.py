import socket
import struct
import binascii
import time
from network import LoRa
import crypto
from crypto import AES
import pycom
import machine

# A basic package header
# B: 1 byte for the deviceId
# B: 1 byte for the pkg size
# B: 1 byte for the messageId
# %ds: Formated string for string
_LORA_PKG_FORMAT = "B%ds"

# A basic ack package
# B: 1 byte for the deviceId
# B: 1 byte for the pkg size
# B: 1 byte for the messageId
# B: 1 byte for the Ok (200) or error messages
_LORA_PKG_ACK_FORMAT = "BBB"


class LoraNode():

    _MAX_ACK_TIME = 5000
    _RETRY_COUNT = 3

    def __init__(self, conf=None):
        self.conf = conf
        print("Joining...")
        loraSaved = pycom.nvs_get('loraSaved')
        if not loraSaved:
            self.lora = LoRa(
                mode=LoRa.LORAWAN,
                adr=True,
                tx_retries=3,
                device_class=LoRa.CLASS_A,
                sf=12
            )
            print("First join")

            lora_type =  self.conf['config']['lora']['type']
            if lora_type == "ABP":
                # create an ABP authentication params
                dev_addr_abp = struct.unpack(
                    ">l", binascii.unhexlify(
                        self.conf['config']['lora']['dev_addr_abp']
                    )
                )[0]
                nwk_swkey_abp = binascii.unhexlify(
                    self.conf['config']['lora']['nwk_swkey_abp']
                )
                app_swkey_abp = binascii.unhexlify(
                    self.conf['config']['lora']['app_swkey_abp']
                )
                auth = (dev_addr_abp, nwk_swkey_abp, app_swkey_abp)
            else:
                # create an OTAA authentication params
                app_eui_otaa = binascii.unhexlify(
                    self.conf['config']['lora']['app_eui_otaa']
                )
                app_key_otaa = binascii.unhexlify(
                    self.conf['config']['lora']['app_key_otaa']
                )
                if self.conf['config']['lora']['dev_eui_otaa'] is not None:
                    dev_eui_otaa = binascii.unhexlify(
                        self.conf['config']['lora']['dev_eui_otaa']
                    )
                    auth = (dev_eui_otaa, app_eui_otaa, app_key_otaa)
                else:
                    auth = (app_eui_otaa, app_key_otaa)

            # join the network
            self.lora.join(
                activation= LoRa.ABP if lora_type == 'ABP' else LoRa.OTAA,
                auth=auth,
                timeout=0
            )

            # wait until the module has joined the network
            while not self.lora.has_joined():
                machine.idle()

            # create a LoRa socket
            self.lora_sock = socket.socket(socket.AF_LORA, socket.SOCK_RAW)

            # # selecting confirmed type of messages
            # self.lora_sock.setsockopt(socket.SOL_LORA, socket.SO_CONFIRMED, True)

            # set the LoRaWAN data rate
            self.lora_sock.setsockopt(socket.SOL_LORA, socket.SO_DR, self.conf['LORA_NODE_DR'])
            self.lora_sock.setblocking(True)

        else:
            print("Restoring LoRa")
            self.lora = LoRa(
                mode=LoRa.LORAWAN,
                adr=True,
                tx_retries=3,
                device_class=LoRa.CLASS_A
            )
            self.lora.nvram_restore()

            # wait until the module has joined the network
            while not self.lora.has_joined():
                machine.idle()

            # create a LoRa socket
            self.lora_sock = socket.socket(socket.AF_LORA, socket.SOCK_RAW)

            # # set the LoRaWAN data rate
            # self.lora_sock.setsockopt(socket.SOL_LORA, socket.SO_CONFIRMED, True)

            # set the LoRaWAN data rate
            self.lora_sock.setsockopt(socket.SOL_LORA, socket.SO_DR, self.conf['LORA_NODE_DR'])
            self.lora_sock.setblocking(True)
        print("Joined")

    # Method to send messages
    def send_msg(self, msg, chrono):
        pkg = struct.pack(
            _LORA_PKG_FORMAT % len(msg),
            len(msg),
            msg
        )

        # send some data
        prob = 'high'
        while self.lora.ischannel_free(-110):
            if chrono.read() > 20:
                prob = 'low'
                break
            else:
                continue
        self.lora_sock.send(pkg)

        self.lora_sock.setblocking(False)

        data = self.lora_sock.recv(64)
        print(data)
        self.lora.nvram_save()
        pycom.nvs_set('loraSaved', 1)
        return { 'prob': prob, 'stats': self.lora.stats()}
