import asyncio
import json
import logging
import os
import re
import time
from pathlib import Path
from typing import AsyncGenerator, Dict, List, Optional, Tuple

import httpx

log = logging.getLogger("Leviathan_Eye.ai")

OLLAMA_BASE = "http://localhost:11434"
CONFIG_PATH = Path(__file__).parent / "config.json"

TOOL_CAPABLE_MODELS = [
    "mistral","llama3.1","llama3.2","llama3.3",
    "qwen2","qwen2.5","command-r","hermes",
    "firefunction","functionary","nexusraven",
    "mixtral","llama-3.1","llama-3.2","llama-3.3",
]

SYSTEM_PROMPT = """You are Leviathan_Eye-AI, an intelligence analysis engine for a live global geospatial intelligence dashboard.

You have access to tools to fetch live data. Always use them before answering.

AVAILABLE TOOLS:
- search_news(query, category?, threat?, limit?)
- get_base_info(name, nation?)
- get_conflict_status(name?)
- get_country_intel(iso2)
- web_research(query, timespan?)
- classify_news(count?)
- modify_base_data(store, upsert?, remove?)

TOOL FORMAT (text-based):
<tool_call>{"name": "tool_name", "args": {"key": "value"}}</tool_call>

RULES:
- Always call at least one tool before giving a final answer
- Use markdown: ## headers, **bold** key entities, bullet lists for facts
- Cite sources inline
- Threat levels: CRITICAL > WARNING > INFO
- Be direct and specific"""


def load_config() -> Dict:
    if CONFIG_PATH.exists():
        try:
            return json.loads(CONFIG_PATH.read_text())
        except Exception:
            pass
    return {"mode": "none"}


def model_has_native_tools(model_name: str) -> bool:
    return any(p in model_name.lower() for p in TOOL_CAPABLE_MODELS)


TOOLS_SCHEMA = [
    {"type":"function","function":{"name":"search_news","description":"Search live intelligence news","parameters":{"type":"object","properties":{"query":{"type":"string"},"category":{"type":"string"},"threat":{"type":"string"},"limit":{"type":"integer"}},"required":["query"]}}},
    {"type":"function","function":{"name":"get_base_info","description":"Get military installation intel","parameters":{"type":"object","properties":{"name":{"type":"string"},"nation":{"type":"string"}},"required":["name"]}}},
    {"type":"function","function":{"name":"get_conflict_status","description":"Get conflict zone data","parameters":{"type":"object","properties":{"name":{"type":"string"}}}}},
    {"type":"function","function":{"name":"get_country_intel","description":"Country military/economic intel","parameters":{"type":"object","properties":{"iso2":{"type":"string"}},"required":["iso2"]}}},
    {"type":"function","function":{"name":"web_research","description":"GDELT event stream research","parameters":{"type":"object","properties":{"query":{"type":"string"},"timespan":{"type":"string"}},"required":["query"]}}},
    {"type":"function","function":{"name":"classify_news","description":"Get high-threat news items","parameters":{"type":"object","properties":{"count":{"type":"integer"}}}}},
    {"type":"function","function":{"name":"modify_base_data","description":"Update OSINT data files","parameters":{"type":"object","properties":{"store":{"type":"string"},"upsert":{"type":"array","items":{"type":"object"}},"remove":{"type":"array","items":{"type":"string"}}},"required":["store"]}}},
]


