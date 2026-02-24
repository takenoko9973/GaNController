# -*- coding: utf-8 -*-
"""----------------------------------------------------------------------
MPES-15000
Heat Cleaning program
----------------------------------------------------------------------"""

import pyvisa
import sys

from datetime import datetime
import time

from libs.gm10 import gm10
import libs.pfr_100l50 as pfr_100l50
from libs.pwux import pwux

# User setting parmeters -----------------------------------------------------

VERSION = 1.0
PROTOCOL = "HC"
ENCODE = "utf-8"

NUMBER = "7.2"
COMMENT = ""
WAIT_TIME = 0  # 開始時間を遅らせる(不要なら0にすること)

AMD_DEGAS = 1  # 0: なし, 1: デガス

"""
シーケンス設定 I=A・[Time]^[Exponent]
    [時間(second), Command, Exponent]
     Command: r >> 昇温, c >> HC(維持), d >> 降温, w >> 待機
#"""
INITIAL_CURRENT = 0.0  # A 初期ヒーター電流値
SEQUENCE = [
    [3600 * 1, "r", 0.33],
    [3600 * 1, "c", 0.33],
    [3600 * 0.5, "d", 0.33],
    [3600 * 7.5, "w", 0.33],
]
SEQUENCE_TIME = 1

SEQUENCE *= SEQUENCE_TIME

HC_CURRENT = 6.0
AMD_CURRENT = 3.0

STEP_TIME = 10  # second ステップ時間

# Setting parmeters -----------------------------------------------------
GM10_VISA = "TCPIP0::" + "192.168.1.105" + "::" + "34434" + "::SOCKET"
CH_EXT = 1  # Logger 真空計測定チャンネル番号
CH_SIP = 2  # Logger SIP測定Ch番号
CH_TC = 2  # Logger TC測定チャンネル番号

HPS_VISA = "TCPIP0::" + "192.168.1.111" + "::" + "2268" + "::SOCKET"
HPS_UNIT = 0
HPS_V_LIMIT = 18  # 最大印加電圧[V]
HPS_OVP = 19  # 過電圧保護値[V]
HPS_OCP = 10  # 過電流保護値[A]

APS_VISA = "TCPIP0::" + "192.168.1.112" + "::" + "2268" + "::SOCKET"
APS_UNIT = 0
APS_V_LIMIT = 18  # 最大印加電圧[V]
APS_OVP = 19  # 過電圧保護値[V]
APS_OCP = 5  # 過電流保護値[A]

PWUX_COM = 1  # デバイスマネージャーで確認


def ext_calculation_pressure(value):
    return 10 ** (value - 10)


def sip_calculation_pressure(value):
    # V = 2(log(Pa) - log(Pa(0))) Pa(0)はSIPの種類による(マニュアル参照)
    return 5 * 10 ** (-7) * (10 ** (value)) ** (1 / 2)


LOG_DIR = "logs"

GET_DATA = [
    "Time[s]",
    "Volt[V]",
    "Current[A]",
    "Power[W]",
    "Temp(TC)[deg.C]",
    "Pressure(EXT)[Pa]",
    "Pressure(SIP)[Pa]",
    "Volt(AMD)[V]",
    "Current(AMD)[A]",
    "Power(AMD)[W]",
]
# ----------------------------------------------------------------------


def wait(dt):
    st = datetime.now()
    t = 0.0
    while t < dt:
        sys.stdout.write("\rWait for{:6.0f} s".format(dt - t))
        sys.stdout.flush()
        time.sleep(1)
        t = (datetime.now() - st).total_seconds()
    sys.stdout.write("\rWait for{:6.0f} s".format(0))
    sys.stdout.flush()
    print("")

def write_data():
    

