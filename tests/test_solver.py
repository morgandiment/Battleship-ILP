import unittest
from src.board import BattleshipPuzzle, BattleshipBoard
from src.ship_solver import ShipModelSolver
from src.cell_solver import CellModelSolver

WATER = 0
SUB = 1
MID = 2
LEFT = 3
RIGHT = 4
TOP = 5
BOTTOM = 6


class TestSolver(unittest.TestCase):
    def _run_solver_test(self, solver):
        """Helper method to test a solver."""
        # Full fleet tallies with hints
        row_tallies = [1, 4, 1, 2, 6, 2, 2, 2, 3, 2]
        col_tallies = [5, 1, 5, 1, 1, 5, 0, 2, 4, 1]
        my_hints = {(1, 1): LEFT, (2, 5): MID, (7, 3): SUB}

        puzzle = BattleshipPuzzle(row_tallies, col_tallies, hints=my_hints)

        # Run Solver
        result = solver.solve(puzzle)

        # Validate result
        self.assertIsNotNone(result, "Solver returned infeasible result")

        solution, nodes = result
        self.assertGreater(len(solution), 0, "Solver found no ships")

        # Load results into Board
        board = BattleshipBoard(puzzle)
        board.load_ship_model(solution)

        # Validate the board
        is_valid, msg = board.is_valid_solution()
        self.assertTrue(is_valid, f"Solver output is invalid: {msg}")

    def test_cell_model_solver(self):
        """Test that the Cell Model solver works correctly."""
        solver = CellModelSolver()
        self._run_solver_test(solver)

    def test_ship_model_solver(self):
        """Test that the Ship Model solver works correctly."""
        solver = ShipModelSolver()
        self._run_solver_test(solver)


if __name__ == "__main__":
    unittest.main()
