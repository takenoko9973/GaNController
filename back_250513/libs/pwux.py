"""
PWUX
#"""

import pyvisa

# import numpy as np # type: ignore
import math
import time

PWUX_COM = 1  # デバイスマネージャーで確認


class pwux:
    def __init__(self, rm: pyvisa.ResourceManager, visa_address: str, wait_time=0.05):
        self.inst = rm.open_resource(
            visa_address,
            read_termination="\r\n",
            write_termination="\r\n",
            timeout=10000,
        )
        # print(self.inst.query("*IDN?"))
        pass

    def __del__(self):
        self.inst.close()
        pass

    def set_pointer(self, status):
        # status >> 0: OFF, 1: ON
        return self.inst.query("LS {}".format(status))[3:]

    def get_temp(self):
        response = "{}".format(self.inst.query("PV")[3:])
        if "OVER" in response:
            return 9999
        else:
            return float(response)

    def test(self):
        self.inst.write("EE 0.05")
        print(">> {}".format(self.inst.read()))
        print(">> {}".format(self.inst.query("VR")))
        pass


def main():
    rm = pyvisa.ResourceManager()
    visa_list = rm.list_resources()
    print(visa_list)

    rt = pwux(rm, visa_list[PWUX_COM - 1])

    print("Temp: {} deg.C".format(rt.get_temp()))
    print(rt.set_pointer(1))
    time.sleep(1)
    print(rt.set_pointer(0))

    del rt
    return


if __name__ == "__main__":
    main()
    print("END")

"""
2025/04/08  Version1.0  出射 幹也@09Laser404
"""
