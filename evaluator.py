import re
import time
from board import BattleshipPuzzle
from cell_solver import CellModelSolver

from ship_solver import ShipModelSolver 

# Mapping CSPLib Prolog symbols to 7 Solver Constants
HINT_MAP = {
    'w': 0, # Water
    'c': 1, # Submarine / Circle
    'm': 2, # Middle
    'l': 3, # Left
    'r': 4, # Right
    't': 5, # Top
    'b': 6  # Bottom
}

def parse_prolog_csplib(filepath):
    """
    Parses a text file containing one or more Prolog-formatted Battleship problems.
    Returns a list of BattleshipPuzzle objects.
    """
    puzzles = []
    with open(filepath, 'r') as f:
        content = f.read()

    pattern = re.compile(
        r'problem\s*\(\s*(\d+)\s*,'      
        r'\s*\[(.*?)\]\s*,'              
        r'\s*\[(.*?)\]\s*,'              
        r'\s*\[(.*?)\]\s*,'              
        r'\s*\[(.*?)\]\s*\)\.',          
        re.DOTALL
    )

    for match in pattern.finditer(content):
        inst_id = int(match.group(1))

        # 1. Parse Fleet
        fleet_str = match.group(2).strip()
        fleet_spec = {}
        if fleet_str:
            for item in fleet_str.split(','):
                length, count = item.split(':')
                fleet_spec[int(length)] = int(count)

        # 2. Parse Tallies
        row_tallies = [int(x) for x in match.group(3).split(',') if x.strip()]
        col_tallies = [int(x) for x in match.group(4).split(',') if x.strip()]

        # 3. Parse Hints
        hints_str = match.group(5).strip()
        hints = {}
        if hints_str:
            hint_items = re.findall(r'([wcmlrtb])@\[\s*(\d+)\s*,\s*(\d+)\s*\]', hints_str)
            for h_type, r_str, c_str in hint_items:
                r = int(r_str) - 1
                c = int(c_str) - 1
                hints[(r, c)] = HINT_MAP[h_type]

        # 4. Create Puzzle Object
        puzzle = BattleshipPuzzle(row_tallies, col_tallies, hints)
        puzzle.fleet_spec = fleet_spec
        puzzle.id = inst_id 
        
        puzzles.append(puzzle)

    return puzzles

def run_evaluation(filepath):
    """
    Loads all puzzles from the file and runs them through both solvers.
    """
    print(f"Loading puzzles from {filepath}...")
    puzzles = parse_prolog_csplib(filepath)
    print(f"Found {len(puzzles)} puzzles. Starting evaluation...\n")
    
    # Updated Table Header
    print(f"{'Puzzle ID':<10} | {'Size':<6} | {'Ship Model Time':<18} | {'Cell Model Time':<18}")
    print("-" * 62)
    
    # Initialize both solvers
    cell_solver = CellModelSolver()
    ship_solver = ShipModelSolver() 
    
    for puzzle in puzzles:
        size = len(puzzle.row_tallies)
        
        # Evaluate Ship Model
        start_time_ship = time.time()
        res_ship = ship_solver.solve(puzzle)
        ship_time = time.time() - start_time_ship
        
        if res_ship:
            ship_status = f"{ship_time:.4f}s"
        else:
            ship_status = "Infeasible"

        # Evaluate Cell Model 
        start_time_cell = time.time()
        res_cell = cell_solver.solve(puzzle)
        cell_time = time.time() - start_time_cell
        
        if res_cell:
            cell_status = f"{cell_time:.4f}s"
        else:
            cell_status = "Infeasible"
            
        # Print side-by-side comparison
        print(f"{puzzle.id:<10} | {size}x{size:<4} | {ship_status:<18} | {cell_status:<18}")

if __name__ == "__main__":
    # DATA_FILE = "data/csplibExample.txt"
    DATA_FILE = "data/csplib.pl"
    
    run_evaluation(DATA_FILE)