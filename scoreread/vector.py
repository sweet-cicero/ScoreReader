"""Reads a page that notation software wrote into a PDF, from the PDF's own drawing. No model, and no image.

Such a PDF keeps every sign as a character of a music font at its exact place: a note head, a clef, a sharp, a flag,
a dot. The staff lines, the stems and the bar lines are drawn lines, the beams are filled shapes, and the words are
plain text. So nothing has to be recognised: the step looks each sign up in a table and applies the same music rules
as the reader of scans (scoreread.music). A scan has no such signs, and this step then gives None.

Two ways of drawing are read:
- Finale (fonts Maestro, Petrucci) and MuseScore (Leland, a SMuFL font): lines for the staves, stems and bar lines.
- Encore (font Anastasia): the staff, the stems and the bar lines are characters too ('=' is a piece of staff, a
  stem is a pile of short pieces), and a beam is a thick stroke.

The step needs pdfplumber (pure Python). read_pdf_page() gives the same kind of result as reader.read_page().
"""
from __future__ import annotations

from collections import Counter

from .music import build_staff, musicxml, staff_columns

# The signs of the fonts that follow Adobe's Sonata (Maestro, Petrucci, Anastasia), by their code.
SONATA = {0x26: 'clef G', 0x3F: 'clef F', 0x56: 'clef G8', 0x42: 'clef C',
          0xCF: 'head black', 0xF6: 'head black', 0xFA: 'head half', 0x77: 'head whole', 0x57: 'head breve',
          0x23: 'sharp', 0x62: 'flat', 0x6E: 'natural', 0x4E: 'natural', 0x2E: 'dot',
          0x6A: 'flag up 1', 0x4A: 'flag down 1', 0x72: 'flag up 2', 0x52: 'flag down 2',
          0xCE: 'rest 1', 0xEE: 'rest 2', 0xB7: 'rest 4', 0xE4: 'rest 1/2', 0xC5: 'rest 1/4',
          0x3D: 'staff', 0x6C: 'bar', 0x5F: 'ledger', 0xC7: 'stem up', 0xC8: 'stem down'}
# Some PDF writers name these signs after other characters (the code of the sign is lost): what each one shows.
ODD = {'α': 0x62, 'µ': 0x6E, 'ϖ': 0x77, '−': 0x2E, '∀': 0x23, 'Ι': 0x4A, 'ι': 0x6A}
ODD_CLEFS = {'%': 'clef G', '>': 'clef F'}     # these two only where a clef stands: at the start of a staff
# The signs of a SMuFL font (Leland, Bravura), by their code point.
SMUFL = {0xE050: 'clef G', 0xE052: 'clef G8', 0xE062: 'clef F', 0xE05C: 'clef C',
         0xE0A4: 'head black', 0xE0A3: 'head half', 0xE0A2: 'head whole', 0xE0A0: 'head breve',
         0xE262: 'sharp', 0xE260: 'flat', 0xE261: 'natural', 0xE1E7: 'dot',
         0xE240: 'flag up 1', 0xE241: 'flag down 1', 0xE242: 'flag up 2', 0xE243: 'flag down 2',
         0xE4E5: 'rest 1', 0xE4E4: 'rest 2', 0xE4E3: 'rest 4', 0xE4E6: 'rest 1/2', 0xE4E7: 'rest 1/4'}
SONATA_FONTS = ('Maestro', 'Petrucci', 'Anastasia', 'Sonata')
SMUFL_FONTS = ('Leland', 'Bravura', 'Petaluma', 'Emmentaler', 'Gonville', 'MScore')
HEADS = ('head black', 'head half', 'head whole', 'head breve')

