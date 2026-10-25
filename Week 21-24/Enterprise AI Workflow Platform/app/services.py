import json, os, time, uuid, difflib
from pathlib import Path
import httpx
from fastapi import HTTPException
from .config import ROOT, MAX_INPUT, SECURITY, read_json
from .security import injection_signals, output_is_safe
from .storage import audit, connect


def documents():
    return json.loads((ROOT/"data"/"documents.json").read_text(encoding="utf-8"))

def visible_docs(user):
    return [d for d in documents() if user["role"]=="reviewer" or d["owner_id"]==user["user_id"]]

def get_doc(doc_id,user):
    doc=next((d for d in visible_docs(user) if d["id"]==doc_id),None)
    if not doc: raise HTTPException(404,detail="Document not found")
    return doc

def doc_search(q,user):
    if not q or len(q)>300: raise HTTPException(422,detail="Search query must be 1–300 characters")
    return [d for d in visible_docs(user) if q.casefold() in (d["title"]+" "+d["content"]+" "+" ".join(d["tags"])).casefold()]

def compare_docs(a,b,user):
    da,db=get_doc(a,user),get_doc(b,user)
    diff=list(difflib.unified_diff(da["content"].splitlines(),db["content"].splitlines(),fromfile=a,tofile=b,lineterm=""))
    return {"document_a":a,"document_b":b,"differences":diff,"changed":da["content"]!=db["content"]}

def tool_call(name,user,**args):
    if name in {"search_documents","get_document_metadata","get_document_content","search_knowledge_base","compare_revisions","get_related_documents","validate_document","summarize_document"} and user["role"] not in {"app","reviewer"}:
        raise HTTPException(403,detail="Tool permission denied")
    if name=="search_documents": result=doc_search(args["query"],user)
    elif name=="get_document_metadata":
        d=get_doc(args["document_id"],user); result={k:v for k,v in d.items() if k!="content"}
    elif name=="get_document_content": result={"document_id":args["document_id"],"content":get_doc(args["document_id"],user)["content"]}
    elif name=="search_knowledge_base": result=doc_search(args["query"],user)
    elif name=="compare_revisions": result=compare_docs(args["revision_a"],args["revision_b"],user)
    elif name=="get_related_documents":
        d=get_doc(args["document_id"],user); result=[x for x in visible_docs(user) if x["id"]!=d["id"] and (x["project"]==d["project"] or set(x["tags"])&set(d["tags"]))]
    elif name=="validate_document":
        d=get_doc(args["document_id"],user); missing=[k for k in ("title","type","revision","project","content") if not d.get(k)]; result={"valid":not missing,"missing_fields":missing}
    elif name=="summarize_document":
        d=get_doc(args["document_id"],user); result={"document_id":d["id"],"summary":d["content"][:240]}
    else: raise HTTPException(404,detail="Unknown or unauthorized tool")
    audit(user["user_id"],"mcp_tool_call",str(args.get("document_id") or args.get("revision_a") or "search"),{"tool":name})
    return result


def analyze_document(doc_id,user,task):
    d=get_doc(doc_id,user)
    found=injection_signals(d["content"])
    if found: return {"proposed_action":"manual_security_review","confidence":0.35,"risk":"high","signals":found,"label":"untrusted document content"}
    title=d["title"].casefold()
    label="Structural Shop Drawing" if "structural" in title and "drawing" in title else d["type"].title()
    confidence=0.72 if "revision" in title else 0.88
    return {"proposed_action":"register_classification","confidence":confidence,"risk":"normal","label":label,"document_id":d["id"],"revision":d["revision"],"source":"configured demo rule"}

