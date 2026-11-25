"""Draw a line-drawing CSP from junction coordinates."""

from math import cos, hypot, pi, sin

from matplotlib.patches import FancyArrowPatch


LABEL_COLORS = {
    "+": "#2471a3",
    "-": "#d68910",
    "R": "#196f3d",
    "L": "#6c3483",
}

NEUTRAL = "#7f8c8d"
JUNCTION = "#1f4e79"
VIOLATED = "#c0392b"
SELECTED = "#f4d03f"


def junction_positions(csp):
    identifiers = list(csp.junctions)
    raw = {
        junction_id: (
            csp.junctions[junction_id].x,
            csp.junctions[junction_id].y,
        )
        for junction_id in identifiers
    }

    if len(raw) <= 1:
        return raw

    unique = {
        (round(x, 6), round(y, 6))
        for x, y in raw.values()
    }

    if len(unique) > 1:
        return raw

    laid_out = {}

    for index, junction_id in enumerate(identifiers):
        angle = 2 * pi * index / len(identifiers)
        laid_out[junction_id] = (cos(angle), sin(angle))

    return laid_out


def _span(positions):
    xs = [point[0] for point in positions.values()]
    ys = [point[1] for point in positions.values()]
    width = max(xs) - min(xs) if xs else 1.0
    height = max(ys) - min(ys) if ys else 1.0
    return max(width, height, 1.0)


def _segment_distance(px, py, ax, ay, bx, by):
    dx = bx - ax
    dy = by - ay
    length_sq = dx * dx + dy * dy

    if length_sq == 0:
        return hypot(px - ax, py - ay)

    t = ((px - ax) * dx + (py - ay) * dy) / length_sq
    t = max(0.0, min(1.0, t))
    return hypot(px - (ax + t * dx), py - (ay + t * dy))


def _along(start, end, t):
    return (
        start[0] + (end[0] - start[0]) * t,
        start[1] + (end[1] - start[1]) * t,
    )


def hit_test(csp, x, y):
    if x is None or y is None or not csp.junctions:
        return None, None

    positions = junction_positions(csp)
    threshold = 0.08 * _span(positions)

    nearest_junction = None
    nearest_distance = threshold

    for junction_id, (jx, jy) in positions.items():
        distance = hypot(x - jx, y - jy)
        if distance <= nearest_distance:
            nearest_junction = junction_id
            nearest_distance = distance

    if nearest_junction is not None:
        return "junction", nearest_junction

    nearest_edge = None
    nearest_distance = threshold

    for edge in csp.edges.values():
        ax, ay = positions[edge.u]
        bx, by = positions[edge.v]
        distance = _segment_distance(x, y, ax, ay, bx, by)
        if distance <= nearest_distance:
            nearest_edge = edge.id
            nearest_distance = distance

    if nearest_edge is not None:
        return "edge", nearest_edge

    return None, None


def draw_graph(
    ax,
    csp,
    labels=None,
    violated=None,
    selected_junction=None,
    selected_edge=None,
):
    ax.clear()
    ax.set_aspect("equal", adjustable="box")
    ax.axis("off")

    if csp is None or not csp.junctions:
        ax.set_title("Load a JSON instance")
        return

    labels = labels or {}
    violated = violated or set()
    positions = junction_positions(csp)
    span = _span(positions)

    for edge in csp.edges.values():
        start = positions[edge.u]
        end = positions[edge.v]
        label = labels.get(edge.id)
        color = LABEL_COLORS.get(label, NEUTRAL)
        width = 2.6 if edge.id == selected_edge else 1.6
        style = "-" if label in LABEL_COLORS else (0, (4, 3))

        ax.plot(
            [start[0], end[0]],
            [start[1], end[1]],
            color=color,
            linewidth=width,
            linestyle=style,
            solid_capstyle="round",
            zorder=1,
        )

        dx = end[0] - start[0]
        dy = end[1] - start[1]
        length = hypot(dx, dy) or 1.0
        normal = (-dy / length, dx / length)
        offset = 0.045 * span

        midpoint = _along(start, end, 0.5)
        id_point = _along(start, end, 0.28)

        ax.text(
            id_point[0] - normal[0] * offset,
            id_point[1] - normal[1] * offset,
            edge.id,
            color="#566573",
            fontsize=8,
            ha="center",
            va="center",
            zorder=4,
        )

        if label in ("R", "L"):
            arrow_start, arrow_end = (
                (start, end) if label == "R" else (end, start)
            )
            ax.add_patch(FancyArrowPatch(
                _along(arrow_start, arrow_end, 0.38),
                _along(arrow_start, arrow_end, 0.68),
                arrowstyle="-|>",
                mutation_scale=11,
                linewidth=1.4,
                color=color,
                zorder=2,
            ))

        if label in LABEL_COLORS:
            ax.text(
                midpoint[0] + normal[0] * offset * 1.35,
                midpoint[1] + normal[1] * offset * 1.35,
                label,
                color=color,
                fontsize=9,
                fontweight="bold",
                ha="center",
                va="center",
                zorder=4,
                bbox={
                    "boxstyle": "round,pad=0.15",
                    "facecolor": "white",
                    "edgecolor": color,
                    "linewidth": 0.8,
                },
            )

    for junction_id, (x, y) in positions.items():
        selected = junction_id == selected_junction
        face = VIOLATED if junction_id in violated else JUNCTION
        ax.scatter(
            [x],
            [y],
            s=220 if selected else 160,
            c=face,
            edgecolors=SELECTED if selected else "white",
            linewidths=2.0 if selected else 0.8,
            zorder=3,
        )
        junction = csp.junctions[junction_id]
        ax.text(
            x,
            y + 0.055 * span,
            f"{junction.id} ({junction.type})",
            color="#1c2833",
            fontsize=8,
            ha="center",
            va="bottom",
            zorder=5,
        )

    xs = [point[0] for point in positions.values()]
    ys = [point[1] for point in positions.values()]
    pad = 0.18 * span
    ax.set_xlim(min(xs) - pad, max(xs) + pad)
    ax.set_ylim(min(ys) - pad, max(ys) + pad)
