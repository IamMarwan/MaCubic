import io
import json
import sys
import unittest
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from evalkit.common import write_json
if __name__=='__main__':
    stream=io.StringIO()
    suite=unittest.defaultTestLoader.discover(str(ROOT/'tests'))
    result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
    print(stream.getvalue())
    path=ROOT/'outputs'/'test_report.json'
    write_json(path,{'timestamp':datetime.now(timezone.utc).isoformat(),'tests_run':result.testsRun,
                'failures':len(result.failures),'errors':len(result.errors),'skipped':len(result.skipped),'passed':result.wasSuccessful(),
                'transcript':stream.getvalue()})
    raise SystemExit(0 if result.wasSuccessful() else 1)
