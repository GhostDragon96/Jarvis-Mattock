from copy import copy, deepcopy
from enum import Enum


CompoundCoordinate = tuple[int, int] | tuple[int, int, int]
FullCoordinate = tuple[int, int, int]
Coordinate = tuple[int, int]


class Space(Enum):
    """
    Tracks the 4 possible states that a board space can be in:
    solid wall, empty mined space, mined space with a red piece in it,
    mined space with a blue piece in it
    """

    WALL = 0
    EMPTY = 1
    RED = 2
    BLUE = 3


def _hex_neighbors(coord: CompoundCoordinate) -> list[FullCoordinate]:
    if len(coord) == 2:
        q, r = coord
        s = -q - r
    else:
        q, r, s = coord
    directions = [
        (1, -1, 0),
        (1, 0, -1),
        (0, 1, -1),
        (-1, 1, 0),
        (-1, 0, 1),
        (0, -1, 1),
    ]
    return [(q + a, r + b, s + c) for a, b, c in directions]


class Board:
    """
    Class to represent a specific board state.
    """

    def __init__(self, small: bool = False):
        """
        Create a new board in the default starting state

        Args:
            small (bool, optional): Is the board the small (5-hex) size or
                the large (7-hex) size. Defaults to False. (small)
        """
        self.size = 5 if small else 7
        self.miner_count = 3 if small else 6
        self.cells: dict[FullCoordinate, Space] = {}
        frontier = [(0, 0, 0)]
        for _ in range(self.size - 1):
            next_frontier = []
            while frontier:
                curr = frontier.pop()
                for neighbor in (
                    n for n in _hex_neighbors(curr) if n not in self.cells
                ):
                    self.cells[neighbor] = Space.WALL
                    next_frontier.append(neighbor)
            frontier = next_frontier
        red_miners = [(1, -3), (2, 1), (-3, 2), (6, -4), (-4, -2), (-2, 6)]
        blue_miners = [(-1, 3), (-2, -1), (3, -2), (-6, 4), (4, 2), (2, -6)]
        for cell in red_miners:
            if cell in self:
                self[cell] = Space.RED
        for cell in blue_miners:
            if cell in self:
                self[cell] = Space.BLUE

    def __hash__(self) -> int:
        return hash(frozenset(self.cells.items()))

    def __copy__(self) -> "Board":
        out = Board.__new__(Board)
        out.size = self.size
        out.miner_count = self.miner_count
        out.cells = deepcopy(self.cells)
        return out

    def count_elements(self, element: Space) -> int:
        """
        Count how many of a given space exist on the board

        Args:
            element (Space): The element to count

        Returns:
            int: The number of instances of that space on the board
        """
        return len([c for c in self.cells.values() if c == element])

    def _full_coordinate(self, coord: CompoundCoordinate) -> FullCoordinate:
        if len(coord) == 2:
            q, r = coord
            s = -q - r
        else:
            q, r, s = coord
        return (q, r, s)

    def __setitem__(self, coord: CompoundCoordinate, value: Space):
        """
        Replace a space on the board with different contents.
        Usage example: board[1, 3] = Space.EMPTY

        Args:
            coord (CompoundCoordinate): The location to replace
            value (Space): The Space value to place at that location

        Raises:
            ValueError: The given coord is not a valid coordinate on this board
        """
        coord = self._full_coordinate(coord)
        if coord not in self.cells:
            raise ValueError(f"{coord} is not a valid coordinate.")
        self.cells[coord] = value

    def __getitem__(self, coord: CompoundCoordinate) -> Space:
        """
        Check what the contents of a specific space is
        Usage example: print(board[1, 3])

        Args:
            coord (CompoundCoordinate): The coordinates of the space to check

        Raises:
            ValueError: The given coord is not a valid coordinate on this board

        Returns:
            Space: The value contained at that coordinate
        """
        coord = self._full_coordinate(coord)
        if coord not in self.cells:
            raise ValueError(f"{coord} is not a valid coordinate.")
        return self.cells[coord]

    def __contains__(self, coord: CompoundCoordinate) -> bool:
        """
        Is a given coordinate a valid coordinate on the board?
        Usage example: if (2,5) in board: ...

        Args:
            coord (CompoundCoordinate): A coordinate to check

        Returns:
            bool: True if the coordinate exists on the board, False otherwise
        """
        coord = self._full_coordinate(coord)
        return coord in self.cells

    def find_all(self, space: Space) -> set[Coordinate]:
        """
        Find the coordinates of all instances of a given space

        Args:
            space (Space): The space for which to search

        Returns:
            set[Coordinate]: The coordinates at which the given space appears
        """
        return {coord[:2] for coord in self.cells if self[coord] == space}

    def neighbors(
        self, coord: CompoundCoordinate, space: Space | None = None
    ) -> set[Coordinate]:
        """
        Find all valid adjacent neighbors of a given coordinate. If a space type is
        given, only lists coordinates of neighbors of a particular type.

        Args:
            coord (CompoundCoordinate): The location whose neighbors you'd like to find
            space (Space | None, optional): The type of space you'd like to filter to.
                gives all neighbors if this is None. Defaults to None.

        Returns:
            set[Coordinate]: The coordinates of the neighbors
        """
        if space is None:
            return {n[:2] for n in _hex_neighbors(coord) if n in self.cells}
        return {
            n[:2] for n in _hex_neighbors(coord) if n in self.cells and self[n] == space
        }

    def walkable_from_coord(self, start: CompoundCoordinate) -> set[Coordinate]:
        """
        Find all spaces that a piece starting at a given location could walk to.
        This includes spaces that it could get to by traveling through a friend, but not the
        spaces of those friends.

        Args:
            start (CompoundCoordinate): The starting location of the piece

        Returns:
            set[Coordinate]: The spaces that a piece on the starting location could walk to.
        """
        if self[start] == Space.WALL:
            return set()
        traversable = {self[start], Space.EMPTY}
        out: set[Coordinate] = set()
        frontier = set([start])
        visited: set[Coordinate] = set()
        while frontier:
            curr = frontier.pop()
            curr = curr[:2]
            visited.add(curr)
            if self[curr] not in traversable:
                continue
            if self[curr] == Space.EMPTY:
                out.add(curr)
            frontier |= self.neighbors(curr) - visited
        return out

    def walkable_by_player(self, player: Space) -> set[Coordinate]:
        """
        Find all spaces that a given player's pieces can walk to.
        Includes only empty spaces, NOT spaces currently occupied by that player's pieces

        Args:
            player (Space): The starting player

        Raises:
            ValueError: The input must be either Space.RED or Space.BLUE

        Returns:
            set[Coordinate]: The coordinates walkable by that player
        """
        if player not in {Space.BLUE, Space.RED}:
            raise ValueError("The only valid players are Space.RED and Space.BLUE")
        player_coords = self.find_all(player)
        out = set()
        for p in player_coords:
            out |= self.walkable_from_coord(p)
        return out

    def is_mineable(self, coord: CompoundCoordinate) -> bool:
        """
        Check if a space can be mined. Factors in only the type of space and mined neighbor counts

        Args:
            coord (CompoundCoordinate): The coordinates of the space in question

        Returns:
            bool: _description_
        """
        if self[coord] != Space.WALL:
            return False
        empty_neighbors = (
            self.neighbors(coord, Space.EMPTY)
            | self.neighbors(coord, Space.RED)
            | self.neighbors(coord, Space.BLUE)
        )
        if len(empty_neighbors) > 3:
            return False
        for n in empty_neighbors:
            if (
                len(
                    self.neighbors(n, Space.EMPTY)
                    | self.neighbors(n, Space.RED)
                    | self.neighbors(n, Space.BLUE)
                )
                >= 3
            ):
                return False
        return True

    def mineable_by_player(self, player: Space) -> set[Coordinate]:
        """
        Find all spaces that a given player can mine, factoring both accessibility and neighbor count

        Args:
            player (Space): The player in question

        Raises:
            ValueError: player must be either Space.RED or Space.BLUE

        Returns:
            set[Coordinate]: All coordinates that a given player can mine
        """
        if player not in {Space.BLUE, Space.RED}:
            raise ValueError("The only valid players are Space.RED and Space.BLUE")
        neighboring_walls = set()
        player_coords = self.find_all(player)
        for hall in self.walkable_by_player(player) | player_coords:
            neighboring_walls |= {
                w for w in self.neighbors(hall, Space.WALL) if self.is_mineable(w)
            }
        return neighboring_walls

    def is_miner_dead(self, coord: CompoundCoordinate) -> bool:
        """
        Check if a given miner is dead due to having 2 connected enemies and no connected friends

        Args:
            coord (CompoundCoordinate): The location of the miner in question

        Raises:
            ValueError: The coordinate must contain a miner

        Returns:
            bool: True if the miner needs to be removed from the board, False otherwise
        """
        player = self[coord]
        if player not in {Space.BLUE, Space.RED}:
            raise ValueError("The only valid players are Space.RED and Space.BLUE")
        other_player = Space.RED if player == Space.BLUE else Space.BLUE
        enemy_count = 0
        frontier = set([coord])
        visited: set[Coordinate] = set()
        while frontier:
            curr = frontier.pop()
            curr = curr[:2]
            visited.add(curr)
            if self[curr] == player and curr != coord[:2]:
                return False
            if self[curr] == other_player:
                enemy_count += 1
                continue
            if self[curr] == Space.WALL:
                continue
            frontier |= self.neighbors(curr) - visited
        return enemy_count >= 2

    def clear_dead(self, other_color: Space):
        dead_enemies = {
            coord
            for coord in self.cells
            if self[coord] == other_color and self.is_miner_dead(coord)
        }
        for enemy in dead_enemies:
            self[enemy] = Space.EMPTY

