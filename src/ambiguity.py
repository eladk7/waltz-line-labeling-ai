import csv
import json
from collections import Counter
from pathlib import Path

from src.loader import load_csp
from src.validation import objective
from src.waltz_enumeration import enumerate_waltz
from src.hill_climbing import random_restart_hc
from src.genetic_algorithm import genetic_algorithm

root = Path("instances/benchmark")
manifest = json.loads(
    (root / "manifest.json").read_text(encoding="utf-8-sig")
)

rows = []

for name in ["small_triangle", "small_cube"]:
    item = next(x for x in manifest if x["name"] == name)
    csp = load_csp(root / item["file"])

    solutions, stats = enumerate_waltz(
        csp, N=10000, seed=42, timeout=10
    )

    assert stats.status == "MULTIPLE", stats.status

    def key(assignment):
        return tuple(sorted(assignment.items()))

    known = {key(s): i + 1 for i, s in enumerate(solutions)}

    print(f"\n{name}: {len(solutions)} interpretations")

    for solution, number in known.items():
        print(f"Solution {number}: {dict(solution)}")

    for method in ["HC", "GA"]:
        counts = Counter()

        for seed in range(42, 62):
            if method == "HC":
                assignment, stats = random_restart_hc(
                    csp, budget=100001, seed=seed,
                    S=10, return_stats=True,
                    max_evaluations=100000, timeout=10
                )
            else:
                assignment, stats = genetic_algorithm(
                    csp, P=100, p_c=0.8, p_m=0.02,
                    seed=seed, max_evaluations=100000,
                    timeout=10
                )

            h = objective(csp, assignment)
            number = known[key(assignment)] if h == 0 else 0
            counts[number] += 1

            rows.append({
                "instance": name,
                "method": method,
                "seed": seed,
                "solution": number,
                "best_h": h,
                "runtime_ms": stats.runtime_ms,
                "stop_reason": stats.stop_reason
            })

        print(f"\n{method}:")
        print(f"Distinct solutions: {sum(k != 0 for k in counts)}")

        for number in range(1, len(solutions) + 1):
            print(f"Solution {number}: {counts[number]}/20")

        print(f"Failed: {counts[0]}/20")

path = Path("results/ambiguity.csv")
path.parent.mkdir(exist_ok=True)

with path.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)

print(f"\nCompleted {len(rows)} runs: {path}")
