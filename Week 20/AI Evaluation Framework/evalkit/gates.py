"""Small explicit regression gate: missing data never passes a threshold."""
from .common import finite_number

def check_gate(bundle,rules):
    problems=[]
    summary=bundle['summary']
    if bundle['status']!='completed': problems.append('Run is not completed without errors')
    if summary['cases']<rules.get('minimum_cases',1): problems.append('Too few cases')
    if bundle['manifest']['split']!=rules.get('split','test'): problems.append('Wrong benchmark split')
    for metric,threshold in rules.get('minimum',{}).items():
        value=summary.get(metric)
        if not finite_number(value) or value<threshold: problems.append(f'{metric}: {value} < required {threshold}')
    for metric,threshold in rules.get('maximum',{}).items():
        value=summary.get(metric)
        if not finite_number(value) or value>threshold: problems.append(f'{metric}: {value} > allowed {threshold}')
    return {'passed':not problems,'problems':problems,'rules':rules}
