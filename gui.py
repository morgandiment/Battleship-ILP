import customtkinter as ctk
from tkinter import filedialog
import threading
import time
import sys
import os
import re

from evaluator import run_evaluation, HINT_MAP
from src.ship_solver import ShipModelSolver
from src.cell_solver import CellModelSolver
from src.board import BattleshipPuzzle

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")


class TextboxRedirector:
    def __init__(self, textbox):
        self.textbox = textbox

    def write(self, text):
        self.textbox.after(0, self._insert_text, text)

    def _insert_text(self, text):
        self.textbox.insert("end", text)
        self.textbox.see("end")

    def flush(self):
        pass


class BattleshipGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Battleship Solitaire Optimizer")
        self.geometry("900x750")

        self.tabview = ctk.CTkTabview(self, width=850, height=700)
        self.tabview.pack(padx=20, pady=20, expand=True, fill="both")

        self.tab_batch = self.tabview.add("Batch Evaluation")
        self.tab_single = self.tabview.add("Single Puzzle Solver")

        self.setup_batch_tab()
        self.setup_single_tab()

    # Batch Evaluation Tab
    def setup_batch_tab(self):
        control_frame = ctk.CTkFrame(self.tab_batch)
        control_frame.pack(pady=10, padx=20, fill="x")

        # Fixing width to keep buttons on screen
        self.file_label = ctk.CTkLabel(control_frame, text="No dataset loaded.", width=250, anchor="w")
        self.file_label.pack(side="left", padx=10)

        load_btn = ctk.CTkButton(control_frame, text="Load .pl Dataset", command=self.load_file)
        load_btn.pack(side="left", padx=10)

        self.solver_var = ctk.StringVar(value="ALL")
        solver_menu = ctk.CTkOptionMenu(
            control_frame,
            variable=self.solver_var,
            values=["ALL", "SHIP", "CELL", "CELL_IMPROVED"],
        )
        solver_menu.pack(side="left", padx=10)

        run_btn = ctk.CTkButton(
            control_frame,
            text="Run Evaluation",
            fg_color="green",
            hover_color="darkgreen",
            command=self.run_evaluation,
        )
        run_btn.pack(side="right", padx=10)

        self.console_output = ctk.CTkTextbox(self.tab_batch, wrap="none", font=("Courier", 12))
        self.console_output.pack(pady=10, padx=20, expand=True, fill="both")
        self.console_output.insert("end", "System Ready...\nSelect a dataset and press Run Evaluation.\n")

    def load_file(self):
        filepath = filedialog.askopenfilename(filetypes=[("Prolog Files", "*.pl"), ("Text Files", "*.txt")])
        if filepath:
            self.loaded_filepath = filepath  # Saving the real path
            filename = os.path.basename(filepath)  # Only show the short path
            self.file_label.configure(text=f"Loaded: {filename}")
            self.console_output.insert("end", f"\nLoaded File: {filepath}\n")

    def run_evaluation(self):
        if not hasattr(self, "loaded_filepath"):
            self.console_output.insert("end", "\n[ERROR] Please load a dataset file first!\n")
            return

        filepath = self.loaded_filepath
        solver_choice = self.solver_var.get()
        self.console_output.insert("end", f"\n--- Starting {solver_choice} Evaluation ---\n")

        def thread_target():
            old_stdout = sys.stdout
            sys.stdout = TextboxRedirector(self.console_output)
            try:
                run_evaluation(filepath, solver_choice)
            except Exception as e:
                print(f"\n[CRITICAL ERROR]: {e}")
            finally:
                sys.stdout = old_stdout
                self.console_output.insert("end", "\n--- Evaluation Complete ---\n")

        threading.Thread(target=thread_target, daemon=True).start()

    # Single Puzzle Solver Tab
    def setup_single_tab(self):
        control_frame = ctk.CTkFrame(self.tab_single)
        control_frame.pack(pady=10, padx=10, fill="x")

        self.fleet_input = ctk.CTkEntry(control_frame, placeholder_text="Fleet", width=120)
        self.fleet_input.pack(side="left", padx=5)
        self.fleet_input.insert(0, "4:1,3:2,2:3,1:4")

        self.puzzle_input = ctk.CTkEntry(
            control_frame,
            placeholder_text="Paste CSPLib string OR draw on grid",
            width=450,
        )
        self.puzzle_input.pack(side="left", padx=5)

        self.single_solver_var = ctk.StringVar(value="SHIP")
        single_solver_menu = ctk.CTkOptionMenu(
            control_frame,
            variable=self.single_solver_var,
            values=["SHIP", "CELL", "CELL_IMPROVED"],
            width=95,
        )
        single_solver_menu.pack(side="right", padx=5)

        solve_btn = ctk.CTkButton(control_frame, text="Solve", command=self.solve_single)
        solve_btn.pack(side="right", padx=10)

        self.status_label = ctk.CTkLabel(
            self.tab_single,
            text="Click cells to change hints. Type tallies in the edges.",
            text_color="gray",
            font=("Arial", 14),
        )
        self.status_label.pack(pady=5)

        self.grid_frame = ctk.CTkFrame(self.tab_single)
        self.grid_frame.pack(pady=5, expand=True)

        self.cells = {}
        self.row_entries = {}
        self.col_entries = {}

        # Cell state options
        self.cell_modes = ["", "w", "c", "l", "r", "t", "b", "m"]
        self.cell_mode_idx = {(r, c): 0 for r in range(10) for c in range(10)}

        grid_size = 10
        for r in range(grid_size + 1):
            for c in range(grid_size + 1):
                if r == 0 and c == 0:
                    continue
                elif r == 0:
                    # Column Tally Inputs
                    entry = ctk.CTkEntry(
                        self.grid_frame,
                        width=35,
                        height=35,
                        font=("Arial", 14),
                        justify="center",
                    )
                    entry.insert(0, "0")
                    entry.grid(row=r, column=c, padx=2, pady=2)
                    self.col_entries[c - 1] = entry
                elif c == 0:
                    # Row Tally Inputs
                    entry = ctk.CTkEntry(
                        self.grid_frame,
                        width=35,
                        height=35,
                        font=("Arial", 14),
                        justify="center",
                    )
                    entry.insert(0, "0")
                    entry.grid(row=r, column=c, padx=2, pady=2)
                    self.row_entries[r - 1] = entry
                else:
                    # Clickable Grid Cells
                    btn = ctk.CTkButton(
                        self.grid_frame,
                        text="",
                        width=35,
                        height=35,
                        corner_radius=2,
                        fg_color="#1f538d",
                        border_width=1,
                        border_color="#14375e",
                        command=lambda rr=r - 1, cc=c - 1: self.on_cell_click(rr, cc),
                    )
                    btn.grid(row=r, column=c, padx=1, pady=1)
                    self.cells[(r - 1, c - 1)] = btn

        self.clear_btn = ctk.CTkButton(
            self.tab_single,
            text="Clear Board",
            fg_color="#8b0000",
            hover_color="#5c0000",
            command=self.clear_single,
        )
        self.clear_btn.pack(pady=10)

    def on_cell_click(self, r, c):
        # Clear the input string because the user is modifying the board manually
        self.puzzle_input.delete(0, "end")

        # Cycle to the next mode
        idx = (self.cell_mode_idx[(r, c)] + 1) % len(self.cell_modes)
        self.cell_mode_idx[(r, c)] = idx
        mode = self.cell_modes[idx]

        btn = self.cells[(r, c)]
        if mode == "":
            btn.configure(text="", fg_color="#1f538d")
        elif mode == "w":
            btn.configure(text="~", fg_color="#0a1d33", text_color="cyan")
        else:
            btn.configure(text=mode.upper(), fg_color="#2b2b2b", text_color="white")

    def build_string_from_grid(self):
        """Converts the current UI state into a CSPLib string."""
        fleet_str = self.fleet_input.get().strip()
        try:
            row_t = [int(self.row_entries[r].get() or 0) for r in range(10)]
            col_t = [int(self.col_entries[c].get() or 0) for c in range(10)]
        except ValueError:
            self.status_label.configure(text="Tallies must be valid integers!", text_color="red")
            return None

        hints = []
        for r in range(10):
            for c in range(10):
                mode = self.cell_mode_idx[(r, c)]
                if mode > 0:
                    char = self.cell_modes[mode]
                    hints.append(f"{char}@[{r+1},{c+1}]")

        row_str = ",".join(map(str, row_t))
        col_str = ",".join(map(str, col_t))
        hint_str = ",".join(hints)
        prob_str = f"problem(999, [{fleet_str}], [{row_str}], [{col_str}], " f"[{hint_str}])."
        return prob_str

    def parse_single_string(self, content):
        pattern = re.compile(
            r"problem\s*\(\s*(\d+)\s*,\s*\[(.*?)\]\s*,\s*\[(.*?)\]\s*,\s*" r"\[(.*?)\]\s*,\s*\[(.*?)\]\s*\)\.",
            re.DOTALL,
        )
        match = pattern.search(content)
        if not match:
            return None

        fleet_spec = {
            int(ship_length): int(count)
            for ship_length, count in [item.split(":") for item in match.group(2).split(",") if item]
        }
        row_tallies = [int(x) for x in match.group(3).split(",") if x.strip()]
        col_tallies = [int(x) for x in match.group(4).split(",") if x.strip()]

        hints = {}
        hint_items = re.findall(r"([wcmlrtb])@\[\s*(\d+)\s*,\s*(\d+)\s*\]", match.group(5))
        for h_type, r_str, c_str in hint_items:
            hints[(int(r_str) - 1, int(c_str) - 1)] = HINT_MAP[h_type]

        puzzle = BattleshipPuzzle(row_tallies, col_tallies, hints)
        puzzle.fleet_spec = fleet_spec
        return puzzle

    def clear_single(self):
        """Resets the board to a blank state."""
        # Clear text inputs
        self.puzzle_input.delete(0, "end")
        self.fleet_input.delete(0, "end")
        self.fleet_input.insert(0, "4:1,3:2,2:3,1:4")  # Default 10x10 fleet

        # Reset tallies to 0
        for r in range(10):
            if r in self.row_entries:
                self.row_entries[r].delete(0, "end")
                self.row_entries[r].insert(0, "0")
            if r in self.col_entries:
                self.col_entries[r].delete(0, "end")
                self.col_entries[r].insert(0, "0")

        # Paint the grid back to standard water
        for r in range(10):
            for c in range(10):
                self.cell_mode_idx[(r, c)] = 0
                self.cells[(r, c)].configure(text="", fg_color="#1f538d")

        self.status_label.configure(text="Board cleared. Ready for new puzzle.", text_color="gray")

    def solve_single(self):
        puzzle_string = self.puzzle_input.get().strip()

        # Check if the string box is empty
        if not puzzle_string:
            puzzle_string = self.build_string_from_grid()
            if not puzzle_string:
                return  # Error handled in builder
            self.puzzle_input.insert(0, puzzle_string)  # Show them the string built

        # Parse the string
        puzzle = self.parse_single_string(puzzle_string)
        if not puzzle:
            self.status_label.configure(text="Invalid CSPLib format. Check your syntax.", text_color="red")
            return

        # Update UI to match the parsed string
        self.fleet_input.delete(0, "end")
        self.fleet_input.insert(0, ",".join([f"{ship_length}:{count}" for ship_length, count in puzzle.fleet_spec.items()]))

        for r, tally in enumerate(puzzle.row_tallies):
            if r in self.row_entries:
                self.row_entries[r].delete(0, "end")
                self.row_entries[r].insert(0, str(tally))
        for c, tally in enumerate(puzzle.col_tallies):
            if c in self.col_entries:
                self.col_entries[c].delete(0, "end")
                self.col_entries[c].insert(0, str(tally))

        # Reset Grid and Apply Hints
        rev_map = {0: "w", 1: "c", 2: "m", 3: "l", 4: "r", 5: "t", 6: "b"}

        for r in range(10):
            for c in range(10):
                self.cell_mode_idx[(r, c)] = 0
                self.cells[(r, c)].configure(text="", fg_color="#1f538d")

        for (r, c), val in puzzle.hints.items():
            char = rev_map[val]
            self.cell_mode_idx[(r, c)] = self.cell_modes.index(char)
            if val == 0:
                self.cells[(r, c)].configure(text="~", fg_color="#0a1d33", text_color="cyan")
            else:
                self.cells[(r, c)].configure(text=char.upper(), fg_color="#2b2b2b", text_color="white")

        self.status_label.configure(text="Solving...", text_color="white")
        self.update()

        # Running solve
        solver_choice = self.single_solver_var.get()
        if solver_choice == "SHIP":
            solver = ShipModelSolver(verbose=False)
        elif solver_choice == "CELL_IMPROVED":
            solver = CellModelSolver(use_improv=True)
        else:
            solver = CellModelSolver(use_improv=False)

        # Start the timer
        start_time = time.time()
        solve_result = solver.solve(puzzle)
        elapsed_time = time.time() - start_time

        # Show result on the grid
        if solve_result:
            solution, nodes = solve_result

            # Handle ship model format
            if isinstance(solution, list) and len(solution) > 0 and isinstance(solution[0], dict):
                for cand in solution:
                    for r, c in cand["cells"]:
                        if (r, c) not in puzzle.hints:
                            self.cells[(r, c)].configure(text="", fg_color="#a8a8a8")

            # Handle cell model format
            elif isinstance(solution, list) and isinstance(solution[0], list):
                for r in range(len(solution)):
                    for c in range(len(solution[0])):
                        if solution[r][c] == 1 and (r, c) not in puzzle.hints:
                            self.cells[(r, c)].configure(text="", fg_color="#a8a8a8")

            self.status_label.configure(
                text=f"Solved successfully via {solver_choice} in {elapsed_time:.4f}s (Nodes Explored: {int(nodes)})",
                text_color="green",
            )
        else:
            self.status_label.configure(
                text=f"Puzzle is Infeasible! (Time: {elapsed_time:.4f}s)",
                text_color="red",
            )


if __name__ == "__main__":
    app = BattleshipGUI()
    app.mainloop()
