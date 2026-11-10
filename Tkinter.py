import tkinter as tk
from tkinter import messagebox
from Model.Board import Board
from Model.Npc import Npc
from Model.IntellectNpc import IntellectNpc
from Model.Player import Player


class GameGUI:
    def __init__(self, root: tk.Tk, file: str):
        self.root = root
        self.file = file
        self.board = None
        self.player = None
        self.npcs = []
        self.cell_size = 50
        self.turn = 0
        self.turn_limit = 100
        self.npc_move_interval = 1000

        self._init_game()

        self.score = tk.StringVar(value=f"Current Score: {self.player.score}")
        self.label = tk.Label(self.root, textvariable=self.score)
        self.label.pack()

        self.current_turn = tk.StringVar(value=f"Current Turn: {self.turn}")
        self.label = tk.Label(self.root, textvariable=self.current_turn)
        self.label.pack()

        width = self.board._cols * self.cell_size
        height = self.board._rows * self.cell_size
        self.root.geometry(f"{width}x{height + 25 * 2}")
        self.canvas = tk.Canvas(
            root,
            width=width,
            height=height,
        )
        self.canvas.pack()

        self.root.bind("<Up>", lambda e: self.handle_player_move("u"))
        self.root.bind("<Down>", lambda e: self.handle_player_move("d"))
        self.root.bind("<Left>", lambda e: self.handle_player_move("l"))
        self.root.bind("<Right>", lambda e: self.handle_player_move("r"))
        self.root.bind("<Button>", lambda e: self.handle_player_click(e))
        self.root.bind_all("q", lambda e: self.handle_close())
        self.root.bind_all("Q", lambda e: self.handle_close())

        self.draw_board()
        self.auto_npc_move()

    def _init_game(self):
        self.board = Board()
        self.board.load_board(self.file)

        self.player = Player()
        self.board.init_player(self.player)

        self.npcs = [IntellectNpc()] + [Npc() for _ in range(2)]
        self.board.init_npc(self.npcs)

        self.turn = 0
        # for first __init__
        if hasattr(self, "score"):
            self.score.set(f"Current Score: {self.player.score}")
        if hasattr(self, "current_turn"):
            self.current_turn.set(f"Current Turn: {self.turn}")

    def _handle_game_over(self):
        if self.board.game_over:
            messagebox.showinfo(
                title=None,
                message=f"You got {self.player.score} point{'s' if self.player.score > 1 else ''} in total",
            )
            answer = messagebox.askquestion(title=None, message="Play Again?")
            if answer == "yes":
                self._init_game()
                self.draw_board()
            else:
                self.root.destroy()

    def handle_player_move(self, direction: str, distance: int = 1):
        if self.board.game_over:
            return

        self.board.move_character(self.player, direction, distance)
        self.score.set(f"Current Score: {self.player.score}")
        self.turn += 1
        self.current_turn.set(f"Current Turn: {self.turn}")
        self.draw_board()

        # in case that game over causes current turn unupdated
        self.root.update()

        if self.turn >= self.turn_limit:
            self.board.game_over = True

        self._handle_game_over()

    def handle_player_click(self, e):
        x, y = e.y // self.cell_size, e.x // self.cell_size
        p_x, p_y = self.board._objs[self.player]
        print(e.x, e.y)
        print(x, y)
        print(p_x, p_y)

        direction = None
        distance = 0
        # same row
        if x == p_x:
            if y > p_y:
                direction = "r"
            elif y < p_y:
                direction = "l"
            distance = abs(y - p_y)
        # same col
        elif y == p_y:
            if x > p_x:
                direction = "d"
            elif x < p_x:
                direction = "u"
            distance = abs(x - p_x)

        if direction != None and (0 < distance <= 3):
            self.handle_player_move(direction, distance)

    def auto_npc_move(self):
        if not self.board.game_over:
            for npc in self.npcs:
                direction, _distance = npc.move(self.board)
                self.board.move_character(npc, direction, 1)

            self.draw_board()
            self.root.update()

            if self.board.game_over:
                self._handle_game_over()

            self.root.after(self.npc_move_interval, self.auto_npc_move)

    def draw_board(self):
        self.canvas.delete("all")

        for r in range(self.board._rows):
            for c in range(self.board._cols):
                item = self.board._grid[r][c]
                x1, y1 = c * self.cell_size, r * self.cell_size
                x2, y2 = x1 + self.cell_size, y1 + self.cell_size

                color = "white"
                text = str(item)

                colors = {
                    "M": "gray",
                    "L": "lightblue",
                    "HF": "lightgreen",
                    "SF": "brown",
                    "R": "pink",
                    "-": "white",
                }

                self.canvas.create_rectangle(
                    x1, y1, x2, y2, fill=colors[text], outline="black"
                )
                if text != "-":
                    self.canvas.create_text(
                        (x1 + x2) / 2,
                        (y1 + y2) / 2,
                        text=text,
                        font=("Arial", 12, "bold"),
                    )

        for obj, (r, c) in self.board._objs.items():
            x1, y1 = c * self.cell_size, r * self.cell_size
            x2, y2 = x1 + self.cell_size, y1 + self.cell_size
            color = "green" if isinstance(obj, Player) else "red"

            self.canvas.create_oval(x1 + 5, y1 + 5, x2 - 5, y2 - 5, fill=color)
            self.canvas.create_text(
                (x1 + x2) / 2, (y1 + y2) / 2, text=str(obj), font=("Arial", 10, "bold")
            )

    def handle_close(self):
        answer = messagebox.askquestion(title=None, message="Wanna Leave?")
        if answer == "yes":
            self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    root.title("Ecosystem Saviour")

    app = GameGUI(root, "sample.txt")
    root.mainloop()