def route_request(task_type,prompt,user):
    validate = prompt.strip()
    if len(validate)>MAX_INPUT: raise HTTPException(413,detail="Prompt exceeds configured size limit")
    signals=injection_signals(prompt)
    if signals:
        audit(user["user_id"],"prompt_injection_blocked",None,{"signals":signals})
        raise HTTPException(400,detail={"message":"Prompt blocked by input security policy","signals":signals})
    model_cfg=read_json("configs/models.json")["models"]
    routes=read_json("configs/routing.json"); evals=read_json("configs/evaluation_results.json")["models"]
    route=routes["tasks"].get(task_type,routes["tasks"][routes["default_task"]])
    weights=routes["weights"]
    by_id={m["id"]:m for m in model_cfg}
    candidates=[]
    for mid in route["candidates"]:
        m=by_id.get(mid); e=evals.get(mid)
        if not m or not m["enabled"] or not e or e["quality"]<route["minimum_quality"] or e["cost_per_1k"]>route["maximum_cost_per_1k"] or e["latency_ms"]>route["maximum_latency_ms"]: continue
        score=weights["quality"]*e["quality"]+weights["cost"]*(1-min(1,e["cost_per_1k"]/max(route["maximum_cost_per_1k"],0.000001)))+weights["latency"]*(1-min(1,e["latency_ms"]/route["maximum_latency_ms"]))
        candidates.append((score,m))
    candidates.sort(key=lambda x:x[0],reverse=True)
    if not candidates: raise HTTPException(503,detail="No enabled model satisfies route constraints")
    primary=candidates[0][1]; order=[primary]
    for fid in primary.get("fallbacks",[]):
        fallback=by_id.get(fid)
        if fallback and fallback["enabled"] and fallback not in order: order.append(fallback)
    order += [m for _,m in candidates if m not in order]
    error=None; used=None; output=""; latency=0
    for m in order:
        for attempt in range(m.get("retries",0)+1):
            start=time.perf_counter()
            try:
                output=provider_generate(m,prompt)
                latency=int((time.perf_counter()-start)*1000); used=m; break
            except Exception as exc:
                error=str(exc)
        if used: break
    if not used: raise HTTPException(502,detail="All configured providers failed") from None
    if not output_is_safe(output): raise HTTPException(502,detail="Provider output failed validation")
    in_tokens=max(1,len(prompt.split())); out_tokens=max(1,len(output.split()))
    cost=(in_tokens*m["cost_per_1k_input"]+out_tokens*m["cost_per_1k_output"])/1000
    with connect() as db: db.execute("INSERT INTO usage(user_id,task_type,model_id,input_tokens,output_tokens,cost,latency_ms,fallback_used) VALUES(?,?,?,?,?,?,?,?)",(user["user_id"],task_type,used["id"],in_tokens,out_tokens,cost,latency,int(used["id"]!=primary["id"])))
    audit(user["user_id"],"gateway_request",None,{"task_type":task_type,"model":used["id"],"fallback":used["id"]!=primary["id"]})
    return {"response":output,"model_id":used["id"],"usage":{"input_tokens":in_tokens,"output_tokens":out_tokens,"estimated_cost":round(cost,8),"latency_ms":latency,"fallback_used":used["id"]!=primary["id"]}}

def provider_generate(model,prompt):
    if model["provider"]=="mock":
        words=prompt.split()
        return f"Demo response ({model['model']}): " + " ".join(words[:90])
    if model["provider"]=="openai_compatible":
        key=os.getenv(model.get("api_key_env",""))
        if not key: raise RuntimeError("Provider API key is not configured")
        response=httpx.post(model["base_url"],headers={"Authorization":f"Bearer {key}"},json={"model":model["model"],"messages":[{"role":"user","content":prompt}]},timeout=model["timeout_seconds"])
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    raise RuntimeError("Unsupported provider")


def submit_workflow(doc_id,user,task="classify"):
    result=analyze_document(doc_id,user,task)
    action=result["proposed_action"]; confidence=result["confidence"]; risk=result["risk"]
    confidence_cfg=SECURITY["confidence"]
    high_risk=action in SECURITY["always_review_actions"] or risk=="high"
    if high_risk or confidence<confidence_cfg["auto_min"]:
        status="pending"
        if confidence<confidence_cfg["review_min"]: result["review_reason"]="low confidence requires mandatory review"
        elif high_risk: result["review_reason"]="high-risk action always requires approval"
        else: result["review_reason"]="medium confidence requires human review"
    else: status="executed"; result["execution"]={"status":"registered","action":action,"label":result.get("label")}
    approval_id=str(uuid.uuid4()) if status=="pending" else None
    if approval_id:
        with connect() as db: db.execute("INSERT INTO approvals(id,owner_id,status,action,confidence,risk,payload) VALUES(?,?,?,?,?,?,?)",(approval_id,user["user_id"],status,action,confidence,risk,json.dumps(result)))
    audit(user["user_id"],"workflow_submitted",doc_id,{"status":status,"action":action,"confidence":confidence,"approval_id":approval_id})
    return {"status":status,"approval_id":approval_id,"analysis":result}

def approval_rows(user):
    with connect() as db: rows=db.execute("SELECT * FROM approvals WHERE status='pending' ORDER BY created_at").fetchall()
    return [dict(r) for r in rows if user["role"]=="reviewer" or r["owner_id"]==user["user_id"]]

def decide(approval_id,decision,user,modified_action=None):
    with connect() as db:
        row=db.execute("SELECT * FROM approvals WHERE id=?",(approval_id,)).fetchone()
        if not row or (user["role"]!="reviewer" and row["owner_id"]!=user["user_id"]): raise HTTPException(404,detail="Approval not found")
        if row["status"]!="pending": raise HTTPException(409,detail="Approval has already been decided")
        if decision not in {"approve","reject","modify"}: raise HTTPException(422,detail="Decision must be approve, reject, or modify")
        if decision=="modify" and (not modified_action or len(modified_action)>300): raise HTTPException(422,detail="A modified action of at most 300 characters is required")
        payload=json.loads(row["payload"]); action=modified_action if decision=="modify" else row["action"]
        status="executed" if decision in {"approve","modify"} else "rejected"
        payload["execution"]={"status":status,"action":action,"reviewer":user["user_id"]}
        db.execute("UPDATE approvals SET status=?,action=?,payload=?,updated_at=CURRENT_TIMESTAMP WHERE id=?",(status,action,json.dumps(payload),approval_id))
    audit(user["user_id"],f"approval_{decision}",approval_id,{"action":action,"status":status})
    return {"approval_id":approval_id,"status":status,"action":action}
