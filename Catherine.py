from random import choice
from board import Board, Space, Coordinate
import copy

class Catherine:

    count = 0

    def __init__(self):
        self.name = f"Catherine_{Catherine.count}"
        Catherine.count += 1

    def overall_grade(self, possible_boards: list[Board], color: Space) -> tuple[Board, float]:
        all_grades = []
        enemy = self.flip_color(color)
        for board in possible_boards:
            color_grade = len(board.mineable_by_player(color)) *10
            enemy_grade = len(board.mineable_by_player(enemy)) *10  # put number to modify value
            color_grade += len(board.walkable_by_player(color)) *10
            enemy_grade += len(board.walkable_by_player(enemy)) * 1 # put number to modify value
            #for miner in board.find_all(enemy):
             #   if board.is_miner_dead(miner):
              #     color_grade += 10 # put number to modify value
            for miner in board.find_all(color):
                if board.is_miner_dead(miner):
                    enemy_grade += 200 # put number to modify value
            total = color_grade - enemy_grade   
            all_grades.append((board, total))
        return max(all_grades, key= lambda x: x[1])

       

    '''
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
        enemy = self.flip_color(color)
        a = len(Board.mineable_by_player(board, color))
        b = len(Board.mineable_by_player(board, enemy))
        for miner in board.find_all(color):
            if board.is_miner_dead(miner):
                b += 10
        grade = a - b
        return grade
    
        
    def mine_help(self, boards: set[Board], color: Space) -> Coordinate:
        for board in boards:
            self.grade_board_state_by_mine(board, color)
        '''

    def mine(self, board: Board, color: Space, flag: bool = True) -> Coordinate:
        mineable = board.mineable_by_player(color)
        boards: list[Board] = []
        dict_boards: dict[Board, Coordinate] = {}
        for mine in mineable:
            temp_board = copy.copy(board)
            temp_board[mine] = (
                Space.EMPTY
                if temp_board.count_elements(color) == temp_board.miner_count
                else color
            )
            boards.append(temp_board)
            dict_boards.update({temp_board: mine})
        best_board = self.overall_grade(boards, color)[0]
        mine = dict_boards[best_board]
        return mine
    
    def flip_color(self, color: Space) -> Space:
        return Space.RED if color != Space.RED else Space.BLUE
    
        '''    
    def mine_help(self, board: Board, color: Space, i: int) -> list[tuple[Board, Coordinate]]:
        mineable = board.mineable_by_player(color)
        boards: list[tuple[Board, Coordinate]] = []
        for mine in mineable:
            temp_board = copy.deepcopy(board)
            temp_board[mine] = Space.EMPTY
            boards.append((temp_board, mine))
        if i != 2:
            all_boards = []
            for b in boards:
                all_boards += self.mine_help(b[0], Catherine.flip_color(self, color), i+1)
            boards = all_boards
        return boards

    def mine(self, board: Board, color: Space) -> Coordinate:
        boards = Catherine.mine_help(self, board, color, 0)
        best_grade = 0 - float('inf')
        best = None
        for poss_board, coor in boards:
            grade = Catherine.grade_board_state_by_mine(self, poss_board, color)
            print(grade)
            if grade > best_grade:
                best = coor
                best_grade = grade
        if best is not None:
            return best
        else:
            raise ValueError('I messed up.')
            '''
    
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
