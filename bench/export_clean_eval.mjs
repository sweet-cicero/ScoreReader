#!/usr/bin/env node
// Exports truth JSON files (with explicit rest intervals) and creates a strict, group-stratified
// Dev / Locked-Holdout split for clean PDF scans outside git (in out/eval/).
//
// Usage:
//   node --experimental-strip-types bench/export_clean_eval.mjs \
//     --litchoir "$HOME/Projects/LitChoir" \
//     --clean-json "$HOME/Projects/LitChoir/tmp/omr-test/survey-2026-11-24/clean-pages.json" \
//     --out out/eval
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {existsSync, mkdirSync, readFileSync, writeFileSync} from 'node:fs';
import {createRequire} from 'node:module';
import {join, resolve} from 'node:path';

const args = process.argv.slice(2);
const flag = (name, fallback = null) => {
  const idx = args.indexOf(name);
  return idx >= 0 && idx + 1 < args.length ? args[idx + 1] : fallback;
};

const litchoir = resolve(flag('--litchoir', join(process.env.HOME, 'Projects/LitChoir')));
const cleanJson = resolve(flag('--clean-json', join(litchoir, 'tmp/omr-test/survey-2026-11-24/clean-pages.json')));
const kitCasesPath = resolve(flag('--kit-cases', join(litchoir, 'tmp/omr-test/cases.json')));
const outDir = resolve(flag('--out', 'out/eval'));

const {hymns, sourcePath} = await import(join(litchoir, 'app/src/catalog.ts'));
const {abcText, scoreParts, wordsOf} = await import(join(litchoir, 'app/src/notes.ts'));
const abcjs = createRequire(join(litchoir, 'app/package.json'))('abcjs');

const round = (v) => Math.round(v * 1e6) / 1e6;

function voicesOf(tune) {
  const voices = [];
  for (const [line, music] of tune.lines.entries()) {
    let voice = 0;
    for (const staff of music.staff ?? []) {
      for (const elements of staff.voices ?? []) {
        voices[voice] ??= [];
        for (const element of elements) voices[voice].push({line, element});
        voice++;
      }
    }
  }
  return voices;
}

function parseStaves(stavesSpec, parts) {
  if (!stavesSpec) return [parts];
  const groups = [];
  let current = null;
  for (const tok of stavesSpec.replaceAll('(', ' ( ').replaceAll(')', ' ) ').trim().split(/\s+/)) {
    if (!tok) continue;
    if (tok === '(') {
      current = [];
    } else if (tok === ')') {
      if (current && current.length) groups.push(current);
      current = null;
    } else if (parts.includes(tok)) {
      if (current !== null) current.push(tok);
      else groups.push([tok]);
    }
  }
  return groups.length ? groups : [parts];
}

function writtenNotesAndRests(tune, parts) {
  const tracks = tune.setUpAudio({}).tracks;
  const voices = voicesOf(tune);
  const outNotes = {};
  const outRests = {};
  for (const [index, part] of parts.entries()) {
    const sounds = new Map();
    for (const sound of tracks[index] ?? []) {
      if (sound.cmd === 'note') {
        const list = sounds.get(sound.startChar) ?? [];
        list.push(sound);
        sounds.set(sound.startChar, list);
      }
    }
    const notes = [];
    const rests = [];
    let position = 0;
    let tuplet = 1;
    for (const {line, element} of voices[index] ?? []) {
      if (element.el_type === 'bar') {
        position = round(position);
        continue;
      }
      if (element.el_type !== 'note' || element.duration === undefined) continue;
      if (element.startTriplet) tuplet = element.tripletMultiplier ?? 1;
      const beats = element.duration * 4 * tuplet;
      if (element.endTriplet) tuplet = 1;
      if (element.rest) {
        rests.push({at: round(position), len: round(beats), line});
        position += beats;
        continue;
      }
      const heard = sounds.get(element.startChar);
      if (heard?.length) {
        const lyric = element.lyric?.[0];
        const syllable = lyric?.syllable?.trim();
        notes.push({
          at: round(position),
          len: round(beats),
          midi: [...new Set(heard.map((s) => s.pitch))].sort((a, b) => b - a),
          ...(syllable ? {syl: syllable, div: lyric.divider} : {}),
          line,
        });
      } else if (element.pitches?.some((p) => p.endTie) && notes.length) {
        notes.at(-1).len = round(notes.at(-1).len + beats);
      }
      position += beats;
    }
    outNotes[part] = notes;
    outRests[part] = rests;
  }
  return {parts: outNotes, rests: outRests};
}

const clean = JSON.parse(readFileSync(cleanJson, 'utf8'));
const kitCases = existsSync(kitCasesPath) ? JSON.parse(readFileSync(kitCasesPath, 'utf8')).cases : [];
const kitLayoutById = new Map(kitCases.map((c) => [c.id, c.layout]));
const kitBaseIds = new Set(kitCases.map((c) => c.id.split('--')[0]));
const hymnById = new Map(hymns.map((h) => [h.id, h]));

