"""Reads the rows of the words of a scan with Tesseract, when it is installed. This is the one step that uses a model.

Tesseract is a small text reader that runs on this computer (Apache-2.0 licence). The reader does not need it: the
notes are read by rules alone, and the words can be read by the letter shapes of the hymn (scorereader.lyrics). Where
Tesseract is installed and asked for, it reads each row of words as one line of text, and this step cuts the line
into the syllables of the row with their places, so that scorereader.lyrics.set_under() can set them under the notes.

The rows are the reader's own (scorereader.words): Tesseract never sees the notes.
"""
from __future__ import annotations

import itertools
import os
import re
import shutil
import subprocess
import tempfile

import cv2
import numpy as np

from . import setting

PROGRAM = 'tesseract'    # the program's name, or its path (SCOREREADER_TESSERACT names another)
LANGUAGE = 'eng'         # the language file (SCOREREADER_OCR_LANGUAGE names another, as 'eng+ell')
HIGH = 40                # a row of words is scaled so that its band is this many px high
AGAIN = (32, 50)         # a second look: the row is read again at these sizes, and the reading that fits best is kept.
#                          With a list of words that is the reading of which the list holds the most letters, else
#                          the one that Tesseract is surest of. A row whose words the list holds all is not read
#                          again (an empty tuple: each row is read once)
ROOM = (0.6, 2.0)        # the room kept over and under the band, and at its sides, in staff spaces
DIGITS = True            # a 0 or a 1 that Tesseract read in the place of a letter is read as that letter (O, I, l)
DIGIT_JOIN = True        # a 0 with a hyphen beside it is the syllable o too ('The-0-to-kos')
DIGIT_LIST = True        # with a list of words, a 1 among small letters is an i where the list holds the word with an i
#                          and not with an l ('1s' is 'is'): the word is the piece with the pieces that its hyphens
#                          join it to, with the word that the row before leaves open where the piece stands in the first
#                          word of its row ('Al-le-' and then 'lu-1a' is 'alleluia', see MEND_BEFORE), or the piece alone
#                          where no hyphen stands beside it. False: an l. (The piece stays as sure as Tesseract was of
#                          the digit: counted as a piece that it is not sure of, so that the mending may choose the
#                          letter, short pieces went that had been read right, 2 syllables gained and 4 lost on all
#                          scan pages.)
ROUND = (('Q', 'QO', 'OQ', 'Qo', 'Oo'), '©', 0.7)   # with a list of words that holds the word O: a word that is read
#                          as one of these and stands alone is the word O. And the sign after them is, where it is this
#                          share of the row's height wide or more (a narrow one is a dot or a piece of a note) and no
#                          number follows it (the sign of a copyright line). (None: off)
SURE = (20, True)        # a word that Tesseract is less sure of than this (of 100) and that has under three letters is
#                          left out; with a list of words it stays when the list holds it (True)
SURE_JOIN = True         # and it stays where the list holds the word that it makes with the pieces beside its hyphens: the
#                          hyphen was read, so a syllable stands there ('Bless-' and an unsure 'ed', an unsure 'el-'
#                          before 'der') (False: off)
SURE_ALIKE = 2           # and it stays where every reading of the row as the picture is holds it with the same letters
#                          in its columns, at each size and by each language file (one further file at least): readers
#                          that agree have read the page. A hymn's own syllables are in no list ('ke' of the names of
#                          the notes, the syllables of a hymn in another language than the list's, the first piece of
#                          a word whose letters were misread). Such a word speaks for no reading, since every reading
#                          holds it: how well a reading fits, whether it is whole and whether it is a row at all is
#                          asked without the word, and the reading that is kept has it. 1: only in the readings of
#                          the first file, whose limit SURE is; 2: in those of the further files too, so that a
#                          reading of a further file is set beside a standing one that has the word as well.
#                          (On all scan pages 11 syllables gained and none lost in the full reading, 12 by the
#                          replay and 7 there by the first file alone; the fresh set does not change.) None: off
SOLID = (0.3, 0.9, 0.5)  # a word of two letters or more is no word where this share of the columns of its box is ink from
#                          over the row to under it (a column: this share of it; over and under: this many heights
#                          of the row): the black edge of a scan, a punch hole, a bar line that crosses the row. A
#                          letter fills its column over the row or under it, not both. The picture that Tesseract
#                          gets stays as it is: with the edge painted out it read other words of the row otherwise
#                          (None: off)
BOW = (1.0, 0.45, 0.3, 80, 0.3, 0.5, 0.15, 0.75)   # with a list of words: a word that the list does not hold and
#                          that Tesseract is less sure of than the fourth number, whose box holds a bow after its
#                          letters: one stroke of
#                          ink in each column over the first number of row heights or more, at most the second number
#                          of row heights thick, whose middle rises or falls by the third (a level stroke is a hyphen or
#                          the line of a held syllable). It is the slur of the staff under the row, which touches the
#                          word, and Tesseract reads letters from it ('the' with a slur is 'thes'), or a dash, which
#                          would join two words as a hyphen does: a dash is no hyphen where such a bow runs through
#                          its middle, in its columns and a row height at each side. The word is its letters before
#                          the bow where they are a word of the list and letters of the row stand there: the ink before
#                          the bow fills the last number of the rows of the row or more (the hook of a clef by hand, a
#                          hyphen and a slur alone were read as short words, and do not: 0.61 at most against 0.84 or
#                          more on LitChoir's pages), as many letters as were read stand there by the usual width of a
#                          letter of the row, within the fifth number of letters (0.15 at most where the letters are
#                          the word, 0.49 or more where the bow begins inside a letter), and no letter stands behind
#                          the bow (less than a letter's width of other ink). The ink is looked at in the rows of the
#                          row and the sixth number of row heights over and under it, and a stroke is one stroke
#                          where its middle moves by the seventh number of row heights at most from a column to the
#                          next. A rule for one print in what it trims (three words of one carol, and two words of
#                          two copies by hand). None: off
CLEF = (3.0, 50, 2, 1.5)   # a word that ends within this many staff spaces of the left end of the staff over its row, in
#                          the columns of the clef, and that Tesseract is less sure of than the second number is no
#                          word: the tail of the clef, the brace, a smudge at the edge of the page. The words of a
#                          row begin under its first note; a row that goes on under the clef is read surely there.
#                          The word has the third number of letters or more (a stroke that is read as one letter
#                          has rules of its own) and begins at most the fourth number of staff spaces before the
#                          staff: a label in the margin is another matter. Such a word can hold letters of the
#                          list ('la', 'las') and make a reading win that leaves out a true syllable. (None: off)
CLEF_WHOLE = True        # a reading that lost such a word is not whole, as a reading with a mended word is not
UNREAD = (0.3, 1.5, 0.85, 0.6, 0.5, 0.25, 0.6, 1.6)   # a reading that holds only words of the list is not whole where a
#                          letter stands between two of its words that it did not read: a lone capital O between
#                          "THEE," and "LORD," stood in no reading at one size, that reading was whole, and the other
#                          sizes were not read. The piece is a letter by its ink: as wide as 0.3 to 1.5 heights of the
#                          row, with ink in 0.85 of the row's rows, no more than 0.6 heights over the row and 0.5 under
#                          it (a bar line and a stem go on), 0.25 heights of paper to both words, and strokes 0.6 to 1.6
#                          times those of the row. A rule for one row of LitChoir's scan pages (None: off)
DIGIT_END = ('47', '5')  # behind the letters of a word of the list a 4 or a 7 is a stroke beside the word (a bar line
#                          through the last letter, a full stop, the end of a slur: "THY4", "a4.", "us7"), and a 5 is the
#                          s of a hand where the list holds the word with it ("a5" is "as"). The digits with a bow of
#                          their own (2, 3, 6, 8, 9) stand for a letter by hand as often as for stray ink, and stay
#                          (MEND_WHOLE): the other sizes are read too. Without it a first reading that held only
#                          words of the list beside the stray word won, and a syllable that it misread stayed lost
ROW = 40                 # a row that Tesseract is less sure of than this, over all its letters, is no row of words (stray
#                          ink under a staff: a slur, a hairpin, the ends of stems). None: every row is kept
ROUND_SIDE = ('()[]', '@©')  # the word O with a bracket at one side ('0)', '@)', '©)'): the ring of a large O is read
#                          as a round sign and a bracket. The second: signs that are the word O only so (the sign of a
#                          copyright line has no bracket; of 4 such tokens of LitChoir's scan pages 3 are an O and
#                          one, in a reading of a copy by hand that is not kept, is not). (None: off)
JOINS = '-‐‑‒–—~='     # what a hyphen between two syllables can be read as
STOPS = '.,;:!?'         # a dash after a syllable that ends with one of these is the line of a held syllable, no hyphen
LINES = '_'              # the line after a syllable that is held
ROW_HELD = (0.5, 6, 3)   # with a list of words, a row that Tesseract is not sure of is a row of words all the same
#                          when the list holds the words of this share of its letters, and it has this many letters
#                          or more; only words of this many letters or more count as held (stray ink reads as a row
#                          of short words: 'a nus me a t i le we'). None: off
CUT = (0.3, 2.0, 2, 1, 1.6, 0.2, 1.3)   # two words that Tesseract read as one are cut at a wide gap: the gap is
#                          this share of the row's height or more, and this many times the usual gap between the
#                          letters of the word; each part keeps this many letters or more. Only where each sign of
#                          the word is one piece of ink, so that the gaps can be counted: pieces this many px apart
#                          are one sign, and where one sign is missing, a piece this many times as wide as the usual
#                          piece is two signs that touch. A row whose letters stand all but as far apart, centre to
#                          centre (the distances differ by this share of the usual one at most), is from a
#                          typewriter: there the letters at the two sides of a cut stand this many times the usual
#                          distance apart (None: off)
CUT_VOWEL = True         # no cut where the letters between the cut and the next hyphen of the word hold no vowel: a
#                          piece with no vowel is no syllable ('An-g' and 'els' of 'An-gels', whose A and n touch so
#                          that the pieces of ink stand a sign off; 'UN-DI-VI' and 'D-ED', where a print sets the
#                          letters of one syllable wide apart). Only on a page whose words fit the list of words
#                          (see MEND): in another language a consonant beside a hyphen is a word ('s-a', 'n-am'),
#                          and only the letters of the plain alphabet are judged
STOP_INSIDE = True       # a comma or another stop between two letters of a word ends a word: two words that stand
#                          close were read as one ('Lord,where'). (Without it the list must hold both words: ENDS.)
MEND = (4, 2, 80, 50, 0.2)   # with a list of words: a word of this many letters or more that the list does not hold
#                          becomes the list's word that is one letter away (one letter more, less or other), when
#                          the list holds one such word only, and holds it this often or more. Only a word that
#                          Tesseract is less sure of than the third number is mended. The end of a word changes in
#                          the language itself (stone, stones): there the word is mended only when Tesseract is less
#                          sure of it than the fourth number. And only on a page of whose letters this share or more
#                          stands in words that the list holds: else the page is in another language than the list
#                          (None: off)
MEND_TWIN = (('m', 'rn'),)   # with a list of words: a word of three letters or more that the list does not hold becomes
#                          the list's word that has the two letters where the one letter was read ('bom' is 'born':
#                          an r and an n that touch are an m for Tesseract at every size and with every file, and it
#                          is sure of the m), where the list holds one such word (None: off)
MEND_PAIR = 7            # two words side by side that the list does not hold, of this many letters or more together,
#                          become the one word of the list that they are with one letter read otherwise: the end
#                          of a word under a long melody stands far from its start, with no hyphen that was read
#                          ('Al-le-lu la' is 'Al-le-lu-ia'). None: off
PAIR = 3                 # with a list of words that tells which words follow each other (`lex.pairs`, from plain
#                          text): a word of at most this many letters that the list does not hold becomes the
#                          list's word one letter away that the list holds behind the word before it and before
#                          the word after it ('Lord tq have' is 'Lord to have'), where there is one such word
#                          only. A short word is not mended by the list alone: too many words are one letter
#                          away. None: off
PAIR_OTHER = 0.7         # and a word that does not stand with both of its neighbours in the list's text becomes
#                          the word that another reading of the row holds at its place (they share this much of
#                          their width), where that word stands with both ('at thy night hand' is 'right' in
#                          another reading), and the other readings hold one such word only. None: off
MEND_PAIR_RARE = 20      # two words side by side are mended into one (MEND_PAIR) although the list holds one of
#                          them, where it holds the whole this many times as often ('Al-le-lu la': the list holds
#                          'la' three times and 'alleluia' two hundred times). None: a piece that the list holds
#                          is never joined
MEND_OPEN = True         # a word that a hyphen leaves open at the end of a row ('foun-', the row goes on with
#                          'tain') is not mended by a letter added at its end ('found'): the word is not whole there
MEND_HEAD = True         # a word that a hyphen leaves open at the end of a row and that the list does not hold is the
#                          beginning of a word as the list parts it ('shep-', and the next row goes on with 'herds';
#                          'cher-u-' before 'bim'): it is not mended into a word of the list ('she'), and no word of
#                          another reading takes its place ('thee'), unless that word begins the parted words of the
#                          list more often ('op-' is 'up-': 'up-on')
MEND_BEFORE = 2          # the first word of a row is the rest of the word that the row before leaves open at its
#                          end ('glo-', and the next row begins 'ri-ous') where the list holds the two together:
#                          it is not mended alone ('pious'). A letter of it that was read wrongly is mended by the
#                          whole word ('glo-' and 'yi-ous' is 'glorious') where both pieces have this many letters
#                          or more, and where Tesseract is not sure of the first word and it is no rest of the open
#                          word, the first word of another reading that is one, of this many letters or more, takes
#                          its place ('Moth-' and 'were', another reading begins 'er'). A piece of one letter is a
#                          stray stroke as often as a letter: 'has-' and 'v' is no 'hast'. The row before is the
#                          first row under the staff of the same part in the system before. 0: off
MEND_FRAME = (3, 2, 1)   # the first word of a row ends the word that the row before leaves open, and the syllable
#                          between was misread ('Al-le-', and the next row begins 'fas-ia': the seam of a scan cut the
#                          letters of the row in half): the list holds one word only that begins with the open piece
#                          (this many letters or more) and ends with the last syllable of the first word (the second
#                          number of letters or more), with as many letters between as were read, give or take the
#                          third number, and Tesseract is not sure of the syllable between. The syllable is written
#                          in capitals where its row was read in capitals. (Two rows of LitChoir's scan pages and
#                          none of the fresh set: the row at the seam, and 'FOR-' before 'E — VER-MORE', where the
#                          lone E is lost in its line and a letter added to 'VER' had given the same word.) None: off
MEND_PAGE = True         # the row before the first row of a page is the last row of the page before it in the hymn:
#                          a word that the end of a page leaves open goes on over the page ('Al-le-', and the next page
#                          begins 'lu-ia'), as it does from system to system (MEND_BEFORE). False: a page begins anew
MEND_REST = True         # the first word of a row goes on from the word that the row before leaves open also
#                          where its first syllables make a word of the list with the open piece ('car-', and the
#                          next row begins 'ry-ing': 'carry'): it is not mended alone ('crying'). The open piece
#                          has MEND_BEFORE letters or more, and so have the syllables. False: off
MEND_REST_FIT = 2        # and the letters of such a first word count in the fit of its reading as letters of a word
#                          of the list do: a reading at another size that begins with a word of the list ('Ty-ing')
#                          was as good a fit and won by how sure Tesseract was. The reading is not whole by it.
#                          2: also a first word that is a word of the list with the open piece (MEND_BEFORE). 0: off
MEND_REST_STRAY = (2, 80)   # a word of this many letters or fewer before the word that goes on from the open piece,
#                          of which Tesseract is less sure than this, is stray ink at the start of the row (the
#                          brace, a bar line, the clef): 'pas-', and the next row begins 'he cha'. None: off
SMALL_I = True           # a small i that stands alone as a word is no word, on a page whose words fit the list (see
#                          MEND): the word I is a capital, and the brace, the clef and a bar line beside a row are
#                          read as a small i (61 on LitChoir's scan pages, none of them a typed word). It goes after
#                          the reading of the row is chosen: taken out of each reading, a reading without it was
#                          whole, the other sizes were not read, and 8 syllables were lost for 1. False: off
MEND_S = True            # an s at the end of a word is never taken away and never added by the mending: the list
#                          holds 'sake' and lacks 'sakes', and the page prints 'sakes'
LONE_I = (0.1, 0.6, 0.2, 0.7, 1.5)   # a stroke that stands alone between two words ('|') is the word I where its
#                          ink is a letter: it begins at most LONE_I[0] heights of the band under the band's top and
#                          under LONE_I[1] over it, it ends within LONE_I[2] of the band's foot, and it is LONE_I[3]
#                          to LONE_I[4] times as thick as the strokes of the row's letters. A bar line goes on over
#                          the row; a line by hand and a dashed line are hairlines.
FOUR_A = (0.5, 0.15, 1.0)   # a 4 that stands alone between two words is the letter a where the stem of a note runs into
#                          the top of the a: its box is one letter wide (at most FOUR_A[2] of the band's height) and holds
#                          closed paper (the bowl of the a) whose middle lies at least FOUR_A[0] of the band's height
#                          under the band's top, at most FOUR_A[1] of the band's height squared. The first word of a row
#                          and a 4 with a full stop are the numbers of verses. (A census of every lone 4 in the stored
#                          rows of LitChoir's scan pages at the first size, 50 places: the four that pass are an a with a
#                          stem in it, on three scans of one print and one other; a stem through a hyphen or through an
#                          i, a tie and a number by hand hold no such paper. At other sizes a 4 was read over a word by
#                          hand, a stem on a staff line and a blot: each is wider than a letter. None: off)
SECOND = 1000            # a second language file of Tesseract (SCOREREADER_OCR_SECOND names its folder: the standard or
#                          the 'best' file beside the small one that Tesseract comes with) is a second opinion: where
#                          no reading with the first file holds only words of the list, the row is read with the
#                          second file too, at the three sizes, and the reading that fits the list best is kept. Its
#                          readings are the sizes from SECOND on (SECOND + 40). In the place of the small file the
#                          large one read 26 syllables more and 81 fewer on the clean copies: the limits of how sure
#                          Tesseract is were set with the small file.
SECOND_MORE = 2          # how sure the two files are does not compare: a reading with the second file is kept only
#                          where it leaves fewer letters in words that the list does not hold, and no fewer letters
#                          in words of the list. Words of fewer letters than this do not count as words of the list
#                          there: the large file reads a stroke as the word I.
SECOND_FIRM = True       # a word that the list lacks and that the first file read with the same letters at each of
#                          its sizes is a word of the hymn. A reading of a further file that lacks such a word and
#                          has fewer letters than the reading that stands is not kept ('patience' as 'patence',
#                          'Ison' as 'son'): it counts fewer letters outside the list only because it read the
#                          word shorter.
SECOND_MEND = True       # a word of the second file's reading that the first file read with the same letters is not
#                          mended: two readers that agree have read the page, and the word is one that the list
#                          lacks (False: no word of the second file's reading is mended)
MEND_ODD = 2             # a word that Tesseract is sure of is mended all the same when it holds this many runs of
#                          three letters, its beginning and its end counted, that no word of the list holds: it is no
#                          word of the list's language ('thov', 'lotd'), where 'banner' and 'jews' are (None: off)
MEND_OFTEN = (0.06, 0.012)   # and it is mended all the same when the word that it becomes is one of the list's
#                          commonest: the list holds it this share as often as its commonest word ('thov' is
#                          'thou', at the end of the word too; not a piece of a word whose hyphen was not read,
#                          'glori ous'), or the second share where one such run of three letters is in no word of
#                          the list and the letter is not the word's last ('mishty' is 'mighty') (None: off)
MEND_ALIKE = 2           # a word that every reading of a row holds with the same letters counts as a word that Tesseract
#                          is sure of: it is a true word of the hymn that the list lacks more often than a misread,
#                          and it is mended only as a sure word is (1: every size of the first file; 2: every size
#                          of every file; 0: off)
MEND_WHOLE = True        # a reading with a mended word is not whole: the row is read at the other sizes too, and
#                          the reading that fits best is kept ('Theel' mended, and a syllable left out beside it)
OTHER_SIZE = (0.7, 2)    # with a list of words: the row is read at three sizes and one reading is kept. A word of it
#                          that the list does not hold becomes the word that another size read at its place (the two
#                          share this much of their width), when the list holds that word this often or more and it
#                          is as long, or a letter longer or shorter. A word of the list with an s behind it
#                          stays: the list need not hold that form (None: off)
CROSS = (2.0, 1.8, 1.3, 0.3, 1.9, 3.0, 0.4, 0.25, 0.4)   # a second look at a row that ink crosses: the row is read
#                          again without that ink where no reading of the picture as it is holds only words of the
#                          list. The page is looked at this many staff spaces over and under the row. An upright
#                          stroke as long as the second number of staff spaces and the third of row heights, or one
#                          that comes in over that edge, is a bar line or a stem: it goes outside the letters, and
#                          between them where it runs on past them by the fourth number of staff spaces at both
#                          sides or where no ink hangs on it. The letters stand in the row, made as high as the
#                          fifth number of staff spaces where the row is lower. A slur goes too: one thin stroke
#                          in each column (the eighth number of staff spaces at most) over the sixth number of row
#                          heights or more, that rises or falls by the seventh. Before the slurs are looked for,
#                          an upright stroke is taken away but where it lies between ink that is nearer than the
#                          last number of staff spaces (a slur that crosses a bar line stays whole). None: off
CROSS_LIST = True        # on a page whose words do not fit the list of words (another language, see MEND), the
#                          second look is kept only where it holds more letters in words of the list than the best
#                          reading of the picture as it is: there the list holds few words of either reading, and
#                          how sure Tesseract is does not choose between two pictures
HELD = (1.2, 0.25, 0.35)   # the line of a held syllable is taken out of the picture before Tesseract
#                          reads the row: a level line this many times as long as the band is high or longer, this
#                          share of the band's height thick at most, that lies this near the band's lower edge
ENDS = (2, 2, 3, 0.001)   # with a list of words: a word that the list does not hold is parted where the list holds the
#                          words on both sides this often or more, each of this many letters or more. On a page
#                          whose language the list holds, a word of one letter (o, a, I) can be one of the two when
#                          the other one has this many letters or more, and when it is this share of all the words
#                          of the list or more (a list holds stray letters too). And two words are joined that the
#                          list holds as one word (None: off)
ENDS_VOWEL = True        # a piece of two letters or more that holds no vowel is no word there: a list that is made
#                          from typed hymns holds such pieces ('th' of a 'wi-th' that a hymn spreads under two notes),
#                          and 'sav-eth' was parted into 'save' and 'th'. The test only takes a cut away: where it
#                          left the other ways to part a word, it made new cuts ('in-tru')
ENDS_CARRIED = True      # the first word of a row is not parted where it is a word of the list with the word that
#                          the row before leaves open ('a-' and then 'lone': not 'lo' and 'ne'; see MEND_BEFORE)
THREE = (0.0003, 0.0025)  # three words that were read as one ('mercyonus') are parted too, on a page whose language
#                          the list holds: each of them is this share of all the words of the list or more, and a
#                          word of under three letters this share (two cuts need more witness than one; None: off)
PARTS = (1, 0.5)         # with a list of words that shows how its words are parted into syllables (a word written
#                          with hyphens between them): a word that was read in fewer syllables than the list parts it
#                          into is parted as the list does (a scan loses its hyphens, and many a page prints none),
#                          when the list parts it so this many times or more, and in this share of the times that
#                          it holds the word (None: off)
ONE = (2, 3)             # with such a list: pieces that are one word of the list (held this many times or more; up
#                          to this many pieces). A word that the page parts with a hyphen where the list never parts
#                          it, and of which a piece holds no vowel, is one syllable: the page spreads it under its
#                          notes ('wi-th', 'sha-ll'). And two or three read words side by side, of which one is no
#                          word of the list, are one word that a wide gap cut ('mer ciful'): it is parted as the list
#                          parts it. Not joined: a piece of one letter that is no vowel (what a misread leaves), a
#                          piece with a hyphen after it at the end of the row, a piece that is a word with its other
#                          neighbour, and a word that the page parts as the list does (None: off)
ABC = 'abcdefghijklmnopqrstuvwxyz'
VOWELS = 'aeiouy'
LABEL = True             # the first word of a row with a colon behind it ('Ison:', 'Refrain:') is a label: where the
#                          list does not hold it, it is not parted into two words that the list holds ('Is on:')
FIRST = (50, 80)         # the first row under a staff holds the first verse. Where Tesseract is less sure of its
#                          letters than the first number (of 100, the picture as it is) and as sure of the next row
#                          under the staff as the second, the first row is stray ink (a note by hand, a heading)
#                          and the next row holds the words. A first row with no letter at all is stray too


