from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone
from fastapi import FastAPI, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from .config import RATE_LIMIT, APP_KEYS
from .security import identity, require_role, validate_text
from .services import route_request, submit_workflow, approval_rows, decide, doc_search
from .storage import audit_rows, audit, usage_rows

app=FastAPI(title="Enterprise AI Workflow Platform",version="1.0.0",description="Combined Week 21–24 gateway, MCP, approval, and security demonstration.")
_hits=defaultdict(deque)
@app.middleware("http")
async def throttle(request:Request,call_next):
    if request.url.path.startswith("/v1/"):
        key=request.headers.get("x-api-key","anonymous"); now=datetime.now(timezone.utc); q=_hits[key]
        while q and q[0]<now-timedelta(minutes=1): q.popleft()
        if len(q)>=RATE_LIMIT: return __import__("starlette.responses",fromlist=["JSONResponse"]).JSONResponse({"detail":"Rate limit exceeded"},status_code=429)
        q.append(now)
    response=await call_next(request)
    if request.url.path.startswith("/v1/"):
        actor=APP_KEYS.get(key,{}).get("user_id","anonymous")
        audit(actor,"api_request",None,{"method":request.method,"path":request.url.path,"status_code":response.status_code})
    return response
class ChatRequest(BaseModel):
    task_type:str=Field(default="general",min_length=1,max_length=80)
    prompt:str=Field(min_length=1)
class WorkflowRequest(BaseModel):
    document_id:str=Field(min_length=1,max_length=100)
    task:str=Field(default="classify",max_length=80)
class DecisionRequest(BaseModel):
    decision:str
    modified_action:str|None=None
@app.get("/health")
def health(): return {"status":"ok"}
@app.post("/v1/gateway/chat")
def gateway(body:ChatRequest,user=Depends(identity)):
    validate_text(body.prompt,"prompt"); return route_request(body.task_type,body.prompt,user)
@app.post("/v1/workflows")
def workflow(body:WorkflowRequest,user=Depends(identity)):
    return submit_workflow(body.document_id,user,body.task)
@app.get("/v1/approvals")
def approvals(user=Depends(identity)):
    require_role(user,"reviewer","app"); return {"items":approval_rows(user)}
@app.post("/v1/approvals/{approval_id}/decision")
def approval_decision(approval_id:str,body:DecisionRequest,user=Depends(identity)):
    require_role(user,"reviewer"); return decide(approval_id,body.decision,user,body.modified_action)
@app.get("/v1/audit")
def audit(user=Depends(identity),limit:int=100):
    return {"items":audit_rows(user["user_id"],user["role"]=="reviewer",max(1,min(limit,500)))}
@app.get("/v1/documents/search")
def search(q:str,user=Depends(identity)):
    return {"items":doc_search(q,user)}

@app.get("/v1/usage")
def usage(user=Depends(identity),limit:int=100):
    return {"items":usage_rows(user["user_id"],user["role"]=="reviewer",max(1,min(limit,500)))}
