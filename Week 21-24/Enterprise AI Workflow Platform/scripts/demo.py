import json, urllib.request
BASE="http://127.0.0.1:8000"
def call(path,key,method="GET",data=None):
    req=urllib.request.Request(BASE+path,data=json.dumps(data).encode() if data is not None else None,headers={"X-API-Key":key,"Content-Type":"application/json"},method=method)
    with urllib.request.urlopen(req) as response: return json.loads(response.read())
if __name__=="__main__":
    print("Gateway:",call("/v1/gateway/chat","demo-app-key","POST",{"task_type":"classification","prompt":"Classify a structural shop drawing"}))
    automatic=call("/v1/workflows","demo-app-key","POST",{"document_id":"DOC-102"}); print("High-confidence automatic workflow:",automatic)
    result=call("/v1/workflows","demo-app-key","POST",{"document_id":"DOC-100"}); print("Medium-confidence review workflow:",result)
    if result.get("approval_id"):
        decision=call("/v1/approvals/"+result["approval_id"]+"/decision","demo-reviewer-key","POST",{"decision":"modify","modified_action":"register corrected classification"}); print("Reviewer decision:",decision)
    print("Audit events:",len(call("/v1/audit","demo-reviewer-key")["items"]))
    print("MCP: python mcp_server.py (stdio); configured tools are listed in docs/ARCHITECTURE.md")