LONG = 60.0           # points: a drawn staff line is at least this long (a ledger line is short)
GAPS = (2.5, 12.0)    # points: the lines of a staff stand this far apart
EVEN = 0.12           # the four gaps of a staff differ by at most this share of a gap
THIN = 1.6            # points: a filled box this thin is a line
ON_GRID = 0.3         # a head stands on a line or in a space: at most this share of half a gap off
NEAR_STAFF = 8.5      # a head belongs to a staff at most this many gaps from its middle line
STEM_SIDE = 0.3       # a stem stands at most this many gaps from the left or right edge of its head
STEM_END = 0.75       # and passes the head, or ends at most this many gaps from its middle
STEM_LEAST = 1.5      # a stem is at least this many gaps long
FLAG_NEAR = (0.6, 1.2)    # a flag stands this near its stem's free end, sideways and along the stem, in gaps
BEAM_THICK = (0.25, 1.0)  # a beam is this thick, in gaps
BEAM_REACH = 2.6      # the beams of a stem lie within this many gaps of its free end
DOT_AT = (0.1, 2.2, 0.7)  # a dot stands this far right of its head (from, to), and at most this far over or under it
SIGN_AT = (3.2, 0.3)  # a sharp, flat or natural stands at most this far left of its head, and this far off its height
KEY_STEP = 1.6        # the signs of a key signature follow the clef, each at most this many gaps after the last
WORDS_UNDER = 9.0     # a row of words belongs to a staff at most this many gaps under its last line
WORD_NEAR = 1.6       # a syllable stands under its note: its middle or its start at most this many gaps from the head


def _codec(texts: Counter) -> str:
    """How a Sonata font's characters were turned into text: as Mac Roman or as Windows Latin. The codes of the
    note heads are the same in every such font, and a page of music is full of heads: the reading that finds more
    heads is the right one."""
    best, count = 'mac_roman', -1
    for codec in ('mac_roman', 'cp1252'):
        heads = 0
        for text, number in texts.items():
            try:
                code = text.encode(codec)[0]
            except (UnicodeEncodeError, IndexError):
                continue
            if SONATA.get(code, '').startswith('head'):
                heads += number
        if heads > count:
            best, count = codec, heads
    return best


def _signs(page) -> tuple[list[dict], list[dict]]:
    """(the signs of the music fonts, the other characters). Each sign: 'kind', 'x' (its origin), 'y' (its baseline,
    from the top of the page), 'wide' (its advance), 'size'."""
    music, plain = [], []
    fonts: dict[str, Counter] = {}
    for char in page.chars:
        name = char['fontname']
        if any(font in name for font in SONATA_FONTS):
            fonts.setdefault(name, Counter())[char['text']] += 1
    codecs = {name: _codec(texts) for name, texts in fonts.items()}
    for char in page.chars:
        name, text = char['fontname'], char['text']
        y = char['bottom'] - (char['matrix'][5] - char['y0'])
        sign = {'x': float(char['x0']), 'y': float(y), 'wide': float(char['x1'] - char['x0']), 'size': float(char['size']),
                'text': text}
        if any(font in name for font in SMUFL_FONTS):
            kind = SMUFL.get(ord(text[0])) if len(text) == 1 else None
        elif name in codecs:
            kind = None
            if len(text) == 1:
                if 0xF000 <= ord(text) <= 0xF0FF:
                    code = ord(text) - 0xF000
                elif text in ODD:
                    code = ODD[text]
                else:
                    try:
                        code = text.encode(codecs[name])[0]
                    except UnicodeEncodeError:
                        code = None
                kind = ODD_CLEFS.get(text) and 'maybe ' + ODD_CLEFS[text] or SONATA.get(code)
        else:
            if text.strip():
                plain.append(char)
            continue
        if kind:
            music.append(dict(sign, kind=kind))
    return music, plain


