import pytest
from board import Space
from game import Game
from random_bot import RandomPlayer


@pytest.fixture
def blank_game() -> Game:
    game = Game(RandomPlayer(), RandomPlayer(), small=True)
    game.board.cells = {coord: Space.WALL for coord in game.board.cells}
    return game


@pytest.fixture
def time_reserve_game() -> Game:
    game = Game(
        RandomPlayer(1.5),
        RandomPlayer(),
        small=True,
        time_per_move=1.0,
        reserve_time=2.0,
    )
    game.board.cells = {coord: Space.WALL for coord in game.board.cells}
    game.board[0, 0] = Space.RED
    return game


def test_kill(blank_game: Game):
    g = blank_game
    g.board[0, 0] = Space.EMPTY
    g.board[0, -1] = Space.RED
    g.board[1, 0] = Space.RED
    g.board[-1, 1] = Space.BLUE
    g.red_turn = True
    assert g.board.is_miner_dead((-1, 1))
    g.board.clear_dead(Space.RED)
    assert g.board[0, 0] == Space.EMPTY
    assert g.board[0, -1] == Space.RED
    assert g.board[1, 0] == Space.RED
    assert g.board[-1, 1] == Space.BLUE
    g.board.clear_dead(Space.BLUE)
    assert g.board[0, 0] == Space.EMPTY
    assert g.board[0, -1] == Space.RED
    assert g.board[1, 0] == Space.RED
    assert g.board[-1, 1] == Space.EMPTY


def test_reserve_time(time_reserve_game: Game):
    g = time_reserve_game
    g.step()
    assert g.reserve_time[Space.RED] == pytest.approx(1.5, abs=0.01)
