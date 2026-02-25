import numpy as np
from board import BattleshipPuzzle, BattleshipBoard, WATER

def test_valid_board():
    print("Testing Valid Board:")
    # Reduced fleet for testing: 1x Battleship(4), 1x Cruiser(3)
    # Row 0: Battleship (4) -> Tally 4
    # Row 2: Cruiser (3)    -> Tally 3
    # All other rows 0
    row_tallies = [4, 0, 3, 0, 0, 0, 0, 0, 0, 0]
    col_tallies = [1, 1, 1, 1, 0, 0, 1, 1, 1, 0] # Example for vertical/horizontal mix
    
    
    puzzle = BattleshipPuzzle(row_tallies, col_tallies)

    custom_fleet = {4: 1, 3: 1} 
    puzzle.fleet_spec = custom_fleet

    board = BattleshipBoard(puzzle)

    # 2. Place ships (Simulating a Solver)
    # Battleship at (0,0) to (0,3)
    board.grid[0, 0] = 4
    board.grid[0, 1] = 4
    board.grid[0, 2] = 4
    board.grid[0, 3] = 4

    # Cruiser at (2,6) to (2,8)
    board.grid[2, 6] = 3
    board.grid[2, 7] = 3
    board.grid[2, 8] = 3

    # Set everything else to WATER (0)
    for r in range(10):
        for c in range(10):
            if board.grid[r, c] == -1:
                board.grid[r, c] = WATER

    # Validation
    is_valid, msg = board.is_valid_solution()
    if is_valid:
        print("SUCCESS: Valid board accepted.")
    else:
        print(f"FAILED: Valid board rejected. Reason: {msg}")
    
    return board

def test_invalid_geometry(valid_board):
    print("\nTesting Invalid Geometry (Diagonal Touch):")
    # Take the valid board and break it
    # Add a '1' (Submarine) at (1,4) - touches Battleship at (0,3) diagonally
    valid_board.grid[1, 4] = 1

    # Updating tally numbers to pass checks
    valid_board.puzzle.row_tallies[1] += 1
    valid_board.puzzle.col_tallies[4] += 1
    
    is_valid, msg = valid_board.is_valid_solution()

    # Cleanup
    valid_board.grid[1, 4] = 0
    valid_board.puzzle.row_tallies[1] -= 1
    valid_board.puzzle.col_tallies[4] -= 1

    if not is_valid and "Diagonal" in msg:
        print(f"SUCCESS: Caught diagonal touch. ({msg})")
    else:
        print(f"FAILED: Failed to catch diagonal touch. Result: {is_valid}, {msg}")

def test_invalid_tally(valid_board):
    print("\nTesting Invalid Tally:")
    # Reset board
    valid_board.grid[1, 4] = 0 
    # Add a random ship segment that ruins the row count
    valid_board.grid[9, 9] = 1
    
    is_valid, msg = valid_board.is_valid_solution()
    if not is_valid and "Tally" in msg:
        print(f"SUCCESS: Caught wrong tally. ({msg})")
    else:
        print(f"FAILED: Failed to catch tally error. Result: {is_valid}, {msg}")

if __name__ == "__main__":
    b = test_valid_board()
    test_invalid_geometry(b)
    test_invalid_tally(b)