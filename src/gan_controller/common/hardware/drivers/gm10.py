import contextlib
import re
import time
from typing import TYPE_CHECKING

import pyvisa  # pyvisa > pyvisa-py > zeroconf > psutil

if TYPE_CHECKING:
    from pyvisa.resources import TCPIPInstrument

VISA_ADDRESS = "TCPIP0::" + "192.168.1.105" + "::" + "34434" + "::SOCKET"


class GM10:
    """YOKOGAWA SMARTDAC+ GM10"""

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
            self.inst: TCPIPInstrument = rm.open_resource(visa_address)  # pyright: ignore[reportAttributeAccessIssue]
            self.inst.read_termination = "\r\n"
            self.inst.write_termination = "\r\n"
            self.inst.timeout = timeout

            self.inst.clear()  # バッファクリア
            time.sleep(self.wait_time)  # 初期化待機

            # 応答確認 ('GM10',<serial number>,<MAC address>,<version> <crlf>)
            self.idn = self.check_connection()
            print(self.idn)

        except pyvisa.VisaIOError as e:
            print(f"GM10 接続エラー: {e}")
            raise

    def __enter__(self) -> "GM10":
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:  # noqa: ANN001
        self.close()

    def __del__(self) -> None:
        self.close()

    # ============================================================
    # 内部通信メソッド
    # ============================================================
    def _query_multiline(self, command: str) -> list[str]:
        """出力コマンド(F...)を送信し、EA~ENまでの複数行データを取得"""
        for attempt in range(self.retry_count):
            lines = []

            try:
                self.inst.write(command)
                time.sleep(self.wait_time)

                # ヘッダ "EA" を待つ
                header = self.inst.read()
                if header.startswith("E1"):  # エラー応答
                    msg = f"GM10 クエリエラー: {header}"
                    raise RuntimeError(msg)

                # データ本体からフッタ "EN" まで読む
                while True:
                    line = self.inst.read()
                    if line.startswith("EN"):
                        break
                    lines.append(line)

                break

            except pyvisa.VisaIOError as e:
                print(f"Query Error (Attempt {attempt + 1}): {e}")
                if attempt == self.retry_count - 1:
                    raise

                # エラー回復: バッファクリア等を試みる
                with contextlib.suppress(Exception):
                    self.inst.clear()

                if self.wait_time > 0:
                    time.sleep(self.wait_time)

        return lines

    def _parse_fdata_lines(self, lines: list[str]) -> dict[str, tuple[float, str]]:
        """FDataのASCIIレスポンス行を解析して辞書化

        返り値 : (数値, 単位文字列)

        形式: s_cccca1a2a3a4uuuuuuuuuufddddddddE-pp
        ※ a1-4はそれぞれ1文字で表現されるアラームステータス
        ※ u は単位を表し、左詰めで表示される
        例:   N 0001    V          +00123456E-03
        """
        result = {}

        # Group1: ステータス (N, E, O, B,...)
        # Group2: チャンネル (0001, 0002,...)
        # Group3: アラーム   (<空白>,H,L,h,l,R,r,...)
        # Group4: 単位情報   (V, mV)
        # Group5: 数値文字列 (+12345678E-03)
        pattern = re.compile(r"^([A-Z])\s([\w]{4})(.{4})(.{10})([+-]\d{8}E[+-]\d{2})")

        for line in lines:
            # 日付・時刻行はスキップ
            if line.startswith(("DATE", "TIME")):
                continue

            match = pattern.search(line)
            if match:
                status = match.group(1)
                ch_id = match.group(2)
                alarm_stat = match.group(3)  # noqa: F841
                unit = match.group(4)
                val_str = match.group(5)

                try:
                    if status in {"N", "D"}:  # Normal, Delta
                        val = float(val_str)
                    elif status == "O":  # Over range
                        # +Over or -Over
                        val = float("inf") if val_str.startswith("+") else float("-inf")
                    elif status in {"E", "B"}:  # Error
                        val = float("nan")
                    elif status == "S":  # Skip (設定なし)
                        continue
                    else:  # その他不明ステータス
                        val = float(val_str)  # 一応変換を試みる

                    result[ch_id] = (val, unit.strip())

                except ValueError:
                    result[ch_id] = (float("nan"), unit.strip())

        return result

    def _get_fdata_range(self, start_ch: str, end_ch: str) -> dict[str, tuple[float, str]]:
        """FDataコマンドの発行とレスポンス解析"""
        cmd = f"FData,0,{start_ch},{end_ch}"
        lines = self._query_multiline(cmd)
        return self._parse_fdata_lines(lines)

    def _fmt_ch_str(self, channel: int | str) -> str:
        """チャンネル番号を4桁文字列にフォーマット"""
        if isinstance(channel, int):
            return f"{channel:04d}"
        return str(channel)

    # ============================================================
    # ユーザー用メソッド
    # ============================================================

    def check_connection(self) -> str:
        """応答確認"""
        lines = self._query_multiline("_INF")
        if lines:
            return lines[0]

        return "Unknown"

    def read_channels(self, start_ch: int | str, end_ch: int | str) -> dict[str, tuple[float, str]]:
        # start_ch より end_ch が大きい場合は入れ替え
        if isinstance(start_ch, int) and isinstance(end_ch, int) and start_ch < end_ch:
            temp = start_ch
            start_ch = end_ch
            end_ch = temp
            del temp

        s_ch = self._fmt_ch_str(start_ch)
        e_ch = self._fmt_ch_str(end_ch)

        return self._get_fdata_range(s_ch, e_ch)

    def read_channel(self, channel: int | str) -> tuple[float, str]:
        ch_str = self._fmt_ch_str(channel)

        # FDataコマンドで「開始CH」と「終了CH」を同じにして単一取得
        data_dict = self.read_channels(ch_str, ch_str)
        if ch_str in data_dict:
            return data_dict[ch_str]

        # 取得できなかった場合 (レスポンスに含まれていない場合)
        print(f"GM10 Warning: Channel {ch_str} not found in response.")
        return (float("nan"), "")

    def close(self) -> None:
        if hasattr(self, "inst"):
            with contextlib.suppress(Exception):
                self.inst.close()

            del self.inst


def main() -> None:
    rm = pyvisa.ResourceManager()
    visa_list = rm.list_resources()
    print(visa_list)

    logger = GM10(rm, VISA_ADDRESS)
    result = logger.read_channel(10)
    print(result)
    logger.close()

    del logger


if __name__ == "__main__":
    main()
    print("END")
