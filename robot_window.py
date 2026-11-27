"""Okno gry: plansza, program robota i czytelne animacje krok po kroku."""

import tkinter as tk
from tkinter import messagebox

from robot_controls import bind_keyboard
from robot_model import MAX_LEVEL, Board, Campaign, GameMode, Move, advance


NAVY = "#13233F"
PANEL = "#213653"
WHITE = "#F5F7FC"
CYAN = "#65DCDD"
YELLOW = "#FFD369"
CORAL = "#FF917C"
PATH = "#DFEAF2"
WALL = "#506680"
TRAIL = "#A9E5DC"
ARROWS = {Move.RIGHT: "→", Move.UP: "↑", Move.LEFT: "←", Move.DOWN: "↓"}


class RobotGameWindow:
    def __init__(self, root: tk.Tk, fullscreen: bool = False,
                 seed: int | None = None, board: Board | None = None,
                 mode: GameMode = GameMode.STANDARD) -> None:
        self.root = root
        self.campaign = Campaign(seed=seed, board=board, mode=mode)
        self.mode = mode
        self.commands: list[Move] = []
        self.position = self.board.start
        self.trail = [self.board.start]
        self.running = False
        self.active_index: int | None = None
        self.timer: str | None = None
        self.result: str | None = None
        self.result_detail = ""
        self.result_point: tuple[int, int] | None = None
        self.controls: list[tk.Button] = []
        self.layout_width = 0
        root.title(f"Misja: zaprogramuj robota! — {mode.title}")
        root.configure(bg=NAVY)
        width = min(1180, root.winfo_screenwidth() - 60)
        height = min(820, root.winfo_screenheight() - 80)
        root.geometry(f"{width}x{height}")
        root.minsize(800, 600)
        root.attributes("-fullscreen", fullscreen)
        self.seed = seed
        root.columnconfigure(0, weight=1)
        root.rowconfigure(2, weight=1)
        root.bind("<F11>", self.toggle_fullscreen)
        root.bind("<Escape>", lambda event: root.attributes("-fullscreen", False))
        root.protocol("WM_DELETE_WINDOW", self.close)

        self.heading = tk.StringVar(value=f"MISJA: ZAPROGRAMUJ ROBOTA!  •  {mode.title}")
        tk.Label(root, textvariable=self.heading,
                 font=("Arial", 20, "bold"),
                 fg=WHITE, bg=NAVY).grid(row=0, column=0, pady=(12, 4))
        self.round_title = tk.StringVar()
        tk.Label(root, textvariable=self.round_title,
                 font=("Arial", 13),
                 fg=CYAN, bg=NAVY).grid(row=1, column=0)
        middle = tk.Frame(root, bg=NAVY)
        middle.grid(row=2, column=0, sticky="nsew", padx=18, pady=10)
        middle.columnconfigure(0, weight=1)
        middle.rowconfigure(0, weight=1)
        map_panel = tk.Frame(middle, bg=PANEL)
        map_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 14))
        map_panel.columnconfigure(0, weight=1)
        map_panel.rowconfigure(1, weight=1)
        tk.Label(map_panel, text="1. ZNAJDŹ DROGĘ OD STARTU DO SKARBU",
                 font=("Arial", 11, "bold"), fg=WHITE, bg=PANEL).grid(
                     row=0, column=0, pady=(6, 0))
        self.canvas = tk.Canvas(map_panel, bg=PANEL, highlightthickness=0,
                                width=1, height=1)
        self.canvas.grid(row=1, column=0, sticky="nsew")
        self.canvas.bind("<Configure>", lambda event: self.draw_board())
        self.canvas.tag_bind("result-action", "<Button-1>", self.result_action)
        self.canvas.tag_bind("result-action", "<Enter>",
                             lambda event: self.canvas.configure(cursor="hand2"))
        self.canvas.tag_bind("result-action", "<Leave>",
                             lambda event: self.canvas.configure(cursor=""))
        self.legend = tk.Label(
            map_panel, text="S: START  •  złota skrzynia: SKARB\n"
            "jasne pola: droga  •  ciemne bloki: przeszkody",
            font=("Arial", 10), fg=WHITE, bg=PANEL,
        )
        self.legend.grid(row=2, column=0, pady=(0, 6))
        sidebar = tk.Frame(middle, bg=NAVY, width=210)
        sidebar.grid(row=0, column=1, sticky="n")
        tk.Label(sidebar, text="2. UŁÓŻ STRZAŁKI", font=("Arial", 13, "bold"),
                 fg=WHITE, bg=NAVY).pack(pady=(0, 4))
        directions = tk.Frame(sidebar, bg=NAVY)
        directions.pack()
        for move, row, col in ((Move.UP, 0, 1), (Move.RIGHT, 1, 2),
                               (Move.LEFT, 1, 0), (Move.DOWN, 1, 1)):
            button = self.button(directions, ARROWS[move], lambda m=move: self.add(m),
                                 CYAN, font_size=18)
            button.configure(pady=1)
            button.grid(row=row, column=col, padx=3, pady=2, ipadx=4)
        self.next_button = self.button(
            sidebar, "Kolejna runda (N)", self.next_round, YELLOW, font_size=12,
        )
        self.next_button.configure(pady=1)
        self.next_button.pack(fill="x", pady=(3, 0))
        self.mode_caption = tk.StringVar()
        tk.Label(sidebar, textvariable=self.mode_caption, font=("Arial", 10, "bold"),
                 fg=CYAN, bg=NAVY, justify="center").pack(pady=(7, 2))
        self.turbo_button = self.button(
            sidebar, "Turbo teraz (T)", self.start_turbo, CORAL, font_size=11,
        )
        self.turbo_button.configure(pady=1)
        self.turbo_button.pack(fill="x", pady=(3, 0))
        self.ultra_button = self.button(
            sidebar, "Ultra teraz (L)", self.start_ultra, CORAL, font_size=11,
        )
        self.ultra_button.configure(pady=1)
        self.ultra_button.pack(fill="x", pady=(3, 0))
        self.keyboard_legend = tk.Label(
            sidebar, text="Klawiatura:\n↑ ↓ ← → dodaj krok\nS: start • N: nowa runda\n"
                 "U: cofnij • R: wyczyść\nE: popraw strzałki\nP: standard • T: turbo • L: ultra\n"
                 "F11: pełny ekran • Esc: okno",
                 font=("Arial", 10), fg=WHITE, bg=NAVY)
        self.keyboard_legend.pack(pady=4)

        actions = tk.Frame(root, bg=NAVY)
        actions.grid(row=3, column=0, sticky="ew", padx=18, pady=4)
        for col, (text, callback, color) in enumerate((
            ("3. START (S)", self.start, YELLOW),
            ("Cofnij (U)", self.undo, WHITE),
            ("Wyczyść (R)", self.clear, WHITE),
            ("Pokaż podpowiedź", self.hint, CORAL),
        )):
            actions.columnconfigure(col, weight=1, uniform="actions")
            self.button(actions, text, callback, color, font_size=12).grid(
                row=0, column=col, sticky="ew", padx=3)
        self.status = tk.StringVar(value="Zaplanuj drogę. Dodaj strzałki, potem naciśnij START!")
        self.status_label = tk.Label(
            root, textvariable=self.status, font=("Arial", 14, "bold"),
            fg=YELLOW, bg=NAVY, wraplength=740,
        )
        self.status_label.grid(row=4, column=0, padx=18, pady=4)
        self.program_title = tk.StringVar()
        tk.Label(root, textvariable=self.program_title, font=("Arial", 11, "bold"),
                 fg=CYAN, bg=NAVY).grid(row=5, column=0, pady=(3, 0))
        self.program_frame = tk.Frame(root, bg=NAVY)
        self.program_frame.grid(row=6, column=0, padx=18, pady=(4, 10))
        root.bind("<Configure>", self.resize_layout, add="+")
        bind_keyboard(root, self.handle_key)
        self.update_round_title()
        self.set_running(False)
        self.draw_program()

    @property
    def board(self) -> Board:
        return self.campaign.puzzle.board

    def update_round_title(self) -> None:
        level = self.campaign.puzzle.level
        if self.mode is not GameMode.STANDARD:
            details = (f"Poziom {level}/{MAX_LEVEL}  |  {self.board.width}×{self.board.height}"
                       f"  |  {len(self.campaign.puzzle.solution)} kroków")
        else:
            details = f"Poziom {level}/{MAX_LEVEL}"
        self.round_title.set(
            f"{self.mode.title}  |  Runda {self.campaign.round_number}"
            f"  |  {details}  |  Skarby: {self.campaign.wins}"
        )
        description = {
            GameMode.STANDARD: "mała plansza",
            GameMode.TURBO: "otwarta plansza z kamieniami",
            GameMode.ULTRA: "wielki labirynt",
        }[self.mode]
        self.mode_caption.set(f"{self.mode.title} • {description}\n"
                              f"Limit: {self.mode.max_commands} strzałek")
        self.legend.configure(text=(
            "S: START  •  złota skrzynia: SKARB\n"
            "jasne pola: droga  •  "
            + ("ściany: ciemne bloki" if self.mode is GameMode.ULTRA else "przeszkody: kamienie")
        ))

    def resize_layout(self, event) -> None:
        if event.widget is self.root and event.width != self.layout_width:
            self.layout_width = event.width
            self.status_label.configure(wraplength=max(300, event.width - 48))
            self.root.after_idle(self.draw_program)

    def start_turbo(self) -> None:
        self.switch_mode(GameMode.TURBO)

    def start_ultra(self) -> None:
        self.switch_mode(GameMode.ULTRA)

    def start_standard(self) -> None:
        self.switch_mode(GameMode.STANDARD)

    def switch_mode(self, mode: GameMode) -> None:
        if self.running:
            return
        if self.mode is mode:
            self.status.set(f"Już grasz w trybie {mode.title}. Naciśnij START, aby spróbować ponownie.")
            return
        campaign = Campaign(seed=self.seed, mode=mode)
        self.mode = mode
        self.campaign = campaign
        self.commands.clear()
        self.reset_robot()
        self.update_round_title()
        self.set_running(False)
        self.draw_program()
        self.status.set(f"Tryb {mode.title}! Nowa przygoda zaczyna się od poziomu 1.")
        self.heading.set(f"MISJA: ZAPROGRAMUJ ROBOTA!  •  {mode.title}")
        self.root.title(f"Misja: zaprogramuj robota! — {mode.title}")

    def handle_key(self, keysym: str) -> None:
        for move, key in ((Move.UP, "Up"), (Move.DOWN, "Down"),
                          (Move.LEFT, "Left"), (Move.RIGHT, "Right")):
            if keysym == key:
                self.add(move)
                return
        action = {"s": self.start, "n": self.next_round,
                  "u": self.undo, "r": self.clear, "t": self.start_turbo,
                  "l": self.start_ultra, "p": self.start_standard,
                  "e": self.correct_program}.get(keysym.casefold())
        if action:
            action()

    def next_round(self) -> None:
        if self.running:
            return
        if not self.campaign.solved:
            self.status.set("Najpierw zdobądź skarb. Wtedy odblokuje się kolejna runda!")
            return
        self.campaign.next_round()
        self.commands.clear()
        self.reset_robot()
        self.draw_program()
        self.update_round_title()
        self.set_running(False)
        self.status.set("Nowa mapa i nowy skarb! Ułóż strzałki i naciśnij START.")

    def button(self, parent: tk.Widget, text: str, command, color: str,
               font_size: int = 15) -> tk.Button:
        button = tk.Button(parent, text=text, command=command, bg=color, fg=NAVY,
                           activebackground=WHITE, font=("Arial", font_size, "bold"),
                           relief="flat", padx=10, pady=7, cursor="hand2",
                           disabledforeground="#666666")
        self.controls.append(button)
        return button

    def toggle_fullscreen(self, event=None) -> None:
        self.root.attributes("-fullscreen", not self.root.attributes("-fullscreen"))

    def add(self, move: Move) -> None:
        if self.running:
            return
        if len(self.commands) >= self.mode.max_commands:
            self.status.set(
                f"Limit {self.mode.max_commands} kroków. Cofnij strzałkę, aby zmienić program."
            )
            return
        self.commands.append(move)
        self.reset_robot()
        self.status.set("Co robot zrobi najpierw? Przewidźmy jego drogę!")
        self.draw_program()

    def undo(self) -> None:
        if self.running:
            return
        if not self.commands:
            self.status.set("Nie ma jeszcze strzałek do cofnięcia.")
            return
        self.commands.pop()
        self.reset_robot()
        self.status.set("Ostatnia strzałka cofnięta. Możesz ją zastąpić.")
        self.draw_program()

    def clear(self) -> None:
        if self.running:
            return
        self.commands.clear()
        self.reset_robot()
        self.status.set("Nowy pomysł! Ułóż program od początku.")
        self.draw_program()

    def hint(self) -> None:
        beginning = self.campaign.puzzle.solution[:2]
        messagebox.showinfo(
            "Podpowiedź, nie gotowy program",
            f"Początek jednej z dróg: {'  '.join(ARROWS[move] for move in beginning)}\n"
            + ("Jak ominąć kamienie i dotrzeć do skarbu?"
               if self.mode is not GameMode.ULTRA
               else "Idź jasnymi polami. Jak ominąć ściany i dotrzeć do skarbu?"),
            parent=self.root,
        )

    def reset_robot(self) -> None:
        self.result = None
        self.result_point = None
        self.position = self.board.start
        self.trail = [self.board.start]
        self.active_index = None
        self.draw_board()

    def set_running(self, running: bool) -> None:
        self.running = running
        for control in self.controls:
            control.configure(state="disabled" if running else "normal")
        self.next_button.configure(
            state="normal" if self.campaign.solved and not running else "disabled",
        )
        self.turbo_button.configure(
            text="Standard (P)" if self.mode is GameMode.TURBO else "Turbo teraz (T)",
            command=self.start_standard if self.mode is GameMode.TURBO else self.start_turbo,
        )
        self.ultra_button.configure(
            text="Standard (P)" if self.mode is GameMode.ULTRA else "Ultra teraz (L)",
            command=self.start_standard if self.mode is GameMode.ULTRA else self.start_ultra,
        )

    def start(self) -> None:
        if self.running:
            return
        if not self.commands:
            self.status.set("Najpierw dodaj strzałki. Robot potrzebuje instrukcji!")
            return
        self.reset_robot()
        self.set_running(True)
        self.execute(0)

    def execute(self, index: int) -> None:
        self.timer = None
        if index == len(self.commands):
            self.active_index = None
            self.set_running(False)
            if self.position == self.board.treasure:
                self.campaign.record_win()
                self.update_round_title()
                self.set_running(False)
                next_hint = ("nowa mapa i trudniejszy plan" if self.campaign.puzzle.level < MAX_LEVEL
                             else "nowa mapa na poziomie mistrzowskim")
                self.status.set(f"SKARB ZDOBYTY! Kolejna runda: {next_hint}!")
                self.result = "success"
                self.result_detail = "Świetny plan! Czeka na Ciebie nowa mapa."
            else:
                self.status.set("Program się skończył. Skarb jeszcze czeka. Poprawmy strzałki!")
                self.result = "missed"
                self.result_detail = "Robot skończył tutaj. Dodaj lub zmień strzałki."
            self.result_point = self.position
            self.draw_board()
            self.draw_program()
            return
        self.active_index = index
        move = self.commands[index]
        step = advance(self.board, self.position, move)
        self.draw_program()
        if step.error:
            self.set_running(False)
            error = step.error
            if self.mode is GameMode.ULTRA:
                error = error.replace("Kamień na drodze!", "Ściana labiryntu!")
            self.status.set(f"Krok {index + 1}: {error}")
            self.result = "collision"
            self.result_detail = f"Krok {index + 1}: {error.split('!')[0]}! Zmień tę strzałkę."
            dx, dy = move.delta
            self.result_point = (self.position[0] + dx, self.position[1] + dy)
            self.draw_board()
            return
        self.position = step.position
        self.trail.append(self.position)
        self.draw_board()
        self.status.set(f"Krok {index + 1}: {move.label}. Co będzie dalej?")
        delay = {GameMode.STANDARD: 750, GameMode.TURBO: 500, GameMode.ULTRA: 250}[self.mode]
        self.timer = self.root.after(delay, lambda: self.execute(index + 1))

    def draw_program(self) -> None:
        for child in self.program_frame.winfo_children():
            child.destroy()
        self.program_title.set(
            f"TWÓJ PROGRAM  •  {len(self.commands)}/{self.mode.max_commands} kroków"
            "  •  czytaj od lewej →"
        )
        if not self.commands:
            tk.Label(self.program_frame, text="↑  →  ↓  ←   Tu pojawi się Twój plan!",
                     font=("Arial", 15), fg=WHITE, bg=PANEL, padx=18, pady=5).grid()
            return
        compact = (
            self.mode is GameMode.STANDARD
            and len(self.commands) > 6
            and self.root.winfo_width() < 950
        )
        columns = 12 if compact else self.mode.program_columns
        if self.mode is GameMode.ULTRA and self.root.winfo_width() >= 950:
            columns = 16
        font_size = 16 if self.mode is not GameMode.STANDARD else 16 if compact else 20
        for index, move in enumerate(self.commands):
            color = YELLOW if index == self.active_index else PANEL
            fg = NAVY if index == self.active_index else WHITE
            if self.mode is GameMode.STANDARD:
                card = tk.Label(self.program_frame, text=f"{index + 1}\n{ARROWS[move]}",
                                font=("Arial", font_size, "bold"), width=4,
                                fg=fg, bg=color, relief="solid", borderwidth=1)
            else:
                card = tk.Canvas(self.program_frame, width=44, height=44, bg=color,
                                 highlightthickness=0)
                card.create_text(7, 8, text=str(index + 1), anchor="w",
                                 font=("Arial", 9, "bold"), fill=fg)
                card.create_text(25, 28, text=ARROWS[move],
                                 font=("Arial", 23, "bold"), fill=fg)
            card.grid(row=index // columns, column=index % columns, padx=3, pady=2)

    def draw_board(self) -> None:
        canvas = self.canvas
        canvas.delete("all")
        canvas.configure(cursor="")
        size = min((max(canvas.winfo_width(), 1) - 20) / self.board.width,
                   (max(canvas.winfo_height(), 1) - 20) / self.board.height)
        if size <= 0:
            return
        left = (canvas.winfo_width() - size * self.board.width) / 2
        top = (canvas.winfo_height() - size * self.board.height) / 2
        for y in range(self.board.height):
            for x in range(self.board.width):
                x0, y0 = left + x * size, top + y * size
                center_x, center_y = x0 + size / 2, y0 + size / 2
                point = (x, y)
                blocked = point in self.board.obstacles
                color = WALL if blocked else TRAIL if point in self.trail else PATH
                gap = 1 if self.mode is not GameMode.STANDARD else 2
                canvas.create_rectangle(x0 + gap, y0 + gap,
                                        x0 + size - gap, y0 + size - gap,
                                        fill=color, outline=NAVY if blocked else "#BECEDC",
                                        tags=("wall" if blocked else "path",))
                if (x, y) in self.board.obstacles:
                    if self.mode is not GameMode.ULTRA:
                        canvas.create_polygon(
                            center_x - size * .3, center_y + size * .2,
                            center_x - size * .24, center_y - size * .18,
                            center_x + size * .05, center_y - size * .3,
                            center_x + size * .3, center_y,
                            center_x + size * .22, center_y + size * .23,
                            fill="#94A7BC", outline=NAVY, width=2,
                            tags=("obstacle",),
                        )
                    else:
                        canvas.create_line(x0 + 2, center_y, x0 + size - 2, center_y,
                                           fill="#71849A", tags=("obstacle",))
                elif (x, y) == self.board.treasure:
                    self.draw_treasure(x0, y0, size)
                if point == self.board.start:
                    canvas.create_rectangle(x0 + 2, y0 + 2, x0 + size - 2, y0 + size - 2,
                                            outline="#117C76", width=3, tags=("start",))
                if (x, y) == self.position:
                    canvas.create_line(center_x, y0 + size * .12,
                                       center_x, y0 + size * .23,
                                       fill=NAVY, width=2, tags=("robot",))
                    canvas.create_oval(center_x - size * .045, y0 + size * .08,
                                       center_x + size * .045, y0 + size * .17,
                                       fill=CORAL, outline="", tags=("robot",))
                    canvas.create_rectangle(x0 + size * .2, y0 + size * .23,
                                            x0 + size * .8, y0 + size * .78,
                                            fill=CYAN, outline="#117C76",
                                            width=2, tags=("robot",))
                    for eye_x in (.36, .64):
                        canvas.create_oval(x0 + size * (eye_x - .055), y0 + size * .36,
                                           x0 + size * (eye_x + .055), y0 + size * .47,
                                           fill=NAVY, outline="")
                    canvas.create_line(x0 + size * .37, y0 + size * .63,
                                       x0 + size * .63, y0 + size * .63,
                                       fill=NAVY, width=3)
                if point == self.board.start:
                    canvas.create_text(
                        center_x if size >= 45 or point != self.position else x0 + 2,
                        y0 + size - 2,
                        anchor="s" if size >= 45 or point != self.position else "sw",
                        text="START" if size >= 45 else "S",
                        font=("Arial", max(8, min(12, int(size * .13))), "bold"),
                        fill=NAVY, tags=("start", "start-label"),
                    )
        if self.result:
            self.draw_result(left, top, size)

    def result_action(self, event=None) -> None:
        if self.running:
            return
        if self.result == "success":
            self.next_round()
        else:
            self.correct_program()

    def correct_program(self) -> None:
        if not self.running and self.result in ("collision", "missed"):
            self.reset_robot()
            self.draw_program()
            self.status.set("Popraw strzałki: U cofa, strzałki dodają krok. Potem START (S)!")

    def draw_treasure(self, x: float, y: float, size: float) -> None:
        canvas = self.canvas
        outline = max(1, min(2, size * .025))

        def polygon(points, fill, tag):
            coordinates = [coordinate for px, py in points
                           for coordinate in (x + px * size, y + py * size)]
            canvas.create_polygon(*coordinates, fill=fill, outline="#80500B",
                                  width=outline, tags=("treasure", tag))

        canvas.create_oval(x + .04 * size, y + .04 * size,
                           x + .96 * size, y + .96 * size,
                           fill="#FFF1A8", outline="", tags=("treasure", "treasure-glow"))
        # Raised lid behind the gold; all coordinates scale with the maze cell.
        polygon(((.17, .43), (.13, .18), (.75, .1), (.82, .36)),
                "#9A512B", "treasure-lid")
        polygon(((.23, .35), (.21, .22), (.69, .17), (.74, .3)),
                "#FFD369", "treasure-lid-band")
        polygon(((.13, .51), (.28, .4), (.85, .45), (.76, .65)),
                "#583325", "treasure-inside")
        for offset in (0, .24):
            polygon(((.25 + offset, .49), (.31 + offset, .34),
                     (.47 + offset, .34), (.51 + offset, .49)),
                    "#FFD34D", "treasure-gold")
            polygon(((.31 + offset, .34), (.35 + offset, .3),
                     (.49 + offset, .3), (.47 + offset, .34)),
                    "#FFF4AB", "treasure-gold")
        polygon(((.63, .37), (.69, .26), (.8, .28), (.85, .38), (.73, .55)),
                "#56E2F4", "treasure-diamond")
        canvas.create_line(x + .69 * size, y + .26 * size,
                           x + .73 * size, y + .55 * size,
                           fill="#E7FFFF", width=outline,
                           tags=("treasure", "treasure-diamond"))
        polygon(((.13, .51), (.76, .58), (.76, .87), (.13, .78)),
                "#B76B32", "treasure-front")
        polygon(((.76, .58), (.85, .45), (.85, .74), (.76, .87)),
                "#784222", "treasure-side")
        for offset in (.24, .61):
            polygon(((offset, .52), (offset + .065, .53),
                     (offset + .065, .81), (offset, .8)),
                    "#FFD34D", "treasure-band")
        polygon(((.44, .64), (.55, .65), (.55, .76), (.44, .75)),
                "#FFF4AB", "treasure-lock")
        for px, py in ((.89, .16), (.08, .37)):
            canvas.create_line(x + (px - .045) * size, y + py * size,
                               x + (px + .045) * size, y + py * size,
                               fill="#BA740A", width=outline, tags=("treasure", "treasure-sparkle"))
            canvas.create_line(x + px * size, y + (py - .045) * size,
                               x + px * size, y + (py + .045) * size,
                               fill="#BA740A", width=outline, tags=("treasure", "treasure-sparkle"))

    def draw_result(self, left: float, top: float, size: float) -> None:
        canvas = self.canvas
        success = self.result == "success"
        accent = YELLOW if success else CORAL
        point_x, point_y = self.result_point
        # A border collision is marked on the edge, not outside the visible canvas.
        marker_x = left + (min(max(point_x, 0), self.board.width - 1) + .5) * size
        marker_y = top + (min(max(point_y, 0), self.board.height - 1) + .5) * size
        radius = max(9, size * .43)
        canvas.create_oval(marker_x - radius, marker_y - radius,
                           marker_x + radius, marker_y + radius,
                           outline=accent, width=4, tags=("result-marker",))
        if not success:
            canvas.create_text(marker_x, marker_y, text="!", fill=NAVY,
                               font=("Arial", max(12, int(size * .4)), "bold"),
                               tags=("result-marker",))
        width, height = canvas.winfo_width(), canvas.winfo_height()
        card_width = min(480, width - 20)
        card_height = min(146, height - 20)
        x0 = (width - card_width) / 2
        y0 = 8 if marker_y > height / 2 else height - card_height - 8
        center = width / 2
        canvas.create_rectangle(x0, y0, x0 + card_width, y0 + card_height,
                                fill=NAVY, outline=accent, width=3, tags=("result-card",))
        title = {"success": "SKARB ZDOBYTY!",
                 "collision": "STOP! Przeszkoda!",
                 "missed": "Skarb jeszcze czeka!"}[self.result]
        canvas.create_text(center, y0 + 25, text=title, fill=accent,
                           font=("Arial", 21, "bold"), tags=("result-card", "result-title"))
        canvas.create_text(center, y0 + 65, text=self.result_detail, width=card_width - 28,
                           fill=WHITE, font=("Arial", 12),
                           tags=("result-card", "result-detail"))
        button_y = y0 + card_height - 27
        canvas.create_rectangle(x0 + 25, button_y - 18,
                                x0 + card_width - 25, button_y + 18,
                                fill=accent, outline="", tags=("result-card", "result-action"))
        canvas.create_text(center, button_y,
                           text="Kolejna runda (N)" if success else "Popraw strzałki (E)",
                           fill=NAVY, font=("Arial", 13, "bold"),
                           tags=("result-card", "result-action"))
        if success:
            for offset, color in ((-180, CYAN), (-150, CORAL), (150, CYAN), (180, CORAL)):
                if abs(offset) < card_width / 2 - 10:
                    canvas.create_text(center + offset, y0 + 24, text="★", fill=color,
                                       font=("Arial", 16, "bold"), tags=("result-card",))

    def close(self) -> None:
        if self.timer is not None:
            self.root.after_cancel(self.timer)
            self.timer = None
        self.root.destroy()
