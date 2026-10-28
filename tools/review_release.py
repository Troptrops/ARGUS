"""Independent archived-evidence review. No ARGUS counting code is imported.

Usage: python tools/review_release.py CAPTURE.zip --out OUTPUT
Requires numpy and blosc2. Does not access a network.
"""
import argparse
from collections import Counter
import csv
import hashlib
from itertools import product
import json
import math
from pathlib import Path
import struct
import zipfile
import blosc2
import numpy as np

CT_SHA = 'c754c949661243c8e60a4b3212d924882908f480c8249d8f9557eb83c84856c4'
PRED_SHA = 'e94ae5d7a63dfbf5923a0030f3d2fe969383995acf02ffb60f73e72959e6319f'
PLAN_SHA = 'a8bcb68978589f8314952f64e8243d556628bcf76a038bf371f077aa20964d97'
H11_SHA = '28676496bf281c635598ca4d3816dce9890ef5e7a03121207ab73280e17ec1c7'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def canonical(obj):
    return json.dumps(obj,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode()


def decode(blob, metadata):
    require(metadata['dtype']=='|u1' and metadata['order']=='C', 'Unsupported prediction layout')
    require(not metadata.get('filters') and metadata['compressor']['id']=='blosc','Unsupported filter/codec')
    raw = blosc2.decompress(blob)
    require(len(raw)==math.prod(metadata['chunks']),'Decoded chunk length mismatch')
    a = np.frombuffer(raw,dtype=np.uint8).reshape(tuple(metadata['chunks']))
    require(int(np.count_nonzero(a))==len(raw)-raw.count(0),'Independent nonzero counters disagree')
    return a


def partition(key, cm, pm):
    require(cm['shape']==pm['shape'],'Nominal array shapes differ')
    origin = np.array([int(v)*c for v,c in zip(key.split('/'),pm['chunks'])])
    stop = np.minimum(origin+pm['chunks'],cm['shape'])
    require(bool(np.all(stop>origin)),'Invalid prediction key')
    cells = []
    for idx in product(*(range(int(lo//c),int((hi-1)//c)+1) for lo,hi,c in zip(origin,stop,cm['chunks']))):
        start = np.maximum(origin,np.array(idx)*cm['chunks'])-origin
        end = np.minimum(stop,(np.array(idx)+1)*cm['chunks'])-origin
        cells.append(('/'.join(map(str,idx)),tuple(slice(int(a),int(b)) for a,b in zip(start,end))))
    return origin,cells


def count_case(identifier, key, arr, cm, pm, states):
    origin,cells = partition(key,cm,pm)
    shape = tuple(pm['chunks'])
    coverage = np.zeros(shape,dtype=np.uint8)
    gap = np.zeros(shape,dtype=bool)
    counts = Counter()
    rows = []
    for ctkey,slices in cells:
        require(ctkey in states,'Missing CT observation '+ctkey)
        state = states[ctkey]
        require(state in ('PRESENT','ABSENT_404'),'Unknown CT state cannot be absence')
        coverage[slices] += 1
        if state == 'ABSENT_404':
            gap[slices] = True
        n = int(np.count_nonzero(arr[slices])) if arr is not None else 0
        counts[state] += n
        rows.append({'id':identifier,'prediction_key':key,'ct_key':ctkey,'ct_state':state,'positive_voxels':n})
    valid_shape = tuple(int(min(c,n-o)) for c,n,o in zip(pm['chunks'],pm['shape'],origin))
    valid_slices = tuple(slice(0,n) for n in valid_shape)
    require(bool(np.all(coverage[valid_slices]==1)),'Partition not exact')
    total = int(np.count_nonzero(arr[valid_slices])) if arr is not None else 0
    require(total==sum(counts.values()),'Positive counts fail reconciliation')
    result = {'id':identifier,'prediction_key':key,'total_positive':total,
        'positive_in_absent_ct':counts['ABSENT_404'],'positive_in_stored_ct':counts['PRESENT']}
    return result,rows,gap


def review_heldout(path):
    with zipfile.ZipFile(path) as z:
        require(z.testzip() is None,'Bad ZIP CRC')
        require(len(z.namelist())==len(set(z.namelist())),'Duplicate archive names')
        plan=json.loads(z.read('HELDOUT_PLAN.json'))
        hist=z.read('HISTORICAL_POINTS_EXCLUSION_SOURCE.json')
        require(sha(canonical(plan))==PLAN_SHA,'Plan hash mismatch')
        require(sha(hist)==plan['prior_18_point_survey_sha256'],'Historical hash mismatch')
        history=json.loads(hist)
        excluded={'/'.join(str(int(v)//c) for v,c in zip(p['zyx'],plan['prediction_chunk_shape'])) for p in history['points']}
        require(set(plan['excluded_prior_prediction_keys'])==excluded,'Exclusions changed')
        frame=plan['frame_half_open_zyx']; chunks=plan['prediction_chunk_shape']
        candidates=[]
        for idx in product(*(range(frame[axis][0]//c,(frame[axis][1]-1)//c+1) for axis,c in zip(('z','y','x'),chunks))):
            key='/'.join(map(str,idx))
            if key not in excluded:candidates.append((idx,key))
        regenerated=[]
        for stratum,(low,high) in enumerate(plan['strata_z_chunk_ranges']):
            group=[(idx,key) for idx,key in candidates if low<=idx[0]<=high]
            group.sort(key=lambda pair:(sha((plan['seed']+'|'+pair[1]).encode()),pair[1]))
            for _,key in group[:plan['sample_per_stratum']]:
                regenerated.append({'id':f'H{len(regenerated):02}','prediction_key':key,'stratum':stratum})
        require(regenerated==plan['sample'] and len(candidates)==423,'Selection cannot be regenerated')
        m=json.loads(z.read('manifest.json')); receipts=json.loads(z.read('receipts.json'))
        require(m['status']=='COMPLETE' and m['plan_sha256_canonical']==PLAN_SHA,'Incomplete or wrong-plan capture')
        lookup={(r['method'],r['url']):r for r in receipts}
        require(len(lookup)==len(receipts) and all(not r.get('cache_hit') for r in receipts),'Nonunique/cached receipts')
        require(len(receipts)==m['fresh_http_attempts']==212,'Receipt count mismatch')
        cmraw=z.read('ct_metadata.json'); pmraw=z.read('prediction_metadata.json')
        require(sha(cmraw)==CT_SHA and sha(pmraw)==PRED_SHA,'Metadata fingerprints differ')
        cm,pm=json.loads(cmraw),json.loads(pmraw)
        for base,raw,name in [(plan['ct_base_url'],cmraw,'ct_metadata.json'),(plan['prediction_base_url'],pmraw,'prediction_metadata.json')]:
            rc=lookup[('GET',base+'/.zarray')]
            require(rc['http_status']==200 and rc['sha256']==sha(raw) and rc['length']==len(raw),'Metadata receipt mismatch')
            require(m['metadata'][name]['sha256']==sha(raw),'Manifest metadata hash mismatch')
        states={}
        for row in m['ct_checks']:
            rc=lookup[('HEAD',plan['ct_base_url']+'/'+row['key'])]
            require(rc['http_status']==row['http_status'] and rc['http_status'] in (200,404),'CT receipt/status mismatch')
            state='PRESENT' if rc['http_status']==200 else 'ABSENT_404'
            require(state==row['state'],'CT state contradicts receipt')
            require(row['key'] not in states,'Duplicate CT keys')
            states[row['key']]=state
        require(len(states)==186,'CT inventory incomplete')
        samplemap={r['id']:r for r in m['samples']}
        require(len(samplemap)==len(m['samples'])==24,'Missing/duplicate samples')
        results=[]; partitions=[]; h11=None; ct_used=set()
        totalbytes=len(cmraw)+len(pmraw)
        for chosen in plan['sample']:
            item=samplemap[chosen['id']];key=chosen['prediction_key']
            require(item['prediction_key']==key,'Sample key changed')
            rc=lookup[('GET',plan['prediction_base_url']+'/'+key)]
            require(rc['http_status']==item['http_status'] and rc['http_status'] in (200,404),'Prediction receipt mismatch')
            require(item['state']==('PRESENT' if rc['http_status']==200 else 'ABSENT_404'),'Prediction state mismatch')
            arr=None
            if rc['http_status']==200:
                require(item['file']=='raw/'+key.replace('/','_')+'.blosc','Wrong raw member')
                blob=z.read(item['file'])
                require(sha(blob)==item['sha256']==rc['sha256'],'Raw source hash mismatch')
                require(len(blob)==item['bytes']==rc['length'],'Raw source byte-length mismatch')
                arr=decode(blob,pm);totalbytes+=len(blob)
            else:require(item['bytes']==0,'Missing object has nonzero payload')
            result,parts,gap=count_case(chosen['id'],key,arr,cm,pm,states)
            result.update(stratum=chosen['stratum'],prediction_status=item['state'])
            results.append(result);partitions.extend(parts);ct_used.update(p['ct_key'] for p in parts)
            if chosen['id']=='H11':
                require(arr is not None,'H11 source missing')
                slab=np.zeros_like(arr,dtype=bool);slab[128:192,176:192,:]=True
                mask=(arr!=0)&gap
                require(bool(np.array_equal(mask,slab)),'H11 absent-storage positives are not exactly the slab')
                require(sha(z.read(item['file']))==H11_SHA,'H11 fingerprint changed')
                h11={'chunk_key':key,'compressed_sha256':H11_SHA,'total_positive':result['total_positive'],
                    'positive_in_absent_ct':result['positive_in_absent_ct'],
                    'positive_in_stored_ct':result['positive_in_stored_ct'],
                    'local_bounds_zyx_half_open':[[128,192],[176,192],[0,192]],
                    'native_bounds_zyx_half_open':[[18560,18624],[6320,6336],[4416,4608]],
                    'positive_in_absent_storage_mask_equals_slab':True,
                    'entire_positive_mask_equals_slab':bool(np.array_equal(arr!=0,slab)),
                    'slab_voxels':int(slab.sum()),'label_values':np.unique(arr).tolist()}
        require(ct_used==set(states),'Extraneous or missing CT keys')
        require(totalbytes==m['fresh_get_bytes'],'Total captured bytes differ')
        total=sum(r['total_positive'] for r in results);absent=sum(r['positive_in_absent_ct'] for r in results)
        return {'capture_sha256':sha(Path(path).read_bytes()),'plan_sha256':PLAN_SHA,
            'selection_regenerated':True,'external_preregistration_attestation':False,
            'capture_timestamps_locally_recorded':[m['created_utc'],m['finished_utc']],
            'candidate_cells':len(candidates),'cells':results,'stored_prediction_chunks':sum(r['prediction_status']=='PRESENT' for r in results),
            'absent_prediction_chunks':sum(r['prediction_status']=='ABSENT_404' for r in results),
            'positive_voxels':total,'positive_in_absent_ct':absent,'positive_in_stored_ct':total-absent,
            'absent_share':absent/total,'ct_states':dict(Counter(states.values())),
            'receipts':len(receipts),'h11':h11},partitions


def review_six(path):
    with zipfile.ZipFile(path) as z:
        require(z.testzip() is None,'Six-case CRC failure')
        m=json.loads(z.read('manifest.json'));rcs=m['receipts']
        for name,digest in m['files_sha256'].items():
            require(sha(z.read(name))==digest,'Six-case source hash differs '+name)
        cm=json.loads(z.read('ct_metadata.json'));pm=json.loads(z.read('prediction_metadata.json'))
        require(sha(z.read('ct_metadata.json'))==CT_SHA and sha(z.read('prediction_metadata.json'))==PRED_SHA,'Six-case metadata mismatch')
        ct={r['url'].split('/0/',1)[-1]:('PRESENT' if r['status']==200 else 'ABSENT_404' if r['status']==404 else 'UNKNOWN') for r in rcs if r['method']=='HEAD'}
        if 'plan.json' in z.namelist():
            plan=json.loads(z.read('plan.json'))
            require(sha(json.dumps(plan,sort_keys=True).encode())==m['predeclared_plan_sha256'],'Comparator canonical hash mismatch')
            cases=[{'id':p['id'],'prediction_key':p['prediction_chunk']} for p in plan['comparator_cases']]
        else:
            report=json.loads(z.read('source_report.json'))
            require(sha(json.dumps(report,sort_keys=True).encode())==m['source_report_sha256'],'Flagged canonical source-report hash mismatch')
            cases=[{'id':p['case_id'],'prediction_key':p['prediction_key']} for p in report['cases']]
        results=[]
        for case in cases:
            blob=z.read('prediction_'+case['id']+'.blosc')
            matching=[r for r in rcs if r['method']=='GET' and r['url'].endswith('/'+case['prediction_key'])]
            require(len(matching)==1 and matching[0]['status']==200 and matching[0]['sha256']==sha(blob),'Six-case prediction receipt mismatch')
            arr=decode(blob,pm)
            result,_,_=count_case(case['id'],case['prediction_key'],arr,cm,pm,ct)
            results.append(result)
        return {'archive_sha256':sha(Path(path).read_bytes()),'cases':results,'receipt_entries':len(rcs)}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('capture',type=Path)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    result,parts=review_heldout(args.capture)
    args.out.mkdir(parents=True,exist_ok=True)
    (args.out/'RELEASE_REPLAY.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    for name,rows in [('RELEASE_CELLS.csv',result['cells']),('RELEASE_PARTITIONS.csv',parts)]:
        with (args.out/name).open('w',newline='',encoding='utf8') as stream:
            writer=csv.DictWriter(stream,fieldnames=rows[0].keys());writer.writeheader();writer.writerows(rows)
    print(json.dumps({k:result[k] for k in ('positive_voxels','positive_in_absent_ct','positive_in_stored_ct','stored_prediction_chunks','absent_prediction_chunks','h11')}))

if __name__=='__main__':main()
