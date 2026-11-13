"""Makes the list of words for the words of a scan (--words) from typed hymns: wordlist.py <folder of typed hymns> [--without ID] > words.txt

A typed hymn is a JSON file of the test kit (truth/<id>.json): the notes of the part named by 'words' hold the
syllables ('syl'; 'div' is '-' inside a word). Each line of the list is a word and how often the hymns have it. A
word is written with hyphens between its syllables, as the hymns part it ('mer-cy 160'): the reader takes it as the
word without them, and it learns from them how to part a word where a scan shows no hyphen.
--without leaves out one hymn and its other scores (<id>, <id>--s2, ...): the test of a scan reads its words with
the words of the other hymns only. The list is made from the app's hymns: keep it outside git.
"""
import collections
import json
import re
import sys
from pathlib import Path


def hymn_words(truth: dict) -> list[str]:
    """The words of a typed hymn, in small letters, each with hyphens between its syllables."""
    notes = truth.get('parts', {}).get(truth.get('words') or '') or []
    words, now = [], []
    for note in notes:
        if not note.get('syl'):
            continue
        now.append(re.sub(r"[^a-z']", '', note['syl'].lower().replace('’', "'")))
        if note.get('div') != '-':
            words.append(now)
            now = []
    words.append(now)
    plain = ('-'.join(part for part in (piece.strip("'") for piece in word) if part) for word in words)
    return [word for word in plain if word]


def word_list(folder: Path, without: str | None = None) -> collections.Counter:
    counts: collections.Counter = collections.Counter()
    for path in sorted(folder.glob('*.json')):
        if without and path.stem.split('--')[0] == without.split('--')[0]:
            continue
        counts.update(hymn_words(json.loads(path.read_text())))
    return counts


if __name__ == '__main__':
    arguments = sys.argv[1:]
    without = arguments.pop(arguments.index('--without') + 1) if '--without' in arguments else None
    folders = [argument for argument in arguments if argument != '--without']
    if len(folders) != 1:
        sys.exit(__doc__)
    for word, count in sorted(word_list(Path(folders[0]), without).items(), key=lambda item: (-item[1], item[0])):
        print(word, count)
