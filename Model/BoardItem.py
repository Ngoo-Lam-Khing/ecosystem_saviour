from typing import Literal, override


class BoardItem:
    """
    - M = Mountain
    - L = Lake
    - R = Repair Station
    - SF = Sick Forest
    - HF = Healthy Forest
    - - = to represent an empty square
    """

    # Define a type alias for valid board item types
    # Literal is used to restrict the type to specific string values
    ValidTypes = Literal["M", "L", "R", "SF", "HF", "-"]

    # Initialize the BoardItem with a type, defaulting to "-" for an empty square
    def __init__(self, type: ValidTypes = "-"):
        self.type = type

    # Return the string representation of the BoardItem, which is its type
    def __str__(self):
        return self.type

    # Define a property to check if the BoardItem is enterable, which defaults to True for this class
    @property
    def is_enterable(self) -> bool:
        return True

    # Define a method to handle the event when a character steps on this BoardItem(Frorest, Repair Station);
    def on_stepped_by(self, character, board) -> None:
        pass
