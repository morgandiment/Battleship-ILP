import unittest
from src.solver_utils import generate_ship_candidates


class TestCandidateGenerator(unittest.TestCase):
    """Tests for the Ship Model's pre-processing candidate generator."""

    def test_unpruned_count_matches_expected(self):
        """A standard 10x10 fleet produces exactly 580 candidates without pruning."""
        fleet = {4: 1, 3: 2, 2: 3, 1: 4}
        candidates = generate_ship_candidates(10, fleet)
        self.assertEqual(
            len(candidates), 580, "Expected 580 candidates for the standard 10x10 fleet, " f"got {len(candidates)}."
        )

    def test_water_hint_prunes_overlapping_candidates(self):
        """A water hint forbids every candidate covering that cell."""
        fleet = {2: 1}
        # Without pruning, a length-2 ship has 180 candidates on a
        # 10x10 grid.
        full = generate_ship_candidates(10, fleet)
        pruned = generate_ship_candidates(10, fleet, hints={(0, 0): 0})
        with_zero = [c for c in full if (0, 0) in c["cells"]]
        self.assertEqual(
            len(full) - len(pruned), len(with_zero), "Water-hint pruning removed the wrong number of candidates."
        )

    def test_zero_tally_row_prunes_candidates_in_that_row(self):
        """A zero row tally forbids every candidate touching that row."""
        fleet = {2: 1}
        row_tallies = [0, 1, 1, 0, 0, 0, 0, 0, 0, 0]
        col_tallies = [1, 1, 0, 0, 0, 0, 0, 0, 0, 0]
        pruned = generate_ship_candidates(10, fleet, row_tallies=row_tallies, col_tallies=col_tallies)
        # No surviving candidate should touch row 0 (zero tally).
        for c in pruned:
            self.assertFalse(
                any(r == 0 for r, _ in c["cells"]),
                f"Candidate {c['id']} survives despite touching row 0 " f"(R_0 = 0): cells = {c['cells']}",
            )


if __name__ == "__main__":
    unittest.main()
