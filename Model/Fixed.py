from Model.BoardItem import BoardItem


class Fixed(BoardItem):
    def __init__(self, type: str):
        super().__init__(type)

    @property
    def is_enterable(self) -> bool:
        return False
