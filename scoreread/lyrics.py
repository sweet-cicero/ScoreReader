"""Reads the words under the notes of a scan with a list of words. No model is used.

scoreread.letters groups the letters of a hymn by shape, without names. The names are a puzzle that the hymn sets
itself: the same shape is the same letter in every word, and the words of the hymn are words of the list (the words
of other hymns, given by the user). The names under which the page reads most like the words of the list are the
names of the shapes. A letter's height (over the small letters, under the line), its dot and its holes say which
letters a shape can be at all.

Shapes that come once (a broken letter, letters that touch) get their names after that: from the named shape that
they are near, or as a row of named shapes side by side.

The steps: the kind of each glyph (letter, hyphen, comma), the syllables and the words of each row, the names of the
groups, the text of each syllable, and the note that each syllable stands under.
"""
from __future__ import annotations

import collections
import re
from pathlib import Path

import cv2
import numpy as np

from .letters import STRICT, differ, group_glyphs, normal

ASC = set('bdfhklt')    # the small letters that rise over the others
LETTERS = 'abcdefghijklmnopqrstuvwxyz'
TALL = 1.2              # a letter this many x-heights high rises over the small letters (b, d, h, a capital)
DEEP = 0.2              # a letter that reaches this many x-heights under the line goes down (g, j, p, q, y)
HYPHEN = (0.5, 0.15, 0.9)   # a thick hyphen: at most this many x-heights high, at least as wide as high, and it hangs
#                             between this many x-heights over the line and this many
GAP = 0.45              # two letters this many x-heights apart are two syllables
GAP_WIDE = 2.5          # or this many times the usual gap between two letters, where that is more (a typewriter sets
#                         its letters far apart, and most of all a thin one, as an i)
CAPITALS = (0.15, 0.06, 1.5)    # words in capitals only: under this share of the letters rises, under this share goes
#                                 down; the shapes are then compared at this many times the size
TOUCH = 1.9             # a group this many times as wide as the usual letter holds letters that touch
HOLED = {'a': 1, 'b': 1, 'd': 1, 'e': 1, 'g': 1, 'o': 1, 'p': 1, 'q': 1}    # the holes of a small letter
HOLED_TALL = {'a': 1, 'b': 2, 'd': 1, 'o': 1, 'p': 1, 'q': 1, 'r': 1}       # and of a capital
HOLE = -2.0             # a name whose letter has another count of holes than the shape costs this at each place
HOLE_SURE = 0.75        # when this share of the glyphs of the group has one count of holes
HOLE_AREA = 0.012       # a hole is at least this share of a square x-height
WORD = 4.0              # a whole word of the list counts this much more than its runs of three letters
UNNAMED = -4.5          # a letter with no name counts as a rare letter
MISS = -14.0            # the score of a word that is not in the list (the rarest word of the list has about -10)
VOTE = 0.5              # the first names: a group is named while the words vote for a letter with this weight
SHAKE = (6.0, 0.4, 8000, 600000)    # the shaking of the names: its heat at first and at last, the tries for each
#                                     group, and the most tries in all
BEGINS = 6              # more beginnings for the names, each a shake of the best names so far
EACH = 0.05             # each shape more in a row of touching letters costs this share of the ink
SPLIT = 0.5             # a row of shapes names touching letters when it misses under this share of their ink
ALIKE = (0.4, 12)       # a lone shape has the name of a named shape that it differs from by under this share of the
#                         ink and by no piece of this many points
MEND = (1, 2, 3.0)      # a word that is no word of the list is mended when a word of the list fits it but for this
#                         many letters (a word of up to five letters, a longer word), and that word is this many
#                         times as usual as the next one that fits as well
KNOWN = (0.2, 3.0)      # a shape that an earlier hymn named: a group that differs from it by under this share of the ink,
#                         and by no piece of ink, gets up to this much for that name at each place
KNOWN_LOOK = 24         # this many of the nearest known shapes are looked at for a group
KNOWN_SURE = (0.12, 0.05)   # a group has the name of a known shape at once when it differs from it by under this share
#                         of the ink, and from every known shape with another name by this share more (None: off)
SURE = (0.6, 0.8, 3)    # a hymn teaches its shapes when this share of its words are words of the list; a shape, when
#                         this share of the words of four letters or more that hold it are, and it stands in this many
#                         such words and has this many glyphs
DOUBLE = 1.4            # a letter with no name that is this many times as wide as the usual letter can be two letters
UNDER = 3.0             # a syllable stands at most this many staff spaces beside its note
RECITED = True          # a syllable that has no note of its own is sung on the note before it (a reciting note holds
#                         many syllables, and a note that was not read must not cost its syllable): it is written
#                         after that note's syllable. False: such a syllable is left out


