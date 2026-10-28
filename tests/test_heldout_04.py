import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

from tools.heldout_protocol import create_plan, verify_plan, canonical, known_keys
from tools.heldout_capture import run, metadata_is_expected, Fetch
from tools.heldout_verify import verify, raw_rect_positive
from argus_support.overlap import overlaps

ROOT=Path(__file__).resolve().parents[1]
HIST=(ROOT/'protocol/HISTORICAL_POINTS_EXCLUSION_SOURCE.json').read_bytes()
PLAN=create_plan(HIST)
RAW_ZIP=ROOT/'private_inputs_DO_NOT_PUBLISH/ARGUS_032_COMPARATOR_CAPTURE.zip' # Not required by tests


class FakeFetch:
    def __init__(self,fail_ct=False):
        import blosc2
        self.ct=(ROOT/'protocol/SOURCE_CT_ZARRAY.json').read_bytes()
        self.pred=(ROOT/'protocol/SOURCE_PREDICTION_ZARRAY.json').read_bytes()
        sample=bytearray(192**3)
        sample[:10000]=b'\xff'*10000
        self.raw=blosc2.compress(sample,clevel=1,codec=blosc2.Codec.ZSTD)
        self.fail_ct=fail_ct
        self.receipts=[];self.total_get_bytes=0
        self.calls=[]

    def request(self,url,method='GET'):
        self.calls.append((method,url))
        if url.endswith('/.zarray'):
            data=self.pred if '/representations/' in url else self.ct
            status=200
        elif method=='HEAD':
            status=503 if self.fail_ct and len([x for x in self.calls if x[0]=='HEAD'])==1 else 200
            data=b''
        else:
            status=200 if url.endswith('/'+PLAN['sample'][0]['prediction_key']) else 404
            data=self.raw if status==200 else b''
        if method=='GET':self.total_get_bytes+=len(data)
        self.receipts.append({'method':method,'url':url,'http_status':status,
                              'sha256':hashlib.sha256(data).hexdigest() if status==200 and method=='GET' else None,
                              'cache_hit':False})
        return status,data


class Heldout04Tests(unittest.TestCase):
    def test_lock_equal_to_distributed_digest(self):
        x=(ROOT/'protocol/HELDOUT_PLAN.sha256').read_text().split()[0]
        self.assertEqual(verify_plan(PLAN,HIST),x)
        self.assertEqual(PLAN,json.loads((ROOT/'protocol/HELDOUT_PLAN.json').read_text()))

    def test_no_selection_on_six_or_any_of_eighteen_prior_points(self):
        self.assertEqual(len(PLAN['sample']),24)
        self.assertEqual(len(set(p['prediction_key'] for p in PLAN['sample'])),24)
        forbidden=set(known_keys(json.loads(HIST)))
        self.assertFalse(forbidden.intersection(p['prediction_key'] for p in PLAN['sample']))
        self.assertEqual([sum(p['stratum']==i for p in PLAN['sample']) for i in range(3)],[8,8,8])

    def test_tampered_selection_is_rejected(self):
        fake=copy.deepcopy(PLAN)
        fake['sample'][0]['prediction_key']=fake['sample'][1]['prediction_key']
        with self.assertRaises(ValueError):verify_plan(fake,HIST)

    def test_metadata_exact_fingerprint(self):
        ct=(ROOT/'protocol/SOURCE_CT_ZARRAY.json').read_bytes()
        pred=(ROOT/'protocol/SOURCE_PREDICTION_ZARRAY.json').read_bytes()
        cm,pm=metadata_is_expected(ct,pred)
        self.assertEqual(cm['chunks'],[128]*3)
        self.assertEqual(pm['chunks'],[192]*3)
        with self.assertRaises(ValueError): metadata_is_expected(b'{}',pred)

    def test_capture_and_independent_verify_two_methods(self):
        with tempfile.TemporaryDirectory() as d:
            out=Path(d,'HOLDOUT.zip');network=FakeFetch()
            m=run(ROOT,out,network,log=lambda *x:None)
            self.assertEqual(m['status'],'COMPLETE')
            self.assertEqual(len(m['samples']),24)
            self.assertEqual(sum(x['state']=='PRESENT' for x in m['samples']),1)
            self.assertEqual(len({c['key'] for c in m['ct_checks']}),len(m['ct_checks']))
            self.assertFalse(any(x['cache_hit'] for x in network.receipts))
            report,parts=verify(out,ROOT)
            self.assertEqual(report['status'],'COMPLETE')
            self.assertEqual(report['sampled_cells'],24)
            self.assertEqual(report['positive_voxels'],10000)
            self.assertEqual(report['positive_voxels_in_absent_masked_ct_storage'],0)
            self.assertEqual(report['prediction_absent_404_cells'],23)
            self.assertEqual(sum(x['positive_voxels'] for x in parts),10000)
            self.assertEqual(len(report['cells']),24)

    def test_unknown_network_does_not_become_absence(self):
        with tempfile.TemporaryDirectory() as d:
            out=Path(d,'HOLDOUT.zip')
            m=run(ROOT,out,FakeFetch(fail_ct=True),log=lambda *x:None)
            self.assertEqual(m['status'],'PARTIAL_NETWORK_UNKNOWN')
            report,parts=verify(out,ROOT)
            self.assertEqual(report['status'],'PARTIAL')
            self.assertIsNone(report['fraction_of_positive_voxels_in_absent_ct_storage'])
            self.assertGreater(m['unknown_ct_chunks'],0)

    def test_mutating_ct_storage_status_without_receipt_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            original=Path(d,'base.zip'); tampered=Path(d,'tampered.zip')
            m=run(ROOT,original,FakeFetch(),log=lambda *x:None)
            with zipfile.ZipFile(original) as source, zipfile.ZipFile(tampered,'w') as dst:
                for name in source.namelist():
                    content=source.read(name)
                    if name=='manifest.json':
                        report=json.loads(content)
                        report['ct_checks'][0]['state']='ABSENT_404'
                        report['ct_checks'][0]['http_status']=404
                        content=json.dumps(report).encode()
                    dst.writestr(name,content)
            with self.assertRaisesRegex(ValueError,'CT storage state lacks matching HEAD receipt'):
                verify(tampered,ROOT)

    def test_exact_coverage_for_edge_rectangles(self):
        raw=bytes([1,0,1,1,0,0,1,0])
        self.assertEqual(raw_rect_positive(raw,[2,2,2],[0,0,0],[0,0,0],[1,1,1]),4)
        self.assertEqual(raw_rect_positive(raw,[2,2,2],[0,0,0],[1,0,0],[1,1,1]),1)

    def test_partial_metadata_failure_still_produces_zip(self):
        class BadFetch(FakeFetch):
            def request(self,url,method='GET'):
                if url.endswith('.zarray'):
                    self.receipts.append({'method':method,'url':url,'http_status':503})
                    return 503,b''
                return super().request(url,method)
        with tempfile.TemporaryDirectory() as d:
            out=Path(d,'HOLDOUT.zip');m=run(ROOT,out,BadFetch(),log=lambda *x:None)
            self.assertEqual(m['status'],'INCOMPLETE_ERROR')
            with zipfile.ZipFile(out) as z:
                self.assertIn('manifest.json',z.namelist())
                self.assertIn('receipts.json',z.namelist())
                self.assertTrue(json.loads(z.read('manifest.json'))['error_messages'])
            report,_=verify(out,ROOT)
            self.assertEqual(report['status'],'INCOMPLETE_NO_METADATA')

if __name__=='__main__':unittest.main()
