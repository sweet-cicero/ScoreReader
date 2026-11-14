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
    was missed, or the page has no such staff), it gets empty bars at the page's end.

    A tie over the end of a page: each page marks its half (scoreread.ties.TIE_PAGE), the last note of a part with
    'tie_start' and the first note of the part on the next page with 'tie_stop'. The tie holds where both pages
    mark it at one pitch; a half without its other half is taken away, at the end of the hymn too."""
    width = max(len(page['parts']) for page in pages)
    parts: list[list[dict]] = [[] for _ in range(width)]
    names: dict[int, str] = {}
    for page in pages:
        names.update(page.get('names') or {})
        bars = max((len(part) for part in page['parts']), default=0)
        for number, part in enumerate(parts):
            own = page['parts'][number] if number < len(page['parts']) else []
            _page_ties(part, own)
            part.extend(own)
            last = part[-1] if part else {'clef': 'G', 'key': page.get('key', 0)}
            part.extend({'notes': [], 'clef': last['clef'], 'key': last['key']} for _ in range(bars - len(own)))
    for part in parts:
        _page_ties(part, [])
    return parts, names


def _page_ties(before: list[dict], after: list[dict]) -> None:
    """Keeps the ties over the end of a page that both pages mark, in one part: `before` are its bars so far and
    `after` the bars of the next page. A note of the last bar with 'tie_start' and no note of its pitch after it,
    and a note of the first bar with 'tie_stop' and no note of its pitch before it, are the halves."""
    last = next((bar['notes'] for bar in reversed(before) if bar['notes']), [])
    first = next((bar['notes'] for bar in after if bar['notes']), [])
    going = [note for note in last if note.get('tie_start')
             and not any(other['midi'] == note['midi'] and other['onset'] > note['onset'] for other in last)]
    coming = [note for note in first if note.get('tie_stop')
              and not any(other['midi'] == note['midi'] and other['onset'] < note['onset'] for other in first)]
    if not before:
        return
    for note in going:
        if not any(other['midi'] == note['midi'] for other in coming):
            note['tie_start'] = False
    for note in coming:
        if not any(other['midi'] == note['midi'] for other in going):
            note['tie_stop'] = False
