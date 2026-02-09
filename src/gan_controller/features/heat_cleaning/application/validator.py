import re


class ProtocolValidator:
    @staticmethod
    def validate_name(name: str) -> tuple[bool, str]:
        if not name:
            return False, "名前が空です。"

        if not re.fullmatch(r"[A-Z0-9]+", name):
            return False, "プロトコル名は英大文字(A-Z)と数字(0-9)のみ使用可能です。"

        return True, ""
