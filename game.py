from copy import deepcopy
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
            mine_res = pool.apply_async(
                player.mine, (deepcopy(self.board), player_color)
            )
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
            move_res = pool.apply_async(
                player.move, (deepcopy(self.board), player_color)
            )
            try:
                if self.min_sleep_time > 0:
                    delay.get()
                start_time = time.monotonic()
                move = move_res.get(available_time)
                end_time = time.monotonic()
                available_time -= end_time - start_time
                self.reserve_time[player_color] -= max(0, total_time - available_time - self.time_per_move)
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
