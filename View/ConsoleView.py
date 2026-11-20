from Model.Constants import color
from Model.Board import Board


class ConsoleView:

    # responsible for displaying the game state and messages to the console
    def show_messages(self, messages: list[str]) -> None:
        for message in messages:
            print(message)

    # responsible for rendering the game board to the console
    def render(self, board: Board):
        display_grid = [
            [f"{str(board.grid[r][c]):^3}" for c in range(board.cols)]
            for r in range(board.rows)
        ]

        for obj, (x, y) in board.objs.items():
            # map color to npc and player for being recognizable
            display_grid[x][
                y
            ] = f"\033[{color[type(obj).__name__.lower()]}m{str(obj):^3}\033[0m"

        for row in display_grid:
            print(" ".join(row))
