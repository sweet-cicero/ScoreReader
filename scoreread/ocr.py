"""Reads the rows of the words of a scan with Tesseract, when it is installed. This is the one step that uses a model.

Tesseract is a small text reader that runs on this computer (Apache-2.0 licence). The reader does not need it: the
notes are read by rules alone, and the words can be read by the letter shapes of the hymn (scoreread.lyrics). Where
Tesseract is installed and asked for, it reads each row of words as one line of text, and this step cuts the line
into the syllables of the row with their places, so that scoreread.lyrics.set_under() can set them under the notes.

The rows are the reader's own (scoreread.words): Tesseract never sees the notes.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile

import cv2
import numpy as np

PROGRAM = 'tesseract'    # the program's name, or its path (SCOREREAD_TESSERACT names another)
LANGUAGE = 'eng'         # the language file (SCOREREAD_OCR_LANGUAGE names another, as 'eng+ell')
HIGH = 40                # a row of words is scaled so that its band is this many px high
AGAIN = (32, 50)         # a second look: the row is read again at these sizes, and the reading that fits best is kept.
#                          With a list of words that is the reading of which the list holds the most letters, else
#                          the one that Tesseract is surest of. A row whose words the list holds all is not read
#                          again (an empty tuple: each row is read once)
ROOM = (0.6, 2.0)        # the room kept over and under the band, and at its sides, in staff spaces
SURE = 20                # a word that Tesseract is less sure of than this (of 100) and that has under three letters is left out
ROW = 40                 # a row that Tesseract is less sure of than this, over all its letters, is no row of words (stray
#                          ink under a staff: a slur, a hairpin, the ends of stems). None: every row is kept
JOINS = '-‐‑‒–—~='     # what a hyphen between two syllables can be read as
STOPS = '.,;:!?'         # a dash after a syllable that ends with one of these is the line of a held syllable, no hyphen
LINES = '_'              # the line after a syllable that is held
CUT = (0.3, 2.0, 2, 1, 1.6, 0.2, 1.3)   # two words that Tesseract read as one are cut at a wide gap: the gap is
#                          this share of the row's height or more, and this many times the usual gap between the
#                          letters of the word; each part keeps this many letters or more. Only where each sign of
#                          the word is one piece of ink, so that the gaps can be counted: pieces this many px apart
#                          are one sign, and where one sign is missing, a piece this many times as wide as the usual
#                          piece is two signs that touch. A row whose letters stand all but as far apart, centre to
#                          centre (the distances differ by this share of the usual one at most), is from a
#                          typewriter: there the letters at the two sides of a cut stand this many times the usual
#                          distance apart (None: off)
MEND = (4, 2, 80, 50, 0.2)   # with a list of words: a word of this many letters or more that the list does not hold
#                          becomes the list's word that is one letter away (one letter more, less or other), when
#                          the list holds one such word only, and holds it this often or more. Only a word that
#                          Tesseract is less sure of than the third number is mended. The end of a word changes in
#                          the language itself (stone, stones): there the word is mended only when Tesseract is less
#                          sure of it than the fourth number. And only on a page of whose letters this share or more
#                          stands in words that the list holds: else the page is in another language than the list
#                          (None: off)
HELD = (1.2, 0.25, 0.35)   # the line of a held syllable is taken out of the picture before Tesseract
#                          reads the row: a level line this many times as long as the band is high or longer, this
#                          share of the band's height thick at most, that lies this near the band's lower edge
ENDS = (2, 2)            # with a list of words: a word that the list does not hold is parted where the list holds the
#                          words on both sides this often or more, each of this many letters or more; and two words
#                          are joined that the list holds as one word (None: off)
ABC = 'abcdefghijklmnopqrstuvwxyz'
VOWELS = 'aeiouy'


def program() -> str | None:
    """The path of Tesseract on this computer, or None when it is not installed."""
    return shutil.which(os.environ.get('SCOREREAD_TESSERACT', PROGRAM))


def available() -> bool:
    return program() is not None


def _line(crop: np.ndarray, folder: str, name: str) -> list[tuple[str, int, int, float]]:
    """The words of one line of text: (text, left, right, how sure) each, in the crop's px."""
    path = os.path.join(folder, name + '.png')
    cv2.imwrite(path, crop)
    # One thread: on a line of text Tesseract's threads only wait for each other, most of all on a busy computer.
    done = subprocess.run([program(), path, '-', '--psm', '7', '-l', os.environ.get('SCOREREAD_OCR_LANGUAGE', LANGUAGE),
                           'tsv'], capture_output=True, text=True, check=False,
                          env=dict(os.environ, OMP_THREAD_LIMIT='1'))
    found = []
    for row in done.stdout.splitlines()[1:]:
        cells = row.split('\t')
        if len(cells) < 12 or cells[0] != '5' or not cells[11].strip():
            continue
        found.append((cells[11].strip(), int(cells[6]), int(cells[6]) + int(cells[8]), float(cells[10])))
    return found