def _strokes(page) -> tuple[list[dict], list[dict], list[dict]]:
    """The drawn lines of a page as (level strokes, upright strokes, slanted thick strokes and filled shapes).
    A level stroke: 'y', 'x0', 'x1', 'thick'. An upright stroke: 'x', 'top', 'bottom'. A shape: its corner points."""
    level, upright, shapes = [], [], []

    def add(x0, top, x1, bottom, thick):
        if abs(bottom - top) <= THIN and x1 - x0 > abs(bottom - top):
            level.append({'y': (top + bottom) / 2, 'x0': x0, 'x1': x1, 'thick': max(thick, abs(bottom - top))})
        elif abs(x1 - x0) <= THIN:
            upright.append({'x': (x0 + x1) / 2, 'top': top, 'bottom': bottom})

    for line in page.lines:
        add(line['x0'], line['top'], line['x1'], line['bottom'], line.get('linewidth') or 0)
    for box in page.rects:
        if box.get('fill') or box.get('stroke'):
            if min(box['x1'] - box['x0'], box['bottom'] - box['top']) <= THIN:
                add(box['x0'], box['top'], box['x1'], box['bottom'], 0)
            else:
                shapes.append({'points': [(box['x0'], box['top']), (box['x1'], box['top']), (box['x1'], box['bottom']),
                                          (box['x0'], box['bottom'])], 'thick': 0})
    for curve in page.curves:
        points = [(float(x), float(y)) for x, y in curve.get('pts', [])]
        if len(points) >= 2 and points[0] == points[-1]:
            points = points[:-1]
        if len(points) == 2:
            (x0, y0), (x1, y1) = sorted(points)
            thick = curve.get('linewidth') or 0
            if abs(y1 - y0) <= 0.3 or abs(x1 - x0) <= 0.3:
                add(min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1), thick)
            elif curve.get('stroke') and thick > 0:
                # A thick slanted stroke (a beam of Encore): the shape that the stroke covers.
                half = thick / 2
                shapes.append({'points': [(x0, y0 - half), (x1, y1 - half), (x1, y1 + half), (x0, y0 + half)], 'thick': thick})
        elif len(points) == 4 and curve.get('fill'):
            shapes.append({'points': points, 'thick': 0})
        elif len(points) > 4:
            shapes.append({'points': points, 'thick': 0, 'bow': True, 'fill': bool(curve.get('fill'))})
    return level, upright, shapes


def _joined(level: list[dict]) -> list[dict]:
    """Level strokes that meet end to end at one height are one line (MuseScore draws a staff line bar by bar)."""
    out: list[dict] = []
    for stroke in sorted(level, key=lambda stroke: (round(stroke['y'], 1), stroke['x0'])):
        last = out[-1] if out else None
        if last and abs(last['y'] - stroke['y']) <= 0.25 and stroke['x0'] - last['x1'] <= 1.0 and last['x0'] - stroke['x1'] <= 1.0:
            if stroke['x1'] - stroke['x0'] > last['x1'] - last['x0']:
                last['y'] = stroke['y']
            last['x0'], last['x1'] = min(last['x0'], stroke['x0']), max(last['x1'], stroke['x1'])
        else:
            out.append(dict(stroke))
    return out


