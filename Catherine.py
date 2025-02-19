from dataclasses import Field, dataclass
from typing import Self
from board import Board, Space, Coordinate
import copy


class Node:
    value: Board | None = None
    parent: Self | None = None
    children: list["Node"] = []
    grade: float = float("-inf")
    children_as_board: list[Board] = []

    def __init__(self, value) -> None:
        self.value = value

class Catherine:

    count = 0

    def __init__(self):
        self.name = f"Catherine_{Catherine.count}"
        Catherine.count += 1

    def overall_grade(
        self, possible_boards: list[Board], color: Space
    ) -> tuple[Board, float]:
        # TODO: calculate grade for each board in possible boards and return best board, grade
        best = []
        for board in possible_boards:
            best.append(
                (
                    board,
                    (
                        self.grade_board_state_by_walk(board, color)
                        + self.grade_board_state_by_mine(board, color)
                    )
                    / 2,
                )
            )
        return max(best, key=lambda x: x[1])

    def grade_board_state_by_walk(self, board: Board, color: Space) -> float:
        enemy = Space.RED if color != Space.RED else Space.BLUE
        a = len(Board.walkable_by_player(board, color))
        b = len(Board.walkable_by_player(board, enemy)) * 1.2
        for miner in board.find_all(color):
            if board.is_miner_dead(miner):
                b += 10
        for miner in board.find_all(enemy):
            if board.is_miner_dead(miner):
                a += 2
        grade = a - b
        return grade

    def grade_board_state_by_mine(self, board: Board, color: Space) -> float:
        enemy = Space.RED if color != Space.RED else Space.BLUE
        a = len(Board.mineable_by_player(board, color))
        b = len(Board.mineable_by_player(board, enemy))
        for miner in board.find_all(color):
            if board.is_miner_dead(miner):
                b += 10
        grade = a - b
        return grade

        """
    def mine_help(self, boards: set[Board], color: Space) -> Coordinate:
        for board in boards:
            self.grade_board_state_by_mine(board, color)
        """

    def mine(self, board: Board, color: Space, flag: bool = True) -> Coordinate:
        top = Node(board)
        dict_boards: dict[Board, Coordinate] = {}
        new_dict, top = self.mine_help(top, color)
        dict_boards.update(new_dict if new_dict is not None else {})
        best_board = self.overall_grade(top.children_as_board, color)[0]
        return dict_boards[best_board]

    def flip_color(self, color: Space) -> Space:
        return Space.RED if color != Space.RED else Space.BLUE
  
    def mine_help(self, node: Node, color: Space) -> tuple[dict, Node] | tuple[None, Node]:
        board = node.value
        if board is None:
            return None, node
        mineable = board.mineable_by_player(color)
        dict_boards: dict[Board, Coordinate] = {}
        for mine in mineable:
            temp_board = copy.deepcopy(board)
            temp_board[mine] = (
                Space.EMPTY
                if temp_board.count_elements(color) == temp_board.miner_count
                else color
            )
            curr = Node(temp_board)
            curr.parent = node
            node.children += [curr]
            node.children_as_board += [temp_board]
            dict_boards.update({temp_board: mine})
        return dict_boards, node

    def move(self, board: Board, color: Space) -> tuple[Coordinate, Coordinate] | None:
        pieces = board.find_all(color)
        dict_boards: dict[Board, tuple[Coordinate, Coordinate] | None] = {board: None}
        boards = [board]
        for start in pieces:
            ends = board.walkable_from_coord(start)
            for end in ends:
                temp_board = copy.deepcopy(board)
                temp_board[start] = Space.EMPTY
                temp_board[end] = color
                boards.append(temp_board)
                dict_boards.update({temp_board: (start, end)})
        best = self.overall_grade(boards, color)[0]
        return dict_boards[best]
