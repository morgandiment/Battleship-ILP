from board import BattleshipPuzzle, BattleshipBoard
from ship_solver import ShipModelSolver
from cell_solver import CellModelSolver

WATER = 0
SUB = 1
MID = 2
LEFT = 3
RIGHT = 4
TOP = 5
BOTTOM = 6

def test_full_solver():
    print("--- Testing Full ILP Solver ---")
    
    # First define the Puzzle (A known valid configuration)
    # Example uses the same layout as boardTest
    # Row 0: Battleship (4) at 0,0
    # Row 2: Cruiser (3) at 2,6
    # All others empty (Water)
    # Fleet overriden to keep it simple.
    
    # Reduced fleet tallies
    # row_tallies = [4, 0, 3, 0, 0, 0, 0, 0, 0, 0]
    # col_tallies = [1, 1, 1, 1, 0, 0, 1, 1, 1, 0]

    # Full fleet tallies with hints
    row_tallies = [1, 4, 1, 2, 6, 2, 2, 2, 3, 2]
    col_tallies = [5, 1, 5, 1, 1, 5, 0, 2, 4, 1]
    my_hints = {
        (1, 1): LEFT,
        (2, 5): MID,
        (7, 3): SUB
    }
    
    puzzle = BattleshipPuzzle(row_tallies, col_tallies, hints=my_hints)
    # puzzle.fleet_spec = {4: 1, 3: 1}
    
    # Run Solver
    # solver = ShipModelSolver()
    solver = CellModelSolver()
    result = solver.solve(puzzle)
    
    # Load results into Board
    if result:
        solution, nodes = result
        print(f"Solver found {len(solution)} ships.")
        board = BattleshipBoard(puzzle)
        board.load_ship_model(solution)
        
        # 4. Display and Validate
        board.display()
        is_valid, msg = board.is_valid_solution()
        
        if is_valid:
            print("SUCCESS: Solver output is valid!")
        else:
            print(f"FAILED: Solver output invalid. {msg}")
    else:
        print("FAILED: Solver returned Infeasible.")

if __name__ == "__main__":
    test_full_solver()