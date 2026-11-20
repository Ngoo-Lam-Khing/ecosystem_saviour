import os
from Model.Constants import round_limit
from Model.Board import Board
from Model.Player import Player
from Model.Npc import Npc
from Model.IntellectNpc import IntellectNpc
from View.ConsoleView import ConsoleView
from Controller.Controller import Controller


def resolve_board_file(filename: str) -> str:
    # Support both current working directory and script-relative paths
    # 同時支援當前工作目錄與 main.py 所在目錄尋找地圖檔
    if os.path.exists(filename):
        return filename
    script_dir = os.path.dirname(os.path.abspath(__file__))
    candidate = os.path.join(script_dir, filename)
    return candidate if os.path.exists(candidate) else filename


def main():
    # Initialize the game components
    board = Board()
    player = Player()
    npcs = [IntellectNpc()] + [Npc() for _ in range(2)]
    # Initialize the view and controller with resolved board file path
    view = ConsoleView()
    board_path = resolve_board_file("sample.txt")
    controller = Controller(board, player, npcs, view, board_path)
    controller.new_game()

    # Run the game loop
    while controller.is_playing:
        print(f"Turn (Current / Total): {controller.turn + 1} / {round_limit}")
        controller.run_turn()

    print("Game Over")
    print(f"You played {controller.turn} out of {round_limit} turns")
    print(
        f"You got {controller.player.score} point{'s' if controller.player.score >= 1 else ''} in total"
    )


if __name__ == "__main__":
    main()
