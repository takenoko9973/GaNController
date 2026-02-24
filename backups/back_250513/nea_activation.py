# -*- coding: utf-8 -*-
"""----------------------------------------------------------------------
NEA activation program
----------------------------------------------------------------------"""

from datetime import datetime
import time
import pyvisa
import serial  # pip3 install pyserial

from libs.gm10 import gm10
from libs.ibeam import ibeam
# from OphirUSBI import OphirUSBI

# User setting parameter -------------------------------------------------------
NUMBER = "7.1"
COMMENT = ""

LOGGER_RANGE = ["20mV", -5000, 20000]  # 表示範囲: -5 ~ 20 mV

S_TIME = 1  # 測定前の待ち時間(安定化時間: Stabilization time)[s]
INTEGRATED = 1  # 積算回数
INTERVAL = 0  # 積算時の測定間隔[s](0: MW100の設定上の最小となる -> 500 msとか)

"""----------------------------------------------------------------------------------"""
VERSION = 1.0
ENCODE = "utf-8"
PROTOCOL = "NEA"

VISA_GM10 = "TCPIP0::" + "192.168.1.105" + "::" + "34434" + "::SOCKET"
GM10_PC = 10  # フォトカレント測定Ch番号
GM10_EXT = 1  # 真空度測定Ch番号
GM10_HV = 22  # HV制御出力Ch番号
GM10_SIP = 2  # SIP測定Ch番号
GM10_TC = 2  # TC測定Ch番号

IBEAM_COM = 3
WAVELENGTH = 406  # nm
LASER_POWER = 120  # mW

# 100 mW, FilterInでの測定結果: 164 μW
# 10 mW, FilterInでの測定結果: 70 μW
LP_PV = 164 * 10 ** (-6)

HV = 100  # V

LOG_DIR = "logs"

GET_DATA = [
    "Time[s]",
    #'LP(PV)[W]', #Laser power (PV)
    #'QE[%]', #Quantum efficiency
    #'PC[A]', #Photocurrent
    "Pressure(EXT)[Pa]",
    "Pressure(SIP)[Pa]",
    "BPc[A]",  # Bright photocurrent
    "DPc[A]",  # Dark photocurrent
    #'BLP[W]', #Bright laser power
    #'DLP[W]', #Dark laser power
    #'PD[W/cm^2]', #Power density
    #'CD[A/cm^2]', #Current density
    "Event",
    #'Range',
    #'TC[deg.C]']
    #'BPcAll[A]',
    #'DPcAll[A]']
]

FF = 0
if FF == 0:
    COMMENT += "405nm15mW,BG=0.7mV"
    WAVELENGTH = 405  # nm
    LASER_POWER = 15  # mW
    # VP>>試料: 実際に試料に照射されるパワー10 mWと仮定
    LP_PV = 10 * 10 ** (-3)

    BG_PC = 0.7 * 10 ** (-3)  # V

"""----------------------------------------------------------------------------------"""


def isfloat(value):
    try:
        float(value)
    except ValueError:
        return False
    else:
        return True


def ext_calculation_pressure(value):
    return 10 ** (float(value) - 10)


def sip_calculation_pressure(value):
    # V = 2(log(Pa) - log(Pa(0))) Pa(0)はSIPの種類による(マニュアル参照)
    return 5 * 10 ** (-7) * (10 ** (float(value))) ** (1 / 2)


