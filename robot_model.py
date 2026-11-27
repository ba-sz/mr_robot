"""Mechanika robota, wspólna dla prezentacji i gry."""

from __future__ import annotations

from collections import deque
from collections.abc import Collection
from dataclasses import dataclass
from enum import Enum
from random import Random


class Move(Enum):
    RIGHT = (1, 0, "PRAWO")
    UP = (0, -1, "GÓRA")
    LEFT = (-1, 0, "LEWO")
    DOWN = (0, 1, "DÓŁ")

    @property
    def delta(self) -> tuple[int, int]:
        return self.value[:2]

    @property
    def label(self) -> str:
        return self.value[2]


@dataclass(frozen=True)
class Board:
    width: int = 5
    height: int = 4
    start: tuple[int, int] = (0, 2)
    treasure: tuple[int, int] = (4, 0)
    obstacles: frozenset[tuple[int, int]] = frozenset({(2, 2), (2, 0), (3, 3)})

    def __post_init__(self) -> None:
        if self.width < 1 or self.height < 1:
            raise ValueError("Plansza musi mieć dodatnie wymiary.")
        for point in (self.start, self.treasure, *self.obstacles):
            if not self.contains(point):
                raise ValueError(f"Pole {point} leży poza planszą.")
        if self.start in self.obstacles or self.treasure in self.obstacles:
            raise ValueError("Start i skarb nie mogą leżeć na przeszkodzie.")
        if self.start == self.treasure:
            raise ValueError("Start i skarb muszą być różnymi polami.")

    def contains(self, point: tuple[int, int]) -> bool:
        x, y = point
        return 0 <= x < self.width and 0 <= y < self.height


BOARD = Board()
SOLUTION = (Move.RIGHT, Move.UP, Move.RIGHT, Move.RIGHT, Move.UP, Move.RIGHT)
BLOCKED_ROUTE = (Move.RIGHT, Move.RIGHT, Move.UP, Move.RIGHT, Move.UP, Move.RIGHT)
BUG_ROUTE = (Move.RIGHT, Move.UP, Move.RIGHT, Move.RIGHT, Move.DOWN, Move.RIGHT)
MAX_COMMANDS = 12


@dataclass(frozen=True)
class Step:
    position: tuple[int, int]
    error: str | None = None


def advance(board: Board, position: tuple[int, int], move: Move) -> Step:
    if not board.contains(position) or position in board.obstacles:
        raise ValueError("Robot musi stać na dostępnym polu planszy.")
    dx, dy = move.delta
    destination = (position[0] + dx, position[1] + dy)
    if not board.contains(destination):
        return Step(position, "Brzeg planszy! Popraw strzałkę i spróbuj ponownie.")
    if destination in board.obstacles:
        return Step(position, "Kamień na drodze! Popraw strzałkę i spróbuj ponownie.")
    return Step(destination)


@dataclass(frozen=True)
class Run:
    positions: tuple[tuple[int, int], ...]
    won: bool
    error: str | None = None
    failed_command: int | None = None


def simulate(commands: tuple[Move, ...], board: Board = BOARD) -> Run:
    """Wykonaj cały program; skarb liczy się na końcu, nie po drodze."""
    positions = [board.start]
    for index, move in enumerate(commands, start=1):
        step = advance(board, positions[-1], move)
        if step.error:
            return Run(tuple(positions), False, step.error, index)
        positions.append(step.position)
    return Run(tuple(positions), positions[-1] == board.treasure)


MAX_LEVEL = 6
DEFAULT_ROUNDS = 6
TURBO_WIDTH = 11
TURBO_HEIGHT = 9
TURBO_MAX_COMMANDS = 24
TURBO_FIRST_PATH = 8
TURBO_PATH_STEP = 2
ULTRA_WIDTH = 21
ULTRA_HEIGHT = 17
ULTRA_MAX_COMMANDS = 48
ULTRA_FIRST_PATH = 20
ULTRA_PATH_STEP = 5


class GameMode(Enum):
    STANDARD = "standard"
    TURBO = "turbo"
    ULTRA = "ultra"

    @property
    def title(self) -> str:
        return {GameMode.STANDARD: "PRZYGODA", GameMode.TURBO: "TURBO",
                GameMode.ULTRA: "ULTRA"}[self]

    @property
    def max_commands(self) -> int:
        return {GameMode.STANDARD: MAX_COMMANDS, GameMode.TURBO: TURBO_MAX_COMMANDS,
                GameMode.ULTRA: ULTRA_MAX_COMMANDS}[self]

    @property
    def program_columns(self) -> int:
        return 6 if self is GameMode.STANDARD else 12


