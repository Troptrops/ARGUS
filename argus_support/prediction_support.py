"""Voxel-exact positive-prediction counts partitioned by stored CT chunks.

This is a **storage** audit, not proof of physical papyrus or spatial
registration. Input data are a native-grid uint8 prediction Zarr chunk and
an exhaustive non-overlapping partition by CT chunk storage status.
"""
import math

from .overlap import bounds, parse_key

VALID_STATES = frozenset(('PRESENT', 'ABSENT_404', 'INDETERMINATE', 'UNKNOWN_NOT_TESTED'))


def count_positives_in_bounds(raw, pred_meta, pred_key, lo, hi):
    """Count strictly nonzero uint8 voxels over an inclusive native ZYX box.

    Efficient in stdlib; rows are sliced using the native C-order strides.
    Does not require NumPy, and never touches CT data values.
    """
    if pred_meta['dtype'] != '|u1' or pred_meta['order'] != 'C':
        raise ValueError('Strict uint8 C-order prediction array is required')
    c = pred_meta['chunks']
    if len(c) != 3 or len(raw) != math.prod(c):
        raise ValueError('Decoded prediction chunk has incorrect length')
    pred_lo, pred_hi = bounds(parse_key(pred_key, pred_meta), c, pred_meta['shape'])
    if any(a < l or b > h or b < a for l,h,a,b in zip(pred_lo,pred_hi,lo,hi)):
        raise ValueError('Partition is outside prediction chunk')
    z0,y0,x0 = (l-p for l,p in zip(lo,pred_lo))
    z1,y1,x1 = (h-p for h,p in zip(hi,pred_lo))
    size_x = x1-x0+1
    positive=0
    for iz in range(z0,z1+1):
        for iy in range(y0,y1+1):
            off=((iz*c[1])+iy)*c[2]+x0
            positive += size_x - raw[off:off+size_x].count(0)
    n=math.prod(b-a+1 for a,b in zip(lo,hi))
    return positive, n


def count_chunk_prediction_support(raw, pred_meta, case):
    """Compute exhaustive storage-conditioned prediction-positive rates.

    Unknown storage remains *unknown*, never counted as missing or present.
    The prediction chunk need not be all positive. For boundary chunks,
    comparisons are limited to in-array coordinates (Zarr fill excluded).
    """
    predkey=case['prediction_key']
    candidates=case['ct_candidates']
    if not candidates:
        raise ValueError('No CT-partition candidates')
    # Equal summed volumes alone cannot rule out overlapping duplicate boxes.
    for i,a in enumerate(candidates):
        for b in candidates[i+1:]:
            if all(max(x,y)<=min(u,v) for x,u,y,v in zip(
                a['intersection_lo_zyx'],a['intersection_hi_zyx'],
                b['intersection_lo_zyx'],b['intersection_hi_zyx'])):
                raise ValueError('Overlapping or duplicate CT-partition boxes')
    out=[]; totals={s:{'positive':0,'voxels':0} for s in VALID_STATES}
    for row in candidates:
        state=row['state']
        if state not in VALID_STATES:
            raise ValueError('Unknown CT chunk state: '+str(state))
        positive, n=count_positives_in_bounds(raw,pred_meta,predkey,
            row['intersection_lo_zyx'],row['intersection_hi_zyx'])
        if n != row['intersection_voxels']:
            raise ValueError('Partition volume mismatch for '+row['ct_key'])
        rec={**row,'prediction_positive_voxels':positive,
             'prediction_zero_voxels':n-positive,
             'prediction_positive_fraction':positive/n}
        out.append(rec)
        totals[state]['positive']+=positive
        totals[state]['voxels']+=n
    predicted_total=sum(t['positive'] for t in totals.values())
    total=sum(t['voxels'] for t in totals.values())
    expected=case['prediction_voxels']
    if total != expected:
        raise ValueError(f'Predicted positive voxels partition is incomplete: {total} vs {expected}')
    if predicted_total > total:
        raise AssertionError('Predicted positive count exceeds chunk volume')
    unknown=sum(totals[s]['positive'] for s in ('INDETERMINATE','UNKNOWN_NOT_TESTED'))
    missing=totals['ABSENT_404']['positive']; stored=totals['PRESENT']['positive']
    return {
        'case_id':case['id'], 'prediction_key':predkey,
        'prediction_voxels':total, 'prediction_positive_voxels':predicted_total,
        'prediction_zero_voxels':total-predicted_total,
        'nonzero_prediction_in_ct_stored_regions':stored,
        'nonzero_prediction_in_ct_storage_absent_regions':missing,
        'nonzero_prediction_in_ct_unknown_regions':unknown,
        'ct_absent_share_among_nonzero_prediction_lower_bound': missing/predicted_total if predicted_total else None,
        'ct_absent_share_among_nonzero_prediction_upper_bound': (missing+unknown)/predicted_total if predicted_total else None,
        'ct_storage_status_counts':totals,
        'ct_intersections':out,
        'classification': ('COMPLETE_STORAGE_PARTITION' if all(c['state'] in ('PRESENT','ABSENT_404') for c in candidates) else 'PARTIAL_STORAGE_PARTITION'),
        'scientific_scope': ('Voxel-exact counts of nonzero surface-prediction bytes on the nominal same ZYX grid, '
                             'stratified by native CT Zarr chunk storage. Missing CT chunk is not demonstrated '
                             'missing source CT data or a physically invalid papyrus surface. '
                             'Spatial registration and papyrus/ink identity are unverified.')
    }
