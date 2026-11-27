from collections import deque
from random import Random
import unittest

from robot_model import (
    Campaign, GameMode, MAX_LEVEL, TURBO_FIRST_PATH, TURBO_PATH_STEP, TURBO_WIDTH, TURBO_HEIGHT,
    ULTRA_FIRST_PATH, ULTRA_PATH_STEP, ULTRA_WIDTH, ULTRA_HEIGHT, ULTRA_MAX_COMMANDS,
    generate_puzzle, generate_rounds, generate_turbo_puzzle, generate_ultra_puzzle,
    shortest_solution, simulate, turns,
)


def independent_distance(board):
    queue = deque([(board.start, 0)])
    seen = {board.start}
    while queue:
        (x, y), distance = queue.popleft()
        if (x, y) == board.treasure:
            return distance
        for point in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if (0 <= point[0] < board.width and 0 <= point[1] < board.height
                    and point not in board.obstacles and point not in seen):
                seen.add(point)
                queue.append((point, distance + 1))
    return None


def independent_route_count(board):
    distances = {board.start: 0}
    counts = {board.start: 1}
    queue = deque([board.start])
    while queue:
        x, y = queue.popleft()
        for point in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if not board.contains(point) or point in board.obstacles:
                continue
            distance = distances[(x, y)] + 1
            if point not in distances:
                distances[point] = distance
                counts[point] = 0
                queue.append(point)
            if distances[point] == distance:
                counts[point] += counts[(x, y)]
    return counts.get(board.treasure, 0), len(distances)


def independent_maze_graph_and_route(board):
    free = {
        (x, y) for y in range(board.height) for x in range(board.width)
        if (x, y) not in board.obstacles
    }
    graph = {
        (x, y): {point for point in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1))
                 if point in free}
        for x, y in free
    }
    parents = {board.start: None}
    queue = deque([board.start])
    while queue:
        current = queue.popleft()
        for neighbor in graph[current]:
            if neighbor not in parents:
                parents[neighbor] = current
                queue.append(neighbor)
    route = []
    current = board.treasure
    while current is not None:
        route.append(current)
        current = parents[current]
    return graph, list(reversed(route))