def load_words(path: str | Path) -> collections.Counter:
    """The list of words from a text file: {word: how often}. The file holds plain text (each word counts once
    each time it stands there) or lines of a word and its count. Small letters and the apostrophe count; all
    else parts the words."""
    counts: collections.Counter = collections.Counter()
    last = None
    for token in re.findall(r"[A-Za-z'’]+|\d+", Path(path).read_text(encoding='utf-8')):
        if token.isdigit():
            if last:
                counts[last] += int(token) - 1
            last = None
            continue
        last = token.lower().replace('’', "'").strip("'")
        if last:
            counts[last] += 1
    return counts


def kind_of(glyph: dict) -> str:
    """What a glyph is by its size and its place on the line alone: 'letter', 'hyphen', 'line' (the line that
    holds a syllable), 'dot', 'comma', 'high' (an apostrophe) or 'mark' (a stem or a slur that reaches into the
    words)."""
    xh, base = glyph['xh'], glyph['base']
    high, wide = glyph['y1'] - glyph['y0'] + 1, glyph['x1'] - glyph['x0'] + 1
    middle = (glyph['y0'] + glyph['y1']) / 2
    if wide >= 1.5 * high and high <= 0.35 * xh:
        if abs(middle - base) <= 0.3 * xh and wide >= 0.9 * xh:
            return 'line'
        if base - 0.85 * xh <= middle <= base - 0.15 * xh and wide <= 1.5 * xh:
            return 'hyphen'
        return 'line' if middle > base - 0.3 * xh else 'mark'
    if high > 1.9 * xh:
        return 'mark'
    if HYPHEN and high <= HYPHEN[0] * xh and high <= wide <= 1.5 * xh \
            and glyph['y1'] <= base - HYPHEN[1] * xh and glyph['y0'] >= base - HYPHEN[2] * xh:
        return 'hyphen'     # the short thick hyphen of a bold type: no letter is so low and hangs over the line
    if high <= 0.75 * xh and wide <= 0.45 * xh:
        if glyph['y1'] < base - 0.5 * xh:
            return 'high'
        if glyph['y0'] > base - 0.45 * xh:
            return 'dot' if glyph['y1'] <= base + 0.15 * xh else 'comma'
    return 'letter'


def _rise(glyph: dict) -> float:
    return (glyph['base'] - glyph['y0'] + 1) / glyph['xh']


def _fall(glyph: dict) -> float:
    return (glyph['y1'] - glyph['base']) / glyph['xh']


def shape_class(glyphs: list[dict]) -> set[str]:
    """The letters that a group can be, by how most of its glyphs rise over the small letters and go down under
    the line, and by a dot. (A capital is written here as its small letter: a group has one name.)"""
    if np.median([_fall(glyph) for glyph in glyphs]) >= DEEP:
        return set('gjpqy')
    if np.median([glyph['parts'] for glyph in glyphs]) >= 2:
        return set('ij')
    if np.median([_rise(glyph) for glyph in glyphs]) >= TALL:
        return set(LETTERS)         # b, d, f, h, k, l, t, or any capital
    return set('acemnorsuvwxz')


def holes_of(glyph: dict) -> int:
    """The count of holes of a glyph: the white that its ink closes in."""
    white = np.pad(~glyph['mask'], 1, constant_values=True).astype(np.uint8)
    count, labels, stats, _ = cv2.connectedComponentsWithStats(white, connectivity=4)
    least = max(2, HOLE_AREA * glyph['xh'] ** 2)
    return sum(1 for label in range(1, count) if label != labels[0, 0] and stats[label][4] >= least)


def hole_bias(glyphs: list[dict], capitals: bool) -> dict[str, float]:
    """What each name costs a group by its holes: {letter: cost}. An o has a hole and a c has none; a thick copy
    fills a hole and a thin one opens it, so the holes cost a little and forbid nothing, and they count only when
    the glyphs of the group agree."""
    counts = collections.Counter(min(2, holes_of(glyph)) for glyph in glyphs)
    holes, share = counts.most_common(1)[0]
    if len(glyphs) < 2 or share < HOLE_SURE * len(glyphs):
        return {}
    tall = np.median([_rise(glyph) for glyph in glyphs]) >= TALL
    bias = {}
    for letter in LETTERS:
        allowed = set()
        if capitals or tall:
            allowed.add(HOLED_TALL.get(letter, 0))
        if not capitals and (not tall or letter in ASC or letter == 'i'):
            allowed.add(HOLED.get(letter, 0))
        if not capitals and letter == 'g':
            allowed.add(2)
        if holes not in allowed:
            bias[letter] = HOLE
    return bias


