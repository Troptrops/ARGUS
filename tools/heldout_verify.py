"""Independently verify frozen held-out capture: zip hashes, byte counts, CT partition.

Requires blosc2 only to decode actual prediction bytes, optionally numpy to
cross-check each rectangle using a second implementation. Does not download data.
"""
from __future__ import annotations
import argparse,csv,hashlib,io,json,zipfile
from pathlib import Path
import sys
try:
    from argus_support.overlap import overlaps
    from tools.heldout_protocol import verify_plan
    from tools.heldout_capture import metadata_is_expected
except ImportError:
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
    from argus_support.overlap import overlaps
    from tools.heldout_protocol import verify_plan
    from tools.heldout_capture import metadata_is_expected


def sh(x):return hashlib.sha256(x).hexdigest()


def raw_rect_positive(raw,chunks,pred_lo,inter_lo,inter_hi):
    # Independent stdlib method: count zeros for each contiguous X strip.
    starts=[inter_lo[i]-pred_lo[i] for i in range(3)]
    ends=[inter_hi[i]-pred_lo[i]+1 for i in range(3)]
    ny,nx=chunks[1:]
    positives=0
    for z in range(starts[0],ends[0]):
        for y in range(starts[1],ends[1]):
            a=(z*ny+y)*nx+starts[2];b=(z*ny+y)*nx+ends[2]
            positives+=(b-a)-raw[a:b].count(0)
    return positives


