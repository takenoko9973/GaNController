"""----------------------------------------------------------------------
NEA activation program
----------------------------------------------------------------------
"""  # noqa: D205

import datetime
import time

import pyvisa
import serial  # pip3 install pyserial  # noqa: F401

from const import HC_PROTOCOL, NEA_PROTOCOL
from libs.gm10 import gm10
from libs.ibeam import ibeam
from utils.calc import ext_calculation_pressure, sip_calculation_pressure
from utils.log_file import LogFileManager

# from OphirUSBI import OphirUSBI

# User setting parameter -------------------------------------------------------
COMMENT = ""

LOGGER_RANGE = ["20mV", -5000, 20000]  # 表示範囲: -5 ~ 20 mV

S_TIME = 1  # 測定前の待ち時間(安定化時間: Stabilization time)[s]
INTEGRATED = 1  # 積算回数
INTERVAL = 0  # 積算時の測定間隔[s](0: MW100の設定上の最小となる -> 500 msとか)

"""----------------------------------------------------------------------------------"""
VERSION = 1.0
ENCODE = "utf-8"
PROTOCOL = NEA_PROTOCOL

VISA_GM10 = "TCPIP0::" + "192.168.1.105" + "::" + "34434" + "::SOCKET"
GM10_EXT = 1  # 真空度測定Ch番号
GM10_SIP = 2  # SIP測定Ch番号
GM10_PC = 10  # フォトカレント測定Ch番号
GM10_HV = 22  # HV制御出力Ch番号
GM10_TC = -1  # TC測定Ch番号

COM_IBEAM = 3
WAVELENGTH = 406  # nm
LASER_POWER = 120  # mW

# 100 mW, FilterInでの測定結果: 164 μW
# 10 mW, FilterInでの測定結果: 70 μW
LP_PV = 164 * 10 ** (-6)

HV = 500  # V

LOG_DIR = "logs"

