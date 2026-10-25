"""Minimal MCP-compatible client proving stdio discovery and tool invocation."""
import asyncio, os, sys
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    project=Path(__file__).resolve().parents[1]
    env=os.environ.copy(); env.setdefault("MCP_USER_ID","user-1"); env.setdefault("MCP_ROLE","reviewer")
    params=StdioServerParameters(command=sys.executable,args=[str(project/"mcp_server.py")],env=env,cwd=str(project))
    async with stdio_client(params) as (read_stream,write_stream):
        async with ClientSession(read_stream,write_stream) as session:
            await session.initialize()
            tools=await session.list_tools()
            print("Discovered MCP tools:",", ".join(tool.name for tool in tools.tools))
            result=await session.call_tool("search_documents",{"query":"structural"})
            print("Search result:",result.content)

if __name__=="__main__": asyncio.run(main())