def syllables_of(glyphs: list[dict]) -> list[dict]:
    """The glyphs of each row as syllables, in the order of the rows and from the left: {'band', 'glyphs', 'join'
    (a hyphen follows: the word goes on)} each. A gap or a hyphen ends a syllable."""
    found = []
    rows = [sorted((glyph for glyph in glyphs if glyph['band'] == band), key=lambda glyph: glyph['x0'])
            for band in sorted({glyph['band'] for glyph in glyphs})]
    # Most letters stand beside a letter of their own syllable: the usual gap of the hymn is a gap inside a syllable.
    gaps = [(glyph['x0'] - before['x1']) / glyph['xh'] for row in rows for before, glyph in zip(row, row[1:])
            if before['kind'] == 'letter' and glyph['kind'] == 'letter']
    apart = max(GAP, GAP_WIDE * float(np.median(gaps))) if gaps else GAP
    for row in rows:
        band = row[0]['band']
        now = None
        for index, glyph in enumerate(row):
            kind = glyph['kind']
            gap = glyph['x0'] - row[index - 1]['x1'] if index else 99
            if kind == 'hyphen':
                if now is not None:
                    now['join'] = True
                    found.append(now)
                    now = None
                elif found and found[-1]['band'] == band:
                    found[-1]['join'] = True
                continue
            if kind in ('line', 'mark'):
                if now is not None:
                    found.append(now)
                    now = None
                continue
            if now is not None and gap > apart * glyph['xh'] and kind == 'letter':
                found.append(now)
                now = None
            if now is None:
                if kind != 'letter':
                    continue        # a comma with no word before it
                now = {'band': band, 'glyphs': [], 'join': False}
            now['glyphs'].append(glyph)
        if now is not None:
            found.append(now)
    return found


def words_of(syllables: list[dict]) -> list[list[dict]]:
    """Whole words: the syllables that hyphens join, within a row (a word cut at the end of a row is left out)."""
    words, now = [], []
    for index, syllable in enumerate(syllables):
        now.append(syllable)
        last = index + 1 == len(syllables) or syllables[index + 1]['band'] != syllable['band']
        if not syllable['join']:
            words.append(now)
            now = []
        elif last:
            now = []
    return words


def _codes(words: list[list[dict]]) -> list[list]:
    """Each word as its signs: the number of the group for a letter, and the apostrophe as itself."""
    codes = []
    for word in words:
        code = [glyph['group'] if glyph['kind'] == 'letter' else "'" for syllable in word for glyph in syllable['glyphs']
                if glyph['kind'] in ('letter', 'high')]
        while code and code[-1] == "'":
            code.pop()
        codes.append(code)
    return codes


