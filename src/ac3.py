from collections import deque
from time import perf_counter
from dataclasses import dataclass

from src.loader import load_csp
from src.domains import build_domains, print_domains
from src.arcs import build_arcs
from src.revise import revise
from src.events import (
    arc_to_dict,
    check_cancel,
    copy_domains,
    make_event,
    tuple_difference,
)


@dataclass
class AC3Stats:
    revise_calls: int = 0
    constraint_checks: int = 0
    removed_tuples: int = 0
    max_queue_size: int = 0
    timed_out: bool = False


def ac3(
    domains,
    arcs,
    initial_queue=None,
    verbose=False,
    *,
    on_event=None,
    cancel=None,
    deadline=None,
):

    stats = AC3Stats()

    queue = deque(
        arcs if initial_queue is None else initial_queue
    )

    stats.max_queue_size = len(queue)

    def emit(kind, **payload):
        if on_event is not None:
            on_event(make_event("ac3", kind, **payload))

    if on_event is not None:
        emit(
            "queue",
            queue=[arc_to_dict(arc) for arc in queue],
            domains=copy_domains(domains),
        )

    if any(not domain for domain in domains.values()):
        return False, stats

    while queue:

        if deadline is not None and perf_counter() >= deadline:
            stats.timed_out = True
            return False, stats
        check_cancel(cancel)

        arc = queue.popleft()

        stats.revise_calls += 1

        before = (
            list(domains[arc.source])
            if on_event is not None
            else None
        )

        removed = revise(domains, arc, stats)

        stats.removed_tuples += removed

        if removed > 0:

            if verbose:
                print(
                    f"{arc.source} -> {arc.target}: "
                    f"removed={removed}, "
                    f"remaining={len(domains[arc.source])}"
                )

            if not domains[arc.source]:
                if on_event is not None:
                    emit(
                        "revise",
                        arc=arc_to_dict(arc),
                        removed=removed,
                        removed_tuples=tuple_difference(
                            before, domains[arc.source]
                        ),
                        queue=[arc_to_dict(item) for item in queue],
                        domains=copy_domains(domains),
                        emptied=True,
                    )
                return False, stats

            for neighbor_arc in arcs:

                if (
                    neighbor_arc.target == arc.source
                    and neighbor_arc.source != arc.target
                ):
                    if neighbor_arc not in queue:
                        queue.append(neighbor_arc)

            stats.max_queue_size = max(
                stats.max_queue_size,
                len(queue)
            )

        if on_event is not None:
            emit(
                "revise",
                arc=arc_to_dict(arc),
                removed=removed,
                removed_tuples=tuple_difference(
                    before, domains[arc.source]
                ),
                queue=[arc_to_dict(item) for item in queue],
                domains=copy_domains(domains),
                emptied=not domains[arc.source],
            )

    return True, stats


def print_stats(stats):

    print("REVISE calls:", stats.revise_calls)
    print("Constraint checks:", stats.constraint_checks)
    print("Removed tuples:", stats.removed_tuples)
    print("Max queue size:", stats.max_queue_size)


if __name__ == "__main__":

    # TEST 1 - Unique solution
    print("TEST 1 - e1-e6 fixed to R")

    csp = load_csp("instances/cube.json")

    for i in range(1, 7):
        csp.edges[f"e{i}"].domain = ("R",)

    domains = build_domains(csp)
    arcs = build_arcs(csp)

    success, stats = ac3(
        domains, arcs, verbose=True
    )

    print("Consistent:", success)
    print_domains(domains)
    print_stats(stats)

    assert success is True
    assert all(len(d) == 1 for d in domains.values())
    assert domains["O"] == [("+", "+", "+")]
    assert stats.removed_tuples == 4

    # TEST 2 - No solution
    print("\nTEST 2 - e7 fixed to minus")

    csp = load_csp("instances/cube.json")
    csp.edges["e7"].domain = ("-",)

    domains = build_domains(csp)
    arcs = build_arcs(csp)

    success, stats = ac3(
        domains, arcs, verbose=True
    )

    print("Consistent:", success)
    print_domains(domains)
    print_stats(stats)

    assert success is False
    assert any(len(d) == 0 for d in domains.values())

    # TEST 3 - All edges open
    print("\nTEST 3 - All edges open")

    csp = load_csp("instances/cube.json")

    domains = build_domains(csp)
    arcs = build_arcs(csp)

    success, stats = ac3(
        domains, arcs, verbose=True
    )

    print("Consistent:", success)
    print_domains(domains)
    print_stats(stats)

    assert success is True
    assert all(len(d) > 0 for d in domains.values())

    for arc in arcs:
        assert revise(domains, arc) == 0

    print("\nAll AC-3 tests passed!")
