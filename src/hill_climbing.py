import random

from src.loader import load_csp
from src.domains import build_domains
from src.validation import (
    validate_assignment,
    objective
)


def random_assignment(csp, rng):

    assignment = {}

    for edge_id, edge in csp.edges.items():

        if not edge.domain:
            raise ValueError(
                f"Empty domain for edge {edge_id}"
            )

        assignment[edge_id] = rng.choice(edge.domain)

    return assignment


if __name__ == "__main__":

    print("TEST 1 - Random complete assignment")

    csp = load_csp("instances/cube.json")
    rng = random.Random(42)

    assignment = random_assignment(csp, rng)

    validate_assignment(csp, assignment)

    print("Assignment:", assignment)
    print("Total edges:", len(assignment))
    print("h(s):", objective(csp, assignment))

    assert len(assignment) == 9
    assert 0 <= objective(csp, assignment) <= 7

    print("\nTEST 2 - Fixed edges")

    for i in range(1, 7):
        csp.edges[f"e{i}"].domain = ("R",)

    for _ in range(100):

        assignment = random_assignment(csp, rng)

        validate_assignment(csp, assignment)

        for i in range(1, 7):
            assert assignment[f"e{i}"] == "R"

    print("100 random assignments generated")
    print("All fixed edges preserved")

    print("\nTEST 3 - Reproducibility")

    csp = load_csp("instances/cube.json")

    first = random_assignment(
        csp, random.Random(42)
    )

    second = random_assignment(
        csp, random.Random(42)
    )

    assert first == second

    print("Same seed produces same assignment")

    print("\nTEST 4 - Label distribution")

    rng = random.Random(42)

    counts = {
        label: 0
        for label in csp.edges["e1"].domain
    }

    samples = 10000

    for _ in range(samples):

        assignment = random_assignment(csp, rng)

        counts[assignment["e1"]] += 1

    for label, count in counts.items():

        percentage = 100 * count / samples

        print(
            f"{label}: {count} "
            f"({percentage:.2f}%)"
        )

        assert 22 <= percentage <= 28

    print("\nTEST 5 - Empty domain")

    csp.edges["e1"].domain = ()

    try:
        random_assignment(csp, rng)

    except ValueError:
        print("Empty domain correctly rejected")

    else:
        raise AssertionError(
            "Empty domain was not rejected"
        )

    print("\nAll random assignment tests passed!")

def generate_neighbors(csp, assignment):

    validate_assignment(csp, assignment)

    for edge_id, edge in csp.edges.items():

        current_label = assignment[edge_id]

        for new_label in edge.domain:

            if new_label == current_label:
                continue

            neighbor = assignment.copy()
            neighbor[edge_id] = new_label

            yield neighbor


def count_neighbors(csp):

    return sum(
        len(edge.domain) - 1
        for edge in csp.edges.values()
    )


if __name__ == "__main__":

    print("\nTEST 1 - All edges open")

    csp = load_csp("instances/cube.json")
    rng = random.Random(42)

    assignment = random_assignment(csp, rng)

    neighbors = list(
        generate_neighbors(csp, assignment)
    )

    print("Original assignment:", assignment)
    print("Expected neighbors:", count_neighbors(csp))
    print("Actual neighbors:", len(neighbors))

    assert len(neighbors) == 27

    print("\nTEST 2 - Exactly one changed edge")

    original = assignment.copy()

    for neighbor in neighbors:

        validate_assignment(csp, neighbor)

        changed = [
            edge_id
            for edge_id in assignment
            if assignment[edge_id] != neighbor[edge_id]
        ]

        assert len(changed) == 1

    assert assignment == original

    print("All 27 neighbors differ by exactly one edge")
    print("Original assignment preserved")

    print("\nTEST 3 - No duplicate neighbors")

    unique = {
        tuple(sorted(neighbor.items()))
        for neighbor in neighbors
    }

    assert len(unique) == len(neighbors)

    print("Unique neighbors:", len(unique))

    print("\nTEST 4 - Six fixed edges")

    for i in range(1, 7):
        csp.edges[f"e{i}"].domain = ("R",)

    assignment = random_assignment(csp, rng)

    neighbors = list(
        generate_neighbors(csp, assignment)
    )

    print("Expected neighbors:", count_neighbors(csp))
    print("Actual neighbors:", len(neighbors))

    assert len(neighbors) == 9

    for neighbor in neighbors:

        validate_assignment(csp, neighbor)

        for i in range(1, 7):
            assert neighbor[f"e{i}"] == "R"

    print("All fixed edges preserved")

    print("\nTEST 5 - All edges fixed")

    for edge_id, edge in csp.edges.items():
        edge.domain = (assignment[edge_id],)

    neighbors = list(
        generate_neighbors(csp, assignment)
    )

    print("Expected neighbors:", count_neighbors(csp))
    print("Actual neighbors:", len(neighbors))

    assert len(neighbors) == 0

    print("\nTEST 6 - Mixed domain sizes")

    csp = load_csp("instances/cube.json")

    csp.edges["e1"].domain = ("R", "L")
    csp.edges["e2"].domain = ("+", "-", "R")
    csp.edges["e3"].domain = ("R",)

    assignment = random_assignment(csp, rng)

    neighbors = list(
        generate_neighbors(csp, assignment)
    )

    print("Expected neighbors:", count_neighbors(csp))
    print("Actual neighbors:", len(neighbors))

    assert len(neighbors) == 21

    for neighbor in neighbors:
        validate_assignment(csp, neighbor)

    print("\nAll neighbor generation tests passed!")