def name_groups(words: list[list[dict]], classes: dict[int, set[str]], lex: collections.Counter,
                bias: dict[int, dict[str, float]] | None = None) -> tuple[dict[int, str], dict[str, float]]:
    """Names the groups of shapes: {group: letter}, and the score of each word of the list.

    First the words vote: a word of the page can be each word of the list in which the same shape is the same
    letter, and the group that the words agree on best is named, and so on. Then the names are tried against the
    whole page: a word of the list counts, and so does every run of three letters that the words of the list often
    have (so a piece of a word counts too). The names are shaken, much at first and then less and less, so that
    three or four names that are wrong together can come right together; the best names of several beginnings
    stay. The shakes are the same each time: a page reads the same each time."""
    bias = bias or {}
    total = sum(lex.values())
    logp = {word: float(np.log((count + 0.5) / total)) for word, count in lex.items()}
    by_length = collections.defaultdict(list)
    counts3, counts2 = collections.Counter(), collections.Counter()
    for word, count in lex.items():
        by_length[len(word)].append((word, count))
        padded = '^^' + word + '$'
        for at in range(2, len(padded)):
            counts3[padded[at - 2:at + 1]] += count
            counts2[padded[at - 2:at]] += count
    memo: dict[str, float] = {}

    def threes(text: str) -> float:
        """How usual the runs of three letters of a word are in the words of the list (a log share for each letter)."""
        if text not in memo:
            padded = '^^' + text + '$'
            memo[text] = sum(float(np.log((counts3[padded[at - 2:at + 1]] + 0.05) / (counts2[padded[at - 2:at]] + 0.05 * 28)))
                             for at in range(2, len(padded)))
        return memo[text]

    codes = [code for code in _codes(words) if code and all(sign == "'" or sign in classes for sign in code)]
    named: dict[int, str] = {}

    def candidates(code: list) -> list[tuple[str, int]]:
        found = []
        for word, count in by_length.get(len(code), []):
            seen = {}
            for group, letter in zip(code, word):
                if group == "'":
                    if letter != "'":
                        break
                    continue
                if letter == "'" or named.get(group, letter) != letter or seen.setdefault(group, letter) != letter:
                    break
                if group not in named and letter not in classes[group]:
                    break
            else:
                found.append((word, count))
        return found

    while True:
        votes = collections.defaultdict(collections.Counter)
        for code in codes:
            if all(group == "'" or group in named for group in code):
                continue
            found = candidates(code)
            if not found:
                continue
            all_counts = sum(count for _, count in found)
            weight = 1.0 / (1 + sum(1 for group in set(code) if group != "'" and group not in named)) ** 0.5
            for word, count in found:
                for group, letter in set(zip(code, word)):
                    if group != "'" and group not in named:
                        votes[group][letter] += weight * count / all_counts
        best = None
        for group, tally in votes.items():
            ranked = tally.most_common(2)
            first = ranked[0][1]
            second = ranked[1][1] if len(ranked) > 1 else 0.0
            sure = (first - second) * (first / (first + second))
            if best is None or sure > best[0]:
                best = (sure, group, ranked[0][0], first)
        if best is None or best[3] < VOTE:
            break
        named[best[1]] = best[2]

    holds = collections.defaultdict(list)
    for index, code in enumerate(codes):
        for group in set(code):
            if group != "'":
                holds[group].append(index)
    order = sorted(holds, key=lambda group: -len(holds[group]))
    options = {group: [letter for letter in LETTERS if letter in classes[group]] for group in order}

    def score(index: int) -> float:
        code = codes[index]
        shape = sum(bias[group].get(named[group], 0.0) for group in code if group in bias and group in named)
        if any(group != "'" and group not in named for group in code):
            text = ''.join(group if group == "'" else named.get(group, '?') for group in code)
            return shape + sum(threes(piece) for piece in text.split('?') if piece) + UNNAMED * text.count('?')
        text = ''.join(group if group == "'" else named[group] for group in code)
        return shape + threes(text) + (WORD if text in logp else 0.0)

    def climb() -> float:
        """One name at a time is changed where the page then reads more like the words of the list, and two groups
        change their names with each other, until nothing changes."""
        for _ in range(8):
            changed = False
            for group in order:
                before = named.get(group)
                best_letter, best_score = before, sum(score(index) for index in holds[group])
                for letter in options[group]:
                    if letter == before:
                        continue
                    named[group] = letter
                    now = sum(score(index) for index in holds[group])
                    if now > best_score + 1e-9:
                        best_letter, best_score = letter, now
                if best_letter is None:
                    named.pop(group, None)
                else:
                    named[group] = best_letter
                changed = changed or best_letter != before
            for one in order[:24]:
                for other in order[:24]:
                    if one >= other or one not in named or other not in named or named[one] == named[other]:
                        continue
                    if named[other] not in classes[one] or named[one] not in classes[other]:
                        continue
                    touched = set(holds[one]) | set(holds[other])
                    before = sum(score(index) for index in touched)
                    named[one], named[other] = named[other], named[one]
                    if sum(score(index) for index in touched) > before + 1e-9:
                        changed = True
                    else:
                        named[one], named[other] = named[other], named[one]
            if not changed:
                break
        return sum(score(index) for index in range(len(codes)))

    # A beginning with no word: the commonest shape is the commonest letter that it can be, and so on.
    usual = [letter for letter, _ in collections.Counter(''.join(word * count for word, count in lex.items())).most_common()
             if letter in LETTERS]
    by_rank, free = {}, list(usual)
    for group in order:
        letter = next((letter for letter in free if letter in classes[group]), None)
        if letter:
            by_rank[group] = letter
            free.remove(letter)
            if not free:
                free = list(usual)
    rng = np.random.RandomState(7)

    def shake(start: dict[int, str]) -> None:
        named.clear()
        named.update(start)
        for group in order:
            if group not in named:
                named[group] = by_rank.get(group, options[group][0])
        now = [score(index) for index in range(len(codes))]
        total_now = sum(now)
        best_names, best_at = dict(named), total_now
        steps = min(SHAKE[2] * len(order), SHAKE[3])
        for step in range(steps):
            heat = SHAKE[0] * (SHAKE[1] / SHAKE[0]) ** (step / steps)
            one = order[rng.randint(len(order))]
            if rng.rand() < 0.3:
                other = order[rng.randint(len(order))]
                if named[one] == named[other] or named[other] not in classes[one] or named[one] not in classes[other]:
                    continue
                touched = set(holds[one]) | set(holds[other])
                undo = ((one, named[one]), (other, named[other]))
                named[one], named[other] = named[other], named[one]
            else:
                letter = options[one][rng.randint(len(options[one]))]
                if letter == named[one]:
                    continue
                touched = holds[one]
                undo = ((one, named[one]),)
                named[one] = letter
            new = {index: score(index) for index in touched}
            gain = sum(new.values()) - sum(now[index] for index in touched)
            if gain >= 0 or rng.rand() < np.exp(gain / heat):
                for index, value in new.items():
                    now[index] = value
                total_now += gain
                if total_now > best_at + 1e-9:
                    best_names, best_at = dict(named), total_now
            else:
                for group, letter in undo:
                    named[group] = letter
        named.clear()
        named.update(best_names)

    begins = [dict(named), by_rank]
    best_names, best_total = {}, None
    turn = 0
    while turn < len(begins) and order:
        named.clear()
        named.update(begins[turn])
        if SHAKE and turn == 1:
            shake(best_names)
        total_now = climb()
        if best_total is None or total_now > best_total:
            best_names, best_total = dict(named), total_now
        if turn >= 1 and len(begins) < 2 + BEGINS:
            shaken = dict(best_names)
            for group in order:
                if rng.rand() < 0.25:
                    shaken[group] = options[group][rng.randint(len(options[group]))]
            begins.append(shaken)
        turn += 1
    return best_names, logp


