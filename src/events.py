"""Optional search events and cooperative cancellation.

Algorithms emit events only when a caller passes ``on_event``. Benchmarks
that omit the callback do not build traces and do not render anything.
"""

import threading


class SearchCancelled(Exception):
    """Raised when a running search observes a cancellation request."""


class CancellationToken:
    """Thread-safe flag the GUI can set while a worker is searching."""

    def __init__(self):
        self._event = threading.Event()

    def cancel(self):
        self._event.set()

    def is_cancelled(self):
        return self._event.is_set()

    def __call__(self):
        return self._event.is_set()


def check_cancel(cancel):
    if cancel is not None and cancel():
        raise SearchCancelled()


def make_event(algorithm, kind, **payload):
    return {
        "algorithm": algorithm,
        "kind": kind,
        "payload": payload,
    }


def arc_to_dict(arc):
    return {
        "source": arc.source,
        "target": arc.target,
        "edge_id": arc.edge_id,
        "source_index": arc.source_index,
        "target_index": arc.target_index,
    }


def copy_domains(domains):
    return {
        junction_id: list(domain)
        for junction_id, domain in domains.items()
    }


def tuple_difference(before, after):
    """Tuples present in ``before`` but not matched in ``after``."""

    remaining = list(after)
    removed = []

    for item in before:
        try:
            remaining.remove(item)
        except ValueError:
            removed.append(item)

    return removed