class ToolExecutor:
    def __init__(self, news_store, data_manager):
        self.news = news_store
        self.dm   = data_manager

    async def execute(self, name: str, args: Dict) -> str:
        fn = getattr(self, f"_t_{name}", None)
        if not fn:
            return json.dumps({"error": f"Unknown tool: {name}"})
        try:
            return json.dumps(await fn(**args), ensure_ascii=False, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)})

    async def _t_search_news(self, query="", category="all", threat=None, limit=8):
        q = query.lower()
        items = self.news.items
        matched = [i for i in items if q in (i.get("headline","")+" "+i.get("summary","")).lower()]
        if category != "all": matched = [i for i in matched if i.get("category")==category]
        if threat: matched = [i for i in matched if i.get("threat")==threat]
        return {"total":len(matched),"results":[{"headline":i["headline"],"source":i["source"],"threat":i["threat"],"time":i["time"],"url":i.get("url","")} for i in matched[:min(limit,20)]]}

    async def _t_get_base_info(self, name="", nation=None):
        q = name.lower()
        all_b = self.dm.get("bases")+self.dm.get("construction")
        matches = [b for b in all_b if q in b.get("name","").lower() or any(q in str(b.get(k,"")).lower() for k in ["notes","type","tags"])]
        if nation: matches = [b for b in matches if b.get("nation","").lower()==nation.lower()]
        return {"primary":matches[0],"related":matches[1:3],"total":len(matches)} if matches else {"error":f"No base: '{name}'"}

    async def _t_get_conflict_status(self, name=None):
        conflicts = self.dm.get("conflicts")
        if name:
            q = name.lower()
            return {"results":[c for c in conflicts if q in c.get("name","").lower()]}
        return {"total":len(conflicts),"critical":[c for c in conflicts if c.get("threat")=="critical"],"warning":[c for c in conflicts if c.get("threat")=="warning"]}

    async def _t_get_country_intel(self, iso2=""):
        iso = iso2.upper()
        bases = self.dm.filter("bases",nation=iso.lower())
        gdp = mil = None
        try:
            async with httpx.AsyncClient(timeout=6.0) as c:
                r1 = await c.get(f"https://api.worldbank.org/v2/country/{iso.lower()}/indicator/NY.GDP.MKTP.CD?format=json&mrv=1&per_page=1")
                r2 = await c.get(f"https://api.worldbank.org/v2/country/{iso.lower()}/indicator/MS.MIL.XPND.CD?format=json&mrv=1&per_page=1")
                d1=r1.json(); d2=r2.json()
                gdp=d1[1][0]["value"] if d1[1] else None
                mil=d2[1][0]["value"] if d2[1] else None
        except Exception: pass
        return {"iso2":iso,"gdp_usd":gdp,"military_expenditure_usd":mil,"mil_pct_gdp":round((mil/gdp)*100,2) if (mil and gdp) else None,"known_bases":[{"id":b["id"],"name":b["name"],"type":b["type"],"status":b["status"]} for b in bases]}

    async def _t_web_research(self, query="", timespan="24h"):
        try:
            async with httpx.AsyncClient(timeout=10.0) as c:
                r = await c.get("https://api.gdeltproject.org/api/v2/doc/doc",params={"query":query,"mode":"artlist","maxrecords":10,"format":"json","timespan":timespan,"sort":"DateDesc"},headers={"User-Agent":"Leviathan_Eye/7.0"},timeout=10.0)
                arts = r.json().get("articles") or []
                return {"query":query,"total":len(arts),"articles":[{"title":a.get("title",""),"domain":a.get("domain",""),"url":a.get("url",""),"date":a.get("seendate","")} for a in arts[:8]]}
        except Exception as e:
            return {"error":str(e)}

    async def _t_classify_news(self, count=15):
        items = self.news.items[:count]
        return {"critical":[{"headline":i["headline"],"source":i["source"],"time":i["time"]} for i in items if i.get("threat")=="critical"][:5],"warning":[{"headline":i["headline"],"source":i["source"],"time":i["time"]} for i in items if i.get("threat")=="warning"][:5]}

    async def _t_modify_base_data(self, store="bases", upsert=None, remove=None):
        result = self.dm.apply_ai_patch({"store":store,"upsert":upsert or [],"remove":remove or []})
        return {"status":"ok","result":result}


class OllamaClient:
    def __init__(self, base=OLLAMA_BASE):
        self.base = base

    async def list_models(self) -> List[Dict]:
        try:
            async with httpx.AsyncClient(timeout=3.0) as c:
                return (await c.get(f"{self.base}/api/tags")).json().get("models",[])
        except Exception:
            return []

    async def is_up(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=2.0) as c:
                return (await c.get(f"{self.base}/api/tags")).status_code == 200
        except Exception:
            return False

    async def stream(self, model, messages, system=None, tools=None) -> AsyncGenerator[Dict,None]:
        payload = {"model":model,"messages":messages,"stream":True,"options":{"temperature":0.2,"num_ctx":8192}}
        if system: payload["system"] = system
        if tools:  payload["tools"]  = tools
        async with httpx.AsyncClient(timeout=None) as c:
            async with c.stream("POST", f"{self.base}/api/chat", json=payload) as resp:
                async for line in resp.aiter_lines():
                    if not line: continue
                    try: yield json.loads(line)
                    except Exception: continue


class OpenAIClient:
    def __init__(self, key, url, model):
        self.key=key; self.base=url.rstrip("/"); self.model=model

    async def stream(self, messages, system=None) -> AsyncGenerator[str,None]:
        msgs = ([{"role":"system","content":system}] if system else []) + messages
        hdrs = {"Authorization":f"Bearer {self.key}","Content-Type":"application/json"}
        async with httpx.AsyncClient(timeout=None) as c:
            async with c.stream("POST",f"{self.base}/chat/completions",
                                json={"model":self.model,"messages":msgs,"stream":True,"temperature":0.2},
                                headers=hdrs) as resp:
                async for line in resp.aiter_lines():
                    if not line or line=="data: [DONE]": continue
                    if line.startswith("data: "):
                        try:
                            t = json.loads(line[6:])["choices"][0]["delta"].get("content","")
                            if t: yield t
                        except Exception: continue


