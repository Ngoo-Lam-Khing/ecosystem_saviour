from collections import (
    defaultdict,
)  # [新增] 用於將同一格的多個角色分組，避免重疊時互相遮蓋
import tkinter as tk
from tkinter import messagebox, simpledialog
from Model.Board import Board
from Model.Npc import Npc
from Model.IntellectNpc import IntellectNpc
from Model.Player import Player


class GameGUI:
    # [修改] 將顏色對照表抽成類別常數，避免每次重繪都在雙層迴圈中重複建立字典
    # Map grid symbols to background colors as a class constant to avoid rebuilding on every redraw
    CELL_COLORS: dict[str, str] = {
        "M": "gray",
        "L": "lightblue",
        "HF": "lightgreen",
        "SF": "brown",
        "R": "pink",
        "-": "white",
    }

    def __init__(self, root: tk.Tk, file: str):
        self.root = root
        self.file = file
        self.board = Board()
        self.player = Player()
        self.npcs: list[Npc] = []

        self.cell_size = 50
        self.turn = 0
        self.turn_limit = 20
        self.npc_move_interval = 1000
        # [新增] 記錄計時器 ID，方便在遊戲結束或暫停時用 after_cancel 取消，避免重開局計時器失效或疊加
        # Track the active Tkinter 'after' callback ID to prevent duplicate or dangling timers
        self.npc_timer_id: str | None = None

        self.score_var = tk.StringVar()
        self.turn_var = tk.StringVar()
        # [新增] 新增材料持有狀態的文字變數，讓玩家在介面上看得到是否有材料
        self.material_var = tk.StringVar()

        # [修改] 將建立介面、初始化遊戲、綁定事件拆分為獨立方法，提升程式可讀性
        self._build_ui()
        self._init_game()
        self._bind_events()

    def _ask_turn_limit(self) -> int:
        # 跳出整數輸入視窗，minvalue=1 會自動擋掉文字、0 或負數
        # Prompt user for a valid positive integer; retain previous turn_limit if cancelled
        limit = simpledialog.askinteger(
            title="Turn Limit",
            prompt="Please enter the turn limit:",
            parent=self.root,
            minvalue=1,
            initialvalue=self.turn_limit,
        )
        # 若玩家按「取消」回傳 None，則沿用原本的預設值或上一局設定
        return limit if limit is not None else self.turn_limit

    def _build_ui(self) -> None:
        info_frame = tk.Frame(self.root)
        info_frame.pack(pady=4)

        # [修改] 修正原本 self.label 被連續覆蓋兩次的問題，並改為橫向並排顯示資訊
        self.score_label = tk.Label(info_frame, textvariable=self.score_var)
        self.score_label.pack(side=tk.LEFT, padx=8)

        self.turn_label = tk.Label(info_frame, textvariable=self.turn_var)
        self.turn_label.pack(side=tk.LEFT, padx=8)

        # [新增] 顯示玩家目前是否持有修復材料
        self.material_label = tk.Label(info_frame, textvariable=self.material_var)
        self.material_label.pack(side=tk.LEFT, padx=8)

        self.canvas = tk.Canvas(self.root)
        self.canvas.pack()

    def _bind_events(self) -> None:
        self.root.bind("<Up>", lambda _e: self.handle_player_move("u"))
        self.root.bind("<Down>", lambda _e: self.handle_player_move("d"))
        self.root.bind("<Left>", lambda _e: self.handle_player_move("l"))
        self.root.bind("<Right>", lambda _e: self.handle_player_move("r"))
        # [修改] 改為只對畫布 (canvas) 綁定滑鼠左鍵 (<Button-1>)，避免點擊上方文字標籤或滾輪/右鍵時誤觸移動
        # Bind left-click strictly to the canvas so clicking status labels won't trigger movement
        self.canvas.bind("<Button-1>", self.handle_player_click)
        self.root.bind_all("q", lambda _e: self.handle_close())
        self.root.bind_all("Q", lambda _e: self.handle_close())
        # [新增] 攔截視窗右上角的 X 關閉按鈕，統一跳出離開確認視窗
        # Intercept window close button (X) to route through the exit confirmation dialog
        self.root.protocol("WM_DELETE_WINDOW", self.handle_close)

    def _init_game(self) -> None:
        # [新增] 重開新局前先取消舊的 NPC 計時器，防止多個計時器同時運作
        # Cancel any existing NPC timer before resetting state for a new game
        self._stop_npc_timer()

        self.board = Board()
        self.board.load_board(self.file)

        self.player = Player()
        self.board.init_player(self.player)

        self.npcs = [IntellectNpc()] + [Npc() for _ in range(2)]
        self.board.init_npc(self.npcs)

        self.turn = 0
        self._update_status_labels()

        # Resize canvas and root window dynamically based on loaded board dimensions
        width = self.board.cols * self.cell_size
        height = self.board.rows * self.cell_size
        # [新增] 重開局時同步更新畫布尺寸
        self.canvas.config(width=width, height=height)
        self.root.geometry(f"{width}x{height + 35}")

        self.draw_board()
        self.root.update_idletasks()
        self.turn_limit = self._ask_turn_limit()
        self._update_status_labels()
        # [修改] 透過統一的計時器管理方法啟動 NPC 自動移動
        self._start_npc_timer()

    # [新增] 集中更新分數、回合數與材料狀態顯示
    def _update_status_labels(self) -> None:
        self.score_var.set(f"Score: {self.player.score}")
        self.turn_var.set(f"Turn: {self.turn}/{self.turn_limit}")
        self.material_var.set(
            f"Material: {'Yes' if self.player.has_material else 'No'}"
        )

    # [新增] 統一啟動 NPC 移動計時器
    def _start_npc_timer(self) -> None:
        # Ensure at most one periodic NPC movement timer is scheduled at a time
        self._stop_npc_timer()
        self.npc_timer_id = self.root.after(self.npc_move_interval, self.auto_npc_move)

    # [新增] 統一取消 NPC 移動計時器
    def _stop_npc_timer(self) -> None:
        if self.npc_timer_id is not None:
            self.root.after_cancel(self.npc_timer_id)
            self.npc_timer_id = None

    def _handle_game_over(self) -> None:
        if not self.board.game_over:
            return

        # [新增] 遊戲結束時立即停止計時器，避免跳出視窗期間 NPC 繼續在背景移動
        # Halt background NPC movement immediately while modal dialogs are displayed
        self._stop_npc_timer()
        # [修改] 改用 update_idletasks() 確保畫布完成最後畫面更新，避免 root.update() 引發事件重入問題
        # Flush pending drawing tasks safely without triggering full event re-entrancy
        self.canvas.update_idletasks()

        score = self.player.score
        messagebox.showinfo(
            title="Game Over",
            # [修改] 修正單複數判斷 (原本 score > 1 會讓 0 分顯示為 "0 point")
            message=f"You got {score} point{'s' if score != 1 else ''} in total",
        )
        if messagebox.askyesno(title="Game Over", message="Play Again?"):
            self._init_game()
        else:
            self.root.destroy()

    def handle_player_move(self, direction: str, distance: int = 1) -> None:
        if self.board.game_over:
            return

        self.board.move_character(self.player, direction, distance)
        self.turn += 1
        # [修改] 同步更新材料狀態與分數顯示，並移除原本容易造成重入風險的 self.root.update()
        self._update_status_labels()
        self.draw_board()

        # End game if player reaches or exceeds the configured turn limit
        if self.turn >= self.turn_limit:
            self.board.game_over = True

        self._handle_game_over()

    def handle_player_click(self, event: tk.Event) -> None:
        # [新增] 遊戲結束後忽略滑鼠點擊
        if self.board.game_over:
            return
        # Convert clicked pixel coordinates into grid row/column indices
        target_r = event.y // self.cell_size
        target_c = event.x // self.cell_size
        # [修改] 改用公開方法 get_position() 取得玩家座標，並移除原本除錯用的 print()
        player_r, player_c = self.board.get_position(self.player)

        direction: str | None = None
        distance = 0
        # Allow orthogonal movement along the same row or column
        if target_r == player_r:
            if target_c > player_c:
                direction = "r"
            elif target_c < player_c:
                direction = "l"
            distance = abs(target_c - player_c)
        elif target_c == player_c:
            if target_r > player_r:
                direction = "d"
            elif target_r < player_r:
                direction = "u"
            distance = abs(target_r - player_r)

        # [修改] 改用符合 PEP 8 規範的 is not None 判斷
        # Restrict click-to-move range between 1 and 3 tiles
        if direction is not None and (0 < distance <= 3):
            self.handle_player_move(direction, distance)

    def auto_npc_move(self) -> None:
        if self.board.game_over:
            return

        for npc in self.npcs:
            # [新增] 若其中一隻 NPC 撞到玩家導致遊戲結束，立即中斷迴圈，不讓剩餘 NPC 繼續移動
            # Stop remaining NPCs from moving if an earlier NPC already ended the game
            if self.board.game_over:
                break
            direction, _distance = npc.move(self.board)
            self.board.move_character(npc, direction, 1)

        self._update_status_labels()
        self.draw_board()

        if self.board.game_over:
            self._handle_game_over()
        else:
            # [修改] 確認遊戲尚未結束才排程下一次移動，解決重開局後計時器可能永久中斷的問題
            # Reschedule next NPC tick only while the game remains active
            self._start_npc_timer()

    def draw_board(self) -> None:
        self.canvas.delete("all")

        # 1. Render static terrain tiles
        for r in range(self.board.rows):
            for c in range(self.board.cols):
                item = self.board.grid[r][c]
                x1, y1 = c * self.cell_size, r * self.cell_size
                x2, y2 = x1 + self.cell_size, y1 + self.cell_size

                text = str(item)
                fill_color = self.CELL_COLORS.get(text, "white")

                self.canvas.create_rectangle(
                    x1, y1, x2, y2, fill=fill_color, outline="black"
                )
                if text != "-":
                    self.canvas.create_text(
                        (x1 + x2) / 2,
                        (y1 + y2) / 2,
                        text=text,
                        font=("Arial", 12, "bold"),
                    )
        # 2. Group dynamic entities by grid position to handle co-located characters cleanly
        # record the objects' positions and group them by their coordinates
        grouped_objs: dict[tuple[int, int], list[object]] = defaultdict(list)
        for obj, pos in self.board.objs.items():
            grouped_objs[pos].append(obj)

        for (r, c), objs_at_pos in grouped_objs.items():
            x1, y1 = c * self.cell_size, r * self.cell_size
            x2, y2 = x1 + self.cell_size, y1 + self.cell_size

            has_player = any(isinstance(o, Player) for o in objs_at_pos)
            npcs_at_pos = [o for o in objs_at_pos if not isinstance(o, Player)]
            # 情況 1：玩家與 NPC 撞在同一格 -> 原地重疊，上層玩家設為 50% 透明度
            # Case 1: Player and NPC(s) occupy the same tile (collision state)
            if has_player and npcs_at_pos:
                npc_label = (
                    str(npcs_at_pos[0])
                    if len(npcs_at_pos) == 1
                    else f"N*{len(npcs_at_pos)}"
                )
                # 1. 底層先畫出實心 NPC（紅色）
                # Draw solid red NPC base layer
                self.canvas.create_oval(
                    x1 + 5,
                    y1 + 5,
                    x2 - 5,
                    y2 - 5,
                    fill="red",
                    outline="black",
                    width=1,
                )

                # 2. 上層同座標疊上玩家（綠色 + gray50 遮罩模擬 50% 透明度，讓底層紅色透出來）
                # Overlay player with 50% stipple transparency so both entities remain visible
                outline_color = "gold" if self.player.has_material else "black"
                outline_width = 3 if self.player.has_material else 1
                self.canvas.create_oval(
                    x1 + 5,
                    y1 + 5,
                    x2 - 5,
                    y2 - 5,
                    fill="green",
                    stipple="gray50",
                    outline=outline_color,
                    width=outline_width,
                )

                # 3. 文字顯示合併代號，避免兩組字疊在正中央糊在一起
                self.canvas.create_text(
                    (x1 + x2) / 2,
                    (y1 + y2) / 2,
                    text=f"{self.player}+{npc_label}",
                    fill="white",
                    font=("Arial", 8, "bold"),
                )
                continue

            # Case 2: Single entity type at this tile (Player, single NPC, or stacked NPCs)
            if has_player:
                fill_color = "green"
                # [新增] 玩家持有材料時加上金色粗外框作為視覺提示
                # Highlight player border in gold when carrying repair material
                outline_color = "gold" if self.player.has_material else "black"
                outline_width = 3 if self.player.has_material else 1
                label = str(self.player)
            elif len(objs_at_pos) == 1:
                fill_color = "red"
                outline_color = "black"
                outline_width = 1
                label = str(objs_at_pos[0])
            else:
                # [新增] 多隻 NPC 同格時改以深紅色與 "N*數量" 提示，避免後畫的圓形完全遮住前者
                # Visually indicate multiple stacked NPCs on the same tile
                fill_color = "darkred"
                outline_color = "black"
                outline_width = 1
                label = f"N*{len(objs_at_pos)}"

            self.canvas.create_oval(
                x1 + 5,
                y1 + 5,
                x2 - 5,
                y2 - 5,
                fill=fill_color,
                outline=outline_color,
                width=outline_width,
            )
            self.canvas.create_text(
                (x1 + x2) / 2,
                (y1 + y2) / 2,
                text=label,
                fill="white",  # [新增] 改用白色字體提高深色圓形上的對比度
                font=("Arial", 10, "bold"),
            )

    def handle_close(self) -> None:
        # [新增] 跳出離開確認視窗時先暫停 NPC 計時器；若玩家選擇留下且遊戲未結束則恢復計時
        # Pause NPC timer while confirmation dialog is open; resume if user stays
        self._stop_npc_timer()
        if messagebox.askyesno(title="Exit", message="Wanna Leave?"):
            self.root.destroy()
        elif not self.board.game_over:
            self._start_npc_timer()


if __name__ == "__main__":
    root = tk.Tk()
    root.title("Ecosystem Saviour")
    app = GameGUI(root, "sample.txt")
    root.mainloop()
