"""Step-by-step reduction of real search events into a view state."""


class ViewState:

    def __init__(self):
        self.algorithm = None
        self.domains = None
        self.labels = {}
        self.empty_junctions = set()
        self.queue = []
        self.current_arc = None
        self.removed_tuples = []
        self.removed_count = 0
        self.removed_total = 0
        self.tree = []
        self.hc_current = None
        self.hc_best = None
        self.hc_current_h = None
        self.hc_best_h = None
        self.hc_steps = 0
        self.hc_restarts = 0
        self.hc_sideways = 0
        self.hc_move = None
        self.hc_violations = {}
        self.generations = []
        self.best_assignment = None
        self.best_h = None
        self.samples = []
        self.status = ""
        self.solved = None
        self.decisions = 0
        self.backtracks = 0
        self.objective_evaluations = 0
        self.elapsed_ms = 0.0


def determined_edge_labels(csp, domains):
    """Label an edge only when every incident junction forces one value."""

    grouped = {edge_id: [] for edge_id in csp.edges}

    for junction in csp.junctions.values():
        domain = domains.get(junction.id, [])

        for index, edge_id in enumerate(junction.edges):
            grouped[edge_id].append({
                candidate[index] for candidate in domain
            })

    labels = {}

    for edge_id, choice_sets in grouped.items():
        if not choice_sets:
            labels[edge_id] = None
            continue

        common = set.intersection(*choice_sets)
        labels[edge_id] = next(iter(common)) if len(common) == 1 else None

    return labels


def _sync_waltz(state, csp):
    if state.domains is None:
        return

    state.empty_junctions = {
        junction_id
        for junction_id, domain in state.domains.items()
        if len(domain) == 0
    }

    if csp is not None:
        state.labels = determined_edge_labels(csp, state.domains)


def _add_sample(state, payload):
    best_h = payload.get("best_h")

    if best_h is None:
        return

    state.best_h = best_h
    state.elapsed_ms = payload.get("elapsed_ms", state.elapsed_ms)
    state.objective_evaluations = payload.get(
        "objective_evaluations",
        state.objective_evaluations,
    )
    state.samples.append({
        "time_ms": payload.get("elapsed_ms", 0.0),
        "evaluations": payload.get("objective_evaluations", 0),
        "best_h": best_h,
    })


def _remember_algorithm(state, event):
    algorithm = event.get("algorithm")

    if algorithm == "ac3":
        algorithm = "waltz"

    if algorithm in ("waltz", "hc", "ga"):
        state.algorithm = algorithm


