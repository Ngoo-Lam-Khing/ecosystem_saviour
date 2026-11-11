from typing import override
from Model.BoardItem import BoardItem
from Model.Player import Player


class RepairStation(BoardItem):
    def __init__(self, type: str):
        super().__init__(type)

    @override
    def on_stepped_by(self, character: Player, _board):
        # if the player steps on the repair station, it will repair the player's bag if it is not full
        if isinstance(character, Player):
            if not character.has_material:
                character.has_material = True
                print("Got Material")
            else:
                print("Bag is Full")
