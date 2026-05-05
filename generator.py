import random
import math


def generate_dynamic_fleet(size):
    """
    Dynamically scales the fleet based on grid area to maintain ~20% density.
    Base fleet (10x10): 1x4, 2x3, 3x2, 4x1 (Total segments = 20)
    """
    base_area = 100
    current_area = size * size

    # Calculate a scaling multiplier
    multiplier = math.ceil(current_area / base_area)

    # Scale the standard CSPLib Battleship fleet
    fleet = {
        4: 1 * multiplier,  # Battleships
        3: 2 * multiplier,  # Cruisers
        2: 3 * multiplier,  # Destroyers
        1: 4 * multiplier,  # Submarines
    }
    return fleet


def generate_valid_board(size, fleet):
    """
    Attempts to place the fleet legally on an empty grid.
    Returns the grid if successful, or None if it gets stuck.
    """
    grid = [[0 for _ in range(size)] for _ in range(size)]

    def can_place(r, c, length, orient):
        # Check boundaries
        if orient == "H" and c + length > size:
            return False
        if orient == "V" and r + length > size:
            return False

        # Check physical overlap and 1-cell buffer
        for i in range(length):
            cr = r + (i if orient == "V" else 0)
            cc = c + (i if orient == "H" else 0)

            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    nr, nc = cr + dr, cc + dc
                    if 0 <= nr < size and 0 <= nc < size:
                        if grid[nr][nc] != 0:
                            return False
        return True

    def place_ship(r, c, length, orient):
        if length == 1:
            grid[r][c] = 1  # Sub
        elif orient == "H":
            grid[r][c] = 3  # Left
            for i in range(1, length - 1):
                grid[r][c + i] = 2  # Mid
            grid[r][c + length - 1] = 4  # Right
        elif orient == "V":
            grid[r][c] = 5  # Top
            for i in range(1, length - 1):
                grid[r + i][c] = 2  # Mid
            grid[r + length - 1][c] = 6  # Bot

    # Place ships from largest to smallest
    for length, count in sorted(fleet.items(), reverse=True):
        for _ in range(count):
            placed = False
            retries = 0
            while not placed and retries < 100:
                orient = random.choice(["H", "V"])
                r = random.randint(0, size - 1)
                c = random.randint(0, size - 1)

                if can_place(r, c, length, orient):
                    place_ship(r, c, length, orient)
                    placed = True
                retries += 1

            if not placed:
                return None  # Failed to fit, need to restart grid
    return grid


def format_as_prolog(id_num, size, fleet, grid, num_hints=5):
    """
    Converts a filled grid into the CSPLib problem(...) format.
    """
    # 1. Calculate Tallies
    row_tallies = [sum(1 for val in row if val != 0) for row in grid]
    col_tallies = [sum(1 for r in range(size) if grid[r][c] != 0) for c in range(size)]

    # 2. Sample Random Hints
    # Mapping numeric constants back to CSPLib characters
    rev_map = {0: "w", 1: "c", 2: "m", 3: "l", 4: "r", 5: "t", 6: "b"}

    all_coords = [(r, c) for r in range(size) for c in range(size)]

    # Prevent hint number being larger than total cells.
    actual_hints = min(num_hints, size * size)
    hint_coords = random.sample(all_coords, actual_hints)

    hints_list = []
    for r, c in hint_coords:
        val = grid[r][c]
        char = rev_map[val]
        # CSPLib format uses 1-based indexing for coordinates
        hints_list.append(f"{char}@[{r+1},{c+1}]")

    # 3. Format Strings
    fleet_str = ",".join([f"{length}:{count}" for length, count in fleet.items()])
    row_str = ",".join(map(str, row_tallies))
    col_str = ",".join(map(str, col_tallies))
    hint_str = ",".join(hints_list)

    return f"problem({id_num},\n    [{fleet_str}],\n    [{row_str}],\n    [{col_str}],\n    [{hint_str}])."


