import unittest
from evalkit.gates import check_gate
class GateTests(unittest.TestCase):
    def base(self):return {'status':'completed','manifest':{'split':'test'},'summary':{'cases':70,'accuracy':.9,'errors':0}}
    def test_passing_metrics(self):self.assertTrue(check_gate(self.base(),{'minimum_cases':70,'minimum':{'accuracy':.85}})['passed'])
    def test_regression_fails(self):self.assertFalse(check_gate(self.base(),{'minimum':{'accuracy':.95}})['passed'])
    def test_missing_metric_fails(self):self.assertFalse(check_gate(self.base(),{'minimum':{'missing':.8}})['passed'])
    def test_incomplete_run_fails(self):
        b=self.base();b['status']='interrupted';self.assertFalse(check_gate(b,{})['passed'])
    def test_small_sample_fails(self):self.assertFalse(check_gate(self.base(),{'minimum_cases':100})['passed'])
if __name__=='__main__':unittest.main()
