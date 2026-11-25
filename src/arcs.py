
from dataclasses import dataclass
from src.loader import load_csp


@dataclass(frozen=True)
class Arc:
    source: str
    target: str
    edge_id: str
    source_index: int
    target_index: int


def build_arcs(csp):
    arcs = []

    for edge in csp.edges.values():
        u = csp.get_junction(edge.u)
        v = csp.get_junction(edge.v)

        u_index = u.edges.index(edge.id)
        v_index = v.edges.index(edge.id)

        arcs.append(
            Arc(u.id, v.id, edge.id, u_index, v_index)
        )

        arcs.append(
            Arc(v.id, u.id, edge.id, v_index, u_index)
        )

    return arcs


if __name__ == "__main__":
    csp = load_csp("instances/cube.json")
    arcs = build_arcs(csp)

    print("Total edges:", len(csp.edges))
    print("Total directed arcs:", len(arcs))

    print("\nDirected arcs:")

    for arc in arcs:
        print(
            f"{arc.source} -> {arc.target}, "
            f"edge={arc.edge_id}, "
            f"indices=({arc.source_index}, "
            f"{arc.target_index})"
        )

    assert len(arcs) == 18
    assert len(set(arcs)) == 18

    for arc in arcs:
        reverse = Arc(
            arc.target,
            arc.source,
            arc.edge_id,
            arc.target_index,
            arc.source_index
        )

        assert reverse in arcs

    print("\nAll arc tests passed!")
