from Model.BoardItem import BoardItem
from Model.Player import Player


class RepairStation(BoardItem):
    def __init__(self, type: str):
        super().__init__(type)

    def on_stepped_by(self, character: Player, _board):
        if isinstance(character, Player):
            if not character.has_material:
                character.has_material = True
                print("Got Material")
            else:
                print("Bag is Full")
