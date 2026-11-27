import unittest

from robot_model import BOARD, BLOCKED_ROUTE, BUG_ROUTE, SOLUTION, Board, Move, advance, simulate


class RobotModelTests(unittest.TestCase):
    def test_solution_reaches_treasure_in_six_moves(self):
        result = simulate(SOLUTION)
        self.assertTrue(result.won)
        self.assertIsNone(result.error)
        self.assertEqual(result.positions[-1], BOARD.treasure)
        self.assertEqual(len(result.positions), 7)

    def test_blocked_route_stops_at_second_command(self):
        result = simulate(BLOCKED_ROUTE)
        self.assertFalse(result.won)
        self.assertEqual(result.failed_command, 2)
        self.assertIn("Kamień", result.error)
        self.assertEqual(result.positions[-1], (1, 2))

    def test_wrong_direction_misses_treasure(self):
        result = simulate(BUG_ROUTE)
        self.assertFalse(result.won)
        self.assertIsNone(result.error)
        self.assertEqual(result.positions[-1], (4, 2))

    def test_moving_outside_board_preserves_position(self):
        for position, move in (((0, 0), Move.LEFT), ((0, 0), Move.UP),
                               ((4, 3), Move.RIGHT), ((4, 3), Move.DOWN)):
            with self.subTest(position=position, move=move):
                result = advance(BOARD, position, move)
                self.assertEqual(result.position, position)
                self.assertIn("Brzeg", result.error)

    def test_empty_program_does_not_win(self):
        self.assertFalse(simulate(()).won)
        self.assertEqual(simulate(()).positions, (BOARD.start,))

    def test_treasure_only_counts_at_end(self):
        self.assertFalse(simulate((*SOLUTION, Move.DOWN)).won)

    def test_invalid_board_is_rejected(self):
        for kwargs in ({"width": 0}, {"start": (-1, 0)}, {"treasure": (99, 99)},
                       {"start": (2, 2)}, {"obstacles": frozenset({(6, 6)})},
                       {"start": BOARD.treasure}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                Board(**kwargs)

    def test_robot_cannot_start_on_obstacle(self):
        with self.assertRaises(ValueError):
            advance(BOARD, (2, 2), Move.UP)


if __name__ == "__main__":
    unittest.main()
