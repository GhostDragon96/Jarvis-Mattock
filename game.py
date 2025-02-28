from copy import copy
import time
import traceback
from typing import Protocol
from multiprocessing import Pool, TimeoutError

from board import Coordinate, Board, Space


class Player(Protocol):

    @property
    def name(self) -> str: ...

    def mine(self, board: Board, color: Space) -> Coordinate: ...

    def move(
        self, board: Board, color: Space
    ) -> tuple[Coordinate, Coordinate] | None: ...


class Game:

    def __init__(
        self,
        red: Player,
        blue: Player,
        small: bool = False,
        time_per_move: float = 3.0,
        reserve_time: float = 10.0,
        min_sleep_time: float = 0.0,
    ):
        self.players = {Space.RED: red, Space.BLUE: blue}  # red, blue
        self.red_turn = True
        self.board = Board(small)
        self.winner: Space | None = None
        self.time_per_move = time_per_move
        self.min_sleep_time = min_sleep_time
        self.reserve_time = {Space.RED: reserve_time, Space.BLUE: reserve_time}

    def step(self):
        if self.winner:
            return
        player_color = Space.RED if self.red_turn else Space.BLUE
        other_color = Space.BLUE if self.red_turn else Space.RED
        total_time = self.time_per_move + self.reserve_time[player_color]
        available_time = total_time
        player = self.players[player_color]
        # Check if a player just lost by not being able to mine
        if len(self.board.mineable_by_player(player_color)) == 0:
            self.winner = other_color
            return
        # Current player needs to dig out a space
        with Pool(processes=1) as pool:
            mine_res = pool.apply_async(player.mine, (copy(self.board), player_color))
            try:
                start_time = time.monotonic()
                mine_coord = mine_res.get(available_time)
                end_time = time.monotonic()
                available_time -= end_time - start_time
            # Player crashed or timed out
            except TimeoutError:
                self.winner = other_color
                print(f"{player.name} timed out!")
                return
            except Exception:
                self.winner = other_color
                print(f"{player.name} crashed!")
                traceback.print_exc()
                return
        # Current player made an illegal dig
        if not self.board.is_mineable(mine_coord):
            print(f"{player.name} illegally tried to mine at {mine_coord}")
            self.winner = other_color
            return
        # Dig out the space
        self.board[mine_coord] = (
            Space.EMPTY
            if self.board.count_elements(player_color) == self.board.miner_count
            else player_color
        )
        # Current player may move
        with Pool(processes=2) as pool:
            if self.min_sleep_time > 0:
                sleep_time = max(
                    0,
                    min(
                        available_time,
                        self.min_sleep_time
                        - (
                            self.time_per_move
                            + self.reserve_time[player_color]
                            - available_time
                        ),
                    ),
                )
                delay = pool.apply_async(time.sleep, (sleep_time,))
            move_res = pool.apply_async(player.move, (copy(self.board), player_color))
            try:
                if self.min_sleep_time > 0:
                    delay.get()  # type: ignore
                start_time = time.monotonic()
                move = move_res.get(available_time)
                end_time = time.monotonic()
                available_time -= end_time - start_time
                self.reserve_time[player_color] -= max(
                    0, total_time - available_time - self.time_per_move
                )
            # player crashed or timed out
            except TimeoutError:
                self.winner = other_color
                print(f"{player.name} timed out!")
                return
            except Exception:
                self.winner = other_color
                print(f"{player.name} crashed!")
                traceback.print_exc()
                return
        if move is not None:
            move_start, move_end = move
            if self.board[
                move_start
            ] != player_color or move_end not in self.board.walkable_from_coord(
                move_start
            ):
                print(
                    f"{player.name} tried to illegally move from {move_start} to {move_end}."
                )
                self.winner = other_color
                return
            self.board[move_start] = Space.EMPTY
            self.board[move_end] = player_color
        # Clear dead enemies
        self.board.clear_dead(other_color)
        # Switch players
        self.red_turn = not self.red_turn

    def play_game(self) -> Space:
        while not self.winner:
            self.step()
        return self.winner


if __name__ == "__main__":
    from random import choice
    from Catherine import Catherine
    from random_bot import RandomPlayer
    def close_to(fl1: float, fl2: float) -> bool:
        if abs(fl1-fl2) > 1:
            return False
        return True

    i = 0
    o = 0
    iter_of_change = 0
    changes: list[tuple[float, float, float, float, float]] = [
        (100, 10, 10, 1, 200),
        (50, 10, 10, 1, 200),
        (0, 10, 10, 1, 200),
    ]
    worst: list[tuple[float, float]] = []
    while not close_to(changes[0][iter_of_change], changes[1][iter_of_change]):
        for change in changes:
            for o in range(3): #######################
                try:
                    if o % 2 == 0:
                        player_a, player_b = Catherine(change), RandomPlayer(rng_seed=o)
                    else:
                        player_b, player_a = Catherine(change), RandomPlayer(rng_seed=o)
                    game = Game(
                        player_a, player_b, time_per_move=3, small=True, min_sleep_time=0
                    )
                    winner = game.play_game()
                    if o % 2 == 0:
                        if winner == Space.BLUE:
                            i += 1
                            # print('Random', i)
                    else:
                        if winner == Space.RED:
                            i += 1
                            # print("Random", i)
                except KeyboardInterrupt:
                    print((i / (o + 1)) * 100, "percent lost", changes)
                    exit()
            # print((i / 25) * 100, "percent lost", change)
            worst.append((change[iter_of_change], (i / 3) * 100)) #######################
            i = 0
        for poss in changes:
            if poss[iter_of_change] == max(worst, key= lambda x: x[1])[0]:
                changes.remove(poss)
        avg = (changes[0][iter_of_change]+changes[1][iter_of_change])/2
        plus_or_minus = 0.7 * abs(changes[0][iter_of_change] - avg) # 70% of the change
        mid_tup_list: list[float] = list(changes[0])
        mid_tup_list[iter_of_change] = avg
        front_tup_list = list(mid_tup_list)
        front_tup_list[iter_of_change] = avg - plus_or_minus
        end_tup_list = list(mid_tup_list)
        end_tup_list[iter_of_change] = avg + plus_or_minus
        changes = [tuple(front_tup_list), tuple(mid_tup_list), tuple(end_tup_list)] # type: ignore # will be 5 long
    print(changes)


    