def program() -> str | None:
    """The path of Tesseract on this computer, or None when it is not installed."""
    return shutil.which(setting('TESSERACT', PROGRAM))


def available() -> bool:
    return program() is not None


def second_files() -> list[str]:
    """The folders of further language files of Tesseract (SCOREREADER_OCR_SECOND: one folder, or several with the
    path separator between them), each when it holds the file of the language that is read. Tesseract comes with a
    small file; its standard and its 'best' file hold a larger network that reads other words wrongly than the
    small one, and than each other. See SECOND."""
    language = setting('OCR_LANGUAGE', LANGUAGE)
    folders = [folder for folder in (setting('OCR_SECOND') or '').split(os.pathsep) if folder] if SECOND else []
    return [folder for folder in folders
            if all(os.path.exists(os.path.join(folder, name + '.traineddata')) for name in language.split('+'))]


def _line(crop: np.ndarray, folder: str, name: str, files: str | None = None) -> list[tuple[str, int, int, float]]:
    """The words of one line of text: (text, left, right, how sure) each, in the crop's px. `files`: the folder of
    another language file than the one that Tesseract comes with."""
    path = os.path.join(folder, name + '.png')
    cv2.imwrite(path, crop)
    # One thread: on a line of text Tesseract's threads only wait for each other, most of all on a busy computer.
    # The table of the words is asked for by its setting, not by the config file 'tsv': a folder with only a
    # language file has no config files.
    done = subprocess.run([program(), path, '-', '--psm', '7', '-l', setting('OCR_LANGUAGE', LANGUAGE)]
                          + (['--tessdata-dir', files] if files else []) + ['-c', 'tessedit_create_tsv=1'],
                          capture_output=True, text=True, check=False,
                          env=dict(os.environ, OMP_THREAD_LIMIT='1'))
    found = []
    for row in done.stdout.splitlines()[1:]:
        cells = row.split('\t')
        if len(cells) < 12 or cells[0] != '5' or not cells[11].strip():
            continue
        found.append((cells[11].strip(), int(cells[6]), int(cells[6]) + int(cells[8]), float(cells[10])))
    return found


