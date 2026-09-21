"""Explicit denominators, abstentions, errors and source-grounded atomic scoring."""
import math
from collections import Counter
from .common import norm, mean, LABELS

VERSION='1.0.0'

def same(value,annotation):
    return norm(value) in {norm(annotation['value']),*(norm(x) for x in annotation.get('aliases',[]))}

def retrieval_metrics(ranked,relevant,k):
    ranked=list(dict.fromkeys(ranked))[:k]
    relevant=set(relevant)
    if not relevant: return {key:None for key in ('retrieval_recall','retrieval_precision','mrr','ndcg')}
    hits=[int(d in relevant) for d in ranked]
    dcg=sum(h/math.log2(i+2) for i,h in enumerate(hits))
    ideal=sum(1/math.log2(i+2) for i in range(min(k,len(relevant))))
    return {'retrieval_recall':sum(hits)/len(relevant),'retrieval_precision':sum(hits)/k,
            'mrr':next((1/(i+1) for i,h in enumerate(hits) if h),0.0),'ndcg':dcg/ideal}

def score(case,prediction,ranked,docs,facts,k,error=False):
    task=case['task'];gold=case['expected']
    m={'task_success':0.0 if error else None}
    counts={'claims':0,'unsupported_claims':0,'citations':0,'valid_citations':0,'supporting_citations':0,
            'cited_claims':0,'expected_claims':len(gold.get('claims',[])),'correct_cited_claims':0,
            'metadata_slots':0,'metadata_correct':0,'metadata_tp':0,'metadata_fp':0,'metadata_fn':0}
    if task=='qa':
        m.update(retrieval_metrics(ranked,gold.get('relevant_ids',[]),k))
        m.update({'answer_correctness':0.0,'answer_f1':0.0,'abstention_correctness':0.0})
        if error: return m,counts
        claims=prediction['claims'];counts['claims']=len(claims)
        expected={(c['doc_id'],c['field']):c for c in gold['claims']}
        correct=0
        for c in claims:
            key=(c['doc_id'],c['field'])
            ann=facts.get(c['doc_id'],{}).get(c['field'])
            supported=ann is not None and ann['value'] is not None and same(c['value'],ann)
            counts['unsupported_claims']+=not supported
            is_correct=key in expected and same(c['value'],facts[key[0]][key[1]])
            correct+=is_correct
            any_cite=False
            for cite in c['citations']:
                counts['citations']+=1
                valid=cite['doc_id'] in docs
                counts['valid_citations']+=valid
                # Source existence is insufficient: the quote must contain the annotated field line.
                good=bool(valid and supported and cite['doc_id']==c['doc_id'] and cite['quote'] and
                          cite['quote'] in docs[cite['doc_id']]['text'] and ann['quote'] in cite['quote'])
                counts['supporting_citations']+=good
                any_cite=any_cite or good
            counts['cited_claims']+=any_cite
            counts['correct_cited_claims']+=is_correct and any_cite
        exact=(correct==len(expected)==len(claims)) and prediction['abstain']==gold['abstain']
        m['answer_correctness']=float(exact)
        m['answer_f1']=2*correct/(len(expected)+len(claims)) if expected or claims else float(prediction['abstain'])
        m['abstention_correctness']=float(prediction['abstain']==gold['abstain'])
        m['task_success']=float(exact)
    elif task=='metadata':
        counts['metadata_slots']=len(gold['metadata'])
        for field,value in gold['metadata'].items():
            p=None if error else prediction['metadata'].get(field)
            equal=not error and norm(p)==norm(value)
            counts['metadata_correct']+=equal
            counts['metadata_tp']+=equal and value is not None
            counts['metadata_fn']+=value is not None and not equal
            counts['metadata_fp']+=p is not None and not equal
        m['metadata_accuracy']=counts['metadata_correct']/counts['metadata_slots']
        m['task_success']=float(m['metadata_accuracy']==1)
    else:
        m['classification_accuracy']=float(not error and prediction['label']==gold['label'])
        m['task_success']=m['classification_accuracy']
    return m,counts

def percentile(values,p):
    values=sorted(values)
    if not values: return None
    position=(len(values)-1)*p;lo=int(position);hi=min(lo+1,len(values)-1)
    return values[lo]+(values[hi]-values[lo])*(position-lo)

def aggregate(rows):
    keys=set(k for row in rows for k in row['metrics'])
    result={key:mean([r['metrics'].get(key) for r in rows]) for key in sorted(keys)}
    result['denominators']={key:sum(r['metrics'].get(key) is not None for r in rows) for key in sorted(keys)}
    total=Counter()
    for row in rows: total.update(row['counts'])
    for name,num,den in [('hallucination_rate','unsupported_claims','claims'),('citation_accuracy','supporting_citations','citations'),
                         ('citation_validity','valid_citations','citations'),('citation_coverage','cited_claims','claims'),
                         ('gold_citation_recall','correct_cited_claims','expected_claims'),('metadata_micro_accuracy','metadata_correct','metadata_slots')]:
        result[name]=total[num]/total[den] if total[den] else None
        result['denominators'][name]=total[den]
    den=2*total['metadata_tp']+total['metadata_fp']+total['metadata_fn']
    result['metadata_f1']=2*total['metadata_tp']/den if den else None
    labels=sorted({r['expected'].get('label') for r in rows if r['task']=='classification'})
    confusion={label:{p:0 for p in LABELS+['unknown','error']} for label in labels}
    for r in rows:
        if r['task']=='classification':
            p='error' if r['error'] else r['prediction']['label'] or 'unknown'
            confusion[r['expected']['label']][p]+=1
    f1=[]
    for label in labels:
        tp=confusion[label][label];fp=sum(confusion[g][label] for g in labels if g!=label)
        fn=sum(confusion[label].values())-tp
        f1.append(2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else 0.0)
    result['classification_macro_f1']=mean(f1)
    result['confusion_matrix']=confusion
    latencies=[r['latency_ms'] for r in rows if r['latency_ms'] is not None]
    result.update({'latency_mean_ms':mean(latencies),'latency_p50_ms':percentile(latencies,.5),
                   'latency_p95_ms':percentile(latencies,.95),'cases':len(rows),'errors':sum(bool(r['error']) for r in rows),
                   'count_totals':dict(total)})
    for key in ('input_tokens','output_tokens','cached_input_tokens'):
        values=[r['usage'].get(key) for r in rows]
        result[key]=sum(v for v in values if v is not None) if all(v is not None for v in values) else None
        result['known_'+key]=sum(v for v in values if v is not None)
    costs=[r['estimated_cost_usd'] for r in rows]
    result['estimated_cost_usd']=sum(costs) if all(x is not None for x in costs) else None
    result['known_cost_usd']=sum(x for x in costs if x is not None)
    successes=sum(r['metrics']['task_success'] for r in rows)
    cost=result['estimated_cost_usd']
    result['successful_cases_per_usd']=successes/cost if cost is not None and cost>0 else None
    result['cost_per_success_usd']=cost/successes if cost is not None and successes else None
    return result
