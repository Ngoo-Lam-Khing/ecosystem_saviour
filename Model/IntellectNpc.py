import random
from Model.Npc import Npc
from Model.Player import Player


class IntellectNpc(Npc):
    def __init__(self, type="INPC"):
        super().__init__(type)

    def _manhattan_distance(self, pos1: tuple[int, int], pos2: tuple[int, int]) -> int:
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])

    def move(self, board) -> tuple[str, int]:
        directions = ["u", "d", "l", "r"]

        targets = []

        # get player pos into targets
        for character in board._objs:
            if isinstance(character, Player):
                targets.append(board._objs[character])
                break

        for forest in board._forests:
            if not forest.is_sick:
                targets.append(board._forests[forest])

        if len(targets) == 0:
            return (random.choice(directions), random.randint(1, 3))

        pos = board.get_position(self)
        closest_target = min(
            targets, key=lambda target: self._manhattan_distance(pos, target)
        )

        best_move = None
        min_dist_to_target = float("inf")
        valid_fallback_moves = []

        moves = {"u": (-1, 0), "d": (1, 0), "l": (0, -1), "r": (0, 1)}

        # auto npc only moves 1 square a time for simplicity
        for direction, distance in moves.items():
            next_pos = (pos[0] + distance[0], pos[1] + distance[1])

            # if next position is enterable then append fallback list
            # check check if its distance is closer
            if board.is_valid_position(next_pos):
                valid_fallback_moves.append((direction, 1))
                dist = self._manhattan_distance(next_pos, closest_target)

                if dist < min_dist_to_target:
                    min_dist_to_target = dist
                    best_move = (direction, 1)

        if best_move:
            return best_move
        elif valid_fallback_moves:
            return random.choice(valid_fallback_moves)

        return ("u", 1)
