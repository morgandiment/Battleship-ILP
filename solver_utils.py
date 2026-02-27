import numpy as np

def generate_ship_candidates(size, fleet_spec):
    """
    Generates all valid ship placements for the given fleet.
    Returns a list of candidate dictionaries.
    """
    candidates = []
    candidate_id = 0

    # Iterate through each ship type/length in the fleet
    for length, count in fleet_spec.items():
        # Horizontal first
        for r in range(size):
            for c in range(size - length + 1):
                # Valid horizontal ship from (r, c) to (r, c+length-1)
                cells = [(r, c + k) for k in range(length)]
                candidates.append({
                    'id': candidate_id,
                    'length': length,
                    'orientation': 'H',
                    'row': r,
                    'col': c,
                    'cells': cells
                })
                candidate_id += 1

        # Vertical
        # Length 1 are skipped as orientation does not matter
        if length > 1:
            for c in range(size):
                for r in range(size - length + 1):
                    # Valid vertical ship from (r, c) to (r+length-1, c)
                    cells = [(r + k, c) for k in range(length)]
                    candidates.append({
                        'id': candidate_id,
                        'length': length,
                        'orientation': 'V',
                        'row': r,
                        'col': c,
                        'cells': cells
                    })
                    candidate_id += 1

    return candidates

# Quick test with a standard fleet
if __name__ == "__main__":
    fleet = {4: 1, 3: 2, 2: 3, 1: 4}
    candidates = generate_ship_candidates(10, fleet)
    print(f"Generated {len(candidates)} valid ship positions.")
    # 580 expected