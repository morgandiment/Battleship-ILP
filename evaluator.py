import re
import time
import argparse
from datetime import datetime
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
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

def get_difficulty(hints_dict):
    """Categorises puzzle difficutly based on number of hints."""
    num_hints = len(hints_dict)
    if num_hints >= 10:
        return "Easy"
    elif 4 <= num_hints <= 9:
        return "Medium"
    else:
        return "Hard"

def plot_scatter_results(ids, ship_times, cell_times, categories, timestamp):
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
    
    results_dir = Path(__file__).resolve().parent / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    out_file = results_dir / f"solver_difficulty_scatter_{timestamp}.png"

    plt.tight_layout()
    plt.savefig(out_file, dpi=300)
    print(f"\nScatter plot saved at '{out_file}'")
    # plt.show()

def plot_cactus_results(ship_times, cell_times, cell_improv_times, timestamp):
    """
    Generates a cumulative performance (Cactus) plot.
    X-axis: Number of instances solved.
    Y-axis: Time taken to solve that instance.
    """
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Filter out failures
    valid_ship = [t for t in ship_times if t > 0]
    valid_cell = [t for t in cell_times if t > 0]
    valid_cell_improv = [t for t in cell_improv_times if t > 0]
    
    # Sort times in ascending order
    valid_ship.sort()
    valid_cell.sort()
    valid_cell_improv.sort()
    
    # X-axis
    x_ship = range(1, len(valid_ship) + 1)
    x_cell = range(1, len(valid_cell) + 1)
    x_cell_improv = range(1, len(valid_cell_improv) + 1)
    
    # Plot the lines
    if valid_ship:
        ax.plot(x_ship, valid_ship, label='Ship Model', 
                color='blue', linewidth=2, marker='o', markersize=4, markevery=max(1, len(valid_ship)//20))
    if valid_cell:
        ax.plot(x_cell, valid_cell, label='Cell Model (Standard)', 
                color='red', linewidth=2, marker='^', markersize=4, markevery=max(1, len(valid_cell)//20))
    if valid_cell_improv:
        ax.plot(x_cell_improv, valid_cell_improv, label='Cell Model (Improved)', 
                color='seagreen', linewidth=2, marker='s', markersize=4, markevery=max(1, len(valid_cell_improv)//20))
        
    # Formatting
    ax.set_xlabel('Number of Puzzles Solved', fontsize=12, fontweight='bold')
    ax.set_ylabel('Time to Solve (Seconds)', fontsize=12, fontweight='bold')
    ax.set_title('Cumulative Solver Performance (Cactus Plot)', fontsize=14, fontweight='bold')
    
    # Optional: Logarithmic Y-axis if the time differences are massive
    # ax.set_yscale('log') 
    
    ax.legend(loc='upper left', framealpha=0.9, fontsize=11)
    ax.grid(True, linestyle='--', alpha=0.7)
    
    # Save the plot
    results_dir = Path(__file__).resolve().parent / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    out_file = results_dir / f"solver_cactus_{timestamp}.png"

    plt.tight_layout()
    plt.savefig(out_file, dpi=300)
    print(f"Cactus plot saved at '{out_file}'")
    # plt.show()

def plot_line_comparison(sizes, ship_times, cell_times, cell_improv_times, timestamp):
    """
    Generates a line graph comparing Cell (Std) vs Cell (Improved) vs Ship models across different grid sizes.
    """
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Convert n x n to total cells
    total_cells = [s * s for s in sizes]
    unique_cells = sorted(list(set(total_cells)))
    
    avg_ship, avg_cell, avg_cell_improv = [], [], []
    
    for uc in unique_cells:
        # Get times for this grid size, ignoring infeasible results
        s_times = [s for s, cells in zip(ship_times, total_cells) if cells == uc and s > 0]
        c_times = [c for c, cells in zip(cell_times, total_cells) if cells == uc and c > 0]
        c_improv_times = [cut for cut, cells in zip(cell_improv_times, total_cells) if cells == uc and cut > 0]
        
        # Calculate averages, default to 0 if no successful solves
        avg_ship.append(sum(s_times)/len(s_times) if s_times else 0)
        avg_cell.append(sum(c_times)/len(c_times) if c_times else 0)
        avg_cell_improv.append(sum(c_improv_times)/len(c_improv_times) if c_improv_times else 0)

    # Plot the lines
    ax.plot(unique_cells, avg_cell, marker='o', linestyle='-', color='red', label='Cell Model (Std)', linewidth=2)
    ax.plot(unique_cells, avg_cell_improv, marker='s', linestyle='-', color='seagreen', label='Cell Model (Improved)', linewidth=2)
    ax.plot(unique_cells, avg_ship, marker='^', linestyle='-', color='blue', label='Ship Model', linewidth=2)

    # Formatting
    ax.set_yscale('log')
    ax.set_xlabel('Grid Size (Total Cells)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Average Solve Time (Seconds, Log Scale)', fontsize=12, fontweight='bold')
    ax.set_title('Scaling Performance: ILP Models by Grid Size', fontsize=14, fontweight='bold')
    
    ax.legend(loc='upper left', framealpha=0.9, fontsize=11)
    ax.grid(True, which="both", ls="--", alpha=0.5)
    
    # Save the plot
    results_dir = Path(__file__).resolve().parent / "results"
    out_file = results_dir / f"solver_line_comparison_{timestamp}.png"

    plt.tight_layout()
    plt.savefig(out_file, dpi=300)
    print(f"Line graph saved at '{out_file}'")

def plot_cuts_comparison(sizes, cell_times, cell_improv_times, timestamp):
    """
    Generates a grouped bar chart comparing the Cell model with and without valid inequalities.
    """
    fig, ax = plt.subplots(figsize=(10, 6))
    
    total_cells = [s * s for s in sizes]
    unique_cells = sorted(list(set(total_cells)))
    
    avg_cell = []
    avg_cuts = []
    
    for uc in unique_cells:
        c_times = [c for c, cells in zip(cell_times, total_cells) if cells == uc and c > 0]
        cut_times = [cut for cut, cells in zip(cell_improv_times, total_cells) if cells == uc and cut > 0]
        
        avg_cell.append(sum(c_times)/len(c_times) if c_times else 0)
        avg_cuts.append(sum(cut_times)/len(cut_times) if cut_times else 0)

    x = np.arange(len(unique_cells))
    width = 0.35
    
    # Plotting the bars side-by-side
    ax.bar(x - width/2, avg_cell, width, label='Cell Model (Standard)', color='crimson', alpha=0.8)
    ax.bar(x + width/2, avg_cuts, width, label='Cell Model (With Improvisations)', color='seagreen', alpha=0.8)
    
    ax.set_ylabel('Average Solve Time (Seconds)', fontsize=12, fontweight='bold')
    ax.set_xlabel('Grid Size (Total Cells)', fontsize=12, fontweight='bold')
    ax.set_title('Impact of Valid Inequalities on Cell Model Performance', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(unique_cells)
    
    ax.legend(loc='upper left', framealpha=0.9, fontsize=11)
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    
    results_dir = Path(__file__).resolve().parent / "results"
    out_file = results_dir / f"solver_cuts_comparison_{timestamp}.png"
    plt.tight_layout()
    plt.savefig(out_file, dpi=300)
    print(f"Improvisation comparison graph saved at '{out_file}'")

def plot_node_comparison(sizes, ship_nodes, cell_nodes, cell_improv_nodes, timestamp):
    """
    Generates a grouped bar chart comparing Branch & Bound nodes explored.
    """
    fig, ax = plt.subplots(figsize=(10, 6))
    
    total_cells = [s * s for s in sizes]
    unique_cells = sorted(list(set(total_cells)))
    
    avg_ship, avg_cell, avg_cuts = [], [], []
    
    for uc in unique_cells:
        # Get nodes, ignoring -1 (our flag for infeasible)
        s_n = [n for n, cells in zip(ship_nodes, total_cells) if cells == uc and n >= 0]
        c_n = [n for n, cells in zip(cell_nodes, total_cells) if cells == uc and n >= 0]
        cut_n = [n for n, cells in zip(cell_improv_nodes, total_cells) if cells == uc and n >= 0]
        
        avg_ship.append(sum(s_n)/len(s_n) if s_n else 0)
        avg_cell.append(sum(c_n)/len(c_n) if c_n else 0)
        avg_cuts.append(sum(cut_n)/len(cut_n) if cut_n else 0)

    x = np.arange(len(unique_cells))
    width = 0.25
    
    ax.bar(x - width, avg_ship, width, label='Ship Model', color='blue', alpha=0.8)
    ax.bar(x, avg_cell, width, label='Cell Model (Std)', color='crimson', alpha=0.8)
    ax.bar(x + width, avg_cuts, width, label='Cell Model (Improvements)', color='seagreen', alpha=0.8)
    
    # Symlog allows plotting 0 on a logarithmic scale
    # ax.set_yscale('symlog', linthresh=1.0)
    ax.set_yscale('linear')

    ax.set_ylabel('Avg Branch & Bound Nodes (Symlog Scale)', fontsize=12, fontweight='bold')
    ax.set_xlabel('Grid Size (Total Cells)', fontsize=12, fontweight='bold')
    ax.set_title('Mathematical Complexity: Nodes Explored by Solver', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(unique_cells)
    
    ax.legend(loc='upper left', framealpha=0.9, fontsize=11)
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    
    results_dir = Path(__file__).resolve().parent / "results"
    out_file = results_dir / f"solver_nodes_comparison_{timestamp}.png"
    plt.tight_layout()
    plt.savefig(out_file, dpi=300)
    print(f"Nodes comparison graph saved at '{out_file}'")

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
    print(f"{'ID':<6} | {'Size':<6} | {'Hints':<5} | {'Diff':<6} | {'Ship Time':<10} | {'Cell Time':<10} | {'Cell Improved':<10}")
    print("-" * 70)
    
    # Initialize both solvers
    cell_solver = CellModelSolver(use_improv=False) if solver_choice in ['CELL', 'ALL'] else None
    cell_improv_solver = CellModelSolver(use_improv=True) if solver_choice in ['CELL_IMPROVED', 'ALL'] else None
    ship_solver = ShipModelSolver() if solver_choice in ['SHIP', 'ALL'] else None

    # Data for graph
    ids, ship_times, cell_times, cell_improv_times, categories, sizes = [], [], [], [], [], []
    ship_nodes, cell_nodes, cell_improv_nodes = [], [], []
    
    for puzzle in puzzles:
        size = len(puzzle.row_tallies)
        num_hints = len(puzzle.hints)
        diff = get_difficulty(puzzle.hints)

        sizes.append(size)
        ids.append(str(puzzle.id))
        categories.append(diff)

        ship_status = cell_status = cell_improv_status = "N/A"
        
        # Evaluate Ship Model
        if ship_solver:
            start_time_ship = time.time()
            res = ship_solver.solve(puzzle)
            ship_time = time.time() - start_time_ship
            if res:
                solution, nodes = res
                ship_status = f"{ship_time:.4f}s"
                ship_times.append(ship_time)
                ship_nodes.append(nodes)
            else:
                ship_status = "Infeasible"
                ship_times.append(0)
                ship_nodes.append(-1)

        # Evaluate Cell Model 
        if cell_solver:
            start_time_cell = time.time()
            res = cell_solver.solve(puzzle)
            cell_time = time.time() - start_time_cell
            if res:
                solution, nodes = res
                cell_status = f"{cell_time:.4f}s"
                cell_times.append(cell_time)
                cell_nodes.append(nodes)
            else:
                cell_status = "Infeasible"
                cell_times.append(0)
                cell_nodes.append(-1)

        # Evaluate Improved Cell Model
        if cell_improv_solver:
            start_time = time.time()
            res = cell_improv_solver.solve(puzzle)
            t = time.time() - start_time
            if res:
                solution, nodes = res
                cell_improv_status = f"{t:.4f}s"
                cell_improv_times.append(t)
                cell_improv_nodes.append(nodes)
            else:
                cell_improv_status =  "Infeasible"
                cell_improv_times.append(0)
                cell_improv_nodes.append(-1)
                
        # Print side-by-side comparison
        print(f"{puzzle.id:<6} | {size}x{size:<4} | {num_hints:<5} | {diff:<6} | {ship_status:<10} | {cell_status:<10} | {cell_improv_status:<10}")

    # Results summary
    print("\n" + "="*75)
    print(f"EVALUATION SUMMARY BY DIFFICULTY ({solver_choice})".center(60))
    print("="*75)
    
    for diff_level in ['Easy', 'Medium', 'Hard']:
        # Filter metrics for this specific difficulty
        d_ships = [s for s, cat in zip(ship_times, categories) if s > 0 and cat == diff_level]
        d_cells = [c for c, cat in zip(cell_times, categories) if c > 0 and cat == diff_level]
        d_cell_improv = [cut for cut, cat in zip(cell_improv_times, categories) if cut > 0 and cat == diff_level]
        
        count_ships = len(d_ships)
        count_cells = len(d_cells)
        count_cell_improv = len(d_cell_improv)

        if count_ships == 0 and count_cells == 0 and count_cell_improv == 0:
            continue

        print(f"{diff_level.upper()}".center(75)) 

        if solver_choice in ['SHIP', 'ALL'] and count_ships > 0:
            ship_avg = sum(d_ships) / count_ships
            print(f"  Ship Model -> Solved: {count_ships} | Avg Time: {ship_avg:.4f}s")

        if solver_choice in ['CELL', 'ALL'] and count_cells > 0:
            cell_avg = sum(d_cells) / count_cells
            print(f"  Cell Model (Std) -> Solved: {count_cells} | Avg Time: {cell_avg:.4f}s")

        if solver_choice in ['CELL_IMPROVED', 'ALL'] and count_cell_improv > 0:
            cell_improv_avg = sum(d_cell_improv) / count_cell_improv
            print(f"  Cell Model (Improved) -> Solved: {count_cell_improv} | Avg Time: {cell_improv_avg:.4f}s")

        if solver_choice == 'ALL' and count_ships > 0 and count_cells > 0 and count_cell_improv > 0:
            joint_pairs =  [(s, c, cut) for s, c, cut, cat in zip(ship_times, cell_times, cell_improv_times, categories) if s > 0 and c > 0 and cut > 0 and cat == diff_level]
            if joint_pairs:
                ship_wins = sum(1 for s, c, cut in joint_pairs if s < c and s < cut)
                cell_wins = sum(1 for s, c, cut in joint_pairs if c < s and c < cut)
                cell_improv_wins = sum(1 for s, c, cut in joint_pairs if cut < s and cut < c)
                print(f"  Win Count -> Ship: {ship_wins:<4} | Cell Std: {cell_wins:<4} | Cell Improved: {cell_improv_wins:<4}")
        
        print("-" * 75)

    if solver_choice == 'ALL':
        run_timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        plot_scatter_results(ids, ship_times, cell_times, categories, run_timestamp)
        plot_cactus_results(ship_times, cell_times, cell_improv_times, run_timestamp)
        plot_line_comparison(sizes, ship_times, cell_times, cell_improv_times, run_timestamp)
        plot_cuts_comparison(sizes, cell_times, cell_improv_times, run_timestamp)
        plot_node_comparison(sizes, ship_nodes, cell_nodes, cell_improv_nodes, run_timestamp)
    else:
        print("\nSkipping plot generation (requires ALL solvers to be run).")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate Battleship Solitaire ILP models.")
    parser.add_argument('filepath', type=str, help="Path to the CSPLib formatted dataset (e.g., data/test.pl)")
    parser.add_argument('--solver', type=str, choices=['CELL', 'SHIP', 'BOTH'], default='BOTH', help="Which solver to run: CELL, SHIP or BOTH (default is BOTH)")
    args = parser.parse_args()

    run_evaluation(args.filepath, args.solver)