def apply_event(state, event, csp=None):
    _remember_algorithm(state, event)

    kind = event.get("kind")
    payload = event.get("payload", {})

    if kind == "queue":
        state.queue = list(payload.get("queue", []))
        if "domains" in payload:
            state.domains = payload["domains"]
            _sync_waltz(state, csp)

    elif kind == "domains":
        state.domains = payload.get("domains")
        _sync_waltz(state, csp)

    elif kind == "revise":
        state.current_arc = payload.get("arc")
        state.queue = list(payload.get("queue", []))
        state.removed_count = payload.get("removed", 0)
        state.removed_tuples = list(payload.get("removed_tuples", []))
        state.removed_total += state.removed_count
        if "domains" in payload:
            state.domains = payload["domains"]
            _sync_waltz(state, csp)

    elif kind == "mrv":
        state.tree.append({
            "depth": payload.get("depth", 0),
            "text": (
                f"MRV {payload.get('junction')} "
                f"({payload.get('domain_size')} values)"
            ),
        })

    elif kind == "decision":
        state.decisions += 1
        state.tree.append({
            "depth": payload.get("depth", 0),
            "text": (
                f"try {payload.get('junction')} = "
                f"{payload.get('candidate')}"
            ),
        })
        if "domains" in payload:
            state.domains = payload["domains"]
            _sync_waltz(state, csp)

    elif kind == "backtrack":
        state.backtracks += 1
        state.tree.append({
            "depth": payload.get("depth", 0),
            "text": (
                f"backtrack {payload.get('junction')} "
                f"{payload.get('candidate')}"
            ),
        })

    elif kind == "result":
        state.status = payload.get("status", "")
        state.solved = payload.get("solved")
        state.decisions = payload.get("decisions", state.decisions)
        state.backtracks = payload.get("backtracks", state.backtracks)
        solution = payload.get("solution")
        if solution:
            state.labels = dict(solution)
            state.best_assignment = dict(solution)
            state.empty_junctions = set()
        _add_sample(state, payload)

    elif kind == "restart":
        state.hc_current = dict(payload.get("current") or {})
        state.hc_current_h = payload.get("current_h")
        state.hc_best = dict(payload.get("best") or {})
        state.hc_best_h = payload.get("best_h")
        state.hc_steps = payload.get("steps", 0)
        state.hc_restarts = payload.get("restarts", 0)
        state.hc_sideways = payload.get("sideways_steps", 0)
        state.hc_violations = dict(payload.get("violations") or {})
        state.labels = dict(state.hc_current)
        state.best_assignment = dict(state.hc_best) if state.hc_best else None
        state.hc_move = None
        _add_sample(state, payload)

    elif kind == "move":
        state.hc_move = dict(payload)
        state.hc_current = dict(payload.get("current") or {})
        state.hc_best = dict(payload.get("best") or {})
        state.hc_current_h = payload.get("h_after")
        state.hc_best_h = payload.get("best_h")
        state.hc_steps = payload.get("steps", state.hc_steps)
        state.hc_restarts = payload.get("restarts", state.hc_restarts)
        state.hc_sideways = payload.get("sideways_steps", state.hc_sideways)
        state.hc_violations = dict(payload.get("violations") or {})
        state.labels = dict(state.hc_current)
        state.best_assignment = dict(state.hc_best) if state.hc_best else None
        _add_sample(state, payload)

    elif kind == "progress":
        assignment = payload.get("best_assignment")
        if assignment:
            state.best_assignment = dict(assignment)
            state.labels = dict(assignment)
        _add_sample(state, payload)

    elif kind == "generation":
        state.generations.append(payload)
        assignment = payload.get("best_assignment")
        if assignment:
            state.best_assignment = dict(assignment)
            state.labels = dict(assignment)
        _add_sample(state, payload)

    elif kind == "done":
        state.solved = payload.get("solved")
        if payload.get("cancelled"):
            state.status = "CANCELLED"
        elif payload.get("stop_reason"):
            state.status = payload["stop_reason"]
        elif payload.get("solved"):
            state.status = "SOLVED"
        else:
            state.status = "DONE"

        best = payload.get("best_assignment") or payload.get("best")
        if best:
            state.best_assignment = dict(best)
            if state.algorithm == "ga":
                state.labels = dict(best)
            elif state.algorithm == "hc":
                state.hc_best = dict(best)
                state.hc_best_h = payload.get("best_h")
        _add_sample(state, payload)


def replay(events, csp=None):
    state = ViewState()

    for event in events:
        apply_event(state, event, csp)

    return state


def event_summary(event):
    kind = event.get("kind", "")
    payload = event.get("payload", {})
    algorithm = event.get("algorithm", "")

    if kind == "revise":
        arc = payload.get("arc") or {}
        return (
            f"{algorithm} revise {arc.get('source')} -> {arc.get('target')} "
            f"removed {payload.get('removed')}"
        )

    if kind == "mrv":
        return (
            f"waltz MRV {payload.get('junction')} "
            f"size {payload.get('domain_size')}"
        )

    if kind == "decision":
        return (
            f"waltz try {payload.get('junction')} = "
            f"{payload.get('candidate')}"
        )

    if kind == "backtrack":
        return (
            f"waltz backtrack {payload.get('junction')} "
            f"{payload.get('candidate')}"
        )

    if kind == "move":
        return (
            f"hc {payload.get('move_type')} {payload.get('edge_id')} "
            f"{payload.get('old_label')} -> {payload.get('new_label')} "
            f"h {payload.get('h_before')} -> {payload.get('h_after')}"
        )

    if kind == "restart":
        return (
            f"hc restart {payload.get('restarts')} "
            f"h={payload.get('current_h')} best={payload.get('best_h')}"
        )

    if kind == "generation":
        metrics = payload.get("metrics") or {}
        average = metrics.get("average_h")
        std = metrics.get("std_h")
        average_text = f"{average:.3f}" if isinstance(average, float) else average
        std_text = f"{std:.3f}" if isinstance(std, float) else std
        return (
            f"ga gen {metrics.get('generation')} "
            f"best {metrics.get('best_h')} avg {average_text} "
            f"std {std_text} unique {metrics.get('unique_chromosomes')}"
        )

    if kind == "progress":
        return (
            f"{algorithm} best h={payload.get('best_h')} "
            f"evals={payload.get('objective_evaluations')}"
        )

    if kind in ("result", "done"):
        status = (
            payload.get("status")
            or payload.get("stop_reason")
            or ""
        )
        return f"{algorithm} {kind} {status} h={payload.get('best_h')}"

    if kind == "queue":
        return f"{algorithm} queue size {len(payload.get('queue', []))}"

    if kind == "domains":
        return f"{algorithm} domains ({payload.get('phase', 'update')})"

    return f"{algorithm} {kind}"