def split_touching(mean: np.ndarray, wide: float, templates: list[tuple], keep: int = 5) -> list[tuple[float, str]]:
    """Letters that touch, read with the hymn's own shapes: the rows of named shapes, side by side, that cover the
    ink best. Returns [(the share of the ink that the row misses, its text)], the best first."""
    ink = float(mean.sum())
    width = int(min(mean.shape[1], round(wide) + 1))
    if ink <= 0 or not templates:
        return []
    best = {0: [(0.0, '')]}
    for x in range(width):
        for cost, text in best.get(x, []):
            for letter, shape, w in templates:
                w = int(round(w))
                if w < 3:
                    continue
                for lap in ((0,) if x == 0 else (0, 1, 2)):
                    start = x - lap
                    end = min(start + w, mean.shape[1])
                    if start + w > width + 2 or end <= x:
                        continue
                    window, part = mean[:, start:end], shape[:, :end - start]
                    # Where the shape lies over the letter before it, only its ink that the glyph lacks counts.
                    miss = float(np.abs(window[:, lap:] - part[:, lap:]).sum()) \
                        + float(np.clip(part[:, :lap] - window[:, :lap], 0, None).sum())
                    row = best.setdefault(min(start + w, width), [])
                    if all(other != text + letter for _, other in row):
                        row.append((cost + miss + EACH * ink, text + letter))
                        row.sort()
                        del row[keep:]
    ends = sorted((cost + float(mean[:, x:width].sum()), text) for x, row in best.items() if x >= width - 3
                  for cost, text in row if len(text) >= 2)
    found = []
    for cost, text in ends:
        if all(text != other for _, other in found):
            found.append((cost / ink - EACH * len(text), text))
    return found[:keep]


def name_rest(groups: list[dict], members: dict[int, list[dict]], named: dict[int, str], classes: dict[int, set[str]],
              score) -> dict[int, str]:
    """The names of the groups that the words did not name: {group: text}. A lone shape can have the name of a
    named shape that it is near; letters that touch are a row of the hymn's own shapes. Of the names that the
    shapes allow, the one that makes the most words of the list stays."""
    templates = [(named[group], groups[group]['mean'], groups[group]['wide']) for group in named if len(members[group]) >= 2]
    more: dict[int, str] = {}
    for group in sorted(members, key=lambda group: -len(members[group])):
        if group in named:
            continue
        mean, wide = groups[group]['mean'], groups[group]['wide']
        options = []
        if group in classes:
            for letter, shape, w in templates:
                if abs(w - wide) > 0.25 * max(w, wide) + 1:
                    continue
                share, lacks = differ(shape, mean)
                if share < ALIKE[0] and lacks < ALIKE[1]:
                    options.append((share, letter))
            options = sorted(options)[:4]
        if not options:
            options = [(cost, text) for cost, text in split_touching(mean, wide, templates) if cost < SPLIT]
        if not options:
            continue
        tried = {}
        for cost, text in options:
            if text not in tried:
                tried[text] = score(group, text, more) - 8.0 * cost
        more[group] = max(tried, key=tried.get)
    return more


def _fit(plain: str, double: list[bool], other: str, most: int) -> tuple[int, list[str]] | None:
    """How a word of the list fits a word of the page: (how many named letters are wrong, the letters of the word
    of the list for each sign of the page), or None when more than `most` are wrong. A letter with no name fits
    every letter, and a wide one fits two (letters that touch, as Th)."""
    best: list = [None]

    def walk(at: int, into: int, wrong: int, parts: list[str]) -> None:
        if wrong > most or (best[0] is not None and wrong >= best[0][0]):
            return
        if at == len(plain):
            if into == len(other):
                best[0] = (wrong, list(parts))
            return
        if into >= len(other) or len(other) - into < len(plain) - at:
            return
        sign, letter = plain[at], other[into]
        if sign == '?':
            if letter != "'":
                walk(at + 1, into + 1, wrong, parts + [letter])
                if double[at] and into + 1 < len(other) and other[into + 1] != "'":
                    walk(at + 1, into + 2, wrong, parts + [other[into:into + 2]])
        elif sign == letter:
            walk(at + 1, into + 1, wrong, parts + [letter])
        elif "'" not in (sign, letter):
            walk(at + 1, into + 1, wrong + 1, parts + [letter])

    walk(0, 0, 0, [])
    return best[0]


