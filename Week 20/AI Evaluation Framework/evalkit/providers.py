"""Local statistical pipelines, OpenAI Responses, and external prediction replay."""
import json
import os
import re
import urllib.error
import urllib.request
from .common import FIELDS, LABELS, norm, read_json, finite_number
from .classifiers import Classifier

ALIASES={
 'project':['Project name','Project'], 'document_no':['Document number','Reference'],
 'revision':['Revision','Rev'], 'issue_date':['Issue date','Issued on'],
 'status':['Review status','Disposition'], 'reviewer':['Reviewer','Checked by'],
 'due_date':['Due date','Response deadline']}

def extract(text,policy='grounded'):
    values={};quotes={}
    for field,aliases in ALIASES.items():
        found=[]
        for line in text.splitlines():
            for label in aliases if policy=='grounded' else aliases[:1]:
                m=re.fullmatch(re.escape(label)+r'\s*:\s*(.+)',line.strip(),re.I)
                if m: found.append((m.group(1).strip(),line))
        # Conflicting duplicate labels require abstention for that field.
        if len({norm(x[0]) for x in found})==1:
            values[field],quotes[field]=found[0]
        else: values[field]=None
    return values,quotes

def empty_prediction():
    return {'claims':[],'metadata':{f:None for f in FIELDS},'label':None,'abstain':False}

def validate_prediction(p):
    if not isinstance(p,dict) or set(p)!={'claims','metadata','label','abstain'}:
        raise ValueError('Prediction must match the documented schema')
    if type(p['abstain']) is not bool or not isinstance(p['claims'],list):
        raise ValueError('Invalid abstention or claims')
    if not isinstance(p['metadata'],dict) or set(p['metadata'])!=set(FIELDS):
        raise ValueError('Metadata must include every schema field, using null for missing values')
    if any(v is not None and not isinstance(v,str) for v in p['metadata'].values()):
        raise ValueError('Metadata values must be strings or null')
    if p['label'] is not None and p['label'] not in LABELS+['unknown']:
        raise ValueError('Unknown classification label')
    seen=set()
    for c in p['claims']:
        if not isinstance(c,dict) or set(c)!={'doc_id','field','value','citations'} or not all(isinstance(c[k],str) and c[k] for k in ('doc_id','field','value')):
            raise ValueError('Invalid atomic claim')
        pair=(c['doc_id'],c['field'])
        if pair in seen: raise ValueError('Duplicate claim field for a document')
        seen.add(pair)
        if not isinstance(c['citations'],list): raise ValueError('Invalid citations')
        for cite in c['citations']:
            if not isinstance(cite,dict) or set(cite)!={'doc_id','quote'} or not all(isinstance(v,str) for v in cite.values()):
                raise ValueError('Invalid citation')
    if p['abstain'] and p['claims']:
        raise ValueError('Abstention cannot include factual claims')
    return p

def validate_usage(u):
    if not isinstance(u,dict): raise ValueError('Invalid usage')
    for key in ['input_tokens','output_tokens','cached_input_tokens']:
        n=u.get(key)
        if n is not None and (type(n) is not int or n<0): raise ValueError('Invalid token count')
    if u.get('cached_input_tokens') is not None and u.get('input_tokens') is not None and u['cached_input_tokens']>u['input_tokens']:
        raise ValueError('Cached tokens exceed input tokens')
    return u

class LocalProvider:
    def __init__(self,config,training):
        self.policy=config['extraction_policy']
        self.classifier=Classifier(training,config['model'])
    def predict(self,inp,contexts):
        p=empty_prediction()
        if inp['task']=='classification':
            text=inp['document']['text']
            if inp.get('omit_title'): text='\n'.join(text.splitlines()[1:])
            p['label']=self.classifier.predict(text)
        elif inp['task']=='metadata':
            p['metadata']=extract(inp['document']['text'],self.policy)[0]
        else:
            # Identity resolution reads document content, never the answer key.
            question=norm(inp['question'])
            refs=set(re.findall(r'\b[A-Z]{2,4}-\d+\b',inp['question'],re.I))
            refs={x.casefold() for x in refs}
            revisions=re.findall(r'\brevision\s+([a-z0-9]+)',question)
            for doc in contexts:
                identity,_=extract(doc['text'],'grounded')
                if identity.get('project') and norm(identity['project']) not in question: continue
                if refs and norm(identity.get('document_no')) not in refs: continue
                if revisions and norm(identity.get('revision')) not in revisions: continue
                fields,quotes=extract(doc['text'],self.policy)
                for field in inp['fields']:
                    if fields.get(field) is not None:
                        p['claims'].append({'doc_id':doc['id'],'field':field,'value':fields[field],
                                            'citations':[{'doc_id':doc['id'],'quote':quotes[field]}]})
            p['abstain']=not p['claims']
        return p,{'input_tokens':0,'output_tokens':0,'cached_input_tokens':0,'source':'local_no_llm'},{}

