"""Evaluate configuration snapshots against a fixed split and persist every result."""
import json
import os
import platform
import random
import re
import time
import uuid
from datetime import datetime,timezone
from pathlib import Path
from .common import ROOT, read_json, write_json, digest, public_input, load_dataset, code_hash, finite_number
from .metrics import score,aggregate,VERSION
from .providers import LocalProvider,OpenAIProvider,ReplayProvider,ProviderError,validate_prediction,validate_usage
from .retrieval import Retriever
from .storage import History


def cost_for(usage,config):
    if usage.get('source')=='local_no_llm': return 0.0
    rates=config.get('pricing')
    if not rates: return None
    inp,out,cached=(usage.get(k) for k in ('input_tokens','output_tokens','cached_input_tokens'))
    if inp is None or out is None: return None
    a,b,c=(rates.get(k) for k in ('input_per_million','output_per_million','cached_input_per_million'))
    if a is None or b is None: return None
    if cached is None:
        # Unless equal prices are explicit, unknown cache usage makes cost unknown.
        if c!=a: return None
        cached=0
    if cached and c is None: return None
    return ((inp-cached)*a+cached*(c or 0)+out*b)/1_000_000


def resolve_config(path):
    config=read_json(path)
    if not re.fullmatch(r'[a-zA-Z0-9_-]+',config.get('id','')): raise ValueError('Unsafe configuration ID')
    if config.get('provider') not in ('local','openai','replay'): raise ValueError('Unknown provider')
    if type(config.get('top_k')) is not int or not 1<=config['top_k']<=50: raise ValueError('top_k must be 1..50')
    if config['provider']=='local' and config.get('extraction_policy') not in ('basic','grounded'): raise ValueError('Unknown extraction policy')
    if config.get('retrieval') not in ('tfidf','bm25','vectors'): raise ValueError('Unknown retrieval')
    if config['provider']=='openai':
        config['model']=config.get('model') or os.environ.get(config.get('model_env','OPENAI_MODEL'))
        if not config['model']: raise ValueError('Set model environment variable before running')
    for key in ('vectors_file','predictions_file','prompt_file'):
        if key in config: config[key]=str((ROOT/config[key]).resolve())
    if config.get('pricing'):
        for key in ('input_per_million','output_per_million','cached_input_per_million'):
            value=config['pricing'].get(key)
            if value is not None and (not finite_number(value) or value<0): raise ValueError('Invalid pricing')
    return config