def _no_digits(text: str, first: bool = False) -> str:
    """A word in which Tesseract read a letter as a digit: a 0 that stands alone is the word O, a 1 that stands
    alone is the word I (not at the start of a row or before a full stop: the number of a verse), and among letters
    a 0 is an o and a 1 is an I between capitals and an l between small letters. Other digits stay."""
    core = text.strip(STOPS + '\'"‘’“”' + (JOINS + LINES if DIGIT_JOIN else ''))
    if ROUND_SIDE and core.strip(ROUND_SIDE[0]) == '0' and core != '0' and '(0)' not in core:
        return text.replace('0', 'O')
    if core == '0':
        return text.replace('0', 'O')
    if core == '1':
        return text if first or '.' in text else text.replace('1', 'I')
    letters = [sign for sign in text if sign.isalpha()]
    if not letters or not any(sign in '01' for sign in text) or any(sign.isdigit() and sign not in '01' for sign in text):
        return text
    capitals = sum(sign.isupper() for sign in letters) * 2 > len(letters)
    return text.replace('0', 'O' if capitals else 'o').replace('1', 'I' if capitals else 'l')


def _joined(found: list[dict], words: list[tuple[str, float, float, float]], number: int, text: str,
            carried: str = '') -> str:
    """The letters of a piece of a line with the pieces that hyphens join it to: the syllables found so far, and the
    words of the line after the piece. '' where no hyphen joins it to another piece. `carried`: the letters of the
    word that the row before leaves open; they stand before the first word of the line."""
    before, at = '', len(found) - 1
    while at >= 0 and found[at]['join']:
        before, at = found[at]['text'] + before, at - 1
    if at < 0:
        before = carried + before
    after, goes = '', text[-1] in JOINS
    for other, _, _, _ in words[number + 1:]:
        other = other.replace('|', '').strip(LINES)
        if not other:
            continue
        if all(sign in JOINS + LINES + '.,' for sign in other):
            goes = goes or any(sign in JOINS for sign in other)
            continue
        if not goes:
            break
        after, goes = after + other, other[-1] in JOINS
        if not goes:
            break
    return ''.join(sign for sign in (before + text + after).lower() if sign.isalpha()) if before or after else ''


def _in_word(found: list[dict], words: list[tuple[str, float, float, float]], number: int, text: str,
             known: dict[str, int]) -> bool:
    """Whether a piece of a line stands in a word of the list with the pieces that hyphens join it to (see
    SURE_JOIN)."""
    word = _joined(found, words, number, text)
    return bool(word) and word in known


def _at_stops(piece: str) -> list[str]:
    """A piece of a line cut after each stop that stands between two letters (see STOP_INSIDE)."""
    parts, start = [], 0
    for at in range(1, len(piece) - 1):
        if piece[at] in STOPS and piece[at - 1].isalpha() and piece[at + 1].isalpha():
            parts.append(piece[start:at + 1])
            start = at + 1
    return parts + [piece[start:]]


def _syllables(words: list[tuple[str, float, float, float]], known: dict[str, int] | None = None,
               high: float | None = None, carried: str = '', short=None) -> list[dict]:
    """Cuts the words of a line into syllables: {'text', 'x0', 'x1', 'join' (a hyphen follows), 'sure'} each. A hyphen
    stands alone between two syllables, or inside a word that the reader took for one; the line after a held
    syllable is no letter, and a dash after a comma or a full stop is such a line too. `carried`: the letters of the
    word that the row before leaves open (see DIGIT_LIST). `short(text, left, right)`: whether every reading of the
    row holds this short word (see SURE_ALIKE)."""
    found: list[dict] = []
    for number, (text, left, right, sure) in enumerate(words):
        text = text.replace('|', '').strip(LINES)
        if not text:
            continue
        if DIGITS:
            digit, text = text, _no_digits(text, first=number == 0)
            other = ''.join('i' if was == '1' and now == 'l' else now for was, now in zip(digit, text)) \
                if len(digit) == len(text) else text
            if DIGIT_LIST and known and other != text:
                # A 1 that was read as an l can be an i: the list of words tells.
                alone = tuple(''.join(sign for sign in word.lower() if sign.isalpha()) for word in (text, other))
                ways = [tuple(_joined(found, words, number, word, lead) for word in (text, other)) for lead in (carried, '')]
                for with_l, with_i in [way for way in ways if way[0]] + [alone]:
                    if with_l in known or with_i in known:
                        text = text if with_l in known else other
                        break
        if ROUND and known and known.get('o', 0) >= 2:
            core = text.strip(STOPS + '\'"‘’“”')
            if core in ROUND[0] or (core == ROUND[1] and high and right - left >= ROUND[2] * high and not (
                    number + 1 < len(words) and words[number + 1][0][:1].isdigit())):
                text = text.replace(core, 'O')
            elif ROUND_SIDE and core != core.strip(ROUND_SIDE[0]) and '(' + core.strip(ROUND_SIDE[0]) + ')' not in core \
                    and core.strip(ROUND_SIDE[0]) in ROUND[0] + tuple(ROUND_SIDE[1]):
                text = text.replace(core.strip(ROUND_SIDE[0]), 'O')
        if DIGIT_END and known:
            marks = STOPS + JOINS + LINES + '\'"‘’“”'
            core = text.rstrip(marks)
            stray, hand = DIGIT_END
            bare = core.rstrip(stray).rstrip('\'"‘’“”') if stray else core
            if bare != core and bare and not any(sign.isdigit() for sign in bare) \
                    and ''.join(sign for sign in bare.lower() if sign.isalpha()) in known:
                text = bare + text[len(core):]
            elif hand and core[-1:] and core[-1] in hand and not any(sign.isdigit() for sign in core[:-1]) \
                    and core[:-1].isalpha() and core[:-1].lower() + 's' in known:
                text = core[:-1] + 's' + text[len(core):]
        if all(sign in JOINS + LINES + '.,' for sign in text):
            if found and any(sign in JOINS for sign in text) and found[-1]['text'][-1] not in STOPS:
                found[-1]['join'] = True
            continue
        letters = sum(sign.isalpha() for sign in text)
        if letters == 0:
            continue
        spared = False
        if sure < SURE[0] and letters < 3 and not (
                SURE[1] and known and ''.join(sign for sign in text.lower() if sign.isalpha()) in known) \
                and not (SURE_JOIN and known and _in_word(found, words, number, text, known)):
            spared = short is not None and short(text, left, right)
            if not spared:
                continue
        # The pieces between hyphens, each with its share of the word's width.
        wide = (right - left) / max(1, len(text))
        at = 0
        for piece in re.split('([' + re.escape(JOINS) + ']+|[' + re.escape(LINES) + ']+)', text):
            if piece and piece[0] in JOINS:
                if found and found[-1]['text'][-1] not in STOPS:
                    found[-1]['join'] = True
            elif piece and piece[0] not in LINES and any(sign.isalpha() for sign in piece):
                start = at
                for part in _at_stops(piece) if STOP_INSIDE else [piece]:
                    found.append({'text': part, 'x0': left + wide * start, 'x1': left + wide * (start + len(part)),
                                  'join': False, 'sure': sure})
                    if spared:
                        found[-1]['spared'] = True
                    start += len(part)
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


def _mute(piece: str) -> bool:
    """Whether a piece of a word holds letters and no vowel: letters of the plain alphabet only, each a consonant. (A
    letter with a sign of its own or of another alphabet is not judged: the list of vowels is that of the plain one.)"""
    letters = [sign for sign in piece.lower() if sign.isalpha()]
    return bool(letters) and all(sign in ABC and sign not in VOWELS for sign in letters)


def _mute_cut(text: str, cut: int) -> bool:
    """Whether a cut before sign `cut` of a word leaves a piece with no vowel between the cut and the next hyphen of
    the word, at one of its sides (see CUT_VOWEL)."""
    marks = JOINS + LINES
    before, after = text[:cut], text[cut:]
    pieces = []
    if any(sign in marks for sign in before):
        pieces.append(re.split('[' + re.escape(marks) + ']', before)[-1])
    if any(sign in marks for sign in after):
        pieces.append(re.split('[' + re.escape(marks) + ']', after)[0])
    return any(_mute(piece) for piece in pieces)


def _cut_wide(words: list[tuple[str, float, float, float]], grey: np.ndarray, band: dict,
              voiced: bool = False) -> list[tuple[str, float, float, float]]:
    """Cuts a word at its wide gaps. Where the words of a row stand close under quick notes, Tesseract reads two or
    three of them as one word. The pieces of ink in the word's box are counted, column by column: when each sign of
    the word is one piece, the gaps between the pieces are the gaps between its signs. A gap beside a hyphen is wide
    in any word and does not count. In a row from a typewriter the gap beside a thin letter (i, l) is wide in any
    word: there two words are parted only where their letters stand further apart than a letter's box. `voiced`: the
    words of the page fit the list of words, and each piece at a cut holds a vowel (see CUT_VOWEL)."""
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
                if CUT_VOWEL and voiced:
                    cuts = [number for number in cuts if not _mute_cut(text, number)]
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


class _Known(dict):
    """The list of words by letters alone (see _known), with `pairs`: the words that follow each other in the
    list's text (see PAIR), and `heads`: the beginnings of the words that the list parts, each with how often the
    list parts a word there (see MEND_HEAD)."""
    pairs: frozenset = frozenset()
    heads: dict | None = None


def _known(lex) -> dict[str, int]:
    """The list of words by letters alone: {the letters of a word: how often}, and the pairs of words that follow
    each other in the list's text (`lex.pairs`) as `pairs`."""
    def plain(word: str) -> str:
        return ''.join(sign for sign in word.lower() if sign.isalpha())

    known = _Known()
    for word, count in (lex or {}).items():
        letters = plain(word)
        known[letters] = known.get(letters, 0) + count
    known.pairs = frozenset((plain(first), plain(second)) for first, second in (getattr(lex, 'pairs', None) or ()))
    if MEND_HEAD:
        # The beginnings of the words that the list parts ('shep' of 'shep-herds', 'al' and 'alle' of 'al-le-lu-ia'),
        # each with how often the list parts a word there.
        known.heads = {}
        for parts, count in (getattr(lex, 'parts', None) or {}).items():
            way = [plain(part) for part in parts]
            for cut in range(1, len(way) if all(way) else 0):
                head = ''.join(way[:cut])
                known.heads[head] = known.heads.get(head, 0) + count
    return known


