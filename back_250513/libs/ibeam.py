# -*- coding: utf-8 -*-
"""
TOPTICA iBeam
#"""

import pyvisa  # pyvisa > pyvisa-py > zeroconf > psutilという順でinstallが必要
import serial  # pip3 install pyserial
import sys

import numpy as np  # type: ignore
import math
import time

IBEAM_COM = 3  # デバイスマネージャーで確認

INTERVAL = 0.05


class ibeam:
    def __init__(self, port="COM4"):
        try:
            self.inst = serial.Serial(
                port=port,
                bytesize=serial.EIGHTBITS,
                baudrate=115200,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=1,
            )

            time.sleep(INTERVAL)
            self.set_prompt(0)  # Responseを[OK]に設定

        except Exception as e:
            print("Visa io error")
            sys.exit(0)

    def __del__(self):
        print("LaserDeL")
        self.set_prompt(1)  # Prompt設定戻さないと、iBeamSmartソフトウェアが使えない
        self.inst.flush()
        self.inst.close()

    def set_prompt(self, value=0):
        if value == 0:
            self.write("prom off")
        else:  # [OK]が帰ってこなくなるので、独自で送信する
            self.inst.flush()
            self.inst.write("{0}\r\n".format("prom on").encode("ASCII"))
            time.sleep(INTERVAL)

    def write(self, cmd):
        self.inst.flush()
        self.inst.write("{0}\r\n".format(cmd).encode("ASCII"))

        flag = 1
        while flag:
            # \r\nまで取得する
            response = self.inst.read_until(b"\r\n").decode("utf-8")
            if "OK" in response:
                # print('{} >> {}'.format(Command, Response))
                flag = 0

        time.sleep(INTERVAL)
        return response

    def read(self, cmd):
        self.inst.flush()
        self.inst.write("{0}\r\n".format(cmd).encode("ASCII"))

        response = self.inst.read_until(b"\r\n").decode("utf-8")
        while response == "\r\n":
            response = self.inst.read_until(b"\r\n").decode("utf-8")
            # \r\nのままなら、データが帰ってきていない

        flag = 1
        while flag:
            if "OK" in self.inst.read_until(b"\r\n").decode("utf-8"):
                # print('{} >> {}'.format(Command, Response))
                flag = 0

        time.sleep(INTERVAL)
        return response

    def laser_on(self):
        self.write("la on")

    def laser_off(self):
        self.write("la off")

    def ch_on(self, ch=1):
        self.write("en {}".format(ch))

    def ch_off(self, ch=1):
        self.write("di {}".format(ch))

    def set_lp(self, ch=1, power=0):  # [mW]で設定する
        self.write("ch {} pow {:.3f}".format(ch, power))

    def get_lp(self):
        return self.read("sh pow")
        # %SYS-I-077, scaled と返ってくる(tempも) → 搭載していないか非対応なのか...?
        # tempもTOPAS iBeam smartで90 mW出力でしばらく様子見ても変化しない(30.2℃)ので、非対応なのかも

    def get_current(self):
        return self.read("sh cur")

    def get_status(self, status="LD_Driver", ch=1):
        if status == "LD_Driver":
            return self.read("sta la")
        elif status == "Temp":
            return self.read("sta temp")
        elif status == "UpTime":
            return self.read("sta up")

    def get_error(self):
        return self.read("err")


def main():
    print("TOPTICA iBeam test")  # Ch1だと出力かわらないので、Ch2でやること
    print("COM Port: {}".format(IBEAM_COM))

    laser = ibeam("COM{}".format(IBEAM_COM))

    try:
        laser.ch_on(2)
        laser.set_lp(2, 50)
        laser.laser_on()
        time.sleep(1)
        print("Power: {}".format(laser.get_lp()))

        print("LD status: {}".format(laser.get_status("LD_Driver")))

        laser.set_lp(2, 20)
        # laser.laser_on()
        time.sleep(1)
        print("Power: {}".format(laser.get_lp()))

    except Exception as e:
        print("Error stop:", e)

    finally:
        laser.laser_off()
        print("LD status: {}".format(laser.get_status("LD_Driver")))
        laser.ch_off(2)
        print("Up time: {}".format(laser.get_status("UpTime")))
        print("Error: {}".format(laser.get_error()))
        del laser
        print("END")


if __name__ == "__main__":
    main()

""" ----------------------------------------------------------------------
Rivision history
2022/09/27: Version1.0 Created a program @Idei
2024/07/17: Version2.0 変数名などを改修 @Idei
2025/04/11  Version2.0 微修正 @Idei
---------------------------------------------------------------------- """
