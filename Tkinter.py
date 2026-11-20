# Group co-located characters on the same tile to prevent overlapping occlusion
# 用於將同一格的多個角色分組，避免重疊時互相遮蓋
from collections import defaultdict
import os
import tkinter as tk
from tkinter import messagebox, simpledialog
from Model.Board import Board
from Model.Npc import Npc
from Model.IntellectNpc import IntellectNpc
from Model.Player import Player


class GameGUI:
    # Map grid symbols to background colors as a class constant to avoid rebuilding on every redraw
    # 將顏色對照表抽成類別常數，避免每次重繪都在雙層迴圈中重複建立字典
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
        # Track the active Tkinter 'after' callback ID to prevent duplicate or dangling timers
        # 記錄計時器 ID，方便在遊戲結束或暫停時用 after_cancel 取消，避免重開局計時器失效或疊加
        self.npc_timer_id: str | None = None
        # Store the specific reason why the game ended for the final summary popup
        # 記錄遊戲結束的具體原因，供結算彈窗顯示
        self.game_over_reason = ""

        self.score_var = tk.StringVar()
        self.turn_var = tk.StringVar()
        # Track material inventory and real-time board event/error messages on the UI
        # 追蹤材料持有狀態與即時棋盤事件、錯誤訊息顯示
        self.material_var = tk.StringVar()
        self.status_var = tk.StringVar()

        # Modularize UI setup, game initialization, and event bindings for better readability
        # 將建立介面、初始化遊戲、綁定事件拆分為獨立方法，提升程式可讀性
        self._build_ui()
        self._init_game()
        self._bind_events()

    def _ask_turn_limit(self) -> int:
        # Prompt user for a valid positive integer; retain previous turn_limit if cancelled
        # 跳出整數輸入視窗，minvalue=1 會自動擋掉文字、0 或負數；若按取消則沿用原本設定
        limit = simpledialog.askinteger(
            title="Turn Limit",
            prompt="Please enter the turn limit:",
            parent=self.root,
            minvalue=1,
            initialvalue=self.turn_limit,
        )
        return limit if limit is not None else self.turn_limit

    def _build_ui(self) -> None:
        info_frame = tk.Frame(self.root)
        info_frame.pack(pady=(4, 2))

        # Display score, turn count, and material status horizontally
        # 橫向並排顯示分數、回合數與目前是否持有修復材料
        self.score_label = tk.Label(info_frame, textvariable=self.score_var)
        self.score_label.pack(side=tk.LEFT, padx=8)

        self.turn_label = tk.Label(info_frame, textvariable=self.turn_var)
        self.turn_label.pack(side=tk.LEFT, padx=8)

        self.material_label = tk.Label(info_frame, textvariable=self.material_var)
        self.material_label.pack(side=tk.LEFT, padx=8)

        # Reserve fixed 2-line height so long status messages wrap cleanly without resizing the window
        # 固定預留 2 行文字高度並置中對齊，避免操作訊息過長或換行時導致視窗上下跳動
        self.status_label = tk.Label(
            self.root,
            textvariable=self.status_var,
            height=2,
            justify=tk.CENTER,
        )
        self.status_label.pack(pady=(0, 4))

        self.canvas = tk.Canvas(self.root)
        self.canvas.pack()

    def _bind_events(self) -> None:
        # Support both arrow keys and u/d/l/r (upper & lower case) for player movement
        # 同時支援方向鍵與 u/d/l/r（大小寫皆可）控制玩家移動
        move_bindings = (
            ("<Up>", "u"),
            ("<Down>", "d"),
            ("<Left>", "l"),
            ("<Right>", "r"),
            ("u", "u"),
            ("U", "u"),
            ("d", "d"),
            ("D", "d"),
            ("l", "l"),
            ("L", "l"),
            ("r", "r"),
            ("R", "r"),
        )
        for key, direction in move_bindings:
            self.root.bind(key, lambda _e, d=direction: self.handle_player_move(d))

        # Bind left-click strictly to the canvas so clicking status labels won't trigger movement
        # 改為只對畫布 (canvas) 綁定滑鼠左鍵 (<Button-1>)，避免點擊上方文字標籤或滾輪/右鍵時誤觸移動
        self.canvas.bind("<Button-1>", self.handle_player_click)
        self.root.bind_all("q", lambda _e: self.handle_close())
        self.root.bind_all("Q", lambda _e: self.handle_close())
        # Intercept window close button (X) to route through the exit confirmation dialog
        # 攔截視窗右上角的 X 關閉按鈕，統一跳出離開確認視窗
        self.root.protocol("WM_DELETE_WINDOW", self.handle_close)

    def _resolve_board_file(self) -> str:
        # Support both current working directory and script-relative paths for board files
        # 同時支援當前執行目錄與程式所在目錄尋找地圖檔，避免不同執行路徑找不到檔案
        if os.path.exists(self.file):
            return self.file
        script_dir = os.path.dirname(os.path.abspath(__file__))
        candidate = os.path.join(script_dir, self.file)
        return candidate if os.path.exists(candidate) else self.file

    def _init_game(self) -> None:
        # Cancel any existing NPC timer before resetting state for a new game
        # 重開新局前先取消舊的 NPC 計時器，防止多個計時器同時運作
        self._stop_npc_timer()

        self.board = Board()
        self.board.load_board(self._resolve_board_file())

        self.player = Player()
        self.board.init_player(self.player)

        self.npcs = [IntellectNpc()] + [Npc() for _ in range(2)]
        self.board.init_npc(self.npcs)

        # Clear any startup events and reset UI status text
        # 清空初始化階段的事件佇列並重設畫面提示文字
        self.board.consume_events()
        self.game_over_reason = ""
        self.status_var.set("Use arrows, U/D/L/R, or click 1-3 tiles.")

        self.turn = 0
        self._update_status_labels()

        # Resize canvas dynamically and constrain status label wrapping to the board width
        # 依棋盤尺寸調整畫布大小，並限制提示列自動換行寬度不超過棋盤寬度，防止視窗被撐寬
        width = self.board.cols * self.cell_size
        height = self.board.rows * self.cell_size
        self.canvas.config(width=width, height=height)
        self.status_label.config(wraplength=max(width - 16, 200))
        self.root.geometry("")
        self.root.resizable(False, False)

        self.draw_board()
        self.root.update_idletasks()
        self.turn_limit = self._ask_turn_limit()
        self._update_status_labels()
        self._start_npc_timer()

    def _update_status_labels(self) -> None:
        # Centralize updates for score, turn count, and material status labels
        # 集中更新分數、回合數與材料狀態顯示
        self.score_var.set(f"Score: {self.player.score}")
        self.turn_var.set(f"Turn: {self.turn}/{self.turn_limit}")
        self.material_var.set(
            f"Material: {'Yes' if self.player.has_material else 'No'}"
        )

    def _process_board_events(self, is_player_action: bool = False) -> None:
        # Drain accumulated model events to prevent memory buildup and capture critical alerts
        # 讀取並清空模型事件佇列，擷取遊戲結束原因並防止背景 NPC 移動洗掉玩家操作提示
        events = self.board.consume_events()
        if not events:
            return

        if self.board.game_over:
            # Extract specific game-over trigger message if available
            # 優先擷取觸發遊戲結束的關鍵訊息（相撞、無材料進生病森林或回合上限）
            game_over_msgs = [
                e
                for e in events
                if "game over" in e.lower()
                or "sick" in e.lower()
                or "encountered" in e.lower()
            ]
            self.game_over_reason = (
                " | ".join(game_over_msgs) if game_over_msgs else " | ".join(events)
            )
            self.status_var.set(self.game_over_reason)
        elif is_player_action:
            # Update status bar on player actions without letting background NPC ticks overwrite it
            # 僅在玩家主動操作時更新提示列，避免每秒自動移動的 NPC 洗掉錯誤回饋
            self.status_var.set(" | ".join(events))

    def _start_npc_timer(self) -> None:
        # Ensure at most one periodic NPC movement timer is scheduled at a time
        # 統一啟動 NPC 移動計時器，確保同一時間只有一個計時器在運作
        self._stop_npc_timer()
        self.npc_timer_id = self.root.after(self.npc_move_interval, self.auto_npc_move)

    def _stop_npc_timer(self) -> None:
        # Cancel the active NPC movement timer safely
        # 統一取消 NPC 移動計時器
        if self.npc_timer_id is not None:
            self.root.after_cancel(self.npc_timer_id)
            self.npc_timer_id = None

    def _handle_game_over(self) -> None:
        if not self.board.game_over:
            return

        # Halt background NPC movement immediately while modal dialogs are displayed
        # 遊戲結束時立即停止計時器，避免跳出視窗期間 NPC 繼續在背景移動
        self._stop_npc_timer()
        # Flush pending drawing tasks safely without triggering full event re-entrancy
        # 改用 update_idletasks() 確保畫布完成最後畫面更新，避免 root.update() 引發事件重入問題
        self.canvas.update_idletasks()

        score = self.player.score
        reason_line = f"{self.game_over_reason}\n" if self.game_over_reason else ""
        messagebox.showinfo(
            title="Game Over",
            # Handle singular/plural wording properly (e.g., 0 points, 1 point, 2 points)
            # 修正單複數判斷（0 分顯示為 "0 points"，1 分為 "1 point"）
            message=(
                f"{reason_line}"
                f"You got {score} point{'s' if score != 1 else ''} in total"
            ),
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

        # End game if player reaches or exceeds the configured turn limit
        # 若玩家達到或超過設定的回合上限則結束遊戲
        if not self.board.game_over and self.turn >= self.turn_limit:
            self.board.game_over = True
            self.board.add_event("Turn limit reached! Game Over!")

        self._process_board_events(is_player_action=True)
        self._update_status_labels()
        self.draw_board()
        self._handle_game_over()

    def handle_player_click(self, event: tk.Event) -> None:
        # Ignore mouse clicks after the game has ended
        # 遊戲結束後忽略滑鼠點擊
        if self.board.game_over:
            return

        # Convert clicked pixel coordinates into grid row/column indices
        # 將點擊的像素座標換算為棋盤的列與行索引
        target_r = event.y // self.cell_size
        target_c = event.x // self.cell_size
        player_r, player_c = self.board.get_position(self.player)

        if target_r == player_r and target_c == player_c:
            return

        direction: str | None = None
        distance = 0

        # Allow orthogonal movement along the same row or column
        # 僅允許沿同一列或同一行進行上下左右直線移動
        if target_r == player_r:
            direction = "r" if target_c > player_c else "l"
            distance = abs(target_c - player_c)
        elif target_c == player_c:
            direction = "d" if target_r > player_r else "u"
            distance = abs(target_r - player_r)

        # Restrict click-to-move range between 1 and 3 orthogonal tiles
        # 限制滑鼠點擊移動的距離必須在 1 到 3 格之間
        if direction is not None and (0 < distance <= 3):
            self.handle_player_move(direction, distance)
        else:
            self.status_var.set(
                "Invalid move: click 1-3 tiles horizontally or vertically."
            )

    def auto_npc_move(self) -> None:
        if self.board.game_over:
            return

        for npc in self.npcs:
            # Stop remaining NPCs from moving if an earlier NPC already ended the game
            # 若其中一隻 NPC 撞到玩家導致遊戲結束，立即中斷迴圈，不讓剩餘 NPC 繼續移動
            if self.board.game_over:
                break
            # Use the actual distance determined by each NPC's strategy (1 for IntellectNpc, 1-3 for Npc)
            # 依照各 NPC 策略回傳的實際距離移動（智慧型 NPC 為 1 格，一般 NPC 為 1-3 格）
            direction, distance = npc.move(self.board)
            self.board.move_character(npc, direction, distance)

        self._process_board_events(is_player_action=False)
        self._update_status_labels()
        self.draw_board()

        if self.board.game_over:
            self._handle_game_over()
        else:
            # Reschedule next NPC tick only while the game remains active
            # 確認遊戲尚未結束才排程下一次移動，解決重開局後計時器可能永久中斷的問題
            self._start_npc_timer()

    def draw_board(self) -> None:
        self.canvas.delete("all")

        # 1. Render static terrain tiles
        # 1. 繪製靜態地形格子
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
        # 2. 依座標將動態角色分組，避免同格重疊時互相遮蓋
        grouped_objs: dict[tuple[int, int], list[object]] = defaultdict(list)
        for obj, pos in self.board.objs.items():
            grouped_objs[pos].append(obj)

        for (r, c), objs_at_pos in grouped_objs.items():
            x1, y1 = c * self.cell_size, r * self.cell_size
            x2, y2 = x1 + self.cell_size, y1 + self.cell_size

            has_player = any(isinstance(o, Player) for o in objs_at_pos)
            npcs_at_pos = [o for o in objs_at_pos if not isinstance(o, Player)]

            # Case 1: Player and NPC(s) occupy the same tile (collision state)
            # 情況 1：玩家與 NPC 撞在同一格 -> 原地重疊，上層玩家設為 50% 透明度
            if has_player and npcs_at_pos:
                npc_label = (
                    str(npcs_at_pos[0])
                    if len(npcs_at_pos) == 1
                    else f"N*{len(npcs_at_pos)}"
                )
                # Draw solid red NPC base layer
                # 底層先畫出實心 NPC（紅色）
                self.canvas.create_oval(
                    x1 + 5,
                    y1 + 5,
                    x2 - 5,
                    y2 - 5,
                    fill="red",
                    outline="black",
                    width=1,
                )

                # Overlay player with 50% stipple transparency so both entities remain visible
                # 上層同座標疊上玩家（綠色 + gray50 遮罩模擬 50% 透明度，讓底層紅色透出來）
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

                # Display combined label so two overlapping texts do not blur together
                # 文字顯示合併代號，避免兩組字疊在正中央糊在一起
                self.canvas.create_text(
                    (x1 + x2) / 2,
                    (y1 + y2) / 2,
                    text=f"{self.player}+{npc_label}",
                    fill="white",
                    font=("Arial", 8, "bold"),
                )
                continue

            # Case 2: Single entity type at this tile (Player, single NPC, or stacked NPCs)
            # 情況 2：單一類型角色在此格（玩家、單隻 NPC 或多隻重疊 NPC）
            if has_player:
                fill_color = "green"
                # Highlight player border in gold when carrying repair material
                # 玩家持有材料時加上金色粗外框作為視覺提示
                outline_color = "gold" if self.player.has_material else "black"
                outline_width = 3 if self.player.has_material else 1
                label = str(self.player)
            elif len(objs_at_pos) == 1:
                fill_color = "red"
                outline_color = "black"
                outline_width = 1
                label = str(objs_at_pos[0])
            else:
                # Visually indicate multiple stacked NPCs on the same tile
                # 多隻 NPC 同格時改以深紅色與 "N*數量" 提示，避免後畫的圓形完全遮住前者
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
                fill="white",
                font=("Arial", 10, "bold"),
            )

    def handle_close(self) -> None:
        # Pause NPC timer while confirmation dialog is open; resume if user stays
        # 跳出離開確認視窗時先暫停 NPC 計時器；若玩家選擇留下且遊戲未結束則恢復計時
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
