from typing import Generator, Self
from board import Board, Space, Coordinate
import copy


class Node:
    value: Board | None = None
    parent: Self | None = None
    children: list["Node"] = []
    grade: float = float("-inf")
    mine: Coordinate | None = None
    walk: tuple[Coordinate, Coordinate] | None = None
    best_child: None | Self = None

    def __init__(self, value) -> None:
        self.value = value

    def add_child(self, child: Self) -> None:
        self.children.append(child)
        child.parent = self


class Catherine:

    count = 0

    def __init__(self):
        self.name = f"Catherine_{Catherine.count}"
        Catherine.count += 1

    def overall_grade(self, node: Node, color: Space) -> None:
        # TODO: calculate grade for each board in possible boards and return best board, grade
        if node.value is None:
            return
        node.grade = (
            self.grade_board_state_by_walk(node.value, color)
            + self.grade_board_state_by_mine(node.value, color)
        ) / 2
        return

    def minimax(
        self,
        node: Node,
        depth: int,
        is_maximizing: bool,
        alpha: float,
        beta: float,
        color: Space,
        max_depth: int = 2,
    ) -> Node:
        if node.children == [] or depth == max_depth:
            self.overall_grade(node, color)
            return node

        if is_maximizing:
            best = float("-inf")
            child = None
            for child in node.children:
                value = self.minimax(child, depth + 1, False, alpha, beta, color).grade
                bestVal = max(best, value)
                alpha = max(alpha, bestVal)
                if beta <= alpha:
                    break
            node.best_child = child
            return child if child is not None else node
        else:
            best = float("inf")
            child = None
            for child in node.children:
                value = self.minimax(child, depth + 1, False, alpha, beta, color).grade
                bestVal = min(best, value)
                beta = min(alpha, bestVal)
                if beta <= alpha:
                    break
            node.best_child = child
            return child if child is not None else node

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

    def mine(self, board: Board, color: Space) -> Coordinate:
        top = Node(board)
        for node in self.mine_help(top, color, False):
            if type(node) != Node:
                raise ValueError("flag not working")
            next(self.mine_help(node, self.flip_color(color), True))
        best = self.minimax(top, 0, True, float("-inf"), float("inf"), color)
        if best.best_child and best.best_child.mine:
            return best.best_child.mine
        else:
            i = [child.value for child in top.children if child.mine is None]
            raise ValueError(f"{i}")

    def flip_color(self, color: Space) -> Space:
        return Space.RED if color != Space.RED else Space.BLUE

    def mine_help(self, node: Node, color: Space, flag: bool) -> Generator[Node]:
        board = node.value
        if board is None:
            raise ValueError(f"{node.value=}")
        mineable = board.mineable_by_player(color)
        for mine in mineable:
            temp_board = copy.deepcopy(board)
            temp_board[mine] = (
                Space.EMPTY
                if temp_board.count_elements(color) == temp_board.miner_count
                else color
            )
            curr = Node(temp_board)
            node.add_child(curr)
            curr.mine = mine
            if not flag:
                yield curr
        if flag:
            yield node

    def move(self, board: Board, color: Space) -> tuple[Coordinate, Coordinate] | None:
        node = Node(board)
        for start in board.find_all(color):
            ends = board.walkable_from_coord(start)
            for end in ends:
                walk_board = copy.deepcopy(board)
                walk_board[start] = Space.EMPTY
                walk_board[end] = color
                new = Node(walk_board)
                new.walk = (start, end)
                node.add_child(new)
                next(self.mine_help(new, self.flip_color(color), True))
        node.add_child(node)
        self.minimax(node, 0, True, float("-inf"), float("inf"), color)
        print(node.best_child.walk if node.best_child else "no best child")
        return node.best_child.walk if node.best_child is not None else None


if __name__ == "__main__":
    import display

    display.main()
