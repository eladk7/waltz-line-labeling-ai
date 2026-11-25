
from dataclasses import dataclass, field


GLOBAL_LABELS = ("+", "-", "R", "L")


@dataclass
class Edge:
    id: str
    u: str
    v: str
    domain: tuple[str, ...] = GLOBAL_LABELS

    def is_first_endpoint(self, junction_id):
        if junction_id == self.u:
            return True

        if junction_id == self.v:
            return False

        raise ValueError(
            f"Junction {junction_id} is not on edge {self.id}"
        )


@dataclass
class Junction:
    id: str
    type: str
    edges: tuple[str, ...]
    x: float = 0.0
    y: float = 0.0
    reflection: bool = False


@dataclass
class CSP:
    edges: dict[str, Edge] = field(default_factory=dict)
    junctions: dict[str, Junction] = field(default_factory=dict)

    def add_edge(self, edge):
        self.edges[edge.id] = edge

    def add_junction(self, junction):
        self.junctions[junction.id] = junction

    def get_edge(self, edge_id):
        return self.edges[edge_id]

    def get_junction(self, junction_id):
        return self.junctions[junction_id]


if __name__ == "__main__":
    csp = CSP()

    csp.add_edge(Edge("e1", "A", "B"))
    csp.add_edge(Edge("e6", "F", "A"))

    csp.add_junction(
        Junction("A", "L", ("e1", "e6"), -1, 1)
    )

    edge = csp.get_edge("e1")
    junction = csp.get_junction("A")

    print("Edge:", edge)
    print("Junction:", junction)

    print("\nA is first endpoint:",
          edge.is_first_endpoint("A"))

    print("B is first endpoint:",
          edge.is_first_endpoint("B"))

    assert edge.is_first_endpoint("A") is True
    assert edge.is_first_endpoint("B") is False

    assert junction.edges == ("e1", "e6")
    assert len(csp.edges) == 2
    assert len(csp.junctions) == 1

    print("\nAll model tests passed!")