def generate_dataset(filename, dynamic=False, seed=42):
    random.seed(seed)
    """
    Generates a dataset of Battleship puzzles.

    Args:
        filename: Output file path
        dynamic: If True, uses dynamically scaled fleets based on grid size.
                If False, uses fixed static fleet configurations.
    """
    if dynamic:
        # Dynamic mode: scales fleets based on grid area
        grid_sizes = [10, 15, 20, 25, 30]
        hint_counts = [0, 2, 4, 6, 8, 10, 12, 14]
        instances_per_config = 5

        with open(filename, "w") as f:
            id_counter = 1
            for size in grid_sizes:
                fleet = generate_dynamic_fleet(size)
                for hints in hint_counts:
                    print(f"Generating {size}x{size} grid with {hints} hints...")
                    successes = 0
                    while successes < instances_per_config:
                        grid = generate_valid_board(size, fleet)
                        if grid:  # Ensure the generator didn't get stuck
                            prolog_str = format_as_prolog(id_counter, size, fleet, grid, hints)
                            f.write(prolog_str + "\n")
                            id_counter += 1
                            successes += 1

        print(f"\nSuccessfully generated {id_counter - 1} scalable puzzles into '{filename}'!")

    else:
        # Static mode: uses fixed fleet configurations
        configs = [
            # Medium/Hard Puzzles
            {"size": 6, "hints": 3, "count": 10, "fleet": {3: 1, 2: 2, 1: 3}},
            {"size": 8, "hints": 4, "count": 10, "fleet": {4: 1, 3: 2, 2: 3, 1: 4}},
            {
                "size": 10,
                "hints": 5,
                "count": 10,
                "fleet": {5: 1, 4: 1, 3: 2, 2: 3, 1: 4},
            },
            {
                "size": 12,
                "hints": 6,
                "count": 10,
                "fleet": {5: 1, 4: 2, 3: 3, 2: 4, 1: 5},
            },
            {
                "size": 15,
                "hints": 8,
                "count": 10,
                "fleet": {6: 1, 5: 2, 4: 3, 3: 4, 2: 5, 1: 6},
            },
            # Hardest Puzzles
            {
                "size": 10,
                "hints": 2,
                "count": 5,
                "fleet": {5: 1, 4: 1, 3: 2, 2: 3, 1: 4},
            },
            {
                "size": 10,
                "hints": 0,
                "count": 5,
                "fleet": {5: 1, 4: 1, 3: 2, 2: 3, 1: 4},
            },
            {
                "size": 12,
                "hints": 2,
                "count": 5,
                "fleet": {5: 1, 4: 2, 3: 3, 2: 4, 1: 5},
            },
            {
                "size": 12,
                "hints": 0,
                "count": 5,
                "fleet": {5: 1, 4: 2, 3: 3, 2: 4, 1: 5},
            },
            {
                "size": 15,
                "hints": 2,
                "count": 5,
                "fleet": {6: 1, 5: 2, 4: 3, 3: 4, 2: 5, 1: 6},
            },
            {
                "size": 15,
                "hints": 0,
                "count": 5,
                "fleet": {6: 1, 5: 2, 4: 3, 3: 4, 2: 5, 1: 6},
            },
        ]

        with open(filename, "w") as f:
            id_counter = 1
            for config in configs:
                print(f"Generating {config['size']}x{config['size']} with {config['hints']} hints...")
                successes = 0
                while successes < config["count"]:
                    grid = generate_valid_board(config["size"], config["fleet"])
                    if grid:
                        prolog_str = format_as_prolog(
                            id_counter,
                            config["size"],
                            config["fleet"],
                            grid,
                            config["hints"],
                        )
                        f.write(prolog_str + "\n")
                        id_counter += 1
                        successes += 1

        print(f"\nSuccessfully generated {id_counter - 1} scalable puzzles into '{filename}'!")


if __name__ == "__main__":
    import sys

    filename = "data/scalable_puzzles.txt"

    # Check for --dynamic flag (default is STATIC)
    use_dynamic = "--dynamic" in sys.argv

    if use_dynamic:
        print("Running in DYNAMIC mode (scaled fleets based on grid size)")
        generate_dataset(filename, dynamic=True)
    else:
        print("Running in STATIC mode (fixed fleet configurations)")
        generate_dataset(filename, dynamic=False)