def _staves(level: list[dict], signs: list[dict]) -> list[dict]:
    """The staves: {'lines': the heights of the five lines from the top, 'gap', 'x0', 'x1'}."""
    staves = []
    long = [line for line in _joined(level) if line['x1'] - line['x0'] >= LONG]
    # Lines at one height (a thick line drawn as hairlines, or the two halves of a line) are one line.
    rows: list[dict] = []
    for line in sorted(long, key=lambda line: line['y']):
        if rows and line['y'] - rows[-1]['ys'][-1] <= 0.9:
            rows[-1]['ys'].append(line['y'])
            rows[-1]['x0'], rows[-1]['x1'] = min(rows[-1]['x0'], line['x0']), max(rows[-1]['x1'], line['x1'])
        else:
            rows.append({'ys': [line['y']], 'x0': line['x0'], 'x1': line['x1']})
    for row in rows:
        row['y'] = (row['ys'][0] + row['ys'][-1]) / 2
    # The five lines of a staff begin and end together: another long line between them (the line that holds a
    # syllable, a hairpin) does not.
    used: set[int] = set()
    for first in rows:
        if id(first) in used:
            continue
        like = [row for row in rows if id(row) not in used and abs(row['x0'] - first['x0']) <= 1.5
                and abs(row['x1'] - first['x1']) <= 1.5 and 0 <= row['y'] - first['y'] <= 4.2 * GAPS[1]]
        five = None
        for second in like[1:]:
            gap = second['y'] - first['y']
            if not GAPS[0] <= gap <= GAPS[1]:
                continue
            found = [first]
            for step in range(1, 5):
                near = [row for row in like if abs(row['y'] - (first['y'] + step * gap)) <= EVEN * gap]
                if not near:
                    break
                found.append(min(near, key=lambda row: abs(row['y'] - (first['y'] + step * gap))))
            if len(found) == 5:
                five = found
                break
        if five:
            used.update(id(row) for row in five)
            staves.append({'lines': [row['y'] for row in five], 'gap': (five[4]['y'] - five[0]['y']) / 4,
                           'x0': min(row['x0'] for row in five), 'x1': max(row['x1'] for row in five)})
    # Encore: the staff is a run of '=' signs. The baseline is the bottom line, and the sign is four gaps high.
    runs: dict[tuple, list[dict]] = {}
    for sign in signs:
        if sign['kind'] == 'staff':
            runs.setdefault((round(sign['y'], 1), round(sign['size'], 1)), []).append(sign)
    for (y, size), run in runs.items():
        if len(run) >= 3:
            gap = size / 4
            staves.append({'lines': [y - 4 * gap + step * gap for step in range(5)], 'gap': gap,
                           'x0': min(sign['x'] for sign in run), 'x1': max(sign['x'] + sign['wide'] for sign in run)})
    return sorted(staves, key=lambda staff: staff['lines'][0])


def _uprights(upright: list[dict]) -> list[dict]:
    """Upright strokes on one line that meet end to end are one stroke."""
    out: list[dict] = []
    for stroke in sorted(upright, key=lambda stroke: (round(stroke['x'], 1), stroke['top'])):
        last = out[-1] if out else None
        if last and abs(last['x'] - stroke['x']) <= 0.25 and stroke['top'] - last['bottom'] <= 0.6 and last['top'] - stroke['bottom'] <= 0.6:
            last['top'], last['bottom'] = min(last['top'], stroke['top']), max(last['bottom'], stroke['bottom'])
        else:
            out.append(dict(stroke))
    return out


def _at(points: list[tuple], x: float) -> tuple[float, float] | None:
    """The top and the bottom of a shape at a column, or None where the shape does not reach."""
    xs = [point[0] for point in points]
    if not min(xs) - 0.8 <= x <= max(xs) + 0.8:
        return None
    x = min(max(x, min(xs)), max(xs))
    rows = []
    for (x0, y0), (x1, y1) in zip(points, points[1:] + points[:1]):
        if x0 != x1 and min(x0, x1) <= x <= max(x0, x1):
            rows.append(y0 + (y1 - y0) * (x - x0) / (x1 - x0))
    return (min(rows), max(rows)) if rows else None


def read_pdf_page(path, number: int, title: str = '') -> dict | None:
    """Reads page `number` (from 1) of a PDF that notation software wrote. None when the page is not such a page:
    it has no signs of a music font, or no staff. The result is as reader.read_page() gives it; each note has its
    'lyric' where a syllable stands under it."""
    import pdfplumber

    with pdfplumber.open(str(path)) as pdf:
        if not 1 <= number <= len(pdf.pages):
            return None
        page = pdf.pages[number - 1]
        signs, plain = _signs(page)
        if not any(sign['kind'] in HEADS for sign in signs):
            return None
        level, upright, shapes = _strokes(page)
        words = page.extract_words(x_tolerance=1.5, y_tolerance=2, keep_blank_chars=False, extra_attrs=['fontname', 'size']) \
            if plain else []
        words = [word for word in words if not any(font in word['fontname'] for font in SONATA_FONTS + SMUFL_FONTS)]
    staves = _staves(level, signs)
    if not staves:
        return None
    return _read(staves, signs, level, _uprights(upright), shapes, words, title)