def _syllables(words: list[tuple[str, float, float, float]]) -> list[dict]:
    """Cuts the words of a line into syllables: {'text', 'x0', 'x1', 'join' (a hyphen follows), 'sure'} each. A hyphen
    stands alone between two syllables, or inside a word that the reader took for one; the line after a held
    syllable is no letter, and a dash after a comma or a full stop is such a line too."""
    found: list[dict] = []
    for text, left, right, sure in words:
        text = text.replace('|', '').strip(LINES)
        if not text:
            continue
        if all(sign in JOINS + LINES + '.,' for sign in text):
            if found and any(sign in JOINS for sign in text) and found[-1]['text'][-1] not in STOPS:
                found[-1]['join'] = True
            continue
        letters = sum(sign.isalpha() for sign in text)
        if letters == 0 or (sure < SURE and letters < 3):
            continue
        # The pieces between hyphens, each with its share of the word's width.
        wide = (right - left) / max(1, len(text))
        at = 0
        for piece in re.split('([' + re.escape(JOINS) + ']+|[' + re.escape(LINES) + ']+)', text):
            if piece and piece[0] in JOINS:
                if found and found[-1]['text'][-1] not in STOPS:
                    found[-1]['join'] = True
            elif piece and piece[0] not in LINES and any(sign.isalpha() for sign in piece):
                found.append({'text': piece, 'x0': left + wide * at, 'x1': left + wide * (at + len(piece)), 'join': False,
                              'sure': sure})
            at += len(piece)
    return found


