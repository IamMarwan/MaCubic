"""TF-IDF cosine, BM25, and validated precomputed embedding retrieval."""
import math
from collections import Counter
from .common import tokens, read_json, digest, finite_number

def cosine(a,b):
    den=math.sqrt(sum(x*x for x in a.values())*sum(x*x for x in b.values()))
    return sum(v*b.get(k,0) for k,v in a.items())/den if den else 0.0

class Retriever:
    def __init__(self, documents, method='tfidf', vector_path=None):
        self.docs=documents
        self.method=method
        self.counts={k:Counter(tokens(d['text'])) for k,d in documents.items()}
        self.df=Counter(t for counts in self.counts.values() for t in counts)
        self.n=len(documents)
        self.idf={t:math.log((1+self.n)/(1+df))+1 for t,df in self.df.items()}
        self.vectors={k:self.weight(c) for k,c in self.counts.items()}
        self.avglen=sum(map(lambda c:sum(c.values()),self.counts.values()))/max(1,self.n)
        self.embedding=None
        if method=='vectors':
            self.embedding=read_json(vector_path)
            if self.embedding['corpus_hash']!=digest(documents):
                raise ValueError('Embedding corpus hash mismatch')
            if set(self.embedding['documents'])!=set(documents):
                raise ValueError('Embedding document IDs mismatch')
            dim=self.embedding['dimensions']
            if not isinstance(dim,int) or dim<1:
                raise ValueError('Invalid embedding dimension')
            for v in list(self.embedding['documents'].values())+[q['vector'] for q in self.embedding['queries'].values()]:
                if len(v)!=dim or not all(finite_number(x) for x in v) or not any(v):
                    raise ValueError('Invalid or zero embedding vector')
        elif method not in ('tfidf','bm25'):
            raise ValueError('Unknown retrieval method')
    def weight(self,counts):
        return {t:(1+math.log(n))*self.idf.get(t,0) for t,n in counts.items()}
    def search(self,question,k,case_id):
        if self.method=='vectors':
            q=self.embedding['queries'][case_id]
            if q['question_hash']!=digest(question):
                raise ValueError('Embedding query hash mismatch')
            v=dict(enumerate(q['vector']))
            scores={d:cosine(v,dict(enumerate(x))) for d,x in self.embedding['documents'].items()}
        elif self.method=='tfidf':
            query=self.weight(Counter(tokens(question)))
            scores={d:cosine(query,v) for d,v in self.vectors.items()}
        else:
            query=set(tokens(question));scores={}
            for d,counts in self.counts.items():
                length=sum(counts.values())
                scores[d]=sum(math.log(1+(self.n-self.df[t]+0.5)/(self.df[t]+0.5))*counts[t]*2.5 /
                              (counts[t]+1.5*(0.25+0.75*length/self.avglen)) for t in query if counts[t])
        # Deterministic ties; zero lexical similarity is not a retrieval hit.
        return [{'doc_id':d,'score':score} for d,score in sorted(scores.items(),key=lambda p:(-p[1],p[0]))[:k] if score>0]