def _read(staves, signs, level, upright, shapes, words, title) -> dict:
    # Stems and bar lines of Encore are signs: a bar line at its origin, a stem as a pile of pieces at the head.
    for sign in signs:
        if sign['kind'] == 'bar':
            upright.append({'x': sign['x'], 'top': sign['y'] - sign['size'], 'bottom': sign['y'], 'bar': True})
    for index, staff in enumerate(staves):
        staff['index'] = index
        staff['top'], staff['bottom'], staff['middle'] = staff['lines'][0], staff['lines'][4], staff['lines'][2]
    # Systems: an upright stroke at the left that runs from one staff to the next joins them.
    system = 0
    for index, staff in enumerate(staves):
        if index:
            upper = staves[index - 1]
            joins = any(stroke['top'] <= upper['bottom'] + 0.5 * upper['gap'] and stroke['bottom'] >= staff['top'] - 0.5 * staff['gap']
                        and upper['x0'] - 3 * upper['gap'] <= stroke['x'] <= upper['x1'] + upper['gap'] for stroke in upright)
            if not joins:
                system += 1
        staff['system'] = system
    for staff in staves:
        staff['number'] = sum(1 for other in staves if other['system'] == staff['system'] and other['index'] < staff['index'])
    # Bar lines: upright strokes over the whole height of a staff.
    bars = {staff['index']: [] for staff in staves}
    stems = []
    for stroke in upright:
        crossed = [staff for staff in staves if stroke['top'] <= staff['top'] + 0.3 * staff['gap']
                   and stroke['bottom'] >= staff['bottom'] - 0.3 * staff['gap']
                   and staff['x0'] - staff['gap'] <= stroke['x'] <= staff['x1'] + staff['gap']]
        exact = [staff for staff in crossed if stroke.get('bar') or len(crossed) > 1
                 or (abs(stroke['top'] - staff['top']) <= 0.3 * staff['gap'] and abs(stroke['bottom'] - staff['bottom']) <= 0.3 * staff['gap'])]
        if exact:
            for staff in exact:
                bars[staff['index']].append(stroke['x'])
        else:
            stems.append(stroke)
    # Heads: each on the staff whose lines and spaces it fits, the nearest first.
    heads = []
    for sign in signs:
        if sign['kind'] not in HEADS:
            continue
        fits = []
        for staff in staves:
            if not staff['x0'] - staff['gap'] <= sign['x'] <= staff['x1'] + staff['gap']:
                continue
            place = (staff['middle'] - sign['y']) / (staff['gap'] / 2)
            if abs(place) <= 2 * NEAR_STAFF:
                fits.append((abs(place - round(place)) > ON_GRID, abs(place), staff, int(round(place))))
        if not fits:
            continue
        _, _, staff, place = min(fits, key=lambda fit: fit[:2])
        gap = staff['gap']
        heads.append({'staff': staff['index'], 'place': place, 'x0': sign['x'], 'x1': sign['x'] + sign['wide'],
                      'cx': sign['x'] + sign['wide'] / 2, 'cy': sign['y'], 'y0': sign['y'] - gap / 2, 'y1': sign['y'] + gap / 2,
                      'hollow': sign['kind'] != 'head black', 'whole': sign['kind'] in ('head whole', 'head breve'),
                      'breve': sign['kind'] == 'head breve', 'stems': [], 'tails': {}, 'small': sign['size'], 'gap': gap})
    # Stems of Encore: the pieces that stand at a head's origin.
    pieces = [sign for sign in signs if sign['kind'] in ('stem up', 'stem down')]
    for head in heads:
        gap = head['gap']
        for direction in ('up', 'down'):
            own = [piece for piece in pieces if piece['kind'] == 'stem ' + direction and abs(piece['x'] - head['x0']) <= 0.2 * gap
                   and -0.3 * gap <= (head['cy'] - piece['y'] if direction == 'up' else piece['y'] - head['cy']) <= 5 * gap]
            if own and any(abs(piece['y'] - head['cy']) <= 0.3 * gap for piece in own):
                if direction == 'up':
                    end = min(piece['y'] for piece in own) - gap
                    stems.append({'x': head['x1'], 'top': end, 'bottom': head['cy']})
                else:
                    end = max(piece['y'] for piece in own) + gap
                    stems.append({'x': head['x0'], 'top': head['cy'], 'bottom': end})
    # A stem and its heads: the stem stands at an edge of the head and passes it or ends at it.
    for stem in stems:
        own = []
        for head in heads:
            gap = head['gap']
            if head['whole'] or stem['bottom'] - stem['top'] < STEM_LEAST * gap:
                continue
            side = min(abs(stem['x'] - head['x0']), abs(stem['x'] - head['x1']))
            if side <= STEM_SIDE * gap and stem['top'] - STEM_END * gap <= head['cy'] <= stem['bottom'] + STEM_END * gap:
                own.append(head)
        if not own:
            continue
        above = min(head['cy'] for head in own) - stem['top']
        below = stem['bottom'] - max(head['cy'] for head in own)
        direction = 'up' if above >= below else 'down'
        end = stem['top'] if direction == 'up' else stem['bottom']
        gap = own[0]['gap']
        # Flags at the free end, and beams near it.
        tails = 0
        for sign in signs:
            if sign['kind'].startswith('flag') and abs(sign['x'] - stem['x']) <= FLAG_NEAR[0] * gap \
                    and abs(sign['y'] - end) <= FLAG_NEAR[1] * gap:
                tails = max(tails, int(sign['kind'][-1]))
        seen = []
        for shape in shapes:
            if shape.get('bow'):
                continue
            rows = _at(shape['points'], stem['x'])
            if rows is None:
                continue
            thick = rows[1] - rows[0]
            xs = [point[0] for point in shape['points']]
            middle = (rows[0] + rows[1]) / 2
            reach = (middle - end) if direction == 'up' else (end - middle)
            if BEAM_THICK[0] * gap <= thick <= BEAM_THICK[1] * gap and max(xs) - min(xs) >= 0.7 * gap \
                    and -0.6 * gap <= reach <= BEAM_REACH * gap and all(abs(middle - other) > 0.3 * gap for other in seen):
                seen.append(middle)
        tails = max(tails, len(seen))
        for head in own:
            if all(other['direction'] != direction for other in head['stems']):
                head['stems'].append({'direction': direction, 'x': stem['x'], 'end': end})
                head['tails'][direction] = tails
    # Dots, and the sharps, flats and naturals before a head.
    clefs, keys, ends = [], [], []
    for staff in staves:
        gap = staff['gap']
        near = [sign for sign in signs if staff['top'] - 4 * gap <= sign['y'] <= staff['bottom'] + 4 * gap
                and staff['x0'] - gap <= sign['x'] <= staff['x1']]
        clef_signs = sorted((sign for sign in near if sign['kind'].replace('maybe ', '').startswith('clef')
                             and sign['x'] <= staff['x0'] + 8 * gap), key=lambda sign: sign['x'])
        clef, edge = None, staff['x0']
        if clef_signs:
            sign = clef_signs[0]
            clef = {'clef G': 'G', 'clef G8': 'G8vb', 'clef F': 'F', 'clef C': 'C'}[sign['kind'].replace('maybe ', '')]
            edge = sign['x'] + max(sign['wide'], 2 * gap)
        first = min((head['x0'] for head in heads if head['staff'] == staff['index']), default=staff['x1'])
        count = 0
        for sign in sorted((sign for sign in near if sign['kind'] in ('sharp', 'flat', 'natural')), key=lambda sign: sign['x']):
            if sign['x'] - edge > KEY_STEP * gap or sign['x'] + sign['wide'] > first - 0.5 * gap:
                break
            sign['in_key'] = True
            edge = sign['x'] + sign['wide']
            count += {'sharp': 1, 'flat': -1, 'natural': 0}[sign['kind']]
        clefs.append(clef)
        keys.append(count)
        ends.append(edge)
    # A staff without a clef of its own (a page that shows the clefs on its first system only) keeps the clef and the
    # key of the staff over it at the same place in the system.
    for staff in staves:
        if clefs[staff['index']] is None:
            earlier = [other for other in staves if other['index'] < staff['index'] and other['number'] == staff['number']
                       and clefs[other['index']] is not None]
            clefs[staff['index']] = clefs[earlier[-1]['index']] if earlier else 'G'
            if earlier and keys[staff['index']] == 0:
                keys[staff['index']] = keys[earlier[-1]['index']]
    for head in heads:
        gap = head['gap']
        for sign in signs:
            if sign['kind'] == 'dot' and DOT_AT[0] * gap <= sign['x'] - head['x1'] + 0.3 * gap <= DOT_AT[1] * gap \
                    and -DOT_AT[2] * gap <= head['cy'] - sign['y'] <= DOT_AT[2] * gap:
                between = [other for other in heads if other is not head and other['staff'] == head['staff']
                           and head['x1'] < other['cx'] < sign['x'] and abs(other['cy'] - sign['y']) <= DOT_AT[2] * gap]
                if not between:
                    head['dot'] = True
            if sign['kind'] in ('sharp', 'flat', 'natural') and not sign.get('in_key') \
                    and 0 <= head['x0'] - sign['x'] <= SIGN_AT[0] * gap and abs(sign['y'] - head['cy']) <= SIGN_AT[1] * gap:
                between = [other for other in heads if other is not head and other['staff'] == head['staff']
                           and sign['x'] < other['cx'] < head['x0'] and other['place'] == head['place']]
                if not between:
                    head['sign'] = {'sharp': 1, 'flat': -1, 'natural': 0}[sign['kind']]
    _words(staves, heads, words)
    # Choir rule, as in the reader of scans: in a system of three or more staves, a treble staff over the bass
    # staff is the tenors'.
    width = max(staff['number'] for staff in staves) + 1
    if width >= 3:
        low = {staff['system']: clefs[staff['index']] for staff in staves if staff['number'] == width - 1}
        for staff in staves:
            if staff['number'] == width - 2 and clefs[staff['index']] == 'G' and low.get(staff['system']) == 'F':
                clefs[staff['index']] = 'G8vb'
    parts = [[] for _ in range(width + 1)]      # the last part is the ison of a chant page, where there is one
    notes = []
    for staff in staves:
        index, gap = staff['index'], staff['gap']
        own = [head for head in heads if head['staff'] == index]
        clef = clefs[index] if clefs[index] in ('G', 'G8vb', 'F') else 'G'
        plan = staff_columns(staff, own, bars[index], gap)
        drones = _drones(plan) if width == 1 else []
        for part, measures in ((staff['number'], plan), (width, drones)):
            for number, bar in enumerate(build_staff(staff, [], bars[index], clef, keys[index], gap, measures)):
                parts[part].append({'notes': bar, 'clef': clef, 'key': keys[index]})
                for note in bar:
                    head = note.pop('head')
                    if head.get('lyric') and note['voice'] == min(other['voice'] for other in bar if other['x'] == note['x']):
                        note['lyric'] = head['lyric']
                    notes.append(dict(note, staff=index, bar=number, onset=float(note['onset']), length=float(note['length']),
                                      ison=part == width))
    if not parts[width]:
        parts.pop()
    key = Counter(keys).most_common(1)[0][0] if keys else 0
    return {'musicxml': musicxml(parts, title), 'notes': notes, 'staves': len(staves),
            'systems': len({staff['system'] for staff in staves}), 'key': key, 'clefs': clefs, 'keys': keys,
            'heads': heads, 'bars': bars, 'vector': True}


