#!/usr/bin/env python3
"""Independent NumPy block audit of a frozen ARGUS 0.4 held-out capture.

Install: python -m pip install numpy blosc2
Usage: python tools/verify_heldout_vectorized.py CAPTURE.zip --out OUTPUT
No internet access. Counts all positive voxels from original stored Blosc bytes,
and classifies each using the exact intersecting native CT chunk status.
"""
import collections, csv, hashlib, io, json, math, sys, zipfile
from pathlib import Path
import numpy as np
import blosc2

PINNED_PLAN_SHA='a8bcb68978589f8314952f64e8243d556628bcf76a038bf371f077aa20964d97'
PINNED_CT_META='c754c949661243c8e60a4b3212d924882908f480c8249d8f9557eb83c84856c4'
PINNED_PRED_META='e94ae5d7a63dfbf5923a0030f3d2fe969383995acf02ffb60f73e72959e6319f'
PINNED_HISTORY='1030bbcfbc2e50fbd762b0a3e0fafcd64c2d0fefd1e760f716f59853abf80769'

sha=lambda b:hashlib.sha256(b).hexdigest()

def audit(path):
    if not __debug__:
        raise RuntimeError("Use normal Python for this historical verifier; use review_release.py for optimized execution")
    with zipfile.ZipFile(path) as z:
        if z.testzip():raise ValueError('Damaged ZIP')
        names=set(z.namelist())
        for name in ('HELDOUT_PLAN.json','manifest.json','receipts.json','ct_metadata.json','prediction_metadata.json','HISTORICAL_POINTS_EXCLUSION_SOURCE.json'):
            if name not in names:raise ValueError('Required file missing: '+name)
        plan=json.loads(z.read('HELDOUT_PLAN.json'))
        dig=sha(json.dumps(plan,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode('utf8'))
        if dig!=PINNED_PLAN_SHA:raise ValueError('Prespecified plan digest mismatch')
        if sha(z.read('HISTORICAL_POINTS_EXCLUSION_SOURCE.json'))!=PINNED_HISTORY:raise ValueError('Historical exclusions mismatch')
        cm=z.read('ct_metadata.json');pm=z.read('prediction_metadata.json')
        if sha(cm)!=PINNED_CT_META or sha(pm)!=PINNED_PRED_META:raise ValueError('Metadata changed')
        c=json.loads(cm);p=json.loads(pm)
        assert c['chunks']==[128,128,128] and p['chunks']==[192,192,192]
        assert c['shape']==p['shape']==[19416,7948,7948]
        assert c['fill_value']==p['fill_value']==0 and c['dtype']==p['dtype']=='|u1'
        assert c['order']==p['order']=='C'
        m=json.loads(z.read('manifest.json'))
        receipts=json.loads(z.read('receipts.json'))
        assert m['status']=='COMPLETE' and m['plan_sha256_canonical']==dig
        assert len(plan['sample'])==24 and len(m['samples'])==24 and len(m['ct_checks'])==186
        assert len(receipts)==212 and m['fresh_http_attempts']==212
        assert all(r['cache_hit'] is False for r in receipts)
        lut={(r['method'],r['url']):r for r in receipts}
        assert len(lut)==len(receipts)
        ctmap={q['key']:q for q in m['ct_checks']}
        assert len(ctmap)==186
        prediction_map={q['id']:q for q in m['samples']}
        assert len(prediction_map)==24
        out=[]; chunks=[]; checked_ct=set(); totalbytes=0
        for label,base,name,blob in [('ct',plan['ct_base_url'],'ct_metadata.json',cm),('prediction',plan['prediction_base_url'],'prediction_metadata.json',pm)]:
            rc=lut.get(('GET',base+'/.zarray'))
            assert rc and rc['http_status']==200 and rc['sha256']==sha(blob) and rc['length']==len(blob)
            assert m['metadata'][name]['sha256']==sha(blob)
            totalbytes+=len(blob)
        seen_preds=set()
        for s in plan['sample']:
            sid, key=s['id'],s['prediction_key']
            assert key not in seen_preds;seen_preds.add(key)
            record=prediction_map[sid]
            assert record['prediction_key']==key
            rc=lut.get(('GET',plan['prediction_base_url']+'/'+key))
            assert rc and rc['http_status']==record['http_status']
            assert record['state']==('PRESENT' if rc['http_status']==200 else 'ABSENT_404')
            starts=np.array(list(map(int,key.split('/'))))*192
            stops=np.minimum(starts+192,np.array(p['shape']))
            if record['state']=='PRESENT':
                file='raw/'+key.replace('/','_')+'.blosc'
                assert record['file']==file and file in names
                blob=z.read(file)
                assert sha(blob)==record['sha256']==rc['sha256'] and len(blob)==record['bytes']==rc['length']
                totalbytes+=len(blob)
                raw=blosc2.decompress(blob)
                assert len(raw)==192**3
                mask=np.frombuffer(raw,dtype='u1').reshape((192,192,192)) != 0
                pos=int(mask.sum(dtype=np.int64))
            else:
                mask=None
                pos=0
                assert record['bytes']==0
            # Derive native chunk partition independently with global Z,Y,X ranges.
            expected=np.zeros((192,192,192),dtype=np.uint8)
            states={'PRESENT':0,'ABSENT_404':0}
            ct_states=collections.Counter()
            for iz in range(starts[0]//128,(stops[0]-1)//128+1):
                for iy in range(starts[1]//128,(stops[1]-1)//128+1):
                    for ix in range(starts[2]//128,(stops[2]-1)//128+1):
                        ck=f'{iz}/{iy}/{ix}'
                        checked_ct.add(ck)
                        cr=ctmap.get(ck)
                        if cr is None:raise ValueError('Missing CT chunk: '+ck)
                        receipt=lut.get(('HEAD',plan['ct_base_url']+'/'+ck))
                        assert receipt and receipt['http_status']==cr['http_status']
                        assert cr['state']==('PRESENT' if receipt['http_status']==200 else 'ABSENT_404')
                        lo=np.maximum(starts,[iz*128,iy*128,ix*128])-starts
                        hi=np.minimum(stops,[(iz+1)*128,(iy+1)*128,(ix+1)*128])-starts
                        slices=tuple(slice(int(lo[i]),int(hi[i])) for i in range(3))
                        expected[slices]+=1
                        count=int(mask[slices].sum(dtype=np.int64)) if mask is not None else 0
                        states[cr['state']]+=count
                        ct_states[cr['state']]+=1
                        chunks.append({'id':sid,'prediction_key':key,'ct_chunk':ck,'ct_status':cr['state'],
                                       'partition_voxels':math.prod((hi-lo).tolist()),'positive_voxels':count})
            assert (expected==1).all(), ('CT partition incomplete/overlapped',sid)
            assert pos==sum(states.values()),('Positive partition mismatch',sid)
            out.append({'id':sid,'prediction_key':key,'stratum':s['stratum'],
                       'prediction_status':record['state'],'total_positive':pos,
                       'positive_in_stored_ct':states['PRESENT'],
                       'positive_in_absent_ct':states['ABSENT_404'],
                       'fraction_in_absent_ct':(states['ABSENT_404']/pos if pos else None),
                       'ct_chunks_present':ct_states['PRESENT'],'ct_chunks_absent':ct_states['ABSENT_404']})
        assert checked_ct==set(ctmap)
        assert totalbytes==m['fresh_get_bytes'], (totalbytes,m['fresh_get_bytes'])
        assert set(lut)==({('GET',plan['ct_base_url']+'/.zarray'),('GET',plan['prediction_base_url']+'/.zarray')} |
                 {('GET',plan['prediction_base_url']+'/'+s['prediction_key']) for s in plan['sample']} |
                 {('HEAD',plan['ct_base_url']+'/'+k) for k in checked_ct})
        grand=sum(s['total_positive'] for s in out)
        absent=sum(s['positive_in_absent_ct'] for s in out)
        result={'audit':'ARGUS 0.4.1 — Independent vectorized held-out verification',
                'status':'VERIFIED_FROM_ARCHIVED_SOURCE_BYTES_AND_HTTP_RECEIPTS',
                'capture_sha256':sha(Path(path).read_bytes()),
                'plan_sha256':dig,
                'capture_created_utc':m['created_utc'],
                'capture_finished_utc':m['finished_utc'],
                'cells_predeclared':len(out),
                'sample_frame_candidates':plan['candidate_cells_after_exclusion'],
                'prediction_chunks_stored':sum(x['prediction_status']=='PRESENT' for x in out),
                'prediction_chunks_not_stored':sum(x['prediction_status']=='ABSENT_404' for x in out),
                'nonzero_positive_prediction_voxels':grand,
                'positive_voxels_in_absent_ct_storage':absent,
                'positive_voxels_in_stored_ct_storage':grand-absent,
                'positive_fraction_in_absent_ct_storage':absent/grand,
                'distinct_ct_checks':len(ctmap),
                'distinct_ct_stored':sum(x['state']=='PRESENT' for x in ctmap.values()),
                'distinct_ct_absent':sum(x['state']=='ABSENT_404' for x in ctmap.values()),
                'fresh_request_receipts':len(receipts),
                'cells_positive_some_absent_ct':sum(x['positive_in_absent_ct']>0 for x in out),
                'cells_positive_all_absent_ct':sum(x['total_positive']>0 and x['positive_in_absent_ct']==x['total_positive'] for x in out),
                'cells':out}
        return result, chunks

def main():
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('capture',type=Path)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    report,chunks=audit(args.capture)
    args.out.mkdir(parents=True,exist_ok=True)
    (args.out/'INDEPENDENT_AUDIT.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    for name,rows in [('CASE_COUNTS.csv',report['cells']),('PARTITION_COUNTS.csv',chunks)]:
        with (args.out/name).open('w',newline='',encoding='utf8') as stream:
            writer=csv.DictWriter(stream,fieldnames=rows[0].keys());writer.writeheader();writer.writerows(rows)
    print('INDEPENDENT AUDIT: PASS',report['nonzero_positive_prediction_voxels'],report['positive_voxels_in_absent_ct_storage'])

if __name__=='__main__':main()
