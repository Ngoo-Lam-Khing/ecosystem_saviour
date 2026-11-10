from typing import Literal
class BoardItem:
    """
    - M = Mountain
    - L = Lake
    - R = Repair Station
    - SF = Sick Forest
    - HF = Healthy Forest
    - a dash, -, to represent an empty square 
    """
    ValidTypes = Literal['M', 'L', 'R', "SF", "HF", '-']

    def __init__(self, type: ValidTypes = '-'):
        self._type = type

    def __str__(self):
        return self._type

    @property
    def is_enterable(self) -> bool:
        return True

    def on_stepped_by(self, character, board):
        pass