"""Joins the pages of a hymn into one score.

Each page is read alone (scoreread.reader for an image, scoreread.vector for a software-made PDF) and gives its
parts: one list of bars for each staff of a system, from the top. The same staff of every system of every page is
one part of the hymn. The pages follow each other bar after bar.
"""
from __future__ import annotations


def join_pages(pages: list[dict]) -> tuple[list[list[dict]], dict[int, str]]:
    """The parts of a hymn from what was read on its pages, in order (each as read_page() or read_pdf_page() gives
    it, with 'parts' and 'names'). Returns the parts and the names of the parts that have one.

    A page begins at the same bar in every part: where a part of a page has fewer bars than another (a bar line
    was missed, or the page has no such staff), it gets empty bars at the page's end."""
    width = max(len(page['parts']) for page in pages)
    parts: list[list[dict]] = [[] for _ in range(width)]
    names: dict[int, str] = {}
    for page in pages:
        names.update(page.get('names') or {})
        bars = max((len(part) for part in page['parts']), default=0)
        for number, part in enumerate(parts):
            own = page['parts'][number] if number < len(page['parts']) else []
            part.extend(own)
            last = part[-1] if part else {'clef': 'G', 'key': page.get('key', 0)}
            part.extend({'notes': [], 'clef': last['clef'], 'key': last['key']} for _ in range(bars - len(own)))
    return parts, names
