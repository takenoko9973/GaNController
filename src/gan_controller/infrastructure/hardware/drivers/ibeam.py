import re
import time
from typing import ClassVar, cast

import pyvisa
from pyvisa.constants import Parity, StopBits
from pyvisa.resources import SerialInstrument

IBEAM_COM = 3  # デバイスマネージャーで確認


class IBeam:
    """TOPTICA iBeam Smart"""

    inst: SerialInstrument

    VALID_CHANNELS: ClassVar = [1, 2]

    # --- 通信定数 ---
    TERMINATION = "\r\n"
    ACK_WORD = "[OK]"
    PROMPT_WORD = "CMD>"

    # --- タイミング設定 (秒) ---
    WAIT_AFTER_MODE_SWITCH = 0.5
    WAIT_FOR_BUFFER = 0.1

    def __init__(
        self,
        rm: pyvisa.ResourceManager,
        resource_name: str,
        baud_rate: int = 115200,
        timeout: int = 2000,
    ) -> None:
        self.rm = rm
        self.resource_name = resource_name
        self.baud_rate = baud_rate
        self.timeout = timeout

        self._connect()

    def _connect(self) -> None:
        """機器への接続と初期設定を行う"""
        try:
            self.inst = cast("SerialInstrument", self.rm.open_resource(self.resource_name))

            # 通信パラメータ設定
            self.inst.baud_rate = self.baud_rate
            self.inst.timeout = self.timeout

            self.inst.data_bits = 8
            self.inst.parity = Parity.none
            self.inst.stop_bits = StopBits.one

            self.inst.read_termination = self.TERMINATION
            self.inst.write_termination = self.TERMINATION

            # 接続直後のゴミデータを掃除 (inst.clear()は使用しない)
            self._flush_buffer()

            print(f"[iBeam] Connected to {self.resource_name}")

            # 自動化モードへ移行
            self._set_protocol_mode(interactive=False)

        except Exception as e:
            # 接続失敗時はリソースを解放
            self.close()
            msg = f"Failed to connect to {self.resource_name}: {e}"
            raise ConnectionError(msg) from e

    def __enter__(self) -> "IBeam":
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:  # noqa: ANN001
        self.close()

    def __del__(self) -> None:
        self.close()

    # ============================================================
    # 内部通信メソッド
    # ============================================================

    def _flush_buffer(self) -> None:
        """
        受信バッファに残っているデータをバイト単位で読み捨てる。

        inst.clear() が不安定なデバイスのための対策。
        """
        if not self.inst:
            return

        try:
            # データ到着待ち
            time.sleep(self.WAIT_FOR_BUFFER)

            bytes_to_read = self.inst.bytes_in_buffer
            while bytes_to_read > 0:
                self.inst.read_bytes(bytes_to_read)

                # 読み込み後、さらにデータが流れてきていないか少し待って確認
                time.sleep(self.WAIT_FOR_BUFFER)
                bytes_to_read = self.inst.bytes_in_buffer

        except pyvisa.VisaIOError:
            # 読み込みエラーは「バッファが空」とみなして無視
            pass

    def _validate_channel(self, ch: int) -> None:
        """チャンネル番号が正しい確認"""
        if ch not in self.VALID_CHANNELS:
            msg = f"Invalid Channel: {ch}. Available channels are {self.VALID_CHANNELS}"
            raise ValueError(msg)

    def send_command(self, command: str) -> list[str]:
        """
        コマンドを送信し、[OK]が返るまでの応答を行リストとして返す。

        Returns:
            List[str]: 応答メッセージのリスト ([OK]行を除く)

        """
        if not self.inst:
            msg = "Device not connected."
            raise ConnectionError(msg)

        try:
            # バッファに何もないことを確認
            if self.inst.bytes_in_buffer > 0:
                self._flush_buffer()

            self.inst.write(command)
            response_lines = []
            while True:
                # 1行読み込み (read_terminationで区切られる)
                line = self.inst.read().strip()
                if not line:
                    continue

                # 終了条件
                if line == self.ACK_WORD:  # [OK] が来たら終了
                    break

                # エッジケース対策: まれに混入するプロンプトを無視
                if line.endswith(self.PROMPT_WORD):  # CMD> が流れたら無視
                    continue

                response_lines.append(line)

        except pyvisa.VisaIOError as e:
            print(f"[Error] Communication failed: {e}")
            return []

        else:
            return response_lines

    # ============================================================
    # 内部用メソッド
    # ============================================================
    def _set_protocol_mode(self, interactive: bool) -> None:
        """
        通信プロトコルモードを切り替える。

        Args:
            interactive (bool):
                True  -> 'prom on' (対話モード: 末尾 CMD>)
                False -> 'prom off' (自動化モード: 末尾 [OK])

        """
        cmd = "prom on" if interactive else "prom off"
        try:
            self.inst.write(cmd)

            # モード切替完了まで待機
            time.sleep(self.WAIT_AFTER_MODE_SWITCH)

            # 切替に伴う出力(CMD>など)を全て破棄
            self._flush_buffer()

            # 自動化モードへの移行時は、同期確認のために空打ちを行う
            if not interactive:
                self.inst.write("")
                time.sleep(self.WAIT_FOR_BUFFER)
                self._flush_buffer()

        except Exception as e:  # noqa: BLE001
            print(f"[Warning] Mode switch to '{cmd}' failed: {e}")

    # ============================================================
    # ユーザー用メソッド
    # ============================================================
    def set_emission(self, enable: bool) -> None:
        """レーザー発振(Emission)制御"""
        enable_str = "on" if enable else "off"
        self.send_command(f"laser {enable_str}")

    def is_emission(self) -> bool:
        return self.send_command("status laser")[0].upper() == "ON"

    # ============================================================

    def set_channel_enable(self, ch: int, enable: bool) -> None:
        """チャンネル有効/無効"""
        self._validate_channel(ch)

        enable_str = "enable" if enable else "disable"
        self.send_command(f"{enable_str} {ch}")

    def is_channel_enable(self, ch: int) -> bool:
        return self.send_command(f"status channel {ch}")[0].upper() == "ON"

    # ============================================================

    def set_channel_power(self, ch: int, power_mw: float) -> None:
        """出力パワー設定(mW)"""
        self._validate_channel(ch)

        power_uw = int(power_mw * 1000)
        self.send_command(f"channel {ch} power {power_uw} micro")  # uW で入力

    def _get_all_channel_powers(self) -> dict[int, float]:
        """
        各チャンネルの設定出力取得 (mW)

        返り値 : "CH<channel>, PWR: <value> <uW or mW>"
        """
        # 大文字小文字は一応無視
        pattern = re.compile(r"CH(\d+),\s*PWR:\s*([\d.]+)\s*(mW|uW)", flags=re.IGNORECASE)

        reply = self.send_command("show level power")

        powers: dict[int, float] = {}
        for ln in reply:
            match = re.match(pattern, ln)

            if match:
                prefix_correct = 1e-3 if match[3].lower() == "uw" else 1
                power = float(match[2]) * prefix_correct  # mW に変換
                powers[int(match[1])] = power

        return powers

    def get_channel_power(self, ch: int) -> float:
        """設定出力取得 (mW)"""
        return self._get_all_channel_powers()[ch]

    def get_output_power(self) -> float:
        """実出力取得 (mW)"""
        pattern = re.compile(r"PIC\s*=\s*([\d.]+)\s*(mW|uW)")

        reply = self.send_command("show power")[-1]

        match = re.match(pattern, reply, flags=re.IGNORECASE)
        if match:
            prefix_correct = 1e-3 if match[2].lower() == "uw" else 1
            return float(match[1]) * prefix_correct  # mW に変換

        print(f"[Warning] Can not parse output replay '{reply}'")
        return float("nan")

    # ============================================================

    def get_current(self, ch: int) -> str | None:
        self._validate_channel(ch)
        message = self.send_command("show current")  # レーザー出力中でないと取得できない

        return message[ch - 1]

    def get_work_time(self) -> list[str]:
        """Get the work hours (power on time and laser on time)"""
        return self.send_command("status uptime")

    def get_temperatures(self) -> list[float]:
        """
        温度を取得 (仮)

        機能してないかもしれない
        """
        pattern = re.compile(r"TEMP\s*=\s*([\d.]+)\s*C")

        temperatures = []
        for cmd in ["show temperature", "show temperature system"]:
            reply = self.send_command(cmd)[-1]

            match = re.match(pattern, reply, flags=re.IGNORECASE)
            if match:
                temperatures.append(float(match[1]))

        return temperatures

    def close(self) -> None:
        """接続を終了する。終了前に必ず対話モード(prom on)に戻す。"""
        if hasattr(self, "inst"):
            try:
                print("\n[iBeam] Restoring device settings...")
                self._set_protocol_mode(interactive=True)

            except Exception as e:  # noqa: BLE001
                print(f"[Error] Failed to restore settings: {e}")

            finally:
                self.inst.close()
                del self.inst
                print("[iBeam] Connection closed.")


def main() -> None:
    print("TOPTICA iBeam test")  # Ch1だと出力かわらないので、Ch2でやること
    print(f"COM Port: {IBEAM_COM}")

    rm = pyvisa.ResourceManager()
    laser = IBeam(rm, f"COM{IBEAM_COM}")

    try:
        laser.set_channel_enable(2, True)
        laser.set_channel_power(2, 50)
        laser.set_emission(True)
        time.sleep(1)
        print(f"Power: {laser.get_channel_power(2)}")
        print(f"LD status: {laser.is_emission()}")

        laser.set_channel_power(2, 20)
        time.sleep(1)
        print(f"Power: {laser.get_channel_power(2)}")

    except Exception as e:  # noqa: BLE001
        print("Error stop:", e)

    finally:
        laser.set_emission(False)
        print(f"LD status: {laser.is_emission()}")
        laser.set_channel_enable(2, False)
        print(f"Up time: {laser.get_work_time()}")

        del laser
        print("END")


if __name__ == "__main__":
    main()
