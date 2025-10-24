"""TEXIO PFR-100L50
#
"""

# import numpy as np # type: ignore
import time

import pyvisa

VISA_ADDRESS = "TCPIP0::" + "192.168.1.111" + "::" + "2268" + "::SOCKET"


class pfr_100l50:
    def __init__(self, rm: pyvisa.ResourceManager, visa_address: str, wait_time=0.05) -> None:
        self.inst = rm.open_resource(
            visa_address,
            read_termination="\n",
            write_termination="\n",
            timeout=10000,
        )
        self.inst.clear()
        print(self.inst.query("*IDN?"))

    def __del__(self) -> None:
        self.inst.clear()
        self.inst.close()

    def set_current(self, sv: float) -> None:
        self.inst.write(f":CURR {sv}")

    def set_voltage(self, sv: float) -> None:
        self.inst.write(f":VOLT {sv}")

    def set_output(self, status: int) -> None:
        if status == 0:
            command = "OFF"
        elif status == 1:
            command = "ON"
        self.inst.write(f":OUTP {command}")

    def get_output(self, select: int) -> float:
        if select == 0:
            command = "CURR"
        elif select == 1:
            command = "VOLT"
        elif select == 2:  # noqa: PLR2004
            command = "POW"
        return float(self.inst.query(f":MEAS:{command}?"))


def main() -> None:
    rm = pyvisa.ResourceManager()
    visa_list = rm.list_resources()
    print(visa_list)

    ps = pfr_100l50(rm, VISA_ADDRESS)

    ps.set_voltage(0.5)
    ps.set_current(0.01)
    ps.set_output(1)
    time.sleep(1)
    print(f"I: {ps.get_output(0)} A")
    print(f"V: {ps.get_output(1)} V")
    print(f"W: {ps.get_output(2)} W")
    ps.set_output(0)

    del ps


if __name__ == "__main__":
    main()
    print("END")

"""
2025/04/08  Version1.0  出射 幹也@09Laser404
"""
