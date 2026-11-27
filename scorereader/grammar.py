"""Global music-grammar duration solver and calibrated note confidence estimator.

Combines three sources of musical evidence inside each bar of a system:
  1. Per-note visual log-likelihoods from SymNet (filled, hollow, whole, breve)
     and StemNet (0, 1, or 2 tails) combined with local stem, flag, beam, and dot evidence.
  2. Cross-voice vertical column synchronization across all staves of a system
     (active for both metered scores and unmeasured chant).
  3. Exact bar-duration balance against the active time signature, including bars
     with high-confidence shared rests, without forcing pickup bars or unmeasured chant.

Runs in less than 1 ms per bar via bounded beam search (pure Python and Fractions).
"""
from __future__ import annotations

import math
from fractions import Fraction

from .music import ACROSS, TYPES

STEP_CANDIDATES = (
    Fraction(1, 4),
    Fraction(1, 2),
    Fraction(3, 4),
    Fraction(1),
    Fraction(3, 2),
    Fraction(2),
    Fraction(3),
    Fraction(4),
    Fraction(6),
    Fraction(8),
)

_HEAD_KIND = {
    Fraction(1, 8): 'filled',
    Fraction(1, 4): 'filled',
    Fraction(3, 8): 'filled',
    Fraction(1, 2): 'filled',
    Fraction(3, 4): 'filled',
    Fraction(1): 'filled',
    Fraction(3, 2): 'filled',
    Fraction(7, 4): 'filled',
    Fraction(2): 'hollow',
    Fraction(3): 'hollow',
    Fraction(7, 2): 'hollow',
    Fraction(4): 'whole',
    Fraction(6): 'whole',
    Fraction(8): 'breve',
    Fraction(12): 'breve',
}

_KIND_INDEX = {'filled': 0, 'hollow': 1, 'whole': 2, 'breve': 3}


def _safe_log(p: float, floor: float = 1e-4) -> float:
    return math.log(max(floor, min(1.0, float(p))))


def _base_duration(dur: Fraction) -> Fraction:
    if dur in (Fraction(3, 8), Fraction(3, 4), Fraction(3, 2), Fraction(3), Fraction(6), Fraction(12)):
        return dur * Fraction(2, 3)
    if dur in (Fraction(7, 4), Fraction(7, 2)):
        return dur * Fraction(4, 7)
    return dur


def _event_stem(event: dict) -> dict | None:
    head = event.get('head') or {}
    direction = 'up' if event.get('voice') == 1 else 'down'
    return next((s for s in head.get('stems', []) if s['direction'] == direction), None)


def _unwitnessed_beam(stem: dict | None) -> bool:
    if stem is None:
        return False
    return any(m.get('beam') and not m.get('witness') for m in stem.get('marks', []))


