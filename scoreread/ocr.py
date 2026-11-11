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
ROOM = (0.6, 2.0)        # the room kept over and under the band, and at its sides, in staff spaces
SURE = 20                # a word that Tesseract is less sure of than this (of 100) and that has under three letters is left out
ROW = 40                 # a row that Tesseract is less sure of than this, over all its letters, is no row of words (stray
#                          ink under a staff: a slur, a hairpin, the ends of stems). None: every row is kept
JOINS = '-‐‑‒–—~='     # what a hyphen between two syllables can be read as
STOPS = '.,;:!?'         # a dash after a syllable that ends with one of these is the line of a held syllable, no hyphen
LINES = '_'              # the line after a syllable that is held


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
    """Cuts the words of a line into syllables: {'text', 'x0', 'x1', 'join' (a hyphen follows)} each. A hyphen
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
                found.append({'text': piece, 'x0': left + wide * at, 'x1': left + wide * (at + len(piece)), 'join': False})
            at += len(piece)
    return found


def _words_row(words: list[tuple[str, float, float, float]]) -> bool:
    """Whether a line of text is a row of words: how sure Tesseract is of its letters, each letter counted once."""
    if ROW is None:
        return True
    letters = [(sum(sign.isalpha() for sign in text), sure) for text, _, _, sure in words]
    count = sum(number for number, _ in letters)
    return count > 0 and sum(number * sure for number, sure in letters) / count >= ROW


def read_rows(layers: dict, page: int = 0) -> list[dict]:
    """The syllables of the rows of words of a page, read with Tesseract: {'band': (page, the number of the row),
    'text', 'x0', 'x1', 'join'} each, as scoreread.lyrics.read_words() gives them."""
    bands = layers.get('words') or []
    if not bands or not available():
        return []
    grey, space = layers['grey'], layers['space']
    height, width = grey.shape
    found = []
    with tempfile.TemporaryDirectory() as folder:
        for number, band in enumerate(bands):
            top, bottom = max(0, int(band['top'] - ROOM[0] * space)), min(height, int(band['bottom'] + ROOM[0] * space) + 1)
            first, last = max(0, int(band['x0'] - ROOM[1] * space)), min(width, int(band['x1'] + ROOM[1] * space) + 1)
            scale = HIGH / max(1.0, band['bottom'] - band['top'])
            crop = cv2.resize(grey[top:bottom, first:last], None, fx=scale, fy=scale,
                              interpolation=cv2.INTER_CUBIC if scale > 1 else cv2.INTER_AREA)
            edge = HIGH // 2
            crop = cv2.copyMakeBorder(crop, edge, edge, edge, edge, cv2.BORDER_CONSTANT, value=255)
            words = [(text, first + (left - edge) / scale, first + (right - edge) / scale, sure)
                     for text, left, right, sure in _line(crop, folder, f'{page}_{number}')]
            if not _words_row(words):
                continue
            for syllable in _syllables(words):
                found.append(dict(syllable, band=(page, number)))
    return found
