"""Frozen, unselected-in-advance held-out sample capture; stdlib only.

Always packages a manifest, including on metadata/network failures.
No downloads outside 24 frozen prediction chunk keys + intersecting CT heads.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import sys
import time
import urllib.error
import urllib.request
import zipfile

try:
    from argus_support.overlap import overlaps
    from argus_support.volume import validate
    from tools.heldout_protocol import canonical,verify_plan
except ImportError:
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
    from argus_support.overlap import overlaps
    from argus_support.volume import validate
    from tools.heldout_protocol import canonical,verify_plan

EXPECTED_CT_META_SHA='c754c949661243c8e60a4b3212d924882908f480c8249d8f9557eb83c84856c4'
EXPECTED_PRED_META_SHA='e94ae5d7a63dfbf5923a0030f3d2fe969383995acf02ffb60f73e72959e6319f'
MAX_DOWNLOAD = 12_000_000
MAX_TOTAL = 125_000_000


def utc():return datetime.now(timezone.utc).isoformat()
def sha(b):return hashlib.sha256(b).hexdigest()


class Fetch:
    def __init__(self,opener=None,timeout=25,retries=2):
        self.opener=opener or urllib.request.urlopen
        self.timeout=timeout;self.retries=retries
        self.receipts=[];self.total_get_bytes=0

    def request(self,url,method='GET'):
        if not url.startswith('https://vesuvius-challenge-open-data.s3.amazonaws.com/PHerc0211/'):
            raise ValueError('Refusing URL outside frozen PHerc0211 public dataset')
        for attempt in range(self.retries+1):
            status=None; data=b'';headers={};err=None
            try:
                req=urllib.request.Request(url,method=method,headers={
                    'User-Agent':'ARGUS-heldout-0.4-prespecified/20261022',
                    'Cache-Control':'no-cache'})
                with self.opener(req,timeout=self.timeout) as r:
                    status=r.status
                    headers={k:v for k,v in r.headers.items() if k.lower() in ('date','etag','last-modified','content-length')}
                    if method=='GET':
                        remaining=MAX_TOTAL-self.total_get_bytes
                        if remaining<=0:
                            raise ValueError('Run download budget exhausted')
                        data=r.read(min(MAX_DOWNLOAD,remaining)+1)
                        self.total_get_bytes+=len(data)
                        if len(data)>MAX_DOWNLOAD:
                            raise ValueError('Chunk response exceeds safety bound')
                        if self.total_get_bytes>MAX_TOTAL:
                            raise ValueError('Run download budget exceeded')
            except urllib.error.HTTPError as e:
                status=e.code;err=f'HTTP_{e.code}'
            except Exception as e:
                err=f'{type(e).__name__}: {e}'
                # A transport/size-policy failure is not a successful HTTP body.
                # Preserve the diagnostic, but never return stale status 200.
                status=None;data=b''
            row={'observed_utc':utc(),'method':method,'url':url,'http_status':status,
                 'status':'OK' if status==200 else 'ABSENT_404' if status==404 else 'UNKNOWN',
                 'attempt':attempt+1,'length':len(data),'sha256':sha(data) if method=='GET' and status==200 else None,
                 'response_headers':headers,'error':err,'cache_hit':False}
            self.receipts.append(row)
            if err and err.startswith('ValueError:'):
                return -1,b''
            if status in (200,404):return status,data
            if status not in (408,429,500,502,503,504,None) or attempt==self.retries:
                return status or -1,b''
            time.sleep(min(2**attempt,3))
        return -1,b''


def metadata_is_expected(ct_bytes,pred_bytes):
    if sha(ct_bytes)!=EXPECTED_CT_META_SHA or sha(pred_bytes)!=EXPECTED_PRED_META_SHA:
        raise ValueError('Zarr metadata does not match previously frozen source SHA256')
    ct=json.loads(ct_bytes); pred=json.loads(pred_bytes)
    validate(ct);validate(pred)
    if ct['shape']!=pred['shape'] or ct['chunks'] != [128,128,128] or pred['chunks'] != [192,192,192]:
        raise ValueError('Source grids/chunks unexpectedly changed')
    if ct['dtype']!='|u1' or pred['dtype']!='|u1' or ct['order']!='C' or pred['order']!='C':
        raise ValueError('Unexpected Zarr dtype/order')
    if ct.get('dimension_separator')!='/' or pred.get('dimension_separator')!='/':
        raise ValueError('Unexpected Zarr key separator')
    if ct.get('fill_value')!=0 or pred.get('fill_value')!=0:
        raise ValueError('Expected zero-fill missing chunks')
    if pred.get('compressor',{}).get('id')!='blosc':
        raise ValueError('Expected Blosc prediction codec')
    return ct,pred


def capture(plan,historical_bytes,fetch,zf,log=print):
    manifest={'artifact':'ARGUS_0_4_BLIND_HELDOUT_CAPTURE','created_utc':utc(),
              'status':'STARTED','plan_sha256_canonical':verify_plan(plan,historical_bytes),
              'samples':[],'ct_checks':[],'metadata':{},'error_messages':[],
              'interpretation':'Stored Zarr chunk objects only; same-grid registration and physical support unverified'}
    ctbase=plan['ct_base_url'];predbase=plan['prediction_base_url']
    try:
        sources=[]
        for name,base in [('ct_metadata.json',ctbase),('prediction_metadata.json',predbase)]:
            code,blob=fetch.request(base+'/.zarray')
            if code!=200:
                raise RuntimeError(f'{name} returned {code}; cannot safely interpret Zarr chunk keys')
            zf.writestr(name,blob)
            manifest['metadata'][name]={'sha256':sha(blob),'bytes':len(blob)}
            sources.append(blob)
        ctmeta,predmeta=metadata_is_expected(*sources)
        all_ct=set()
        for p in plan['sample']:
            all_ct.update(c['ct_key'] for c in overlaps(p['prediction_key'],ctmeta,predmeta)['ct_candidates'])
        # Run CT inventory for ALL frozen cells, including absent prediction keys.
        log(f'Predeclared prediction cells: {len(plan["sample"])}; unique CT chunks: {len(all_ct)}')
        for n,p in enumerate(plan['sample'],1):
            k=p['prediction_key'];code,blob=fetch.request(predbase+'/'+k)
            row={'id':p['id'],'prediction_key':k,'http_status':code,
                 'state':'PRESENT' if code==200 else 'ABSENT_404' if code==404 else 'UNKNOWN',
                 'sha256':sha(blob) if code==200 else None,'bytes':len(blob)}
            if code==200:
                fname='raw/'+k.replace('/','_')+'.blosc';zf.writestr(fname,blob);row['file']=fname
            manifest['samples'].append(row)
            log(f'  prediction {n:02}/{len(plan["sample"])}  {k}: {row["state"]}')
        for i,k in enumerate(sorted(all_ct,key=lambda x:tuple(map(int,x.split('/')))),1):
            code,_=fetch.request(ctbase+'/'+k,'HEAD')
            state='PRESENT' if code==200 else 'ABSENT_404' if code==404 else 'UNKNOWN'
            manifest['ct_checks'].append({'key':k,'http_status':code,'state':state})
            if i%20==0 or i==len(all_ct):log(f'  CT checks {i}/{len(all_ct)}')
        unk_pred=sum(x['state']=='UNKNOWN' for x in manifest['samples'])
        unk_ct=sum(x['state']=='UNKNOWN' for x in manifest['ct_checks'])
        manifest['status']='COMPLETE' if unk_ct==0 and unk_pred==0 else 'PARTIAL_NETWORK_UNKNOWN'
    except Exception as exc:
        manifest['status']='INCOMPLETE_ERROR'
        manifest['error_messages'].append(type(exc).__name__+': '+str(exc))
    finally:
        manifest['finished_utc']=utc()
        manifest['fresh_http_attempts']=len(fetch.receipts)
        manifest['fresh_get_bytes']=fetch.total_get_bytes
        manifest['unknown_predictions']=sum(x['state']=='UNKNOWN' for x in manifest['samples'])
        manifest['unknown_ct_chunks']=sum(x['state']=='UNKNOWN' for x in manifest['ct_checks'])
        zf.writestr('manifest.json',json.dumps(manifest,indent=2)+'\n')
        zf.writestr('receipts.json',json.dumps(fetch.receipts,indent=2)+'\n')
    return manifest


def run(root,out,fetch=None,log=print):
    root=Path(root)
    prior=(root/'protocol/HISTORICAL_POINTS_EXCLUSION_SOURCE.json').read_bytes()
    plan=json.loads((root/'protocol/HELDOUT_PLAN.json').read_bytes())
    expected=(root/'protocol/HELDOUT_PLAN.sha256').read_text().split()[0]
    digest=verify_plan(plan,prior)
    if digest!=expected:raise ValueError('HELDOUT_PLAN SHA256 mismatch; regenerate only before measurements')
    out=Path(out);out.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(out,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        z.writestr('HELDOUT_PLAN.json',json.dumps(plan,indent=2)+'\n')
        z.writestr('HISTORICAL_POINTS_EXCLUSION_SOURCE.json',prior)
        r=capture(plan,prior,fetch or Fetch(),z,log)
    log('Result status:',r['status'])
    log('Upload:',out.resolve())
    return r


def main():
    p=argparse.ArgumentParser();p.add_argument('--root',default=str(Path(__file__).resolve().parents[1]));p.add_argument('--output',default='ARGUS_04_HELDOUT_CAPTURE.zip');p.add_argument('--dry-run',action='store_true')
    args=p.parse_args()
    try:
        if args.dry_run:
            root=Path(args.root);r=json.loads((root/'protocol/HELDOUT_PLAN.json').read_text())
            verify_plan(r,(root/'protocol/HISTORICAL_POINTS_EXCLUSION_SOURCE.json').read_bytes())
            print('DRY RUN, no network. Locked cells:',len(r['sample']))
            print('\n'.join(p['id']+' '+p['prediction_key'] for p in r['sample']))
            return 0
        m=run(args.root,args.output)
        return 0 if m['status']=='COMPLETE' else 1
    except Exception as exc:
        # Fail closed with log zip even if plan integrity check fails.
        print('ERROR:',type(exc).__name__,exc)
        diagnostic=Path(args.output)
        if diagnostic.exists():
            diagnostic=diagnostic.with_name(diagnostic.stem+'_error_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')+'.zip')
        diagnostic.parent.mkdir(parents=True,exist_ok=True)
        with zipfile.ZipFile(diagnostic,'x') as z:
            z.writestr('FATAL_ERROR.txt',type(exc).__name__+': '+str(exc)+'\n')
        print('Diagnostic ZIP:',diagnostic.resolve())
        return 1

if __name__=='__main__':sys.exit(main())
