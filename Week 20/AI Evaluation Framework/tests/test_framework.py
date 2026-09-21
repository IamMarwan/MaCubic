import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from evalkit.common import ROOT,load_dataset,read_json,write_json
from evalkit.runner import evaluate,paired_compare
from evalkit.report import generate_report
from evalkit.storage import History
from evalkit.providers import ProviderError

class FrameworkTests(unittest.TestCase):
    def test_dataset_integrity_and_split_counts(self):
        docs,cases,_,training=load_dataset(ROOT/'data')
        self.assertEqual(len(cases),105);self.assertEqual(sum(c['split']=='test' for c in cases),70)
        self.assertEqual(len(docs),30);self.assertEqual(len(training),40)
    def test_all_local_configurations_run_and_persist(self):
        with tempfile.TemporaryDirectory() as tmp:
            runs=[evaluate(ROOT/'configs'/f'{c}.json',tmp) for c in ['baseline','retrieval_only','policy_only','candidate']]
            self.assertTrue(all(r['summary']['errors']==0 for r in runs))
            self.assertTrue(all(r['summary']['cases']==70 for r in runs))
            self.assertTrue(all(r['summary']['input_tokens']==0 for r in runs))
            self.assertIsNone(runs[0]['summary']['successful_cases_per_usd'])
            h=History(Path(tmp)/'history.sqlite3')
            self.assertEqual(len(h.list()),4);h.close()
            compare=paired_compare(runs[0],runs[1]);self.assertEqual(compare['pairs'],70)
            path=generate_report(tmp);self.assertTrue(path.exists());self.assertTrue((Path(tmp)/'summary.csv').exists())
    def test_errors_are_persisted_and_score_zero(self):
        with tempfile.TemporaryDirectory() as tmp,patch('evalkit.runner.LocalProvider.predict',side_effect=ProviderError('Deliberate test failure')):
            r=evaluate(ROOT/'configs'/'candidate.json',tmp,limit=10)
            self.assertEqual(r['summary']['errors'],10);self.assertEqual(r['summary']['task_success'],0)
            self.assertEqual(r['status'],'completed_with_errors')
    def test_different_samples_cannot_be_compared(self):
        with tempfile.TemporaryDirectory() as tmp:
            a=evaluate(ROOT/'configs'/'baseline.json',tmp,limit=2);b=evaluate(ROOT/'configs'/'candidate.json',tmp,limit=3)
            with self.assertRaises(ValueError):paired_compare(a,b)
    def test_changed_benchmark_cannot_be_compared(self):
        with tempfile.TemporaryDirectory() as tmp:
            a=evaluate(ROOT/'configs'/'baseline.json',tmp,limit=3);b=json.loads(json.dumps(a));b['manifest']['benchmark_hash']='changed'
            with self.assertRaises(ValueError):paired_compare(a,b)
    def test_report_neutralizes_script_injection(self):
        with tempfile.TemporaryDirectory() as tmp:
            r=evaluate(ROOT/'configs'/'baseline.json',tmp,limit=3)
            r['manifest']['prompt']='</script><script>alert(1)</script>'
            write_json(Path(tmp)/'runs'/'x.json',r)
            html=generate_report(tmp).read_text()
            self.assertNotIn('</script><script>alert(1)</script>',html)
            payload=html.split('<script id="data" type="application/json">')[1].split('</script>')[0]
            parsed=json.loads(payload);self.assertTrue(any(x['manifest']['prompt'].startswith('</script>') for x in parsed))
    def test_replay_round_trip_scores_equal(self):
        with tempfile.TemporaryDirectory() as tmp:
            r=evaluate(ROOT/'configs'/'candidate.json',tmp)
            bundle={'benchmark_hash':r['manifest']['benchmark_hash'],'model':'recorded-local-test','records':[{'case_id':x['case_id'],'prediction':x['prediction'],'retrieved_ids':x['retrieved_ids'],'latency_ms':x['latency_ms'],'usage':x['usage']} for x in r['rows']]}
            path=Path(tmp)/'predictions.json';write_json(path,bundle)
            config=Path(tmp)/'replay.json';write_json(config,{'id':'replay_test','provider':'replay','retrieval':'bm25','top_k':3,'predictions_file':str(path)})
            replay=evaluate(config,tmp)
            self.assertEqual(replay['summary']['task_success'],r['summary']['task_success'])
            self.assertEqual(replay['manifest']['evidence_type'],'imported_unverified')
            with self.assertRaises(ValueError):paired_compare(r,replay)
    def test_history_appends_identical_configuration(self):
        with tempfile.TemporaryDirectory() as tmp:
            a=evaluate(ROOT/'configs'/'baseline.json',tmp,limit=2);b=evaluate(ROOT/'configs'/'baseline.json',tmp,limit=2)
            self.assertNotEqual(a['manifest']['run_id'],b['manifest']['run_id'])
            h=History(Path(tmp)/'history.sqlite3');self.assertEqual(len(h.list()),2);h.close()
if __name__=='__main__':unittest.main()
