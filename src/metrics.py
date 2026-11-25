from src.loader import load_csp
from src.waltz import waltz, print_result
from src.ac3 import AC3Stats
from src.arcs import Arc
from src.revise import revise


def test_constraint_count():

    domains = {
        "A": [(0,), (1,)],
        "B": [(0,), (1,)]
    }

    arc = Arc("A", "B", "e1", 0, 0)
    stats = AC3Stats()

    removed = revise(domains, arc, stats)

    assert removed == 0
    assert stats.constraint_checks == 3

    print("TEST 1 - Exact constraint counting")
    print("Expected checks: 3")
    print("Actual checks:", stats.constraint_checks)


def run_case(name, fixed_edges, expected_status):

    print("\n" + name)

    csp = load_csp("instances/cube.json")

    for edge_id, label in fixed_edges.items():
        csp.edges[edge_id].domain = (label,)

    solution, stats = waltz(csp)

    print_result(solution, stats)

    assert stats.status == expected_status
    assert stats.constraint_checks > 0
    assert stats.decided_by_propagation
    assert stats.decisions == 0

    assert stats.solved_by_propagation == (
        solution is not None
    )

    return stats


if __name__ == "__main__":

    test_constraint_count()

    results = []

    results.append(
        run_case(
            "TEST 2 - All edges open",
            {},
            "SOLVED"
        )
    )

    results.append(
        run_case(
            "TEST 3 - e1-e6 fixed to R",
            {f"e{i}": "R" for i in range(1, 7)},
            "SOLVED"
        )
    )

    results.append(
        run_case(
            "TEST 4 - e7 fixed to minus",
            {"e7": "-"},
            "UNSAT"
        )
    )

    decided = sum(
        s.decided_by_propagation for s in results
    )

    percentage = 100 * decided / len(results)

    average_checks = sum(
        s.constraint_checks for s in results
    ) / len(results)

    print("\nMETRICS SUMMARY")
    print("Total instances:", len(results))
    print("Decided by propagation:", decided)
    print(f"Propagation decision rate: {percentage:.2f}%")
    print(f"Average constraint checks: {average_checks:.2f}")

    assert percentage == 100.0

    print("\nAll metrics tests passed!")
