"""A further reader of a row of words: a text network that OpenCV runs, when its folder is named.

The network reads one line of text from its picture. It is PaddleOCR's recognizer of a line (PP-OCRv6 small, Apache-2.0
licence, converted to ONNX by the onnxocr package; `bench/textnet_get.py` fetches it once): each column of the scaled
picture gives one sign or none (CTC). Its folder holds `rec.onnx`, the network, and `dict.txt`, its signs one to a line,
and is named among the further readers of the words (SCOREREADER_OCR_SECOND, or `--second`), beside Tesseract's larger
language files (scorereader.ocr.SECOND). OpenCV 5 reads the network (OpenCV 4 cannot import it); no model library is
needed, and nothing is fetched while a page is read. Without the folder the words are read as before.

The words come with their columns, from the columns of their signs, and with how sure the network is of them (the mean
of its signs, of 100), as scorereader.ocr._line gives Tesseract's words."""
from __future__ import annotations

import os
import sys

import cv2
import numpy as np

HIGH = 48                  # the network reads a line scaled to this many px high
_NETS: dict[str, tuple | None] = {}


def _load(folder: str) -> tuple | None:
    """The network of a folder and its signs, read once; None where the folder holds none or OpenCV cannot read it."""
    if folder not in _NETS:
        _NETS[folder] = None
        model, signs = os.path.join(folder, 'rec.onnx'), os.path.join(folder, 'dict.txt')
        if os.path.exists(model) and os.path.exists(signs):
            with open(signs, encoding='utf-8') as lines:
                chars = lines.read().split('\n')
            if chars and chars[-1] == '':
                chars = chars[:-1]
            try:
                _NETS[folder] = (cv2.dnn.readNetFromONNX(model), [''] + chars + [' '])
            except cv2.error as error:
                print(f'scorereader: the text network in {folder} is left out: OpenCV {cv2.__version__} cannot read it '
                      f'({str(error).strip().splitlines()[-1][:120]})', file=sys.stderr)
    return _NETS[folder]


def holds(folder: str) -> bool:
    """Whether a folder holds a text network that OpenCV can run."""
    return os.path.exists(os.path.join(folder, 'rec.onnx')) and _load(folder) is not None


def line(crop: np.ndarray, folder: str) -> list[tuple[str, int, int, float]]:
    """The words of one line of text: (text, left, right, how sure) each, in the crop's px."""
    net, signs = _load(folder)
    picture = cv2.cvtColor(crop, cv2.COLOR_GRAY2BGR) if crop.ndim == 2 else crop
    scale = HIGH / picture.shape[0]
    wide = max(16, int(round(picture.shape[1] * scale)))
    picture = cv2.resize(picture, (wide, HIGH), interpolation=cv2.INTER_AREA if scale < 1 else cv2.INTER_CUBIC)
    net.setInput(((picture.astype(np.float32) / 255.0 - 0.5) / 0.5).transpose(2, 0, 1)[None])
    out = net.forward()[0]
    if out.shape[1] != len(signs):
        return []
    step = wide / out.shape[0] / scale        # the crop's px of one column of the network's output
    # The signs, each with its first and last column and how sure the network is of it.
    read, last = [], 0
    for column, (sign, how) in enumerate(zip(out.argmax(1), out.max(1))):
        if sign and sign != last:
            read.append([signs[sign], column, column, float(how)])
        elif sign and read:
            read[-1][2] = column
        last = sign
    words, word = [], []
    for sign in read + [[' ', 0, 0, 0.0]]:
        if sign[0] != ' ':
            word.append(sign)
        elif word:
            words.append((''.join(part[0] for part in word), int(word[0][1] * step), int((word[-1][2] + 1) * step),
                          100.0 * float(np.mean([part[3] for part in word]))))
            word = []
    return words
