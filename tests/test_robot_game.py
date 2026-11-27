import tkinter as tk
import unittest

from robot_controls import dispatch_key
from robot_model import (
    BOARD, BLOCKED_ROUTE, MAX_COMMANDS, SOLUTION, GameMode, Move, TURBO_MAX_COMMANDS,
    TURBO_FIRST_PATH, TURBO_PATH_STEP, TURBO_WIDTH, TURBO_HEIGHT,
    ULTRA_FIRST_PATH, ULTRA_PATH_STEP, ULTRA_MAX_COMMANDS, MAX_LEVEL,
)
from robot_window import RobotGameWindow


class RobotGameTests(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.game = RobotGameWindow(self.root, seed=7, board=BOARD)

    def tearDown(self):
        self.game.close()

    def finish_run(self):
        while self.game.running:
            self.assertIsNotNone(self.game.timer)
            self.root.after_cancel(self.game.timer)
            self.game.timer = None
            self.game.execute(self.game.active_index + 1)

    def test_win_and_replay(self):
        for move in SOLUTION:
            self.game.add(move)
        for _ in range(2):
            self.game.start()
            self.finish_run()
            self.assertEqual(self.game.position, BOARD.treasure)
            self.assertIn("SKARB ZDOBYTY", self.game.status.get())
            self.assertTrue(all(button["state"] == "normal" for button in self.game.controls))
            self.assertEqual(self.game.campaign.wins, 1)

    def test_next_round_is_gated_and_uses_new_map(self):
        before = self.game.board
        self.game.next_round()
        self.assertEqual(self.game.board, before)
        self.assertEqual(self.game.next_button["state"], "disabled")
        for move in SOLUTION:
            self.game.add(move)
        self.game.start()
        self.assertEqual(self.game.next_button["state"], "disabled")
        self.finish_run()
        self.game.next_round()
        self.assertNotEqual(self.game.board.treasure, before.treasure)
        self.assertEqual(self.game.campaign.puzzle.level, 2)
        self.assertEqual(self.game.campaign.round_number, 2)
        self.assertEqual(self.game.commands, [])
        self.assertEqual(self.game.position, self.game.board.start)
        self.assertEqual(self.game.next_button["state"], "disabled")
        self.assertIn("Skarby: 1", self.game.round_title.get())

    def test_turbo_can_be_started_immediately_by_button_or_keyboard(self):
        self.assertEqual(self.game.campaign.puzzle.level, 1)
        self.assertEqual(self.game.mode, GameMode.STANDARD)
        self.game.handle_key("t")
        self.assertEqual(self.game.mode, GameMode.TURBO)
        self.assertEqual((self.game.board.width, self.game.board.height), (TURBO_WIDTH, TURBO_HEIGHT))
        self.assertEqual(len(self.game.campaign.puzzle.solution), TURBO_FIRST_PATH)
        self.assertEqual(self.game.campaign.wins, 0)
        self.assertEqual(self.game.campaign.round_number, 1)
        self.assertEqual(self.game.turbo_button["state"], "normal")
        self.assertEqual(self.game.turbo_button["text"], "Standard (P)")
        self.assertIn("TURBO", self.game.round_title.get())
        self.game.handle_key("T")
        self.assertEqual(self.game.campaign.wins, 0)

    def test_ultra_and_turbo_switch_reset_campaign_and_update_heading(self):
        self.game.ultra_button.invoke()
        self.assertEqual(self.game.mode, GameMode.ULTRA)
        self.assertEqual((self.game.board.width, self.game.board.height), (21, 17))
        self.assertEqual(len(self.game.campaign.puzzle.solution), ULTRA_FIRST_PATH)
        self.assertIn("ULTRA", self.game.heading.get())
        self.assertIn("ULTRA", self.root.title())
        self.assertEqual(self.game.ultra_button["state"], "normal")
        self.assertEqual(self.game.ultra_button["text"], "Standard (P)")
        original = self.game.campaign
        self.game.handle_key("L")
        self.assertIs(self.game.campaign, original)
        self.game.campaign.record_win()
        self.game.add(Move.RIGHT)
        self.game.turbo_button.invoke()
        self.assertEqual(self.game.mode, GameMode.TURBO)
        self.assertEqual(self.game.campaign.wins, 0)
        self.assertEqual(self.game.campaign.round_number, 1)
        self.assertEqual(self.game.commands, [])
        self.assertEqual(self.game.position, self.game.board.start)
        self.assertIn("TURBO", self.game.heading.get())
        self.assertEqual(self.game.ultra_button["state"], "normal")

    def test_turbo_button_does_nothing_during_animation(self):
        self.game.add(Move.RIGHT)
        self.game.start()
        original = self.game.campaign
        self.game.handle_key("t")
        self.game.handle_key("L")
        self.assertIs(self.game.campaign, original)
        self.finish_run()

    def test_dynamic_hint_matches_current_board(self):
        from unittest.mock import patch

        self.game.campaign.solved = True
        self.game.next_round()
        from robot_window import ARROWS
        beginning = self.game.campaign.puzzle.solution[:2]
        with patch("robot_window.messagebox.showinfo") as popup:
            self.game.hint()
        self.assertIn("  ".join(ARROWS[move] for move in beginning), popup.call_args.args[1])

    def test_collision_and_edit(self):
        for move in BLOCKED_ROUTE:
            self.game.add(move)
        self.game.start()
        self.finish_run()
        self.assertEqual(self.game.position, (1, 2))
        self.assertIn("Krok 2", self.game.status.get())
        self.game.undo()
        self.assertEqual(self.game.position, BOARD.start)
        self.assertEqual(len(self.game.commands), len(BLOCKED_ROUTE) - 1)
        self.game.clear()
        self.assertEqual(self.game.commands, [])

    def test_empty_start_and_command_limit(self):
        self.game.start()
        self.assertFalse(self.game.running)
        self.assertIn("Najpierw", self.game.status.get())
        for _ in range(MAX_COMMANDS + 2):
            self.game.add(Move.RIGHT)
        self.assertEqual(len(self.game.commands), MAX_COMMANDS)
        self.assertIn("12 kroków", self.game.status.get())

    def test_cannot_change_program_during_animation(self):
        self.game.add(Move.RIGHT)
        self.game.start()
        self.game.add(Move.DOWN)
        self.game.undo()
        self.game.clear()
        self.assertEqual(self.game.commands, [Move.RIGHT])
        self.finish_run()
        self.assertIn("Skarb jeszcze czeka", self.game.status.get())

    def test_small_window_shows_controls_status_and_twelve_steps(self):
        self.root.geometry("800x600")
        self.root.deiconify()
        self.root.update()
        for _ in range(MAX_COMMANDS):
            self.game.add(Move.RIGHT)
        self.root.update()
        self.assertEqual(
            {int(widget.grid_info()["row"]) for widget in self.game.program_frame.winfo_children()},
            {0},
        )
        widgets = [*self.game.controls, self.game.status_label,
                   *self.game.program_frame.winfo_children()]
        for widget in widgets:
            with self.subTest(widget=widget):
                self.assertTrue(widget.winfo_ismapped())
                self.assertGreaterEqual(widget.winfo_height(), widget.winfo_reqheight())
                x = widget.winfo_rootx() - self.root.winfo_rootx()
                y = widget.winfo_rooty() - self.root.winfo_rooty()
                self.assertGreaterEqual(x, 0)
                self.assertGreaterEqual(y, 0)
                self.assertLessEqual(x + widget.winfo_width(), self.root.winfo_width())
                self.assertLessEqual(y + widget.winfo_height(), self.root.winfo_height())

    def test_animation_callback_finishes_without_manual_stepping(self):
        self.game.add(Move.RIGHT)
        self.game.start()
        self.root.after(1500, self.root.quit)
        self.root.mainloop()
        self.assertFalse(self.game.running)
        self.assertEqual(self.game.position, (1, 2))
        self.assertIn("Skarb jeszcze czeka", self.game.status.get())

    def test_keyboard_dispatch_maps_requested_hotkeys(self):
        calls = []
        for keysym in ("Up", "Down", "Left", "Right", "s", "S", "n", "N",
                       "u", "U", "r", "R"):
            with self.subTest(keysym=keysym):
                self.assertTrue(dispatch_key(keysym, calls.append))
        self.assertFalse(dispatch_key("Escape", calls.append))
        self.assertTrue(dispatch_key("t", calls.append))
        self.assertTrue(dispatch_key("T", calls.append))
        self.assertTrue(dispatch_key("l", calls.append))
        self.assertTrue(dispatch_key("L", calls.append))
        for keysym in ("p", "P", "e", "E"):
            self.assertTrue(dispatch_key(keysym, calls.append))
        self.assertEqual(len(calls), 20)

    def test_keyboard_events_control_arrows_and_actions(self):
        self.root.deiconify()
        self.root.focus_force()
        self.root.update()
        self.game.controls[0].focus_force()
        self.root.update()
        for key, expected in (("Right", Move.RIGHT), ("Up", Move.UP),
                              ("Left", Move.LEFT), ("Down", Move.DOWN)):
            self.root.event_generate("<KeyPress>", keysym=key)
            self.root.update()
            self.assertEqual(self.game.commands[-1], expected)
        self.root.event_generate("<KeyPress>", keysym="R")
        self.root.update()
        self.assertEqual(self.game.commands, [])
        self.root.event_generate("<KeyPress>", keysym="Right")
        self.root.event_generate("<KeyPress>", keysym="s")
        self.root.update()
        self.assertTrue(self.game.running)
        self.finish_run()
        self.root.event_generate("<KeyPress>", keysym="u")
        self.root.update()
        self.assertEqual(len(self.game.commands), 0)

    def test_n_key_starts_a_new_round_only_after_collecting_the_treasure(self):
        self.root.deiconify()
        self.root.focus_force()
        self.root.update()
        self.root.event_generate("<KeyPress>", keysym="n")
        self.root.update()
        self.assertEqual(self.game.campaign.round_number, 1)
        for move in SOLUTION:
            self.game.add(move)
        self.game.start()
        self.finish_run()
        self.root.event_generate("<KeyPress>", keysym="N")
        self.root.update()
        self.assertEqual(self.game.campaign.round_number, 2)
        self.assertEqual(self.game.campaign.wins, 1)

    def test_turbo_window_accepts_long_keyboard_program_and_uses_bigger_map(self):
        self.game.close()
        self.root = tk.Tk()
        self.root.withdraw()
        self.game = RobotGameWindow(self.root, seed=42, mode=GameMode.TURBO)
        self.root.geometry("1000x750")
        self.root.deiconify()
        solution = self.game.campaign.puzzle.solution
        self.assertEqual(len(solution), TURBO_FIRST_PATH)
        self.assertGreater(self.game.board.width, BOARD.width)
        self.assertGreater(self.game.board.height, BOARD.height)
        for move in solution:
            self.game.handle_key({
                Move.UP: "Up", Move.DOWN: "Down",
                Move.LEFT: "Left", Move.RIGHT: "Right",
            }[move])
        self.root.update()
        self.assertEqual(self.game.commands, list(solution))
        self.assertLessEqual(len(self.game.commands), TURBO_MAX_COMMANDS)
        self.assertEqual(
            len(self.game.program_frame.winfo_children()),
            len(solution),
        )
        controls = [*self.game.controls, self.game.status_label, self.game.canvas,
                    *self.game.program_frame.winfo_children()]
        for control in controls:
            with self.subTest(control=control):
                self.assertTrue(control.winfo_ismapped())
                self.assertGreaterEqual(control.winfo_height(), control.winfo_reqheight())
                x = control.winfo_rootx() - self.root.winfo_rootx()
                y = control.winfo_rooty() - self.root.winfo_rooty()
                self.assertGreaterEqual(x, 0)
                self.assertGreaterEqual(y, 0)
                self.assertLessEqual(x + control.winfo_width(), self.root.winfo_width())
                self.assertLessEqual(y + control.winfo_height(), self.root.winfo_height())
        self.game.start()
        self.finish_run()
        self.assertEqual(self.game.campaign.wins, 1)
        self.game.handle_key("N")
        self.assertEqual(self.game.campaign.puzzle.level, 2)
        self.assertEqual(len(self.game.campaign.puzzle.solution), len(solution) + TURBO_PATH_STEP)

    def test_ultra_last_level_accepts_full_solution_and_enforces_limit(self):
        self.game.start_ultra()
        for _ in range(MAX_LEVEL - 1):
            self.game.campaign.record_win()
            self.game.next_round()
        solution = self.game.campaign.puzzle.solution
        self.assertEqual(len(solution), ULTRA_FIRST_PATH + ULTRA_PATH_STEP * (MAX_LEVEL - 1))
        self.root.geometry("1000x750")
        self.root.deiconify()
        for move in solution:
            self.game.add(move)
        self.root.update()
        for widget in [*self.game.controls, self.game.canvas, self.game.status_label,
                       *self.game.program_frame.winfo_children()]:
            with self.subTest(widget=widget):
                self.assertTrue(widget.winfo_ismapped())
                self.assertGreaterEqual(widget.winfo_height(), widget.winfo_reqheight())
                self.assertLessEqual(widget.winfo_rooty() - self.root.winfo_rooty()
                                     + widget.winfo_height(), self.root.winfo_height())
                self.assertLessEqual(widget.winfo_rootx() - self.root.winfo_rootx()
                                     + widget.winfo_width(), self.root.winfo_width())
        self.game.start()
        self.finish_run()
        self.assertEqual(self.game.campaign.wins, MAX_LEVEL)
        self.game.clear()
        for _ in range(ULTRA_MAX_COMMANDS + 1):
            self.game.add(Move.RIGHT)
        self.assertEqual(len(self.game.commands), ULTRA_MAX_COMMANDS)

    def test_standard_mode_still_enforces_its_short_program_limit(self):
        for _ in range(MAX_COMMANDS + 1):
            self.game.add(Move.RIGHT)
        self.assertEqual(len(self.game.commands), MAX_COMMANDS)
        self.assertIn("12 kroków", self.game.status.get())

    def test_start_marker_stays_visible_after_robot_moves(self):
        self.root.geometry("800x600")
        self.root.deiconify()
        self.root.update()
        self.game.add(Move.RIGHT)
        self.game.start()
        self.assertNotEqual(self.game.position, self.game.board.start)
        self.assertEqual(len(self.game.canvas.find_withtag("start-label")), 1)
        self.assertEqual(
            self.game.canvas.itemcget(
                self.game.canvas.find_withtag("start-label")[0], "text"),
            "START",
        )
        self.assertTrue(self.game.canvas.find_withtag("robot"))
        self.assertTrue(self.game.canvas.find_withtag("treasure"))
        self.finish_run()

    def test_mode_legend_and_program_counter_follow_edits_and_resets(self):
        self.game.add(Move.RIGHT)
        self.assertIn("1/12 kroków", self.game.program_title.get())
        self.assertIn("kamienie", self.game.legend["text"])
        self.game.start_ultra()
        self.assertIn("ULTRA", self.game.mode_caption.get())
        self.assertIn("48 strzałek", self.game.mode_caption.get())
        self.assertIn("ściany", self.game.legend["text"])
        self.assertIn("0/48 kroków", self.game.program_title.get())
        self.game.add(Move.UP)
        self.assertIn("1/48 kroków", self.game.program_title.get())
        self.game.undo()
        self.assertIn("0/48 kroków", self.game.program_title.get())

    def test_maze_walls_are_blocks_instead_of_scattered_rocks(self):
        self.game.start_ultra()
        self.root.deiconify()
        self.root.update()
        walls = self.game.canvas.find_withtag("wall")
        self.assertEqual(len(walls), len(self.game.board.obstacles))
        self.assertTrue(all(self.game.canvas.type(wall) == "rectangle" for wall in walls))
        self.assertFalse(any(self.game.canvas.type(item) == "polygon"
                             for item in self.game.canvas.find_withtag("obstacle")))
        for move in Move:
            dx, dy = move.delta
            start_x, start_y = self.game.board.start
            if (start_x + dx, start_y + dy) in self.game.board.obstacles:
                self.game.add(move)
                self.game.start()
                self.assertFalse(self.game.running)
                self.assertIn("Ściana labiryntu", self.game.status.get())
                break
        else:
            self.fail("Test maze needs a wall next to START")

    def test_turbo_draws_rocks_and_uses_stone_hint_and_collision_message(self):
        from unittest.mock import patch
        from robot_model import Board, Campaign
        self.game.start_turbo()
        self.root.deiconify()
        self.root.update()
        self.assertIn("kamienie", self.game.legend["text"])
        self.assertNotIn("labirynt", self.game.mode_caption.get())
        rocks = self.game.canvas.find_withtag("obstacle")
        self.assertEqual(len(rocks), len(self.game.board.obstacles))
        self.assertTrue(all(self.game.canvas.type(item) == "polygon" for item in rocks))
        with patch("robot_window.messagebox.showinfo") as popup:
            self.game.hint()
        self.assertIn("kamienie", popup.call_args.args[1])
        self.assertNotIn("ściany", popup.call_args.args[1])
        # A fixed rock directly right of START makes the collision deterministic.
        self.game.campaign = Campaign(
            board=Board(11, 9, (0, 0), (3, 0), frozenset({(1, 0)})),
            mode=GameMode.TURBO)
        self.game.reset_robot()
        self.game.add(Move.RIGHT)
        self.game.start()
        self.assertEqual(self.game.result, "collision")
        self.assertIn("Kamień", self.game.status.get())

    def test_program_reflows_on_resize_without_editing(self):
        self.root.geometry("1000x750")
        self.root.deiconify()
        for _ in range(MAX_COMMANDS):
            self.game.add(Move.RIGHT)
        self.root.update()
        self.assertEqual(
            {int(widget.grid_info()["row"]) for widget in self.game.program_frame.winfo_children()},
            {0, 1},
        )
        self.root.geometry("800x600")
        self.root.update()
        self.assertEqual(
            {int(widget.grid_info()["row"]) for widget in self.game.program_frame.winfo_children()},
            {0},
        )
        self.assertEqual(len(self.game.commands), MAX_COMMANDS)

    def result_text(self, tag):
        return " ".join(self.game.canvas.itemcget(item, "text")
                        for item in self.game.canvas.find_withtag(tag)
                        if self.game.canvas.type(item) == "text")

    def click_result_action(self):
        self.root.update()
        item = self.game.canvas.find_withtag("result-action")[0]
        x0, y0, x1, y1 = self.game.canvas.bbox(item)
        x, y = int((x0 + x1) / 2), int((y0 + y1) / 2)
        self.game.canvas.event_generate("<Motion>", x=x, y=y)
        self.game.canvas.event_generate("<Button-1>", x=x, y=y)
        self.root.update()

    def test_success_card_survives_resize_and_click_starts_next_round(self):
        self.root.deiconify()
        self.root.update()
        for move in SOLUTION:
            self.game.add(move)
        for _ in range(2):
            self.game.start()
            self.assertIsNone(self.game.result)
            self.finish_run()
            self.assertEqual(self.game.result, "success")
            self.assertIn("SKARB ZDOBYTY", self.result_text("result-title"))
            self.assertIn("Kolejna runda (N)", self.result_text("result-action"))
            self.assertEqual(self.game.campaign.wins, 1)
            self.assertIsNone(self.game.timer)
        self.root.geometry("800x600")
        self.root.update()
        self.assertIn("SKARB ZDOBYTY", self.result_text("result-title"))
        self.click_result_action()
        self.assertEqual(self.game.campaign.round_number, 2)
        self.assertEqual(self.game.campaign.wins, 1)
        self.assertIsNone(self.game.result)
        self.assertFalse(self.game.canvas.find_withtag("result-card"))
        self.assertFalse(self.game.running)

    def test_collision_card_marks_blocked_cell_and_allows_editing(self):
        self.root.deiconify()
        self.root.update()
        for move in BLOCKED_ROUTE:
            self.game.add(move)
        self.game.start()
        self.finish_run()
        self.assertEqual(self.game.result, "collision")
        self.assertEqual(self.game.result_point, (2, 2))
        self.assertIn("STOP", self.result_text("result-title"))
        self.assertIn("Krok 2", self.result_text("result-detail"))
        self.assertTrue(self.game.canvas.find_withtag("result-marker"))
        self.assertEqual(self.game.active_index, 1)
        commands = self.game.commands.copy()
        self.click_result_action()
        self.assertIsNone(self.game.result)
        self.assertEqual(self.game.commands, commands)
        self.assertEqual(self.game.position, self.game.board.start)
        self.assertEqual(self.game.trail, [self.game.board.start])
        self.assertIsNone(self.game.active_index)
        self.assertFalse(self.game.canvas.find_withtag("result-marker"))
        self.assertFalse(self.game.running)
        self.assertIsNone(self.game.timer)
        self.assertIn("START (S)", self.game.status.get())

    def test_correct_arrows_click_resets_missed_goal_without_changing_program(self):
        self.root.deiconify()
        self.root.update()
        self.game.add(Move.RIGHT)
        self.game.start()
        self.finish_run()
        self.assertNotEqual(self.game.position, self.game.board.start)
        commands = self.game.commands.copy()
        self.click_result_action()
        self.assertEqual(self.game.position, self.game.board.start)
        self.assertEqual(self.game.trail, [self.game.board.start])
        self.assertEqual(self.game.commands, commands)
        self.assertIsNone(self.game.active_index)
        self.assertIsNone(self.game.result)
        self.assertFalse(self.game.canvas.find_withtag("result-card"))
        self.assertFalse(self.game.running)
        self.assertEqual(self.game.campaign.wins, 0)

    def test_open_treasure_contains_gold_and_diamond_in_every_mode(self):
        self.root.deiconify()
        for mode in GameMode:
            with self.subTest(mode=mode):
                self.game.switch_mode(mode)
                self.root.update()
                for tag in ("treasure-lid", "treasure-gold", "treasure-diamond",
                            "treasure-front", "treasure-sparkle"):
                    self.assertTrue(self.game.canvas.find_withtag(tag))
                for item in self.game.canvas.find_withtag("treasure"):
                    coordinates = self.game.canvas.coords(item)
                    self.assertTrue(all(0 <= value <= self.game.canvas.winfo_width()
                                        for value in coordinates[::2]))
                    self.assertTrue(all(0 <= value <= self.game.canvas.winfo_height()
                                        for value in coordinates[1::2]))

    def test_missed_goal_card_and_overlay_clearing_actions(self):
        self.root.deiconify()
        self.root.update()
        for action in (self.game.undo, self.game.clear,
                       lambda: self.game.add(Move.UP), self.game.start_turbo):
            with self.subTest(action=action):
                self.game.clear()
                self.game.add(Move.RIGHT)
                self.game.start()
                self.finish_run()
                self.assertEqual(self.game.result, "missed")
                self.assertIn("Skarb jeszcze czeka", self.result_text("result-title"))
                self.assertEqual(self.game.result_point, self.game.position)
                self.assertIn("Popraw strzałki", self.result_text("result-action"))
                action()
                self.assertIsNone(self.game.result)
                self.assertFalse(self.game.canvas.find_withtag("result-card"))

    def test_ultra_result_card_fits_with_full_program(self):
        self.game.start_ultra()
        for _ in range(MAX_LEVEL - 1):
            self.game.campaign.record_win()
            self.game.next_round()
        self.root.geometry("1000x750")
        self.root.deiconify()
        for move in self.game.campaign.puzzle.solution:
            self.game.add(move)
        self.root.update()
        self.game.start()
        self.finish_run()
        self.root.update()
        self.assertEqual(self.game.result, "success")
        for item in self.game.canvas.find_withtag("result-card"):
            x0, y0, x1, y1 = self.game.canvas.bbox(item)
            self.assertGreaterEqual(x0, 0)
            self.assertGreaterEqual(y0, 0)
            self.assertLessEqual(x1, self.game.canvas.winfo_width())
            self.assertLessEqual(y1, self.game.canvas.winfo_height())

    def test_border_collision_result_marker_stays_on_visible_board(self):
        self.root.geometry("800x600")
        self.root.deiconify()
        self.root.update()
        self.game.add(Move.LEFT)
        self.game.start()
        self.assertEqual(self.game.result, "collision")
        self.assertEqual(self.game.result_point, (-1, 2))
        x0, y0, x1, y1 = self.game.canvas.bbox("result-marker")
        self.assertGreaterEqual(x0, 0)
        self.assertGreaterEqual(y0, 0)
        self.assertLessEqual(x1, self.game.canvas.winfo_width())
        self.assertLessEqual(y1, self.game.canvas.winfo_height())

    def test_other_mode_buttons_return_to_standard_and_reset_once(self):
        for mode, button in ((GameMode.TURBO, self.game.turbo_button),
                             (GameMode.ULTRA, self.game.ultra_button)):
            with self.subTest(mode=mode):
                self.game.switch_mode(mode)
                self.game.campaign.record_win()
                self.game.add(Move.RIGHT)
                self.assertEqual(button["text"], "Standard (P)")
                self.assertEqual(button["state"], "normal")
                button.invoke()
                self.assertEqual(self.game.mode, GameMode.STANDARD)
                self.assertEqual((self.game.board.width, self.game.board.height), (5, 4))
                self.assertEqual(self.game.commands, [])
                self.assertEqual(self.game.campaign.wins, 0)
                self.assertEqual(self.game.campaign.round_number, 1)
                self.assertEqual(self.game.turbo_button["text"], "Turbo teraz (T)")
                self.assertEqual(self.game.ultra_button["text"], "Ultra teraz (L)")
                campaign = self.game.campaign
                self.game.add(Move.RIGHT)
                self.game.handle_key("p")
                self.assertIs(self.game.campaign, campaign)
                self.assertEqual(self.game.commands, [Move.RIGHT])

    def test_real_p_and_e_events_correct_failure_but_never_advance_success(self):
        self.root.deiconify()
        self.root.focus_force()
        self.root.update()
        for mode in (GameMode.TURBO, GameMode.ULTRA):
            self.game.switch_mode(mode)
            self.root.event_generate("<KeyPress>", keysym="P")
            self.root.update()
            self.assertEqual(self.game.mode, GameMode.STANDARD)
        for program in ((Move.RIGHT,), BLOCKED_ROUTE):
            self.game.clear()
            for move in program:
                self.game.add(move)
            self.game.start()
            self.finish_run()
            self.assertIn("Popraw strzałki (E)", self.result_text("result-action"))
            self.root.event_generate("<KeyPress>", keysym="e")
            self.root.update()
            self.assertIsNone(self.game.result)
            self.assertEqual(self.game.commands, list(program))
            self.assertEqual(self.game.position, self.game.board.start)
            self.assertEqual(self.game.trail, [self.game.board.start])
            self.assertIsNone(self.game.active_index)
            self.assertFalse(self.game.running)
        self.game.clear()
        for move in self.game.campaign.puzzle.solution:
            self.game.add(move)
        self.game.start()
        self.finish_run()
        self.root.event_generate("<KeyPress>", keysym="E")
        self.root.update()
        self.assertEqual(self.game.result, "success")
        self.assertEqual(self.game.campaign.round_number, 1)
        self.assertEqual(self.game.campaign.wins, 1)
        self.assertIn("E: popraw", self.game.keyboard_legend["text"])
        self.assertIn("P: standard", self.game.keyboard_legend["text"])

    def test_mode_delays_and_animation_lock_with_timer_cleanup(self):
        from unittest.mock import patch

        for mode, delay in ((GameMode.STANDARD, 750),
                            (GameMode.TURBO, 500), (GameMode.ULTRA, 250)):
            with self.subTest(mode=mode):
                self.game.switch_mode(mode)
                self.game.clear()
                self.game.add(self.game.campaign.puzzle.solution[0])
                with patch.object(self.root, "after", wraps=self.root.after) as after:
                    self.game.start()
                    self.assertEqual(after.call_args.args[0], delay)
                campaign = self.game.campaign
                timer = self.game.timer
                self.assertEqual(self.game.turbo_button["state"], "disabled")
                self.assertEqual(self.game.ultra_button["state"], "disabled")
                for key in ("p", "P", "e", "E", "t", "l"):
                    self.game.handle_key(key)
                self.assertIs(self.game.campaign, campaign)
                self.assertEqual(self.game.timer, timer)
                self.assertTrue(self.game.running)
                self.finish_run()
                self.assertIsNone(self.game.timer)
                self.assertEqual(self.game.turbo_button["state"], "normal")
                self.assertEqual(self.game.ultra_button["state"], "normal")

    def test_close_cancels_pending_mode_timer(self):
        from unittest.mock import patch

        self.game.start_ultra()
        self.game.add(self.game.campaign.puzzle.solution[0])
        self.game.start()
        timer = self.game.timer
        with patch.object(self.root, "after_cancel", wraps=self.root.after_cancel) as cancel:
            self.game.close()
            cancel.assert_called_once_with(timer)
        self.assertIsNone(self.game.timer)
        self.root = tk.Tk()
        self.root.withdraw()
        self.game = RobotGameWindow(self.root, seed=7, board=BOARD)


if __name__ == "__main__":
    unittest.main()
