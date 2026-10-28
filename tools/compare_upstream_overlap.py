"""Run only a pinned upstream pure function on the same 24 local cells.

No network requests, upstream catalog execution or CT-intensity cleanup occurs.
Supply the upstream clean_predictions.py file pinned in UPSTREAM_SOURCE_RECORD.json.
"""
import argparse,ast,hashlib,json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from argus_support.overlap import overlaps


def main():
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True)
    p.add_argument('--package',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();record=json.loads((a.package/'09_REFERENCES/UPSTREAM_SOURCE_RECORD.json').read_text())
    source_record=next(x for x in record['files'] if x['file']=='tools/clean_predictions.py')
    source=a.source.read_bytes()
    if hashlib.sha256(source).hexdigest()!=source_record['sha256']:
        raise ValueError('Source does not match the reviewed upstream commit')
    tree=ast.parse(source)
    function=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='overlapping_vol_chunks')
    namespace={};exec(compile(ast.Module(body=[function],type_ignores=[]),'<pinned upstream pure function>','exec'),namespace)
    root=Path(__file__).resolve().parents[1]
    cm=json.loads((root/'protocol/SOURCE_CT_ZARRAY.json').read_bytes())
    pm=json.loads((root/'protocol/SOURCE_PREDICTION_ZARRAY.json').read_bytes())
    plan=json.loads((root/'protocol/HELDOUT_PLAN.json').read_bytes());matches=0
    for cell in plan['sample']:
        key=cell['prediction_key'];native=tuple(map(int,key.split('/')))
        existing=set(namespace['overlapping_vol_chunks'](native,pm['chunks'],cm['chunks']))
        ours={tuple(x['ct_index']) for x in overlaps(key,cm,pm)['ct_candidates']}
        matches+=existing==ours
    result={'scope':'Pinned upstream pure overlap function only; no full upstream tool or CT-intensity cleanup run',
        'commit':record['commit'],'file':'tools/clean_predictions.py','function':'overlapping_vol_chunks',
        'cells_compared':len(plan['sample']),'exact_chunk_key_set_agreement':matches,
        'timings_not_comparable_to_end_to_end_tools':True}
    a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))


if __name__=='__main__':main()
