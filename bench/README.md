# Tests

```
export SCOREREADER_KIT="$HOME/Projects/LitChoir/tmp/omr-test"     # the test kit, see below
PY="$SCOREREADER_KIT/tools/copisteria/.venv/bin/python"           # or any Python with opencv-python and numpy
$PY bench/drawn_check.py                                        # the whole reader on a page the script draws; needs no kit
$PY bench/staves_check.py "$SCOREREADER_KIT/pages" out/staves   # 38 of 38 pages right
$PY bench/systems_check.py "$SCOREREADER_KIT"                   # 37 of 38; on the other page the copy lost a staff
bash bench/kit.sh own                                           # reads all 38 pages
bash bench/kit.sh v04 --yardstick                               # the yardstick: the same clean pages with copisteria's network
python3 "$SCOREREADER_KIT/score.py" --results out/kit --tools own v04
```

`bench/kit.sh` takes its Python from `SCOREREADER_PYTHON`, or the kit's copisteria environment without it.

The yardstick (`bench/yardstick`) reads the reader's clean pages with copisteria's network, to measure the own rules
against it. It is a test tool: the reader does not load it, and nothing of it ships with the reader.

`bench/wordlist.py` makes the list of words for the words of a scan (`--words`) from typed hymns. With `--text` it writes the
words of each hymn in their order, so the list also tells which words follow each other.

The wide test (every score of LitChoir) is run with scripts outside this repository, because it needs the app's
scans and typed hymns.

`bench/headnet/` trains the small network of `scorereader/headnet.py` (filled head, hollow head, no head):
`build.py` cuts the reader's own crop around every read head of a run of the wide test, labelled by the scorer
against the typed hymn, and `train.py` trains it with JAX on the CPU (`pip install jax optax`), held out by hymn
or on everything. The weights trained on everything ship with the reader (`scorereader/headnet.npz`); other weights
are given with `SCOREREADER_HEADNET=<file>.params.npz`, and `SCOREREADER_HEADNET=off` reads by the rules alone. The
shipped weights saw LitChoir's pages, the kit's among them, so a measure on those pages names the weights of the fold
that never saw the hymn, or reads with the network off.

## The test kit

The tests need the test kit, which is not in this repository. The reader itself does not need it.

- `pages/`: 38 page images of 31 hymns. They are scans of the choir's scores, so they stay out of git.
- `truth/`: the same hymns typed by hand, as the answer key.
- `score.py`, `cases.json`, `env.sh`: the scoring script, the list of hymns and the settings of the tools.
- `tools/copisteria`: copisteria with its own Python and its model files (about 4 GB with the other readers), for
  the yardstick (`bench/yardstick`).

`SCOREREADER_KIT` names the kit's folder. Without it, the tests look in `~/Projects/LitChoir/tmp/omr-test`.
`SCOREREADER_COPISTERIA` names another copy of copisteria.