def _ways(lex, known: dict[str, int]) -> dict[str, tuple[str, ...]]:
    """How the list of words parts its words into syllables: {the letters of a word: its syllables}, for the words
    that the list parts in one way most of the times (`lex.parts`: {the syllables of a word: how often}; a list
    with no parted words gives none)."""
    ways: dict[str, tuple[tuple[str, ...], int]] = {}
    if not PARTS:
        return _Ways()
    for parts, count in (getattr(lex, 'parts', None) or {}).items():
        way = tuple(''.join(sign for sign in part.lower() if sign.isalpha()) for part in parts)
        word = ''.join(way)
        if len(way) > 1 and all(way) and count >= PARTS[0] and count >= PARTS[1] * known.get(word, 0) \
                and count > ways.get(word, (None, 0))[1]:
            ways[word] = (way, count)
    found = _Ways({word: way for word, (way, _) in ways.items()})
    found.parted = {''.join(sign for part in parts for sign in part.lower() if sign.isalpha())
                    for parts in (getattr(lex, 'parts', None) or {}) if len(parts) > 1}
    return found


class _Ways(dict):
    """How the list parts its words (see _ways), with `parted`: every word that the list parts in any way."""
    parted: set = set()


def _between(syllables: list[dict], known: dict[str, int]) -> list[dict]:
    """A short word that the list of words does not hold becomes the list's word one letter away that stands
    between its two neighbours in the list's text (see PAIR). Capitals and signs stay as they were read."""
    pairs = getattr(known, 'pairs', None) or frozenset()
    words = _read_words(syllables)
    texts = [''.join(sign for part in word for sign in part['text'].lower() if sign.isalpha()) for word in words]
    for number in range(1, len(words) - 1):
        read = texts[number]
        if len(words[number]) != 1 or not read or len(read) > PAIR or read in known:
            continue
        before, after = texts[number - 1], texts[number + 1]
        near = set()
        for at in range(len(read) + 1):
            near.update(read[:at] + sign + read[at:] for sign in ABC)
            if at < len(read):
                near.add(read[:at] + read[at + 1:])
                near.update(read[:at] + sign + read[at + 1:] for sign in ABC)
        meant = [new for new in near if new and new != read and new in known
                 and (before, new) in pairs and (new, after) in pairs]
        if len(meant) != 1:
            continue
        part = dict(words[number][0])
        text = part['text']
        places = [at for at, sign in enumerate(text) if sign.isalpha()]
        new = meant[0].upper() if text[places[0]].isupper() and all(text[at].isupper() for at in places) and len(places) > 1 \
            else meant[0].capitalize() if text[places[0]].isupper() else meant[0]
        part['text'] = text[:places[0]] + new + text[places[-1] + 1:]
        words[number][0] = part
        texts[number] = meant[0]
    return [part for word in words for part in word]


def _whole(syllables: list[dict], known: dict[str, int], ways: dict[str, tuple[str, ...]]) -> list[dict]:
    """Pieces side by side that are one word of the list become that word again (see ONE). _parted() parts it as
    the list does afterwards."""
    parted = getattr(ways, 'parted', set())

    def letters(part: dict) -> str:
        return ''.join(sign for sign in part['text'].lower() if sign.isalpha())

    def word(text: str) -> bool:
        return known.get(text, 0) >= 1 and (len(text) > 1 or text in 'aio')

    def lone(text: str) -> bool:
        return len(text) == 1 and text not in VOWELS          # one letter that is no syllable: what a misread leaves

    def one(run: list[dict]) -> dict:
        return dict(run[0], text=''.join(part['text'] for part in run), x1=run[-1]['x1'], join=run[-1]['join'])

    # The words as they were read: syllables with a hyphen between them are one word.
    words: list[list[dict]] = [[]]
    for number, part in enumerate(syllables):
        words[-1].append(part)
        if not part['join'] and number + 1 < len(syllables):
            words.append([])
    for number, run in enumerate(words):
        # A word that was read with a hyphen and that the list never parts, where a piece is no syllable (it holds
        # no vowel): the page spreads one syllable under its notes.
        whole = ''.join(letters(part) for part in run)
        beside = [''.join(letters(part) for part in other) for other in words[max(0, number - 1):number] + words[number + 1:number + 2]]
        pieces = [letters(part) for part in run]
        if len(run) > 1 and all(pieces) and known.get(whole, 0) >= ONE[0] and whole not in parted \
                and all(any(sign in VOWELS for sign in text) for text in beside + pieces[:1]) \
                and not any(lone(text) for text in pieces) and not run[-1]['join'] \
                and any(not any(sign in VOWELS for sign in text) for text in pieces):
            # (A piece beside it that has no vowel is no syllable: it belongs to this word, a longer one. And a first
            # piece with no vowel is the end of the word before: 'as k-ing'.)
            words[number] = [one(run)]
    found: list[dict] = []
    at = 0
    while at < len(words):
        done = False
        for count in range(ONE[1], 1, -1):
            runs = words[at:at + count]
            parts = [part for run in runs for part in run]
            if len(runs) < count or len(parts) > ONE[1]:
                continue
            texts = [''.join(letters(part) for part in run) for run in runs]
            whole = ''.join(texts)
            if not all(texts) or known.get(whole, 0) < ONE[0] or all(word(text) for text in texts):
                continue
            if any(lone(letters(part)) for part in parts) or parts[-1]['join']:
                continue          # (a hyphen after the last piece, at the end of the row: the word goes on)
            if whole not in ways and whole in parted:
                continue          # the list parts the word in more than one way
            if len(ways.get(whole, ())) > len(parts):
                continue          # fewer syllables than the list has (see PARTS)
            beside = [''.join(letters(part) for part in run) for run in words[max(0, at - 1):at] + words[at + count:at + count + 1]]
            if not all(word(text) for text in beside):
                continue          # a piece is left over beside it: the word may be a longer one that the list lacks
            if any(known.get(text + whole, 0) or known.get(whole + text, 0) for text in beside):
                continue          # with the word beside it, it is a longer word that the list holds seldom
            before, after = ''.join(letters(part) for part in words[at - 1]) if at else '', beside[-1] if at + count < len(words) else ''
            if (after and not word(texts[-1]) and word(texts[-1] + after)) or (before and not word(texts[0]) and word(before + texts[0])):
                continue          # the piece that is no word is one with the word at its other side ('the se raphim')
            if len(ways.get(whole, ())) == len(parts):
                # As many syllables as the list has: they stay as the page parts them, and are one word.
                found.extend(dict(part, join=True) for part in parts[:-1])
                found.append(parts[-1])
            else:
                found.append(one(parts))
            at += count
            done = True
            break
        if not done:
            found.extend(words[at])
            at += 1
    return found


def _parted(syllables: list[dict], ways: dict[str, tuple[str, ...]]) -> list[dict]:
    """Parts the words into syllables as the list of words does, where a word was read in fewer syllables than the
    list parts it into ('mercy' under two notes, or 'mer cy' whose hyphen the scan lost). Each letter keeps its
    place in the row: the letters of a syllable that was read stand evenly in its width."""
    found: list[dict] = []
    word: list[dict] = []
    for number, syllable in enumerate(syllables):
        word.append(syllable)
        if syllable['join'] and number + 1 < len(syllables):
            continue
        signs = [(part, at) for part in word for at in range(len(part['text']))]
        way = ways.get(''.join(part['text'][at] for part, at in signs if part['text'][at].isalpha()).lower())
        if way and len(way) > len(word):
            ends, letters = [], 0          # the number of the last sign of each syllable
            for piece in way:
                letters += len(piece)
                ends.append(letters)
            groups: list[list[tuple[dict, int]]] = [[] for _ in way]
            seen = 0
            for part, at in signs:
                seen += part['text'][at].isalpha()
                # a sign that is no letter stays with the letter before it
                groups[next((index for index, end in enumerate(ends) if seen <= end), len(way) - 1)].append((part, at))

            def edge(place: tuple[dict, int], right: int) -> float:
                part, at = place
                return part['x0'] + (part['x1'] - part['x0']) * (at + right) / max(1, len(part['text']))

            for index, group in enumerate(groups):
                found.append(dict(group[0][0], text=''.join(part['text'][at] for part, at in group),
                                  x0=edge(group[0], 0), x1=edge(group[-1], 1),
                                  join=True if index + 1 < len(groups) else word[-1]['join']))
                # 'cut': this syllable and the one before it are one piece of the page, as it was read, that the list
                # of words parted in two (scorereader.lyrics.ONE_NOTE asks the notes about it). A piece that the
                # mending changed is none ('ter-nal' at the start of a row, mended to 'e-ter-nal': the e has no
                # ink), and a piece that gives letters to a third syllable is none either.
                found[-1].pop('cut', None)
                if index and group and groups[index - 1]:
                    piece = group[0][0]
                    if (all(part is piece for part, _ in group) and all(part is piece for part, _ in groups[index - 1])
                            and not (index >= 2 and groups[index - 2] and groups[index - 2][-1][0] is piece)
                            and not (index + 1 < len(groups) and groups[index + 1] and groups[index + 1][0][0] is piece)
                            and piece['text'] == piece.get('read')):
                        found[-1]['cut'] = True
        else:
            found.extend(word)
        word = []
    return found


def _cuts(read: str, known: dict[str, int], fits: bool = False) -> list[int]:
    """Where a word that the list of words does not hold is parted into words that it holds: the places between
    its letters, or none. Two words of two letters or more come first; then, on a page that the list fits (`fits`:
    a list in another language holds an 'a' and an 'o' too), a word of one letter and a word, and then three
    words. The first of these that the list allows decides, and only when it allows one way."""
    total = sum(known.values())

    def mute(pieces: list[str]) -> bool:
        return bool(ENDS_VOWEL) and any(len(piece) > 1 and _mute(piece) for piece in pieces)

    def two(pieces: list[str], short: bool) -> bool:
        small = [piece for piece in pieces if len(piece) < ENDS[1]]
        if any(known.get(piece, 0) < ENDS[0] for piece in pieces) or bool(small) != short:
            return False
        return not small or (len(small) == 1 and len(small[0]) == 1 and known[small[0]] >= ENDS[3] * total
                             and all(len(piece) >= ENDS[2] for piece in pieces if piece is not small[0]))

    def more(pieces: list[str]) -> bool:
        return all(known.get(piece, 0) >= max(ENDS[0], THREE[0 if len(piece) > 2 else 1] * total) for piece in pieces)

    tiers = [(2, lambda pieces: two(pieces, False), False), (2, lambda pieces: two(pieces, True), True)]
    if THREE:
        tiers.append((3, more, True))
    for count, allowed, daring in tiers:
        if daring and not fits:
            break
        ways = [list(cuts) for cuts in itertools.combinations(range(1, len(read)), count - 1)
                if allowed([read[first:last] for first, last in zip((0,) + cuts, cuts + (len(read),))])]
        if ways:
            # (A way with a piece that holds no vowel counts as a way and is not taken: ENDS_VOWEL only takes cuts away.)
            return ways[0] if len(ways) == 1 and not mute([read[first:last] for first, last in
                                                           zip([0, *ways[0]], [*ways[0], len(read)])]) else []
    return []


def _ends(syllables: list[dict], known: dict[str, int], fits: bool = False, carried: str = '') -> list[dict]:
    """Sets where the words end by the list of words. Tesseract reads the line of a held syllable as a hyphen
    ('Thy-church'), it reads two words that stand close as one ('thelord'), and it misses a hyphen here and there
    ('re joice'). A word that the list does not hold is parted at the one place, at a hyphen or between two letters,
    where the list holds the words on both sides, or (`fits`: on a page in the list's language) at two places ('mercyonus'). Two words in a row are joined where the list holds them as one
    word and does not hold one of them alone. `carried`: the letters of the word that the row before leaves open (see
    ENDS_CARRIED)."""
    found: list[dict] = []
    word: list[dict] = []
    for number, syllable in enumerate(syllables):
        word.append(dict(syllable))
        if syllable['join'] and number + 1 < len(syllables):
            continue
        places = [(part, at) for part in word for at, sign in enumerate(part['text']) if sign.isalpha()]
        read = ''.join(part['text'][at] for part, at in places).lower()
        label = LABEL and number + 1 == len(word) and len(word) == 1 and word[0]['text'].rstrip().endswith(':') \
            and word[0]['text'][:1].isupper()
        going = bool(ENDS_CARRIED and carried and not found and known.get(carried + read, 0) >= ENDS[0])
        for at in reversed(_cuts(read, known, fits) if known.get(read, 0) < ENDS[0] and not label and not going else []):
            part, place = places[at]
            before = places[at - 1][0]
            if before is not part:
                before['join'] = False
            else:
                text, wide = part['text'], (part['x1'] - part['x0']) / max(1, len(part['text']))
                second = dict(part, text=text[place:], x0=part['x0'] + wide * place)
                part.update(text=text[:place], x1=part['x0'] + wide * place, join=False)
                word.insert(next(n for n, other in enumerate(word) if other is part) + 1, second)
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


