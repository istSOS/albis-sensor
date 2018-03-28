import socket
import struct
import time
from network import LoRa
import crypto
from crypto import AES

# A basic package header
# B: 1 byte for the deviceId
# B: 1 byte for the pkg size
# B: 1 byte for the messageId
# %ds: Formated string for string
_LORA_PKG_FORMAT = "!BB%ds"

# A basic ack package
# B: 1 byte for the deviceId
# B: 1 byte for the pkg size
# B: 1 byte for the messageId
# B: 1 byte for the Ok (200) or error messages
_LORA_PKG_ACK_FORMAT = "BBB"


class LoraNodeRaw():

    _MAX_ACK_TIME = 5000
    _RETRY_COUNT = 3

    def __init__(self, conf=None):
        # conf: {
        #    "deviceId": integer[0...255]
        # }
        self._DEVICE_ID = 0x01
        self.conf = conf
        if conf is not None and 'deviceId' in conf:
            self._DEVICE_ID = conf['deviceId']

        self.msg_id = 0
        self.lora = LoRa(mode=LoRa.LORA, tx_iq=True, region=LoRa.EU868)
        self.lora_sock = socket.socket(socket.AF_LORA, socket.SOCK_RAW)
        self.lora_sock.setblocking(False)

    def increase_msg_id(self):
        self.msg_id = (self.msg_id + 1) & 0xFF

    # Method for acknoledge waiting time keep
    def check_ack_time(self, from_time):
        current_time = time.ticks_ms()
        return (current_time - from_time > self._MAX_ACK_TIME)

    # Method to send messages
    def send_msg(self, msg):

        # Encrypting message if key present in conf
        if self.conf is not None and 'key' in self.conf:
            # hardware generated random IV
            iv = crypto.getrandbits(128)
            cipher = AES(
                self.conf['key'],
                AES.MODE_CFB, iv
            )
            msg = iv + cipher.encrypt(b'%s' % msg)

        retry = self._RETRY_COUNT
        sent = False
        while (retry > 0):
            retry -= 1
            pkg = struct.pack(
                _LORA_PKG_FORMAT % len(msg),
                self._DEVICE_ID,
                len(msg),
                msg
            )
            self.lora_sock.send(pkg)

            # Wait for the response from the server.
            start_time = time.ticks_ms()

            while(not self.check_ack_time(start_time)):
                recv_ack = self.lora_sock.recv(256)
                # If a message of the size of the acknoledge
                # message is received
                if (len(recv_ack) > 0):
                    device_id, pkg_len, ack = struct.unpack(_LORA_PKG_ACK_FORMAT, recv_ack)
                    if (device_id == self._DEVICE_ID):
                        if (ack == 200):
                            sent = True
                            # If the uart = machine.UART(0, 115200) and os.dupterm(uart) are set in the boot.py this print should appear in the serial port
                            print("ACK")
                            retry = 0
                            return

        raise Exception("Message not sent after {} attempt".format(
            self._RETRY_COUNT
        ))