def evaluate(config_path,output,data=None,split='test',limit=None,seed=20):
    config=resolve_config(config_path);output=Path(output)
    docs,cases,facts,training=load_dataset(data or ROOT/'data')
    benchmark_hash=digest({'corpus':docs,'cases':cases,'facts':facts,'training':training})
    selected=[c for c in cases if c['split']==split]
    if not selected: raise ValueError('Empty split')
    # Stable case sample across configurations, with deterministic processing order.
    random.Random(seed).shuffle(selected)
    if limit is not None:
        if limit<1: raise ValueError('limit must be positive')
        selected=selected[:limit]
    prompt=Path(config['prompt_file']).read_text(encoding='utf-8') if config.get('prompt_file') else ''
    started=time.perf_counter()
    retriever=Retriever(docs,config['retrieval'],config.get('vectors_file'))
    if config['provider']=='local': provider=LocalProvider(config,training)
    elif config['provider']=='openai': provider=OpenAIProvider(config,prompt)
    else: provider=ReplayProvider(config,benchmark_hash)
    setup_ms=(time.perf_counter()-started)*1000
    now=datetime.now(timezone.utc)
    run_id=now.strftime('%Y%m%dT%H%M%S')+'-'+config['id']+'-'+uuid.uuid4().hex[:8]
    manifest={'run_id':run_id,'created_at':now.isoformat(),'config':config,'config_hash':digest(config),
              'prompt':prompt,'prompt_hash':digest(prompt),'benchmark_hash':benchmark_hash,'code_hash':code_hash(),
              'metric_version':VERSION,'split':split,'case_ids':[c['id'] for c in selected],
              'sample_hash':digest(sorted(c['id'] for c in selected)),'seed':seed,
              'python':platform.python_version(),'platform':platform.platform(),'setup_ms':setup_ms,
              'evidence_type':'measured_local' if config['provider']=='local' else ('live_api' if config['provider']=='openai' else 'imported_unverified'),
              'latency_scope':'retrieval and prediction; setup excluded' if config['provider']!='replay' else 'imported original latency; replay I/O excluded',
              'embedding_provenance':{k:v for k,v in (retriever.embedding or {}).items() if k not in ('documents','queries')}}
    history=History(output/'history.sqlite3');history.start(manifest)
    rows=[]
    try:
        for case in selected:
            inp=public_input(case,docs);start=time.perf_counter();ranked=[];prediction=None;error=None;raw={}
            usage={'input_tokens':None,'output_tokens':None,'cached_input_tokens':None,'source':'unavailable'}
            retrieval_ms=0.0
            try:
                t=time.perf_counter()
                if case['task']=='qa':
                    if config['provider']=='replay':
                        ranked=provider.records[case['id']].get('retrieved_ids',[])
                        if not isinstance(ranked,list) or any(not isinstance(d,str) for d in ranked): raise ValueError('Invalid imported ranking')
                        if len(ranked)!=len(set(ranked)): raise ValueError('Duplicate imported ranking')
                        if any(d not in docs for d in ranked): raise ValueError('Unknown imported ranking document')
                        ranked=ranked[:config['top_k']]
                    else: ranked=[r['doc_id'] for r in retriever.search(inp['question'],config['top_k'],case['id'])]
                retrieval_ms=(time.perf_counter()-t)*1000
                prediction,usage,raw=provider.predict(inp,[docs[d] for d in ranked])
                validate_prediction(prediction);validate_usage(usage)
            except Exception as exc:
                error=f'{type(exc).__name__}: {str(exc)[:240]}'
                if isinstance(exc,ProviderError): usage=exc.usage;raw=exc.raw
            measured_ms=(time.perf_counter()-start)*1000
            latency=raw.get('original_latency_ms') if config['provider']=='replay' else measured_ms
            metrics,counts=score(case,prediction,ranked,docs,facts,config['top_k'],bool(error))
            row={'case_id':case['id'],'task':case['task'],'tags':case['tags'],'input':inp,'expected':case['expected'],
                 'retrieved_ids':ranked,'context_documents':[docs[d] for d in ranked],'prediction':prediction,'error':error,'metrics':metrics,'counts':counts,
                 'latency_ms':latency,'retrieval_ms':retrieval_ms if config['provider']!='replay' else None,
                 'usage':usage,'estimated_cost_usd':cost_for(usage,config),'provider_metadata':raw}
            rows.append(row);history.record(run_id,row)
        summary=aggregate(rows)
        summary['slices']={tag:aggregate([r for r in rows if tag in r['tags']])['task_success'] for tag in sorted({t for r in rows for t in r['tags']})}
        status='completed' if not summary['errors'] else 'completed_with_errors'
        history.finish(run_id,summary,status)
        bundle={'manifest':manifest,'status':status,'summary':summary,'rows':rows}
        write_json(output/'runs'/f'{run_id}.json',bundle)
        return bundle
    except BaseException:
        history.finish(run_id,aggregate(rows),'interrupted')
        raise
    finally: history.close()


def paired_compare(a,b,metric='task_success',iterations=2000):
    ma,mb=a['manifest'],b['manifest']
    for key in ('benchmark_hash','sample_hash','split','metric_version','code_hash'):
        if ma[key]!=mb[key]: raise ValueError(f'Incomparable runs: {key} differs')
    if ma['evidence_type']!=mb['evidence_type']: raise ValueError('Do not compare different evidence types')
    if ma['config']['top_k']!=mb['config']['top_k'] and metric in ('retrieval_recall','retrieval_precision','mrr','ndcg'):
        raise ValueError('Retrieval k differs')
    ar={r['case_id']:r['metrics'].get(metric) for r in a['rows']}
    br={r['case_id']:r['metrics'].get(metric) for r in b['rows']}
    diffs=[br[k]-ar[k] for k in sorted(ar) if ar[k] is not None and br[k] is not None]
    if not diffs: raise ValueError('Metric has no eligible paired cases')
    rng=random.Random(20)
    samples=sorted(sum(rng.choices(diffs,k=len(diffs)))/len(diffs) for _ in range(iterations))
    return {'metric':metric,'delta':sum(diffs)/len(diffs),'ci95':[samples[int(iterations*.025)],samples[min(iterations-1,int(iterations*.975))]],
            'pairs':len(diffs),'method':'paired case bootstrap; synthetic/template-correlated cases, exploratory only'}
