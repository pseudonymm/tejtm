from __future__ import annotations


def assign_one_to_one(
    scores: list[list[float]],
    min_confidence: float,
) -> list[tuple[int, int] | None]:
    """Return (row, col) per row index, or None when unassigned."""
    if not scores:
        return []
    n_rows = len(scores)
    n_cols = len(scores[0]) if scores else 0
    if n_cols == 0:
        return [None] * n_rows

    pairs = _hungarian_maximize(scores)
    result: list[tuple[int, int] | None] = [None] * n_rows
    for row, col in pairs:
        if scores[row][col] >= min_confidence:
            result[row] = (row, col)
    return result


def _hungarian_maximize(scores: list[list[float]]) -> list[tuple[int, int]]:
    n_rows = len(scores)
    n_cols = len(scores[0])
    n = max(n_rows, n_cols)
    cost = [[1.0 - scores[i][j] if i < n_rows and j < n_cols else 1.0 for j in range(n)] for i in range(n)]
    assignment = _linear_sum_assignment(cost)
    out: list[tuple[int, int]] = []
    for i, j in assignment:
        if i < n_rows and j < n_cols:
            out.append((i, j))
    return out


def _linear_sum_assignment(cost: list[list[float]]) -> list[tuple[int, int]]:
    try:
        from scipy.optimize import linear_sum_assignment  # type: ignore import-not-found

        import numpy as np

        row_ind, col_ind = linear_sum_assignment(np.array(cost))
        return [(int(r), int(c)) for r, c in zip(row_ind, col_ind, strict=True)]
    except ImportError:
        return _greedy_maximize(cost)


def _greedy_maximize(cost: list[list[float]]) -> list[tuple[int, int]]:
    n = len(cost)
    candidates: list[tuple[float, int, int]] = []
    for i in range(n):
        for j in range(n):
            candidates.append((cost[i][j], i, j))
    candidates.sort(key=lambda t: t[0])
    used_rows: set[int] = set()
    used_cols: set[int] = set()
    pairs: list[tuple[int, int]] = []
    for _, i, j in candidates:
        if i in used_rows or j in used_cols:
            continue
        used_rows.add(i)
        used_cols.add(j)
        pairs.append((i, j))
    return pairs
