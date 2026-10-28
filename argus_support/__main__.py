import argparse
import csv
import datetime
import hashlib
import json
from pathlib import Path
import platform
import time
from . import __version__
from .audit import audit, OFFSETS
from .geometry import file_hash, load_map
from .transport import Transport
from .volume import Volume

CT_URL = ('https://vesuvius-challenge-open-data.s3.amazonaws.com/PHerc0211/volumes/'
          '20250821151803-9.362um-1.2m-113keV-masked.zarr/0')


def clean(value):
    import math
    if isinstance(value,float) and not math.isfinite(value):
        return None
    if isinstance(value,dict):
        return {k:clean(v) for k,v in value.items()}
    if isinstance(value,(list,tuple)):
        return [clean(v) for v in value]
    return value


def main(argv=None):
    p = argparse.ArgumentParser(description='Observe native CT support; no papyrus/ink inference.')
    source = p.add_mutually_exclusive_group(required=True)
    source.add_argument('--points',type=Path,help='JSON with NATIVE_CT_ZYX and points[].zyx')
    source.add_argument('--map',type=Path,help='NPZ coordinate maps and mask, including frozen R04 arena')
    source.add_argument('--tifxyz',type=Path,help='Use installed upstream vesuvius.tifxyz at stored resolution')
    p.add_argument('--tifxyz-grid-assertion',help='Provenance that tifxyz coordinates refer to selected native CT')
    p.add_argument('--mask-key',default='region12_mask')
    p.add_argument('--limit',type=int,default=0,help='0: all masked pixels; otherwise fixed stratified subset')
    p.add_argument('--controls',type=int,default=0)
    p.add_argument('--seed',type=int,default=1729)
    p.add_argument('--ct-url',default=CT_URL,help='Native Zarr v2 array URL or local folder, including level')
    p.add_argument('--prediction-url')
    p.add_argument('--prediction-grid-assertion',help='Required provenance that prediction uses the CT native grid')
    p.add_argument('--decode-prediction',action='store_true')
    p.add_argument('--mode',choices=['chunk-only','voxel','surface-support'],default='surface-support')
    p.add_argument('--radius',type=int,default=2)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--cache',type=Path)
    p.add_argument('--offline',action='store_true')
    p.add_argument('--retries',type=int,default=2)
    p.add_argument('--timeout',type=float,default=20)
    p.add_argument('--budget-mb',type=float,default=128)
    p.add_argument('--max-requests',type=int,default=200)
    p.add_argument('--expected-ct-metadata-sha256',help='Fail if metadata differs from a prior reviewed run')
    a = p.parse_args(argv)
    if a.radius not in range(0,5) or a.retries not in range(0,6) or min(a.limit,a.controls) < 0 or a.budget_mb <= 0 or a.max_requests < 1 or a.timeout <= 0:
        p.error('Invalid radius, selection, retry, timeout or budget setting')
    if a.prediction_url and not a.prediction_grid_assertion:
        p.error('--prediction-grid-assertion is required; array shape alone does not establish registration')
    if a.tifxyz and not a.tifxyz_grid_assertion:
        p.error('--tifxyz-grid-assertion must identify the native CT coordinate provenance')
    a.out.mkdir(parents=True,exist_ok=True)
    if (a.out/'report.json').exists():
        p.error('Output report exists; choose a new output directory')
    started = time.perf_counter()
    transport = Transport(a.cache,a.offline,a.retries,a.timeout,int(a.budget_mb*1_000_000),a.max_requests)
    provenance = {'version':__version__, 'python':platform.python_version(),
        'code_sha256':hashlib.sha256(b''.join(f.name.encode()+f.read_bytes() for f in
            sorted(Path(__file__).parent.glob('*.py')))).hexdigest(),
        'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'ct_url':a.ct_url, 'prediction_url':a.prediction_url,
        'prediction_grid_assertion':a.prediction_grid_assertion,
        'tifxyz_grid_assertion':a.tifxyz_grid_assertion,
        'protocol':{'offsets_vox':OFFSETS, 'radius':a.radius,'mode':a.mode,
                    'rounding':'nearest voxel; half upward; coordinates checked before rounding',
                    'normal_length_range':[0.7,1.3], 'normal_action':'normalize stored XYZ, reverse to ZYX',
                    'seed':a.seed,'controls':a.controls,'limit':a.limit,
                    'byte_budget':int(a.budget_mb*1_000_000),'max_requests':a.max_requests,
                    'retries':a.retries,'timeout_seconds':a.timeout,'offline':a.offline}}
    try:
        if a.tifxyz:
            from .tifxyz import load_tifxyz
            if a.controls:
                raise ValueError('tifxyz controls require an explicit independently selected point file')
            src = load_tifxyz(a.tifxyz,a.limit)
        else:
            src = load_map(a.map,a.mask_key,a.limit,a.controls,a.seed) if a.map else json.loads(a.points.read_text(encoding='utf8'))
        if src.get('coordinate_system') != 'NATIVE_CT_ZYX' or not src.get('points'):
            raise ValueError('Input must declare NATIVE_CT_ZYX and contain points')
        if len(src['points']) > 100_000:
            raise ValueError('Point budget exceeds 100000')
        provenance['input_sha256'] = src['source_sha256'] if a.tifxyz else file_hash(a.map or a.points)
        provenance['input_geometry'] = src.get('geometry')
        ct = Volume(a.ct_url,transport)
        if a.expected_ct_metadata_sha256 and ct.metadata_sha256 != a.expected_ct_metadata_sha256:
            raise ValueError('CT_METADATA_CHANGED: reviewed metadata hash does not match')
        prediction = Volume(a.prediction_url,transport,a.decode_prediction) if a.prediction_url else None
        if prediction and prediction.meta['shape'] != ct.meta['shape']:
            raise ValueError('Prediction/CT native shapes differ; explicit transform required')
        provenance['ct_metadata'] = ct.meta
        provenance['ct_metadata_sha256'] = ct.metadata_sha256
        if prediction:
            provenance['prediction_metadata'] = prediction.meta
            provenance['prediction_metadata_sha256'] = prediction.metadata_sha256
        report = audit(src['points'],ct,prediction,a.mode,a.radius,a.decode_prediction)
    except Exception as exc:
        report = {'status':'FAILED', 'error':type(exc).__name__+': '+str(exc), 'points':[], 'gate_7f':'BLOCKED'}
    report['provenance'] = provenance
    report['transport'] = {'requests':transport.requests,'download_bytes':transport.bytes,'receipts':transport.receipts}
    report['elapsed_seconds'] = time.perf_counter()-started
    (a.out/'report.json').write_text(json.dumps(clean(report),indent=2,allow_nan=False)+'\n',encoding='utf8')
    with (a.out/'points.csv').open('w',newline='',encoding='utf8') as stream:
        writer = csv.writer(stream)
        writer.writerow(['id','group','z','y','x','ct_state','ct_value','neighborhood_complete','nonzero_fraction','stability','geometry_state'])
        for r in report['points']:
            n = r['ct'].get('neighborhood',{})
            writer.writerow([r.get('id'),r.get('group'),*r.get('zyx',[None]*3),r['ct']['state'],r['ct'].get('value'),
                             n.get('complete'),n.get('nonzero_fraction'),r.get('stability'),r['geometry_state']])
    files = sorted(a.out.glob('*'))
    (a.out/'SHA256.txt').write_text(''.join(file_hash(f)+'  '+f.name+'\n' for f in files if f.is_file()),encoding='utf8')
    print(json.dumps({k:report.get(k) for k in ('status','ct_state_counts','stability_counts','elapsed_seconds','error')}))
    return 0 if report['status']=='OBSERVATIONS_COMPLETED' else 2


if __name__ == '__main__':
    raise SystemExit(main())