def mend_words(words: list[list[dict]], lex: collections.Counter) -> int:
    """Mends the words of the page that are no words of the list: a word that one word of the list fits, but for
    a letter or two (a letter with no name fits every letter, and a wide one fits two), becomes that word. The
    mend must be clear: the word of the list is much more usual than the next one that fits as well. Returns how
    many words were mended."""
    by_length = collections.defaultdict(list)
    for word, count in lex.items():
        by_length[len(word)].append((word, count))
    mended = 0
    for word in words:
        places = [(syllable, at) for syllable in word for at, sign in enumerate(syllable['text']) if sign.isalpha() or sign in "?'"]
        while places and places[-1][0]['text'][places[-1][1]] == "'":
            places.pop()
        plain = ''.join(syllable['text'][at] for syllable, at in places).lower()
        unnamed = plain.count('?')
        if not plain or (not unnamed and plain in lex) or 2 * unnamed > len(plain):
            continue
        double = [at in syllable.get('double', ()) for syllable, at in places]
        most = MEND[0] if len(plain) <= 5 else MEND[1]
        fits = []
        for length in range(len(plain), len(plain) + min(2, sum(double)) + 1):
            for other, count in by_length.get(length, []):
                fit = _fit(plain, double, other, most)
                if fit is not None:
                    fits.append((fit[0], -count, other, fit[1]))
        if not fits:
            continue
        fits.sort()
        wrong, count, _, parts = fits[0]
        if len(fits) > 1 and fits[1][0] == wrong and -count < MEND[2] * -fits[1][1]:
            continue
        for (syllable, at), sign, part in reversed(list(zip(places, plain, parts))):
            if sign != part:
                text = syllable['text']
                syllable['text'] = text[:at] + (part.upper() if text[at].isupper() else part) + text[at + 1:]
        mended += 1
    return mended


SHAPE_KEYS = ('wide', 'size', 'glyphs', 'words', 'right', 'hymn')


def load_shapes(path: str | Path) -> list[dict]:
    """The shapes that earlier hymns named, from the file that save_shapes() wrote (see named_shapes()). An empty
    list when there is no such file."""
    path = Path(path)
    if not path.exists():
        return []
    with np.load(path, allow_pickle=False) as held:
        return [dict({key: float(held[key][at]) for key in SHAPE_KEYS}, letter=str(held['letters'][at]),
                     source=str(held['sources'][at]), mean=held['means'][at].astype(np.float32) / 255.0)
                for at in range(len(held['letters']))]


def save_shapes(path: str | Path, shapes: list[dict]) -> None:
    """Writes the named shapes to a file (NumPy's own format: the letters, their shapes on the canvas as pictures,
    the hymn that each came from, and the numbers of named_shapes())."""
    with open(path, 'wb') as file:      # (NumPy adds '.npz' to a name, but not to an open file)
        np.savez_compressed(file, letters=np.array([shape['letter'] for shape in shapes]),
                            means=np.array([np.clip(shape['mean'] * 255.0, 0, 255) for shape in shapes]).astype(np.uint8),
                            sources=np.array([shape['source'] for shape in shapes]),
                            **{key: np.array([shape[key] for shape in shapes], np.float32) for key in SHAPE_KEYS})


def _coarse(mean: np.ndarray) -> np.ndarray:
    """A shape at a quarter of its size, for a first fast look."""
    rows, columns = mean.shape[0] // 4, mean.shape[1] // 4
    return mean[:rows * 4, :columns * 4].reshape(rows, 4, columns, 4).mean(axis=(1, 3)).ravel()


def known_bias(groups: list[dict], wanted, shapes: list[dict], size: float) -> tuple[dict, dict]:
    """What the shapes that earlier hymns named say about the groups of this hymn: ({group: {letter: gain}},
    {group: letter} for the groups whose shape is known for sure). The scores of one choir come from few hands and
    few types, so a shape that one hymn has named can name the same shape in the next hymn, where the text is too
    short for the puzzle alone, or the letter too rare (a capital stands once or twice in a hymn)."""
    held = [shape for shape in shapes if shape['size'] == size and shape['hymn'] >= SURE[0]
            and shape['glyphs'] >= SURE[2] and shape['words'] >= SURE[2] and shape['right'] >= SURE[1] * shape['words']]
    if not held:
        return {}, {}
    coarse = np.array([_coarse(shape['mean']) for shape in held])
    widths = np.array([shape['wide'] for shape in held])
    bias: dict[int, dict[str, float]] = {}
    sure: dict[int, str] = {}
    for group in wanted:
        mean, wide = groups[group]['mean'], groups[group]['wide']
        near = np.nonzero(np.abs(widths - wide) <= 0.25 * np.maximum(widths, wide) + 1)[0]
        if not len(near):
            continue
        apart = np.abs(coarse[near] - _coarse(mean)).sum(axis=1)
        gains: dict[str, float] = {}
        best: dict[str, float] = {}
        for at in near[np.argsort(apart)[:KNOWN_LOOK]]:
            share, lacks = differ(held[at]['mean'], mean)
            letter = held[at]['letter'].lower()      # (a capital and its small letter have one name)
            if lacks < STRICT[1]:
                best[letter] = min(best.get(letter, 1.0), share)
            if share < KNOWN[0] and lacks < STRICT[1]:
                gains[letter] = max(gains.get(letter, 0.0), KNOWN[1] * (1.0 - share / KNOWN[0]))
        if gains:
            bias[group] = gains
        if KNOWN_SURE and best:
            first = min(best, key=best.get)
            if best[first] < KNOWN_SURE[0] and all(share >= best[first] + KNOWN_SURE[1] for letter, share in best.items() if letter != first):
                sure[group] = first
    return bias, sure


