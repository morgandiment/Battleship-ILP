import unittest
from src.board import BattleshipPuzzle, BattleshipBoard, WATER


class TestBoard(unittest.TestCase):
    def setUp(self):
        """Create a valid board for each test."""
        row_tallies = [4, 0, 3, 0, 0, 0, 0, 0, 0, 0]
        col_tallies = [1, 1, 1, 1, 0, 0, 1, 1, 1, 0]

        puzzle = BattleshipPuzzle(row_tallies, col_tallies)
        custom_fleet = {4: 1, 3: 1}
        puzzle.fleet_spec = custom_fleet

        self.board = BattleshipBoard(puzzle)

        # Place ships (Simulating a Solver)
        # Battleship at (0,0) to (0,3)
        self.board.grid[0, 0] = 4
        self.board.grid[0, 1] = 4
        self.board.grid[0, 2] = 4
        self.board.grid[0, 3] = 4

        # Cruiser at (2,6) to (2,8)
        self.board.grid[2, 6] = 3
        self.board.grid[2, 7] = 3
        self.board.grid[2, 8] = 3

        # Set everything else to WATER (0)
        for r in range(10):
            for c in range(10):
                if self.board.grid[r, c] == -1:
                    self.board.grid[r, c] = WATER

    def test_valid_board(self):
        """Test that a valid board is accepted."""
        is_valid, msg = self.board.is_valid_solution()
        self.assertTrue(is_valid, f"Valid board rejected. Reason: {msg}")

    def test_invalid_geometry(self):
        """Test that diagonal touches are caught."""
        # Add a '1' (Submarine) at (1,4) - touches Battleship at (0,3) diagonally
        self.board.grid[1, 4] = 1

        # Update tally numbers to pass checks
        self.board.puzzle.row_tallies[1] += 1
        self.board.puzzle.col_tallies[4] += 1

        is_valid, msg = self.board.is_valid_solution()

        # Cleanup
        self.board.grid[1, 4] = 0
        self.board.puzzle.row_tallies[1] -= 1
        self.board.puzzle.col_tallies[4] -= 1

        self.assertFalse(is_valid, "Failed to catch diagonal touch")
        self.assertIn("Diagonal", msg, f"Expected 'Diagonal' in error message, got: {msg}")

    def test_invalid_tally(self):
        """Test that incorrect tallies are caught."""
        # Add a random ship segment that ruins the row count
        self.board.grid[9, 9] = 1

        is_valid, msg = self.board.is_valid_solution()

        self.assertFalse(is_valid, "Failed to catch tally error")
        self.assertIn("Tally", msg, f"Expected 'Tally' in error message, got: {msg}")


if __name__ == "__main__":
    unittest.main()