def _pieces(text: str, columns: np.ndarray) -> list[tuple[int, int]]:
    """The pieces of ink of a word, column by column: (first column, last column) each. Pieces a px apart are one
    sign, and where one sign is missing, a piece much wider than the others is two signs that touch."""
    runs, start = [], None
    for column, inked in enumerate(list(columns) + [False]):
        if inked and start is None:
            start = column
        elif not inked and start is not None:
            runs.append((start, column - 1))
            start = None
    while len(runs) > len(text):
        gaps = [runs[number + 1][0] - runs[number][1] - 1 for number in range(len(runs) - 1)]
        least = min(range(len(gaps)), key=lambda number: gaps[number])
        if gaps[least] > CUT[3]:
            break
        runs[least:least + 2] = [(runs[least][0], runs[least + 1][1])]
    if len(runs) == len(text) - 1 and len(runs) >= 3:
        wide = [piece[1] - piece[0] + 1 for piece in runs]
        most = max(range(len(wide)), key=lambda number: wide[number])
        if wide[most] >= CUT[4] * float(np.median(wide)):
            begin, end = runs[most]
            runs[most:most + 1] = [(begin, (begin + end) // 2), ((begin + end) // 2 + 1, end)]
    return runs


def _pitch(texts: list[str], pieces: list[list[tuple[int, int]]]) -> tuple[float, float] | None:
    """How far apart the letters of a row stand, centre to centre: (the usual distance, how much the distances
    differ: the middle four fifths of them, as a share of the usual one). None with under eight distances. A
    typewriter sets each letter in a box of one width: its distances differ little."""
    apart = []
    for text, runs in zip(texts, pieces):
        if len(runs) != len(text):
            continue
        middle = [(first + last) / 2 for first, last in runs]
        apart += [middle[number + 1] - middle[number] for number in range(len(runs) - 1)
                  if text[number].isalpha() and text[number + 1].isalpha()]
    if len(apart) < 8:
        return None
    usual = float(np.median(apart))
    return usual, float(np.percentile(apart, 90) - np.percentile(apart, 10)) / max(1.0, usual)


def _cut_wide(words: list[tuple[str, float, float, float]], grey: np.ndarray, band: dict) -> list[tuple[str, float, float, float]]:
    """Cuts a word at its wide gaps. Where the words of a row stand close under quick notes, Tesseract reads two or
    three of them as one word. The pieces of ink in the word's box are counted, column by column: when each sign of
    the word is one piece, the gaps between the pieces are the gaps between its signs. A gap beside a hyphen is wide
    in any word and does not count. In a row from a typewriter the gap beside a thin letter (i, l) is wide in any
    word: there two words are parted only where their letters stand further apart than a letter's box."""
    found = []
    high = band['bottom'] - band['top']
    boxes = [(max(0, int(round(left))), min(grey.shape[1], int(round(right)) + 1)) for _, left, right, _ in words]
    pieces = [_pieces(text, (grey[int(band['top']):int(band['bottom']) + 1, first:last] < 128).any(axis=0))
              for (text, _, _, _), (first, last) in zip(words, boxes)]
    pitch = _pitch([text for text, _, _, _ in words], pieces)
    typed = pitch is not None and pitch[1] <= CUT[5]
    for (text, left, right, sure), (first, _), runs in zip(words, boxes, pieces):
        cuts = []
        if len(runs) == len(text) and len(text) >= 2 * CUT[2]:
            gaps = [runs[number + 1][0] - runs[number][1] - 1 for number in range(len(runs) - 1)]
            free = [number for number in range(len(gaps)) if text[number] not in JOINS + LINES and text[number + 1] not in JOINS + LINES]
            if len(free) >= 2:
                usual = float(np.median([gaps[number] for number in free]))
                cuts = [number + 1 for number in free if gaps[number] >= CUT[0] * high and gaps[number] >= CUT[1] * max(1.0, usual)]
                if typed:
                    cuts = [number for number in cuts
                            if (runs[number][0] + runs[number][1]) / 2 - (runs[number - 1][0] + runs[number - 1][1]) / 2 >= CUT[6] * pitch[0]]
                edges = [0] + cuts + [len(text)]
                if any(sum(sign.isalpha() for sign in text[begin:end]) < CUT[2] for begin, end in zip(edges, edges[1:])):
                    cuts = []
        if not cuts:
            found.append((text, left, right, sure))
            continue
        edges = [0] + cuts + [len(text)]
        for begin, end in zip(edges, edges[1:]):
            found.append((text[begin:end], float(first + runs[begin][0]), float(first + runs[end - 1][1]), sure))
    return found


def _known(lex) -> dict[str, int]:
    """The list of words by letters alone: {the letters of a word: how often}."""
    known: dict[str, int] = {}
    for word, count in (lex or {}).items():
        letters = ''.join(sign for sign in word.lower() if sign.isalpha())
        known[letters] = known.get(letters, 0) + count
    return known


def _ends(syllables: list[dict], known: dict[str, int]) -> list[dict]:
    """Sets where the words end by the list of words. Tesseract reads the line of a held syllable as a hyphen
    ('Thy-church'), it reads two words that stand close as one ('thelord'), and it misses a hyphen here and there
    ('re joice'). A word that the list does not hold is parted at the one place, at a hyphen or between two letters,
    where the list holds the words on both sides. Two words in a row are joined where the list holds them as one
    word and does not hold one of them alone."""
    found: list[dict] = []
    word: list[dict] = []
    for number, syllable in enumerate(syllables):
        word.append(dict(syllable))
        if syllable['join'] and number + 1 < len(syllables):
            continue
        places = [(part, at) for part in word for at, sign in enumerate(part['text']) if sign.isalpha()]
        read = ''.join(part['text'][at] for part, at in places).lower()
        cuts = [at for at in range(ENDS[1], len(read) - ENDS[1] + 1)
                if known.get(read[:at], 0) >= ENDS[0] and known.get(read[at:], 0) >= ENDS[0]] \
            if known.get(read, 0) < ENDS[0] else []
        if len(cuts) == 1:
            part, place = places[cuts[0]]
            before = places[cuts[0] - 1][0]
            if before is not part:
                before['join'] = False
            else:
                text, wide = part['text'], (part['x1'] - part['x0']) / max(1, len(part['text']))
                first = dict(part, text=text[:place], x1=part['x0'] + wide * place, join=False)
                part.update(text=text[place:], x0=part['x0'] + wide * place)
                word.insert(next(n for n, other in enumerate(word) if other is part), first)
        found.extend(word)
        word = []
    words, now = [], []
    for syllable in found:
        now.append(syllable)
        if not syllable['join']:
            words.append(now)
            now = []

    def holds(parts: list[dict]) -> bool:
        return known.get(''.join(sign for part in parts for sign in part['text'].lower() if sign.isalpha()), 0) >= ENDS[0]

    for first, second in zip(words, words[1:]):
        if first[-1]['text'][-1] not in STOPS and holds(first + second) and not (holds(first) and holds(second)):
            first[-1]['join'] = True
    return found


def _mend(syllables: list[dict], known: dict[str, int]) -> list[dict]:
    """Mends the words that the list of words does not hold. Tesseract reads a letter of a word wrongly here and
    there ('tnose', 'orlent', 'trinty'); the hymns of one church use the same words again and again, and the list
    tells which word was meant. A word is the syllables that hyphens join. Only letters count: capitals, commas and
    apostrophes stay as they were read. A word that the list holds is never changed, and a letter that is a whole
    syllable is never taken away (it is a word of its own whose hyphen was read wrongly: 'O-joy'). A vowel that is
    missing between two syllables becomes a syllable of its own ('Trin-ty' is 'Trin-i-ty'), unless the syllable
    before it has no vowel yet ('Gl-ry' is 'Glo-ry')."""
    found: list[dict] = []
    word: list[dict] = []
    for number, syllable in enumerate(syllables):
        word.append(dict(syllable))
        if syllable['join'] and number + 1 < len(syllables):
            continue
        places = [(part, at) for part in word for at, sign in enumerate(part['text']) if sign.isalpha()]
        read = ''.join(part['text'][at] for part, at in places).lower()
        sure = min(part.get('sure', 0.0) for part in word)
        found.extend(word)
        parts, word = word, []
        if len(read) < MEND[0] or read in known or sure >= MEND[2]:
            continue
        near = set()
        for at in range(len(read) + 1):
            near.update((at, 'more', read[:at] + sign + read[at:]) for sign in ABC)
            if at < len(read):
                near.add((at, 'less', read[:at] + read[at + 1:]))
                near.update((at, 'other', read[:at] + sign + read[at + 1:]) for sign in ABC if sign != read[at])
        meant = {new: (at, how) for at, how, new in sorted(near, reverse=True) if known.get(new, 0) >= MEND[1]}
        if len(meant) != 1:
            continue
        (new, (at, how)), = meant.items()
        if at >= len(read) - 1 + (how == 'more') and sure >= MEND[3]:
            continue
        part, place = places[min(at, len(places) - 1)]
        text = part['text']
        if how == 'less':
            if sum(sign.isalpha() for sign in text) > 1:
                part['text'] = text[:place] + text[place + 1:]
            continue
        sign = new[at].upper() if text[place].isupper() and (how == 'other' or text.isupper()) else new[at]
        if how == 'other':
            part['text'] = text[:place] + sign + text[place + 1:]
        elif at == len(places):
            part['text'] = text[:place + 1] + sign + text[place + 1:]
        elif at and places[at - 1][0] is not part and sign.lower() in VOWELS:
            before, last = places[at - 1]
            if any(other.lower() in VOWELS for other in before['text']):
                between = dict(before, text=sign, x0=before.get('x1', 0.0), x1=part.get('x0', 0.0), join=True)
                found.insert(len(found) - len(parts) + next(n for n, other in enumerate(parts) if other is part), between)
            else:
                before['text'] = before['text'][:last + 1] + sign + before['text'][last + 1:]
        else:
            part['text'] = text[:place] + sign + text[place:]
    return found


def _no_held(crop: np.ndarray, top: float, bottom: float) -> np.ndarray:
    """The picture of a row without the lines of held syllables. `top` and `bottom` are the band's edges in the
    picture. Tesseract reads such a line as a row of signs, and the word beside it wrongly."""
    high = bottom - top
    ink = (crop < 128).astype(np.uint8)
    long = cv2.morphologyEx(ink, cv2.MORPH_OPEN, np.ones((1, max(3, int(HELD[0] * high))), np.uint8))
    count, labels, boxes, _ = cv2.connectedComponentsWithStats(long, connectivity=8)
    out = crop
    for label in range(1, count):
        left, upper, wide, tall = boxes[label][:4]
        over = ink[max(0, upper - int(0.6 * high)):max(0, upper - 2), left:left + wide]
        if tall <= max(2.0, HELD[1] * high) and abs(upper + tall / 2 - bottom) <= HELD[2] * high \
                and (over.size == 0 or over.any(axis=0).mean() <= 0.15):     # no letters stand on it
            if out is crop:
                out = crop.copy()
            out[max(0, upper - 3):upper + tall + 3, max(0, left - 3):left + wide + 3] = 255     # with its pale rim
    return out


def _words_row(words: list[tuple[str, float, float, float]]) -> bool:
    """Whether a line of text is a row of words: how sure Tesseract is of its letters, each letter counted once."""
    if ROW is None:
        return True
    letters = [(sum(sign.isalpha() for sign in text), sure) for text, _, _, sure in words]
    count = sum(number for number, _ in letters)
    return count > 0 and sum(number * sure for number, sure in letters) / count >= ROW


def _text_row(words: list[tuple[str, float, float, float]], grey: np.ndarray, band: dict,
              known: dict[str, int], mend: bool = True) -> tuple[list[dict], float, bool]:
    """What one reading of a row gives: its syllables, how well the reading fits, and whether the list of words
    holds each of its words. The fit is the number of letters in words that the list holds, and among readings
    that are level there, or with no list, how sure Tesseract is of the letters."""
    if not _words_row(words):
        return [], -1.0, False
    letters = [(sum(sign.isalpha() for sign in text), sure) for text, _, _, sure in words]
    count = sum(number for number, _ in letters)
    sure = sum(number * sure for number, sure in letters) / count if count else 0.0
    if CUT:
        words = _cut_wide(words, grey, band)
    row = _syllables(words)
    if not known:
        return row, sure, False
    if ENDS:
        row = _ends(row, known)
    if MEND and mend:
        row = _mend(row, known)
    held, total = _held(row, known)
    return row, held + total * sure / 5000.0, 0 < total == held


def _fits(rows: list[tuple[list[tuple[str, float, float, float]], dict]], grey: np.ndarray, known: dict[str, int]) -> bool:
    """Whether the list of words fits the page: the share of the letters of its rows (the words that Tesseract
    read, and the band of each row) that stand in words of the list. A page in another language than the list
    holds few of its words, and the list would mend its words into words of the list's language."""
    held = total = 0
    for words, band in rows:
        row = _text_row(words, grey, band, known, False)[0]
        some, letters = _held(row, known)
        held, total = held + some, total + letters
    return bool(MEND) and held >= MEND[4] * total


def _held(row: list[dict], known: dict[str, int]) -> tuple[int, int]:
    """How many letters of a row stand in words that the list of words holds, and how many letters the row has."""
    held = total = 0
    now = ''
    for number, syllable in enumerate(row):
        now += ''.join(sign for sign in syllable['text'].lower() if sign.isalpha())
        if not syllable['join'] or number + 1 == len(row):
            total += len(now)
            held += len(now) if now in known else 0
            now = ''
    return held, total


def _pick(read, grey: np.ndarray, band: dict, known: dict[str, int], mend: bool = True) -> list[dict]:
    """The syllables of a row from the reading that fits best. `read(size)` gives Tesseract's words at one size."""
    best: tuple[list[dict], float] | None = None
    for size in (HIGH,) + tuple(AGAIN or ()):
        row, fit, whole = _text_row(read(size), grey, band, known, mend)
        if best is None or fit > best[1]:
            best = (row, fit)
        if whole:
            break
    return best[0] if best else []


def read_rows(layers: dict, page: int = 0, lex=None) -> list[dict]:
    """The syllables of the rows of words of a page, read with Tesseract: {'band': (page, the number of the row),
    'text', 'x0', 'x1', 'join'} each, as scoreread.lyrics.read_words() gives them. With a list of words (`lex`:
    {word: how often}) the words that the list does not hold are mended with it, the list sets where a word ends,
    and it chooses between the readings of a row at several sizes."""
    bands = layers.get('words') or []
    if not bands or not available():
        return []
    grey, space = layers['grey'], layers['space']
    height, width = grey.shape
    known = _known(lex)
    found = []
    with tempfile.TemporaryDirectory() as folder:
        readers = []
        for number, band in enumerate(bands):
            top, bottom = max(0, int(band['top'] - ROOM[0] * space)), min(height, int(band['bottom'] + ROOM[0] * space) + 1)
            first, last = max(0, int(band['x0'] - ROOM[1] * space)), min(width, int(band['x1'] + ROOM[1] * space) + 1)
            part = grey[top:bottom, first:last]
            if HELD:
                part = _no_held(part, band['top'] - top, band['bottom'] - top)
            seen: dict[int, list] = {}

            def read(size: int, part=part, first=first, band=band, number=number, seen=seen) -> list[tuple[str, float, float, float]]:
                if size not in seen:
                    scale = size / max(1.0, band['bottom'] - band['top'])
                    crop = cv2.resize(part, None, fx=scale, fy=scale,
                                      interpolation=cv2.INTER_CUBIC if scale > 1 else cv2.INTER_AREA)
                    edge = size // 2
                    crop = cv2.copyMakeBorder(crop, edge, edge, edge, edge, cv2.BORDER_CONSTANT, value=255)
                    seen[size] = [(text, first + (left - edge) / scale, first + (right - edge) / scale, sure)
                                  for text, left, right, sure in _line(crop, folder, f'{page}_{number}_{size}')]
                return seen[size]

            readers.append(read)
        mend = bool(known) and _fits([(read(HIGH), band) for read, band in zip(readers, bands)], grey, known)
        for number, (read, band) in enumerate(zip(readers, bands)):
            for syllable in _pick(read, grey, band, known, mend):
                found.append(dict(syllable, band=(page, number)))
    return found
