"""Simple entry point for the robot game."""

import argparse
import tkinter as tk

from robot_model import GameMode
from robot_window import RobotGameWindow


def main() -> None:
    """Configure and start the robot game."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fullscreen", action="store_true", help="Start in full-screen mode.")
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--turbo", action="store_true",
                        help="Start immediately in turbo mode (skip the standard adventure).")
    modes.add_argument("--ultra", action="store_true", help="Start in the large, harder ultra maze.")
    parser.add_argument("--demo", action="store_true", help="Queue the solution for the current round.")
    parser.add_argument("--seed", type=int, help="Repeat a game, for example --seed 42.")
    args = parser.parse_args()

    mode = GameMode.ULTRA if args.ultra else GameMode.TURBO if args.turbo else GameMode.STANDARD
    root = tk.Tk()
    game = RobotGameWindow(root, fullscreen=args.fullscreen, seed=args.seed, mode=mode)
    if args.demo:
        for move in game.campaign.puzzle.solution:
            game.add(move)
    root.mainloop()


if __name__ == "__main__":
    main()
