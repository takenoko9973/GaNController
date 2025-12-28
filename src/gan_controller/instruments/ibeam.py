import builtins
import contextlib
import time
from typing import ClassVar

import serial  # pip3 install pyserial

IBEAM_COM = 3  # デバイスマネージャーで確認


class IBeam:
    """TOPTICA iBeam Smart"""

    VALID_CHANNELS: ClassVar = [1, 2]

    def __init__(
        self,
        port: str,
        baud_rate: int = 115200,
        wait_time: float = 0.05,
        timeout: float = 1,
    ) -> None:
        self.port = port
        self.baud_rate = baud_rate
        self.wait_time = wait_time
        self.timeout = timeout

        try:
            self.inst = serial.Serial(
                port=port,
                baudrate=self.baud_rate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=self.timeout,
            )

            time.sleep(self.wait_time)

            self.inst.reset_input_buffer()  # バッファ削除

            self.set_prompt(False)  # Responseを[OK]に設定

        except Exception:
            print("Visa io error")
            raise

    def __enter__(self) -> "IBeam":
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:  # noqa: ANN001
        self.close()

    def __del__(self) -> None:
        if hasattr(self, "inst"):
            self.close()

    # ============================================================
    # 内部通信メソッド
    # ============================================================

    def _validate_channel(self, ch: int) -> None:
        """チャンネル番号が正しい確認"""
        if ch not in self.VALID_CHANNELS:
            msg = f"Invalid Channel: {ch}. Available channels are {self.VALID_CHANNELS}"
            raise ValueError(msg)

    def _read_until_ok(self) -> list[str]:
        start_time = time.time()
        lines = []
        while True:
            if time.time() - start_time > self.timeout / 1000:
                msg = "Device did not return [OK]"
                raise TimeoutError(msg)

            with contextlib.suppress(builtins.BaseException):
                line = self.inst.read_until(b"\r\n").decode("utf-8").strip()

            # "[OK]" が来るまで通信を続ける
            if line == "[OK]":
                break

            if line:
                lines.append(line)

        return lines

    def _send_command(self, cmd: str) -> None:
        full_cmd = cmd + "\r\n"
        self.inst.write(full_cmd.encode("ascii"))

        self._read_until_ok()

    def _query(self, cmd: str) -> str | None:
        full_cmd = cmd + "\r\n"
        self.inst.write(full_cmd.encode("ascii"))

        lines = self._read_until_ok()
        return lines[0] if lines else None

    # ============================================================
    # ユーザー用メソッド
    # ============================================================

    def set_prompt(self, enable: bool = False) -> None:
        if enable:
            # [OK]が帰ってこなくなるので、独自で送信する
            self.inst.flush()
            self._send_command("prom on")
            time.sleep(self.wait_time)
        else:
            self._send_command("prom off")

    # ============================================================
    # ユーザー用メソッド
    # ============================================================
    def set_emission(self, enable: bool) -> None:
        """レーザー発振(Emission)制御"""
        cmd = "la on" if enable else "la off"
        self._send_command(cmd)

    def set_channel_enable(self, ch: int, enable: bool) -> None:
        """チャンネル有効/無効"""
        self._validate_channel(ch)

        cmd = f"en {ch}" if enable else f"di {ch}"
        self._send_command(cmd)

    def set_channel_power(self, ch: int, power_mw: float) -> None:
        """出力パワー設定(mW)"""
        self._validate_channel(ch)

        power_uw = int(power_mw * 1000)
        self._send_command(f"ch {ch} pow {power_uw}")

    def get_channel_power(self, ch: int) -> str | None:
        """出力パワー取得(mW)"""
        self._validate_channel(ch)

        # %SYS-I-077, scaled と返ってくる(tempも) → 搭載していないか非対応なのか...?
        # tempもTOPAS iBeam smartで90 mW出力で
        # しばらく様子見ても変化しない(30.2℃)ので、非対応なのかも
        return self._query("sh pow")

    def get_current(self) -> str | None:
        return self._query("sh cur")

    def get_status(self, status: str = "LD_Driver", ch: int = 1) -> str | None:
        if status == "LD_Driver":
            return self._query("sta la")
        if status == "Temp":
            return self._query("sta temp")
        if status == "UpTime":
            return self._query("sta up")

        return None

    def get_error(self) -> str | None:
        return self._query("err")

    def close(self) -> None:
        if hasattr(self, "inst"):
            with contextlib.suppress(builtins.BaseException):
                self.set_prompt(True)  # Prompt設定戻さないと、iBeamSmartソフトウェアが使えない
                self.inst.flush()
                self.inst.close()


def main() -> None:
    print("TOPTICA iBeam test")  # Ch1だと出力かわらないので、Ch2でやること
    print(f"COM Port: {IBEAM_COM}")

    laser = IBeam(f"COM{IBEAM_COM}")

    try:
        laser.set_channel_enable(2, True)
        laser.set_lp(2, 50)
        laser.laser_on()
        time.sleep(1)
        print(f"Power: {laser.get_lp()}")

        print("LD status: {}".format(laser.get_status("LD_Driver")))

        laser.set_lp(2, 20)
        # laser.laser_on()
        time.sleep(1)
        print(f"Power: {laser.get_lp()}")

    except Exception as e:
        print("Error stop:", e)

    finally:
        laser.laser_off()
        print("LD status: {}".format(laser.get_status("LD_Driver")))
        laser.ch_off(2)
        print("Up time: {}".format(laser.get_status("UpTime")))
        print(f"Error: {laser.get_error()}")
        del laser
        print("END")


if __name__ == "__main__":
    main()

""" ----------------------------------------------------------------------
Rivision history
2022/09/27: Version1.0 Created a program @Idei
2024/07/17: Version2.0 変数名などを改修 @Idei
2025/04/11  Version2.0 微修正 @Idei
---------------------------------------------------------------------- """
