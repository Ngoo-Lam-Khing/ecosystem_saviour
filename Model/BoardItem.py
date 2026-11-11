from typing import Literal, override


class BoardItem:
    """
    - M = Mountain
    - L = Lake
    - R = Repair Station
    - SF = Sick Forest
    - HF = Healthy Forest
    - a dash, -, to represent an empty square
    """

    ValidTypes = Literal["M", "L", "R", "SF", "HF", "-"]

    def __init__(self, type: ValidTypes = "-"):
        self.type = type

    def __str__(self):
        return self.type

    @property
    def is_enterable(self) -> bool:
        return True

    @override
    def on_stepped_by(self, character, board) -> None:
        pass
