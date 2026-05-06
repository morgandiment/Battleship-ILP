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

    def test_orthogonal_touch_is_caught(self):
        """Two distinct ships placed orthogonally adjacent should fail validation.

        The validator's diagonal check has priority, so to isolate the
        orthogonal-touch path, a submarine is placed in the same row as the
        Cruiser's right end (2, 8). Cell (2, 9) is orthogonally adjacent to
        (2, 8) but has no diagonal neighbours that contain a ship segment.
        The flood-fill in _analyse_fleet then merges the Cruiser and the
        submarine into a single length-4 ship, which the fleet
        specification {4: 1, 3: 1} does not admit.
        """
        # Place a length-1 ship (submarine) immediately to the right of
        # the Cruiser's right end.
        self.board.grid[2, 9] = 1

        # Adjust tallies so the row/column sum check still passes,
        # forcing the validator to reach the fleet-composition check.
        self.board.puzzle.row_tallies[2] += 1
        self.board.puzzle.col_tallies[9] += 1

        is_valid, msg = self.board.is_valid_solution()

        # Cleanup so a subsequent test sees the clean board
        self.board.grid[2, 9] = 0
        self.board.puzzle.row_tallies[2] -= 1
        self.board.puzzle.col_tallies[9] -= 1

        self.assertFalse(is_valid, "Failed to catch orthogonal touch")
        self.assertIn("Fleet", msg, f"Expected fleet mismatch from merged ships, got: {msg}")

    def test_wrong_fleet_composition_is_caught(self):
        """A board satisfying tallies and geometry but with the wrong
        fleet composition should fail."""
        # Replace the Battleship (length 4) on row 0 with two length-2
        # ships: cells (0,0)-(0,1) and (0,3) on its own (sub).
        # Geometry remains valid; tallies and fleet do not.
        self.board.grid[0, 2] = 0  # split the battleship
        # Now we have a length-2 at (0,0)-(0,1) and a sub at (0,3),
        # with the cruiser still in place at (2,6)-(2,8).
        # Adjust tallies to keep row/col sums correct
        self.board.puzzle.row_tallies[0] -= 1
        self.board.puzzle.col_tallies[2] -= 1

        is_valid, msg = self.board.is_valid_solution()

        # Cleanup
        self.board.grid[0, 2] = 4
        self.board.puzzle.row_tallies[0] += 1
        self.board.puzzle.col_tallies[2] += 1

        self.assertFalse(is_valid, "Failed to catch fleet mismatch")
        self.assertIn("Fleet", msg, f"Expected 'Fleet' in error: {msg}")


if __name__ == "__main__":
    unittest.main()
