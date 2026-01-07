import contextlib
import time
from typing import TYPE_CHECKING

import pyvisa

if TYPE_CHECKING:
    from pyvisa.resources import SerialInstrument

PWUX_COM = 1  # デバイスマネージャーで確認


class PWUX:
    def __init__(
        self,
        rm: pyvisa.ResourceManager,
        resource_name: str,
        wait_time: float = 0.05,
        timeout: int = 10000,
        retry_count: int = 3,
    ) -> None:
        self.wait_time = wait_time
        self.retry_count = retry_count

        try:
            self.inst: SerialInstrument = rm.open_resource(resource_name)  # pyright: ignore[reportAttributeAccessIssue]
            self.inst.read_termination = "\r\n"
            self.inst.write_termination = "\r\n"
            self.inst.timeout = timeout

            self.inst.clear()  # バッファクリア
            time.sleep(self.wait_time)  # 初期化待機

            # 応答確認 ('GM10',<serial number>,<MAC address>,<version> <crlf>)
            # self.idn = self.check_connection()
            # print(self.idn)
            print("PWUX init")

        except pyvisa.VisaIOError as e:
            print(f"PWUX 接続エラー: {e}")
            raise

    def __enter__(self) -> "PWUX":
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:  # noqa: ANN001
        self.close()

    def __del__(self) -> None:
        self.close()

    # ============================================================
    # 内部通信メソッド
    # ============================================================
    def _query_command(self, command: str, param: str | int) -> str:
        """Query用のラッパー (リトライ機能有り)"""
        command = f"{command} {param}"
        for attempt in range(self.retry_count):
            try:
                response = self.inst.query(command)

                break

            except pyvisa.VisaIOError as e:
                print(f"Query Error (Attempt {attempt + 1}/{self.retry_count}): {command} -> {e}")
                self._recover_connection()
                if attempt == self.retry_count - 1:
                    raise

            if self.wait_time > 0:
                time.sleep(self.wait_time)

        response = response.replace(f"{command} ", "")  # コマンド部分を削除
        return response.strip()

    def _recover_connection(self) -> None:
        """エラー発生時回復処理"""
        with contextlib.suppress(Exception):  # 例外処理を無視
            self.inst.clear()

    # ============================================================
    # ユーザー用メソッド
    # ============================================================
    def check_connection(self) -> str:
        """応答確認"""
        # コマンド不明 (臨時)
        lines = self._query_command("*IDN?", "")
        if lines:
            return lines[0]

        return "Unknown"

    def set_pointer(self, status: bool) -> str:
        """計測位置ポイント表示切替"""
        status_num = 1 if status else 0
        return self._query_command("LS", status_num)

    def get_temp(self) -> float:
        response = self._query_command("PV", "")
        return float(response) if "OVER" not in response else float("nan")

    def test(self) -> None:
        print(f">> {self._query_command('EE', '0.05')}")
        print(f">> {self._query_command('VR', '')}")

    def close(self) -> None:
        if hasattr(self, "inst"):
            with contextlib.suppress(Exception):
                self.inst.close()

            del self.inst


def main() -> None:
    rm = pyvisa.ResourceManager()
    visa_list = rm.list_resources()
    print(visa_list)

    rt = PWUX(rm, visa_list[PWUX_COM - 1])

    print(f"Temp: {rt.get_temp()} deg.C")
    print(rt.set_pointer(True))
    time.sleep(1)
    print(rt.set_pointer(False))

    del rt


if __name__ == "__main__":
    main()
    print("END")

"""
2025/04/08  Version1.0  Idei@09Laser404
"""
