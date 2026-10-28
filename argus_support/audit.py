"""Preregistered support observations and signed normal perturbations."""
from collections import Counter
import math
from .volume import nearest

OFFSETS = (-2, -1, 0, 1, 2)


def audit(points, ct, prediction=None, mode='surface-support', radius=2,
          prediction_decode=False):
    rows = []
    for point in points:
        coord = point.get('zyx')
        row = {**point, 'geometry_state':point.get('registration','GEO_REGISTRATION_UNVERIFIED')}
        row['ct'] = ct.observe(coord,radius,mode)
        row['perturbations'] = []
        normal = point.get('normal_xyz')
        if mode == 'surface-support':
            try:
                if not isinstance(normal,(list,tuple)) or len(normal) != 3 or any(
                        isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) for v in normal):
                    raise ValueError('Missing or nonfinite stored normal')
                length = math.sqrt(sum(v*v for v in normal))
                if not 0.7 <= length <= 1.3:
                    raise ValueError('Stored normal length outside preregistered [0.7,1.3]')
                nearest(coord,ct.meta['shape'])
                unit_zyx = [v/length for v in reversed(normal)]
                row['normal_length_before_normalization'] = length
                for offset in OFFSETS:
                    shifted = [v+offset*n for v,n in zip(coord,unit_zyx)]
                    row['perturbations'].append({'offset_vox':offset, 'zyx':shifted,
                        'ct':row['ct'] if offset==0 else ct.observe(shifted,radius,mode)})
                values = [p['ct'].get('value') for p in row['perturbations']]
                valid = all(v is not None for v in values)
                row['stability'] = ('STABLE_NONZERO' if all(v != 0 for v in values) else
                    'STABLE_ZERO' if all(v == 0 for v in values) else 'OFFSET_SENSITIVE') if valid else 'INDETERMINATE'
                row['unique_sampled_voxels'] = len({tuple(p['ct']['sampled_zyx']) for p in row['perturbations']
                                                        if 'sampled_zyx' in p['ct']})
            except (ValueError,TypeError) as exc:
                row['stability'] = 'NORMAL_PERTURBATION_NOT_TESTED'
                row['normal_error'] = str(exc)
        if prediction:
            # Equal shapes alone do not prove registration. CLI requires explicit assertion.
            row['prediction'] = prediction.observe(coord,0,'voxel' if prediction_decode else 'chunk-only')
            state = row['prediction']['state']
            if state.startswith('CT_VOXEL_'):
                row['prediction']['state'] = state.replace('CT_VOXEL_','PREDICTION_VOXEL_',1)
        rows.append(row)
    unknown = any(r['ct']['state'] in ('INDETERMINATE','INVALID_COORDINATE') or
        (mode == 'surface-support' and (r.get('stability') in ('INDETERMINATE','NORMAL_PERTURBATION_NOT_TESTED') or
         any(not p['ct'].get('neighborhood',{}).get('complete',False) for p in r['perturbations']))) or
        (prediction and r['prediction']['state'] in ('INDETERMINATE','INVALID_COORDINATE')) for r in rows)
    return {'status':'PARTIAL_OR_INDETERMINATE' if unknown else 'OBSERVATIONS_COMPLETED',
        'ct_state_counts':dict(Counter(r['ct']['state'] for r in rows)),
        'stability_counts':dict(Counter(r.get('stability','NOT_REQUESTED') for r in rows)),
        'points':rows, 'interpretation':'Observed nonzero CT is not papyrus, sheet identity, or ink evidence.',
        'gate_7f':'BLOCKED', 'r12_ink_status':'UNRESOLVED_PHYSICAL_ANOMALY'}
