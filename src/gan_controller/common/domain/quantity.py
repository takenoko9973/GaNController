from pydantic import BaseModel


class Quantity(BaseModel):
    value: float
    unit: str = ""

    def __format__(self, format_spec: str) -> str:
        """f-string 時に呼ばれる"""
        if not format_spec:
            return str(self)

        # f-string で指定されたフォーマットを適用
        formatted_value = format(self.value, format_spec)
        return f"{formatted_value} {self.unit}"

    def __str__(self) -> str:
        return f"{self.value} {self.unit}"
