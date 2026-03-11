import re
import time

import os
import matplotlib.pyplot as plt
import numpy as np

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

def plot_scatter_results(ids, ship_times, cell_times):
    """
    Generates a scatter plot comparing solve times across a large dataset.
    Filters out infeasible (0 time) results.
    """
    # 1. Filter out any 0s (Infeasible runs)
    valid_ship = []
    valid_cell = []
    for s, c in zip(ship_times, cell_times):
        if s > 0 and c > 0:
            valid_ship.append(s)
            valid_cell.append(c)
            
    if not valid_ship:
        print("No valid data to plot!")
        return

    fig, ax = plt.subplots(figsize=(8, 8))
    
    # 2. Plot the data points
    ax.scatter(valid_ship, valid_cell, alpha=0.6, edgecolors='k', color='mediumpurple', s=40)
    
    # 3. Determine axis limits (make it a perfect square)
    max_time = max(max(valid_ship), max(valid_cell))
    max_limit = max_time * 1.1 # Add 10% padding
    
    # 4. Draw the y=x reference line
    ax.plot([0, max_limit], [0, max_limit], 'r--', linewidth=2, label='Equal Performance ($y=x$)')
    
    # 5. Formatting
    ax.set_xlim([0, max_limit])
    ax.set_ylim([0, max_limit])
    ax.set_xlabel('Ship Model Solve Time (Seconds)', fontsize=12)
    ax.set_ylabel('Cell Model Solve Time (Seconds)', fontsize=12)
    ax.set_title(f'Solver Comparison: {len(valid_ship)} CSPLib Instances', fontsize=14, fontweight='bold')
    
    # Add text labels explaining the regions
    ax.text(max_limit * 0.75, max_limit * 0.25, 'Ship Model\nis Slower', 
            fontsize=11, color='gray', ha='center', va='center', 
            bbox=dict(facecolor='white', alpha=0.8, edgecolor='none'))
            
    ax.text(max_limit * 0.25, max_limit * 0.75, 'Cell Model\nis Slower', 
            fontsize=11, color='gray', ha='center', va='center',
            bbox=dict(facecolor='white', alpha=0.8, edgecolor='none'))
    
    ax.legend(loc='upper left')
    ax.grid(True, linestyle='--', alpha=0.5)
    
    plt.tight_layout()
    plt.savefig("solver_scatter_comparison.png", dpi=300)
    print(f"\nScatter plot saved as 'solver_scatter_comparison.png'")
    plt.show()

def run_evaluation(filepath):
    """
    Loads all puzzles from the file and runs them through both solvers.
    Prints a statisitcal summary.
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

    # Data for graph
    ids = []
    ship_times = []
    cell_times = []
    
    for puzzle in puzzles:
        size = len(puzzle.row_tallies)
        ids.append(str(puzzle.id))
        
        # Evaluate Ship Model
        start_time_ship = time.time()
        res_ship = ship_solver.solve(puzzle)
        ship_time = time.time() - start_time_ship
        
        if res_ship:
            ship_status = f"{ship_time:.4f}s"
            ship_times.append(ship_time)
        else:
            ship_status = "Infeasible"
            ship_times.append(0)

        # Evaluate Cell Model 
        start_time_cell = time.time()
        res_cell = cell_solver.solve(puzzle)
        cell_time = time.time() - start_time_cell
        
        if res_cell:
            cell_status = f"{cell_time:.4f}s"
            cell_times.append(cell_time)
        else:
            cell_status = "Infeasible"
            cell_times.append(0)
            
        # Print side-by-side comparison
        print(f"{puzzle.id:<10} | {size}x{size:<4} | {ship_status:<18} | {cell_status:<18}")

    # Results summary
    total_puzzles = len(puzzles)
    ship_success = sum(1 for t in ship_times if t > 0)
    cell_success = sum(1 for t in cell_times if t > 0)

    jointly_solved = 0
    ship_wins = 0
    cell_wins = 0
    ship_total_time = 0.0
    cell_total_time = 0.0

    for s, c in zip(ship_times, cell_times):
        if s > 0 and c > 0:
            jointly_solved += 1
            ship_total_time += s
            cell_total_time += c
            if s < c:
                ship_wins += 1
            elif c < s:
                cell_wins += 1

    ship_avg = (ship_total_time / jointly_solved) if jointly_solved > 0 else 0
    cell_avg = (cell_total_time / jointly_solved) if jointly_solved > 0 else 0

    print("\n" + "="*55)
    print("EVALUATION SUMMARY".center(55))
    print("="*55)
    print(f"Total Puzzles Processed : {total_puzzles}")
    print(f"Valid Solutions Found   : Ship ({ship_success}), Cell ({cell_success})")
    print(f"Infeasible/Failed       : Ship ({total_puzzles - ship_success}), Cell ({total_puzzles - cell_success})")
    print("-" * 55)
    print("PERFORMANCE COMPARISON (on jointly solved puzzles):")
    print(f"Ship Model Faster       : {ship_wins} times")
    print(f"Cell Model Faster       : {cell_wins} times")
    print(f"Ship Model Avg Time     : {ship_avg:.4f} seconds")
    print(f"Cell Model Avg Time     : {cell_avg:.4f} seconds")
    print("="*55 + "\n")

    plot_scatter_results(ids, ship_times, cell_times)

if __name__ == "__main__":
    # DATA_FILE = "data/csplibExample.txt"
    DATA_FILE = "data/csplib.pl"
    
    run_evaluation(DATA_FILE)