def _drones(plan: list[list[list[dict]]]) -> list[list[list[dict]]]:
    """Takes the ison out of the notes of a chant staff, and gives it as bars of its own.

    A chant staff holds one voice, so a column holds one note. The ison is drawn under the melody as a whole note
    where it begins or moves: a column of two notes whose lower note is a whole note. It holds until the next one,
    so its length is not drawn; the whole note is written as it stands."""
    columns = [column for bar in plan for column in bar]
    single = sum(1 for column in columns if len(column) == 1)
    if not columns or single < 0.7 * len(columns):
        return []
    out = []
    for bar in plan:
        found = []
        for column in bar:
            if len(column) < 2:
                continue
            low = min(column, key=lambda event: event['place'])
            if low['head'].get('whole') and low['stem_x'] is None and sum(1 for event in column if event['place'] == low['place']) == 1:
                column.remove(low)
                found.append([dict(low, voice=1)])
        if found:
            out.append(found)
        bar[:] = [column for column in bar if column]
    return out


def _words(staves: list[dict], heads: list[dict], words: list[dict]) -> None:
    """Sets each syllable under its note: head['lyric'] = [the syllables of the rows under the head, from the top].
    A row of words belongs to the staff over it; a syllable to the head it stands under."""
    rows: dict[tuple, list[dict]] = {}
    for word in words:
        text = word['text'].strip('-_–—')
        if not text:
            continue
        over = [staff for staff in staves if staff['bottom'] < word['bottom'] <= staff['bottom'] + WORDS_UNDER * staff['gap']
                and staff['x0'] - 2 * staff['gap'] <= word['x0'] <= staff['x1']]
        if not over:
            continue
        staff = max(over, key=lambda staff: staff['bottom'])
        # The row must end over the next staff of the page.
        under = [other for other in staves if other['top'] > staff['bottom'] and other['x0'] <= word['x1'] and other['x1'] >= word['x0']]
        if under and word['bottom'] > min(other['top'] for other in under) + 0.5 * staff['gap']:
            continue
        rows.setdefault((staff['index'], round(word['bottom'] / 2)), []).append(dict(word, text=text))
    by_staff: dict[int, list[list[dict]]] = {}
    for (index, _), row in sorted(rows.items()):
        by_staff.setdefault(index, []).append(row)
    for index, staff_rows in by_staff.items():
        gap = staves[index]['gap']
        own = sorted((head for head in heads if head['staff'] == index), key=lambda head: head['cx'])
        if not own:
            continue
        verse = 0
        for row in staff_rows:
            placed = []
            for word in row:
                middle = (word['x0'] + word['x1']) / 2
                best = min(own, key=lambda head: min(abs(head['cx'] - middle), abs(head['cx'] - word['x0'] - 0.5 * gap)))
                apart = min(abs(best['cx'] - middle), abs(best['cx'] - word['x0'] - 0.5 * gap))
                if apart <= WORD_NEAR * gap:
                    placed.append((best, word['text']))
            # A row of words stands under the notes: most of its words find a note. A title or a note for the
            # singers does not.
            if len(placed) < max(1, 0.6 * len(row)):
                continue
            for head, text in placed:
                column = [other for other in own if abs(other['cx'] - head['cx']) <= 0.75 * gap]
                top = max(column, key=lambda other: other['place'])
                top.setdefault('lyrics', {}).setdefault(verse, []).append(text)
            verse += 1
    for head in heads:
        if head.get('lyrics'):
            first = min(head['lyrics'])
            head['lyric'] = ''.join(head['lyrics'][first]) if first == 0 else None