def event_log_likelihood(event: dict, dur: Fraction) -> float:
    """Computes calibrated log-likelihood log P(dur | ink, symnet, stemnet) for one note event."""
    want_kind = _HEAD_KIND.get(dur)
    if want_kind is None:
        # Reject non-representable composite durations (for example 5/2) so beam search cannot exploit them.
        return -8.5

    d0 = event['length']
    head = event.get('head') or {}
    sym = head.get('symnet')
    has_stem = event.get('stem_x') is not None
    hollow = bool(head.get('hollow'))
    hole = float(head.get('hole', 0.0) or 0.0)
    dot = bool(head.get('dot'))
    dot_near = bool(head.get('dot_near'))
    dot_sure = bool(head.get('dot_sure'))
    has_flag_ink = bool(head.get('flag_ink'))
    direction = 'up' if event.get('voice') == 1 else 'down'
    cur_tails = int((head.get('tails') or {}).get(direction, 0))

    # A note with a detected beam or flag cannot be a hollow, whole, or breve head.
    if want_kind != 'filled' and cur_tails > 0:
        return -8.5

    score = 0.0
    if sym is not None:
        p_fill, p_holl, p_whole, p_breve = float(sym[0]), float(sym[1]), float(sym[2]), float(sym[3])
        p_head_tot = max(1e-4, p_fill + p_holl + p_whole + p_breve)
        kind_prob = {
            'filled': p_fill / p_head_tot,
            'hollow': p_holl / p_head_tot,
            'whole': p_whole / p_head_tot,
            'breve': p_breve / p_head_tot,
        }[want_kind]
        score += 1.15 * _safe_log(kind_prob, 2e-3)

    # Protect clear hollow heads with large interior holes from casual conversion to filled heads.
    if want_kind == 'filled' and hollow and hole >= 0.22 and not has_flag_ink and cur_tails == 0:
        score -= 1.5

    stem_probs = event.get('stemnet')
    if stem_probs is not None and want_kind == 'filled' and has_stem:
        base_d = _base_duration(dur)
        if base_d == Fraction(1):
            t_idx = 0
        elif base_d == Fraction(1, 2):
            t_idx = 1
        elif base_d == Fraction(1, 4):
            t_idx = 2
        else:
            t_idx = None
        if t_idx is not None:
            stem_ref = _event_stem(event)
            weight = 0.25 if (t_idx == 1 and cur_tails == 0 and _unwitnessed_beam(stem_ref)) else 1.0
            score += weight * _safe_log(float(stem_probs[t_idx]), 5e-3)

    if dur == d0:
        return score

    # 1. Exact dotted / undotted toggle (d0 <-> 1.5 * d0).
    if dur == d0 * Fraction(3, 2):
        # Never invent a dot without nearby dot ink solely to satisfy bar balance.
        score -= 1.0 if dot_near else 3.4
        return score
    if d0 == dur * Fraction(3, 2):
        score -= 3.4 if dot_sure else (1.5 if dot else 2.6)
        return score

    # 2. Filled <-> Hollow head flip (same dot state).
    if (d0 == Fraction(1) and dur == Fraction(2)) or (d0 == Fraction(2) and dur == Fraction(1)) or \
       (d0 == Fraction(3, 2) and dur == Fraction(3)) or (d0 == Fraction(3) and dur == Fraction(3, 2)):
        if sym is not None:
            score -= 0.85
            if dur > d0 and hole <= 0.0 and not head.get('slit'):
                score -= 0.75
        else:
            score -= 2.4
        return score

    # 3. Eighth <-> Quarter (missed flag or beam, or slur misread as beam).
    if (d0 == Fraction(1) and dur == Fraction(1, 2)) or (d0 == Fraction(1, 2) and dur == Fraction(1)):
        if hollow:
            score -= 4.5
        elif d0 == Fraction(1) and dur == Fraction(1, 2) and has_flag_ink:
            score -= 0.8
        else:
            score -= 1.65
        return score

    # 4. Sixteenth <-> Eighth.
    if (d0 == Fraction(1, 2) and dur == Fraction(1, 4)) or (d0 == Fraction(1, 4) and dur == Fraction(1, 2)):
        score -= 4.5 if hollow else 1.7
        return score

    # 5. Dotted eighth <-> Quarter or Eighth.
    if (d0 in (Fraction(1), Fraction(1, 2)) and dur == Fraction(3, 4)) or \
       (d0 == Fraction(3, 4) and dur in (Fraction(1), Fraction(1, 2))):
        score -= 2.5
        return score

    # 6. Whole <-> Half.
    if (d0 == Fraction(4) and dur == Fraction(2)) or (d0 == Fraction(2) and dur == Fraction(4)):
        score -= 1.3 if (sym is not None or not has_stem) else 2.5
        return score

    # 7. Whole <-> Dotted half.
    if (d0 == Fraction(4) and dur == Fraction(3)) or (d0 == Fraction(3) and dur == Fraction(4)):
        score -= 2.0
        return score

    # 8. Hollow mistaken for eighth (burnt-out filled eighth head with flag ink).
    if d0 == Fraction(2) and dur == Fraction(1, 2) and has_flag_ink:
        score -= 1.2
        return score

    return score - 6.5


def _system_edges(plans: dict[int, list[list[list[dict]]]], bars: dict[int, list[float]], space: float) -> list[float]:
    """Clusters barline x-coordinates across all staves of one system."""
    xs = sorted(x for index in plans for x in bars.get(index, []))
    groups: list[list[float]] = []
    for x in xs:
        if groups and x - groups[-1][-1] <= space:
            groups[-1].append(x)
        else:
            groups.append([x])
    return [sum(g) / len(g) for g in groups]


