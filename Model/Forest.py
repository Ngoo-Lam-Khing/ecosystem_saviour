from Model.BoardItem import BoardItem
from Model.Npc import Npc
from Model.Player import Player


class Forest(BoardItem):
    def __init__(self, type: str):
        super().__init__(type)

    # check if the forest is sick, if it is sick, the player will be polluted when stepping on it without material, and the game will be over
    @property
    def is_sick(self) -> bool:
        return self.type == "SF"

    # set the sick status of the forest, player can heal the sick forest while npc can pollute the healthy forest
    @is_sick.setter
    def is_sick(self, value: bool) -> None:
        self.type = "SF" if value else "HF"

    def on_stepped_by(self, character: Npc | Player, board) -> None:
        # when meeting player, if the forest is sick, the player without material will be polluted and game over
        if isinstance(character, Player):
            if self.is_sick:
                if character.has_material:
                    character.has_material = False
                    # if the player has material, the forest will be healed and the player will get 1 point
                    character.add_score(1)
                    self.recover()
                    board.add_event(
                        "Forest is healed; Material is used. You got 1 point"
                    )

                    # if all forests are healthy, the player will get 2 extra points
                    if board.all_forests_healthy:
                        character.add_score(2)
                        board.add_event(
                            "You healed all forests, and got 2 extra points"
                        )
                else:
                    board.game_over = True
                    board.add_event("You are polluted by sick forest")
        elif isinstance(character, Npc):
            # when meeting npc, if the forest is healthy, the npc will pollute the forest
            if not self.is_sick:
                self.is_sick = True
                board.add_event("The forest is polluted")

    # player can recover the forest, making it healthy again
    def recover(self) -> None:
        self.type = "HF"
