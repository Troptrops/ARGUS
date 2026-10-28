"""Exact spatial chunk-overlap audit for prediction-positive / missing CT samples.

Does NOT establish physical papyrus or ink. CT storage only. No external dependencies.
"""
from __future__ import annotations

from itertools import product
from collections import Counter
import hashlib
import json
import math
from pathlib import Path

from .volume import validate


def bounds(index, chunks, shape):
    """Inclusive native-ZYX voxel bounds for a Zarr chunk."""
    if len(index) != 3 or any(type(i) is not int or i < 0 for i in index):
        raise ValueError('Expected three nonnegative integer chunk indices')
    if any(i * c >= n for i, c, n in zip(index, chunks, shape)):
        raise ValueError('Chunk index outside array')
    lo = tuple(i*c for i, c in zip(index, chunks))
    hi = tuple(min((i+1)*c, n)-1 for i, c, n in zip(index, chunks, shape))
    return lo, hi


def key(index, meta):
    return meta.get('dimension_separator', '.').join(map(str, index))


def parse_key(s, meta):
    sep = meta.get('dimension_separator', '.')
    pieces = s.split(sep)
    if len(pieces) != 3 or any(not x.isdigit() for x in pieces):
        raise ValueError('Invalid chunk key')
    return tuple(map(int,pieces))


def overlaps(pred_chunk_key, ct_meta, pred_meta):
    """All native CT chunks intersecting a prediction chunk, incl. edges."""
    validate(ct_meta); validate(pred_meta)
    if ct_meta['shape'] != pred_meta['shape']:
        raise ValueError('Native grids differ; no unverified transform allowed')
    lo, hi = bounds(parse_key(pred_chunk_key,pred_meta), pred_meta['chunks'], pred_meta['shape'])
    candidates = []
    for indices in product(*(range(a//c,b//c+1) for a,b,c in zip(lo,hi,ct_meta['chunks']))):
        clo, chi = bounds(indices,ct_meta['chunks'],ct_meta['shape'])
        il = tuple(max(a,b) for a,b in zip(lo,clo))
        ih = tuple(min(a,b) for a,b in zip(hi,chi))
        nvox = math.prod(h-l+1 for l,h in zip(il,ih))
        candidates.append({'ct_key':key(indices,ct_meta), 'ct_index':list(indices),
                           'intersection_lo_zyx':list(il), 'intersection_hi_zyx':list(ih),
                           'intersection_voxels':nvox})
    pvox = math.prod(b-a+1 for a,b in zip(lo,hi))
    if sum(c['intersection_voxels'] for c in candidates) != pvox:
        raise AssertionError('Intersection partition did not cover prediction chunk')
    return {'prediction_key':pred_chunk_key,'prediction_lo_zyx':list(lo),'prediction_hi_zyx':list(hi),
            'prediction_voxels':pvox,'ct_candidates':candidates}


def historical_ct_chunk_states(report):
    """Import observed CT storage state, never infer other chunk statuses."""
    states = {}
    for p in report.get('points',[]):
        c = p.get('ct',{})
        k = c.get('chunk_key')
        v = c.get('state')
        s = 'ABSENT_404' if v == 'CHUNK_ABSENT_404' else (
            'PRESENT' if v in ('CT_VOXEL_ZERO','CT_VOXEL_NONZERO','CHUNK_PRESENT_ONLY') else None)
        if not k or not s:
            continue
        if k in states and states[k] != s:
            raise ValueError('Conflicting historical CT chunk evidence: '+k)
        states[k] = s
    return states


def select_cases(report):
    """Require genuinely observed positive prediction voxel, absent CT chunk."""
    selected = []
    for p in report.get('points',[]):
        c, pred = p.get('ct',{}), p.get('prediction',{})
        if (c.get('state')=='CHUNK_ABSENT_404' and
            pred.get('state') in ('PREDICTION_VOXEL_NONZERO','CT_VOXEL_NONZERO') and
            isinstance(pred.get('value'),(int,float)) and pred['value']>0 and pred.get('chunk_key')):
            selected.append({'id':p['id'], 'zyx':p['zyx'], 'prediction_key':pred['chunk_key'],
                             'prediction_sample_value':pred['value'],
                             'sample_ct_chunk_key':c.get('chunk_key')})
    return selected


def classify(case, candidate_state_map):
    for candidate in case['ct_candidates']:
        state=candidate_state_map.get(candidate['ct_key'],'UNKNOWN_NOT_TESTED')
        candidate['state'] = state if state in ('PRESENT','ABSENT_404') else 'UNKNOWN_NOT_TESTED'
    weights = Counter()
    for c in case['ct_candidates']:
        weights[c['state']] += c['intersection_voxels']
    total = case['prediction_voxels']
    present = weights['PRESENT']; unknown = weights['UNKNOWN_NOT_TESTED']+weights['INDETERMINATE']
    case['ct_stored_coverage_lower_bound'] = present/total
    case['ct_stored_coverage_upper_bound'] = (present+unknown)/total
    case['ct_chunk_states'] = dict(Counter(c['state'] for c in case['ct_candidates']))
    case['storage_status'] = ('CT_STORAGE_OVERLAP_CONFIRMED' if present else
                              'NO_CT_STORAGE_OVERLAP' if unknown==0 else 'UNRESOLVED_OVERLAP')
    case['scientific_limit'] = ('Only stored chunk overlap on nominal native grid. '
        'Not CT voxel intensity, surface identity, registration, papyrus, ink or textual evidence.')
    return case


def case_report(source_report, live_states=None):
    provenance = source_report.get('provenance',{})
    cm = provenance.get('ct_metadata'); pm = provenance.get('prediction_metadata')
    if not cm or not pm:
        raise ValueError('Need CT and prediction .zarray metadata in source report')
    selected = select_cases(source_report)
    hist = historical_ct_chunk_states(source_report)
    if not selected:
        raise ValueError('No prediction-positive/CT-chunk-absent cases')
    cases = []
    for sample in selected:
        geometry = overlaps(sample['prediction_key'],cm,pm)
        cases.append(classify({**sample,**geometry}, live_states if live_states is not None else hist))
    all_complete = all(c['ct_stored_coverage_lower_bound'] == c['ct_stored_coverage_upper_bound'] for c in cases)
    return {'status':('LIVE_CT_CHUNK_OVERLAP_COMPLETE' if all_complete else 'LIVE_CT_CHUNK_OVERLAP_PARTIAL')
                   if live_states is not None else 'HISTORICAL_ONLY_PARTIAL_INVENTORY',
            'source_sha256':hashlib.sha256(json.dumps(source_report,sort_keys=True).encode()).hexdigest(),
            'source_observation':'Published ARGUS 0.1 pointwise results imported, not reproduced here',
            'live_chunk_checks':live_states is not None,
            'prediction_geometry':'Same array shape only; registration NOT independently established',
            'cases':cases,'interpretation':'Stored CT chunk overlap, not physical papyrus or ink.',
            'gate_7f':'BLOCKED'}