def named_shapes(groups: list[dict], members: dict[int, list[dict]], named: dict[int, str], words: list[list[dict]],
                 lex: collections.Counter, size: float, source: str = '') -> list[dict]:
    """The shapes that this hymn named, for the hymns after it: {'letter', 'mean', 'wide', 'size' (the size the
    shapes were compared at), 'source' (the hymn), and how sure the name is: 'glyphs' (how many glyphs have the
    shape), 'words' (how many words of four letters or more hold it), 'right' (how many of those are words of the
    list), 'hymn' (the share of the hymn's words of three letters or more that are words of the list)} each.
    A later hymn takes only the sure ones (SURE)."""
    codes = [code for code in _codes(words) if code and all(sign == "'" or sign in named for sign in code)]
    texts = [(code, ''.join(sign if sign == "'" else named[sign] for sign in code)) for code in codes]
    texts = [(code, text) for code, text in texts if len(text) >= 3]
    if not texts:
        return []
    hymn = sum(1 for _, text in texts if text in lex) / len(texts)
    found = []
    for group, letter in named.items():
        if len(letter) != 1 or len(members[group]) < 2:
            continue
        held = [text in lex for code, text in texts if group in code and len(text) >= 4]
        found.append({'letter': letter, 'mean': groups[group]['mean'], 'wide': groups[group]['wide'], 'size': size,
                      'source': source, 'glyphs': len(members[group]), 'words': len(held), 'right': sum(held), 'hymn': hymn})
    return found


def read_words(glyphs: list[dict], lex: collections.Counter, shapes: list[dict] | None = None,
               learned: list[dict] | None = None, source: str = '') -> list[dict]:
    """The syllables of the words of a hymn, from the glyphs of its pages (scoreread.letters.page_glyphs) and a
    list of words: {'band' (the page and the number of the row), 'x0', 'x1', 'text' ('?' for a letter with no
    name), 'join' (a hyphen follows), 'glyphs'} each, in the order of the rows.

    `shapes` are the shapes that earlier hymns named (load_shapes): they help to name the groups of this hymn.
    The shapes that this hymn names are added to the list `learned`, with `source` as their hymn."""
    if not glyphs or not lex:
        return []
    for glyph in glyphs:
        glyph['kind'] = kind_of(glyph)
    letters = [glyph for glyph in glyphs if glyph['kind'] == 'letter']
    if not letters:
        return []
    # Words in capitals only: every letter has one height, and the height says nothing about the letter. A capital
    # is as high as the line, so the shapes are compared at a larger size (an N and an H differ by one stroke).
    tall = sum(1 for glyph in letters if TALL <= _rise(glyph) < 1.7)
    deep = sum(1 for glyph in letters if _fall(glyph) >= DEEP)
    capitals = tall < CAPITALS[0] * len(letters) and deep < CAPITALS[1] * len(letters)
    if capitals and CAPITALS[2] != 1:
        for glyph in glyphs:
            glyph['canvas'], glyph['wide'] = normal(glyph, glyph['base'], glyph['xh'] / CAPITALS[2])
    groups = group_glyphs(glyphs)
    members = collections.defaultdict(list)
    for glyph in letters:
        members[glyph['group']].append(glyph)
    usual = np.median([glyph['wide'] for glyph in letters])
    classes = {group: set(LETTERS) if capitals else shape_class(own) for group, own in members.items()
               if np.median([glyph['wide'] for glyph in own]) <= TOUCH * usual}
    bias = {group: hole_bias(members[group], capitals) for group in classes} if HOLE else {}
    size = float(CAPITALS[2]) if capitals else 1.0
    if shapes and KNOWN:
        gains, sure = known_bias(groups, classes, shapes, size)
        for group, held in gains.items():
            own = bias.setdefault(group, {})
            for letter, gain in held.items():
                if letter in classes[group]:
                    own[letter] = own.get(letter, 0.0) + gain
        for group, letter in sure.items():
            if letter in classes[group]:
                classes[group] = {letter}
    syllables = syllables_of(glyphs)
    words = words_of(syllables)
    named, logp = name_groups(words, classes, lex, bias)
    if learned is not None:
        learned += named_shapes(groups, members, named, words, lex, size, source)
    signs = _codes(words)

    def score(group: int, text: str, more: dict[int, str]) -> float:
        """How well the words that hold the group are words of the list when the group has this name."""
        total = 0.0
        for code in signs:
            if group not in code:
                continue
            names = [sign if sign == "'" else text if sign == group else named.get(sign, more.get(sign)) for sign in code]
            if any(name is None for name in names):
                continue
            total += logp.get(''.join(names), MISS) - MISS
        return total

    named.update(name_rest(groups, members, named, classes, score))
    for syllable in syllables:
        text, double = '', set()
        for glyph in syllable['glyphs']:
            if glyph['kind'] == 'letter':
                letter = named.get(glyph['group'])
                if letter is None:
                    if glyph['wide'] > DOUBLE * usual:
                        double.add(len(text))
                    text += '?'
                elif len(letter) == 1 and _rise(glyph) >= TALL and letter not in ASC and letter not in 'ij':
                    text += letter.upper()
                else:
                    text += letter
            else:
                text += {'dot': '.', 'comma': ',', 'high': "'"}[glyph['kind']]
        syllable['text'], syllable['double'] = text, double
        syllable['x0'], syllable['x1'] = syllable['glyphs'][0]['x0'], syllable['glyphs'][-1]['x1']
    if MEND:
        mend_words(words, lex)
    return syllables


