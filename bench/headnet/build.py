"""build.py <marks.json> <pages> <out.npz>: the training set of the small network (scorereader.headnet).

<marks.json> lists the read heads of a run of the wide test, each labelled by the scorer against the typed hymn
(made with the wide test, outside git): [{"page", "x", "y", "space", "label", "group"}], where label is 0 for a
filled head (typed shorter than a half note), 1 for a hollow head and 2 for a mark that is no note, and group is
the hymn, so that a test can hold whole hymns out. <pages> is the folder of the clean pages that the run read
(<page>.png). The crops are the reader's own (scorereader.headnet.crops)."""
import json
import sys
from collections import defaultdict
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scorereader import headnet  # noqa: E402

marks, pages, out = json.load(open(sys.argv[1])), Path(sys.argv[2]), sys.argv[3]
by_page = defaultdict(list)
for mark in marks:
    by_page[mark['page']].append(mark)
X, Y, G = [], [], []
for page, found in sorted(by_page.items()):
    grey = cv2.imread(str(pages / f'{page}.png'), cv2.IMREAD_GRAYSCALE)
    heads = [{'cx': mark['x'], 'cy': mark['y']} for mark in found]
    X.append((headnet.crops(grey, heads, found[0]['space'])[:, 0] * 255).round().astype(np.uint8))
    Y += [mark['label'] for mark in found]
    G += [mark['group'] for mark in found]
np.savez_compressed(out, X=np.concatenate(X), Y=np.array(Y, np.int8), G=np.array(G))
print(len(Y), np.bincount(Y))
