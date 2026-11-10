import random
from Model.Fixed import Fixed
from Model.RepairStation import RepairStation
from Model.Forest import Forest
from Model.Npc import Npc
from Model.IntellectNpc import IntellectNpc
from Model.Player import Player


class Board:
    def __init__(self):
        self._rows: int = 0
        self._cols: int = 0
        # only record static str, M, L, R, SF, HF, -
        self._grid: list[list[str]] = []
        self._forests: dict[Forest, tuple[int, int]] = {}
        self._objs: dict[Npc | Player, tuple[int, int]] = {}
        self._game_over: bool = False

    def load_board(self, file):
        with open(file, "r") as f:
            for row, line in enumerate(f):
                items = line.strip().split(",")
                objects = []

                for col, item in enumerate(items):
                    if item == "M":
                        objects.append(Fixed(item))
                    elif item == "L":
                        objects.append(Fixed(item))
                    elif item == "R":
                        objects.append(RepairStation(item))
                    elif item == "HF" or item == "SF":
                        forest = Forest(item)
                        objects.append(forest)
                        self._forests[forest] = (row, col)
                    else:
                        objects.append(item)

                self._grid.append(objects)

        self._rows = len(self._grid)
        self._cols = len(self._grid[0])

    def print_board(self):
        display_grid = [
            [f"{str(self._grid[r][c]):^3}" for c in range(self._cols)]
            for r in range(self._rows)
        ]

        color = {"npc": 31, "intellectnpc": 31, "player": 32}
        for obj, (x, y) in self._objs.items():
            # map color to npc and player for being recognizable
            display_grid[x][
                y
            ] = f"\033[{color[type(obj).__name__.lower()]}m{str(obj):^3}\033[0m"

        for row in display_grid:
            print(" ".join(row))

    @property
    def game_over(self) -> bool:
        return self._game_over

    @game_over.setter
    def game_over(self, value: bool):
        self._game_over = value

    def get_position(self, obj: Npc | Player) -> tuple[int, int]:
        return self._objs[obj]

    @property
    def all_forests_healthy(self) -> bool:
        return all(not forest.is_sick for forest in self._forests.keys())

    def init_player(self, player: Player):
        self._objs[player] = (0, 0)

    def init_npc(self, characters: list[Npc | IntellectNpc]):
        length = len(characters)
        index = 0

        while index < length:
            x = random.randint(0, self._rows - 1)
            y = random.randint(0, self._cols - 1)
            if self._grid[x][y] == "-" and (x, y) not in self._objs.values():
                obj = characters[index]
                self._objs[obj] = (x, y)
                index += 1

    def move_character(self, character: Npc | Player, direction: str, distance: int):
        if character not in self._objs:
            return

        origin = self.get_position(character)
        step = 0
        for _ in range(distance):
            moves = {"u": (-1, 0), "d": (1, 0), "l": (0, -1), "r": (0, 1)}
            x, y = self._objs[character]
            dx, dy = moves.get(direction, (0, 0))
            nx, ny = x + dx, y + dy

            # perimeter check of matrix
            if not (0 <= nx < self._rows and 0 <= ny < self._cols):
                print("Over Boundary")
                break

            static_target = self._grid[nx][ny]
            # remind: '-' is not a object

            # check if encounter fixed unenterable site
            if (
                hasattr(static_target, "is_enterable")
                and not static_target.is_enterable
            ):
                print(f"{static_target} is not enterable")
                break

            # npc/player can enter/encounter each others
            # repair stations, forests, normal place
            # so update position and deal with afterward process
            self._objs[character] = (nx, ny)

            # check collision between npc and player
            self._check_character_collisions(character, (nx, ny))
            if self.game_over:
                break

            # check if steps on function site, repair and forest
            if hasattr(static_target, "on_stepped_by"):
                static_target.on_stepped_by(character, self)

            step += 1

        destination = self.get_position(character)

        print(
            f"{str(character)} moved from {origin} to {destination} {'at most' if step != distance else ''}"
        )

    def is_valid_position(self, pos: tuple[int, int]) -> bool:
        r, c = pos
        if not (0 <= r < self._rows and 0 <= c < self._cols):
            return False
        target = self._grid[r][c]
        return str(target) not in ("M", "L")

    # internal methods
    def _check_character_collisions(self, mover: Npc | Player, pos: tuple[int, int]):
        for obj, o_pos in self._objs.items():
            if obj != mover and o_pos == pos:
                if (
                    isinstance(obj, Player)
                    and isinstance(mover, Npc)
                    or (isinstance(obj, Npc) and isinstance(mover, Player))
                ):
                    print("Player and NPC encountered! Game Over!")
                    self.game_over = True