def generate_turbo_puzzle(level: int, rng: Random,
                          excluded_treasures: Collection[tuple[int, int]] = ()) -> Puzzle:
    if not 1 <= level <= MAX_LEVEL:
        raise ValueError(f"Poziom musi należeć do zakresu 1–{MAX_LEVEL}.")
    target_steps = TURBO_FIRST_PATH + TURBO_PATH_STEP * (level - 1)
    points = [(x, y) for y in range(TURBO_HEIGHT) for x in range(TURBO_WIDTH)]
    for _ in range(500):
        obstacles = frozenset(rng.sample(points, 8 + 2 * level))
        available = [point for point in points if point not in obstacles]
        start = rng.choice(available)
        temporary_goal = next(point for point in available if point != start)
        board = Board(TURBO_WIDTH, TURBO_HEIGHT, start, temporary_goal, obstacles)
        paths = shortest_paths(board, start)
        if len(paths) != len(available):
            continue
        # Count shortest routes (capped at two): every puzzle offers a real choice,
        # not just a corridor or a longer route formed by stepping back and forth.
        route_counts = {start: 1}
        for point, path in paths.items():
            if point == start:
                continue
            route_counts[point] = min(2, sum(
                route_counts.get((point[0] - move.delta[0], point[1] - move.delta[1]), 0)
                for move in Move
                if len(paths.get((point[0] - move.delta[0], point[1] - move.delta[1]), ()))
                == len(path) - 1
            ))
        candidates = [
            (point, path) for point, path in paths.items()
            if len(path) == target_steps and point not in excluded_treasures
            and route_counts[point] >= 2 and turns(path) >= 2
        ]
        if candidates:
            treasure, solution = rng.choice(candidates)
            board = Board(TURBO_WIDTH, TURBO_HEIGHT, start, treasure, obstacles)
            return Puzzle(board, solution, level, make_options(board, solution, rng))
    raise RuntimeError("Nie udało się wylosować otwartej planszy turbo z wyborem tras.")


def generate_ultra_puzzle(level: int, rng: Random) -> Puzzle:
    return generate_maze_puzzle(level, rng, GameMode.ULTRA)


def generate_maze_puzzle(level: int, rng: Random, mode: GameMode,
                         excluded_treasures: Collection[tuple[int, int]] = ()) -> Puzzle:
    """Build a connected tree maze with at least three choices on the solution."""
    if not 1 <= level <= MAX_LEVEL:
        raise ValueError(f"Poziom musi należeć do zakresu 1–{MAX_LEVEL}.")
    if mode is GameMode.ULTRA:
        width, height = ULTRA_WIDTH, ULTRA_HEIGHT
        target_steps = ULTRA_FIRST_PATH + ULTRA_PATH_STEP * (level - 1)
    else:
        raise ValueError("Generator labiryntu wymaga trybu ultra.")
    cells = [
        (x, y)
        for y in range(1, height - 1, 2)
        for x in range(1, width - 1, 2)
    ]
    cell_set = set(cells)
    for _ in range(250):
        root = rng.choice(cells)
        open_cells = {root}
        open_corridors = set()
        frontier = []

        def add_frontier(cell: tuple[int, int]) -> None:
            x, y = cell
            frontier.extend(
                (cell, neighbor)
                for neighbor in ((x + 2, y), (x - 2, y), (x, y + 2), (x, y - 2))
                if neighbor in cell_set and neighbor not in open_cells
            )

        # Random frontier edges grow a branching tree, unlike depth-first
        # carving which can hide all the choices beyond the treasure.
        add_frontier(root)
        while frontier:
            index = rng.randrange(len(frontier))
            frontier[index], frontier[-1] = frontier[-1], frontier[index]
            (x, y), (nx, ny) = frontier.pop()
            if (nx, ny) in open_cells:
                continue
            open_cells.add((nx, ny))
            open_corridors.add(((x + nx) // 2, (y + ny) // 2))
            add_frontier((nx, ny))
        open_spaces = open_cells | open_corridors
        walls = frozenset(
            (x, y) for y in range(height) for x in range(width)
            if (x, y) not in open_spaces
        )
        junctions = {
            (x, y) for x, y in cells
            if sum((x + dx, y + dy) in open_spaces
                   for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))) >= 3
        }
        starts = cells.copy()
        rng.shuffle(starts)
        for start_cell in starts:
            temporary_goal = next(cell for cell in cells if cell != start_cell)
            board = Board(width, height, start_cell, temporary_goal, walls)
            paths = shortest_paths(board, start_cell)
            candidates = [
                (point, path) for point, path in paths.items()
                if len(path) == target_steps and point not in excluded_treasures
                and sum(position in junctions
                        for position in simulate(path, board).positions[1:-1]) >= 3
            ]
            if not candidates:
                continue
            # Every off-route branch in this tree ends in a dead end and
            # cannot rejoin the solution to create a shortcut.
            treasure, solution = rng.choice(candidates)
            board = Board(width, height, start_cell, treasure, walls)
            return Puzzle(board, solution, level, make_options(board, solution, rng))
    raise RuntimeError(
        f"Nie udało się wylosować labiryntu {mode.value} o ścieżce długości {target_steps}."
    )


