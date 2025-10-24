"""
TEXIO PFR-100L50
#"""

import pyvisa

# import numpy as np # type: ignore
import math
import time

VISA_ADDRESS = "TCPIP0::" + "192.168.1.111" + "::" + "2268" + "::SOCKET"


class pfr_100l50:
    def __init__(self, rm, visa_address, wait_time=0.05):
        self.inst = rm.open_resource(
            visa_address, read_termination="\n", write_termination="\n", timeout=10000
        )
        self.inst.clear()
        print(self.inst.query("*IDN?"))
        pass

    def __del__(self):
        self.inst.clear()
        self.inst.close()
        pass

    def set_current(self, sv):
        self.inst.write(":CURR {}".format(sv))
        pass

    def set_voltage(self, sv):
        self.inst.write(":VOLT {}".format(sv))
        pass

    def set_output(self, status):
        if status == 0:
            command = "OFF"
        elif status == 1:
            command = "ON"
        self.inst.write(":OUTP {}".format(command))
        pass

    def get_output(self, select):
        if select == 0:
            command = "CURR"
        elif select == 1:
            command = "VOLT"
        elif select == 2:
            command = "POW"
        return float(self.inst.query(":MEAS:{}?".format(command)))


def main():
    rm = pyvisa.ResourceManager()
    visa_list = rm.list_resources()
    print(visa_list)

    ps = pfr_100l50(rm, VISA_ADDRESS)

    ps.set_voltage(0.5)
    ps.set_current(0.01)
    ps.set_output(1)
    time.sleep(1)
    print("I: {} A".format(ps.get_output(0)))
    print("V: {} V".format(ps.get_output(1)))
    print("W: {} W".format(ps.get_output(2)))
    ps.set_output(0)

    del ps
    return


if __name__ == "__main__":
    main()
    print("END")

"""
2025/04/08  Version1.0  出射 幹也@09Laser404
"""
