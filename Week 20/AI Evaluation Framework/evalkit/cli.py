"""Command-line workflow. Every command works from the project root."""
import argparse
import json
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from .common import ROOT,read_json,write_json,load_dataset,digest,public_input
from .runner import evaluate,paired_compare
from .report import generate_report
from .storage import History

def main(argv=None):
    parser=argparse.ArgumentParser(description='Week 20 AI Evaluation Framework')
    sub=parser.add_subparsers(dest='command',required=True)
    for name in ('run','demo'):
        p=sub.add_parser(name)
        if name=='run':p.add_argument('--config',required=True,type=Path)
        p.add_argument('--output',type=Path,default=ROOT/'outputs')
        p.add_argument('--split',choices=['dev','test'],default='test')
        p.add_argument('--limit',type=int)
        p.add_argument('--seed',type=int,default=20)
    for name in ('report','history','serve'):
        p=sub.add_parser(name);p.add_argument('--output',type=Path,default=ROOT/'outputs')
        if name=='serve':p.add_argument('--port',type=int,default=8000)
    p=sub.add_parser('compare');p.add_argument('baseline',type=Path);p.add_argument('candidate',type=Path)
    p.add_argument('--metric',default='task_success')
    p=sub.add_parser('validate')
    p=sub.add_parser('export-inputs');p.add_argument('--output',type=Path,default=ROOT/'outputs'/'public_inputs.json')
    p.add_argument('--split',choices=['dev','test'],default='test')
    args=parser.parse_args(argv)
    if args.command in ('run','demo'):
        paths=[args.config] if args.command=='run' else [ROOT/'configs'/f'{name}.json' for name in ['baseline','retrieval_only','policy_only','candidate']]
        results=[]
        for path in paths:
            result=evaluate(path,args.output,split=args.split,limit=args.limit,seed=args.seed)
            results.append(result)
            print(f'{result["manifest"]["config"]["id"]}: {result["summary"]["cases"]} cases; success {result["summary"]["task_success"]:.1%}; errors {result["summary"]["errors"]}')
        print('Dashboard:',generate_report(args.output))
        if args.command=='demo':
            comparisons={name:paired_compare(results[0],results[i]) for name,i in [('retrieval_only',1),('policy_only',2),('candidate',3)]}
            write_json(args.output/'paired_comparisons.json',comparisons)
        return 1 if any(r['summary']['errors'] for r in results) else 0
    if args.command=='validate':
        docs,cases,facts,training=load_dataset(ROOT/'data')
        print(f'Valid: {len(docs)} documents, {len(cases)} cases, {len(training)} training examples.')
    elif args.command=='report':print(generate_report(args.output))
    elif args.command=='history':
        h=History(args.output/'history.sqlite3')
        try: print(json.dumps(h.list(),indent=2))
        finally:h.close()
    elif args.command=='compare':print(json.dumps(paired_compare(read_json(args.baseline),read_json(args.candidate),args.metric),indent=2))
    elif args.command=='export-inputs':
        docs,cases,facts,training=load_dataset(ROOT/'data')
        # Hash covers hidden gold for identity; answers themselves are omitted.
        write_json(args.output,{'benchmark_hash':digest({'corpus':docs,'cases':cases,'facts':facts,'training':training}),
                    'corpus_hash':digest(docs),'corpus':docs,
                    'cases':[public_input(c,docs) for c in cases if c['split']==args.split]})
        print(args.output)
    elif args.command=='serve':
        handler=partial(SimpleHTTPRequestHandler,directory=str(args.output.resolve()))
        print(f'Open http://127.0.0.1:{args.port}/comparison.html',flush=True)
        server=ThreadingHTTPServer(('127.0.0.1',args.port),handler)
        try:server.serve_forever()
        except KeyboardInterrupt:pass
        finally:server.server_close()
    return 0
