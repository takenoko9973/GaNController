"""----------------------------------------------------------------------
NEA activation program
----------------------------------------------------------------------
"""  # noqa: D205

import datetime
import sys
import time
from collections import deque
from pathlib import Path

import pyvisa
import serial  # pip3 install pyserial  # noqa: F401
from matplotlib import pyplot as plt

from heater_amd_controller.config import Config
from heater_amd_controller.const import NEA_PROTOCOL
from heater_amd_controller.libs.gm10 import gm10
from heater_amd_controller.libs.ibeam import ibeam
from heater_amd_controller.utils.calc import ext_calculation_pressure, sip_calculation_pressure
from heater_amd_controller.utils.log_file import LogFile, LogManager

# from OphirUSBI import OphirUSBI


# User setting parameter -------------------------------------------------------
VERSION = 1.2
PROTOCOL = NEA_PROTOCOL

MAJOR_UPDATE = False  # 前回のNEA活性化と区別したい場合はTrue

COMMENT = ""

HV = 100  # V

# 100 mW, FilterInでの測定結果: 164 μW
# 10 mW, FilterInでの測定結果: 70 μW
LP_PV = 164 * 10 ** (-6)

LOGGER_RANGE = ["20mV", -5000, 20000]  # 表示範囲: -5 ~ 20 mV

S_TIME = 1  # 測定前の待ち時間(安定化時間: Stabilization time)[s]
INTEGRATED = 1  # 積算回数
INTERVAL = 0  # 積算時の測定間隔[s](0: MW100の設定上の最小となる -> 500 msとか)

WAVELENGTH = 406  # nm
LASER_POWER = 120  # mW

USE_LASER = True
if not USE_LASER:
    COMMENT += "405nm15mW,BG=0.7mV"
    WAVELENGTH = 405  # nm
    LASER_POWER = 15  # mW
    # VP>>試料: 実際に試料に照射されるパワー10 mWと仮定
    LP_PV = 10 * 10 ** (-3)

    BG_PC = 0.7 * 10 ** (-3)  # V


# Setting parameters -----------------------------------------------------
config_path = Path("config.toml")
config = Config.load_config(config_path)

DISPLAY_WINDOW_MIN = 30  # 表示範囲[分]
QE_MIN_VALUE = 1e-12  # 対数スケール用最小値

TZ = config.common.get_tz()

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

"""----------------------------------------------------------------------------------"""


class RealtimePlot:
    """QEリアルタイムプロット管理クラス"""

    def __init__(self) -> None:
        plt.ion()
        self.fig, self.ax = plt.subplots()
        self.ax.set_xlabel("Time [min]")
        self.ax.set_ylabel("QE [%]")
        self.ax.set_title("Quantum Efficiency (Real-time)")
        self.ax.grid(True, which="both", ls="--")  # noqa: FBT003
        self.ax.set_yscale("log")

        self.xdata, self.ydata = deque(maxlen=2000), deque(maxlen=2000)
        (self.line,) = self.ax.plot([], [], color="C0")

    def update(self, t_min: float, qe: float) -> None:
        """グラフをリアルタイム更新"""
        # qe = max(qe, QE_MIN_VALUE)  # 対数用の下限処理
        if qe > 0:
            self.xdata.append(t_min)
            self.ydata.append(qe)

        self.line.set_data(self.xdata, self.ydata)
        self.ax.set_xlim(max(0, t_min - DISPLAY_WINDOW_MIN), t_min + 0.5)

        if len(self.ydata) > 1:
            ymin, ymax = min(self.ydata), max(self.ydata)
            self.ax.set_ylim(ymin * 0.8, ymax * 1.2)

        plt.tight_layout()
        plt.pause(0.01)

    def close(self) -> None:
        plt.ioff()
        plt.close(self.fig)