def _classify_bar_rests(bar_rests: list[dict], clusters: list[dict], staff_ids: set[int],
                        space: float) -> tuple[Fraction, bool]:
    """Returns (shared_rest_len, rests_all_shared) for rests inside one system bar.

    A bar counts as having high-confidence shared rests only when every rest in the bar
    stands clear of all note columns, is not a silent-voice whole-bar rest, and covers
    all active voices across the system at matching horizontal columns.
    """
    if not bar_rests:
        return Fraction(0), False

    groups: list[list[dict]] = []
    for r in sorted(bar_rests, key=lambda item: item['x']):
        if groups and abs(r['x'] - groups[-1][0]['x']) <= 1.2 * space:
            groups[-1].append(r)
        else:
            groups.append([r])

    shared_len = Fraction(0)
    all_shared = True
    n_staves = len(staff_ids)
    for grp in groups:
        gx = sum(r['x'] for r in grp) / len(grp)
        overlaps_any = any(abs(cl['x'] - gx) <= 0.85 * space for cl in clusters)
        if overlaps_any:
            all_shared = False
            continue
        if any(r.get('kind') == 'block' and r.get('hangs') and not r.get('sits') for r in grp):
            all_shared = False
            continue
        by_staff: dict[int, list[dict]] = {}
        for r in grp:
            by_staff.setdefault(r['staff'], []).append(r)

        valid_staff_lens: list[Fraction] = []
        staff_ok = True
        for s_rests in by_staff.values():
            # Require high-confidence rests (printed quarter/block or verified neural/short rest).
            if any(r.get('kind') in ('eighth', '16th') and r.get('neural') and float(r.get('prob', 0.0)) < 0.85 for r in s_rests):
                staff_ok = False
                break
            mids = [float(r.get('middle', 0.0)) for r in s_rests]
            centered = len(s_rests) == 1 and abs(mids[0]) < 0.75
            stacked_pair = len(s_rests) >= 2 and min(mids) <= -0.75 and max(mids) >= 0.75
            if not (centered or stacked_pair):
                staff_ok = False
                break
            lens = {Fraction(r.get('length', 1)) for r in s_rests}
            if len(lens) != 1:
                staff_ok = False
                break
            valid_staff_lens.append(next(iter(lens)))

        need_staves = min(2, n_staves) if n_staves >= 2 else 1
        if staff_ok and len(valid_staff_lens) >= need_staves and len(set(valid_staff_lens)) == 1:
            shared_len += valid_staff_lens[0]
        else:
            all_shared = False

    if not all_shared:
        return Fraction(0), False
    return shared_len, True


