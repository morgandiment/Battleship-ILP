from board import BattleshipPuzzle, BattleshipBoard
from solver import ShipModelSolver

def test_full_solver():
    print("--- Testing Full ILP Solver ---")
    
    # First efine the Puzzle (A known valid configuration)
    # Example uses the same layout as boardTest
    # Row 0: Battleship (4) at 0,0
    # Row 2: Cruiser (3) at 2,6
    # All others empty (Water)
    # Fleet overriden to keep it simple.
    
    row_tallies = [4, 0, 3, 0, 0, 0, 0, 0, 0, 0]
    col_tallies = [1, 1, 1, 1, 0, 0, 1, 1, 1, 0]
    
    puzzle = BattleshipPuzzle(row_tallies, col_tallies)
    puzzle.fleet_spec = {4: 1, 3: 1}
    
    # Run Solver
    solver = ShipModelSolver()
    result = solver.solve(puzzle)
    
    # Load results into Board
    if result:
        print(f"Solver found {len(result)} ships.")
        board = BattleshipBoard(puzzle)
        board.load_ship_model(result)
        
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