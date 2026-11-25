from dataclasses import dataclass
from time import perf_counter

from src.loader import load_csp
from src.domains import build_domains
from src.arcs import Arc, build_arcs
from src.ac3 import ac3


@dataclass
class WaltzStats:
    search_nodes: int = 0
    decisions: int = 0
    backtracks: int = 0
    revise_calls: int = 0
    constraint_checks: int = 0
    removed_tuples: int = 0
    max_queue_size: int = 0
    solved_by_propagation: bool = False
    decided_by_propagation: bool = False
    status: str = "UNSAT"
    runtime_ms: float = 0.0


def update_stats(stats, ac3_stats):
    stats.revise_calls += ac3_stats.revise_calls
    stats.constraint_checks += ac3_stats.constraint_checks
    stats.removed_tuples += ac3_stats.removed_tuples

    stats.max_queue_size = max(
        stats.max_queue_size,
        ac3_stats.max_queue_size
    )


def select_mrv(domains):
    candidates = [
        junction_id
        for junction_id, domain in domains.items()
        if len(domain) > 1
    ]

    if not candidates:
        return None

    return min(
        candidates,
        key=lambda j: len(domains[j])
    )


def waltz_search(domains, arcs, stats):

    stats.search_nodes += 1

    if any(not d for d in domains.values()):
        return None

    if all(len(d) == 1 for d in domains.values()):
        return domains

    junction_id = select_mrv(domains)

    for candidate in domains[junction_id]:

        stats.decisions += 1

        new_domains = {
            j: list(d)
            for j, d in domains.items()
        }

        new_domains[junction_id] = [candidate]

        affected_arcs = [
            arc for arc in arcs
            if arc.target == junction_id
        ]

        success, ac3_stats = ac3(
            new_domains,
            arcs,
            initial_queue=affected_arcs
        )

        update_stats(stats, ac3_stats)

        if success:
            result = waltz_search(
                new_domains, arcs, stats
            )

            if result is not None:
                return result

        stats.backtracks += 1

    return None


def extract_solution(csp, domains):
    solution = {}

    for junction_id, domain in domains.items():

        if len(domain) != 1:
            raise ValueError("Incomplete solution")

        junction = csp.get_junction(junction_id)

        for edge_id, label in zip(
            junction.edges, domain[0]
        ):
            if (
                edge_id in solution
                and solution[edge_id] != label
            ):
                raise ValueError("Inconsistent solution")

            solution[edge_id] = label

    return solution


def waltz(csp):

    start = perf_counter()
    stats = WaltzStats()

    domains = build_domains(csp)
    arcs = build_arcs(csp)

    success, ac3_stats = ac3(domains, arcs)

    update_stats(stats, ac3_stats)

    solution = None

    if not success:
        stats.decided_by_propagation = True

    if success:

        if all(len(d) == 1 for d in domains.values()):
            stats.solved_by_propagation = True
            stats.decided_by_propagation = True

        result = waltz_search(
            domains, arcs, stats
        )

        if result is not None:
            solution = extract_solution(csp, result)

    stats.status = "SOLVED" if solution is not None else "UNSAT"

    stats.runtime_ms = (
        perf_counter() - start
    ) * 1000

    return solution, stats


def print_result(solution, stats):

    print("Solved:", solution is not None)

    if solution is not None:
        print("Solution:", solution)

    print("Search nodes:", stats.search_nodes)
    print("Decisions:", stats.decisions)
    print("Backtracks:", stats.backtracks)
    print("REVISE calls:", stats.revise_calls)
    print("Constraint checks:", stats.constraint_checks)
    print("Status:", stats.status)
    print("Decided by propagation:", stats.decided_by_propagation)
    print("Removed tuples:", stats.removed_tuples)
    print("Max queue size:", stats.max_queue_size)
    print(
        "Solved by propagation:",
        stats.solved_by_propagation
    )
    print(f"Runtime: {stats.runtime_ms:.3f} ms")


if __name__ == "__main__":

    print("TEST 1 - All edges open")

    csp = load_csp("instances/cube.json")

    solution, stats = waltz(csp)
    print_result(solution, stats)

    assert solution is not None
    assert len(solution) == 9
    assert stats.solved_by_propagation
    assert stats.decisions == 0

    for i in range(1, 7):
        assert solution[f"e{i}"] == "R"

    for i in range(7, 10):
        assert solution[f"e{i}"] == "+"

    print("\nTEST 2 - e1-e6 fixed to R")

    csp = load_csp("instances/cube.json")

    for i in range(1, 7):
        csp.edges[f"e{i}"].domain = ("R",)

    solution, stats = waltz(csp)
    print_result(solution, stats)

    assert solution is not None
    assert stats.solved_by_propagation

    print("\nTEST 3 - e7 fixed to minus")

    csp = load_csp("instances/cube.json")
    csp.edges["e7"].domain = ("-",)

    solution, stats = waltz(csp)
    print_result(solution, stats)

    assert solution is None

    print("\nTEST 4 - MRV selection")

    domains = {
        "A": [(0,), (1,), (2,)],
        "B": [(0,), (1,)],
        "C": [(0,)]
    }

    selected = select_mrv(domains)

    print("Selected junction:", selected)

    assert selected == "B"

    print("\nTEST 5 - Search with multiple values")

    domains = {
        "A": [(0,), (1,)],
        "B": [(0,), (1,)]
    }

    arcs = [
        Arc("A", "B", "e1", 0, 0),
        Arc("B", "A", "e1", 0, 0)
    ]

    stats = WaltzStats()

    result = waltz_search(domains, arcs, stats)

    print("Result:", result)
    print("Decisions:", stats.decisions)
    print("Search nodes:", stats.search_nodes)

    assert result is not None
    assert result["A"] == result["B"]
    assert stats.decisions > 0
    assert len(domains["A"]) == 2

    print("\nTEST 6 - Backtracking on odd cycle")

    domains = {
        "A": [(0, 1), (1, 0)],
        "B": [(0, 1), (1, 0)],
        "C": [(0, 1), (1, 0)]
    }

    arcs = [
        Arc("A", "B", "e1", 1, 0),
        Arc("B", "A", "e1", 0, 1),
        Arc("B", "C", "e2", 1, 0),
        Arc("C", "B", "e2", 0, 1),
        Arc("C", "A", "e3", 1, 0),
        Arc("A", "C", "e3", 0, 1)
    ]

    success, _ = ac3(domains, arcs)

    assert success is True

    stats = WaltzStats()

    result = waltz_search(domains, arcs, stats)

    print("Initially arc consistent:", success)
    print("Result:", result)
    print("Decisions:", stats.decisions)
    print("Backtracks:", stats.backtracks)

    assert result is None
    assert stats.backtracks == 2

    print("\nAll Waltz tests passed!")
