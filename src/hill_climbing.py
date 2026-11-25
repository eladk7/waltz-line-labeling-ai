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

from src.validation import junction_violations
from src.waltz import waltz


def initialize_state(csp, assignment, domains):

    violations = junction_violations(
        csp, assignment, domains
    )

    h = sum(violations.values())

    return violations, h


def evaluate_junction(
    csp, assignment, domains, junction_id,
    changed_edge=None, new_label=None
):

    junction = csp.junctions[junction_id]

    labels = tuple(
        new_label if edge_id == changed_edge
        else assignment[edge_id]
        for edge_id in junction.edges
    )

    return int(labels not in domains[junction_id])


def delta_h(
    csp, assignment, domains, violations,
    edge_id, new_label
):

    edge = csp.edges[edge_id]

    if new_label not in edge.domain:
        raise ValueError("Label outside edge domain")

    if new_label == assignment[edge_id]:
        raise ValueError("Move must change the label")

    affected = {edge.u, edge.v}

    updates = {}

    for junction_id in affected:

        updates[junction_id] = evaluate_junction(
            csp,
            assignment,
            domains,
            junction_id,
            edge_id,
            new_label
        )

    delta = sum(
        updates[junction_id] - violations[junction_id]
        for junction_id in affected
    )

    return delta, updates


def apply_move(
    assignment, violations, current_h,
    edge_id, new_label, delta, updates
):

    assignment[edge_id] = new_label

    violations.update(updates)

    return current_h + delta


if __name__ == "__main__":

    csp = load_csp("instances/cube.json")
    domains = build_domains(csp)

    print("\nTEST 1 - Initialize state")

    rng = random.Random(42)

    assignment = random_assignment(csp, rng)

    violations, h = initialize_state(
        csp, assignment, domains
    )

    print("Junction violations:", violations)
    print("Cached h:", h)
    print("Full objective:", objective(csp, assignment))

    assert h == objective(csp, assignment)
    assert len(violations) == 7

    print("\nTEST 2 - Delta h for all neighbors")

    checked = 0
    original = assignment.copy()
    original_violations = violations.copy()

    for edge_id, edge in csp.edges.items():

        for new_label in edge.domain:

            if new_label == assignment[edge_id]:
                continue

            delta, updates = delta_h(
                csp, assignment, domains,
                violations, edge_id, new_label
            )

            neighbor = assignment.copy()
            neighbor[edge_id] = new_label

            full_h = objective(csp, neighbor)

            assert h + delta == full_h
            assert len(updates) == 2
            assert -2 <= delta <= 2

            checked += 1

    assert checked == 27
    assert assignment == original
    assert violations == original_violations

    print("Neighbors checked:", checked)
    print("All delta values match full objective")
    print("Original state preserved")

    print("\nTEST 3 - Known Waltz solution")

    solution, stats = waltz(csp)

    assert solution is not None

    assignment = solution.copy()

    violations, h = initialize_state(
        csp, assignment, domains
    )

    assert h == 0

    delta, updates = delta_h(
        csp, assignment, domains,
        violations, "e7", "-"
    )

    print("Original h:", h)
    print("Delta h:", delta)
    print("Affected junctions:", sorted(updates))

    assert delta == 2
    assert set(updates) == {"B", "O"}

    h = apply_move(
        assignment, violations, h,
        "e7", "-", delta, updates
    )

    print("Updated h:", h)

    assert h == 2
    assert h == objective(csp, assignment)

    print("\nTEST 4 - Reverse move")

    delta, updates = delta_h(
        csp, assignment, domains,
        violations, "e7", "+"
    )

    assert delta == -2

    h = apply_move(
        assignment, violations, h,
        "e7", "+", delta, updates
    )

    print("Delta h:", delta)
    print("Updated h:", h)

    assert h == 0
    assert assignment == solution

    print("\nTEST 5 - 1000 random moves")

    assignment = random_assignment(csp, rng)

    violations, h = initialize_state(
        csp, assignment, domains
    )

    for _ in range(1000):

        edge_id = rng.choice(list(csp.edges))

        alternatives = [
            label
            for label in csp.edges[edge_id].domain
            if label != assignment[edge_id]
        ]

        new_label = rng.choice(alternatives)

        delta, updates = delta_h(
            csp, assignment, domains,
            violations, edge_id, new_label
        )

        h = apply_move(
            assignment, violations, h,
            edge_id, new_label, delta, updates
        )

        assert h == objective(csp, assignment)

        assert violations == junction_violations(
            csp, assignment, domains
        )

    print("1000 incremental updates verified")

    print("\nTEST 6 - Fixed edge protection")

    csp.edges["e1"].domain = (
        assignment["e1"],
    )

    domains = build_domains(csp)

    violations, h = initialize_state(
        csp, assignment, domains
    )

    invalid_label = next(
        label
        for label in ("+", "-", "R", "L")
        if label != assignment["e1"]
    )

    try:

        delta_h(
            csp, assignment, domains,
            violations, "e1", invalid_label
        )

    except ValueError:
        print("Illegal fixed-edge move rejected")

    else:
        raise AssertionError(
            "Fixed-edge violation not rejected"
        )

    print("\nTEST 7 - Junction evaluation savings")

    csp = load_csp("instances/cube.json")

    domains = build_domains(csp)

    assignment = random_assignment(csp, rng)

    violations, h = initialize_state(
        csp, assignment, domains
    )

    full_checks = 0
    local_checks = 0

    for edge_id, edge in csp.edges.items():

        for new_label in edge.domain:

            if new_label == assignment[edge_id]:
                continue

            delta, updates = delta_h(
                csp, assignment, domains,
                violations, edge_id, new_label
            )

            neighbor = assignment.copy()
            neighbor[edge_id] = new_label

            assert h + delta == objective(
                csp, neighbor
            )

            full_checks += len(csp.junctions)
            local_checks += len(updates)

    reduction = 100 * (
        1 - local_checks / full_checks
    )

    print("Full junction evaluations:", full_checks)
    print("Local junction evaluations:", local_checks)
    print(f"Reduction: {reduction:.2f}%")

    assert full_checks == 189
    assert local_checks == 54

    print("\nAll delta h tests passed!")
