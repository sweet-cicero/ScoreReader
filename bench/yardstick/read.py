"""Reads clean pages with the yardstick (copisteria's network), to compare with the engine's own reading.

usage: python bench/yardstick/read.py <folder> [--name NAME] [--ledger]

The folder holds what `python -m scoreread layout <page> --out <folder>` wrote: <name>.clean.png and
<name>.layout.json. For each page (or for NAME alone) this writes <name>.musicxml and <name>.notes.json beside them,
as `scoreread read` does, so the kit's score.py scores both in the same way. --ledger turns the ledger rule on.

It needs copisteria with its Python (see engine.py). Nothing here is used by scoreread itself.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description='Reads clean pages with copisteria, as a yardstick.')
    parser.add_argument('folder')
    parser.add_argument('--name', default=None)
    parser.add_argument('--ledger', action='store_true')
    args = parser.parse_args(argv)
    from engine import read_page  # noqa: PLC0415
    folder = Path(args.folder)
    layouts = [folder / f'{args.name}.layout.json'] if args.name else sorted(folder.glob('*.layout.json'))
    for layout in layouts:
        name = layout.name[:-len('.layout.json')]
        start = time.time()
        places = json.loads(layout.read_text())['clean_page']
        result = read_page(folder / f'{name}.clean.png', places, ledger=args.ledger)
        (folder / f'{name}.musicxml').write_text(result['musicxml'])
        (folder / f'{name}.notes.json').write_text(json.dumps(
            {'notes': result['notes'], 'staves': result['staves'], 'systems': result['systems'], 'ledger': result['ledger']}))
        print(json.dumps({'name': name, 'symbols': 'copisteria', 'notes': len(result['notes']),
                          'reader_staves': result['staves'], 'reader_systems': result['systems'],
                          'ledger_changes': len(result['ledger']), 'tenor_staves': len(result['tenor_staves']),
                          'seconds': round(time.time() - start, 1)}))
    return 0


if __name__ == '__main__':
    sys.exit(main())
