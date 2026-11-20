DIRECTIONS: dict[str, tuple[int, int]] = {
    "u": (-1, 0),
    "d": (1, 0),
    "l": (0, -1),
    "r": (0, 1),
}
directions: list[str] = list(DIRECTIONS.keys())
color: dict[str, int] = {"npc": 31, "intellectnpc": 31, "player": 32}
round_limit: int = 20