def verify(capture_zip,root):
    import blosc2
    with zipfile.ZipFile(capture_zip) as z:
        if z.testzip() is not None:raise ValueError('ZIP CRC check failed')
        names=set(z.namelist())
        required={'HELDOUT_PLAN.json','HISTORICAL_POINTS_EXCLUSION_SOURCE.json','manifest.json','receipts.json'}
        if not required.issubset(names):raise ValueError('Missing core capture records')
        plan=json.loads(z.read('HELDOUT_PLAN.json'));hist=z.read('HISTORICAL_POINTS_EXCLUSION_SOURCE.json')
        planhash=verify_plan(plan,hist)
        expected=Path(root,'protocol/HELDOUT_PLAN.sha256').read_text().split()[0]
        if planhash!=expected:raise ValueError('Different selection from the preregistered plan')
        m=json.loads(z.read('manifest.json'));receipts=json.loads(z.read('receipts.json'))
        if m['plan_sha256_canonical']!=planhash:raise ValueError('Wrong capture-plan digest')
        present_ct_meta='ct_metadata.json' in names and 'prediction_metadata.json' in names
        if not present_ct_meta:
            return {'status':'INCOMPLETE_NO_METADATA','capture_status':m['status'],'plan_sha256':planhash,
                    'issues':m['error_messages'],'cells':[]},[]
        cb=z.read('ct_metadata.json');pb=z.read('prediction_metadata.json')
        cm,pm=metadata_is_expected(cb,pb)
        for k,blob in [('ct_metadata.json',cb),('prediction_metadata.json',pb)]:
            if m['metadata'][k]['sha256']!=sh(blob):raise ValueError('Metadata hash mismatch: '+k)
        by_id={r['id']:r for r in m['samples']}
        if set(by_id)!={p['id'] for p in plan['sample']} and m['status'] not in ('INCOMPLETE_ERROR',):
            raise ValueError('No replacement or dropped samples permitted')
        by_ct={r['key']:r for r in m['ct_checks']}
        if len(by_ct)!=len(m['ct_checks']):raise ValueError('Duplicate CT records')
        receipt_by_get={(r['method'],r['url']):r for r in receipts if r['method']=='GET' and r.get('http_status')==200}
        # All chunk-state claims must reconcile with an actual observation receipt.
        last_receipt={}
        for rr in receipts:
            if rr.get('method') in ('GET','HEAD') and rr.get('url'):
                if rr.get('cache_hit',False):
                    raise ValueError('Held-out capture incorrectly used cached receipt')
                last_receipt[(rr['method'],rr['url'])]=rr
        if len(by_id)!=len(m['samples']):raise ValueError('Duplicate prediction sample IDs')
        allowed_sample_keys={p['prediction_key'] for p in plan['sample']}
        if any(v['prediction_key'] not in allowed_sample_keys for v in m['samples']):
            raise ValueError('Non-preregistered prediction key in results')
        allowed_ct={c['ct_key'] for p in plan['sample'] for c in overlaps(p['prediction_key'],cm,pm)['ct_candidates']}
        if not set(by_ct).issubset(allowed_ct):raise ValueError('CT checks outside locked sample')
        for sample in m['samples']:
            url=plan['prediction_base_url']+'/'+sample['prediction_key']
            receipt=last_receipt.get(('GET',url))
            if receipt is None or receipt.get('http_status')!=sample['http_status']:
                raise ValueError('Prediction state lacks matching GET receipt')
            expected_state='PRESENT' if sample['http_status']==200 else 'ABSENT_404' if sample['http_status']==404 else 'UNKNOWN'
            if sample['state']!=expected_state:raise ValueError('Contradictory prediction status')
        for ctrow in m['ct_checks']:
            receipt=last_receipt.get(('HEAD',plan['ct_base_url']+'/'+ctrow['key']))
            if receipt is None or receipt.get('http_status')!=ctrow['http_status']:
                raise ValueError('CT storage state lacks matching HEAD receipt')
            expected_state='PRESENT' if ctrow['http_status']==200 else 'ABSENT_404' if ctrow['http_status']==404 else 'UNKNOWN'
            if ctrow['state']!=expected_state:raise ValueError('Contradictory CT storage status')
        if m['status']=='COMPLETE' and set(by_ct)!=allowed_ct:
            raise ValueError('Complete run omitted frozen CT overlap checks')
        sample_results=[];rows=[]
        for p in plan['sample']:
            sample=by_id.get(p['id'])
            result={'id':p['id'],'prediction_key':p['prediction_key'],'stratum':p['stratum'],
                    'prediction_storage':'UNAVAILABLE','positive_voxels':None,
                    'positives_in_stored_ct':None,'positives_in_absent_ct':None,'positives_in_unknown_ct':None,
                    'positive_fraction_in_absent_ct':None,
                    'unknown_ct_chunk_count':None}
            if not sample:
                sample_results.append(result);continue
            if sample['prediction_key']!=p['prediction_key']:raise ValueError('Sample key mismatch')
            state=sample['state'];result['prediction_storage']=state
            if state=='UNKNOWN':sample_results.append(result);continue
            case=overlaps(p['prediction_key'],cm,pm)
            if state=='ABSENT_404':
                # Declared Zarr fill_value 0; count no positive predictions, even if CT unavailable.
                result.update(positive_voxels=0,positives_in_stored_ct=0,
                              positives_in_absent_ct=0,positives_in_unknown_ct=0)
                result['unknown_ct_chunk_count']=sum(by_ct.get(c['ct_key'],{}).get('state','UNKNOWN')=='UNKNOWN' for c in case['ct_candidates'])
                sample_results.append(result);continue
            if state!='PRESENT':raise ValueError('Unexpected prediction state')
            filename=sample['file']
            if filename!='raw/'+p['prediction_key'].replace('/','_')+'.blosc' or filename not in names:
                raise ValueError('Missing/misnamed raw prediction chunk')
            compressed=z.read(filename)
            if sh(compressed)!=sample['sha256'] or len(compressed)!=sample['bytes']:
                raise ValueError('Prediction raw-byte hash or size mismatch')
            url=plan['prediction_base_url']+'/'+p['prediction_key']
            if receipt_by_get.get(('GET',url),{}).get('sha256')!=sample['sha256']:
                raise ValueError('No matching GET receipt for prediction bytes')
            raw=blosc2.decompress(compressed)
            expected_len=pm['chunks'][0]*pm['chunks'][1]*pm['chunks'][2]
            if len(raw)!=expected_len:raise ValueError('Wrong prediction decoded length')
            total_positive=len(raw)-raw.count(0)
            pos={'PRESENT':0,'ABSENT_404':0,'UNKNOWN':0}
            unknown_count=0
            pred_lo=case['prediction_lo_zyx']
            # Independently check contiguous-row counting with NumPy where installed.
            try:
                import numpy as np
                array=np.frombuffer(raw,dtype='u1').reshape(tuple(pm['chunks']))
            except ImportError:array=None
            for c in case['ct_candidates']:
                status=by_ct.get(c['ct_key'],{}).get('state','UNKNOWN')
                if status not in ('PRESENT','ABSENT_404'):status='UNKNOWN';unknown_count+=1
                observed=raw_rect_positive(raw,pm['chunks'],pred_lo,c['intersection_lo_zyx'],c['intersection_hi_zyx'])
                if array is not None:
                    start=[c['intersection_lo_zyx'][i]-pred_lo[i] for i in range(3)]
                    end=[c['intersection_hi_zyx'][i]-pred_lo[i]+1 for i in range(3)]
                    independently=int((array[start[0]:end[0],start[1]:end[1],start[2]:end[2]]!=0).sum())
                    if observed!=independently:raise AssertionError('Row/Numpy disagreement on '+c['ct_key'])
                pos[status]+=observed
                rows.append({'id':p['id'],'prediction_key':p['prediction_key'],'ct_key':c['ct_key'],
                             'ct_state':status,'intersection_voxels':c['intersection_voxels'],'positive_voxels':observed})
            if sum(pos.values())!=total_positive:
                raise AssertionError('Positive counts do not reconcile with full raw chunk')
            result.update(positive_voxels=total_positive,positives_in_stored_ct=pos['PRESENT'],
                          positives_in_absent_ct=pos['ABSENT_404'],positives_in_unknown_ct=pos['UNKNOWN'],
                          positive_fraction_in_absent_ct=(pos['ABSENT_404']/total_positive if total_positive and pos['UNKNOWN']==0 else None),
                          unknown_ct_chunk_count=unknown_count)
            sample_results.append(result)
        accepted=[r for r in sample_results if r['positive_voxels'] is not None]
        total=sum(r['positive_voxels'] for r in accepted)
        in_absent=sum(r['positives_in_absent_ct'] for r in accepted)
        in_unknown=sum(r['positives_in_unknown_ct'] for r in accepted)
        storage_complete=all(r['state'] in ('PRESENT','ABSENT_404') for r in m['ct_checks'])
        report={'artifact':'ARGUS_0_4_HELDOUT_INDEPENDENT_AUDIT','status':'COMPLETE' if m['status']=='COMPLETE' and len(accepted)==len(plan['sample']) and in_unknown==0 and storage_complete else 'PARTIAL',
                'capture_status':m['status'],'plan_sha256':planhash,
                'frame':'Only historical R04 halo, conditional on excluding previously inspected sample chunks; not full scroll',
                'sampled_cells':len(plan['sample']),'cells_accounted_for':len(accepted),
                'prediction_present_cells':sum(r['prediction_storage']=='PRESENT' for r in sample_results),
                'prediction_absent_404_cells':sum(r['prediction_storage']=='ABSENT_404' for r in sample_results),
                'positive_voxels':total,'positive_voxels_in_absent_masked_ct_storage':in_absent,
                'positive_voxels_in_unknown_masked_ct_storage':in_unknown,
                'fraction_of_positive_voxels_in_absent_ct_storage': in_absent/total if total and in_unknown==0 and len(accepted)==len(plan['sample']) else None,
                'novelty_warning':'Prior public work already estimates voxel-level phantom masks; this is a prespecified local held-out storage audit, not proof of method novelty.',
                'science_warning':'Absent masked-CT storage != physically invalid papyrus; unmasked CT and independent index registration NOT checked.',
                'no_generalization':'No scroll-wide percentage, confidence interval or p-value from 24 spatially correlated grid cells.',
                'cells':sample_results}
        return report,rows