def _bar_clusters(plans: dict[int, list[list[list[dict]]]], bars: dict[int, list[float]],
                  space: float, rests: list[dict] | None) -> tuple[list[dict], list[float]]:
    """Groups system columns by measure and horizontal alignment across staves."""
    edges = _system_edges(plans, bars, space)
    staff_ids = set(plans)
    # Filter page rests strictly to the staves of this system.
    sys_rests = [r for r in (rests or []) if r.get('staff') in staff_ids]

    cells: dict[int, list[tuple[float, int, list[dict]]]] = {}
    for index, measures in plans.items():
        for measure in measures:
            for column in measure:
                cx = sorted(ev['x'] for ev in column)[len(column) // 2]
                m_idx = sum(1 for edge in edges if edge < cx)
                cells.setdefault(m_idx, []).append((cx, index, column))

    out = []
    for m_idx in sorted(cells):
        group = sorted(cells[m_idx], key=lambda item: item[0])
        clusters: list[dict] = []
        for x, index, column in group:
            best = None
            for cl in clusters[-2:]:
                if all(other[1] != index for other in cl['cells']) and abs(cl['x'] - x) <= ACROSS * space:
                    if best is None or abs(cl['x'] - x) < abs(best['x'] - x):
                        best = cl
            if best is None:
                clusters.append({'x': x, 'cells': [(x, index, column)]})
            else:
                best['cells'].append((x, index, column))
                best['x'] = sum(c[0] for c in best['cells']) / len(best['cells'])

        bar_rests = [r for r in sys_rests if sum(1 for edge in edges if edge < r['x']) == m_idx]
        shared_rest_len, rests_all_shared = _classify_bar_rests(bar_rests, clusters, staff_ids, space)
        out.append({
            'bar': m_idx,
            'clusters': clusters,
            'rests': bar_rests,
            'shared_rest': shared_rest_len,
            'rests_all_shared': rests_all_shared,
        })
    return out, edges


def solve_system_durations(plans: dict[int, list[list[list[dict]]]], bars: dict[int, list[float]],
                           space: float, rests: list[dict] | None = None,
                           meter: tuple[int, int, str | None] | None = None,
                           is_first_system: bool = False,
                           meter_changes: dict[int, list[tuple[float, tuple[int, int, str | None]]]] | None = None) -> int:
    """Globally refines note durations inside each bar of a system using calibrated probabilities.

    Overrides durations only when joint cross-voice, neural, and optional meter-balance evidence
    strictly improves the bar objective by a clear safety margin without contradicting strong local ink.
    Returns the number of updated events.
    """
    bar_items, edges = _bar_clusters(plans, bars, space, rests)
    change_by_bar: dict[int, tuple[int, int, str | None]] = {}
    if meter_changes:
        for s_idx, changes in meter_changes.items():
            if s_idx not in plans:
                continue
            for cx, new_m in changes:
                bm = sum(1 for edge in edges if edge < cx)
                change_by_bar[bm] = new_m

    cur_meter = meter
    prev_bar = -1
    changed = 0

    for item_idx, item in enumerate(bar_items):
        m_idx = item['bar']
        for bm in sorted(k for k in change_by_bar if prev_bar < k <= m_idx):
            cur_meter = change_by_bar[bm]
        prev_bar = m_idx
        bar_target = Fraction(cur_meter[0] * 4, cur_meter[1]) if cur_meter is not None else None

        clusters = item['clusters']
        n_steps = len(clusters)
        if n_steps == 0:
            continue
        bar_rests = item['rests']
        shared_rest = item['shared_rest']

        # Skip bars containing triplets (handled explicitly by triplets.py).
        if any(ev['length'].denominator % 3 == 0 for cl in clusters for _, _, col in cl['cells'] for ev in col):
            continue

        # Detect staves that have only one voice per column in this bar so stem-direction
        # flips do not create false multi-column spans.
        mono_staves = set()
        staff_cols: dict[int, list[int]] = {}
        for cl in clusters:
            for _, staff_idx, column in cl['cells']:
                staff_cols.setdefault(staff_idx, []).append(len({ev['voice'] for ev in column}))
        for staff_idx, vcounts in staff_cols.items():
            if all(vc == 1 for vc in vcounts):
                mono_staves.add(staff_idx)

        where: dict[tuple[int, int], list[tuple[int, list[dict]]]] = {}
        for s_idx, cl in enumerate(clusters):
            for _, staff_idx, column in cl['cells']:
                if staff_idx in mono_staves:
                    where.setdefault((staff_idx, 0), []).append((s_idx, list(column)))
                else:
                    for voice in sorted({ev['voice'] for ev in column}):
                        evs = [ev for ev in column if ev['voice'] == voice]
                        where.setdefault((staff_idx, voice), []).append((s_idx, evs))

        step_groups: list[list[list[dict]]] = [[] for _ in range(n_steps)]
        long_spans: list[tuple[int, int, list[dict]]] = []

        for (staff_idx, _voice), seq in where.items():
            for (s0, evs), (s1, after) in zip(seq, seq[1:] + [(n_steps, None)]):
                x0 = max(ev['x'] for ev in evs)
                x1 = min(ev['x'] for ev in after) if after else float('inf')
                has_pause = any(
                    r['staff'] == staff_idx and x0 + 0.3 * space < r['x'] < x1 - 0.3 * space
                    for r in bar_rests
                )
                if s1 == s0 + 1 and not has_pause:
                    step_groups[s0].append(evs)
                elif s1 > s0 + 1 and not has_pause and after is not None:
                    # Only track spans with a definite following note in the bar.
                    long_spans.append((s0, s1, evs))

        # For very long barless chant lines (> 24 columns), run local per-column cross-voice
        # neural resolution without meter balance so unmeasured chant is never forced.
        if n_steps > 24:
            if bar_target is not None:
                continue
            for s in range(n_steps):
                groups_s = step_groups[s]
                if len(groups_s) < 2:
                    continue
                voice_lens = [min(ev['length'] for ev in grp) for grp in groups_s]
                obs = sorted(set(voice_lens))
                pool = set(obs)
                if len(obs) == 1:
                    d0 = obs[0]
                    for cand in STEP_CANDIDATES:
                        if cand in (d0 * 2, d0 / 2):
                            pool.add(cand)
                sc = {
                    cand: sum(sum(event_log_likelihood(ev, cand) for ev in grp) / len(grp) for grp in groups_s)
                    for cand in pool
                }
                indep = sum(sum(event_log_likelihood(ev, ev['length']) for ev in grp) / len(grp) for grp in groups_s)
                best_cand = max(sc, key=sc.get)
                if not (best_cand in TYPES or best_cand / Fraction(3, 2) in TYPES):
                    continue
                if sc[best_cand] >= indep + 1.6:
                    step_all_evs = [ev for grp in groups_s for ev in grp]
                    existing_lens = {ev['length'] for ev in step_all_evs}
                    for ev in step_all_evs:
                        if ev['length'] == best_cand:
                            continue
                        if best_cand == ev['length'] * Fraction(3, 2) and not ev['head'].get('dot_near') and best_cand not in existing_lens:
                            continue
                        if event_log_likelihood(ev, best_cand) - event_log_likelihood(ev, ev['length']) < -3.0:
                            continue
                        ev['length'] = best_cand
                        ev['agreed'] = True
                        ev['grammar'] = True
                        changed += 1
            continue

        # Determine plausible candidate durations per step (one vote per voice, not per chord head).
        raw_step: list[Fraction | None] = [None] * n_steps
        obs_per_step: list[list[Fraction]] = []
        counts_per_step: list[list[Fraction]] = []
        for s in range(n_steps):
            groups_s = step_groups[s]
            voice_lens = [min(ev['length'] for ev in grp) for grp in groups_s]
            obs = sorted(set(voice_lens))
            obs_per_step.append(obs)
            counts_per_step.append(voice_lens)
            if obs:
                raw_step[s] = max(obs, key=lambda d: (voice_lens.count(d), -float(d)))

        if any(d is None for d in raw_step):
            continue
        raw_seq = tuple(d for d in raw_step if d is not None)
        raw_sum = sum(raw_seq, Fraction(0)) + shared_rest

        # Apply meter balance only on interior full bars with no partial/counterpoint rests
        # and whose raw sum is close to the bar target (never forcing unmeasured chant or changed meters).
        is_pickup = is_first_system and item_idx == 0 and raw_sum < (bar_target or Fraction(0))
        close_to_target = (
            bar_target is not None
            and abs(raw_sum - bar_target) <= max(Fraction(1), bar_target / 4)
        )
        use_meter = (
            bar_target is not None
            and not is_pickup
            and item_idx < len(bar_items) - 1
            and (not bar_rests or item['rests_all_shared'])
            and close_to_target
        )

        # Build step candidates: in unmeasured bars, never invent unobserved compromise durations
        # between disagreeing voices, while allowing unanimous neural head flips when all voices agree.
        cands_per_step: list[list[Fraction]] = []
        neural_unanimous = False
        for s in range(n_steps):
            obs = obs_per_step[s]
            pool = set(obs)
            if use_meter or len(obs) == 1:
                for d in obs:
                    for cand in STEP_CANDIDATES:
                        if cand in (d * 2, d / 2, d * Fraction(3, 2), d * Fraction(2, 3)):
                            pool.add(cand)
            if len(obs) == 1 and step_groups[s]:
                cur_kind = _HEAD_KIND.get(obs[0])
                step_evs_all = [ev for grp in step_groups[s] for ev in grp]
                if cur_kind in ('filled', 'hollow') and all(ev.get('head', {}).get('symnet') is not None for ev in step_evs_all):
                    alt_idx = 1 if cur_kind == 'filled' else 0
                    cur_idx = 0 if cur_kind == 'filled' else 1
                    if all(float(ev['head']['symnet'][alt_idx]) >= 0.94 and float(ev['head']['symnet'][cur_idx]) <= 0.03
                           for ev in step_evs_all):
                        neural_unanimous = True
            cands_per_step.append(sorted(pool))

        # Score each (step, cand) with one averaged voice weight per voice group.
        local_scores: list[dict[Fraction, float]] = []
        for s in range(n_steps):
            groups_s = step_groups[s]
            sc = {}
            for cand in cands_per_step[s]:
                sc[cand] = sum(
                    sum(event_log_likelihood(ev, cand) for ev in grp) / len(grp)
                    for grp in groups_s
                )
            local_scores.append(sc)
            # Break voice-count ties in raw_step using local visual log-likelihood.
            obs = obs_per_step[s]
            voice_lens = counts_per_step[s]
            raw_step[s] = max(obs, key=lambda d: (voice_lens.count(d), local_scores[s][d]))

        raw_seq = tuple(d for d in raw_step if d is not None)
        raw_sum = sum(raw_seq, Fraction(0)) + shared_rest

        all_agree = all(
            len({ev['length'] for grp in step_groups[s] for ev in grp}) <= 1
            for s in range(n_steps)
        )
        if all_agree and not neural_unanimous and (not use_meter or raw_sum == bar_target):
            continue

        # Bounded beam search over step durations (exact for short bars).
        beam: list[tuple[float, Fraction, tuple[Fraction, ...], int]] = [(0.0, Fraction(0), (), 0)]
        spans_ending_at: dict[int, list[tuple[int, list[dict]]]] = {}
        for s0, s1, evs in long_spans:
            spans_ending_at.setdefault(s1 - 1, []).append((s0, evs))

        for s in range(n_steps):
            next_beam: list[tuple[float, Fraction, tuple[Fraction, ...], int]] = []
            for cur_sc, cur_sum, cur_seq, n_diff in beam:
                for cand in cands_per_step[s]:
                    new_diff = n_diff + (0 if cand == raw_seq[s] else 1)
                    if new_diff > 2:
                        continue
                    new_sum = cur_sum + cand
                    if use_meter and new_sum + shared_rest > bar_target:
                        continue
                    add_sc = local_scores[s][cand]
                    new_seq = cur_seq + (cand,)
                    for s0, sp_evs in spans_ending_at.get(s, ()):
                        span_dur = sum(new_seq[s0:s + 1], Fraction(0))
                        add_sc += sum(event_log_likelihood(ev, span_dur) for ev in sp_evs) / len(sp_evs)
                    next_beam.append((cur_sc + add_sc, new_sum, new_seq, new_diff))
            if not next_beam:
                beam = []
                break
            next_beam.sort(key=lambda x: x[0], reverse=True)
            beam = next_beam[:48]

        if not beam:
            continue

        meter_bonus = 2.4 if use_meter else 0.0
        scored_final = []
        for sc, tot, seq, n_diff in beam:
            bonus = meter_bonus if (use_meter and tot + shared_rest == bar_target) else 0.0
            scored_final.append((sc + bonus, tot, seq, n_diff))
        scored_final.sort(key=lambda x: x[0], reverse=True)

        best_sc, best_tot, best_seq, _ = scored_final[0]
        raw_sc = sum(local_scores[s][raw_seq[s]] for s in range(n_steps))
        for s0, s1, sp_evs in long_spans:
            span_dur = sum(raw_seq[s0:s1], Fraction(0))
            raw_sc += sum(event_log_likelihood(ev, span_dur) for ev in sp_evs) / len(sp_evs)
        if use_meter and raw_sum == bar_target:
            raw_sc += meter_bonus

        # In unmeasured bars, also require beating each voice keeping its own observed duration.
        baseline_sc = raw_sc
        if not use_meter:
            indep_sc = sum(
                sum(event_log_likelihood(ev, ev['length']) for ev in grp) / len(grp)
                for s in range(n_steps) for grp in step_groups[s]
            )
            for s0, s1, sp_evs in long_spans:
                span_dur = sum(raw_seq[s0:s1], Fraction(0))
                indep_sc += sum(event_log_likelihood(ev, span_dur) for ev in sp_evs) / len(sp_evs)
            baseline_sc = max(raw_sc, indep_sc)

        margin = 0.9 if (use_meter and best_tot + shared_rest == bar_target and raw_sum != bar_target) else 1.15
        if best_seq != raw_seq and best_sc >= baseline_sc + margin:
            changed_steps = {s for s in range(n_steps) if best_seq[s] != raw_seq[s]}
            for s in range(n_steps):
                target_d = best_seq[s]
                if not (target_d in TYPES or target_d / Fraction(3, 2) in TYPES):
                    continue
                if s not in changed_steps:
                    continue
                step_all_evs = [ev for grp in step_groups[s] for ev in grp]
                existing_lens = {ev['length'] for ev in step_all_evs}
                for ev in step_all_evs:
                    if ev['length'] == target_d:
                        continue
                    # Do not invent a dot on an undotted note unless dot ink is nearby or another voice already has it.
                    if target_d == ev['length'] * Fraction(3, 2) and not ev['head'].get('dot_near') and target_d not in existing_lens:
                        continue
                    # Do not override a note whose local visual evidence strongly rejects target_d.
                    if event_log_likelihood(ev, target_d) - event_log_likelihood(ev, ev['length']) < -3.0:
                        continue
                    ev['length'] = target_d
                    ev['agreed'] = True
                    ev['grammar'] = True
                    changed += 1
            for s0, s1, sp_evs in long_spans:
                if not any(k in changed_steps for k in range(s0, s1)):
                    continue
                span_dur = sum(best_seq[s0:s1], Fraction(0))
                if not (span_dur in TYPES or span_dur / Fraction(3, 2) in TYPES):
                    continue
                for ev in sp_evs:
                    if ev['length'] == span_dur:
                        continue
                    # Keep SPAN_CUT=False behavior and never lengthen a span without visual support.
                    if span_dur < ev['length']:
                        continue
                    if span_dur == ev['length'] * Fraction(3, 2) and not ev['head'].get('dot_near'):
                        continue
                    if event_log_likelihood(ev, span_dur) < event_log_likelihood(ev, ev['length']) + 0.5:
                        continue
                    ev['length'] = span_dur
                    ev['agreed'] = True
                    ev['grammar'] = True
                    changed += 1

    return changed


def note_confidence(note: dict, head: dict, stem: dict | None = None,
                    bar_sum_ok: bool | None = None) -> float:
    """Computes a calibrated per-note confidence score in [0.01, 0.999] for .notes.json output."""
    dur = Fraction(note['length']).limit_denominator(192)
    want_kind = _HEAD_KIND.get(dur)
    if want_kind is None:
        want_kind = 'hollow' if head.get('hollow') else 'filled'

    # 1. Head detection and head-type confidence (SymNet when available, else rule priors).
    sym = head.get('symnet')
    if sym is not None and len(sym) >= 4:
        p_det = float(sym[0] + sym[1] + sym[2] + sym[3])
        p_kind = float(sym[_KIND_INDEX[want_kind]]) / max(1e-4, p_det)
        # Mildly smooth neural probabilities to prevent zero/one overconfidence on rare fonts.
        head_conf = (0.05 + 0.95 * min(1.0, max(0.0, p_det))) * (0.10 + 0.90 * min(1.0, max(0.0, p_kind)))
    else:
        head_conf = 0.94
        if head.get('thin') or head.get('alt'):
            head_conf *= 0.90
        if not head.get('stems') and dur < Fraction(4):
            head_conf *= 0.85

    # 2. Stem-tail confidence for filled stemmed notes (StemNet when available).
    tail_conf = 0.98
    if want_kind == 'filled' and stem is not None:
        sp = stem.get('stemnet')
        base_d = _base_duration(dur)
        t_idx = 0 if base_d == Fraction(1) else 1 if base_d == Fraction(1, 2) else 2 if base_d == Fraction(1, 4) else None
        if sp is not None and t_idx is not None and len(sp) > t_idx:
            p_tail = float(sp[t_idx])
            if t_idx == 0 and _unwitnessed_beam(stem):
                tail_conf = 0.88 + 0.11 * p_tail
            else:
                tail_conf = 0.15 + 0.85 * min(1.0, max(0.0, p_tail))
        elif head.get('tails', {}).get(stem['direction'], 0) >= 2:
            tail_conf = 0.92

    # 3. Pitch placement stability (ledger distance and fractional offset from staff step).
    pitch_conf = 0.99
    place = float(head.get('place', note.get('place', 0.0)))
    if abs(place) >= 7.0:
        pitch_conf *= 0.94
    elif abs(place) >= 5.5:
        pitch_conf *= 0.97
    if abs(place - round(place)) > 0.32:
        pitch_conf *= 0.93

    # 4. Musical consensus (cross-voice votes and bar duration consistency).
    music_conf = 1.0
    votes = note.get('votes') or []
    if votes:
        first_v = votes[0]
        tot_v = sum(first_v.values())
        if len(first_v) == 1 and tot_v >= 2:
            music_conf = 1.02
        elif len(first_v) >= 2 and not note.get('agreed'):
            music_conf = 0.93
    if bar_sum_ok is True:
        music_conf *= 1.02
    elif bar_sum_ok is False:
        music_conf *= 0.94

    conf = head_conf * tail_conf * pitch_conf * music_conf
    return round(min(0.999, max(0.01, conf)), 4)
