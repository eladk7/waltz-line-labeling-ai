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

def select_best_neighbor(
    csp, assignment, domains,
    violations, current_h, rng
):

    best_h = float("inf")
    best_moves = []
    evaluated = 0

    for edge_id, edge in csp.edges.items():

        for new_label in edge.domain:

            if new_label == assignment[edge_id]:
                continue

            delta, updates = delta_h(
                csp, assignment, domains,
                violations, edge_id, new_label
            )

            evaluated += 1

            neighbor_h = current_h + delta

            move = (
                edge_id,
                new_label,
                delta,
                updates
            )

            if neighbor_h < best_h:

                best_h = neighbor_h
                best_moves = [move]

            elif neighbor_h == best_h:

                best_moves.append(move)

    if not best_moves:
        return None, evaluated

    return rng.choice(best_moves), evaluated


if __name__ == "__main__":

    csp = load_csp("instances/cube.json")
    domains = build_domains(csp)

    rng = random.Random(42)

    assignment = random_assignment(csp, rng)

    violations, h = initialize_state(
        csp, assignment, domains
    )

    print("\nTEST 1 - Best neighbor selection")

    move, evaluated = select_best_neighbor(
        csp, assignment, domains,
        violations, h, rng
    )

    edge_id, new_label, delta, updates = move

    best_h = h + delta

    print("Current h:", h)
    print("Selected edge:", edge_id)
    print("New label:", new_label)
    print("Delta h:", delta)
    print("Best neighbor h:", best_h)
    print("Neighbors evaluated:", evaluated)

    assert evaluated == 27

    print("\nTEST 2 - Compare with full search")

    neighbors = list(
        generate_neighbors(csp, assignment)
    )

    expected_best_h = min(
        objective(csp, neighbor)
        for neighbor in neighbors
    )

    print("Incremental best h:", best_h)
    print("Full search best h:", expected_best_h)

    assert best_h == expected_best_h

    print("\nTEST 3 - Original state preserved")

    original = assignment.copy()
    original_violations = violations.copy()

    select_best_neighbor(
        csp, assignment, domains,
        violations, h, rng
    )

    assert assignment == original
    assert violations == original_violations

    print("Original assignment preserved")
    print("Original violations preserved")

    print("\nTEST 4 - Random tie-breaking")

    optimal_moves = set()

    for edge_id, edge in csp.edges.items():

        for label in edge.domain:

            if label == assignment[edge_id]:
                continue

            delta, updates = delta_h(
                csp, assignment, domains,
                violations, edge_id, label
            )

            if h + delta == expected_best_h:
                optimal_moves.add((edge_id, label))

    selected_moves = set()

    for seed in range(1000):

        move, evaluated = select_best_neighbor(
            csp, assignment, domains,
            violations, h, random.Random(seed)
        )

        edge_id, label, delta, updates = move

        assert h + delta == expected_best_h

        selected_moves.add((edge_id, label))

    print("Optimal moves:", sorted(optimal_moves))
    print("Selected moves:", sorted(selected_moves))
    print("Random selections tested: 1000")

    assert selected_moves == optimal_moves

    print("\nTEST 5 - Fixed edges")

    fixed_edges = list(csp.edges)[:6]

    for edge_id in fixed_edges:

        csp.edges[edge_id].domain = (
            assignment[edge_id],
        )

    domains = build_domains(csp)

    violations, h = initialize_state(
        csp, assignment, domains
    )

    move, evaluated = select_best_neighbor(
        csp, assignment, domains,
        violations, h, rng
    )

    assert evaluated == 9
    assert move[0] not in fixed_edges

    print("Neighbors evaluated:", evaluated)
    print("All fixed edges preserved")

    print("\nTEST 6 - No available neighbors")

    for edge_id in csp.edges:

        csp.edges[edge_id].domain = (
            assignment[edge_id],
        )

    domains = build_domains(csp)

    violations, h = initialize_state(
        csp, assignment, domains
    )

    move, evaluated = select_best_neighbor(
        csp, assignment, domains,
        violations, h, rng
    )

    assert move is None
    assert evaluated == 0

    print("Neighbors evaluated:", evaluated)
    print("Selected move:", move)

    print("\nTEST 7 - Reproducibility")

    csp = load_csp("instances/cube.json")
    domains = build_domains(csp)

    violations, h = initialize_state(
        csp, assignment, domains
    )

    result1 = select_best_neighbor(
        csp, assignment, domains,
        violations, h, random.Random(42)
    )

    result2 = select_best_neighbor(
        csp, assignment, domains,
        violations, h, random.Random(42)
    )

    assert result1 == result2

    print("Same seed produces same selected move")

    print("\nAll best neighbor tests passed!")

