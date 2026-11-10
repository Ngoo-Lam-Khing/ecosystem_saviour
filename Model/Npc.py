import random
from Model.BoardItem import BoardItem


class Npc(BoardItem):
    def __init__(self, type: str = "NPC"):
        super().__init__(type)

    def move(self, _board) -> tuple[str, int]:
        directions = ["u", "d", "l", "r"]

        direction = random.choice(directions)
        distance = random.randint(1, 3)
        return (direction, distance)
