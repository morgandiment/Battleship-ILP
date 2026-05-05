def generate_ship_candidates(size, fleet_spec, hints=None, row_tallies=None, col_tallies=None):
    """
    Generates all valid ship placements for the given fleet.
    Optionally pruned by water hints and zero-tally row/columns.
    If pruning arguments omitted, all placements are generated.
    Returns a list of candidate dictionaries.
    """
    candidates = []
    candidate_id = 0

    water_cells = {coord for coord, val in (hints or {}).items() if val == 0}
    zero_rows = {i for i, t in enumerate(row_tallies if row_tallies is not None else []) if t == 0}
    zero_cols = {j for j, t in enumerate(col_tallies if col_tallies is not None else []) if t == 0}

    def is_pruned(cells):
        if any(cell in water_cells for cell in cells):
            return True
        if any(r in zero_rows for r, _ in cells):
            return True
        if any(c in zero_cols for _, c in cells):
            return True
        return False

    # Iterate through each ship type/length in the fleet
    for length, count in fleet_spec.items():
        # Horizontal first
        for r in range(size):
            for c in range(size - length + 1):
                # Valid horizontal ship from (r, c) to (r, c+length-1)
                cells = [(r, c + k) for k in range(length)]
                if is_pruned(cells):
                    continue
                candidates.append(
                    {
                        "id": candidate_id,
                        "length": length,
                        "orientation": "H",
                        "row": r,
                        "col": c,
                        "cells": cells,
                    }
                )
                candidate_id += 1

        # Vertical
        # Length 1 are skipped as orientation does not matter
        if length > 1:
            for c in range(size):
                for r in range(size - length + 1):
                    # Valid vertical ship from (r, c) to (r+length-1, c)
                    cells = [(r + k, c) for k in range(length)]
                    if is_pruned(cells):
                        continue
                    candidates.append(
                        {
                            "id": candidate_id,
                            "length": length,
                            "orientation": "V",
                            "row": r,
                            "col": c,
                            "cells": cells,
                        }
                    )
                    candidate_id += 1

    return candidates


# Quick test with a standard fleet
if __name__ == "__main__":
    fleet = {4: 1, 3: 2, 2: 3, 1: 4}
    candidates = generate_ship_candidates(10, fleet)
    print(f"Generated {len(candidates)} valid ship positions.")
