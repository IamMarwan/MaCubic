// Structural JavaScript interaction check; not a browser/rendering test.
const fs=require('fs'),vm=require('vm');
const file=process.argv[2],html=fs.readFileSync(file,'utf8');
class Element{
 constructor(tag){this.tagName=tag;this.children=[];this.style={};this._value='';this.textContent='';this.className='';this.listeners={};}
 append(...children){this.children.push(...children);}
 replaceChildren(...children){this.children=[...children];this._value='';}
 get value(){if(this._value!=='')return this._value;if(this.tagName==='select')return String(this.children[0]?.value??'');return '';}
 set value(v){this._value=String(v);}
 click(){}
}
const elements={};for(const m of html.matchAll(/<(\w+)[^>]*\bid="([^"]+)"[^>]*>/g)){elements[m[2]]=new Element(m[1]);}
elements.data.textContent=html.split('<script id="data" type="application/json">')[1].split('</script>')[0];
elements.task.children=[Object.assign(new Element('option'),{value:'all'})];
const context={document:{getElementById:id=>elements[id],createElement:tag=>new Element(tag)},console,Blob,URL};vm.createContext(context);
const script=html.split('</script><script>')[1].split('</script>')[0];vm.runInContext(script,context);
function assert(condition,message){if(!condition)throw Error(message)}
assert(elements.metrics.children.length===23,'Expected every metric row');
assert(elements.stats.children.length===4,'Expected summary cards');
assert(elements.history.children.length>=4,'Expected historical runs');
assert(elements.case.children.length===70,'Expected full selected test split');
elements.task.value='failures';elements.task.onchange();assert(elements.case.children.length>0,'Expected inspectable failures');
elements.search.value='impossible-no-such-case';elements.search.oninput();assert(elements.gold.textContent==='No matching cases','Empty filter handling');
elements.search.value='';elements.task.value='qa';elements.task.onchange();assert(elements.case.children.length===38,'QA filter count');
elements.case.value='P2-DRW-02-status';elements.case.onchange();assert(elements.sources.textContent.includes('Review status:'),'Source text available');
elements.candidate.value='1';elements.candidate.onchange();assert(elements.pred.textContent.length>0,'Run selection refresh');
elements.export.onclick();
console.log(JSON.stringify({check:'JavaScript execution with a minimal DOM test double',metric_rows:elements.metrics.children.length,history_rows:elements.history.children.length,qa_cases:38,filters:true,source_details:true,csv_handler:true,browser_rendering:false}));