STR={'type':'string'}
NULLSTR={'type':['string','null']}
def obj(properties):
    return {'type':'object','properties':properties,'required':list(properties),'additionalProperties':False}
CITE_SCHEMA=obj({'doc_id':STR,'quote':STR})
CLAIM_SCHEMA=obj({'doc_id':STR,'field':STR,'value':STR,'citations':{'type':'array','items':CITE_SCHEMA}})
PREDICTION_SCHEMA=obj({'claims':{'type':'array','items':CLAIM_SCHEMA},'metadata':obj({f:NULLSTR for f in FIELDS}),
                       'label':{'type':['string','null'],'enum':LABELS+['unknown',None]},'abstain':{'type':'boolean'}})

class ProviderError(RuntimeError):
    def __init__(self,message,usage=None,raw=None):
        super().__init__(message)
        self.usage=usage or {'input_tokens':None,'output_tokens':None,'cached_input_tokens':None,'source':'unavailable'}
        self.raw=raw or {}

class OpenAIProvider:
    def __init__(self,config,prompt,transport=None):
        self.config=config;self.prompt=prompt
        self.model=config.get('model') or os.environ.get(config.get('model_env','OPENAI_MODEL'))
        self.key=os.environ.get(config.get('api_key_env','OPENAI_API_KEY'))
        if not self.model: raise ValueError('Set the configured model environment variable')
        if transport is None and not self.key: raise ValueError('OPENAI_API_KEY is not configured')
        self.transport=transport or self.request
    def request(self,payload):
        req=urllib.request.Request('https://api.openai.com/v1/responses',
            data=json.dumps(payload).encode(),headers={'Authorization':'Bearer '+self.key,'Content-Type':'application/json'})
        try:
            with urllib.request.urlopen(req,timeout=self.config.get('timeout_seconds',60)) as response:
                return json.load(response)
        except urllib.error.HTTPError as exc:
            raise ProviderError(f'OpenAI HTTP {exc.code}; no automatic retry or fallback') from None
        except (urllib.error.URLError,TimeoutError):
            raise ProviderError('OpenAI network error or timeout; usage unavailable') from None
    def predict(self,inp,contexts):
        public=dict(inp)
        if public.get('omit_title'):
            public['document']=dict(public['document'],text='\n'.join(public['document']['text'].splitlines()[1:]))
        payload={'model':self.model,'store':False,'instructions':self.prompt,
                 'input':json.dumps({'task':public,'retrieved_documents':contexts},ensure_ascii=False),
                 'max_output_tokens':self.config.get('max_output_tokens',2000),
                 'text':{'format':{'type':'json_schema','name':'evaluation_prediction','strict':True,'schema':PREDICTION_SCHEMA}}}
        raw=self.transport(payload)
        counts=raw.get('usage') or {}
        usage={'input_tokens':counts.get('input_tokens'),'output_tokens':counts.get('output_tokens'),
               'cached_input_tokens':counts.get('input_tokens_details',{}).get('cached_tokens'), 'source':'provider_reported'}
        metadata={'response_id':raw.get('id'),'model':raw.get('model',self.model),'status':raw.get('status'),
                  'output_tokens_details':counts.get('output_tokens_details',{})}
        if raw.get('status')!='completed': raise ProviderError('Model response was not completed',usage,metadata)
        fragments=[c['text'] for item in raw.get('output',[]) if item.get('type')=='message' for c in item.get('content',[]) if c.get('type')=='output_text']
        try: p=validate_prediction(json.loads(''.join(fragments)));validate_usage(usage)
        except (ValueError,TypeError,KeyError): raise ProviderError('Invalid structured model response',usage,metadata) from None
        return p,usage,metadata

class ReplayProvider:
    def __init__(self,config,benchmark_hash):
        self.bundle=read_json(config['predictions_file'])
        if self.bundle['benchmark_hash']!=benchmark_hash: raise ValueError('Prediction benchmark hash mismatch')
        records=self.bundle['records']
        if len({r['case_id'] for r in records})!=len(records): raise ValueError('Duplicate replay case')
        self.records={r['case_id']:r for r in records}
    def predict(self,inp,contexts):
        r=self.records[inp['case_id']]
        usage=validate_usage(r['usage'])
        latency=r.get('latency_ms')
        if latency is not None and (not finite_number(latency) or latency<0): raise ValueError('Invalid imported latency')
        return validate_prediction(r['prediction']),usage,{'imported':True,'model':self.bundle.get('model'),'original_latency_ms':latency}
