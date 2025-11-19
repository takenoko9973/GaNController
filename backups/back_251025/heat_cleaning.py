"""----------------------------------------------------------------------
MPES-15000
Heat Cleaning program
----------------------------------------------------------------------
"""  # noqa: D205

import datetime
import sys
import time

import pyvisa

from const import HC_PROTOCOL
from libs.gm10 import gm10
from libs.pfr_100l50 import pfr_100l50
from libs.pwux import pwux
from utils.calc import ext_calculation_pressure, sip_calculation_pressure
from utils.log_file import LogFile, LogFileManager
from utils.sequence import Decrease, HeatCleaning, Rising, Sequence, Wait

# User setting parmeters -----------------------------------------------------

VERSION = 1.0
ENCODE = "utf-8"

COMMENT = ""
WAIT_TIME = 0  # 開始時間を遅らせる(不要なら0にすること)

AMD_DEGAS = 1  # 0: なし, 1: デガス

"""
シーケンス設定 I=A・[Time]^[Exponent]
    [時間(second), Command, Exponent]
     Command: r >> 昇温, c >> HC(維持), d >> 降温, w >> 待機
"""
INITIAL_CURRENT = 0.0  # A 初期ヒーター電流値

SEQUENCE_TIME = 1
SEQUENCE: list[Sequence] = [
    # Rising(3600 * 2, 0.33),  # ベーキング用
    # HeatCleaning(3600 * 15, 0.33),  # ベーキング用
    # HeatCleaning(3600 * 7, 0.33),  # ベーキング用
    Rising(3600 * 1, 0.33),
    HeatCleaning(3600 * 1, 0.33),
    Decrease(3600 * 0.5, 0.33),
    Wait(3600 * 7.5, 0.33),
] * SEQUENCE_TIME

HC_CURRENT = 3.5
# HC_CURRENT = 3.0  # ベーキング用
# HC_CURRENT = 5.3  # NEG用
AMD_CURRENT = 3.0
# AMD_CURRENT = 0.0

STEP_TIME = 10  # second ステップ時間

NUMBER_RESET = True
SET_PROTOCOL = HC_PROTOCOL
# SET_PROTOCOL = "HD"

# Setting parmeters -----------------------------------------------------
GM10_VISA = "TCPIP0::" + "192.168.1.105" + "::" + "34434" + "::SOCKET"
GM10_CH_EXT = 1  # Logger 真空計測定チャンネル番号
GM10_CH_SIP = 2  # Logger SIP測定Ch番号
GM10_CH_TC = -1  # Logger TC測定チャンネル番号

# Heater power supply
HPS_VISA = "TCPIP0::" + "192.168.1.111" + "::" + "2268" + "::SOCKET"
HPS_UNIT = 0
HPS_V_LIMIT = 18  # 最大印加電圧[V]
HPS_OVP = 19  # 過電圧保護値[V]
HPS_OCP = 10  # 過電流保護値[A]

# AMD
APS_VISA = "TCPIP0::" + "192.168.1.112" + "::" + "2268" + "::SOCKET"
APS_UNIT = 0
APS_V_LIMIT = 18  # 最大印加電圧[V]
APS_OVP = 19  # 過電圧保護値[V]
APS_OCP = 5  # 過電流保護値[A]

PWUX_COM = 1  # デバイスマネージャーで確認

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

TZ = datetime.timezone(datetime.timedelta(hours=9))

# ----------------------------------------------------------------------


def wait(dt: float) -> None:
    st = datetime.datetime.now(TZ)
    t = 0.0

    while t < dt:
        sys.stdout.write(f"\rWait for{dt - t:6.0f} s")
        sys.stdout.flush()
        time.sleep(1)
        t = (datetime.datetime.now(TZ) - st).total_seconds()

    sys.stdout.write(f"\rWait for{0:6.0f} s")
    sys.stdout.flush()
    print()


def write_log(
    log_file: LogFile,
    sequence: Sequence,
    time: float,
    hps: pfr_100l50,
    logger: gm10,
    rt: pwux | None,
    aps: pfr_100l50 | None,
) -> None:
    hps_set_c = hps.get_output(0)
    hps_set_v = hps.get_output(1)
    hps_pw = float(hps_set_v) * float(hps_set_c)

    ext_monitor = logger.get_data(GM10_CH_EXT)
    ext_pressure = ext_calculation_pressure(float(ext_monitor))
    sip_monitor = logger.get_data(GM10_CH_SIP)
    sip_pressure = sip_calculation_pressure(float(sip_monitor))

    rt_temp = rt.get_temp() if rt else -1.0

    log_data = [
        f"{time:.1f}",
        f"{hps_set_v:.3f}",
        f"{hps_set_c:.3f}",
        f"{hps_pw:.2f}",
        f"{rt_temp:.1f}",
        f"{ext_pressure:.2E}",
        f"{sip_pressure:.2E}",
    ]

    if AMD_DEGAS == 1 and aps is not None:
        aps_set_c = aps.get_output(0)
        aps_set_v = aps.get_output(1)
        aps_pw = float(aps_set_v) * float(aps_set_c)

        log_data.append(f"{aps_set_v:.3f}")
        log_data.append(f"{aps_set_c:.3f}")
        log_data.append(f"{aps_pw:.2f}")

    log_file.write("\t".join(log_data) + "\n")

    sys.stdout.write(
        f"\r{sequence.mode_init}, {time:7.1f}[s], {hps_set_v:.3f}[V], {hps_set_c:.3f}[A], "
        f"{rt_temp:.1f}[deg.C], {ext_pressure:.2E}[Pa], {sip_pressure:.2E}[Pa]"
    )
    sys.stdout.flush()