class RandomRoundsTests(unittest.TestCase):
    def test_many_seeds_have_solvable_strictly_harder_rounds_and_distinct_treasures(self):
        locations = set()
        correct_indices = set()
        for seed in range(100):
            puzzles = generate_rounds(seed=seed)
            self.assertEqual(len({p.board.treasure for p in puzzles}), 6)
            for level, puzzle in enumerate(puzzles, start=1):
                with self.subTest(seed=seed, level=level):
                    self.assertTrue(simulate(puzzle.solution, puzzle.board).won)
                    self.assertEqual(independent_distance(puzzle.board), level + 2)
                    self.assertEqual(len(puzzle.solution), level + 2)
                    self.assertEqual(len(puzzle.board.obstacles), level - 1)
                    self.assertGreaterEqual(turns(puzzle.solution), min(3, (level + 1) // 2))
                    self.assertEqual(len(set(puzzle.options)), 3)
                    self.assertTrue(all(len(route) == len(puzzle.solution) for route in puzzle.options))
                    self.assertEqual(sum(simulate(route, puzzle.board).won for route in puzzle.options), 1)
                    self.assertEqual(shortest_solution(puzzle.board), puzzle.solution)
                    locations.add(puzzle.board.treasure)
                    correct_indices.add(puzzle.correct_index)
        self.assertEqual(locations, {(x, y) for y in range(4) for x in range(5)})
        self.assertEqual(correct_indices, {0, 1, 2})

    def test_seed_reproduces_content_not_one_fixed_deck(self):
        self.assertEqual(generate_rounds(seed=42), generate_rounds(seed=42))
        self.assertNotEqual(generate_rounds(seed=42), generate_rounds(seed=43))

    def test_invalid_parameters_are_rejected(self):
        for count in (0, -1, MAX_LEVEL + 1):
            with self.assertRaises(ValueError):
                generate_rounds(count=count)
            with self.assertRaises(ValueError):
                generate_puzzle(count, Random(42))

    def test_campaign_does_not_advance_or_double_score_without_win(self):
        campaign = Campaign(seed=42)
        before = campaign.puzzle
        with self.assertRaises(ValueError):
            campaign.next_round()
        self.assertEqual(campaign.puzzle, before)
        for number in range(1, 10):
            self.assertEqual(campaign.round_number, number)
            self.assertEqual(campaign.puzzle.level, min(number, MAX_LEVEL))
            self.assertTrue(simulate(campaign.puzzle.solution, campaign.puzzle.board).won)
            self.assertTrue(campaign.record_win())
            self.assertFalse(campaign.record_win())
            self.assertEqual(campaign.wins, number)
            previous_treasure = campaign.puzzle.board.treasure
            campaign.next_round()
            self.assertNotEqual(campaign.puzzle.board.treasure, previous_treasure)
            self.assertFalse(campaign.solved)

    def test_turbo_open_boards_have_longer_paths_and_multiple_routes_at_each_level(self):
        for seed in range(100):
            campaign = Campaign(seed=seed, mode=GameMode.TURBO)
            for level in range(1, MAX_LEVEL + 1):
                puzzle = campaign.puzzle
                with self.subTest(seed=seed, level=level):
                    self.assertEqual((puzzle.board.width, puzzle.board.height),
                                     (TURBO_WIDTH, TURBO_HEIGHT))
                    self.assertEqual(len(puzzle.solution),
                                     TURBO_FIRST_PATH + TURBO_PATH_STEP * (level - 1))
                    self.assertEqual(independent_distance(puzzle.board), len(puzzle.solution))
                    self.assertTrue(simulate(puzzle.solution, puzzle.board).won)
                    count, reachable = independent_route_count(puzzle.board)
                    self.assertGreaterEqual(count, 2)
                    self.assertEqual(reachable, TURBO_WIDTH * TURBO_HEIGHT - len(puzzle.board.obstacles))
                    self.assertEqual(len(puzzle.board.obstacles), 8 + 2 * level)
                    self.assertGreaterEqual(turns(puzzle.solution), 2)
                    self.assertEqual(sum(simulate(route, puzzle.board).won
                                         for route in puzzle.options), 1)
                    self.assertLessEqual(len(puzzle.solution), campaign.mode.max_commands)
                if level < MAX_LEVEL:
                    campaign.record_win()
                    previous_goal = puzzle.board.treasure
                    campaign.next_round()
                    self.assertNotEqual(campaign.puzzle.board.treasure, previous_goal)

    def test_turbo_seed_reproduces_open_board_and_difficulty_is_bounded(self):
        self.assertEqual(Campaign(seed=314, mode=GameMode.TURBO).puzzle,
                         Campaign(seed=314, mode=GameMode.TURBO).puzzle)
        with self.assertRaises(ValueError):
            generate_turbo_puzzle(0, Random(1))
        self.assertGreater(GameMode.TURBO.max_commands, GameMode.STANDARD.max_commands)

    def test_ultra_is_larger_and_progresses_to_45_steps_only_after_wins(self):
        for seed in range(20):
            campaign = Campaign(seed=seed, mode=GameMode.ULTRA)
            self.assertEqual(campaign.puzzle, Campaign(seed=seed, mode=GameMode.ULTRA).puzzle)
            with self.assertRaises(ValueError):
                campaign.next_round()
            for level in range(1, MAX_LEVEL + 3):
                puzzle = campaign.puzzle
                with self.subTest(seed=seed, level=level):
                    self.assertEqual(puzzle.level, min(level, MAX_LEVEL))
                    self.assertEqual(campaign.round_number, level)
                    self.assertEqual(campaign.wins, level - 1)
                    self.assertEqual((puzzle.board.width, puzzle.board.height),
                                     (ULTRA_WIDTH, ULTRA_HEIGHT))
                    expected = ULTRA_FIRST_PATH + ULTRA_PATH_STEP * (min(level, MAX_LEVEL) - 1)
                    self.assertEqual(len(puzzle.solution), expected)
                    self.assertEqual(independent_distance(puzzle.board), expected)
                    self.assertTrue(simulate(puzzle.solution, puzzle.board).won)
                    self.assertLessEqual(expected, GameMode.ULTRA.max_commands)
                    self.assertEqual(sum(simulate(route, puzzle.board).won
                                         for route in puzzle.options), 1)
                self.assertTrue(campaign.record_win())
                self.assertFalse(campaign.record_win())
                self.assertEqual(campaign.wins, level)
                campaign.next_round()
                self.assertNotEqual(campaign.puzzle.board.treasure, puzzle.board.treasure)
        for level in (0, MAX_LEVEL + 1):
            with self.assertRaises(ValueError):
                generate_ultra_puzzle(level, Random(1))
        self.assertGreater(ULTRA_WIDTH, TURBO_WIDTH)
        self.assertGreater(ULTRA_HEIGHT, TURBO_HEIGHT)
        self.assertGreater(ULTRA_FIRST_PATH, TURBO_FIRST_PATH + TURBO_PATH_STEP * (MAX_LEVEL - 1))

    def test_ultra_has_real_dead_end_choices_on_the_solution_for_many_seeds(self):
        for seed in range(100):
            for level in range(1, MAX_LEVEL + 1):
                with self.subTest(seed=seed, level=level):
                    puzzle = generate_ultra_puzzle(level, Random(seed))
                    board = puzzle.board
                    graph, route = independent_maze_graph_and_route(board)
                    self.assertEqual(len(route) - 1, 20 + 5 * (level - 1))
                    self.assertEqual((board.width, board.height), (21, 17))
                    self.assertEqual(independent_route_count(board), (1, len(graph)))
                    self.assertEqual(sum(map(len, graph.values())), 2 * (len(graph) - 1))
                    self.assertEqual(len(puzzle.solution), len(route) - 1)
                    self.assertTrue(simulate(puzzle.solution, board).won)
                    route_set = set(route)
                    choices = 0
                    dead_ends = set()
                    for junction in route[1:-1]:
                        entrances = graph[junction] - route_set
                        if not entrances:
                            continue
                        choices += 1
                        for entrance in entrances:
                            branch = {entrance}
                            queue = deque([entrance])
                            while queue:
                                for neighbor in graph[queue.popleft()] - route_set - branch:
                                    branch.add(neighbor)
                                    queue.append(neighbor)
                            self.assertGreaterEqual(len(branch), 2)
                            attachments = set().union(*(graph[p] & route_set for p in branch))
                            self.assertEqual(attachments, {junction})
                            leaves = {p for p in branch if len(graph[p]) == 1}
                            self.assertTrue(leaves)
                            dead_ends.update(leaves)
                    self.assertGreaterEqual(choices, 3)
                    self.assertGreaterEqual(len(dead_ends), 3)

    def test_ultra_seed_reproduces_every_level_and_command_limit_is_48(self):
        self.assertEqual(ULTRA_MAX_COMMANDS, 48)
        self.assertEqual(GameMode.ULTRA.max_commands, 48)
        for seed in (0, 7, 42, 314):
            for level in range(1, MAX_LEVEL + 1):
                with self.subTest(seed=seed, level=level):
                    puzzle = generate_ultra_puzzle(level, Random(seed))
                    self.assertEqual(puzzle, generate_ultra_puzzle(level, Random(seed)))
                    self.assertNotEqual(puzzle.board,
                                        generate_ultra_puzzle(level, Random(seed + 1)).board)


if __name__ == "__main__":
    unittest.main()