def write_results(report,rows,out):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    (out/'HELDOUT_AUDIT.json').write_text(json.dumps(report,indent=2)+'\n')
    for filename,data in [('HELDOUT_CELLS.csv',report['cells']),('HELDOUT_CT_PARTITIONS.csv',rows)]:
        keys=list(data[0]) if data else ['no_rows']
        with (out/filename).open('w',newline='',encoding='utf8') as f:
            writer=csv.DictWriter(f,fieldnames=keys);writer.writeheader();writer.writerows(data)
    print('AUDIT STATUS:',report['status'])
    print('Cells accounted:',report.get('cells_accounted_for'),'/',report.get('sampled_cells'))
    print('Positive voxels:',report.get('positive_voxels'),'absent-CT positives:',report.get('positive_voxels_in_absent_masked_ct_storage'))
    print('Saved',out)


def main():
    p=argparse.ArgumentParser();p.add_argument('capture_zip');p.add_argument('--root',default=str(Path(__file__).resolve().parents[1]));p.add_argument('--out',default='HELDOUT_ANALYSIS')
    args=p.parse_args()
    try:
        report,rows=verify(args.capture_zip,args.root)
        write_results(report,rows,args.out)
        return 0 if report['status']=='COMPLETE' else 2
    except ImportError:
        print('Decoder unavailable. Install: python -m pip install blosc2 numpy')
        return 2
    except Exception as exc:
        print('VERIFY FAILED:',type(exc).__name__,str(exc))
        return 1

if __name__=='__main__':sys.exit(main())
