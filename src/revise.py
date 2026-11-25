
from src.loader import load_csp
from src.domains import build_domains
from src.arcs import build_arcs


def revise(domains, arc, stats=None):
    source_domain = domains[arc.source]
    target_domain = domains[arc.target]

    remaining = []

    for source_tuple in source_domain:

        supported = False

        for target_tuple in target_domain:

            if stats is not None:
                stats.constraint_checks += 1

            if (
                source_tuple[arc.source_index]
                == target_tuple[arc.target_index]
            ):
                supported = True
                break

        if supported:
            remaining.append(source_tuple)

    removed = len(source_domain) - len(remaining)

    domains[arc.source] = remaining

    return removed


if __name__ == "__main__":

    csp = load_csp("instances/cube.json")

    for i in range(1, 7):
        csp.edges[f"e{i}"].domain = ("R",)

    domains = build_domains(csp)
    arcs = build_arcs(csp)

    arc = next(
        arc for arc in arcs
        if arc.source == "O"
        and arc.target == "B"
    )

    print("TEST 1 - Remove unsupported tuples")

    print("Arc:", arc.source, "->", arc.target)
    print("Shared edge:", arc.edge_id)

    print("Source before:", domains["O"])
    print("Target domain:", domains["B"])

    removed = revise(domains, arc)

    print("Removed tuples:", removed)
    print("Source after:", domains["O"])

    assert removed == 4
    assert domains["O"] == [("+", "+", "+")]

    print("\nTEST 2 - No additional removals")

    removed = revise(domains, arc)

    print("Removed tuples:", removed)

    assert removed == 0

    print("\nTEST 3 - Empty target domain")

    domains["B"] = []

    removed = revise(domains, arc)

    print("Removed tuples:", removed)
    print("Source after:", domains["O"])

    assert removed == 1
    assert domains["O"] == []

    print("\nAll revise tests passed!")
