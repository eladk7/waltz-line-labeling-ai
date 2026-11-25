from src.loader import load_csp
from src.domains import build_domains
from src.waltz import waltz


def validate_assignment(csp, assignment):

    if set(assignment) != set(csp.edges):
        raise ValueError(
            "Assignment must contain exactly all edges"
        )

    for edge_id, edge in csp.edges.items():

        if assignment[edge_id] not in edge.domain:
            raise ValueError(
                f"Invalid label for edge {edge_id}"
            )


def junction_violations(csp, assignment, domains=None):

    validate_assignment(csp, assignment)

    if domains is None:
        domains = build_domains(csp)

    violations = {}

    for junction_id, junction in csp.junctions.items():

        labels = tuple(
            assignment[edge_id]
            for edge_id in junction.edges
        )

        violations[junction_id] = int(
            labels not in domains[junction_id]
        )

    return violations


def objective(csp, assignment, domains=None):

    violations = junction_violations(
        csp, assignment, domains
    )

    return sum(violations.values())


def is_solution(csp, assignment):

    try:
        return objective(csp, assignment) == 0

    except ValueError:
        return False


def print_validation(csp, assignment):

    violations = junction_violations(
        csp, assignment
    )

    for junction_id, violation in violations.items():

        status = "ILLEGAL" if violation else "LEGAL"

        print(f"{junction_id}: {status}")

    print("h(s):", sum(violations.values()))
    print("Valid solution:", is_solution(csp, assignment))


if __name__ == "__main__":

    csp = load_csp("instances/cube.json")

    print("TEST 1 - Waltz solution")

    solution, stats = waltz(csp)

    assert solution is not None

    print_validation(csp, solution)

    assert objective(csp, solution) == 0
    assert is_solution(csp, solution)

    print("\nTEST 2 - Change one edge")

    modified = solution.copy()
    modified["e7"] = "-"

    print_validation(csp, modified)

    assert objective(csp, modified) == 2
    assert not is_solution(csp, modified)

    print("\nTEST 3 - All edges positive")

    all_positive = {
        edge_id: "+"
        for edge_id in csp.edges
    }

    print_validation(csp, all_positive)

    assert objective(csp, all_positive) == 6
    assert not is_solution(csp, all_positive)

    print("\nTEST 4 - Incomplete assignment")

    incomplete = solution.copy()
    del incomplete["e1"]

    assert not is_solution(csp, incomplete)

    print("Incomplete assignment rejected")

    print("\nTEST 5 - Invalid label")

    invalid = solution.copy()
    invalid["e1"] = "X"

    assert not is_solution(csp, invalid)

    print("Invalid label rejected")

    print("\nTEST 6 - Fixed edge violation")

    csp.edges["e1"].domain = ("R",)

    invalid = solution.copy()
    invalid["e1"] = "+"

    assert not is_solution(csp, invalid)

    print("Fixed edge violation rejected")

    print("\nTEST 7 - Valid fixed edge assignment")

    assert is_solution(csp, solution)

    print("Valid fixed edge assignment accepted")

    print("\nAll validation tests passed!")
