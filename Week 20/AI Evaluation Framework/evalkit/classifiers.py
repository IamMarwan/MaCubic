"""Two trained local statistical models, fitted only on training.json."""
import math
from collections import Counter,defaultdict
from .common import tokens
from .retrieval import cosine

class Classifier:
    def __init__(self,training,model):
        if model not in ('centroid','naive_bayes'):
            raise ValueError('Unknown local classifier')
        self.model=model
        self.labels=sorted({r['label'] for r in training})
        self.counts=defaultdict(Counter)
        self.samples=Counter()
        self.df=Counter()
        for row in training:
            c=Counter(tokens(row['text']))
            self.counts[row['label']].update(c)
            self.samples[row['label']]+=1
            self.df.update(c.keys())
        self.n=len(training)
        self.vocab=set(self.df)
        self.idf={t:math.log((1+self.n)/(1+v))+1 for t,v in self.df.items()}
        self.centroids={label:{t:n*self.idf[t]/sum(c.values()) for t,n in c.items()} for label,c in self.counts.items()}
    def predict(self,text):
        query=Counter(t for t in tokens(text) if t in self.vocab)
        if not query:
            return 'unknown'
        if self.model=='centroid':
            vec={t:n*self.idf[t] for t,n in query.items()}
            scores={label:cosine(vec,v) for label,v in self.centroids.items()}
        else:
            scores={label:math.log(self.samples[label]/self.n)+sum(n*math.log((self.counts[label][t]+1)/(sum(self.counts[label].values())+len(self.vocab))) for t,n in query.items()) for label in self.labels}
        return sorted(scores,key=lambda label:(-scores[label],label))[0]