def set_under(result: dict, syllables: list[dict], page: int = 0) -> int:
    """Sets the syllables of a page under its notes: note['lyric'] and note['syllabic'] ('single', 'begin',
    'middle' or 'end': where the syllable stands in its word, from the hyphens) in the notes and in the parts of what
    read_page() gave. A row of words belongs to the staff over it (the first row under a staff holds the first
    verse; only that one is set), and its syllables stand under the notes of that staff in their order, each under
    the note that it is nearest to. A syllable with no note of its own is written after the syllable of the note
    before it: 'Glo-ry to the Fa-ther' under one reciting note. A letter that has no name is written as '?', so
    that a person sees where to mend the word. Returns how many notes got words."""
    layers = result.get('layers')
    if not layers or not syllables:
        return 0
    staves, bands, space = layers['staves'], layers['words'], layers['space']
    rows = collections.defaultdict(list)
    for syllable in syllables:
        if syllable['band'][0] == page:
            rows[syllable['band'][1]].append(syllable)
    taken, count = set(), 0
    for number in sorted(rows):
        band = bands[number]
        over = [index for index, staff in enumerate(staves) if staff['rows'][4] < band['top']]
        if not over:
            continue
        index = max(over, key=lambda index: staves[index]['rows'][4])
        if index in taken:
            continue
        taken.add(index)
        columns: list[list[int]] = []
        for at in sorted((at for at, note in enumerate(result['notes']) if note['staff'] == index),
                         key=lambda at: result['notes'][at]['x']):
            if columns and result['notes'][at]['x'] - result['notes'][columns[-1][0]]['x'] <= 0.75 * space:
                columns[-1].append(at)
            else:
                columns.append([at])
        row = sorted(rows[number], key=lambda syllable: syllable['x0'])
        if not columns or not row:
            continue
        places = [result['notes'][column[0]]['x'] for column in columns]
        # A short syllable stands with its middle under the note, a long one begins under it.
        wants = [min((syllable['x0'] + syllable['x1']) / 2, syllable['x0'] + 1.5 * space) for syllable in row]
        # The syllables and the notes keep their order: the pairs that stand nearest to each other in all.
        skip = UNDER * space
        cost = np.zeros((len(row) + 1, len(places) + 1))
        cost[1:, 0] = skip * np.arange(1, len(row) + 1)
        for i in range(1, len(row) + 1):
            for j in range(1, len(places) + 1):
                apart = abs(wants[i - 1] - places[j - 1])
                cost[i, j] = min(cost[i, j - 1], cost[i - 1, j] + skip,
                                 cost[i - 1, j - 1] + apart if apart <= skip else np.inf)
        i, j = len(row), len(places)
        under: dict[int, int] = {}
        while i and j:
            apart = abs(wants[i - 1] - places[j - 1])
            if apart <= skip and cost[i, j] == cost[i - 1, j - 1] + apart:
                under[i - 1] = j - 1
                i, j = i - 1, j - 1
            elif cost[i, j] == cost[i, j - 1]:
                j -= 1
            else:
                i -= 1
        texts: dict[int, str] = {}
        first: dict[int, int] = {}       # for each note with words: its first and its last syllable in the row
        final: dict[int, int] = {}
        last, before, begun = None, '', 0
        for at, syllable in enumerate(row):
            text = syllable['text'].strip(".,'")
            if not text:
                continue
            link = '-' if at and row[at - 1].get('join') else ' '
            if at in under:
                last = under[at]
                texts[last] = (before + link + text) if before else text
                first[last], final[last] = (begun if before else at), at
                before = ''
            elif not RECITED:
                continue
            elif last is None:
                if not before:
                    begun = at
                before = (before + link + text) if before else text
            else:
                texts[last] += link + text
                final[last] = at
        for j, text in texts.items():
            column = columns[j]
            top = min(column, key=lambda at: (result['notes'][at]['voice'], -result['notes'][at]['midi']))
            # Where the note's words stand in a word: a hyphen before them, a hyphen after them.
            inside = first[j] > 0 and bool(row[first[j] - 1].get('join'))
            goes_on = bool(row[final[j]].get('join'))
            syllabic = {(False, False): 'single', (False, True): 'begin', (True, True): 'middle', (True, False): 'end'}[(inside, goes_on)]
            for notes in (result['notes'], result['part_notes']):
                notes[top]['lyric'] = text
                notes[top]['syllabic'] = syllabic
            count += 1
    return count
