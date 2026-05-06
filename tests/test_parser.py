import unittest
from evaluator import parse_prolog_csplib, HINT_MAP


class TestParser(unittest.TestCase):
    """Tests for the CSPLib Prolog parser."""

    def setUp(self):
        self.puzzles = parse_prolog_csplib("data/csplibExample.txt")

    def test_parses_at_least_one_instance(self):
        """The example file must contain parseable instances."""
        self.assertGreater(len(self.puzzles), 0, "Parser returned zero puzzles from data/csplibExample.txt")

    def test_first_instance_has_correct_shape(self):
        """The first instance from csplibExample.txt is Problem 113.
        Verify a few of its known fields."""
        p = self.puzzles[0]
        self.assertEqual(p.id, 113)
        # Known tallies for problem(113):
        #   rows: [2,4,3,3,2,4,1,1,0,0]
        #   cols: [0,5,0,2,2,3,1,3,2,2]
        self.assertEqual(list(p.row_tallies), [2, 4, 3, 3, 2, 4, 1, 1, 0, 0])
        self.assertEqual(list(p.col_tallies), [0, 5, 0, 2, 2, 3, 1, 3, 2, 2])

    def test_hint_coordinates_zero_indexed(self):
        """CSPLib uses 1-indexed coordinates; the parser must convert
        to 0-indexed before populating BattleshipPuzzle.hints."""
        p = self.puzzles[0]
        # problem(113) declares hints c@[7,10] and w@[1,6].
        self.assertIn((6, 9), p.hints)
        self.assertIn((0, 5), p.hints)
        self.assertEqual(p.hints[(6, 9)], HINT_MAP["c"])  # submarine
        self.assertEqual(p.hints[(0, 5)], HINT_MAP["w"])  # water


if __name__ == "__main__":
    unittest.main()