_RUNS: list = [None, frozenset(), 0]


def _odd(word: str, known: dict[str, int]) -> int:
    """How many runs of three letters of a word no word of the list holds (see MEND_ODD). '^' stands before the
    word and '$' after it."""
    if _RUNS[0] is not known:
        _RUNS[:] = [known, frozenset(text[at:at + 3] for held in known for text in ('^' + held + '$',)
                                    for at in range(len(text) - 2)), max(known.values(), default=0)]
    text = '^' + word + '$'
    return sum(text[at:at + 3] not in _RUNS[1] for at in range(len(text) - 2))


def _mend_twin(syllables: list[dict], known: dict[str, int], mended: list | None = None) -> list[dict]:
    """Mends a word that the list does not hold where two letters that touch were read as one (see MEND_TWIN): the
    word becomes the one word of the list that has the two letters at one such place. `mended` takes each word that
    was mended, as it was read."""
    found: list[dict] = []
    word: list[dict] = []
    for number, syllable in enumerate(syllables):
        word.append(dict(syllable))
        if syllable['join'] and number + 1 < len(syllables):
            continue
        places = [(part, at) for part in word for at, sign in enumerate(part['text']) if sign.isalpha()]
        read = ''.join(part['text'][at] for part, at in places).lower()
        found.extend(word)
        word = []
        if len(read) < 3 or read in known:
            continue
        meant = {(at, two) for one, two in MEND_TWIN for at in range(len(read))
                 if read.startswith(one, at) and known.get(read[:at] + two + read[at + len(one):], 0) >= MEND[1]}
        if len(meant) != 1:
            continue
        (at, two), = meant
        part, place = places[at]
        text = part['text']
        part['text'] = text[:place] + (two.upper() if text[place].isupper() else two) + text[place + 1:]
        if mended is not None:
            mended.append(read)
    return found


def _mend_pair(syllables: list[dict], known: dict[str, int], mended: list | None = None, carried: str = '') -> list[dict]:
    """Joins two words side by side that the list does not hold into the one word of the list that they are with
    one letter read otherwise (see MEND_PAIR). `mended` takes each such pair, as it was read. The second word of
    a row that goes on from the word that the row before leaves open (`carried`) is no piece of such a pair: a
    mark before it is stray ink (see MEND_REST_STRAY)."""
    words: list[list[dict]] = [[]]
    for number, syllable in enumerate(syllables):
        words[-1].append(dict(syllable))
        if not syllable['join'] and number + 1 < len(syllables):
            words.append([])

    def letters(parts: list[dict]) -> list[tuple[dict, int]]:
        return [(part, at) for part in parts for at, sign in enumerate(part['text']) if sign.isalpha()]

    for first, second in zip(words, words[1:]):
        places = letters(first) + letters(second)
        read = ''.join(part['text'][at] for part, at in places).lower()
        one, other = (''.join(part['text'][at] for part, at in letters(parts)).lower() for parts in (first, second))
        if not one or not other or len(read) < MEND_PAIR or first[-1]['join'] or second[-1]['join'] \
                or read in known or (not MEND_PAIR_RARE and (one in known or other in known)):
            continue
        if MEND_REST_STRAY and carried and first is words[0] and len(other) >= MEND_BEFORE and carried + other in known:
            continue
        meant = {read[:at] + sign + read[at + 1:]: at for at in range(len(read)) for sign in ABC if sign != read[at]}
        meant = {new: at for new, at in meant.items() if known.get(new, 0) >= MEND[1]}
        if len(meant) != 1:
            continue
        (new, at), = meant.items()
        if max(known.get(one, 0), known.get(other, 0)) * (MEND_PAIR_RARE or 0) > known[new]:
            continue          # a piece that the list holds is a word, unless the whole is far more common
        if at == len(read) - 1:
            continue          # the end of a word changes in the language itself (see MEND)
        part, place = places[at]
        text = part['text']
        part['text'] = text[:place] + (new[at].upper() if text[place].isupper() else new[at]) + text[place + 1:]
        first[-1]['join'] = True
        if mended is not None:
            mended.append(read)
    return [part for parts in words for part in parts]


def _leads(carried: str, pieces: list[str], known: dict[str, int]) -> bool:
    """Whether the first syllables of a word (`pieces`: its syllables as they were read) make a word of the list
    with the letters of the word that the row before leaves open (`carried`; see MEND_REST)."""
    if len(carried) < MEND_BEFORE:
        return False
    lead = ''
    for piece in pieces[:-1]:
        lead += ''.join(sign for sign in piece.lower() if sign.isalpha())
        if len(lead) >= MEND_BEFORE and carried + lead in known:
            return True
    return False


def _carried_on(row: list[dict], known: dict[str, int], carried: str) -> int:
    """The letters of the first word of a row where that word is no word of the list and goes on from the word
    that the row before leaves open (`carried`), as MEND_REST_FIT counts them; 0 otherwise."""
    if not (MEND_REST_FIT and MEND_BEFORE and carried and row):
        return 0
    first = _read_words(row)[0]
    read = ''.join(sign for part in first for sign in part['text'].lower() if sign.isalpha())
    if not read or read in known:
        return 0
    if (MEND_REST and _leads(carried, [part['text'] for part in first], known)) or (MEND_REST_FIT > 1 and carried + read in known):
        return len(read)
    return 0


def _stray_before(row: list[dict], known: dict[str, int], carried: str) -> list[dict]:
    """A row without its first word, where that word is short, Tesseract is not sure of it, and the word after it
    goes on from the word that the row before leaves open (`carried`; see MEND_REST_STRAY)."""
    words = _read_words(row)
    if len(words) < 2 or len(words[0]) != 1 or words[0][0]['join']:
        return row
    first = ''.join(sign for sign in words[0][0]['text'].lower() if sign.isalpha())
    after = ''.join(sign for part in words[1] for sign in part['text'].lower() if sign.isalpha())
    if (len(first) > MEND_REST_STRAY[0] or words[0][0].get('sure', 0.0) >= MEND_REST_STRAY[1] or carried + first in known
            or len(after) < MEND_BEFORE):
        return row
    if carried + after in known or (MEND_REST and _leads(carried, [part['text'] for part in words[1]], known)):
        return row[1:]
    return row


def _begins(known: dict[str, int], letters: str) -> int:
    """How often the list of words parts a word after these letters (see MEND_HEAD)."""
    return (getattr(known, 'heads', None) or {}).get(letters, 0)


def _framed(carried: str, parts: list[dict], known: dict[str, int]) -> str | None:
    """The letters between the piece that the row before leaves open and the last syllable of the first word of a row,
    where the word has two syllables, the list holds one word only in that frame and Tesseract is not sure of the
    first syllable (MEND_FRAME)."""
    if len(parts) != 2 or parts[-1]['join'] or parts[0].get('sure', 0.0) >= MEND[2]:
        return None
    read, tail = (''.join(sign for sign in part['text'].lower() if sign.isalpha()) for part in parts)
    if len(carried) < MEND_FRAME[0] or len(tail) < MEND_FRAME[1] or not read:
        return None
    meant = {word[len(carried):len(word) - len(tail)] for word, count in known.items()
             if count >= MEND[1] and len(word) > len(carried) + len(tail) and word.startswith(carried) and word.endswith(tail)
             and abs(len(word) - len(carried) - len(tail) - len(read)) <= MEND_FRAME[2]}
    between = meant.pop() if len(meant) == 1 else None
    return between if between != read else None        # read as the list has it: nothing to mend


def _mend(syllables: list[dict], known: dict[str, int], mended: list | None = None,
          agreed: frozenset[str] | set[str] = frozenset(), alike=None, carried: str = '') -> list[dict]:
    """Mends the words that the list of words does not hold. Tesseract reads a letter of a word wrongly here and
    there ('tnose', 'orlent', 'trinty'); the hymns of one church use the same words again and again, and the list
    tells which word was meant. A word is the syllables that hyphens join. Only letters count: capitals, commas and
    apostrophes stay as they were read. A word that the list holds is never changed, nor a word in `agreed` (a
    word that another reading of the row holds too, see SECOND), and a letter that is a whole
    syllable is never taken away (it is a word of its own whose hyphen was read wrongly: 'O-joy'). A vowel that is
    missing between two syllables becomes a syllable of its own ('Trin-ty' is 'Trin-i-ty'), unless the syllable
    before it has no vowel yet ('Gl-ry' is 'Glo-ry'). `mended` takes each word that was mended, as it was read.
    `carried` are the letters of the word that the row before leaves open (see MEND_BEFORE)."""
    found: list[dict] = []
    word: list[dict] = []
    ahead = ''
    for number, syllable in enumerate(syllables):
        word.append(dict(syllable))
        if syllable['join'] and number + 1 < len(syllables):
            continue
        places = [(part, at) for part in word for at, sign in enumerate(part['text']) if sign.isalpha()]
        read = ''.join(part['text'][at] for part, at in places).lower()
        sure = min(part.get('sure', 0.0) for part in word)
        found.extend(word)
        parts, word = word, []
        before, ahead = ahead, read
        if MEND_BEFORE and carried and len(found) == len(parts) and read and read not in known and read not in agreed:
            # The first word of the row with the piece that the row before leaves open.
            if carried + read in known:
                continue
            rest = {(at, read[:at] + sign + read[at + 1:]) for at in range(len(read)) for sign in ABC
                    if sign != read[at] and known.get(carried + read[:at] + sign + read[at + 1:], 0) >= MEND[1]}
            if len(rest) == 1 and sure < MEND[2] and min(len(carried), len(read)) >= MEND_BEFORE:
                (at, new), = rest
                part, place = places[at]
                text = part['text']
                part['text'] = text[:place] + (new[at].upper() if text[place].isupper() else new[at]) + text[place + 1:]
                if mended is not None:
                    mended.append(read)
                continue
            between = _framed(carried, parts, known) if MEND_FRAME else None
            if between:
                text = parts[0]['text']
                first = next(at for at, sign in enumerate(text) if sign.isalpha())
                last = max(at for at, sign in enumerate(text) if sign.isalpha())
                capitals = sum(sign.isupper() for sign in text)       # a row in capitals stays in capitals
                between = between.upper() if capitals > max(1, sum(sign.islower() for sign in text)) \
                    else between.capitalize() if text[first].isupper() else between
                parts[0]['text'] = text[:first] + between + text[last + 1:]
                if mended is not None:
                    mended.append(read)
                continue
            if MEND_REST and _leads(carried, [part['text'] for part in parts], known):
                continue          # 'car-' and 'ry-ing': 'carry'
        if len(read) < MEND[0] or read in known or read in agreed:
            continue
        odd = _odd(read, known) if MEND_ODD or MEND_OFTEN else 0
        firm = (sure >= MEND[2] or (alike is not None and read in alike())) and not (MEND_ODD and odd >= MEND_ODD)
        if firm and (not MEND_OFTEN or parts[-1]['join']):     # a word that goes on in the next row is not whole
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
        if MEND_OPEN and parts[-1]['join'] and how == 'more' and at == len(read):
            continue
        if MEND_HEAD and parts[-1]['join'] and _begins(known, read) >= max(1, _begins(known, new)):
            continue              # the word goes on in the next row, and the list parts a word so
        last = at >= len(read) - 1 + (how == 'more')
        if MEND_S and last and ((how == 'less' and read[-1] == 's') or (how == 'more' and new[-1] == 's')):
            continue
        often = bool(MEND_OFTEN) and known[new] >= MEND_OFTEN[0] * _RUNS[2]
        if often and parts[-1]['join']:
            often = False
        if often:
            # A piece of a word whose hyphen was not read ('glori ous') is no misread word.
            after = ''
            for other in syllables[number + 1:]:
                after += ''.join(sign for sign in other['text'].lower() if sign.isalpha())
                if not other['join']:
                    break
            often = before + read not in known and read + after not in known
        if firm and not often and not (odd and not last and known[new] >= MEND_OFTEN[1] * _RUNS[2]):
            continue
        if last and sure >= MEND[3] and not often:
            continue
        part, place = places[min(at, len(places) - 1)]
        text = part['text']
        if mended is not None and (how != 'less' or sum(sign.isalpha() for sign in text) > 1):
            mended.append(read)
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


