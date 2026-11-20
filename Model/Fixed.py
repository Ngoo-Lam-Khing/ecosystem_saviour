from Model.BoardItem import BoardItem


# Fiexed class is for mountain and lake, which is not enterable by player and npc
class Fixed(BoardItem):
    def __init__(self, type: str):
        super().__init__(type)

    @property
    def is_enterable(self) -> bool:
        return False
