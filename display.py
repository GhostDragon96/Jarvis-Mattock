import numpy as np

import sys

import pygame

from board import Space
from game import Game
from random_bot import RandomPlayer
from Catherine import Catherine


def update():
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()


def hexagon(
    screen: pygame.Surface, x: float, y: float, size: float, color: tuple[int, int, int]
):
    corners = [
        (
            x + 0.9 * size * np.cos(theta),
            y + 0.9 * size * np.sin(theta),
        )
        for theta in np.linspace(0, 2 * np.pi, 6, endpoint=False) + np.pi / 6
    ]
    pygame.draw.polygon(screen, color, corners)


def draw(screen: pygame.Surface, game: Game):
    if game.winner == None:
        screen.fill((0, 0, 0))
    elif game.winner == Space.RED:
        screen.fill((100, 0, 0))
    elif game.winner == Space.BLUE:
        screen.fill((0, 0, 100))
    cell_size = screen.get_width() / (3.5 * game.board.size)
    for coord in game.board.cells:
        q, r = coord[:2]
        x = screen.get_width() / 2 + cell_size * (np.sqrt(3) * q + np.sqrt(3) / 2 * r)
        y = screen.get_height() / 2 + cell_size * 1.5 * r
        contents = game.board.cells[coord]
        if contents == Space.WALL:
            color = (100, 100, 100)
        else:
            color = (255, 255, 255)
        hexagon(screen, x, y, cell_size, color)
        if contents == Space.RED:
            pygame.draw.circle(screen, (255, 0, 0), (x, y), 0.6 * cell_size)
        elif contents == Space.BLUE:
            pygame.draw.circle(screen, (0, 0, 255), (x, y), 0.6 * cell_size)

    pygame.display.flip()


def runPyGame(game: Game):
    pygame.init()

    # Set up the window.
    width, height = 800, 800
    screen = pygame.display.set_mode((width, height))

    while True:
        update()
        draw(screen, game)
        if game.winner is None:
            game.step()


def main():
    player_a, player_b = Catherine(), RandomPlayer()
    game = Game(player_a, player_b, time_per_move=3, small=False, min_sleep_time=2)
    runPyGame(game)


if __name__ == "__main__":
    main()
