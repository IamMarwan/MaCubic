import json
import tempfile
import unittest
from pathlib import Path
from evalkit.common import ROOT,load_dataset,public_input,FIELDS,digest,write_json
from evalkit.providers import extract,empty_prediction,validate_prediction,validate_usage,LocalProvider,OpenAIProvider,ProviderError,ReplayProvider
from evalkit.retrieval import Retriever

class ProviderTests(unittest.TestCase):
    def test_alternate_labels(self):
        text='Reference: RFI-104\nRev: 02\nChecked by: Amal'
        self.assertEqual(extract(text,'grounded')[0]['revision'],'02')
        self.assertIsNone(extract(text,'basic')[0]['revision'])
    def test_conflicting_values_abstain(self):
        self.assertIsNone(extract('Rev: 01\nRevision: 02')[0]['revision'])
    def test_missing_metadata_never_invented(self):
        self.assertIsNone(extract('Nothing here')[0]['reviewer'])
    def test_public_input_excludes_expected_answers(self):
        docs,cases,_,_=load_dataset(ROOT/'data');case=cases[0]
        case['expected']['secret']='DO_NOT_SEND_THIS'
        self.assertNotIn('DO_NOT_SEND_THIS',json.dumps(public_input(case,docs)))
        self.assertNotIn('expected',public_input(case,docs))
    def test_duplicate_claims_rejected(self):
        p=empty_prediction();c={'doc_id':'d','field':'x','value':'y','citations':[]};p['claims']=[c,c]
        with self.assertRaises(ValueError):validate_prediction(p)
    def test_abstention_and_claim_rejected(self):
        p=empty_prediction();p['abstain']=True;p['claims']=[{'doc_id':'d','field':'x','value':'y','citations':[]}]
        with self.assertRaises(ValueError):validate_prediction(p)
    def test_invalid_usage_rejected(self):
        with self.assertRaises(ValueError):validate_usage({'input_tokens':1,'output_tokens':-1})
        with self.assertRaises(ValueError):validate_usage({'input_tokens':1,'cached_input_tokens':2})
    def mock_api(self,raw,capture=None):
        def transport(payload):
            if capture is not None:capture.append(payload)
            return raw
        return OpenAIProvider({'model':'transport-test-model'},'Instruction',transport)
    def raw(self,p=None,status='completed'):
        return {'id':'mock','model':'transport-test-model','status':status,'usage':{'input_tokens':110,'output_tokens':30,'input_tokens_details':{'cached_tokens':10}},
                'output':[{'type':'message','content':[{'type':'output_text','text':json.dumps(p or empty_prediction())}]}]}
    def test_responses_adapter_schema_and_usage(self):
        capture=[];p,u,m=self.mock_api(self.raw(),capture).predict({'task':'qa'},[])
        self.assertEqual(u['output_tokens'],30);self.assertEqual(u['cached_input_tokens'],10)
        self.assertTrue(capture[0]['text']['format']['strict']);self.assertFalse(capture[0]['store'])
    def test_incomplete_response_preserves_usage(self):
        with self.assertRaises(ProviderError) as context:self.mock_api(self.raw(status='incomplete')).predict({},[])
        self.assertEqual(context.exception.usage['output_tokens'],30)
    def test_bad_json_preserves_usage(self):
        raw=self.raw();raw['output'][0]['content'][0]['text']='not json'
        with self.assertRaises(ProviderError) as context:self.mock_api(raw).predict({},[])
        self.assertEqual(context.exception.usage['input_tokens'],110)
    def test_missing_usage_is_unknown(self):
        raw=self.raw();raw.pop('usage');_,u,_=self.mock_api(raw).predict({},[])
        self.assertIsNone(u['input_tokens'])
    def test_title_removed_for_api_classification(self):
        capture=[];self.mock_api(self.raw(),capture).predict({'task':'classification','omit_title':True,'document':{'id':'d','text':'SECRET TITLE\nbody'}},[])
        self.assertNotIn('SECRET TITLE',capture[0]['input'])
    def test_vector_ranking_and_hash_validation(self):
        docs={'a':{'id':'a','text':'one'},'b':{'id':'b','text':'two'}}
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'v.json';data={'corpus_hash':digest(docs),'dimensions':2,'model':'test_vectors','documents':{'a':[1,0],'b':[0,1]},'queries':{'q':{'question_hash':digest('query'),'vector':[0,1]}}};write_json(path,data)
            r=Retriever(docs,'vectors',path);self.assertEqual(r.search('query',1,'q')[0]['doc_id'],'b')
            with self.assertRaises(ValueError):r.search('changed query',1,'q')
            data['corpus_hash']='bad';write_json(path,data)
            with self.assertRaises(ValueError):Retriever(docs,'vectors',path)
    def test_nonfinite_vectors_rejected(self):
        docs={'a':{'id':'a','text':'one'}}
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'v.json';path.write_text(json.dumps({'corpus_hash':digest(docs),'dimensions':1,'documents':{'a':[float('nan')]},'queries':{}}))
            with self.assertRaises(ValueError):Retriever(docs,'vectors',path)
    def test_replay_requires_correct_benchmark(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'p.json';write_json(path,{'benchmark_hash':'different','records':[]})
            with self.assertRaises(ValueError):ReplayProvider({'predictions_file':str(path)},'current')
if __name__=='__main__':unittest.main()
