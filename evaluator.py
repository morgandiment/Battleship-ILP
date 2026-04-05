import re
import time
import argparse
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt

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

def get_difficulty(hints_dict):
    """Categorises puzzle difficutly based on number of hints."""
    num_hints = len(hints_dict)
    if num_hints >= 10:
        return "Easy"
    elif 4 <= num_hints <= 9:
        return "Medium"
    else:
        return "Hard"

def plot_scatter_results(ids, ship_times, cell_times, categories):
    """
    Generates a scatter plot comparing solve times across a large dataset and difficulties.
    """
    fig, ax = plt.subplots(figsize=(9, 9))
    
    # Colors and markers for different difficulties
    styles = {
        'Easy':   {'color': 'limegreen', 'marker': 'o', 'label': 'Easy (10+ Hints)'},
        'Medium': {'color': 'orange',    'marker': '^', 'label': 'Medium (4-9 Hints)'},
        'Hard':   {'color': 'crimson',   'marker': 's', 'label': 'Hard (0-3 Hints)'}
    }
    
    max_time = 0.0
    
    # Plot each category separately so they get distinct legend entries
    for cat in ['Easy', 'Medium', 'Hard']:
        x_vals = [s for s, c, catg in zip(ship_times, cell_times, categories) if s > 0 and c > 0 and catg == cat]
        y_vals = [c for s, c, catg in zip(ship_times, cell_times, categories) if s > 0 and c > 0 and catg == cat]
        
        if x_vals:
            max_time = max(max_time, max(x_vals), max(y_vals))
            ax.scatter(x_vals, y_vals, alpha=0.7, edgecolors='k', 
                       color=styles[cat]['color'], marker=styles[cat]['marker'],
                       s=20, label=styles[cat]['label'])
            
    if max_time == 0:
        print("No valid data to plot!")
        return
        
    max_limit = max_time * 1.1 
    
    # Diagonal Reference Line
    ax.plot([0, max_limit], [0, max_limit], 'k--', linewidth=1.5, alpha=0.5, label='Equal Performance')
    
    ax.set_xlim([0, max_limit])
    ax.set_ylim([0, max_limit])
    ax.set_xlabel('Ship Model Solve Time (Seconds)', fontsize=12)
    ax.set_ylabel('Cell Model Solve Time (Seconds)', fontsize=12)
    ax.set_title('Solver Performance by Puzzle Difficulty', fontsize=14, fontweight='bold')
    
    # Regions
    ax.text(max_limit * 0.75, max_limit * 0.25, 'Ship Slower\nCell Faster', fontsize=11, color='gray', ha='center', va='center')
    ax.text(max_limit * 0.25, max_limit * 0.75, 'Cell Slower\nShip Faster', fontsize=11, color='gray', ha='center', va='center')
    
    ax.legend(loc='upper left', framealpha=0.9)
    ax.grid(True, linestyle=':', alpha=0.6)
    
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    results_dir = Path(__file__).resolve().parent / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    out_file = results_dir / f"solver_difficulty_scatter_{timestamp}.png"

    plt.tight_layout()
    plt.savefig(out_file, dpi=300)
    print(f"\nScatter plot saved at '{out_file}'")
    plt.show()

def run_evaluation(filepath, solver_choice):
    """
    Loads all puzzles from the file and runs them through the selected solver(s).
    Prints a statistical summary.
    """
    print(f"Loading puzzles from {filepath}...")
    try:
        puzzles = parse_prolog_csplib(filepath)
    except FileNotFoundError:
        print(f"Error: The file '{filepath}' was not found.")
        return

    print(f"Found {len(puzzles)} puzzles. Starting evaluation...\n")
    
    # Updated Table Header
    print(f"{'ID':<6} | {'Size':<6} | {'Hints':<5} | {'Diff':<6} | {'Ship Time':<12} | {'Cell Time':<12}")
    print("-" * 60)
    
    # Initialize both solvers
    cell_solver = CellModelSolver() if solver_choice in ['CELL', 'BOTH'] else None
    ship_solver = ShipModelSolver() if solver_choice in ['SHIP', 'BOTH'] else None

    # Data for graph
    ids, ship_times, cell_times, categories = [], [], [], []
    
    for puzzle in puzzles:
        size = len(puzzle.row_tallies)
        num_hints = len(puzzle.hints)
        diff = get_difficulty(puzzle.hints)
        ids.append(str(puzzle.id))
        categories.append(diff)

        ship_status = "N/A"
        cell_status = "N/A"
        s_time = 0
        c_time = 0
        
        # Evaluate Ship Model
        if ship_solver:
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
        if cell_solver:
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
        print(f"{puzzle.id:<6} | {size}x{size:<4} | {num_hints:<5} | {diff:<6} | {ship_status:<12} | {cell_status:<12}")

    # Results summary
    print("\n" + "="*60)
    print(f"EVALUATION SUMMARY BY DIFFICULTY ({solver_choice})".center(60))
    print("="*60)
    
    for diff_level in ['Easy', 'Medium', 'Hard']:
        # Filter metrics for this specific difficulty
        d_ships = [s for s, cat in zip(ship_times, categories) if s > 0 and cat == diff_level]
        d_cells = [c for c, cat in zip(cell_times, categories) if c > 0 and cat == diff_level]
        
        count_ships = len(d_ships)
        count_cells = len(d_cells)

        if count_ships == 0 and count_cells == 0:
            continue

        print(f"{diff_level.upper()}".center(60)) 

        if solver_choice in ['SHIP', 'BOTH'] and count_ships > 0:
            ship_avg = sum(d_ships) / count_ships
            print(f"  Ship Model -> Solved: {count_ships} | Avg Time: {ship_avg:.4f}s")

        if solver_choice in ['CELL', 'BOTH'] and count_cells > 0:
            cell_avg = sum(d_cells) / count_cells
            print(f"  Cell Model -> Solved: {count_cells} | Avg Time: {cell_avg:.4f}s")

        if solver_choice == 'BOTH' and count_ships > 0 and count_cells > 0:
            joint_pairs =  [(s, c) for s, c, cat in zip(ship_times, cell_times, categories) if s > 0 and c > 0 and cat == diff_level]
            if joint_pairs:
                ship_wins = sum(1 for s, c in joint_pairs if s < c)
                cell_wins = sum(1 for s, c in joint_pairs if c < s)
                print(f"  Win Count -> Ship: {ship_wins:<6} | Cell: {cell_wins:<6}")
        
        print("-" * 60)

    if solver_choice == 'BOTH':
        plot_scatter_results(ids, ship_times, cell_times, categories)
    else:
        print("\nSkipping scatter plot generation (requires BOTH solvers to be run).")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate Battleship Solitaire ILP models.")
    parser.add_argument('filepath', type=str, help="Path to the CSPLib formatted dataset (e.g., data/test.pl)")
    parser.add_argument('--solver', type=str, choices=['CELL', 'SHIP', 'BOTH'], default='BOTH', help="Which solver to run: CELL, SHIP or BOTH (default is BOTH)")
    args = parser.parse_args()

    run_evaluation(args.filepath, args.solver)