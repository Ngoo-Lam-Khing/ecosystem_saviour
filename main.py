from Model.Constants import round_limit
from Model.Board import Board
from Model.Player import Player
from Model.Npc import Npc
from Model.IntellectNpc import IntellectNpc
from View.ConsoleView import ConsoleView
from Controller.Controller import Controller


def main():
    # Initialize the game components
    board = Board()
    player = Player()
    npcs = [IntellectNpc()] + [Npc() for _ in range(2)]
    # Initialize the view and controller
    view = ConsoleView()
    controller = Controller(board, player, npcs, view, "sample.txt")
    controller.new_game()

    # Run the game loop
    while controller.is_playing:
        print(f"Turn (Current / Total): {controller.turn + 1} / {round_limit}")
        controller.run_turn()

    print("Game Over")
    print(f"You played {controller.turn} out of {round_limit} turns")
    print(
        f"You got {controller.player.score} point{'s' if controller.player.score > 1 else ''} in total"
    )


if __name__ == "__main__":
    main()
