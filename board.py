import numpy as np

# Constants
UNKNOWN = -1
WATER = 0

class BattleshipPuzzle:
    def __init__(self, row_tallies, col_tallies, hints=None):
        self.row_tallies = np.array(row_tallies)
        self.col_tallies = np.array(col_tallies)
        # Hints are Dict {(row, col): val}
        # Can be 0 for water or 1-4 for ship type
        self.hints = hints if hints else {}
        # Fleet length (for 10x10) then count
        self.fleet_spec = {5: 1, 4: 1, 3: 2, 2: 3, 1: 4}