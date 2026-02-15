import builtins
import contextlib
import time
from typing import TYPE_CHECKING

import pyvisa

if TYPE_CHECKING:
    from pyvisa.resources.messagebased import MessageBasedResource

VISA_ADDRESS = "TCPIP0::" + "192.168.1.111" + "::" + "2268" + "::SOCKET"


class PFR100L50:
    """TEXIO PFR-100L50 直流安定化電源"""

    def __init__(
        self,
        rm: pyvisa.ResourceManager,
        visa_address: str,
        wait_time: float = 0.05,
        timeout: int = 10000,
        retry_count: int = 3,
    ) -> None:
        self.wait_time = wait_time
        self.retry_count = retry_count

        try:
            self.inst: MessageBasedResource = rm.open_resource(visa_address)  # pyright: ignore[reportAttributeAccessIssue]
            self.inst.read_termination = "\n"
            self.inst.write_termination = "\n"
            self.inst.timeout = timeout

            self.inst.clear()  # バッファクリア
            self.inst.write("*CLS")  # 機器内部のエラー情報を消去
            time.sleep(self.wait_time)  # 初期化待機

            # 応答確認 (TEXIO,PFR-100L50,<serial number>,<version>)
            self.idn = self.check_connection()
            print(self.idn)

        except pyvisa.VisaIOError as e:
            print(f"初期化接続エラー: {e}")
            raise

    def __enter__(self) -> "PFR100L50":
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:  # noqa: ANN001
        self.close()

    def __del__(self) -> None:
        self.close()

    # ============================================================
    # 内部通信メソッド
    # ============================================================
    def _send_command(self, command: str) -> None:
        """書き込み用ラッパー (リトライ機能有り)"""
        for attempt in range(self.retry_count):
            try:
                self.inst.write(command)
                if self.wait_time > 0:
                    time.sleep(self.wait_time)

                break  # 通信成功時はループを抜ける

            except pyvisa.VisaIOError as e:
                print(f"Write Error (Attempt {attempt + 1}/{self.retry_count}): {command} -> {e}")
                self._recover_connection()
                if attempt == self.retry_count - 1:
                    raise  # リトライ上限に達したら例外を送出

    def _query_command(self, command: str) -> str:
        """Query用のラッパー (リトライ機能有り)"""
        for attempt in range(self.retry_count):
            try:
                response = self.inst.query(command)
                if self.wait_time > 0:
                    time.sleep(self.wait_time)

                break

            except pyvisa.VisaIOError as e:
                print(f"Query Error (Attempt {attempt + 1}/{self.retry_count}): {command} -> {e}")
                self._recover_connection()
                if attempt == self.retry_count - 1:
                    raise

        return response.strip()

    def _recover_connection(self) -> None:
        """エラー発生時回復処理"""
        with contextlib.suppress(Exception):  # 例外処理を無視
            self.inst.clear()
            time.sleep(0.1)

        with contextlib.suppress(Exception):
            self.inst.write("*CLS")
            time.sleep(0.1)

    # ============================================================
    # ユーザー用メソッド
    # ============================================================

    def check_connection(self) -> str:
        """応答確認"""
        return self._query_command("*IDN?")

    def set_current(self, current_sv: float) -> None:
        """電流設定"""
        self._send_command(f":CURR {current_sv}")

    def measure_current(self) -> float:
        """出力電流の実測"""
        return float(self._query_command(":MEAS:CURR?"))

    def set_voltage(self, volt_sv: float) -> None:
        """電圧設定"""
        self._send_command(f":VOLT {volt_sv}")

    def measure_voltage(self) -> float:
        """出力電圧の実測"""
        return float(self._query_command(":MEAS:VOLT?"))

    def measure_power(self) -> float:
        """出力電力の実測"""
        return float(self._query_command(":MEAS:POW?"))

    def set_output(self, state: bool) -> None:
        """出力 On/Off設定"""
        command = "ON" if state else "OFF"
        self.inst.write(f":OUTP {command}")

    def get_output_state(self) -> bool:
        """出力状態確認"""
        resp = self._query_command(":OUTP?")
        return resp == "1"

    def set_ovp(self, ovp_sv: float) -> None:
        """過電圧保護設定"""
        self._send_command(f":VOLT:PROT {ovp_sv}")

    def set_ocp(self, ocp_sv: float) -> None:
        """過電流保護設定"""
        self._send_command(f":CURR:PROT {ocp_sv}")

    def close(self) -> None:
        if hasattr(self, "inst"):
            with contextlib.suppress(builtins.BaseException):
                self.inst.close()

            del self.inst


def main() -> None:
    rm = pyvisa.ResourceManager()
    visa_list = rm.list_resources()
    print(visa_list)

    ps = PFR100L50(rm, VISA_ADDRESS)

    ps.set_voltage(0.5)
    ps.set_current(0.01)
    ps.set_output(True)
    time.sleep(1)
    print(f"I: {ps.measure_current()} A")
    print(f"V: {ps.measure_voltage()} V")
    print(f"W: {ps.measure_power()} W")
    ps.set_output(False)

    del ps


if __name__ == "__main__":
    main()
    print("END")

"""
2025/04/08  Version1.0  Idei@09Laser404
"""
