# Battleship Solitaire ILP Solver

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)
![Gurobi](https://img.shields.io/badge/Gurobi-10.0%2B-red?logo=gurobi)
![CustomTkinter](https://img.shields.io/badge/GUI-CustomTkinter-green)

A Python framework for solving the NP-Complete **Battleship Solitaire** puzzle using Integer Linear Programming (ILP). The system implements two competing ILP formulations, an Improved variant with four valid inequalities, an automated benchmark harness, and an interactive thread-safe GUI. It accompanies a final-year BSc dissertation (CM3203, Cardiff University). The full report is available in the [dissertation-report](https://github.com/morgandiment/dissertation-report) repository. 

---

## Background

Battleship Solitaire is the deterministic single-player variant of the popular two-player game. The decision problem is NP-Complete (Sevenster, 2004), making it a natural testbed for advanced combinatorial optimisation. The two ILP formulations implemented here follow the framework of Meuffels and den Hertog (2010), *Puzzle-Solving the Battleship Puzzle as an Integer Programming Problem*, INFORMS Transactions on Education 10(3), 156-162. This project provides a modern Python+Gurobi implementation of both formulations, evaluates them across grid sizes from 10x10 to 30x30, and quantifies a scale-dependent "Overhead vs. Pruning" trade-off in the use of valid inequalities.

---

## Architecture

The system is organised as four cooperating layers with thread-safe message passing between the optimisation back-end and the user interface front-end:

- **Data ingestion** (`src/board.py`, `evaluator.py:parse_prolog_csplib`): A regex pipeline parses standard CSPLib Prolog instances into a `BattleshipPuzzle` object. A custom procedural generator (`generator.py`) produces feasibility-guaranteed scaling instances.
- **Optimisation engine** (`src/cell_solver.py`, `src/ship_solver.py`): Two independently swappable Gurobi formulations sharing a `.solve(puzzle)` interface. The Cell Model uses 7-state cell variables with Big-M degree constraints. The Ship Model pre-enumerates valid placements and resolves conflicts via Edge-Based Set Packing.
- **Presentation layer** (`gui.py`): CustomTkinter front-end with a `TextboxRedirector` and `tkinter.after()` event loop to marshal background-solver output safely back to the UI thread.
- **Evaluation pipeline** (`evaluator.py`): Headless matplotlib batch runner that produces five comparison charts and a per-instance CSV per evaluation run.

---

## Prerequisites & License

This project relies on the **Gurobi Optimizer** for mathematical processing. 

1. You must have a valid Gurobi license. Students and academics can obtain a free [Academic Named-User License](https://www.gurobi.com/academia/academic-program-and-licenses/).
2. Once registered, install the license on your machine using the `grbgetkey` command provided in your Gurobi dashboard.

---

## Installation

**Clone the repository:**
```bash
git clone https://github.com/morgandiment/Battleship-ILP.git
cd Battleship-ILP
pip install -r requirements.txt
```

---

## Usage

### Interactive GUI
Launch the visualiser to build, import, and solve puzzles in real-time. The GUI runs Gurobi on background threads to maintain responsiveness.
```bash
python gui.py
```

### Automated Evaluation
Run the evaluator independently to bypass the GUI. Each invocation produces five plots and a per-instance CSV in `results/<timestamp>_<dataset>/`. Run with `-h` flag for help.
```bash
python evaluator.py data/csplib.pl --solver ALL
python evaluator.py data/scalable_puzzles.txt --solver ALL
```

The `--solver` flag accepts `CELL`, `CELL_IMPROVED`, `SHIP`, OR `ALL`.

### Dataset Generation
Generate a static fixed-fleet dataset, or run with the `--dynamic` flag to generate a dynamic-fleet dataset which samples 8 hint counts x 5 grid sizes x 5 instances = 200 reproducible puzzles.
```bash
python generator.py --dynamic
```

### Code Quality
This repository uses Black for formatting and Flake8 for linting, with pre-commit hooks. Run all checks with:
```bash
pre-commit install
pre-commit run --all-files
```

### Tests
Unit tests cover the validator and both solvers:
```bash
python tests/
```

## Project Structure
```text
Battleship-ILP/
├── src/                     # Core system modules
│   ├── board.py             # BattleshipPuzzle data structure & CSPLib parser
│   ├── cell_solver.py       # Dense-matrix Big-M ILP formulation
│   ├── ship_solver.py       # Sparse-matrix Set Packing ILP formulation
│   └── solver_utils.py      # Shared logic and grid formatting utilities
├── tests/                   # Automated unit tests
│   ├── test_board.py         # Validation for parsing and data extraction
│   └── test_solver.py        # Correctness validation for both ILP models
├── data/                    # Benchmark datasets
│   ├── csplib.pl            # Original CSPLib Problem 014 standard dataset
│   └── scalable_puzzles.txt # Procedurally generated macroscopic scaling data
├── gui.py                   # CustomTkinter Interactive UI
├── evaluator.py             # Headless benchmark and plot pipeline
├── generator.py             # Procedural puzzle generator
└── requirements.txt         # Python dependency list
```

---
## Author
Created by Morgan Diment for the CM3203 Individual Project module at Cardiff University, supervised by Jandson Santos Ribeiro Santos.