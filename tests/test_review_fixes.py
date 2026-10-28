import copy
import io
from pathlib import Path
import tempfile
import json
import zipfile
import unittest
from unittest.mock import patch

from tools.heldout_capture import Fetch,run
from argus_support.overlap import overlaps,classify
from argus_support.prediction_support import count_chunk_prediction_support


class Response(io.BytesIO):
    status=200
    headers={}


class ReviewFixTests(unittest.TestCase):
    def test_oversize_http_200_never_success(self):
        with patch('tools.heldout_capture.MAX_DOWNLOAD',8):
            f=Fetch(opener=lambda *a,**k:Response(b'X'*20),retries=0)
            status,data=f.request('https://vesuvius-challenge-open-data.s3.amazonaws.com/PHerc0211/test')
        self.assertEqual((status,data),(-1,b''))
        self.assertEqual(f.receipts[-1]['status'],'UNKNOWN')
        self.assertNotEqual(f.receipts[-1]['http_status'],200)

    def test_total_byte_budget_never_success(self):
        with patch('tools.heldout_capture.MAX_TOTAL',4):
            f=Fetch(opener=lambda *a,**k:Response(b'X'*8),retries=0)
            self.assertEqual(f.request('https://vesuvius-challenge-open-data.s3.amazonaws.com/PHerc0211/test'),(-1,b''))
            self.assertIsNone(f.receipts[-1]['sha256'])

    def test_capture_does_not_overwrite_existing_archive(self):
        from test_heldout_04 import ROOT,FakeFetch
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'existing.zip';path.write_bytes(b'original evidence')
            with self.assertRaises(FileExistsError):run(ROOT,path,FakeFetch(),log=lambda *a:None)
            self.assertEqual(path.read_bytes(),b'original evidence')

    def test_unknown_overlap_state_not_proof_of_absence(self):
        case={'ct_candidates':[{'ct_key':'0/0/0','intersection_voxels':8}],'prediction_voxels':8}
        result=classify(case,{'0/0/0':'UNKNOWN'})
        self.assertEqual(result['storage_status'],'UNRESOLVED_OVERLAP')
        self.assertEqual(result['ct_stored_coverage_upper_bound'],1)

    def case(self):
        meta={'zarr_format':2,'shape':[2,2,2],'chunks':[2,2,2],'dtype':'|u1','order':'C',
              'compressor':None,'filters':None,'dimension_separator':'/'}
        c={**meta,'chunks':[1,2,2]}
        case={'id':'fixture',**overlaps('0/0/0',c,meta)}
        for r in case['ct_candidates']:r['state']='PRESENT'
        return meta,case

    def test_duplicate_partition_cannot_pass_equal_volume(self):
        meta,case=self.case()
        case['ct_candidates'][1]=copy.deepcopy(case['ct_candidates'][0])
        with self.assertRaisesRegex(ValueError,'Overlapping'):
            count_chunk_prediction_support(bytes(8),meta,case)

    def test_unknown_zero_positive_partition_still_partial(self):
        meta,case=self.case()
        case['ct_candidates'][0]['state']='INDETERMINATE'
        result=count_chunk_prediction_support(bytes(8),meta,case)
        self.assertEqual(result['classification'],'PARTIAL_STORAGE_PARTITION')

    def test_zero_positive_unknown_cannot_hide_behind_manifest_complete(self):
        from test_heldout_04 import ROOT,FakeFetch,PLAN
        from tools.heldout_verify import verify
        cm=json.loads((ROOT/'protocol/SOURCE_CT_ZARRAY.json').read_bytes())
        pm=json.loads((ROOT/'protocol/SOURCE_PREDICTION_ZARRAY.json').read_bytes())
        far=overlaps(PLAN['sample'][-1]['prediction_key'],cm,pm)['ct_candidates'][0]['ct_key']
        class FarFailure(FakeFetch):
            def request(self,url,method='GET'):
                status,data=super().request(url,method)
                if method=='HEAD' and url.endswith('/'+far):
                    self.receipts[-1]['http_status']=503
                    return 503,b''
                return status,data
        with tempfile.TemporaryDirectory() as folder:
            original=Path(folder)/'partial.zip';changed=Path(folder)/'changed.zip'
            run(ROOT,original,FarFailure(),log=lambda *a:None)
            with zipfile.ZipFile(original) as source,zipfile.ZipFile(changed,'w') as dest:
                for name in source.namelist():
                    data=source.read(name)
                    if name=='manifest.json':
                        m=json.loads(data);m['status']='COMPLETE';data=json.dumps(m).encode()
                    dest.writestr(name,data)
            report,_=verify(changed,ROOT)
            self.assertEqual(report['positive_voxels_in_unknown_masked_ct_storage'],0)
            self.assertEqual(report['status'],'PARTIAL')


if __name__=='__main__':unittest.main()
