import random
from time import perf_counter

from src.loader import load_csp
from src.domains import build_domains
from src.arcs import build_arcs
from src.ac3 import ac3
from src.waltz import WaltzStats, update_stats, extract_solution
from src.validation import objective


def enumerate_waltz(csp, N=100, seed=42, timeout=10):
    if N < 1 or timeout <= 0:
        raise ValueError("Invalid search limits")

    rng = random.Random(seed)
    start = perf_counter()
    stats = WaltzStats()
    stats.max_depth = 0
    solutions = []
    stop_reason = None

    domains = build_domains(csp)
    arcs = build_arcs(csp)
    rng.shuffle(arcs)

    def cancelled():
        return perf_counter() - start >= timeout

    def search(current, depth=0):
        nonlocal stop_reason

        if cancelled():
            stop_reason = "TIME_LIMIT"
            return

        stats.max_depth = max(stats.max_depth, depth)

        if all(len(d) == 1 for d in current.values()):
            solutions.append(extract_solution(csp, current))

            if len(solutions) >= N:
                stop_reason = "SOLUTION_LIMIT"
            return

        stats.search_nodes += 1

        candidates = [j for j in current if len(current[j]) > 1]
        minimum = min(len(current[j]) for j in candidates)

        junction = rng.choice([
            j for j in candidates if len(current[j]) == minimum
        ])

        for candidate in current[junction]:
            if stop_reason:
                return

            stats.decisions += 1
            child = {j: list(d) for j, d in current.items()}
            child[junction] = [candidate]

            incoming = [a for a in arcs if a.target == junction]

            consistent, metrics = ac3(
                child, arcs, initial_queue=incoming
            )
            update_stats(stats, metrics)

            before = len(solutions)

            if consistent:
                search(child, depth + 1)

            if len(solutions) == before and not stop_reason:
                stats.backtracks += 1

    consistent, metrics = ac3(domains, arcs)
    update_stats(stats, metrics)

    if consistent:
        stats.solved_by_propagation = all(
            len(d) == 1 for d in domains.values()
        )
        search(domains)

    stats.decided_by_propagation = (
        not consistent or stats.solved_by_propagation
    )

    if stop_reason:
        stats.status = stop_reason
    elif not solutions:
        stats.status = "UNSAT"
    elif len(solutions) == 1:
        stats.status = "UNIQUE"
    else:
        stats.status = "MULTIPLE"

    stats.runtime_ms = (perf_counter() - start) * 1000

    return solutions, stats


if __name__ == "__main__":
    cases = [
        ("All edges open", {}, 4),
        ("Outer edges fixed", {
            f"e{i}": ("R",) for i in range(1, 7)
        }, 1),
        ("Contradictory edge", {"e7": ("-",)}, 0)
    ]

    for name, fixed, expected in cases:
        csp = load_csp("instances/cube.json")

        for edge, domain in fixed.items():
            csp.edges[edge].domain = domain

        solutions, stats = enumerate_waltz(csp)

        print("\nTEST:", name)
        print("Expected:", expected)
        print("Actual:", len(solutions))
        print("Status:", stats.status)
        print("Search nodes:", stats.search_nodes)
        print("Decisions:", stats.decisions)
        print("Backtracks:", stats.backtracks)
        print("Max depth:", stats.max_depth)
        print("Constraint checks:", stats.constraint_checks)
        print("Runtime ms:", round(stats.runtime_ms, 3))

        assert len(solutions) == expected

        for i, solution in enumerate(solutions, 1):
            h = objective(csp, solution)
            print(f"Solution {i}: {solution}, h={h}")
            assert h == 0

        assert len({
            tuple(sorted(s.items())) for s in solutions
        }) == expected

        if expected == 1:
            assert stats.search_nodes == 0

    csp = load_csp("instances/cube.json")
    solutions, stats = enumerate_waltz(csp, N=2)

    assert len(solutions) == 2
    assert stats.status == "SOLUTION_LIMIT"

    print("\nSolution limit test: PASSED")
    print("All enumeration tests passed!")
