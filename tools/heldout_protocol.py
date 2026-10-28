"""Generate the deterministic, outcome-blind ARGUS held-out audit plan.

No calls to source datasets are made; candidates depend ONLY on historic
arena bounds, array chunk sizes and the exclusion list from the earlier survey.
This is conditionally held out inside the R04 arena, not scroll-wide random.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path

SEED = 'ARGUS-2026-10-22-HELDOUT-24-PREDECLARED-V1'
FRAME = {'z': [17770, 19282], 'y': [5136, 6256], 'x': [4368, 5488]}  # half-open voxel bounds
CHUNKS = (192, 192, 192)
SHAPE = (19416, 7948, 7948)
N_PER_STRATUM = 8
CT_URL = ('https://vesuvius-challenge-open-data.s3.amazonaws.com/PHerc0211/'
          'volumes/20250821151803-9.362um-1.2m-113keV-masked.zarr/0')
PRED_URL = ('https://vesuvius-challenge-open-data.s3.amazonaws.com/PHerc0211/'
            'representations/predictions/surfaces/'
            '20250821151803-surface-20260413222639-surface-m7-L0-th0.2.zarr/0')


def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode('utf8')


def known_keys(historical):
    return sorted({'/'.join(str(int(v)//192) for v in p['zyx']) for p in historical['points']})


def create_plan(historical_bytes):
    historic = json.loads(historical_bytes)
    excludes = known_keys(historic)
    excluded = set(excludes)
    candidates = []
    for z in range(FRAME['z'][0]//192, (FRAME['z'][1]-1)//192+1):
        for y in range(FRAME['y'][0]//192, (FRAME['y'][1]-1)//192+1):
            for x in range(FRAME['x'][0]//192, (FRAME['x'][1]-1)//192+1):
                if z*192 >= SHAPE[0] or y*192 >= SHAPE[1] or x*192 >= SHAPE[2]:
                    continue
                k = f'{z}/{y}/{x}'
                if k not in excluded:
                    candidates.append((z, y, x, k))
    selected = []
    for s, (low, high) in enumerate([(92,94),(95,97),(98,100)]):
        eligible = [v for v in candidates if low <= v[0] <= high]
        ranked = sorted(eligible, key=lambda v: (hashlib.sha256(f'{SEED}|{v[3]}'.encode()).hexdigest(),v[3]))
        for _,_,_,k in ranked[:N_PER_STRATUM]:
            selected.append({'id': f'H{len(selected):02}', 'prediction_key':k, 'stratum': s})
    if len(selected) != 24 or len({c['prediction_key'] for c in selected}) != 24:
        raise ValueError('Frozen selection must contain 24 unique cells')
    plan = {
        'artifact':'ARGUS_0_4_HELDOUT_PROTOCOL',
        'status':'FROZEN_BEFORE_ANY_HELDOUT_REMOTE_OBSERVATION',
        'sampling':'Hash-ranked deterministic selection without replacement, 8 per native-Z third; 24 nominal prediction cells in R04 arena',
        'population':'Prediction chunk-grid cells intersecting the historical R04 halo; exclude all prior 18-point-survey prediction keys',
        'frame_half_open_zyx':FRAME, 'prediction_chunk_shape':list(CHUNKS),
        'strata_z_chunk_ranges':[[92,94],[95,97],[98,100]],
        'seed':SEED, 'sample_per_stratum':N_PER_STRATUM,
        'prior_18_point_survey_sha256':hashlib.sha256(historical_bytes).hexdigest(),
        'excluded_prior_prediction_keys':excludes,
        'candidate_cells_after_exclusion':len(candidates),
        'selection_used_prediction_values':False,'selection_used_ct_storage_states':False,
        'selection_used_network_or_current_data':False,
        'ct_base_url':CT_URL,'prediction_base_url':PRED_URL,
        'sample':selected,
        'rules':[
            'Attempt every sampled cell; never replace an absent or failed prediction chunk',
            'Capture its raw Blosc bytes on HTTP 200 and record 404 as dataset fill-only',
            'Check every overlapping native masked CT Zarr chunk via HEAD',
            'Any 403, 429, 5xx, timeout or unrecognized HTTP response is UNKNOWN, never ABSENT',
            'Keep all denominators, missingness and errors; no post-selection based on results',
            'Only storage support on nominal matching ZYX grid; registration not validated',
            'No ink, phantom papyrus, surface authenticity or whole-scroll prevalence claim'
        ]
    }
    return plan


def verify_plan(plan, historical_bytes):
    if plan != create_plan(historical_bytes):
        raise ValueError('Plan content differs from frozen selection algorithm and historical points')
    return hashlib.sha256(canonical(plan)).hexdigest()


def main():
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--output',default='protocol/HELDOUT_PLAN.json');args=p.parse_args()
    root=Path(__file__).resolve().parents[1]
    hist=(root/'protocol/HISTORICAL_POINTS_EXCLUSION_SOURCE.json').read_bytes()
    plan=create_plan(hist)
    target=Path(args.output);target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(plan,indent=2)+'\n',encoding='utf8')
    sha=hashlib.sha256(canonical(plan)).hexdigest()
    target.with_suffix('.sha256').write_text(sha+'  HELDOUT_PLAN.json\n')
    print('FROZEN PLAN SHA256 (canonical JSON):',sha)
    print('Candidate cells:',plan['candidate_cells_after_exclusion'],'Selected:',len(plan['sample']))

if __name__=='__main__': main()
