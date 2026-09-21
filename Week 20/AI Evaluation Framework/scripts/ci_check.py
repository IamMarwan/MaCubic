"""Run the candidate and fail the process if configured quality gates fail."""
import argparse
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from evalkit.common import read_json,write_json
from evalkit.runner import evaluate
from evalkit.gates import check_gate
from evalkit.report import generate_report

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=ROOT/'outputs')
    p.add_argument('--config',type=Path,default=ROOT/'configs'/'candidate.json')
    p.add_argument('--rules',type=Path,default=ROOT/'configs'/'quality_gate.json')
    args=p.parse_args()
    run=evaluate(args.config,args.output)
    result=check_gate(run,read_json(args.rules))
    write_json(args.output/'quality_gate.json',dict(result,run_id=run['manifest']['run_id']))
    generate_report(args.output)
    print('Quality gate:', 'PASS' if result['passed'] else 'FAIL')
    for problem in result['problems']:print('-',problem)
    return 0 if result['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