def _sse(**kwargs) -> str:
    return f"data: {json.dumps(kwargs)}\n\n"


class LeviathanPipeline:
    def __init__(self):
        self.ollama   = OllamaClient()
        self.executor: Optional[ToolExecutor] = None
        self._oai:     Optional[OpenAIClient] = None
        self._cfg:     Dict = {}
        self._model:   Optional[str] = None

    def load_config(self):
        self._cfg = load_config()
        mode = self._cfg.get("mode","none")
        if mode=="openai" and self._cfg.get("key"):
            self._oai = OpenAIClient(self._cfg["key"],self._cfg.get("url","https://api.openai.com/v1"),self._cfg.get("model","gpt-4o-mini"))
        if mode=="ollama" and self._cfg.get("ollama_model"):
            self._model = self._cfg["ollama_model"]

    def set_executor(self, ex: ToolExecutor):
        self.executor = ex

    async def get_model(self) -> Optional[str]:
        if self._model: return self._model
        models = await self.ollama.list_models()
        preferred = ["mistral","llama3.1","llama3.2","qwen2.5","llama3","deepseek","gemma2","phi3"]
        names = [m["name"] for m in models]
        for p in preferred:
            for n in names:
                if p in n.lower():
                    self._model=n; return n
        if names: self._model=names[0]; return names[0]
        return None

    async def get_status(self) -> Dict:
        cfg=self._cfg; mode=cfg.get("mode","none")
        model=cfg.get("ollama_model") or cfg.get("model") or ""
        running=False; models=[]
        if mode=="ollama":
            running=await self.ollama.is_up()
            if running: models=[m["name"] for m in await self.ollama.list_models()]
        elif mode=="openai":
            running=bool(cfg.get("key")); models=[cfg.get("model","")]
        return {"mode":mode,"running":running,"model":model,"models":models,
                "native_tools":model_has_native_tools(model),"tool_mode":cfg.get("tool_mode","text")}

    async def chat_stream(self, messages: List[Dict], context: Optional[Dict]=None) -> AsyncGenerator[str,None]:
        cfg=self._cfg; mode=cfg.get("mode","none")
        if mode=="none":
            yield _sse(type="error",content="**AI not configured.** Run SETUP.bat to configure an AI model.")
            return
        ctx = self._ctx_block(context)
        if mode=="openai":
            async for c in self._oai_stream(messages,ctx): yield c
            return
        model = await self.get_model()
        if not model:
            yield _sse(type="error",content="**Ollama not running.** Start with: `ollama serve`")
            return
        native = model_has_native_tools(model)
        yield _sse(type="model",content=model,native_tools=native,mode="ollama")
        async for c in self._agentic(model,messages,ctx,native): yield c

    async def _agentic(self, model, messages, ctx, native_tools) -> AsyncGenerator[str,None]:
        sys_p  = SYSTEM_PROMPT
        tools  = TOOLS_SCHEMA if native_tools else None
        user_q = messages[-1]["content"] if messages else ""
        aug    = messages[:-1]+[{"role":"user","content":ctx+user_q+(""if native_tools else"\n\nUse <tool_call> format for tools.")}]

        yield _sse(type="thinking",content="🔍 Analyzing query...")

        first=""
        native_calls=[]
        try:
            async for chunk in self.ollama.stream(model,aug,sys_p,tools):
                if chunk.get("done"): break
                msg = chunk.get("message",{})
                if msg.get("tool_calls"):
                    for tc in msg["tool_calls"]:
                        fn=tc.get("function",{})
                        native_calls.append({"name":fn.get("name"),"args":fn.get("arguments",{})})
                        yield _sse(type="tool_call",name=fn.get("name"),args=fn.get("arguments",{}))
                c=msg.get("content","")
                if c:
                    first+=c
                    yield _sse(type="thinking_chunk",content=c)
        except httpx.ConnectError:
            yield _sse(type="error",content="**Ollama not reachable.** Run: `ollama serve`"); return
        except Exception as e:
            yield _sse(type="error",content=str(e)); return

        text_calls=[]
        if not native_tools:
            for raw in re.findall(r'<tool_call>(.*?)</tool_call>',first,re.DOTALL):
                try:
                    c=json.loads(raw.strip())
                    text_calls.append(c)
                    yield _sse(type="tool_call",name=c.get("name"),args=c.get("args",{}))
                except Exception: pass

        all_calls=native_calls+text_calls
        tool_results=[]
        if all_calls and self.executor:
            for call in all_calls:
                name=call.get("name",""); args=call.get("args",{})
                yield _sse(type="tool_running",name=name)
                result=await self.executor.execute(name,args)
                tool_results.append({"tool":name,"result":result})
                try:
                    preview=json.dumps(json.loads(result),indent=1)[:300]
                except Exception:
                    preview=result[:300]
                yield _sse(type="tool_result",name=name,preview=preview)

        if tool_results:
            rb="\n\n".join(f"### {r['tool']}\n```json\n{r['result']}\n```" for r in tool_results)
            synth=aug+[{"role":"assistant","content":first},{"role":"user","content":f"Tool results:\n{rb}\n\nWrite a comprehensive intelligence brief with ## headers, **bold** key terms, and bullet lists. Cite sources."}]
            yield _sse(type="synthesizing",content="📊 Synthesizing intelligence brief...")
            try:
                async for chunk in self.ollama.stream(model,synth,sys_p):
                    if chunk.get("done"): break
                    c=(chunk.get("message")or{}).get("content","")
                    if c: yield _sse(type="content",content=c)
            except Exception as e:
                yield _sse(type="error",content=str(e))
        else:
            clean=re.sub(r'<tool_call>.*?</tool_call>',"",first,flags=re.DOTALL).strip()
            if clean: yield _sse(type="content",content=clean)

        yield _sse(type="done")

    async def _oai_stream(self, messages, ctx) -> AsyncGenerator[str,None]:
        if not self._oai:
            yield _sse(type="error",content="API client not configured."); return
        model=self._oai.model
        yield _sse(type="model",content=model,native_tools=False,mode="openai")
        yield _sse(type="thinking",content=f"🔍 Querying {model}...")
        user_q=messages[-1]["content"] if messages else ""
        aug=messages[:-1]+[{"role":"user","content":ctx+user_q+"\n\nUse <tool_call> format for tools."}]
        full=""
        try:
            async for t in self._oai.stream(aug,SYSTEM_PROMPT):
                full+=t; yield _sse(type="thinking_chunk",content=t)
        except Exception as e:
            yield _sse(type="error",content=str(e)); return
        all_calls=[]
        for raw in re.findall(r'<tool_call>(.*?)</tool_call>',full,re.DOTALL):
            try:
                c=json.loads(raw.strip()); all_calls.append(c)
                yield _sse(type="tool_call",name=c.get("name"),args=c.get("args",{}))
            except Exception: pass
        tool_results=[]
        if all_calls and self.executor:
            for call in all_calls:
                name=call.get("name",""); args=call.get("args",{})
                yield _sse(type="tool_running",name=name)
                result=await self.executor.execute(name,args)
                tool_results.append({"tool":name,"result":result})
                yield _sse(type="tool_result",name=name,preview=result[:300])
        if tool_results:
            rb="\n\n".join(f"### {r['tool']}\n```json\n{r['result']}\n```" for r in tool_results)
            synth=aug+[{"role":"assistant","content":full},{"role":"user","content":f"Tool results:\n{rb}\n\nWrite a comprehensive intelligence brief."}]
            yield _sse(type="synthesizing",content="📊 Synthesizing...")
            try:
                async for t in self._oai.stream(synth,SYSTEM_PROMPT):
                    yield _sse(type="content",content=t)
            except Exception as e:
                yield _sse(type="error",content=str(e))
        else:
            clean=re.sub(r'<tool_call>.*?</tool_call>',"",full,flags=re.DOTALL).strip()
            if clean: yield _sse(type="content",content=clean)
        yield _sse(type="done")

    def _ctx_block(self, ctx: Optional[Dict]) -> str:
        if not ctx: return ""
        parts=["## Context\n"]
        if ctx.get("base"):
            b=ctx["base"]
            parts.append(f"**Facility:** {b.get('name')} | Nation: {(b.get('nation','?')).upper()} | Type: {b.get('type')} | Status: {b.get('status')}\n")
            if b.get("notes"): parts.append(f"Notes: {b['notes']}\n")
        if ctx.get("country"): parts.append(f"**Country ISO2:** {ctx['country']}\n")
        if ctx.get("conflict"):
            c=ctx["conflict"]
            parts.append(f"**Conflict:** {c.get('name')} | Threat: {c.get('threat','?').upper()} | Parties: {', '.join(c.get('parties',[]))}\n")
        if ctx.get("chokepoint"): parts.append(f"**Chokepoint:** {ctx['chokepoint']}\n")
        return "".join(parts)+"\n"


pipeline = LeviathanPipeline()

# Alias for backward compatibility
AIPipeline = LeviathanPipeline
