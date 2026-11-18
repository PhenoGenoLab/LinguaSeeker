"""Full-coverage document windowing for the source fact chain.

No source character may be silently dropped. Windows advance with a bounded
overlap so a sentence split across a boundary is still visible to extraction.
"""

from __future__ import annotations

from collections.abc import Iterator

from .contracts import DocumentWindow


def chunk_document(source: str, max_window_length: int = 4000, overlap: int = 200) -> Iterator[DocumentWindow]:
    """Yield overlapping windows covering the entire source exactly once.

    Raises:
        ValueError: when the parameters cannot produce a forward-advancing cover.
    """
    if max_window_length <= 0:
        raise ValueError(f"max_window_length must be positive, got {max_window_length}")
    if overlap < 0:
        raise ValueError(f"overlap must be non-negative, got {overlap}")
    if overlap >= max_window_length:
        raise ValueError(f"overlap ({overlap}) must be smaller than max_window_length ({max_window_length})")
    return _iter_windows(source, max_window_length, overlap)


def _iter_windows(source: str, max_window_length: int, overlap: int) -> Iterator[DocumentWindow]:
    if not source:
        return

    source_length = len(source)
    start = 0
    window_id = 0
    while start < source_length:
        end = min(start + max_window_length, source_length)
        if end < source_length:
            newline_pos = source.rfind("\n", start, end)
            if newline_pos != -1 and (end - newline_pos) < max_window_length // 4:
                end = newline_pos + 1

        yield DocumentWindow(
            window_id=window_id,
            text=source[start:end],
            start_offset=start,
            end_offset=end,
        )

        if end == source_length:
            break
        next_start = end - overlap
        if next_start <= start:
            next_start = end
        start = next_start
        window_id += 1
