import numpy as np

# Constants
UNKNOWN = -1
WATER = 0

class BattleshipPuzzle:
    """
    Definition of the problem.
    """
    def __init__(self, row_tallies, col_tallies, hints=None):
        self.row_tallies = np.array(row_tallies)
        self.col_tallies = np.array(col_tallies)
        # Hints are Dict {(row, col): val}
        # Can be 0 for water or 1-4 for ship type
        self.hints = hints if hints else {}
        # Fleet length (for 10x10) then count
        self.fleet_spec = {5: 1, 4: 1, 3: 2, 2: 3, 1: 4}

class BattleshipBoard:
    """
    State of the grid.
    """
    def __init__(self, puzzle: BattleshipPuzzle, size=10):
        self.puzzle = puzzle
        self.size = size
        # Grid: 0=Water, 1-4=Ship (length), -1=Unknown
        self.grid = np.full((size, size), UNKNOWN, dtype=int)

        # Applying hints
        for (r, c), val in puzzle.hints.items():
            self.grid[r, c] = val

    # Model loaders

    def load_cell_model(self, s_vars, t_vars):
        """
        Loads solution from adapted Cell Model.
        
        :param s_vars: 10x10 matrix of 0/1
        :param t_vars: 10x10 matrix of 0-4
        """
        for r in range(self.size):
            for c in range(self.size):
                # If s=0 then Water, s=1 then take t value
                if s_vars[r][c] < 0.5:
                    self.grid[r][c] = WATER
                else:
                    self.grid[r][c] = int(round(t_vars[r][c]))

    def load_ship_model(self, active_ships):
        """
        Loads solution from Ship Model.
        
        :param active_ships: List of candidate dicts from solver_utils.
        """
        self.grid.fill(WATER)

        for ship in active_ships:
            length = ship['length']

            if 'cells' in ship:
                for r, c in ship['cells']:
                    self.grid[r, c] = length
            else:
                r, c = ship['row'], ship['col']
                is_vert = (ship['orientation'] == 'V')
                for k in range(length):
                    nr = r + k if is_vert else r
                    nc = c if is_vert else c + k
                    self.grid[nr, nc] = length

    # Validation

    def is_valid_solution(self):
        """
        Verifies fleet, geometry and tallies, independent of solver.
        """
        # Check tallies
        is_ship = (self.grid > 0).astype(int)

        if not np.array_equal(np.sum(is_ship, axis=1), self.puzzle.row_tallies):
            return False, "Row Tally Mismatch"
        if not np.array_equal(np.sum(is_ship, axis=0), self.puzzle.col_tallies):
            return False, "Column Tally Mismatch"

        # Check geometry
        for r in range(self.size - 1):
            for c in range(self.size - 1):
                # Diagonals
                if self.grid[r, c] > 0 and self.grid[r+1, c+1] > 0:
                    return False, f"Diagonal Touch at {r}, {c}"
                if self.grid[r, c+1] > 0 and self.grid[r+1, c] > 0:
                    return False, f"Diagonal Touch at {r}, {c+1}"
                
        # Check fleet
        found_ships = self._analyse_fleet()

        from collections import Counter
        counts = Counter(found_ships)

        if counts != self.puzzle.fleet_spec:
            return False, f"Fleet Mismatch. Found {dict(counts)} Expected: {self.puzzle.fleet_spec}"
        
        return True, "Valid Solution"
    
    def _analyse_fleet(self):
        """
        Uses flood fill to find ships and check if they are valid lines.
        Returns list of lengths of valid ships.
        """
        visited = np.zeros_like(self.grid, dtype=bool)
        ship_lengths = []

        for r in range(self.size):
            for c in range(self.size):
                if self.grid[r, c] > 0 and not visited[r, c]:
                    cells = self._flood_fill(r, c, visited)

                    if not self._is_straight_line(cells):
                        ship_lengths.append(0)
                    else:
                        ship_lengths.append(len(cells))

                    actual_len = len(cells)
                    for (sr, sc) in cells:
                        if self.grid[sr, sc] != actual_len:
                            print(f"Warning: Cell {sr}, {sc} says length {self.grid[sr, sc]} but is part of length {actual_len}")
        
        return ship_lengths
    

    def _flood_fill(self, r, c, visited):
        """Recusrive flood fill to find connected components."""
        stack = [(r, c)]
        visited[r, c] = True
        component = []

        while stack:
            curr_r, curr_c = stack.pop()
            component.append((curr_r, curr_c))

            for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nr, nc = curr_r + dr, curr_c + dc
                if 0 <= nr < self.size and 0 <= nc < self.size:
                    if self.grid[nr, nc] > 0 and not visited[nr, nc]:
                        visited[nr, nc] = True
                        stack.append((nr, nc))

        return component
    
    def _is_straight_line(self, cells):
        """Returns True if all cells are in one row or one column."""
        if not cells: return False
        rows = {r for r, c in cells}
        cols = {c for r, c in cells}
        return len(rows) == 1 or len(cols) == 1
    
    def display(self):
        print("   " + " ".join(str(i) for i in range(self.size)))
        print("  " + "-" * (self.size * 2))
        for r in range(self.size):
            row_char = []
            for val in self.grid[r]:
                if val == WATER: row_char.append('.')
                elif val == UNKNOWN: row_char.append('?')
                else: row_char.append(str(val))

            print(f"{r}| {' '.join(row_char)} | {self.puzzle.row_tallies[r]}")
        print("  " + "-" * (self.size * 2))
        print("   " + " ".join(str(c) for c in self.puzzle.col_tallies))
        # Need a renderer that checks for neighbours and draws the top/bottom/left/right of ships.