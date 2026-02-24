"""PWUX"""

import time

import pyvisa

PWUX_COM = 1  # デバイスマネージャーで確認


class pwux:
    def __init__(self, rm: pyvisa.ResourceManager, visa_address: str, wait_time=0.05) -> None:
        self.inst = rm.open_resource(
            visa_address,
            read_termination="\r\n",
            write_termination="\r\n",
            timeout=10000,
        )
        # print(self.inst.query("*IDN?"))

    def __del__(self) -> None:
        self.inst.close()

    def set_pointer(self, status: int) -> str:
        # status >> 0: OFF, 1: ON
        return self.inst.query(f"LS {status}")[3:]

    def get_temp(self) -> float:
        try:
            response = "{}".format(self.inst.query("PV")[3:])
            return float(response) if "OVER" not in response else 9999
        except Exception as e:  # noqa: BLE001
            print(f"Error: {e}")
            return -1

    def test(self) -> None:
        self.inst.write("EE 0.05")
        print(f">> {self.inst.read()}")
        print(f">> {self.inst.query('VR')}")


def main() -> None:
    rm = pyvisa.ResourceManager()
    visa_list = rm.list_resources()
    print(visa_list)

    rt = pwux(rm, visa_list[PWUX_COM - 1])

    print(f"Temp: {rt.get_temp()} deg.C")
    print(rt.set_pointer(1))
    time.sleep(1)
    print(rt.set_pointer(0))

    del rt


if __name__ == "__main__":
    main()
    print("END")

"""
2025/04/08  Version1.0  出射 幹也@09Laser404
"""
