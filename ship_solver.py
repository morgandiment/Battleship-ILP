import gurobipy as gp
from gurobipy import GRB
from solver_utils import generate_ship_candidates

WATER = 0
SUB = 1
MID = 2
LEFT = 3
RIGHT = 4
TOP = 5
BOTTOM = 6

class ShipModelSolver:
    """
    Ship-based model from Meufells paper.
    Variables: y[g] = 1 if ship candidate g is placed, 0 otherwise.
    """
    def __init__(self, verbose=False):
        # Initialises Gurobi env (cleans logs)
        self.verbose = verbose
        self.env = gp.Env(empty=True)
        self.env.setParam("OutputFlag", 0)
        self.env.start()

    def solve(self, puzzle):
        """
        :param puzzle: BattleshipPuzzle object (from board.py)

        Returns: list of candidate dicts (the ships to place) OR None if infeasible
        """
        # Generate ship placement candidates
        size = len(puzzle.row_tallies)
        candidates = generate_ship_candidates(size, puzzle.fleet_spec)

        model = gp.Model("BattleshipSolitaire", env=self.env)

        # Decision variables: y[id]
        y = {}
        for cand in candidates:
            y[cand['id']] = model.addVar(vtype=GRB.BINARY, name=f"y_{cand['id']}")

        # Constraint: Fleet inventory
        for length, count in puzzle.fleet_spec.items():
            model.addConstr(
                gp.quicksum(y[c['id']] for c in candidates if c['length'] == length) == count,
                name=f"Fleet_Count_{length}"
            )

        # Constraint: Row/Col Tallies
        # Mapping for fast lookup
        row_map = {r: [] for r in range(size)}
        col_map = {c: [] for c in range(size)}

        for c in candidates:
            for (r, c_idx) in c['cells']:
                row_map[r].append(c['id'])
                col_map[c_idx].append(c['id'])

        for r in range(size):
            model.addConstr(gp.quicksum(y[cid] for cid in row_map[r]) == puzzle.row_tallies[r], name=f"Row_Tally_{r}")

        for c in range(size):
            model.addConstr(gp.quicksum(y[cid] for cid in col_map[c]) == puzzle.col_tallies[c], name=f"Col_Tally_{c}")

        # Constraint: Geometry / Touching
        if self.verbose:
            print("Generating geometric conflicts...")

        # Map which candidates occupy which cell
        occupancy = {(r, c): [] for r in range(size) for c in range(size)}
        for cand in candidates:
            for r, c in cand['cells']:
                occupancy[(r, c)].append(cand['id'])

        # Preventing overlaps in same square
        for (r, c), cids in occupancy.items():
            if len(cids) > 1:
                model.addConstr(gp.quicksum(y[cid] for cid in cids) <= 1, name=f"NoOverlap_{r}_{c}")

        # Preventing orthogonal and diagonal touching
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]

        for r in range(size):
            for c in range(size):
                for dr, dc in directions:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < size and 0 <= nc < size:
                        # Combine candidates occupying cell A and neighbour cell B
                        combined_cids = set(occupancy[(r, c)] + occupancy[(nr, nc)])

                        # If multiple candidates are fighting for space, enforce limit
                        if len(combined_cids) > 1:
                            model.addConstr(
                                gp.quicksum(y[cid] for cid in combined_cids) <= 1,
                                name=f"NoTouch_{r}_{c}_to_{nr}_{nc}"
                            )

        # Constraint: Hints
        if hasattr(puzzle, 'hints') and puzzle.hints:
            for (r, c_idx), val in puzzle.hints.items():
                covering_ids = [cand['id'] for cand in candidates if (r, c_idx) in cand['cells']]

                if not covering_ids and val != WATER:
                    print(f"Error: Hint says Ship at {r},{c_idx}, but no ship fits there.")
                    return None

                # Handle Water
                if val == WATER:
                    model.addConstr(gp.quicksum(y[cid] for cid in covering_ids) == 0, name=f"Hint_W_{r}_{c_idx}")
                    continue
                
                # Handle Ship Shapes
                # Must be a ship
                model.addConstr(gp.quicksum(y[cid] for cid in covering_ids) == 1, name=f"Hint_S_{r}_{c_idx}")

                # Filter out candidates that violate specific shape
                invalid_cids = []
                for cid in covering_ids:
                    cand = candidates[cid]
                    cells = cand['cells']
                    length = cand['length']
                    orient = cand['orientation']
                    
                    # Find where this cell sits inside the candidate's list of cells
                    idx = cells.index((r, c_idx))
                    
                    is_valid = False
                    if val == SUB:
                        is_valid = (length == 1)
                    elif val == LEFT:
                        is_valid = (orient == 'H' and length > 1 and idx == 0)
                    elif val == RIGHT:
                        is_valid = (orient == 'H' and length > 1 and idx == length - 1)
                    elif val == TOP:
                        is_valid = (orient == 'V' and length > 1 and idx == 0)
                    elif val == BOTTOM:
                        is_valid = (orient == 'V' and length > 1 and idx == length - 1)
                    elif val == MID:
                        is_valid = (length > 2 and 0 < idx < length - 1)

                    if not is_valid:
                        invalid_cids.append(cid)

                # Ban all candidates that don't match shape
                if invalid_cids:
                    model.addConstr(gp.quicksum(y[cid] for cid in invalid_cids) == 0, name=f"Hint_ShapeBan_{r}_{c_idx}")

        # Optimise
        model.optimize()

        # Extracting solution
        if model.Status == GRB.OPTIMAL:
            selected_candidates = []
            for cand in candidates:
                if y[cand['id']].X > 0.5:
                    selected_candidates.append(cand)
            return selected_candidates, model.NodeCount
        else:
            print("No solution found (Infeasible).")
            # Debug line
            # model.computeIIS(); model.write("model.ilp")
            return None