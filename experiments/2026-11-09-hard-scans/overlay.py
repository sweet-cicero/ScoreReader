#!/usr/bin/env python3
"""Draws a copisteria reading over its image: overlay.py image.png notes.json out_prefix
Writes one picture for each staff, with the pitch and the length of each note head beside it."""
import json
import sys

import cv2

NAMES = 'CDEFGAB'
SHORT = {'note_whole': 'w', 'note_half': 'h', 'note_quarter': 'q', 'note_eighth': 'e', 'note_16th': 's'}


def name_of(pos):
    step = pos + 6 + 7 * 4  # pos 0 is the middle line of the treble staff, B4
    return f'{NAMES[step % 7]}{step // 7}'


def main():
    image = cv2.cvtColor(cv2.imread(sys.argv[1], cv2.IMREAD_GRAYSCALE), cv2.COLOR_GRAY2BGR)
    with open(sys.argv[2]) as file:
        data = json.load(file)
    staves = sorted({note['staff'] for note in data['notes']})
    for staff in staves:
        notes = [note for note in data['notes'] if note['staff'] == staff]
        for note in notes:
            x0, y0, x1, y1 = (int(v) for v in note['box'])
            up = note['voice'] == 1
            colour = (0, 0, 255) if up else (200, 80, 0)
            cv2.rectangle(image, (x0, y0), (x1, y1), colour, 1)
            text = name_of(note['pos']) + SHORT.get(note['cls'], '?')
            y = int(note['staff_y0'] - (2.4 if up else 1.5) * note['sp']) if up else int(note['staff_y1'] + 3.3 * note['sp'])
            cv2.putText(image, text, (x0 - 6, y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, colour, 2)
        top = int(notes[0]['staff_y0'] - 4.2 * notes[0]['sp'])
        bottom = int(notes[0]['staff_y1'] + 4.2 * notes[0]['sp'])
        cv2.imwrite(f'{sys.argv[3]}-staff{staff + 1}.png', image[max(0, top):bottom])


if __name__ == '__main__':
    main()
