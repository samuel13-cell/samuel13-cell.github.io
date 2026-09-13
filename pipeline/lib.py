"""Inline-SVG chart helpers shared by the project pages.

No chart library: every page ships plain SVG plus a small hover layer, so
the pages stay dependency-free and render identically in print.
"""
W, H = 760, 300
# The plot spans the full content column so its gridlines share both edges
# with the section rules above them. Axis labels and series labels all sit
# inside the plot rather than in gutters, which is what keeps them aligned.
PAD = {'t': 26, 'r': 0, 'b': 30, 'l': 0}

MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July',
          'August', 'September', 'October', 'November', 'December']


def pretty_month(ym: str) -> str:
    """'2012-04' -> 'April 2012'"""
    y, m = ym.split('-')
    return f'{MONTHS[int(m) - 1]} {y}'


def scales(n, lo, hi, pad=PAD):
    iw = W - pad['l'] - pad['r']
    ih = H - pad['t'] - pad['b']
    return (lambda i: pad['l'] + iw * i / (n - 1),
            lambda v: pad['t'] + ih * (1 - (v - lo) / (hi - lo)))


def _path(xs, ys, values):
    """Break the line across gaps rather than drawing through them."""
    out, pen_down = [], False
    for i, v in enumerate(values):
        if v is None:
            pen_down = False
            continue
        out.append(f'{"L" if pen_down else "M"}{xs(i):.1f},{ys(v):.1f}')
        pen_down = True
    return ' '.join(out)


def _grid(ys, lo, hi, step, pad=PAD):
    out, v = [], lo
    while v <= hi + 1e-9:
        y = ys(v)
        out.append(f'<line class="grid" x1="{pad["l"]}" y1="{y:.1f}" '
                   f'x2="{W - pad["r"]}" y2="{y:.1f}"/>')
        out.append(f'<text class="ax" x="{pad["l"]}" y="{y - 5:.1f}" '
                   f'text-anchor="start">{v:g}</text>')
        v += step
    return out


def _x_ticks(labels, xs, every, pad=PAD, ticks=None):
    """Edge ticks anchor inward so they never overhang the plot."""
    out = []
    last = len(labels) - 1
    chosen = dict(ticks) if ticks else None
    for i, lab in enumerate(labels):
        if chosen is not None:
            if i not in chosen:
                continue
            lab = chosen[i]
        elif not (i % every == 0 or i == last):
            continue
        anchor = 'start' if i == 0 else 'end' if i == last else 'middle'
        out.append(f'<text class="ax" x="{xs(i):.1f}" y="{H - 10}" '
                   f'text-anchor="{anchor}">{lab}</text>')
    return out


def line_chart(labels, series, lo, hi, step=10, every=2, annotate=None, ticks=None):
    """series: list of (label, css-var, values).

    annotate: (index, text) draws a labelled vertical rule.
    ticks: explicit [(index, label)] when every-Nth is the wrong cadence,
    as it is for a monthly series that wants one tick per year.
    """
    xs, ys = scales(len(labels), lo, hi)
    parts = _grid(ys, lo, hi, step)

    parts += _x_ticks(labels, xs, every, ticks=ticks)

    if annotate:
        ai, text = annotate
        x = xs(ai)
        parts.append(f'<line class="rule" x1="{x:.1f}" y1="{PAD["t"]}" '
                     f'x2="{x:.1f}" y2="{H - PAD["b"]}"/>')
        parts.append(f'<text class="anno" x="{x + 6:.1f}" y="{PAD["t"] + 11}">{text}</text>')

    for label, var, values in series:
        parts.append(f'<path class="ln" stroke="var({var})" d="{_path(xs, ys, values)}"/>')
        last = max(i for i, v in enumerate(values) if v is not None)
        ex, ey = xs(last), ys(values[last])
        parts.append(f'<circle class="dot" cx="{ex:.1f}" cy="{ey:.1f}" '
                     f'r="4.5" fill="var({var})"/>')
        # A lone series is already named by the heading, so labelling it again
        # only risks colliding with its own line.
        if len(series) > 1:
            # above the end point and right-aligned, so nothing overhangs
            parts.append(f'<text class="dl" x="{ex - 8:.1f}" y="{ey - 11:.1f}" '
                         f'text-anchor="end" fill="var({var})">{label}</text>')

    parts.append(f'<line class="cross" x1="0" y1="{PAD["t"]}" x2="0" '
                 f'y2="{H - PAD["b"]}" style="opacity:0"/>')
    return '\n    '.join(parts)


def bar_chart(labels, values, lo, hi, step=10, var='--c-input', every=2, mark=None):
    """Single-series columns. mark: index from which bars take the accent hue."""
    pad = dict(PAD)
    xs, ys = scales(len(labels), lo, hi, pad)
    parts = _grid(ys, lo, hi, step, pad)

    slot = (W - pad['l'] - pad['r']) / len(labels)
    bw = min(24, slot - 6)
    base = ys(lo)

    for i, v in enumerate(values):
        x = xs(i) - bw / 2
        top = ys(v)
        hgt = max(0.5, base - top)
        hue = '--c-output' if (mark is not None and i >= mark) else var
        # 4px rounded data-end, square at the baseline
        r = min(4, hgt)
        parts.append(
            f'<path class="bar" fill="var({hue})" d="M{x:.1f},{base:.1f} '
            f'V{top + r:.1f} Q{x:.1f},{top:.1f} {x + r:.1f},{top:.1f} '
            f'H{x + bw - r:.1f} Q{x + bw:.1f},{top:.1f} {x + bw:.1f},{top + r:.1f} '
            f'V{base:.1f} Z"/>')

    parts += _x_ticks(labels, xs, every, pad)
    return '\n    '.join(parts)