def main():
    global PROTOCOL
    wait(WAIT_TIME)
    rm = pyvisa.ResourceManager()

    try:
        # logger = MW100.MW100(rm, LOGGER_VISA)
        hps = pfr_100l50.pfr_100l50(rm, HPS_VISA)
        # hps.SetOVP(HPS_UNIT, 2, HPS_OVP)
        # hps.SetOCP(HPS_UNIT, 2, HPS_OCP)

        if AMD_DEGAS == 1:
            aps = pfr_100l50.pfr_100l50(rm, APS_VISA)
            # aps.SetOVP(APS_UNIT, 2, APS_OVP)
            # aps.SetOCP(APS_UNIT, 2, APS_OCP)

        visa_list = rm.list_resources()
        print(visa_list)
        rt = pwux(rm, visa_list[PWUX_COM - 1])
        logger = gm10(rm, GM10_VISA)

    except pyvisa.VisaIOError as e:
        print(e)
        sys.exit()
    except IOError as e:
        print(e)
        sys.exit()

    try:
        current_time = time.time()
        print("HC program")
        print(
            "\033[32m"
            + "{0:s} Start".format(
                datetime.fromtimestamp(current_time).strftime("%Y/%m/%d %H:%M:%S")
            )
            + "\033[0m"
        )

        start_time = datetime.now()
        file_name = "{}/[{}]HC-{:s}.dat".format(
            LOG_DIR, NUMBER, start_time.strftime("%Y%m%d%H%M")
        )

        with open(file_name, "a", encoding=ENCODE) as file:
            file.write("#Heat Cleaning monitor\n")

            file.write("\n#Protocol:\t{}\n".format(PROTOCOL))

            file.write("\n#Measurement\n")
            file.write("#Number:\t{}\n".format(NUMBER))
            file.write("#Date:\t{0:s}\n".format(start_time.strftime("%Y/%m/%d")))
            file.write("#Time:\t{0:s}\n".format(start_time.strftime("%H:%M:%S")))
            file.write("#ProgramVersion:\t{}\n".format(VERSION))
            file.write("#Encode:\t{}\n".format(ENCODE))

            file.write("\n#Condition\n")
            # file.write('#HeaterVoltageLimit:\t{}[V]\n'.format(HPS_V_LIMIT))
            # file.write('#InitialCurrent:\t{:.2f}[A]\n'.format(INITIAL_CURRENT))
            file.write("#HC_CURRENT:\t{}[A]\n".format(HC_CURRENT))
            if AMD_DEGAS == 1:
                file.write("#AMD_CURRENT:\t{}[A]\n".format(AMD_CURRENT))
            for index, value in enumerate(SEQUENCE):
                file.write("#Sequence{}: {}\n".format(index + 1, value))

            file.write("\n#Comment\n")
            file.write("#{}\n".format(COMMENT))

            file.write("\n#Data\n")
            if AMD_DEGAS == 1:
                file.write("\t".join(GET_DATA) + "\n")
            else:
                file.write("\t".join(GET_DATA[:-3]) + "\n")

            hc_current = INITIAL_CURRENT

            hps.set_voltage(HPS_V_LIMIT)
            hps.set_current(hc_current)
            hps.set_output(1)

            if AMD_DEGAS == 1:
                amd_current = INITIAL_CURRENT
                aps.set_voltage(APS_V_LIMIT)
                aps.set_current(amd_current)
                aps.set_output(1)

            sequence_start = datetime.now()
            t = 0.0
            step_start = 0.0

            # [電流値, 時間(second), Command, Exponent]
            for index, value in enumerate(SEQUENCE):
                print("Sequence{}: {}".format(index + 1, value))

                if value[1] == "r":  # 昇温 I=[hc_c]×t^[Exponent]+StartCurrent
                    print("Rising")
                    hc_start_current = hc_current
                    hc_c = (HC_CURRENT - hc_start_current) / (
                        value[0] ** value[2]
                    )  # 指定した時間で、設定電流値に到達するための係数(Coefficient)
                    if AMD_DEGAS == 1:
                        amd_start_current = amd_current
                        amd_c = (AMD_CURRENT - amd_start_current) / (
                            value[0] ** value[2]
                        )

                    while (t - step_start) <= value[0]:
                        hc_current = (
                            hc_c * ((t - step_start) ** value[2])
                        ) + hc_start_current
                        hps.set_current(hc_current)
                        
                        hps_set_c = hps.get_output(0)
                        hps_set_v = hps.get_output(1)
                        hps_pw = float(hps_set_v) * float(hps_set_c)

                        ext_monitor = logger.get_data(CH_EXT)
                        ext_pressure = ext_calculation_pressure(float(ext_monitor))
                        sip_monitor = logger.get_data(CH_SIP)
                        sip_pressure = sip_calculation_pressure(float(sip_monitor))
                        rt_temp = rt.get_temp()

                        get_data = [
                            "{:.1f}".format(t),
                            "{}".format(hps_set_v),
                            "{}".format(hps_set_c),
                            "{:.2f}".format(hps_pw),
                            "{}".format(rt_temp),
                            "{:.2E}".format(ext_pressure),
                            "{:.2E}".format(sip_pressure),
                        ]

                        if AMD_DEGAS == 1:
                            amd_current = (
                                amd_c * ((t - step_start) ** value[2])
                            ) + amd_start_current
                            aps.set_current(amd_current)
                            aps_set_c = aps.get_output(0)
                            aps_set_v = aps.get_output(1)
                            aps_pw = float(aps_set_v) * float(aps_set_c)

                            get_data.append("{}".format(aps_set_v))
                            get_data.append("{}".format(aps_set_c))
                            get_data.append("{:.2f}".format(aps_pw))

                        file.write("\t".join(get_data) + "\n")
                        file.flush()

                        sys.stdout.write(
                            "\r{:6.1f}[s], {}[V], {}[A], {}[deg.C], {:.2E}[Pa], {:.2E}[Pa]".format(
                                t,
                                hps_set_v,
                                hps_set_c,
                                rt_temp,
                                ext_pressure,
                                sip_pressure,
                            )
                        )
                        sys.stdout.flush()

                        time.sleep(STEP_TIME)
                        t = (datetime.now() - sequence_start).total_seconds()

                    hc_current = HC_CURRENT
                    hps.set_current(hc_current)
                    if AMD_DEGAS == 1:
                        amd_current = AMD_CURRENT
                        aps.set_current(amd_current)

                    step_start = t
                    # print('\n', end='')
                    print("\n")

                elif value[1] == "c":  # Heat cleaning(維持)
                    print("Heat cleaning")

                    hc_current = HC_CURRENT
                    hps.set_current(hc_current)
                    if AMD_DEGAS == 1:
                        amd_current = AMD_CURRENT
                        aps.set_current(amd_current)

                    while (t - step_start) <= value[0]:
                        hps_set_c = hps.get_output(0)
                        hps_set_v = hps.get_output(1)
                        hps_pw = float(hps_set_v) * float(hps_set_c)

                        ext_monitor = logger.get_data(CH_EXT)
                        ext_pressure = ext_calculation_pressure(float(ext_monitor))
                        sip_monitor = logger.get_data(CH_SIP)
                        sip_pressure = sip_calculation_pressure(float(sip_monitor))
                        rt_temp = rt.get_temp()

                        get_data = [
                            "{:.1f}".format(t),
                            "{}".format(hps_set_v),
                            "{}".format(hps_set_c),
                            "{:.2f}".format(hps_pw),
                            "{}".format(rt_temp),
                            "{:.2E}".format(ext_pressure),
                            "{:.2E}".format(sip_pressure),
                        ]

                        if AMD_DEGAS == 1:
                            aps_set_c = aps.get_output(0)
                            aps_set_v = aps.get_output(1)
                            aps_pw = float(aps_set_v) * float(aps_set_c)

                            get_data.append("{}".format(aps_set_v))
                            get_data.append("{}".format(aps_set_c))
                            get_data.append("{:.2f}".format(aps_pw))

                        file.write("\t".join(get_data) + "\n")
                        file.flush()

                        sys.stdout.write(
                            "\r{:6.1f}[s], {}[V], {}[A], {}[deg.C], {:.2E}[Pa], {:.2E}[Pa]".format(
                                t,
                                hps_set_v,
                                hps_set_c,
                                rt_temp,
                                ext_pressure,
                                sip_pressure,
                            )
                        )
                        sys.stdout.flush()

                        time.sleep(STEP_TIME)
                        t = (datetime.now() - sequence_start).total_seconds()

                    step_start = t
                    print("\n")

                elif value[1] == "d":  # 降温 I=-[hc_c]×t+StartCurrent
                    print("Decrease")
                    hc_start_current = hc_current
                    hc_c = (
                        hc_start_current / value[0]
                    )  # DecreaseTime経過後にSetCurrentが0になるための係数
                    if AMD_DEGAS == 1:
                        amd_start_current = amd_current
                        amd_c = amd_start_current / value[0]

                    while (t - step_start) <= value[0]:
                        hc_current = (-1 * hc_c * (t - step_start)) + hc_start_current
                        hps.set_current(hc_current)
                        hps_set_c = hps.get_output(0)
                        hps_set_v = hps.get_output(1)
                        hps_pw = float(hps_set_v) * float(hps_set_c)

                        ext_monitor = logger.get_data(CH_EXT)
                        ext_pressure = ext_calculation_pressure(float(ext_monitor))
                        sip_monitor = logger.get_data(CH_SIP)
                        sip_pressure = sip_calculation_pressure(float(sip_monitor))
                        rt_temp = rt.get_temp()

                        get_data = [
                            "{:.1f}".format(t),
                            "{}".format(hps_set_v),
                            "{}".format(hps_set_c),
                            "{:.2f}".format(hps_pw),
                            "{}".format(rt_temp),
                            "{:.2E}".format(ext_pressure),
                            "{:.2E}".format(sip_pressure),
                        ]

                        if AMD_DEGAS == 1:
                            amd_current = (
                                -1 * amd_c * (t - step_start)
                            ) + amd_start_current
                            aps.set_current(amd_current)
                            aps_set_c = aps.get_output(0)
                            aps_set_v = aps.get_output(1)
                            aps_pw = float(aps_set_v) * float(aps_set_c)

                            get_data.append("{}".format(aps_set_v))
                            get_data.append("{}".format(aps_set_c))
                            get_data.append("{:.2f}".format(aps_pw))

                        file.write("\t".join(get_data) + "\n")
                        file.flush()

                        sys.stdout.write(
                            "\r{:6.1f}[s], {}[V], {}[A], {}[deg.C], {:.2E}[Pa], {:.2E}[Pa]".format(
                                t,
                                hps_set_v,
                                hps_set_c,
                                rt_temp,
                                ext_pressure,
                                sip_pressure,
                            )
                        )
                        sys.stdout.flush()

                        time.sleep(STEP_TIME)
                        t = (datetime.now() - sequence_start).total_seconds()

                    hc_current = 0
                    hps.set_current(hc_current)
                    if AMD_DEGAS == 1:
                        amd_current = 0
                        aps.set_current(amd_current)
                    step_start = t
                    print("\n")

                elif value[1] == "w":  # 待ち時間
                    print("Wait")

                    while (t - step_start) <= value[0]:
                        hps_set_c = hps.get_output(0)
                        hps_set_v = hps.get_output(1)
                        hps_pw = float(hps_set_v) * float(hps_set_c)

                        ext_monitor = logger.get_data(CH_EXT)
                        ext_pressure = ext_calculation_pressure(float(ext_monitor))
                        sip_monitor = logger.get_data(CH_SIP)
                        sip_pressure = sip_calculation_pressure(float(sip_monitor))
                        rt_temp = rt.get_temp()

                        get_data = [
                            "{:.1f}".format(t),
                            "{}".format(hps_set_v),
                            "{}".format(hps_set_c),
                            "{:.2f}".format(hps_pw),
                            "{}".format(rt_temp),
                            "{:.2E}".format(ext_pressure),
                            "{:.2E}".format(sip_pressure),
                        ]

                        if AMD_DEGAS == 1:
                            aps_set_c = aps.get_output(0)
                            aps_set_v = aps.get_output(1)
                            aps_pw = float(aps_set_v) * float(aps_set_c)

                            get_data.append("{}".format(aps_set_v))
                            get_data.append("{}".format(aps_set_c))
                            get_data.append("{:.2f}".format(aps_pw))

                        file.write("\t".join(get_data) + "\n")
                        file.flush()

                        sys.stdout.write(
                            "\r{:6.1f}[s], {}[V], {}[A], {}[deg.C], {:.2E}[Pa], {:.2E}[Pa]".format(
                                t,
                                hps_set_v,
                                hps_set_c,
                                rt_temp,
                                ext_pressure,
                                sip_pressure,
                            )
                        )
                        sys.stdout.flush()

                        time.sleep(STEP_TIME)
                        t = (datetime.now() - sequence_start).total_seconds()

                    print("\n")

    except Exception as e:
        print("\n")
        print(e)

    finally:
        """終わったら電源を閉じる処理をする。"""
        hps.set_output(0)
        del hps
        # del(rt)

        if AMD_DEGAS == 1:
            aps.set_output(0)
        if AMD_DEGAS == 1:
            del aps

        print(
            "\033[31m"
            + "{0:s} Finish".format(datetime.now().strftime("%Y/%m/%d %H:%M:%S"))
            + "\033[0m"
        )


if __name__ == "__main__":
    main()

""" ----------------------------------------------------------------------
20250409 Version1.0 Created a program @Idei
---------------------------------------------------------------------- """
