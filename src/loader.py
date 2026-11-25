
import json

from src.models import CSP, Edge, Junction, GLOBAL_LABELS
from src.catalog import CATALOG


def load_csp(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    csp = CSP()

    # Load edges
    for item in data["edges"]:
        edge = Edge(
            id=item["id"],
            u=item["u"],
            v=item["v"],
            domain=tuple(
                item.get("domain", GLOBAL_LABELS)
            )
        )

        if edge.id in csp.edges:
            raise ValueError(f"Duplicate edge: {edge.id}")

        csp.add_edge(edge)

    # Load junctions
    for item in data["junctions"]:
        junction = Junction(
            id=item["id"],
            type=item["type"],
            edges=tuple(item["edges"]),
            x=item.get("x", 0.0),
            y=item.get("y", 0.0),
            reflection=item.get("reflection", False)
        )

        if junction.id in csp.junctions:
            raise ValueError(
                f"Duplicate junction: {junction.id}"
            )

        csp.add_junction(junction)

    validate_csp(csp)

    return csp


def validate_csp(csp):
    for edge in csp.edges.values():
        if edge.u not in csp.junctions:
            raise ValueError(f"Invalid endpoint: {edge.u}")

        if edge.v not in csp.junctions:
            raise ValueError(f"Invalid endpoint: {edge.v}")

        if edge.u == edge.v:
            raise ValueError(f"Self-loop: {edge.id}")

        if not edge.domain or any(
            label not in GLOBAL_LABELS
            for label in edge.domain
        ):
            raise ValueError(f"Invalid domain: {edge.id}")

        for endpoint in (edge.u, edge.v):
            junction = csp.junctions[endpoint]

            if edge.id not in junction.edges:
                raise ValueError(
                    f"Missing edge {edge.id} in {endpoint}"
                )

    for junction in csp.junctions.values():
        if junction.type not in CATALOG:
            raise ValueError(
                f"Invalid type: {junction.type}"
            )

        expected_degree = len(
            CATALOG[junction.type][0]
        )

        if len(junction.edges) != expected_degree:
            raise ValueError(
                f"Invalid degree: {junction.id}"
            )

        if len(set(junction.edges)) != expected_degree:
            raise ValueError(
                f"Duplicate edges: {junction.id}"
            )

        for edge_id in junction.edges:
            if edge_id not in csp.edges:
                raise ValueError(f"Unknown edge: {edge_id}")

            edge = csp.edges[edge_id]

            if junction.id not in (edge.u, edge.v):
                raise ValueError(
                    f"Invalid connection: {edge_id}"
                )


if __name__ == "__main__":
    csp = load_csp("instances/cube.json")

    print("CSP loaded successfully!")
    print("Edges:", len(csp.edges))
    print("Junctions:", len(csp.junctions))

    print("\nEdges:")

    for edge in csp.edges.values():
        print(
            f"{edge.id}: {edge.u} -> {edge.v}, "
            f"domain={edge.domain}"
        )

    print("\nJunctions:")

    for junction in csp.junctions.values():
        print(
            f"{junction.id}: {junction.type}, "
            f"edges={junction.edges}"
        )

    assert len(csp.edges) == 9
    assert len(csp.junctions) == 7

    print("\nAll loader tests passed!")
