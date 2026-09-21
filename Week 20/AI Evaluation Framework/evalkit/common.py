"""Shared serialization, validation and reproducibility helpers."""
import hashlib
import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIELDS = ['project', 'document_no', 'revision', 'issue_date', 'status', 'reviewer', 'due_date']
LABELS = ['drawing', 'rfi', 'material_submittal', 'method_statement', 'inspection_request', 'meeting_minutes', 'invoice', 'transmittal']

def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))

def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n', encoding='utf-8')

def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()

def norm(value):
    # Preserve punctuation: revision 01 and 1, document A-1 and A1 differ.
    return ' '.join(str(value).casefold().split()) if value is not None else None

def tokens(text):
    return re.findall(r'[a-z0-9]+', text.casefold())

def mean(values):
    values = [v for v in values if v is not None]
    return sum(values) / len(values) if values else None

def finite_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)

def public_input(case, corpus):
    """An explicit allowlist: expected answers never cross the provider boundary."""
    inp = dict(case['input'])
    if case['task'] != 'qa':
        inp['document'] = corpus[inp['document_id']]
    return {'case_id': case['id'], 'task': case['task'], **inp}

def load_dataset(directory):
    directory = Path(directory)
    corpus = read_json(directory / 'corpus.json')
    cases = read_json(directory / 'benchmark.json')
    facts = read_json(directory / 'facts.json')
    training = read_json(directory / 'training.json')
    ids = [d['id'] for d in corpus]
    if len(set(ids)) != len(ids) or len({c['id'] for c in cases}) != len(cases):
        raise ValueError('Duplicate document or case ID')
    docs = {d['id']: d for d in corpus}
    if set(facts) != set(docs):
        raise ValueError('Every corpus document must have a fact annotation')
    for d in corpus:
        if set(d) != {'id', 'text'} or not isinstance(d['text'], str):
            raise ValueError('Corpus contains fields outside id/text')
        for field, entry in facts[d['id']].items():
            if entry['value'] is not None:
                quote = entry['quote']
                if not quote or quote not in d['text'] or norm(entry['value']) not in norm(quote):
                    raise ValueError(f'Invalid source evidence: {d["id"]}/{field}')
    for c in cases:
        if c['task'] not in ('qa', 'metadata', 'classification') or c['split'] not in ('dev', 'test'):
            raise ValueError('Invalid task or split')
        for d in c['expected'].get('relevant_ids', []):
            if d not in docs:
                raise ValueError('Unknown relevance document')
        if c['task'] != 'qa' and c['input']['document_id'] not in docs:
            raise ValueError('Unknown input document')
        for claim in c['expected'].get('claims', []):
            annotation = facts[claim['doc_id']][claim['field']]
            if norm(claim['value']) != norm(annotation['value']):
                raise ValueError('Gold claim contradicts source annotation')
    if any(t['text'] in {d['text'] for d in corpus} for t in training):
        raise ValueError('Identical training and evaluation document')
    return docs, cases, facts, training

def code_hash():
    paths = sorted((ROOT / 'evalkit').glob('*.py'))
    return digest({p.name: p.read_text(encoding='utf-8') for p in paths})
