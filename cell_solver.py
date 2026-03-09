import gurobipy as gp
from gurobipy import GRB
import numpy as np

# Setting symbols
WATER = 0
SUB = 1
MID = 2
LEFT = 3
RIGHT = 4
TOP = 5
BOTTOM = 6

class CellModelSolver:
    """
    Implements Cell-Based Model from Meuffels' paper.
    """
    def __init__(self):
        self.env = gp.Env(empty=True)
        self.env.setParam("OutputFlag", 0)
        self.env.start()

    def solve(self, puzzle):
        """
        Solves using Meuffels' 7-variable constraints.
        Returns: list of candidate dicts.
        """
        rows = len(puzzle.row_tallies)
        cols = len(puzzle.col_tallies)

        model = gp.Model("BattleshipCell", env=self.env)

        # Variables
        x = model.addVars(rows, cols, 7, vtype=GRB.BINARY, name="x")

        # One state per cell
        model.addConstrs(
            (x.sum(r, c, '*') == 1 for r in range(rows) for c in range(cols)),
            name="UniqueState"
        )

        # Row/Col tally sum
        for r in range(rows):
            model.addConstr(
                gp.quicksum(x[r,c,k] for c in range(cols) for k in range(1, 7)) == puzzle.row_tallies[r],
                name=f"Row_{r}"
            )
        for c in range(cols):
            model.addConstr(
                gp.quicksum(x[r,c,k] for r in range(rows) for k in range(1,7)) == puzzle.col_tallies[c],
                name=f"Col_{c}"
            )
        
        # Fleet inventory
        total_ships_expected = sum(puzzle.fleet_spec.values())
        
        model.addConstr(
            x.sum('*', '*', SUB) + x.sum('*', '*', LEFT) + x.sum('*', '*', TOP) == total_ships_expected,
            name="TotalFleetCount"
        )

        if 1 in puzzle.fleet_spec:
            model.addConstr(x.sum('*', '*', SUB) == puzzle.fleet_spec[1], "Count_Subs")

        for length, expected_count in puzzle.fleet_spec.items():
            if length == 1: continue

            detectors = []

            # Horizontals
            for r in range(rows):
                for c in range(cols - length + 1):
                    var_name = f"is_H_len{length}_{r}_{c}"
                    is_ship = model.addVar(vtype=GRB.BINARY, name=var_name)
                    detectors.append(is_ship)

                    pieces = [x[r, c, LEFT]]
                    for k in range(1, length - 1):
                        pieces.append(x[r, c+k, MID])
                    pieces.append(x[r, c+length-1, RIGHT])

                    model.addConstr(is_ship <= x[r, c, LEFT])
                    model.addConstr(is_ship <= x[r, c+length-2, RIGHT])
                    for k in range(1, length-1):
                        model.addConstr(is_ship <= x[r, c+k, MID])

                    model.addConstr(is_ship >= gp.quicksum(pieces) - length + 1)

            # Verticals
            for c in range(cols):
                for r in range(rows - length + 1):
                    var_name = f"is_V_len{length}_{r}_{c}"
                    is_ship = model.addVar(vtype=GRB.BINARY, name=var_name)
                    detectors.append(is_ship)

                    pieces = [x[r, c, TOP]]
                    for k in range(1, length - 1):
                        pieces.append(x[r + k, c, MID])
                    pieces.append(x[r + length - 1, c, BOTTOM])

                    model.addConstr(is_ship <= x[r, c, TOP])
                    model.addConstr(is_ship <= x[r + length - 1, c, BOTTOM])
                    for k in range(1, length - 1):
                        model.addConstr(is_ship <= x[r + k, c, MID])

                    model.addConstr(is_ship >= gp.quicksum(pieces) - length + 1)

            # Exact count
            model.addConstr(gp.quicksum(detectors) == expected_count, name=f"Count_Len{length}")

        # Geometry
        for r in range(rows):
            for c in range(cols):
                # Left
                if c < cols - 1:
                    model.addConstr(x[r,c,LEFT] <= x[r,c+1,MID] + x[r,c+1,RIGHT])
                else:
                    model.addConstr(x[r,c,LEFT] == 0) # Not at edge

                # Right
                if c > 0:
                    model.addConstr(x[r,c,RIGHT] <= x[r,c-1,MID] + x[r,c-1,LEFT])
                else:
                    model.addConstr(x[r,c,RIGHT] == 0)

                # Top
                if r < rows - 1:
                    model.addConstr(x[r,c,TOP] <= x[r+1,c,MID] + x[r+1,c,BOTTOM])
                else:
                    model.addConstr(x[r,c,TOP] == 0)

                # Bottom
                if r > 0:
                    model.addConstr(x[r,c,BOTTOM] <= x[r-1,c,MID] + x[r-1,c,TOP])
                else:
                    model.addConstr(x[r,c,BOTTOM] == 0)

                # Sub neighbours orthogonal
                for dr, dc in [(0,1), (0,-1), (1,0), (-1,0)]:
                    nr, nc = r+dr, c+dc
                    if 0 <= nr < rows and 0 <= nc < cols:
                        model.addConstr(x[r,c,SUB] + x[nr,nc,MID] + x[nr,nc,LEFT] + \
                                        x[nr,nc,RIGHT] + x[nr,nc,TOP] + x[nr,nc,BOTTOM] <= 1)

                # If mid active, must have entry neighbour
                neighbors_in = []
                if c > 0: neighbors_in.append(x[r,c-1,LEFT] + x[r,c-1,MID])
                if r > 0: neighbors_in.append(x[r-1,c,TOP] + x[r-1,c,MID])
                
                if neighbors_in:
                    model.addConstr(x[r,c,MID] <= gp.quicksum(neighbors_in), name=f"MidIn_{r}_{c}")
                else:
                    model.addConstr(x[r,c,MID] == 0)

                # And exit neighbour neighbor
                neighbors_out = []
                if c < cols - 1: neighbors_out.append(x[r,c+1,RIGHT] + x[r,c+1,MID])
                if r < rows - 1: neighbors_out.append(x[r+1,c,BOTTOM] + x[r+1,c,MID])
                
                if neighbors_out:
                    model.addConstr(x[r,c,MID] <= gp.quicksum(neighbors_out), name=f"MidOut_{r}_{c}")
                else:
                    model.addConstr(x[r,c,MID] == 0)

        # Diagonal Constraints
        for r in range(rows - 1):
            for c in range(cols - 1):
                is_ship_A = gp.quicksum(x[r,c,k] for k in range(1,7))
                is_ship_B = gp.quicksum(x[r+1,c+1,k] for k in range(1,7))
                model.addConstr(is_ship_A + is_ship_B <= 1)

                is_ship_C = gp.quicksum(x[r,c+1,k] for k in range(1,7))
                is_ship_D = gp.quicksum(x[r+1,c,k] for k in range(1,7))
                model.addConstr(is_ship_C + is_ship_D <= 1)

        # Hints (Dealing with front/back)
        if hasattr(puzzle, 'hints') and puzzle.hints:
            for (r, c), val in puzzle.hints.items():
                if val == WATER:
                    model.addConstr(x[r,c,WATER] == 1, name=f"Hint_W_{r}_{c}")
                elif val in [SUB, MID, LEFT, RIGHT, TOP, BOTTOM]:
                    # Force the exact shape variable to be 1
                    model.addConstr(x[r,c,val] == 1, name=f"Hint_Shape_{r}_{c}")

        model.optimize()

        # Output
        if model.Status == GRB.OPTIMAL:
            active_ships = self._extract_ships_from_grid(x, rows, cols)
            return active_ships
        else:
            return None
        
    def _extract_ships_from_grid(self, x_vars, rows, cols):
        """
        Parses 7 variable grid to find connected ships and lengths.
        """
        # Temp 0/1 grid
        grid = np.zeros((rows,cols), dtype=int)
        for r in range(rows):
            for c in range(cols):
                if x_vars[r, c, WATER].X < 0.5:
                    grid[r,c] = 1
        
        # Flood fill to find ships
        ships = []
        visited = np.zeros((rows, cols), dtype=bool)

        for r in range(rows):
            for c in range(cols):
                if grid[r,c] == 1 and not visited[r,c]:
                    # Tracing ship
                    cells = []
                    stack = [(r,c)]
                    visited[r,c] = True
                    while stack:
                        curr_r, curr_c = stack.pop()
                        cells.append((curr_r, curr_c))
                        for dr, dc in [(0,1), (0,-1), (1,0), (-1,0)]:
                            nr, nc = curr_r+dr, curr_c+dc
                            if 0 <= nr < rows and 0 <= nc < cols and grid[nr,nc] == 1 and not visited[nr,nc]:
                                visited[nr,nc] = True
                                stack.append((nr, nc))
                    ships.append({
                        'length': len(cells),
                        'cells': cells
                     })
        return ships