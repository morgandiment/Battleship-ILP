# Battleship Solitaire ILP Solver

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)
![Gurobi](https://img.shields.io/badge/Gurobi-10.0%2B-red?logo=gurobi)
![CustomTkinter](https://img.shields.io/badge/GUI-CustomTkinter-green)

A robust, Python-based optimization framework for solving the NP-Complete **Battleship Solitaire** puzzle using Integer Linear Programming (ILP). 

This project evaluates the computational efficiency of two distinct mathematical paradigms: a dense-matrix **Cell Model** utilizing Big-M transition logic, and a highly scalable, sparse-matrix **Ship Model** utilizing candidate generation and Edge-Based Set Packing.

---

## Features

* **Dual Solver Architecture:** Dynamically switch between the Cell-based and Ship-based ILP formulations.
* **CSPLib Parser:** Natively ingests standard Prolog strings from the [Constraint Satisfaction Problem Library](https://www.csplib.org/Problems/prob014/).
* **Procedural Puzzle Generator:** Generates mathematically valid, zero-hint puzzles scaling up to macroscopic $30 \times 30$ grids for stress-testing.
* **Interactive GUI:** A decoupled, thread-safe `CustomTkinter` interface for real-time visualization and interactive puzzle construction.
* **Automated Evaluation Pipeline:** Headless `matplotlib` telemetry to benchmark algorithmic scalability, branch-and-bound node counts, and computational overhead.

---

## Prerequisites & License

This project relies on the **Gurobi Optimizer** for mathematical processing. 

1. You must have a valid Gurobi license. Students and academics can obtain a free [Academic Named-User License](https://www.gurobi.com/academia/academic-program-and-licenses/).
2. Once registered, install the license on your machine using the `grbgetkey` command provided in your Gurobi dashboard.

---

## Installation

1. **Clone the repository:**

2. **Install Dependencies:**
```bash
    pip install -r requirements.txt
```

---

## Usage

### 1. Interactive GUI
Launch the visualizer to build, import, and solve puzzles in real-time. The GUI runs Gurobi on background threads to maintain responsiveness.
```bash
python gui.py
```

### 2. Automated Evaluation
Run the evaluator independently to bypass the GUI. Run with `-h` flag for help.
```bash
python evaluator.py
```
Example usage:
```bash
python evaluator.py --solver ALL data/csplib.pl
```

### 3. Dataset Generation
Generate a static dataset or run with the `--dynamic` flag to generate a dynamic dataset.
```bash
python generator.py
```

## Project Structure
```text
Battleship-ILP/
├── src/                     # Core system modules
│   ├── __init__.py          # Package initializer
│   ├── board.py             # BattleshipPuzzle data structure & CSPLib parser
│   ├── cell_solver.py       # Dense-matrix Big-M ILP formulation
│   ├── ship_solver.py       # Sparse-matrix Set Packing ILP formulation
│   └── solver_utils.py      # Shared logic and grid formatting utilities
├── tests/                   # Automated unit tests
    ├── __init__.py          # Package initializer
│   ├── test_board.py         # Validation for parsing and data extraction
│   └── test_solver.py        # Correctness validation for both ILP models
├── data/                    # Benchmark datasets
│   ├── csplib.pl            # Original CSPLib Problem 014 standard dataset
│   └── scalable_puzzles.txt # Procedurally generated macroscopic scaling data
├── gui.py                   # CustomTkinter Interactive UI
├── evaluator.py             # Headless benchmark telemetry
├── generator.py             # Procedural puzzle generator
├── requirements.txt         # Python dependency list
└── README.md                # Project documentation
```