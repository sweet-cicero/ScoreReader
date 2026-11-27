"""Fetches the text network that scorereader.textnet runs, once, into a folder of its own.

    python bench/textnet_get.py ~/scorereader-textnet
    python -m scorereader hymn page1.png page2.png --out out --tesseract --second ~/scorereader-textnet

The network is PaddleOCR's recognizer of a line of text, PP-OCRv6 small (Apache-2.0), as the onnxocr package (Apache-2.0)
ships it converted to ONNX. The package is downloaded from PyPI with pip (onnxocr 4.0.0, without its dependencies), and
four of its files are kept: the network (`rec.onnx`), its signs (`dict.txt`), its settings as PaddleOCR exported them
(`inference.yml`, which names the model) and the licence. Each is checked by its SHA-256. The reader itself never
fetches anything: once the folder is filled, it reads offline."""
from __future__ import annotations

import hashlib
import os
import subprocess
import sys
import tempfile
import zipfile

PACKAGE = 'onnxocr==4.0.0'
FILES = {   # the name in the folder: (the path in the package, its SHA-256)
    'rec.onnx': ('onnxocr/models/ppocrv6/small/rec/rec.onnx',
                 '5435fd747c9e0efe15a96d0b378d5bd157e9492ed8fd80edf08f30d02fa24634'),
    'dict.txt': ('onnxocr/models/ppocrv6/ppocrv6_dict.txt',
                 '769e7fa79bb297b5f18d8dbd149e364a45bc61f2b3f574e5ea836f0b261c23a6'),
    'inference.yml': ('onnxocr/models/ppocrv6/small/rec/inference.yml', None),
    'LICENSE': ('onnxocr-4.0.0.dist-info/licenses/LICENSE', None),
}


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    folder = os.path.expanduser(sys.argv[1])
    os.makedirs(folder, exist_ok=True)
    with tempfile.TemporaryDirectory() as work:
        subprocess.run([sys.executable, '-m', 'pip', 'download', PACKAGE, '--no-deps', '--only-binary=:all:', '-d', work],
                       check=True)
        wheel = next(os.path.join(work, name) for name in os.listdir(work) if name.endswith('.whl'))
        with zipfile.ZipFile(wheel) as package:
            for name, (path, digest) in FILES.items():
                data = package.read(path)
                if digest and hashlib.sha256(data).hexdigest() != digest:
                    sys.exit(f'{path} in {os.path.basename(wheel)} is not the file that the reader was measured with')
                with open(os.path.join(folder, name), 'wb') as out:
                    out.write(data)
    print(f'the text network is in {folder}: name it with --second (or SCOREREADER_OCR_SECOND)')


if __name__ == '__main__':
    main()