def _no_cross(crop: np.ndarray, around: np.ndarray, down: int, top: float, bottom: float, space: float) -> np.ndarray:
    """The picture of a row without the ink that crosses it (see CROSS). `around` is the page around the picture,
    which begins `down` rows under its top; `top` and `bottom` are the band's edges in the picture. An upright
    stroke that is longer than a letter, or that comes in over the edge of `around` (a bar line, a stem), goes
    outside the band; inside the band it goes where it runs through the whole band and on at both sides, or where
    no other ink hangs on it. A letter that a stem touches keeps every stroke. And a slur, which is long, bent and
    thin where it runs, goes but for the letters that hang on it."""
    high = bottom - top
    ink = (around < 128).astype(np.uint8)
    rows = ink.shape[0]
    first, last = max(0, int(top) + down), min(rows, int(bottom) + down + 1)
    grow = int(max(0.0, CROSS[4] * space - high) / 2)          # a low band holds the small letters only
    first, last = max(down, first - grow), min(down + crop.shape[0], last + grow)
    reach = int(max(CROSS[2] * high, CROSS[1] * space)) | 1
    padded = np.pad(ink, ((reach, reach), (0, 0)))
    upright = cv2.morphologyEx(padded, cv2.MORPH_OPEN, np.ones((reach, 1), np.uint8))[reach:-reach]
    from_top = np.cumprod(ink, axis=0, dtype=np.uint8)
    from_top[:, from_top.sum(axis=0) <= down] = 0
    from_bottom = np.cumprod(ink[::-1], axis=0, dtype=np.uint8)[::-1].copy()
    from_bottom[:, from_bottom.sum(axis=0) <= rows - down - crop.shape[0]] = 0
    upright = upright | from_top | from_bottom
    mask = upright.copy()
    mask[first:last] = 0
    if upright[first:last].any():
        inside = np.ascontiguousarray(upright[first:last])
        other = ink[first:last] & (1 - inside)
        edge = int(CROSS[3] * space)
        count, labels, boxes, _ = cv2.connectedComponentsWithStats(inside, connectivity=8)
        for label in range(1, count):
            left, upper, wide, tall = boxes[label][:4]
            piece = labels[upper:upper + tall, left:left + wide] == label
            through = (tall >= last - first and first - edge >= 0 and last - 1 + edge < rows
                       and upright[first - edge, left:left + wide].any() and upright[last - 1 + edge, left:left + wide].any())
            if not through:
                grown = cv2.dilate((labels == label).astype(np.uint8), np.ones((3, 5), np.uint8))
                if (grown & other).any():
                    continue                               # a letter hangs on it: the stem that touches a letter
            mask[first + upper:first + upper + tall, left:left + wide][piece] = 1
    # A slur: one thin stroke in each column, over a long way, and it rises or falls. The upright strokes are
    # taken away first, but for the ink of a stroke that lies between other ink (where the slur crosses a bar line).
    rest = ink & (1 - upright)
    wide_gap = int(CROSS[8] * space) | 1
    rest = np.ascontiguousarray(rest | (upright & cv2.morphologyEx(np.pad(rest, ((0, 0), (wide_gap, wide_gap))), cv2.MORPH_CLOSE,
                                                                  np.ones((1, wide_gap), np.uint8))[:, wide_gap:-wide_gap]))
    thin = CROSS[7] * space
    count, labels, boxes, _ = cv2.connectedComponentsWithStats(rest, connectivity=8)
    for label in range(1, count):
        left, upper, wide, tall = boxes[label][:4]
        if upper + tall <= down or upper >= down + crop.shape[0] or wide < CROSS[5] * high:
            continue                                   # not in the picture; a letter, a word, a dash
        if upper <= 0 or upper + tall >= rows:
            upper, tall = down, crop.shape[0]          # it hangs on the staff: what the picture shows of it
        piece = labels[upper:upper + tall, left:left + wide] == label
        ink_in = piece.sum(axis=0)
        strokes = (np.diff(np.pad(piece.astype(np.int8), ((1, 0), (0, 0))), axis=0) > 0).sum(axis=0)
        line = (ink_in > 0) & (ink_in <= thin) & (strokes == 1)
        if line.sum() < CROSS[5] * high:
            continue
        middle = (piece * np.arange(tall)[:, None]).sum(axis=0)[line] / ink_in[line]
        if np.percentile(middle, 95) - np.percentile(middle, 5) < CROSS[6] * high:
            continue                                   # a level line: the line of a held syllable, a row of dashes
        mask[upper:upper + tall, left:left + wide][piece & line[None, :]] = 1
    mask = cv2.dilate(mask, np.ones((5, 5), np.uint8))[down:down + crop.shape[0]]     # with its pale rim
    if not mask.any():
        return crop
    out = crop.copy()
    out[mask > 0] = 255
    return out


def _stroke(ink: np.ndarray) -> float:
    """How thick the upright strokes of a piece of a row are: the median of its runs of ink along the rows, in px."""
    runs = []
    for line in ink:
        edges = np.flatnonzero(np.diff(np.concatenate(([0], line.astype(np.int8), [0]))))
        runs.extend((edges[1::2] - edges[::2]).tolist())
    return float(np.median(runs)) if runs else 0.0


def _unread(words: list[tuple[str, float, float, float]], grey: np.ndarray, band: dict) -> list[tuple[int, int]]:
    """The letters of a row that a reading left out (see UNREAD): the columns of each piece of ink between two words
    of the reading that is as wide and as high as a letter of the row, ends with the row, stands apart from both
    words and has strokes as thick as the row's letters."""
    if not UNREAD:
        return []
    least, most, share, over, under, apart, slim, fat = UNREAD
    top, bottom = max(0, int(band['top'])), int(band['bottom'])
    high = max(1, bottom - top)
    usual = None
    found = []
    # A bar line that was read as a stroke covers no letter: its box can begin in one.
    words = [word for word in words if word[0].strip('|')]
    for (_, _, before, _), (_, after, _, _) in zip(words, words[1:]):
        first, last = max(0, int(before) + 1), min(grey.shape[1], int(after))
        if last - first < (least + 2 * apart) * high:
            continue
        columns = (grey[top:bottom + 1, first:last] < 128).any(axis=0)
        edges = np.flatnonzero(np.diff(np.concatenate(([0], columns.astype(np.int8), [0]))))
        for begin, end in zip(edges[::2].tolist(), edges[1::2].tolist()):
            if not least * high <= end - begin <= most * high or begin < apart * high or last - first - end < apart * high:
                continue
            piece = grey[:, first + begin:first + end] < 128
            rows = piece.any(axis=1)
            if rows[top:bottom + 1].mean() < share:
                continue
            up, down = top, min(bottom, len(rows) - 1)
            while up > 0 and rows[up - 1]:
                up -= 1
            while down + 1 < len(rows) and rows[down + 1]:
                down += 1
            if top - up > over * high or down - bottom > under * high:
                continue
            if usual is None:
                usual = _stroke(grey[top:bottom + 1, max(0, int(words[0][1])):min(grey.shape[1], int(words[-1][2]) + 1)] < 128)
            thick = _stroke(piece[up:down + 1])
            if usual > 0 and slim * usual <= thick <= fat * usual:
                found.append((first + begin, first + end - 1))
    return found


def _lone_i(words: list[tuple[str, float, float, float]], grey: np.ndarray, band: dict) -> list[tuple[str, float, float, float]]:
    """The word I that Tesseract read as a stroke. A '|' that stands alone between two words is a bar line, a line
    by hand or the letter I. The letter is as high as the row's capitals (its ink begins near the top of the band
    or over it and ends at the foot of the band) and as thick as the strokes of the row's letters; a bar line goes
    on over the row, and a line by hand or a dashed line is a hairline."""
    if not LONE_I or len(words) < 3:
        return words
    top, bottom = int(band['top']), int(band['bottom'])
    high = max(1, bottom - top)
    found = list(words)
    usual = None
    for number in range(1, len(words) - 1):
        text, left, right, sure = words[number]
        if text != '|' or not all(any(sign.isalpha() for sign in words[other][0]) for other in (number - 1, number + 1)):
            continue
        first, last = max(0, int(left)), min(grey.shape[1], int(right) + 1)
        box = grey[:, first:last] < 128
        rows = box.any(axis=1)
        middle = (top + bottom) // 2
        if last <= first or not 0 <= middle < len(rows) or not rows[middle]:
            continue
        up = down = middle
        while up > 0 and rows[up - 1]:
            up -= 1
        while down + 1 < len(rows) and rows[down + 1]:
            down += 1
        if not (-LONE_I[0] * high <= top - up < LONE_I[1] * high and abs(down - bottom) <= LONE_I[2] * high):
            continue
        if usual is None:
            begin, end = max(0, int(words[0][1])), min(grey.shape[1], int(words[-1][2]) + 1)
            usual = _stroke(grey[max(0, top):bottom + 1, begin:end] < 128)
        thick = float(np.median(box[up:down + 1].sum(axis=1)))
        if usual > 0 and LONE_I[3] * usual <= thick <= LONE_I[4] * usual:
            found[number] = ('I', left, right, sure)
    return found


