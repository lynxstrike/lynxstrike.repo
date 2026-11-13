"""Spatial navigation, with vertical wrapping at the outermost rows."""


def neighbour(current, direction, rects):
    x, y, width, height = rects[current]
    horizontal = direction in ('left', 'right')
    start, end = (y, y + height) if horizontal else (x, x + width)
    candidates = []
    for cid, (ox, oy, ow, oh) in rects.items():
        if cid == current:
            continue
        forward = {'left': x - ox - ow, 'right': ox - x - width,
                   'up': y - oy - oh, 'down': oy - y - height}[direction]
        # A control underneath a wide button is not to its left or right.
        if forward < 0:
            continue
        other_start, other_end = (oy, oy + oh) if horizontal else (ox, ox + ow)
        overlap = min(end, other_end) - max(start, other_start)
        gap = max(0, -overlap)
        if overlap > 0:
            # First stay in the same row/column, choosing the nearest edge.
            # Leading-edge alignment resolves a wide button above two choices.
            rank = (0, forward, abs(start - other_start), forward * forward)
        else:
            rank = (1, forward * forward + gap * gap, gap, forward)
        candidates.append((rank, cid))
    if candidates:
        return min(candidates)[1]
    if direction in ('up', 'down'):
        top = min(r[1] for r in rects.values())
        bottom = max(r[1] + r[3] for r in rects.values())
        at_edge = y == top if direction == 'up' else y + height == bottom
        if at_edge:
            row = {cid: r for cid, r in rects.items()
                   if (r[1] + r[3] == bottom if direction == 'up' else r[1] == top)
                   and cid != current}
            if row:
                def alignment(cid):
                    ox, _, ow, _ = row[cid]
                    gap = max(0, ox - x - width, x - ox - ow)
                    return (gap, abs(ox - x), abs(ox + ow / 2 - x - width / 2))
                return min(row, key=alignment)
    return current


def navigation_map(rects):
    return {cid: {direction: neighbour(cid, direction, rects)
                  for direction in ('up', 'down', 'left', 'right')}
            for cid in rects}
