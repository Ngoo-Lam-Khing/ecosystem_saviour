from Model.Board import Board
from Model.Player import Player
from Model.Npc import Npc
from View.ConsoleView import ConsoleView


class Controller:
    def __init__(
        self, board: Board, player: Player, npcs: list[Npc], view: ConsoleView
    ):
        self._board = board
        self._player = player
        self._npcs = npcs
        self._view = view

    def get_input(self) -> tuple[str, int]:
        while True:
            direction = input("direction (u/d/l/r): ").strip().lower()
            if direction == "q":
                return None
            if direction in ("u", "d", "l", "r"):
                break
            print("Invalid direction.")

        while True:
            try:
                distance = int(input("distance (1-3): "))
            except ValueError:
                print("Invalid distance.")
                continue

            if 1 <= distance <= 3:
                break
            print("Invalid distance.")

        return (direction, distance)

    def move_player(self, move: tuple[str, int]):
        direction, distance = move

        self._board.move_character(self._player, direction, distance)

    def move_npcs(self):
        for npc in self._npcs:
            direction, distance = npc.move(self._board)
            self._board.move_character(npc, direction, distance)

    def run_turn(self) -> bool:
        move = self.get_input()

        if move is None:
            return False

        self.move_player(move)
        self._board.print_board()
        if self._board.game_over:
            return False

        self.move_npcs()
        self._board.print_board()
        if self._board.game_over:
            return False

        return True