def _four_a(words: list[tuple[str, float, float, float]], grey: np.ndarray, band: dict) -> list[tuple[str, float, float, float]]:
    """The letter a that Tesseract read as a 4 where the stem of a note runs into its top (see FOUR_A): a lone 4
    between two words whose box holds the small bowl of an a low in the band."""
    if not FOUR_A or len(words) < 3:
        return words
    top, bottom = int(band['top']), int(band['bottom'])
    high = max(1, bottom - top)
    found = list(words)
    for number in range(1, len(words) - 1):
        text, left, right, sure = words[number]
        if text.strip('\'"‘’“”(') != '4' or not any(any(sign.isalpha() for sign in word[0]) for word in words[:number]) \
                or not any(any(sign.isalpha() for sign in word[0]) for word in words[number + 1:]):
            continue
        first, last = max(0, int(left)), min(grey.shape[1], int(right) + 1)
        upper, lower = max(0, top - high), min(grey.shape[0], bottom + high // 2 + 1)
        if last - first < 3 or lower - upper < 3 or right - left > FOUR_A[2] * high:
            continue
        paper = (grey[upper:lower, first:last] >= 128).astype(np.uint8)
        count, _, stats, middles = cv2.connectedComponentsWithStats(paper, connectivity=4)
        for label in range(1, count):
            x, y, wide, tall, area = (int(value) for value in stats[label])
            if x > 0 and y > 0 and x + wide < paper.shape[1] and y + tall < paper.shape[0] and area >= 4 \
                    and middles[label][1] + upper - top >= FOUR_A[0] * high and area <= FOUR_A[1] * high * high:
                found[number] = (text.replace('4', 'a'), left, right, sure)
                break
    return found


def _no_solid(words: list[tuple[str, float, float, float]], grey: np.ndarray, band: dict) -> list[tuple[str, float, float, float]]:
    """The words of a line without those that are solid ink (see SOLID)."""
    top, bottom = int(band['top']), int(band['bottom'])
    room = int(round(SOLID[2] * (bottom - top)))
    top, bottom = max(0, top - room), bottom + room
    found = []
    for text, left, right, sure in words:
        first, last = max(0, int(left)), min(grey.shape[1], int(right) + 1)
        if sum(sign.isalpha() for sign in text) >= 2 and last > first and bottom > top \
                and ((grey[top:bottom, first:last] < 128).mean(axis=0) > SOLID[1]).mean() >= SOLID[0]:
            continue
        found.append((text, left, right, sure))
    return found


def _bow_from(line: np.ndarray, middle: np.ndarray, high: float, through: int | None = None) -> tuple[int, int] | None:
    """The first bow in the columns of a piece of a row (see BOW), from its first column to the column after its last:
    `line` says which columns hold one thin stroke, `middle` its row there. `through`: only a bow that runs through
    this column counts."""
    start = None
    for column, lined in enumerate([*line, False]):
        # One stroke: its middle moves little from a column to the next (a hyphen beside the end of a slur is not).
        goes = lined and (start is None or abs(float(middle[column] - middle[column - 1])) <= BOW[6] * high)
        if start is not None and not goes:
            rows = middle[start:column]
            if column - start >= BOW[0] * high and float(rows.max() - rows.min()) >= BOW[2] * high \
                    and (through is None or start <= through < column):
                return start, column
            start = None
        if lined and start is None:
            start = column
    return None


def _no_bow(words: list[tuple[str, float, float, float]], grey: np.ndarray, band: dict,
            known: dict[str, int]) -> list[tuple[str, float, float, float]]:
    """The words of a row without what was read from a bow (see BOW): a word without the letters that were read from
    a bow behind it, and no hyphen that is a piece of a bow."""
    high = band['bottom'] - band['top']
    wide = [(right - left) / len(text) for text, left, right, sure in words if sure >= BOW[3] and len(text) > 1]
    if high <= 0 or not wide:
        return words
    usual = float(np.median(wide))
    room = int(BOW[5] * high)
    upper, lower = max(0, int(band['top']) - room), min(grey.shape[0], int(band['bottom']) + room + 1)

    def strokes(first: int, last: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """The columns that hold one thin stroke, the row of the ink's middle in each column, the columns with ink."""
        ink = (grey[upper:lower, first:last] < 128).astype(np.int8)
        thick = ink.sum(axis=0)
        count = (np.diff(np.pad(ink, ((1, 0), (0, 0))), axis=0) > 0).sum(axis=0)
        return ((count == 1) & (thick <= BOW[1] * high),
                (ink * np.arange(ink.shape[0])[:, None]).sum(axis=0) / np.maximum(1, thick), thick > 0)

    found = []
    for text, left, right, sure in words:
        first, last = max(0, round(left)), min(grey.shape[1], round(right) + 1)
        if text and all(sign in JOINS for sign in text):
            # A hyphen is short and level. A stroke that goes on past it and rises or falls is a bow. The dash is the
            # bow where its box holds no other ink: a true hyphen that a slur comes close to stands beside the bow.
            begin = max(0, first - int(high))
            line, middle, inked = strokes(begin, min(grey.shape[1], last + int(high)))
            bow = _bow_from(line, middle, high, (first + last) // 2 - begin)
            other = inked[first - begin:last - begin].copy()
            if bow is not None:
                other[max(0, bow[0] - (first - begin)):max(0, bow[1] - (first - begin))] = False
            if bow is None or other.any():
                found.append((text, left, right, sure))
            continue
        found.append((text, left, right, sure))
        places = [at for at, sign in enumerate(text) if sign.isalpha()]
        read = ''.join(text[at] for at in places).lower()
        if len(read) < 2 or sure >= BOW[3] or read in known or last - first < BOW[0] * high:
            continue
        line, middle, _ = strokes(first, last)
        bow = _bow_from(line, middle, high)
        if bow is None or bow[0] < 1 or int((~line[bow[0]:]).sum()) >= usual:
            continue          # (letters stand after the bow too: two words that were read as one)
        cut = bow[0]
        letters = grey[int(band['top']):int(band['bottom']) + 1, first:first + cut] < 128
        if letters.any(axis=1).mean() < BOW[7]:
            continue          # (no letters of the row before the bow: stray ink that was read as a short word)
        count = cut / max(1.0, usual)
        heads = [number for number in range(1, len(read))
                 if abs(number - count) <= BOW[4] and known.get(read[:number], 0) >= MEND[1]
                 and (read[:number] in ('a', 'i', 'o') if number == 1 else not _mute(read[:number]))]
        if len(heads) != 1:
            continue
        found[-1] = (text[:places[heads[0] - 1] + 1], left, float(first + cut), sure)
    return found


def _words_row(words: list[tuple[str, float, float, float]]) -> bool:
    """Whether a line of text is a row of words: how sure Tesseract is of its letters, each letter counted once."""
    if ROW is None:
        return True
    letters = [(sum(sign.isalpha() for sign in text), sure) for text, _, _, sure in words]
    count = sum(number for number, _ in letters)
    return count > 0 and sum(number * sure for number, sure in letters) / count >= ROW


def _text_row(words: list[tuple[str, float, float, float]], grey: np.ndarray, band: dict,
              known: dict[str, int], mend: bool = True, alone: bool = False, mending: bool = True,
              agreed: frozenset[str] | set[str] = frozenset(), alike=None, short=None) -> tuple[list[dict], float, bool]:
    """What one reading of a row gives: its syllables, how well the reading fits, and whether the list of words
    holds each of its words. The fit is the number of letters in words that the list holds, and among readings
    that are level there, or with no list, how sure Tesseract is of the letters. `alone`: the reading is a second
    look at a row that no reading of the picture as it is took for a row of words; it is tested as a row that
    Tesseract is not sure of. The reading of a row of few words (band['few'], words.SPARSE) must hold only words of
    the list."""
    if SOLID:
        words = _no_solid(words, grey, band)
    unsure = alone or not _words_row(words)       # alone: no reading of the picture as it is gave a row of words
    if (unsure or band.get('few')) and not (known and ROW_HELD):
        return [], -1.0, False
    letters = [(sum(sign.isalpha() for sign in text), sure) for text, _, _, sure in words]
    count = sum(number for number, _ in letters)
    sure = sum(number * sure for number, sure in letters) / count if count else 0.0
    stray = False
    if CLEF and band.get('clef') is not None:
        # After the row is judged as a row of words and how sure Tesseract is of it is taken: a stray word that
        # goes must not make its reading look surer than the others (see CLEF).
        keep = [not (word[2] <= band['clef'][1] and word[1] >= band['clef'][0] and word[3] < CLEF[1]
                     and sum(sign.isalpha() for sign in word[0]) >= CLEF[2]) for word in words]
        words = [word for word, stays in zip(words, keep) if stays]
        stray = CLEF_WHOLE and not all(keep)
        letters = [pair for pair, stays in zip(letters, keep) if stays]
    if LONE_I:
        words = _lone_i(words, grey, band)
    if FOUR_A:
        words = _four_a(words, grey, band)
    if BOW and known and mend:
        words = _no_bow(words, grey, band, known)
    if CUT:
        words = _cut_wide(words, grey, band, bool(known) and mend)
    def reading(short) -> tuple[list[dict], float, bool, bool]:
        row = _syllables(words, known, band['bottom'] - band['top'], band.get('carried', '') if MEND_BEFORE else '', short)
        spared = any(syllable.get('spared') for syllable in row)
        for syllable in row:
            syllable['read'] = syllable['text']         # the piece as it was read (see 'cut' in _parted)
        if not known:
            return row, sure, False, spared
        if ENDS:
            row = _ends(row, known, mend, band.get('carried', '') if MEND_BEFORE else '')
        if MEND_REST_STRAY and MEND_BEFORE and mend and band.get('carried'):
            row = _stray_before(row, known, band['carried'])
        mended: list[str] = []
        if MEND and mend and mending:
            if MEND_TWIN:
                row = _mend_twin(row, known, mended)
            if MEND_PAIR:
                row = _mend_pair(row, known, mended, band.get('carried', '') if MEND_BEFORE else '')
            row = _mend(row, known, mended, agreed, alike, band.get('carried', ''))
        held, total = _held(row, known)
        if unsure and (total < ROW_HELD[1] or _held(row, known, ROW_HELD[2])[0] < ROW_HELD[0] * total):
            return [], -1.0, False, spared
        lettered = [text for (text, _, _, _), (number, _) in zip(words, letters) if number]
        if band.get('few') and (mended or not 0 < total == held or (len(lettered) == 1 and lettered[0].endswith(':'))):
            return [], -1.0, False, spared        # a row of few words (words.SPARSE): only words of the list, and no
            #                                       label (one word with a colon: 'Refrain:', 'Women:')
        going = _carried_on(row, known, band.get('carried', ''))
        return row, held + going + total * sure / 5000.0, \
            0 < total == held and not (mended and MEND_WHOLE) and not stray, spared

    row, fit, whole, spared = reading(short)
    if spared:
        # A short word that stays because every reading of the row holds it (SURE_ALIKE) speaks for no reading: how
        # well this reading fits, whether it is whole and whether it is a row at all is asked without that word.
        plain, fit, whole, _ = reading(None)
        if not plain or not row:
            row = plain
    return row, fit, whole


def _sure(words: list[tuple[str, float, float, float]]) -> float:
    """How sure Tesseract is of the letters of a line of text, each letter counted once (of 100)."""
    letters = [(sum(sign.isalpha() for sign in text), sure) for text, _, _, sure in words]
    count = sum(number for number, _ in letters)
    return sum(number * sure for number, sure in letters) / count if count else 0.0


def _stray_first(rows: list[tuple[list[dict], float]]) -> bool:
    """Whether the first of the rows under one staff is stray ink and the next one holds the words (see FIRST).
    Each row: its syllables, and how sure Tesseract is of the row as it is (_sure)."""
    if not FIRST or len(rows) < 2:
        return False
    (first, sure), (second, other) = rows[:2]

    def letters(row: list[dict]) -> bool:
        return any(sign.isalpha() for syllable in row for sign in syllable['text'])

    return letters(second) and (not letters(first) or (sure < FIRST[0] and other >= FIRST[1]))


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


def _held(row: list[dict], known: dict[str, int], least: int = 1) -> tuple[int, int]:
    """How many letters of a row stand in words that the list of words holds (words of `least` letters or more),
    and how many letters the row has."""
    held = total = 0
    now = ''
    for number, syllable in enumerate(row):
        now += ''.join(sign for sign in syllable['text'].lower() if sign.isalpha())
        if not syllable['join'] or number + 1 == len(row):
            total += len(now)
            held += len(now) if now in known and len(now) >= least else 0
            now = ''
    return held, total


def _lacking(row: list[dict], known: dict[str, int]) -> set[str]:
    """The words of a reading that the list of words does not hold, by their letters."""
    words = (''.join(sign for part in word for sign in part['text'].lower() if sign.isalpha()) for word in _read_words(row))
    return {word for word in words if word and word not in known} if known else set()


def _read_words(row: list[dict]) -> list[list[dict]]:
    """The words of a row: the syllables that hyphens join."""
    words: list[list[dict]] = [[]]
    for number, part in enumerate(row):
        words[-1].append(part)
        if not part['join'] and number + 1 < len(row):
            words.append([])
    return [word for word in words if word]


def _other_size(row: list[dict], others: list[list[dict]], known: dict[str, int]) -> list[dict]:
    """A word of the reading that was kept that the list of words does not hold, where the reading at another size
    holds a word of the list at the same place, is that word (see OTHER_SIZE)."""
    share, least = OTHER_SIZE

    def letters(word: list[dict]) -> str:
        return ''.join(sign for part in word for sign in part['text'].lower() if sign.isalpha())

    found: list[dict] = []
    for word in _read_words(row):
        text = letters(word)
        choice = None
        if text and text not in known:
            left, right = word[0]['x0'], word[-1]['x1']
            begins = _begins(known, text) if MEND_HEAD and word[-1]['join'] else 0    # the word goes on in the next row
            for other in others:
                for there in _read_words(other):
                    new = letters(there)
                    first, last = there[0]['x0'], there[-1]['x1']
                    if known.get(new, 0) >= least and len(new) >= 2 and abs(len(new) - len(text)) <= 1 \
                            and text != new + 's' and not 0 < begins >= _begins(known, new) \
                            and min(right, last) - max(left, first) >= share * max(right - left, last - first, 1e-6) \
                            and (choice is None or known[new] > known[letters(choice)]):
                        choice = there
        if choice is not None:
            found.extend(dict(part) for part in choice[:-1])
            found.append(dict(choice[-1], join=word[-1]['join']))
        else:
            found.extend(word)
    return found


def _other_pair(row: list[dict], others: list[list[dict]], known: dict[str, int]) -> list[dict]:
    """A word of the reading that was kept that does not stand with both of its neighbours in the list's text,
    where another reading holds at the same place a word that does, is that word (see PAIR_OTHER)."""
    pairs = getattr(known, 'pairs', None) or frozenset()

    def letters(word: list[dict]) -> str:
        return ''.join(sign for part in word for sign in part['text'].lower() if sign.isalpha())

    words = _read_words(row)
    texts = [letters(word) for word in words]
    for number in range(1, len(words) - 1):
        text, before, after = texts[number], texts[number - 1], texts[number + 1]
        if not text or ((before, text) in pairs and (text, after) in pairs):
            continue
        left, right = words[number][0]['x0'], words[number][-1]['x1']
        meant: dict[str, list[dict]] = {}
        for other in others:
            for there in _read_words(other):
                new = letters(there)
                first, last = there[0]['x0'], there[-1]['x1']
                if new != text and new in known and (before, new) in pairs and (new, after) in pairs \
                        and min(right, last) - max(left, first) >= PAIR_OTHER * max(right - left, last - first, 1e-6):
                    meant[new] = there
        if len(meant) != 1:
            continue
        (new, there), = meant.items()
        words[number] = [dict(part) for part in there[:-1]] + [dict(there[-1], join=words[number][-1]['join'])]
        texts[number] = new
    return [part for word in words for part in word]


def _open(row: list[dict]) -> str:
    """The letters of the word that a row leaves open at its end (its last syllable has a hyphen), or ''."""
    if not row or not row[-1].get('join'):
        return ''
    word = []
    for syllable in reversed(row):
        if word and not syllable.get('join'):
            break
        word.append(syllable['text'])
    return ''.join(sign for text in reversed(word) for sign in text.lower() if sign.isalpha())


def _other_before(row: list[dict], others: list[list[dict]], known: dict[str, int], carried: str) -> list[dict]:
    """The first word of the reading that was kept, where Tesseract is not sure of it and it is not the rest of the
    word that the row before leaves open, is the first word of another reading that is (see MEND_BEFORE), where
    the other readings begin with one such word only. That word can be longer than the first word of the row
    ('rec', 'a', 'tion' and 'rec-tion'): the words of the row in its columns go with the first."""

    def letters(word: list[dict]) -> str:
        return ''.join(sign for part in word for sign in part['text'].lower() if sign.isalpha())

    words = _read_words(row)
    if not words or carried + letters(words[0]) in known or min(part.get('sure', 0.0) for part in words[0]) >= MEND[2]:
        return row
    left, right = words[0][0]['x0'], words[0][-1]['x1']
    meant: dict[str, list[dict]] = {}
    for other in others:
        there = _read_words(other)
        if there and len(letters(there[0])) >= MEND_BEFORE and carried + letters(there[0]) in known \
                and min(right, there[0][-1]['x1']) > max(left, there[0][0]['x0']):
            meant[letters(there[0])] = there[0]
    if len(meant) != 1:
        return row
    (_, there), = meant.items()
    # The words of the row that lie in the columns of that word are pieces of it.
    after = [word for word in words[1:] if (word[0]['x0'] + word[-1]['x1']) / 2 > there[-1]['x1']]
    return [dict(part) for part in there[:-1]] + [dict(there[-1], join=words[0][-1]['join'] if len(after) == len(words) - 1 else there[-1]['join'])] \
        + [part for word in after for part in word]


def _pick(read, grey: np.ndarray, band: dict, known: dict[str, int], mend: bool = True,
          ways: dict[str, tuple[str, ...]] | None = None, more: tuple[int, ...] = ()) -> list[dict]:
    """The syllables of a row from the reading that fits best. `read(size)` gives Tesseract's words at one size.
    With `ways` the words are parted into syllables as the list of words parts them. `more` are the sizes of a
    second look, read after the others where no reading is whole (a size under 0: the picture without the ink that
    crosses the row, see CROSS and CROSS_LIST; a size from SECOND on: the second language file, see SECOND)."""
    best: tuple[list[dict], float] | None = None
    rows: list[list[dict]] = []
    firsts: set[str] = set()       # the words that the list lacks, as the first file read them
    firm: set[str] | None = None   # those of them that every size of the first file read alike
    same: list[set[str]] = []

    def alike() -> set[str]:
        # The words that every reading of the row holds with the same letters (see MEND_ALIKE), read when first asked.
        if not same:
            sizes = (HIGH,) + tuple(AGAIN or ()) + (tuple(size for size in more if size > 0) if MEND_ALIKE > 1 else ())
            bare = (lambda words: _no_bow(words, grey, band, known)) if BOW and known and mend else (lambda words: words)
            same.append(set.intersection(*(
                {''.join(sign for part in word for sign in part['text'].lower() if sign.isalpha())
                 for word in _read_words(_syllables(bare(read(size)), known, band['bottom'] - band['top']))} for size in sizes)))
        return same[0]

    def short(text: str, left: float, right: float) -> bool:
        # A short word that every reading of the row holds with the same letters in its columns (see SURE_ALIKE).
        sizes = (HIGH,) + tuple(AGAIN or ()) + tuple(size for size in more if size > 0)
        if not (SECOND and any(size >= SECOND for size in sizes)):
            return False
        letters = ''.join(sign for sign in text.lower() if sign.isalpha())
        return all(any(''.join(sign for sign in other.lower() if sign.isalpha()) == letters
                       and min(right, last) - max(left, first) > 0.5 * min(right - left, last - first)
                       for other, first, last, _ in read(size)) for size in sizes)

    for size in (HIGH,) + tuple(AGAIN or ()) + tuple(more):
        again = size < 0 or bool(SECOND and size >= SECOND)      # a second look: another picture or another file
        second = again and size > 0
        row, fit, whole = _text_row(read(size), grey, band, known, mend, again and (best is None or best[1] < 0),
                                    mending=bool(SECOND_MEND) or not second, agreed=firsts if second else frozenset(),
                                    alike=alike if MEND_ALIKE and known else None,
                                    short=short if SURE_ALIKE and known and (SURE_ALIKE > 1 or not second) else None)
        lacking = _lacking(row, known)
        if not again:
            firsts |= lacking
            firm = lacking if firm is None else firm & lacking
        rows.append(row)
        if (again and CROSS_LIST and not mend and best is not None and best[1] >= 0
                and not (known and _held(row, known)[0] > _held(best[0], known)[0])):
            continue
        if second and SECOND_MORE and best is not None and best[1] >= 0:
            (held, total), (old, before) = _held(row, known, SECOND_MORE), _held(best[0], known, SECOND_MORE)
            if not (total - held < before - old and held >= old):
                continue
            if SECOND_FIRM and firm and firm - lacking and total < before:
                continue
        if best is None or fit > best[1]:
            best = (row, fit)
        if whole and not again and known and mend and _unread(read(size), grey, band):
            whole = False        # a letter of the row stands in no word of this reading: the other sizes are read
        if whole:
            break
    row = best[0] if best else []
    if MEND_BEFORE and known and mend and band.get('carried') and len(rows) > 1:
        row = _other_before(row, [other for other in rows if other is not row], known, band['carried'])
    if OTHER_SIZE and known and mend and len(rows) > 1:
        row = _other_size(row, [other for other in rows if other is not row], known)
    if PAIR_OTHER and known and mend and len(rows) > 1 and getattr(known, 'pairs', None):
        row = _other_pair(row, [other for other in rows if other is not row], known)
    if PAIR and known and mend and getattr(known, 'pairs', None):
        row = _between(row, known)
    if SMALL_I and known and mend:
        # After the reading is chosen: a stray word that goes must not change which reading is kept (see CLEF).
        row = [syllable for number, syllable in enumerate(row)
               if syllable['join'] or (number and row[number - 1]['join']) or syllable['text'].strip(STOPS + '\'"‘’“”') != 'i']
    if ONE and ways and mend:
        row = _whole(row, known, ways)
    return _parted(row, ways) if ways else row


def read_rows(layers: dict, page: int = 0, lex=None, before: dict | None = None) -> list[dict]:
    """The syllables of the rows of words of a page, read with Tesseract: {'band': (page, the number of the row),
    'text', 'x0', 'x1', 'join'} each, as scorereader.lyrics.read_words() gives them. With a list of words (`lex`:
    {word: how often}) the words that the list does not hold are mended with it, the list sets where a word ends,
    it chooses between the readings of a row at several sizes, and a list that shows how its words are parted
    (`lex.parts`) parts the words into syllables where the scan shows no hyphen.

    `before` holds the words that the page before left open, for each part (MEND_PAGE): the caller hands the same
    dict to each page of a hymn in turn, and the page leaves its own open words in it for the next one."""
    bands = layers.get('words') or []
    if not bands or not available():
        return []
    grey, space = layers['grey'], layers['space']
    height, width = grey.shape
    known = _known(lex)
    ways = _ways(lex, known)
    others = second_files()
    found = []
    with tempfile.TemporaryDirectory() as folder:
        readers = []
        for number, band in enumerate(bands):
            top, bottom = max(0, int(band['top'] - ROOM[0] * space)), min(height, int(band['bottom'] + ROOM[0] * space) + 1)
            first, last = max(0, int(band['x0'] - ROOM[1] * space)), min(width, int(band['x1'] + ROOM[1] * space) + 1)
            part = grey[top:bottom, first:last]
            if HELD:
                part = _no_held(part, band['top'] - top, band['bottom'] - top)
            bare = None
            if CROSS:
                over = max(0, int(band['top'] - CROSS[0] * space))
                under = min(height, int(band['bottom'] + CROSS[0] * space) + 1)
                bare = _no_cross(part, grey[over:under, first:last], top - over, band['top'] - top, band['bottom'] - top, space)
                if bare is part:
                    bare = None
            seen: dict[int, list] = {}

            def read(size: int, part=part, bare=bare, first=first, band=band, number=number, seen=seen) -> list[tuple[str, float, float, float]]:
                if size not in seen:                   # a size under 0: the picture without the ink that crosses the row
                    files = None
                    if SECOND and size >= SECOND:      # a size from SECOND on: the picture as it is, a further file
                        picture, tall, files = part, size % SECOND, others[size // SECOND - 1]
                    else:
                        picture, tall = (part, size) if size > 0 else (bare, -size)
                    scale = tall / max(1.0, band['bottom'] - band['top'])
                    crop = cv2.resize(picture, None, fx=scale, fy=scale,
                                      interpolation=cv2.INTER_CUBIC if scale > 1 else cv2.INTER_AREA)
                    edge = tall // 2
                    crop = cv2.copyMakeBorder(crop, edge, edge, edge, edge, cv2.BORDER_CONSTANT, value=255)
                    seen[size] = [(text, first + (left - edge) / scale, first + (right - edge) / scale, sure)
                                  for text, left, right, sure in _line(crop, folder, f'{page}_{number}_{size}', files)]
                return seen[size]

            readers.append((read, (() if bare is None else tuple(-size for size in (HIGH,) + tuple(AGAIN or ())))
                            + (tuple(SECOND * (file + 1) + size for file in range(len(others))
                                     for size in (HIGH,) + tuple(AGAIN or ())) if known else ())))
        if CLEF:
            # Each row knows the columns of the clef of the staff over it (see CLEF).
            staves = layers.get('staves') or []
            marked = []
            for band in bands:
                over = [staff for staff in staves if staff['rows'][4] < band['top']]
                left = max(over, key=lambda staff: staff['rows'][4])['x0'] if over else None
                marked.append(band if left is None else dict(band, clef=(left - CLEF[3] * space, left + CLEF[0] * space)))
            bands = marked
        mend = bool(known) and _fits([(read(HIGH), band) for (read, _), band in zip(readers, bands)], grey, known)
        under: dict[int, list[tuple[list[dict], float]]] = {}
        # The first row under a staff of each part: the word that its last hyphen leaves open.
        opened: dict = before if MEND_PAGE and before is not None else {}
        for number, ((read, more), band) in enumerate(zip(readers, bands)):
            # The rows under one staff, from the top (as scorereader.lyrics.set_under() gives a row to the staff over it).
            over = [index for index, staff in enumerate(layers.get('staves') or []) if staff['rows'][4] < band['top']]
            above = max(over, key=lambda index: layers['staves'][index]['rows'][4]) if over else None
            leads = above is not None and band.get('with') is None and above not in under
            voice = layers['staves'][above].get('number') if leads else None
            if MEND_BEFORE and leads and opened.get(voice):
                band = dict(band, carried=opened[voice])
            row = [dict(syllable, band=(page, number)) for syllable in _pick(read, grey, band, known, mend, ways, more)]
            if leads:
                opened[voice] = _open(row)
            if row and above is not None and band.get('with') is None:
                under.setdefault(above, []).append((row, _sure(read(HIGH))))
            found.append(row)
        for rows in under.values():
            if _stray_first(rows):
                rows[0][0].clear()
    return [syllable for row in found for syllable in row]
