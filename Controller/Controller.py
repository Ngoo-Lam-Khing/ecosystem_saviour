from Model.Constants import directions, round_limit
from Model.Board import Board
from Model.Player import Player
from Model.Npc import Npc
from View.ConsoleView import ConsoleView


class Controller:
    def __init__(
        self,
        board: Board,
        player: Player,
        npcs: list[Npc],
        view: ConsoleView,
        data: str,
    ):
        self.board = board
        self.player = player
        self.npcs = npcs
        self.view = view
        self.data = data

        self.turn = 0
        self.playing = False

    def new_game(self) -> None:
        # Initialize board layout, spawn entities, and display initial game state
        self.board.load_board(self.data)
        self.board.init_player(self.player)
        self.board.init_npc(self.npcs)
        self.view.show_messages(self.board.consume_events())
        self.view.render(self.board)
        self.playing = True
        self.turn = 0

    @property
    def is_playing(self) -> bool:
        # Game continues only while active, below the round limit, and not in game-over state
        return self.playing and self.turn < round_limit and not self.board.game_over

    def ask_move(self) -> tuple[str, int] | None:
        # Validate direction input; allow 'q' to quit immediately
        while True:
            direction = input("direction (u/d/l/r): ").strip().lower()
            if direction == "q":
                return None
            if direction in directions:
                break
            print("Invalid direction.")

        # Validate step distance within allowed range [1, 3]
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

    def move_player(self, move: tuple[str, int]) -> None:
        direction, distance = move
        self.board.move_character(self.player, direction, distance)

    def move_npcs(self) -> None:
        for npc in self.npcs:
            # Abort remaining NPC moves immediately if an earlier collision ends the game
            if self.board.game_over:
                break
            direction, distance = npc.move(self.board)
            self.board.move_character(npc, direction, distance)

    def run_turn(self) -> None:
        move = self.ask_move()

        # Terminate session if player chooses to quit
        if move is None:
            self.playing = False
            return

        self.move_player(move)

        # Let NPCs act only if the player's move did not already trigger game over
        if not self.board.game_over:
            self.move_npcs()

        # Flush accumulated model events to the view and render updated board
        self.view.show_messages(self.board.consume_events())
        self.view.render(self.board)

        if self.board.game_over:
            self.playing = False

        self.turn += 1