def random_restart_hc(csp, budget=100, seed=42):

    if budget <= 0:
        raise ValueError("Budget must be positive")

    rng = random.Random(seed)
    domains = build_domains(csp)

    best = None
    best_h = float("inf")

    for _ in range(budget):

        assignment = random_assignment(csp, rng)

        violations, h = initialize_state(
            csp, assignment, domains
        )

        if h < best_h:
            best = assignment.copy()
            best_h = h

        while True:

            # Check whether the current state is a solution
            if h == 0:
                return assignment.copy()

            # Evaluate all neighbors
            move, evaluated = select_best_neighbor(
                csp,
                assignment,
                domains,
                violations,
                h,
                rng
            )

            # No available neighbors
            if move is None:
                break

            edge_id, new_label, delta, updates = move

            # Local minimum or plateau
            if delta >= 0:
                break

            # Move to a strictly improving neighbor
            h = apply_move(
                assignment,
                violations,
                h,
                edge_id,
                new_label,
                delta,
                updates
            )

            # Preserve the best assignment found
            if h < best_h:
                best = assignment.copy()
                best_h = h

    # Budget exhausted: return the best assignment
    return best


if __name__ == "__main__":

    print("\nTEST 1 - Random restart hill climbing")

    csp = load_csp("instances/cube.json")

    result = random_restart_hc(
        csp, budget=100, seed=42
    )

    result_h = objective(csp, result)

    print("Best assignment:", result)
    print("Best h:", result_h)
    print("Solution found:", result_h == 0)

    assert result_h == 0

    print("\nTEST 2 - Compare with Waltz")

    solution, stats = waltz(csp)

    assert solution is not None
    assert objective(csp, solution) == 0
    assert objective(csp, result) == 0

    print("Waltz h:", objective(csp, solution))
    print("Hill climbing h:", result_h)

    print("\nTEST 3 - Reproducibility")

    result1 = random_restart_hc(
        csp, budget=100, seed=42
    )

    result2 = random_restart_hc(
        csp, budget=100, seed=42
    )

    assert result1 == result2

    print("Same seed produces same result")

    print("\nTEST 4 - Fixed edges")

    csp = load_csp("instances/cube.json")

    fixed_edges = [
        "e1", "e2", "e3",
        "e4", "e5", "e6"
    ]

    for edge_id in fixed_edges:
        csp.edges[edge_id].domain = ("R",)

    result = random_restart_hc(
        csp, budget=100, seed=42
    )

    for edge_id in fixed_edges:
        assert result[edge_id] == "R"

    print("All fixed edges preserved")
    print("Best h:", objective(csp, result))

    assert objective(csp, result) == 0

    print("\nTEST 5 - Already solved initial state")

    csp = load_csp("instances/cube.json")

    solution, stats = waltz(csp)

    for edge_id, label in solution.items():
        csp.edges[edge_id].domain = (label,)

    result = random_restart_hc(
        csp, budget=1, seed=42
    )

    assert result == solution
    assert objective(csp, result) == 0

    print("Initial assignment is a solution")
    print("Best h:", objective(csp, result))

    print("\nTEST 6 - Unsatisfiable instance")

    csp = load_csp("instances/cube.json")

    csp.edges["e7"].domain = ("-",)

    result = random_restart_hc(
        csp, budget=100, seed=42
    )

    result_h = objective(csp, result)

    assert result is not None
    assert result["e7"] == "-"
    assert result_h > 0

    print("Best assignment:", result)
    print("Best h:", result_h)
    print("Solution found:", result_h == 0)
    print("Budget exhausted - not a proof of UNSAT")

    print("\nTEST 7 - All edges fixed, no solution")

    csp = load_csp("instances/cube.json")

    for edge in csp.edges.values():
        edge.domain = ("+",)

    result = random_restart_hc(
        csp, budget=10, seed=42
    )

    assert result is not None
    assert objective(csp, result) == 6

    print("Available neighbors:", count_neighbors(csp))
    print("Best h:", objective(csp, result))
    print("Best assignment returned")

    print("\nTEST 8 - Budget comparison")

    csp = load_csp("instances/cube.json")

    previous_h = float("inf")

    for budget in [1, 5, 10, 50, 100]:

        result = random_restart_hc(
            csp, budget=budget, seed=42
        )

        result_h = objective(csp, result)

        print(
            "Budget:", budget,
            "| Best h:", result_h
        )

        assert result_h <= previous_h

        previous_h = result_h

    print("\nTEST 9 - Invalid budget")

    try:

        random_restart_hc(
            csp, budget=0, seed=42
        )

    except ValueError:
        print("Invalid budget correctly rejected")

    else:
        raise AssertionError(
            "Invalid budget was accepted"
        )

    print("\nAll random restart HC tests passed!")