def main():
    print("NEA activation program (Version: {})".format(VERSION))

    flag = "y"
    if flag == "y":
        today = datetime.today()

        # 機器との接続 ------------------------------------------------------------ #
        rm = pyvisa.ResourceManager()
        logger = gm10(rm, VISA_GM10)

        if FF == 1:
            laser = ibeam("COM{}".format(IBEAM_COM))

        wl = WAVELENGTH

        if FF == 1:
            laser.ch_on(2)
            laser.set_lp(2, LASER_POWER)

        start_time = datetime.now()

        file_name = "{}/[{}]{}-{:s}.dat".format(
            LOG_DIR, NUMBER, PROTOCOL, start_time.strftime("%Y%m%d%H%M%S")
        )

        # --------------------------------------------------------------------- #

        try:
            with open(file_name, "a", encoding=ENCODE) as file:
                file.write("#NEA activation monitor\n")
                file.write("\n#Protocol:\t{}\n".format(PROTOCOL))

                file.write("\n#Measurement\n")
                file.write("#Number:\t{}\n".format(NUMBER))
                file.write("#Date:\t{0:s}\n".format(today.strftime("%Y/%m/%d")))
                file.write("#Time:\t{0:s}\n".format(today.strftime("%H:%M:%S")))
                file.write("#Encode:\t{}\n".format(ENCODE))
                file.write("#Version:\t{}\n".format(VERSION))

                file.write("\n#Condition\n")
                file.write("#Wavelength:\t{:d}[nm]\n".format(wl))
                file.write("#LaserPower(SV):\t{:d}[mW]\n".format(LASER_POWER))

                file.write("#StabilizationTime:\t{:.1f}[s]\n".format(S_TIME))
                file.write("#IntegratedTimes:\t{:.1f}[-]\n".format(INTEGRATED))
                file.write("#IntervalTime:\t{:.1f}[s]\n".format(INTERVAL))
                file.write("#ExtractionVoltage:\t{:d}[V]\n".format(HV))

                file.write("\n#Comment\n")
                file.write("#{}\n".format(COMMENT))

                file.write("\n#Data\n")
                file.write("\t".join(GET_DATA) + "\n")

                print(
                    "\033[32m"
                    + "{0:s}\nExperiment start".format(
                        start_time.strftime("%Y/%m/%d %H:%M:%S")
                    )
                    + "\033[0m"
                )
                start_time = datetime.now()  # 測定の開始時間

                while 1:
                    current_time = datetime.now()
                    get_time = (current_time - start_time).total_seconds()
                    print("\033[32m" + "{0:.1f}[s]\t".format(get_time) + "\033[0m")

                    if FF == 1:
                        laser.laser_on()

                    time.sleep(S_TIME)
                    # bpc_all = logger.PhotocurrentMeasurement(pc_ch, shunt_r, INTEGRATED, INTERVAL, 0)
                    # bpc = bpc_all[0]
                    # blp = float(powermeter.read_data()) * ratio
                    # logger_range = logger.GetInputChSetting(pc_ch)[0]['Range']
                    b_data = logger.test()
                    # """

                    if FF == 1:
                        laser.laser_off()
                        time.sleep(S_TIME)
                        d_data = logger.test()
                    else:
                        time.sleep(S_TIME)
                        d_data = BG_PC

                    # dpc_all = logger.PhotocurrentMeasurement(pc_ch, shunt_r, INTEGRATED, INTERVAL, 0)
                    # dpc = dpc_all[0]
                    # dlp = float(powermeter.read_data()) * ratio
                    # """

                    # get_pc = bpc - dpc
                    # get_lp = blp - dlp
                    # qe = 1240 * get_pc / (wl * get_lp) * 100

                    get_ext = ext_calculation_pressure(logger.get_data(GM10_EXT))
                    get_sip = sip_calculation_pressure(logger.get_data(GM10_SIP))

                    # spot_area = math.pi*(spot_size*10**(-4)/2)**2 #[cm^2]
                    # pd = get_lp / spot_area
                    # cd = get_pc / spot_area

                    # get_tc = logger.GetMeasurementData(tc_ch)['Value']

                    # print("\t{:.3E}[%]\t{:.2E}[Pa]".format(qe, get_ext))
                    event = ""
                    get_data = [
                        "{:.1f}".format(get_time),
                        #'{:.4E}'.format(get_lp), #Laser power (PV)
                        #'{:.4E}'.format(qe), #Quantum efficiency
                        #'{:.4E}'.format(get_pc), #Photocurrent
                        "{:.4E}".format(get_ext),
                        "{:.4E}".format(get_sip),
                        "{}".format(b_data),  # Bright photocurrent
                        "{}".format(d_data),  # Dark photocurrent
                        #'{:.4E}'.format(blp), #Bright laser power
                        #'{:.4E}'.format(dlp), #Dark laser power
                        #'{:.2E}'.format(pd), #Power density
                        #'{:.2E}'.format(cd), #Current density
                        "{}".format(event),  # Event
                        #'{}'.format(logger_range),
                        #'{:.2f}'.format(get_tc)]
                        # bpc_all[2],
                        # dpc_all[2]
                    ]

                    pc = ((float(b_data) - float(d_data)) * 10 ** (-3)) / 10000
                    qe = 1240 * pc / (wl * LP_PV) * 100
                    print("{:.3e}%, {:.2e} Pa(EXT)".format(qe, get_ext))

                    data = "\t".join(get_data)
                    file.write(data + "\n")
                    file.flush()

        except Exception as e:
            print("Error stop:", e)

        finally:
            # print("End:\tQE={:.4E}%, Pc={:.4E} A @{:.4E} W".format(qe, get_pc, get_lp))
            # print("\tPD={:.2E} W/cm^2, CD={:.2E} A/cm^2".format(pd, cd))

            del logger
            # del(powermeter)

            if FF == 1:
                laser.set_lp(2, 0)
                laser.laser_off()
                laser.ch_off(2)
                del laser

            # print("End: QE={:.3E}%, Pc={:.2E} A".format(QE, Photocurrent))
            print(
                "\033[31m"
                + "{0:s} Finish".format(datetime.now().strftime("%Y/%m/%d %H:%M:%S"))
                + "\033[0m"
            )


if __name__ == "__main__":
    main()
    pass

"""
20250415 Version1.0 Created a program @出射 幹也

"""
