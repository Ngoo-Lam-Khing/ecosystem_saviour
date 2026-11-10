from Model.Board import Board
from Model.Npc import Npc
from Model.IntellectNpc import IntellectNpc
from Model.Player import Player
from Controller import Controller


def main():
    board = Board()
    board.load_board("sample.txt")

    player = Player()
    board.init_player(player)

    npcs = [IntellectNpc()] + [Npc() for _ in range(2)]
    board.init_npc(npcs)

    board.print_board()

    view = ConsoleView()
    controller = Controller(board, player, npcs, view)

    rounds = 0
    round_limit = 20
    playing = True
    while playing and rounds <= round_limit and not board.game_over:
        playing = controller.run_turn()
        rounds += 1

    print("Game Over")
    print(f"You got {player.score} point{'s' if player.score > 1 else ''} in total")


if __name__ == "__main__":
    main()
