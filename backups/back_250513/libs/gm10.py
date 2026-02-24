"""
GM-10
#"""

import numpy as np
import math
import time

import pyvisa  # pyvisa > pyvisa-py > zeroconf > psutil

# VISA_ADDRESS = 'TCPIP0::' + '169.254.0.19' + '::' + '34434' + '::SOCKET'
# VISA_ADDRESS = 'TCPIP0::' + '192.168.1.201' + '::' + '34434' + '::SOCKET'
VISA_ADDRESS = "TCPIP0::" + "192.168.1.105" + "::" + "34434" + "::SOCKET"


class gm10:
    def __init__(self, rm, visa_address, wait_time=0.05):
        self.inst = rm.open_resource(
            visa_address,
            read_termination="\r\n",
            write_termination="\r\n",
            timeout=10000,
        )
        self.inst.clear()
        print("init")
        pass

    def __del__(self):
        self.inst.clear()
        self.inst.close()
        pass

    def test(self):
        self.inst.write("FData,0,0001,0010")
        time.sleep(0.05)
        # print("Response")
        # print(self.inst.read())

        data = []
        flag = True
        while flag:
            response = self.inst.read()
            if response == "EA":
                continue
            if response == "EN":
                flag = False
            else:
                data.append(response)
        # print('\n'.join(data))
        # print('{}'.format(len(data)))

        # res_data = []
        # n = 10
        # print('{}: {}'.format(n, data[n]))
        # s_data = data[n].split()[3]
        # print('{:.3e}'.format(float(s_data.split('E')[0])*10**(float(s_data.split('E')[1]))))
        # print('{:.3e}'.format(float(s_data)))
        # res_data.append(s_data)
        n = 11
        s_data = data[n].split()[3]
        # res_data.append(s_data)
        # return res_data
        return s_data

    def get_data(self, num=1):
        self.inst.write("FData,0,0001,0010")
        time.sleep(0.05)
        # print("Response")
        # print(self.inst.read())

        data = []
        flag = True
        while flag:
            response = self.inst.read()
            if response == "EA":
                continue
            if response == "EN":
                flag = False
            else:
                data.append(response)
        # print('\n'.join(data))

        n = num + 1
        s_data = data[n].split()[3]
        # print(s_data)
        # res_data.append(s_data)
        # return res_data
        return s_data


def main():
    rm = pyvisa.ResourceManager()
    visa_list = rm.list_resources()
    print(visa_list)

    logger = gm10(rm, VISA_ADDRESS)
    logger.test()

    A = np.average([5, 5])

    del logger
    return


if __name__ == "__main__":
    main()
    print("END")

"""
2024/06/07  Version1.0  出射 幹也@09Laser404
"""
