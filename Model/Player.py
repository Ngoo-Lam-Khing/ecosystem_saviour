from Model.BoardItem import BoardItem


class Player(BoardItem):
    def __init__(self, type: str = "P"):
        super().__init__(type)
        self._has_material: bool = False
        self._score: int = 0

    @property
    def has_material(self) -> bool:
        return self._has_material

    @has_material.setter
    def has_material(self, value: bool):
        self._has_material = value

    @property
    def score(self) -> int:
        return self._score

    def add_score(self, points: int):
        self._score += points
