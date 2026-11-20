from Model.BoardItem import BoardItem


class Player(BoardItem):
    def __init__(self, type: str = "P"):
        super().__init__(type)
        self._has_material: bool = False
        self._score: int = 0

    @property
    def has_material(self) -> bool:
        return self._has_material

    # when stepping on sick forest, it will be used up; when stepping on repair station, it will be supplied
    @has_material.setter
    def has_material(self, value: bool) -> None:
        self._has_material = value

    @property
    def score(self) -> int:
        return self._score

    # when healing sick forest, the score will be added
    def add_score(self, points: int) -> None:
        self._score += points

    # set default value when start or restart a new game
    def reset(self) -> None:
        self._has_material = False
        self._score = 0
