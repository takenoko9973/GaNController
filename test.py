import os
import time
from libs.ibeam import ibeam
from utils.log_file import LogFile, LogFileManager
from utils.sequence import Rising

import pyvisa  # pyvisa > pyvisa-py > zeroconf > psutilという順でinstallが必要
import serial  # pip3 install pyserial

inst = serial.Serial(
                port="COM2",
                bytesize=serial.EIGHTBITS,
                baudrate=115200,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=1000,
            )

message = b"\x01\x03\x00\x00\x00\x04" + b"D\t"
inst.write(message)
time.sleep(1.0)
res = inst.read_all()

print(message, res)