const truthDir = join(outDir, 'truth');
mkdirSync(truthDir, {recursive: true});

const allCases = [];
for (const id of clean.counted) {
  const [base, suf] = id.split('--');
  const hymn = hymnById.get(base);
  if (!hymn?.music) throw new Error(`Missing hymn music for ${id}`);
  const sIdx = suf ? parseInt(suf.slice(1), 10) - 1 : 0;
  const score = hymn.scores[sIdx];
  const rel = sourcePath(hymn, score.file);
  const pdfInChoir = join(litchoir, 'CHOIR', rel);
  const pdfPath = existsSync(pdfInChoir) ? pdfInChoir : join(litchoir, score.file);
  if (!existsSync(pdfPath)) throw new Error(`Missing PDF for ${id}: ${pdfPath}`);

  const info = execFileSync('pdfinfo', [pdfPath], {encoding: 'utf8'});
  const pageCount = parseInt(info.match(/Pages:\s+(\d+)/)?.[1] ?? '1', 10);
  const pages = score.pages ?? Array.from({length: pageCount}, (_, i) => i + 1);
  const parts = scoreParts(hymn.music);
  const layout = kitLayoutById.get(id) ?? parseStaves(hymn.music.staves, parts);

  const tune = abcjs.parseOnly(abcText(hymn.music, parts))[0];
  const {parts: partNotes, rests: partRests} = writtenNotesAndRests(tune, parts);
  const words = wordsOf(hymn.music, layout[0][0]);

  const truth = {
    id,
    base_id: base,
    name: hymn.name,
    kind: 'clean',
    pdf: pdfPath,
    pages,
    layout,
    key: hymn.music.key,
    meter: hymn.music.meter ?? 'none',
    clefs: Object.fromEntries(parts.map((p) => [p, hymn.music.clefs?.[p] ?? 'treble'])),
    words,
    parts: partNotes,
    rests: partRests,
  };
  writeFileSync(join(truthDir, `${id}.json`), JSON.stringify(truth) + '\n', 'utf8');

  const noteCount = Object.values(partNotes).reduce((sum, list) => sum + list.reduce((s, n) => s + n.midi.length, 0), 0);
  const restCount = Object.values(partRests).reduce((sum, list) => sum + list.length, 0);
  allCases.push({
    id,
    base_id: base,
    kind: 'clean',
    pdf: pdfPath,
    pages,
    layout,
    meter: truth.meter,
    note_count: noteCount,
    rest_count: restCount,
    in_kit: kitBaseIds.has(base),
  });
}

// Group by base_id so alternate scans (--s2, --s3) stay in the same split.
// Put all kit hymns into Dev so the Locked Holdout contains zero kit hymns.
const byBase = new Map();
for (const c of allCases) {
  const list = byBase.get(c.base_id) ?? [];
  list.push(c);
  byBase.set(c.base_id, list);
}

const forcedDev = [];
const eligible = [];
for (const [base, group] of byBase.entries()) {
  if (group.some((c) => c.in_kit)) forcedDev.push(...group);
  else eligible.push({base, group, hash: createHash('sha256').update(`scoreread-v1:${base}`).digest('hex')});
}

// Deterministic hash order, filling Locked Holdout to 26 scores without splitting any base_id group.
eligible.sort((a, b) => a.hash.localeCompare(b.hash));
const holdout = [];
const dev = [...forcedDev];
const TARGET_HOLDOUT = 26;
for (const item of eligible) {
  if (holdout.length + item.group.length <= TARGET_HOLDOUT) holdout.push(...item.group);
  else dev.push(...item.group);
}
dev.sort((a, b) => a.id.localeCompare(b.id));
holdout.sort((a, b) => a.id.localeCompare(b.id));

const writeManifest = (name, cases) => {
  const payload = {
    about: `Clean PDF scan split (${name}). Generated outside git; do not commit scans or truth files.`,
    split: name,
    truth_dir: truthDir,
    count: cases.length,
    pages: cases.reduce((s, c) => s + c.pages.length, 0),
    notes: cases.reduce((s, c) => s + c.note_count, 0),
    rests: cases.reduce((s, c) => s + c.rest_count, 0),
    cases,
  };
  writeFileSync(join(outDir, `${name}.json`), JSON.stringify(payload, null, 2) + '\n', 'utf8');
  return payload;
};

const devM = writeManifest('clean_dev', dev);
const holdM = writeManifest('clean_holdout', holdout);
writeManifest('clean_all', allCases.sort((a, b) => a.id.localeCompare(b.id)));

console.log(`Exported ${allCases.length} clean truth files to ${truthDir}`);
console.log(`  clean_dev     : ${devM.count} scores, ${devM.pages} pages, ${devM.notes} notes, ${devM.rests} rests`);
console.log(`  clean_holdout : ${holdM.count} scores, ${holdM.pages} pages, ${holdM.notes} notes, ${holdM.rests} rests (LOCKED)`);
