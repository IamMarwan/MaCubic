import math
import unittest
from evalkit.metrics import retrieval_metrics,score,aggregate
from evalkit.providers import empty_prediction
from evalkit.runner import cost_for

class MetricsTests(unittest.TestCase):
    def setUp(self):
        self.docs={'d1':{'id':'d1','text':'Review status: Under review\nReviewer: Amal'}}
        self.facts={'d1':{'status':{'value':'Under review','quote':'Review status: Under review','aliases':['Pending review']}}}
        self.case={'task':'qa','expected':{'claims':[{'doc_id':'d1','field':'status','value':'Under review'}],'relevant_ids':['d1'],'abstain':False}}
    def prediction(self,value='Under review',citations=True):
        p=empty_prediction();p['claims']=[{'doc_id':'d1','field':'status','value':value,'citations':[{'doc_id':'d1','quote':'Review status: Under review'}] if citations else []}];return p
    def scored(self,p,error=False):return score(self.case,p,['d1'],self.docs,self.facts,3,error)
    def test_retrieval_hand_calculation(self):
        m=retrieval_metrics(['x','a','b'],['a','b'],3)
        self.assertEqual(m['retrieval_recall'],1)
        self.assertAlmostEqual(m['retrieval_precision'],2/3)
        self.assertEqual(m['mrr'],.5)
        self.assertAlmostEqual(m['ndcg'],(1/math.log2(3)+.5)/(1+1/math.log2(3)))
    def test_duplicate_retrieval_cannot_inflate_score(self):
        self.assertEqual(retrieval_metrics(['a','a','a'],['a','b'],3)['retrieval_recall'],.5)
    def test_no_relevant_document_is_na(self):
        self.assertIsNone(retrieval_metrics(['x'],[],3)['mrr'])
    def test_short_ranking_precision_denominator_is_k(self):
        self.assertEqual(retrieval_metrics(['a'],['a'],3)['retrieval_precision'],1/3)
    def test_correct_claim_and_citation(self):
        m,c=self.scored(self.prediction());self.assertEqual(m['answer_correctness'],1);self.assertEqual(c['supporting_citations'],1)
    def test_known_source_does_not_validate_false_answer(self):
        m,c=self.scored(self.prediction('Approved'));self.assertEqual(m['answer_correctness'],0);self.assertEqual(c['unsupported_claims'],1);self.assertEqual(c['supporting_citations'],0)
    def test_wrong_quote_is_not_support(self):
        p=self.prediction();p['claims'][0]['citations'][0]['quote']='Reviewer: Amal'
        _,c=self.scored(p);self.assertEqual(c['valid_citations'],1);self.assertEqual(c['supporting_citations'],0)
    def test_unknown_citation_is_invalid(self):
        p=self.prediction();p['claims'][0]['citations'][0]['doc_id']='invented'
        _,c=self.scored(p);self.assertEqual(c['valid_citations'],0)
    def test_uncited_truth_has_zero_citation_coverage(self):
        _,c=self.scored(self.prediction(citations=False));self.assertEqual(c['unsupported_claims'],0);self.assertEqual(c['cited_claims'],0)
    def test_alias_answers_are_accepted(self):
        m,_=self.scored(self.prediction('Pending review'));self.assertEqual(m['answer_correctness'],1)
    def test_abstention_on_answerable_question_fails(self):
        p=empty_prediction();p['abstain']=True;m,_=self.scored(p);self.assertEqual(m['answer_correctness'],0)
    def test_true_abstention_passes(self):
        self.case['expected'].update(claims=[],abstain=True);p=empty_prediction();p['abstain']=True
        m,c=self.scored(p);self.assertEqual(m['answer_correctness'],1);self.assertEqual(c['claims'],0)
    def test_error_cannot_pass_unanswerable_case(self):
        self.case['expected'].update(claims=[],abstain=True);m,_=self.scored(None,True);self.assertEqual(m['task_success'],0)
    def test_metadata_nulls_and_invented_values(self):
        case={'task':'metadata','expected':{'metadata':{'reviewer':None,'revision':'02'}}};p=empty_prediction();p['metadata'].update(reviewer='Amal',revision='2')
        m,c=score(case,p,[],self.docs,self.facts,3);self.assertEqual(m['metadata_accuracy'],0);self.assertEqual(c['metadata_fp'],2);self.assertEqual(c['metadata_fn'],1)
    def test_metadata_error_null_is_not_correct(self):
        case={'task':'metadata','expected':{'metadata':{'reviewer':None}}}
        m,c=score(case,None,[],self.docs,self.facts,3,True);self.assertEqual(m['metadata_accuracy'],0)
    def test_cost_cached_tokens_are_not_double_counted(self):
        c={'pricing':{'input_per_million':2,'output_per_million':8,'cached_input_per_million':.5}}
        self.assertAlmostEqual(cost_for({'input_tokens':1000,'output_tokens':500,'cached_input_tokens':200},c),.0057)
    def test_unknown_pricing_stays_unknown(self):
        self.assertIsNone(cost_for({'input_tokens':100,'output_tokens':10,'cached_input_tokens':0},{'pricing':None}))
    def test_zero_local_cost_is_not_a_positive_ratio(self):
        self.assertEqual(cost_for({'source':'local_no_llm'},{}),0)
    def test_unknown_cache_usage_requires_equal_rates(self):
        self.assertIsNone(cost_for({'input_tokens':10,'output_tokens':2,'cached_input_tokens':None},{'pricing':{'input_per_million':1,'output_per_million':1,'cached_input_per_million':.5}}))
if __name__=='__main__':unittest.main()