class NEAActivationExperiment:
    def __init__(self, config: Config) -> None:
        self.config = config
        self.logger: gm10 | None = None
        self.laser: ibeam | None = None
        self.logfile: LogFile | None = None
        self.plotter = RealtimePlot()

    # ================ 初期設定 ================

    def _setup_devices(self) -> None:
        print("Connecting to devices...")
        rm = pyvisa.ResourceManager()

        try:
            visa_list = rm.list_resources()
            print("Detected VISA devices:", visa_list)

            self.logger = gm10(rm, self.config.devices.gm10_visa)

            if USE_LASER and self.config.devices.ibeam_com_port > 0:
                self.laser = ibeam(f"COM{self.config.devices.ibeam_com_port}")
                self.laser.ch_on(self.config.devices.ibeam.beam_ch)
                self.laser.set_lp(self.config.devices.ibeam.beam_ch, LASER_POWER)
                print("Toptica Laser connected.")

        except (pyvisa.VisaIOError, OSError) as e:
            print("Device connection error:", e)
            self.cleanup()
            sys.exit(1)

        print("Devices connected.")

    def _setup_logging(self) -> None:
        log_manager = LogManager(self.config.common.log_dir)
        date_directory = log_manager.get_date_directory()
        self.logfile = date_directory.create_logfile(PROTOCOL, MAJOR_UPDATE)
        print(f"Logging to: {self.logfile.path}")

    def run(self) -> None:
        print(f"NEA activation program (Version: {VERSION})")

        start_time = datetime.datetime.now(TZ)
        print(f"\033[32m{start_time:%Y/%m/%d %H:%M:%S} Experiment start\033[0m")

        self._setup_devices()
        self._setup_logging()

        assert self.logger is not None
        assert self.logfile is not None
        self.write_log_header(start_time)

        try:
            while True:
                current_time = datetime.datetime.now(TZ)
                t = (current_time - start_time).total_seconds()
                t_min = t / 60.0
                print("\033[32m" + f"{t:.1f}[s]\t" + "\033[0m")

                # ======

                if USE_LASER and self.laser:
                    self.laser.laser_on()
                time.sleep(S_TIME)

                # bpc_all = logger.PhotocurrentMeasurement(pc_ch, shunt_r, INTEGRATED, INTERVAL, 0)
                # bpc = bpc_all[0]
                # blp = float(powermeter.read_data()) * ratio
                # logger_range = logger.GetInputChSetting(pc_ch)[0]['Range']
                bright_data = float(self.logger.get_data(self.config.devices.gm10.pc_ch))

                # ======

                if USE_LASER and self.laser:
                    self.laser.laser_off()
                time.sleep(S_TIME)

                dark_data = (
                    float(self.logger.get_data(self.config.devices.gm10.pc_ch))
                    if USE_LASER and self.laser
                    else BG_PC
                )

                # ======

                # dpc_all = logger.PhotocurrentMeasurement(pc_ch, shunt_r, INTEGRATED, INTERVAL, 0)
                # dpc = dpc_all[0]
                # dlp = float(powermeter.read_data()) * ratio

                # get_pc = bpc - dpc
                # get_lp = blp - dlp
                # qe = 1240 * get_pc / (wl * get_lp) * 100

                pressure_ext = ext_calculation_pressure(
                    float(self.logger.get_data(self.config.devices.gm10.ext_ch))
                )
                pressure_sip = sip_calculation_pressure(
                    float(self.logger.get_data(self.config.devices.gm10.sip_ch))
                )

                # spot_area = math.pi*(spot_size*10**(-4)/2)**2 #[cm^2]
                # pd = get_lp / spot_area
                # cd = get_pc / spot_area

                # get_tc = logger.GetMeasurementData(tc_ch)['Value']

                pc = ((bright_data - dark_data) * 1e-3) / 1e4  # photocurrent[A]
                # 1240 = hc/e * 1e-6 [J*m/C], λ[nm] * PV[W]
                qe = 1240 * pc / (WAVELENGTH * LP_PV) * 100

                # =========================================

                self.plotter.update(t_min, qe)

                print(f"{qe:.3e}%, {pressure_ext:.2e} Pa(EXT)")

                event = ""
                self.write_data_line(
                    t, qe, pc, pressure_ext, pressure_sip, bright_data, dark_data, event
                )

        except Exception as e:  # noqa: BLE001
            print("Error stop:", e)
        finally:
            self.cleanup()

    def write_log_header(self, start_time: datetime.datetime) -> None:
        # ヘッダ書き込み
        lf = self.logfile
        if lf is None:
            return

        lf.write("#NEA activation monitor\n\n")
        lf.write(f"#Protocol:\t{lf.protocol}\n\n")

        lf.write("#Measurement\n")
        lf.write(f"#Number:\t{lf.number}\n")
        lf.write(f"#Date:\t{start_time.strftime('%Y/%m/%d')}\n")
        lf.write(f"#Time:\t{start_time.strftime('%H:%M:%S')}\n")
        lf.write(f"#Encode:\t{config.common.encode}\n")
        lf.write(f"#Version:\t{VERSION}\n\n")

        lf.write("#Condition\n")
        lf.write(f"#Wavelength:\t{WAVELENGTH:d}[nm]\n")
        lf.write(f"#LaserPower(SV):\t{LASER_POWER:d}[mW]\n")

        lf.write(f"#StabilizationTime:\t{S_TIME:.1f}[s]\n")
        lf.write(f"#IntegratedTimes:\t{INTEGRATED:.1f}[-]\n")
        lf.write(f"#IntervalTime:\t{INTERVAL:.1f}[s]\n")
        lf.write(f"#ExtractionVoltage:\t{HV:d}[V]\n\n")

        lf.write("#Comment\n")
        lf.write(f"#{COMMENT}\n\n")

        lf.write("#Data\n")
        lf.write("\t".join(GET_DATA) + "\n")

    def write_data_line(
        self,
        t: float,
        qe: float,
        pc: float,
        pressure_ext: float,
        pressure_sip: float,
        bright_data: float,
        dark_data: float,
        event: str,
    ) -> None:
        if self.logfile is None:
            return
        data = [
            f"{t:.1f}",
            f"{LP_PV:.4E}",  # Laser power (PV)
            f"{qe:.4E}",  # Quantum efficiency (%)
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
        self.logfile.write("\t".join(data) + "\n")

    def cleanup(self) -> None:
        """全リソースの安全な破棄"""
        print("Cleaning up resources...")

        del self.logger
        del self.logfile

        if self.laser:
            try:
                self.laser.set_lp(2, 0)
                self.laser.laser_off()
                self.laser.ch_off(2)
            except Exception:  # noqa: BLE001, S110
                pass
            finally:
                del self.laser

        self.plotter.close()

        finish_time = datetime.datetime.now(TZ)
        print(f"\033[31m{finish_time:%Y/%m/%d %H:%M:%S} Finish\033[0m")


if __name__ == "__main__":
    NEAActivationExperiment(config).run()