def shortest_paths(board: Board, start: tuple[int, int]) -> dict[tuple[int, int], tuple[Move, ...]]:
    paths: dict[tuple[int, int], tuple[Move, ...]] = {start: ()}
    queue = deque([start])
    while queue:
        position = queue.popleft()
        for move in Move:
            step = advance(board, position, move)
            if not step.error and step.position not in paths:
                paths[step.position] = (*paths[position], move)
                queue.append(step.position)
    return paths


def shortest_solution(board: Board) -> tuple[Move, ...]:
    paths = shortest_paths(board, board.start)
    if board.treasure not in paths:
        raise ValueError("Nie ma drogi do skarbu.")
    return paths[board.treasure]


def turns(commands: tuple[Move, ...]) -> int:
    return sum(a != b for a, b in zip(commands, commands[1:]))


@dataclass(frozen=True)
class Puzzle:
    board: Board
    solution: tuple[Move, ...]
    level: int
    options: tuple[tuple[Move, ...], ...]

    @property
    def correct_index(self) -> int:
        return self.options.index(self.solution)


def make_options(board: Board, solution: tuple[Move, ...], rng: Random) -> tuple[tuple[Move, ...], ...]:
    wrong = []
    for index, original in enumerate(solution):
        for replacement in Move:
            if replacement == original:
                continue
            candidate = (*solution[:index], replacement, *solution[index + 1:])
            if not simulate(candidate, board).won:
                wrong.append(candidate)
    if len(wrong) < 2:
        raise ValueError("Za mało różnych błędnych odpowiedzi do quizu.")
    options = [solution, *rng.sample(wrong, 2)]
    rng.shuffle(options)
    return tuple(options)


def generate_puzzle(level: int, rng: Random,
                    excluded_treasures: Collection[tuple[int, int]] = ()) -> Puzzle:
    if not 1 <= level <= MAX_LEVEL:
        raise ValueError(f"Poziom musi należeć do zakresu 1–{MAX_LEVEL}.")
    target_steps = level + 2
    minimum_turns = min(3, (level + 1) // 2)
    points = [(x, y) for y in range(4) for x in range(5)]
    for _ in range(500):
        obstacles = frozenset(rng.sample(points, level - 1))
        available = [point for point in points if point not in obstacles]
        start = rng.choice(available)
        temporary_goal = next(point for point in available if point != start)
        board = Board(start=start, treasure=temporary_goal, obstacles=obstacles)
        paths = shortest_paths(board, start)
        candidates = [
            (point, path) for point, path in paths.items()
            if point not in excluded_treasures and len(path) == target_steps
            and turns(path) >= minimum_turns
        ]
        if candidates:
            treasure, solution = rng.choice(candidates)
            board = Board(start=start, treasure=treasure, obstacles=obstacles)
            return Puzzle(board, solution, level, make_options(board, solution, rng))
    raise RuntimeError("Nie udało się wylosować rozwiązywalnej planszy o wymaganej trudności.")


def generate_rounds(count: int = DEFAULT_ROUNDS, seed: int | None = None) -> tuple[Puzzle, ...]:
    if not 1 <= count <= MAX_LEVEL:
        raise ValueError(f"Liczba rund musi należeć do zakresu 1–{MAX_LEVEL}.")
    rng = Random(seed)
    rounds: list[Puzzle] = []
    for level in range(1, count + 1):
        rounds.append(generate_puzzle(level, rng, {p.board.treasure for p in rounds}))
    return tuple(rounds)


class Campaign:
    """Wygrana daje jeden skarb; kolejna plansza dopiero po potwierdzeniu."""

    def __init__(self, seed: int | None = None, board: Board | None = None,
                 mode: GameMode = GameMode.STANDARD) -> None:
        self.rng = Random(seed)
        self.mode = mode
        self.round_number = 1
        self.wins = 0
        self.solved = False
        if board is None and mode is GameMode.TURBO:
            self.puzzle = generate_turbo_puzzle(1, self.rng)
        elif board is None and mode is GameMode.ULTRA:
            self.puzzle = generate_maze_puzzle(1, self.rng, mode)
        elif board is None:
            self.puzzle = generate_puzzle(1, self.rng)
        else:
            solution = shortest_solution(board)
            self.puzzle = Puzzle(board, solution, 1, make_options(board, solution, self.rng))

    def record_win(self) -> bool:
        if self.solved:
            return False
        self.solved = True
        self.wins += 1
        return True

    def next_round(self) -> None:
        if not self.solved:
            raise ValueError("Najpierw zdobądź skarb w tej rundzie.")
        next_level = min(MAX_LEVEL, self.wins + 1)
        if self.mode is GameMode.TURBO:
            puzzle = generate_turbo_puzzle(next_level, self.rng, {self.puzzle.board.treasure})
        elif self.mode is GameMode.ULTRA:
            puzzle = generate_maze_puzzle(next_level, self.rng, self.mode,
                                          {self.puzzle.board.treasure})
        else:
            puzzle = generate_puzzle(next_level, self.rng, {self.puzzle.board.treasure})
        self.puzzle = puzzle
        self.round_number += 1
        self.solved = False
