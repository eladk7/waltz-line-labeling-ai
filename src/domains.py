
from src.catalog import get_catalog
from src.labels import local_to_global
from src.loader import load_csp


def build_junction_domain(csp, junction_id):
    junction = csp.get_junction(junction_id)

    catalog = get_catalog(
        junction.type,
        junction.reflection
    )

    domain = []

    for local_tuple in catalog:
        global_tuple = []
        valid = True

        for edge_id, local_label in zip(
            junction.edges, local_tuple
        ):
            edge = csp.get_edge(edge_id)

            is_first = edge.is_first_endpoint(
                junction_id
            )

            global_label = local_to_global(
                local_label, is_first
            )

            if global_label not in edge.domain:
                valid = False
                break

            global_tuple.append(global_label)

        if valid:
            domain.append(tuple(global_tuple))

    return domain


def build_domains(csp):
    return {
        junction_id: build_junction_domain(
            csp, junction_id
        )
        for junction_id in csp.junctions
    }


def print_domains(domains):
    for junction_id, domain in domains.items():
        print(f"{junction_id}: {len(domain)} tuples")
        print(f"   {domain}")

    total = sum(len(d) for d in domains.values())
    print(f"Total tuples: {total}")


if __name__ == "__main__":

    # Test 1: All edges open
    csp = load_csp("instances/cube.json")

    print("TEST 1 - All edges open")

    domains = build_domains(csp)
    print_domains(domains)

    assert sum(len(d) for d in domains.values()) == 32

    # Test 2: e1-e6 fixed to R
    csp = load_csp("instances/cube.json")

    for i in range(1, 7):
        csp.edges[f"e{i}"].domain = ("R",)

    print("\nTEST 2 - e1-e6 fixed to R")

    domains = build_domains(csp)
    print_domains(domains)

    assert domains["A"] == [("R", "R")]
    assert domains["B"] == [("R", "R", "+")]
    assert domains["C"] == [("R", "R")]
    assert domains["D"] == [("R", "R", "+")]
    assert domains["E"] == [("R", "R")]
    assert domains["F"] == [("R", "R", "+")]
    assert len(domains["O"]) == 5

    assert sum(len(d) for d in domains.values()) == 11

    # Test 3: e7 fixed to minus
    csp = load_csp("instances/cube.json")
    csp.edges["e7"].domain = ("-",)

    print("\nTEST 3 - e7 fixed to minus")

    domains = build_domains(csp)
    print_domains(domains)

    assert len(domains["B"]) == 1
    assert len(domains["O"]) == 2

    assert sum(len(d) for d in domains.values()) == 27

    print("\nAll domain tests passed!")