def main() -> None:  # noqa: C901, PLR0912, PLR0915
    wait(WAIT_TIME)
    rm = pyvisa.ResourceManager()

    try:
        # logger = MW100.MW100(rm, LOGGER_VISA)
        hps = pfr_100l50(rm, HPS_VISA)
        # hps.SetOVP(HPS_UNIT, 2, HPS_OVP)
        # hps.SetOCP(HPS_UNIT, 2, HPS_OCP)

        aps = None
        if AMD_DEGAS == 1:
            aps = pfr_100l50(rm, APS_VISA)
            # aps.SetOVP(APS_UNIT, 2, APS_OVP)
            # aps.SetOCP(APS_UNIT, 2, APS_OCP)

        visa_list = rm.list_resources()
        print(visa_list)
        # rt = pwux(rm, visa_list[PWUX_COM - 1])
        rt = None
        logger = gm10(rm, GM10_VISA)

    except pyvisa.VisaIOError as e:
        print(e)
        sys.exit()
    except OSError as e:
        print(e)
        sys.exit()

    try:
        start_time = datetime.datetime.now(TZ)
        print("HC program")
        print(
            "\033[32m" + "{:s} Start".format(start_time.strftime("%Y/%m/%d %H:%M:%S")) + "\033[0m"
        )

        log_file_manager = LogFileManager(LOG_DIR)
        log_file = log_file_manager.create_log_file(SET_PROTOCOL, NUMBER_RESET)

        # -------------------------------------------------------------------------

        log_file.write("#Heat Cleaning monitor\n")

        log_file.write(f"\n#Protocol:\t{log_file.protocol}\n")

        log_file.write("\n#Measurement\n")
        log_file.write(f"#Number:\t{log_file.number}\n")
        log_file.write(f"#Date:\t{start_time.strftime('%Y/%m/%d')}\n")
        log_file.write(f"#Time:\t{start_time.strftime('%H:%M:%S')}\n")
        log_file.write(f"#ProgramVersion:\t{VERSION}\n")
        log_file.write(f"#Encode:\t{ENCODE}\n")

        log_file.write("\n#Condition\n")
        # log_file.write('#HeaterVoltageLimit:\t{}[V]\n'.format(HPS_V_LIMIT))
        # log_file.write('#InitialCurrent:\t{:.2f}[A]\n'.format(INITIAL_CURRENT))
        log_file.write(f"#HC_CURRENT:\t{HC_CURRENT}[A]\n")
        if AMD_DEGAS == 1:
            log_file.write(f"#AMD_CURRENT:\t{AMD_CURRENT}[A]\n")
        for index, sequence in enumerate(SEQUENCE):
            log_file.write(f"#Sequence{index + 1}: {sequence}\n")

        log_file.write("\n#Comment\n")
        log_file.write(f"#{COMMENT}\n")

        log_file.write("\n#Data\n")
        if AMD_DEGAS == 1:
            log_file.write("\t".join(GET_DATA) + "\n")
        else:
            log_file.write("\t".join(GET_DATA[:-3]) + "\n")

        hc_current = INITIAL_CURRENT
        hps.set_voltage(HPS_V_LIMIT)
        hps.set_current(hc_current)
        hps.set_output(1)

        if AMD_DEGAS == 1 and aps is not None:
            amd_current = INITIAL_CURRENT
            aps.set_voltage(APS_V_LIMIT)
            aps.set_current(amd_current)
            aps.set_output(1)

        sequence_start = datetime.datetime.now(TZ)
        t = 0.0

        # [電流値, 時間(second), Command, Exponent]
        for index, sequence in enumerate(SEQUENCE):
            step_start = t

            print(f"Sequence{index + 1}: {sequence}")
            print(sequence.mode_name)

            while (t - step_start) <= sequence.duration_second:
                hc_current = sequence.current(HC_CURRENT, t - step_start)
                hps.set_current(hc_current)

                if AMD_DEGAS == 1 and aps is not None:
                    amd_current = sequence.current(AMD_CURRENT, t - step_start)
                    aps.set_current(amd_current)

                write_log(log_file, sequence, t, hps, logger, rt, aps)

                time.sleep(STEP_TIME)
                t = (datetime.datetime.now(TZ) - sequence_start).total_seconds()

            hc_current = sequence.current(HC_CURRENT, t - step_start)
            hps.set_current(hc_current)

            if AMD_DEGAS == 1 and aps is not None:
                amd_current = sequence.current(AMD_CURRENT, t - step_start)
                aps.set_current(amd_current)

            print("\n")

    except Exception as e:  # noqa: BLE001
        print("\n")
        print(e)

    finally:
        """終わったら電源を閉じる処理をする。"""
        hps.set_output(0)
        del hps
        # del(rt)

        if AMD_DEGAS == 1 and aps is not None:
            aps.set_output(0)
            del aps

        del log_file

        finish_time = datetime.datetime.now(TZ)
        print(
            "\033[31m" + "{:s} Finish".format(finish_time.strftime("%Y/%m/%d %H:%M:%S")) + "\033[0m"
        )


if __name__ == "__main__":
    main()

""" ----------------------------------------------------------------------
20250409 Version1.0 Created a program @Idei
---------------------------------------------------------------------- """
