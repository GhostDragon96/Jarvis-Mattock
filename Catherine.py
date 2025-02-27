from typing import Generator, Self
from board import Board, Space, Coordinate
import copy
from time import time


class Node:

    def __init__(self, value: Board) -> None:
        self.value = value
        self.parent: Node | None = None
        self.children: list[Node] = []
        self.grade: float = float("-inf")
        self.mine: Coordinate | None = None
        self.walk: tuple[Coordinate, Coordinate] | None = None
        self.best_child: Node | None = None

    def add_child(self, child: Self) -> None:
        self.children.append(child)
        child.parent = self


class Catherine:

    count = 0

    def __init__(self, modifiers: tuple[float,float,float,float,float] = (10, 10, 10, 1, 200)):
        self.name = f"Catherine_{Catherine.count}"
        Catherine.count += 1
        self.color_mineable = modifiers[0]
        self.enemy_mineable = modifiers[1]
        self.color_walkable = modifiers[2]
        self.enemy_walkable = modifiers[3]
        self.dead = modifiers[4]

    def overall_grade(self, node: Node, color: Space) -> None:
        if node.value is None:
            return
        enemy = self.flip_color(color)
        color_grade = (len(node.value.mineable_by_player(color))) * self.color_mineable
        enemy_grade = (len(node.value.mineable_by_player(enemy))) * self.enemy_mineable
        color_grade += (len(node.value.walkable_by_player(color))) * self.color_walkable
        enemy_grade += (len(node.value.walkable_by_player(enemy))) * self.enemy_walkable
        for miner in node.value.find_all(color):
            if node.value.is_miner_dead(miner):
                enemy_grade += self.dead
        node.grade = color_grade - enemy_grade

    """
    def overall_grade(self, node: Node, color: Space) -> None:
        # TODO: calculate grade for each board in possible boards and return best board, grade
        if node.value is None:
            return
        node.grade = (
            self.grade_board_state_by_walk(node.value, color)
            + self.grade_board_state_by_mine(node.value, color)
        ) / 2
        return
    """

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
                best = max(best, value)
                alpha = max(alpha, best)
                if beta <= alpha:
                    break
            node.best_child = child
                
            return child if child is not None else node
        else:
            best = float("inf")
            child = None
            for child in node.children:
                if child.mine is None:
                    continue
                value = self.minimax(child, depth + 1, True, alpha, beta, color).grade
                best = min(best, value)
                beta = min(beta, best)
                if beta <= alpha:
                    break
            node.best_child = child
                
            return child if child is not None else node

    def mine(self, board: Board, color: Space) -> Coordinate:
        top = Node(board)
        for node in self.mine_help(top, color, False):
            if type(node) != Node:
                raise ValueError("flag not working")
            next(self.mine_help(node, self.flip_color(color), True))
            for next_node in node.children:
                if type(next_node) != Node:
                    raise ValueError("flag not working")
                next(self.mine_help(next_node, color, True))
        best = self.minimax(top, 0, True, float("-inf"), float("inf"), color, 2)
        if top.best_child and top.best_child.mine and best and best.mine: # wtf is going on? 
            return best.mine # top.best_child.mine
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
        mineable = [m for m in mineable if m not in board.find_all(color)]
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
        node.add_child(node)
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
        self.minimax(node, 0, True, float("-inf"), float("inf"), color)
        # print(node.best_child.walk if node.best_child else "no best child")
        return node.best_child.walk if node.best_child is not None else None


if __name__ == "__main__":
    import display
    '''
    import pygame
    
    from game import Game
    from random_bot import RandomPlayer
    player_a, player_b = Catherine(), RandomPlayer()
    game = Game(player_a, player_b, time_per_move=10, small=True, min_sleep_time=0)
    game.step()
    pygame.init()
    display.update()
    display.draw(pygame.display.set_mode((800, 800)), game)
    display.update()
    while True:
        ...
    '''
    display.main()
    