GET_DATA = [
    "Time[s]",
    "LP(PV)[W]",  # Laser power (PV)
    "QE[%]",  # Quantum efficiency
    "PC[A]",  # Photocurrent
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

TZ = datetime.timezone(datetime.timedelta(hours=9))

USE_LASER = False
if not USE_LASER:
    COMMENT += "405nm15mW,BG=0.7mV"
    WAVELENGTH = 405  # nm
    LASER_POWER = 15  # mW
    # VP>>試料: 実際に試料に照射されるパワー10 mWと仮定
    LP_PV = 10 * 10 ** (-3)

    BG_PC = 0.7 * 10 ** (-3)  # V

"""----------------------------------------------------------------------------------"""


def main() -> None:
    print(f"NEA activation program (Version: {VERSION})")

    # 機器との接続 ------------------------------------------------------------ #
    rm = pyvisa.ResourceManager()
    logger = gm10(rm, VISA_GM10)

    wl = WAVELENGTH
    if USE_LASER:
        laser = ibeam(f"COM{COM_IBEAM}")
        laser.ch_on(2)
        laser.set_lp(2, LASER_POWER)

    log_file_manager = LogFileManager(LOG_DIR)

    latest_log = log_file_manager.get_latest_log_file()
    update_major = latest_log.protocol == HC_PROTOCOL if latest_log is not None else True
    log_file = log_file_manager.create_log_file(PROTOCOL, update_major)

    # --------------------------------------------------------------------- #

    try:
        # 開始時間
        start_time = datetime.datetime.now(TZ)

        log_file.write("#NEA activation monitor\n")
        log_file.write(f"\n#Protocol:\t{log_file.protocol}\n")

        log_file.write("\n#Measurement\n")
        log_file.write(f"#Number:\t{log_file.number}\n")
        log_file.write(f"#Date:\t{start_time.strftime('%Y/%m/%d')}\n")
        log_file.write(f"#Time:\t{start_time.strftime('%H:%M:%S')}\n")
        log_file.write(f"#Encode:\t{ENCODE}\n")
        log_file.write(f"#Version:\t{VERSION}\n")

        log_file.write("\n#Condition\n")
        log_file.write(f"#Wavelength:\t{wl:d}[nm]\n")
        log_file.write(f"#LaserPower(SV):\t{LASER_POWER:d}[mW]\n")

        log_file.write(f"#StabilizationTime:\t{S_TIME:.1f}[s]\n")
        log_file.write(f"#IntegratedTimes:\t{INTEGRATED:.1f}[-]\n")
        log_file.write(f"#IntervalTime:\t{INTERVAL:.1f}[s]\n")
        log_file.write(f"#ExtractionVoltage:\t{HV:d}[V]\n")

        log_file.write("\n#Comment\n")
        log_file.write(f"#{COMMENT}\n")

        log_file.write("\n#Data\n")
        log_file.write("\t".join(GET_DATA) + "\n")

        print(
            "\033[32m"
            + "{:s}\nExperiment start".format(start_time.strftime("%Y/%m/%d %H:%M:%S"))
            + "\033[0m"
        )

        while 1:
            current_time = datetime.datetime.now(TZ)

            t = (current_time - start_time).total_seconds()
            print("\033[32m" + f"{t:.1f}[s]\t" + "\033[0m")

            if USE_LASER:
                laser.laser_on()

            time.sleep(S_TIME)

            # bpc_all = logger.PhotocurrentMeasurement(pc_ch, shunt_r, INTEGRATED, INTERVAL, 0)
            # bpc = bpc_all[0]
            # blp = float(powermeter.read_data()) * ratio
            # logger_range = logger.GetInputChSetting(pc_ch)[0]['Range']
            bright_data = float(logger.get_data(GM10_PC))

            # """

            if USE_LASER:
                laser.laser_off()

            time.sleep(S_TIME)

            dark_data = float(logger.get_data(GM10_PC)) if USE_LASER else BG_PC

            # dpc_all = logger.PhotocurrentMeasurement(pc_ch, shunt_r, INTEGRATED, INTERVAL, 0)
            # dpc = dpc_all[0]
            # dlp = float(powermeter.read_data()) * ratio
            # """

            # get_pc = bpc - dpc
            # get_lp = blp - dlp
            # qe = 1240 * get_pc / (wl * get_lp) * 100

            pressure_ext = ext_calculation_pressure(float(logger.get_data(GM10_EXT)))
            pressure_sip = sip_calculation_pressure(float(logger.get_data(GM10_SIP)))

            # spot_area = math.pi*(spot_size*10**(-4)/2)**2 #[cm^2]
            # pd = get_lp / spot_area
            # cd = get_pc / spot_area

            # get_tc = logger.GetMeasurementData(tc_ch)['Value']

            pc = ((bright_data - dark_data) * 10 ** (-3)) / 10000
            qe = 1240 * pc / (wl * LP_PV) * 100

            print(f"{qe:.3e}%, {pressure_ext:.2e} Pa(EXT)")

            event = ""
            get_data = [
                f"{t:.1f}",
                f"{LP_PV:.4E}",  # Laser power (PV)
                f"{qe:.4E}",  # Quantum efficiency
                f"{pc:.4E}",  # Photocurrent
                f"{pressure_ext:.4E}",
                f"{pressure_sip:.4E}",
                f"{bright_data}",  # Bright photocurrent
                f"{dark_data}",  # Dark photocurrent
                #'{:.4E}'.format(blp), #Bright laser power
                #'{:.4E}'.format(dlp), #Dark laser power
                #'{:.2E}'.format(pd), #Power density
                #'{:.2E}'.format(cd), #Current density
                f"{event}",  # Event
                #'{}'.format(logger_range),
                #'{:.2f}'.format(get_tc)]
                # bpc_all[2],
                # dpc_all[2]
            ]

            data = "\t".join(get_data)
            log_file.write(data + "\n")

    except Exception as e:  # noqa: BLE001
        print("Error stop:", e)

    finally:
        # print("End:\tQE={:.4E}%, Pc={:.4E} A @{:.4E} W".format(qe, get_pc, get_lp))
        # print("\tPD={:.2E} W/cm^2, CD={:.2E} A/cm^2".format(pd, cd))

        del logger
        del log_file
        # del(powermeter)

        if USE_LASER == 1:
            laser.set_lp(2, 0)
            laser.laser_off()
            laser.ch_off(2)
            del laser

        # print("End: QE={:.3E}%, Pc={:.2E} A".format(QE, Photocurrent))
        finish_time = datetime.datetime.now(TZ)
        print(
            "\033[31m" + "{:s} Finish".format(finish_time.strftime("%Y/%m/%d %H:%M:%S")) + "\033[0m"
        )


if __name__ == "__main__":
    main()

"""
20250415 Version1.0 Created a program @出射 幹也

"""
