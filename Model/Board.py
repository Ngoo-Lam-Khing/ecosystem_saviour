import random
from Model.Constants import DIRECTIONS
from Model.Fixed import Fixed
from Model.RepairStation import RepairStation
from Model.Forest import Forest
from Model.Npc import Npc
from Model.Player import Player


class Board:
    def __init__(self):
        self._rows: int = 0
        self._cols: int = 0
        self._grid: list[list[object]] = []
        self._forests: dict[Forest, tuple[int, int]] = {}
        self._objs: dict[Npc | Player, tuple[int, int]] = {}
        self._game_over: bool = False
        self._events: list[str] = []

    @property
    def grid(self) -> list[list[object]]:
        return self._grid

    @property
    def objs(self) -> dict[Npc | Player, tuple[int, int]]:
        return self._objs

    @property
    def rows(self) -> int:
        return self._rows

    @property
    def cols(self) -> int:
        return self._cols

    @property
    def game_over(self) -> bool:
        return self._game_over

    @game_over.setter
    def game_over(self, value: bool) -> None:
        self._game_over = value

    @property
    def all_forests_healthy(self) -> bool:
        return all(not forest.is_sick for forest in self._forests)

    @property
    def player_position(self) -> tuple[int, int] | None:
        for obj, pos in self._objs.items():
            if isinstance(obj, Player):
                return pos
        return None

    @property
    def healthy_forest_positions(self) -> list[tuple[int, int]]:
        return [pos for forest, pos in self._forests.items() if not forest.is_sick]

    # Event queue methods to decouple model state changes from UI/Console output
    def add_event(self, message: str) -> None:
        self._events.append(message)

    def consume_events(self) -> list[str]:
        events = list(self._events)
        self._events.clear()
        return events

    def load_board(self, file: str) -> None:
        # Clear previous board state before loading a new map file
        self._grid.clear()
        self._forests.clear()
        self._objs.clear()
        self._events.clear()
        self._game_over = False

        # Parse comma-separated tile codes into corresponding domain objects
        with open(file, "r", encoding="utf-8") as f:
            for row, line in enumerate(f):
                stripped = line.strip()
                if not stripped:
                    continue
                items = stripped.split(",")
                objects: list[object] = []

                for col, item in enumerate(items):
                    if item in ("M", "L"):
                        objects.append(Fixed(item))
                    elif item == "R":
                        objects.append(RepairStation(item))
                    elif item in ("HF", "SF"):
                        forest = Forest(item)
                        objects.append(forest)
                        self._forests[forest] = (row, col)
                    else:
                        objects.append(item)

                self._grid.append(objects)

        if not self._grid:
            raise ValueError("Board file is empty.")

        self._rows = len(self._grid)
        self._cols = len(self._grid[0])

    def get_position(self, obj: Npc | Player) -> tuple[int, int]:
        return self._objs[obj]

    def init_player(self, player: Player) -> None:
        player.reset()
        self._objs[player] = (0, 0)

    def init_npc(self, npcs: list[Npc]) -> None:
        # Collect all empty ('-') tiles not currently occupied by another character
        occupied = set(self._objs.values())
        available_positions = [
            (r, c)
            for r in range(self._rows)
            for c in range(self._cols)
            if self._grid[r][c] == "-" and (r, c) not in occupied
        ]

        if len(available_positions) < len(npcs):
            raise ValueError(
                f"Not enough empty tiles ({len(available_positions)}) for {len(npcs)} NPCs."
            )

        # Randomly assign distinct valid spawn positions to each NPC
        chosen_positions = random.sample(available_positions, len(npcs))
        for npc, pos in zip(npcs, chosen_positions):
            self._objs[npc] = pos

    def move_character(
        self, character: Npc | Player, direction: str, distance: int
    ) -> None:
        if character not in self._objs:
            return

        origin = self.get_position(character)
        step = 0
        dx, dy = DIRECTIONS.get(direction, (0, 0))

        # Execute movement one tile at a time to check intermediate obstacles and triggers
        for _ in range(distance):
            x, y = self._objs[character]
            nx, ny = x + dx, y + dy

            # Stop movement if the next step exceeds board boundaries
            if not (0 <= nx < self._rows and 0 <= ny < self._cols):
                self.add_event("Over Boundary")
                break

            static_target = self._grid[nx][ny]
            # Note: empty floor tiles '-' are raw strings and default to enterable=True
            if not getattr(static_target, "is_enterable", True):
                self.add_event(f"{static_target} is not enterable")
                break

            self._objs[character] = (nx, ny)
            step += 1

            # Check for player-NPC encounter on every intermediate tile
            self._check_character_collisions(character, (nx, ny))
            if self.game_over:
                break

            # Trigger interactive tile effects (e.g., Forest, RepairStation)
            if hasattr(static_target, "on_stepped_by"):
                static_target.on_stepped_by(character, self)
                if self.game_over:
                    break

        destination = self.get_position(character)
        suffix = " at most" if step != distance else ""
        self.add_event(f"{character} moved from {origin} to {destination}{suffix}")

    def is_valid_position(self, pos: tuple[int, int]) -> bool:
        r, c = pos
        if not (0 <= r < self._rows and 0 <= c < self._cols):
            return False
        target = self._grid[r][c]
        return getattr(target, "is_enterable", True)

    def _check_character_collisions(
        self, mover: Npc | Player, pos: tuple[int, int]
    ) -> None:
        # End the game immediately if a Player and an NPC occupy the same coordinates
        for obj, o_pos in self._objs.items():
            if obj != mover and o_pos == pos:
                if (isinstance(obj, Player) and isinstance(mover, Npc)) or (
                    isinstance(obj, Npc) and isinstance(mover, Player)
                ):
                    self.add_event("Player and NPC encountered! Game Over!")
                    self.game_over = True
                    return
