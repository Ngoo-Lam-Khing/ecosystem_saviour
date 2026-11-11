from typing import override
from Model.BoardItem import BoardItem
from Model.Npc import Npc
from Model.Player import Player


class Forest(BoardItem):
    def __init__(self, type: str):
        super().__init__(type)

    @property
    def is_sick(self) -> bool:
        return self.type == "SF"

    @is_sick.setter
    def is_sick(self, value: bool) -> None:
        self.type = "SF" if value else "HF"

    @override
    def on_stepped_by(self, character: Npc | Player, board) -> None:
        # when meeting player, if the forest is sick, the player without material will be polluted and game over
        # if the player has material, the forest will be healed and the player will get 1 point
        if isinstance(character, Player):
            if self.is_sick:
                if character.has_material:
                    character.has_material = False
                    character.add_score(1)
                    self.recover()
                    print("Forest is healed; Material is used. You got 1 point")

                    if board.all_forests_healthy:
                        character.add_score(2)
                        print("You healed all forests, and got 2 extra points")
                else:
                    board.game_over = True
                    print("You are polluted by sick forest")
        # when meeting npc, if the forest is healthy, it will be polluted
        elif isinstance(character, Npc):
            if not self.is_sick:
                self.is_sick = True
                print("The forest is polluted")

    def recover(self) -> None:
        if self.type == "SF":
            self.type = "HF"
