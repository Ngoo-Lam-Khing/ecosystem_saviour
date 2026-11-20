import random
from typing import override
from Model.Constants import DIRECTIONS, directions
from Model.Npc import Npc


class IntellectNpc(Npc):
    def __init__(self, type: str = "INPC"):
        super().__init__(type)

    # get the distance from position 1 to position 2
    def _manhattan_distance(self, pos1: tuple[int, int], pos2: tuple[int, int]) -> int:
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])

    @override
    def move(self, board) -> tuple[str, int]:
        targets: list[tuple[int, int]] = []

        # get player's position if it exists
        if board.player_position is not None:
            targets.append(board.player_position)
        # combine all forests' positions
        targets.extend(board.healthy_forest_positions)
        # if no targets just randomly move
        if not targets:
            return (random.choice(directions), random.randint(1, 3))
        # get self position
        pos = board.get_position(self)
        # get the closest target position from targets array
        closest_target = min(
            targets, key=lambda target: self._manhattan_distance(pos, target)
        )
        # get best (direction, distance)
        best_move: tuple[str, int] | None = None
        # set an infinity float
        min_dist_to_target = float("inf")

        # auto npc only moves 1 square a time for simplicity
        for direction, (dr, dc) in DIRECTIONS.items():
            next_pos = (pos[0] + dr, pos[1] + dc)
            # if next position is accessible, then compute its distance and compare with min_dist_to_target
            # if it is lesser then assign it
            if board.is_valid_position(next_pos):
                dist = self._manhattan_distance(next_pos, closest_target)
                if dist < min_dist_to_target:
                    min_dist_to_target = dist
                    best_move = (direction, 1)

        if best_move is not None:
            return best_move

        return (random.choice(directions), 1)
