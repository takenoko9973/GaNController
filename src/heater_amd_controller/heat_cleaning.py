"""----------------------------------------------------------------------
MPES-15000
Heat Cleaning program
----------------------------------------------------------------------
"""  # noqa: D205

import datetime
import sys
import time
from pathlib import Path

import pyvisa

from heater_amd_controller.config import Config
from heater_amd_controller.const import HC_PROTOCOL
from heater_amd_controller.libs.gm10 import gm10
from heater_amd_controller.libs.pfr_100l50 import pfr_100l50
from heater_amd_controller.libs.pwux import pwux
from heater_amd_controller.utils.calc import ext_calculation_pressure, sip_calculation_pressure
from heater_amd_controller.utils.log_file import LogFile, LogManager
from heater_amd_controller.utils.sequence import Decrease, HeatCleaning, Rising, Sequence, Wait

# User setting parmeters -----------------------------------------------------
VERSION = 1.1

COMMENT = ""
WAIT_TIME = 0  # 開始時間を遅らせる(不要なら0にすること)

AMD_DEGAS: bool = True  # False: なし, True: デガス

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

DATE_DIR_UPDATE = False  # 大気開放ごとにアップデート
MAJOR_UPDATE = True  # (主に)加熱洗浄ごとにアップデート
PROTOCOL = HC_PROTOCOL
# PROTOCOL = "HD"

# Setting parameters -----------------------------------------------------
config_path = Path("config.toml")
config = Config.load_config(config_path)

TZ = config.common.get_tz()

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


def setup_devices(config: Config) -> tuple[gm10, pfr_100l50, pfr_100l50 | None, pwux | None]:
    print("Connecting to devices...")
    rm = pyvisa.ResourceManager()

    try:
        visa_list = rm.list_resources()
        print(visa_list)

        logger = gm10(rm, config.devices.gm10_visa)

        hps = pfr_100l50(rm, config.devices.hps_visa)
        # hps.SetOVP(config.devices.hps.unit, 2, config.devices.hps.ovp)
        # hps.SetOCP(config.devices.hps.unit, 2, config.devices.hps.ocp)

        aps = None
        if AMD_DEGAS:
            aps = pfr_100l50(rm, config.devices.aps_visa)
            # aps.SetOVP(config.devices.aps.unit, 2, config.devices.aps.ovp)
            # aps.SetOCP(config.devices.aps.unit, 2, config.devices.aps.ocp)

        rt = None
        if config.devices.pwux_com_port < 0:
            rt = pwux(rm, visa_list[config.devices.pwux_com_port - 1])

    except pyvisa.VisaIOError as e:
        print(e)
        sys.exit()

    except OSError as e:
        print(e)
        sys.exit()

    print("Devices connected.")
    return logger, hps, aps, rt


def setup_logging(config: Config) -> LogFile:
    log_manager = LogManager(config.common.log_dir)
    date_directory = log_manager.get_date_directory(DATE_DIR_UPDATE)
    logfile = date_directory.create_logfile(PROTOCOL, MAJOR_UPDATE)

    print(f"Logging to: {logfile.path}")
    return logfile


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

    ext_monitor = logger.get_data(config.devices.gm10.ext_ch)
    ext_pressure = ext_calculation_pressure(float(ext_monitor))
    sip_monitor = logger.get_data(config.devices.gm10.sip_ch)
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

    if AMD_DEGAS and aps is not None:
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

    logger, hps, aps, rt = None, None, None, None
    logfile = None

    try:
        start_time = datetime.datetime.now(TZ)
        print("HC program")
        print(
            "\033[32m" + "{:s} Start".format(start_time.strftime("%Y/%m/%d %H:%M:%S")) + "\033[0m"
        )

        logger, hps, aps, rt = setup_devices(config)
        logfile = setup_logging(config)

        # -------------------------------------------------------------------------

        logfile.write("#Heat Cleaning monitor\n")

        logfile.write(f"\n#Protocol:\t{logfile.protocol}\n")

        logfile.write("\n#Measurement\n")
        logfile.write(f"#Number:\t{logfile.number}\n")
        logfile.write(f"#Date:\t{start_time.strftime('%Y/%m/%d')}\n")
        logfile.write(f"#Time:\t{start_time.strftime('%H:%M:%S')}\n")
        logfile.write(f"#ProgramVersion:\t{VERSION}\n")
        logfile.write(f"#Encode:\t{config.common.encode}\n")

        logfile.write("\n#Condition\n")
        # log_file.write('#HeaterVoltageLimit:\t{}[V]\n'.format(HPS_V_LIMIT))
        # log_file.write('#InitialCurrent:\t{:.2f}[A]\n'.format(INITIAL_CURRENT))
        logfile.write(f"#HC_CURRENT:\t{HC_CURRENT}[A]\n")
        if AMD_DEGAS:
            logfile.write(f"#AMD_CURRENT:\t{AMD_CURRENT}[A]\n")
        for index, sequence in enumerate(SEQUENCE):
            logfile.write(f"#Sequence{index + 1}: {sequence}\n")

        logfile.write("\n#Comment\n")
        logfile.write(f"#{COMMENT}\n")

        logfile.write("\n#Data\n")
        if AMD_DEGAS:
            logfile.write("\t".join(GET_DATA) + "\n")
        else:
            logfile.write("\t".join(GET_DATA[:-3]) + "\n")

        # -------------------------------------------------------------------------

        hc_current = INITIAL_CURRENT
        hps.set_voltage(config.devices.hps.v_limit)
        hps.set_current(hc_current)
        hps.set_output(1)

        if AMD_DEGAS and aps is not None:
            amd_current = INITIAL_CURRENT
            aps.set_voltage(config.devices.amd.v_limit)
            aps.set_current(amd_current)
            aps.set_output(1)

        sequence_start = datetime.datetime.now(TZ)
        t = 0.0

        # メインループ
        # [電流値, 時間(second), Command, Exponent]
        for index, sequence in enumerate(SEQUENCE):
            step_start = t

            print(f"Sequence{index + 1}: {sequence}")
            print(sequence.mode_name)

            while (t - step_start) <= sequence.duration_second:
                hc_current = sequence.current(HC_CURRENT, t - step_start)
                hps.set_current(hc_current)

                if AMD_DEGAS and aps is not None:
                    amd_current = sequence.current(AMD_CURRENT, t - step_start)
                    aps.set_current(amd_current)

                write_log(logfile, sequence, t, hps, logger, rt, aps)

                time.sleep(STEP_TIME)
                t = (datetime.datetime.now(TZ) - sequence_start).total_seconds()

            hc_current = sequence.current(HC_CURRENT, t - step_start)
            hps.set_current(hc_current)

            if AMD_DEGAS and aps is not None:
                amd_current = sequence.current(AMD_CURRENT, t - step_start)
                aps.set_current(amd_current)

            print("\n")

    except Exception as e:  # noqa: BLE001
        print("\n")
        print(e)

    finally:
        """終わったら電源を閉じる処理をする。"""
        if hps is not None:
            hps.set_output(0)
            del hps

        if AMD_DEGAS and aps is not None:
            aps.set_output(0)
            del aps

        if rt is not None:
            del rt

        del logfile

        finish_time = datetime.datetime.now(TZ)
        print(
            "\033[31m" + "{:s} Finish".format(finish_time.strftime("%Y/%m/%d %H:%M:%S")) + "\033[0m"
        )


if __name__ == "__main__":
    main()

""" ----------------------------------------------------------------------
20250409 Version1.0 Created a program @Idei
20251026 Version 1.1 @Takeichi
---------------------------------------------------------------------- """
