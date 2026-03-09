import gurobipy as gp
from gurobipy import GRB
import numpy as np
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
            expr = gp.quicksum(y[c['id']] for c in candidates for (cr, cc) in c['cells'] if cr == r)
            model.addConstr(expr == puzzle.row_tallies[r], name=f"Row_Tally_{r}")

        for c in range(size):
            expr = gp.quicksum(y[cand['id']] for cand in candidates for (cr, cc) in cand['cells'] if cc == c)
            model.addConstr(expr == puzzle.col_tallies[c], name=f"Col_Tally_{c}")

        # Constraint: Geometry / Touching
        if self.verbose:
            print("Generating geometric conflicts...")
        conflicts = self._find_conflicts(candidates, size)
        if self.verbose:
            print(f'Found {len(conflicts)} incompatible pairs.')

        for id_a, id_b in conflicts:
            model.addConstr(y[id_a] + y[id_b] <= 1, name=f"Conflict_{id_a}_{id_b}")

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
            return selected_candidates
        else:
            print("No solution found (Infeasible).")
            # Debug line
            # model.computeIIS(); model.write("model.ilp")
            return None
        
    def _find_conflicts(self, candidates, size):
        """
        Returns list of tuples (id_a, id_b) that cannot coexist
        because they overlap or touch.
        """
        occupancy = {}
        for cand in candidates:
            for cell in cand['cells']:
                if cell not in occupancy: occupancy[cell] = []
                occupancy[cell].append(cand['id'])

        conflicts = set()

        for cand in candidates:
            forbidden_cells = set()
            for r, c in cand['cells']:
                forbidden_cells.add((r, c))
                for dr in [-1, 0, 1]:
                    for dc in [-1, 0, 1]:
                        if dr==0 and dc==0: continue
                        nr, nc = r+dr, c+dc
                        if 0 <= nr < size and 0 <= nc < size:
                            forbidden_cells.add((nr, nc))
            
            for cell in forbidden_cells:
                if cell in occupancy:
                    for other_id in occupancy[cell]:
                        if other_id != cand['id']:
                            pair = tuple(sorted((cand['id'], other_id)))
                            conflicts.add(pair)

        return list(conflicts)