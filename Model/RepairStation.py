from Model.BoardItem import BoardItem
from Model.Npc import Npc
from Model.Player import Player


class RepairStation(BoardItem):
    def __init__(self, type: str = "R"):
        super().__init__(type)

    def on_stepped_by(self, character: Npc | Player, board) -> None:
        if isinstance(character, Player):
            # Check if the player has material; if not, give them material and log the event
            # If they already have material, log that their bag is full
            if not character.has_material:
                character.has_material = True
                board.add_event("Got Material")
            else:
                board.add_event("Bag is Full")
