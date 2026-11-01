import json,sys,time
from llama_cpp import Llama
PROMPT=open('prompt.txt',encoding='utf-8').read()
S=json.load(open('samples.json',encoding='utf-8'))
def norm(w):return w.strip().strip("『』「」'\"‘’“”《》 ")
def run(name,path,suffix=""):
    llm=Llama(model_path=path,n_ctx=2048,n_threads=2,verbose=False)
    hit=miss=extra=0;kind_ok=0;times=[];rows=[]
    for s in S:
        t0=time.time()
        r=llm.create_chat_completion(messages=[{"role":"user","content":PROMPT.replace("{글}",s["text"])+suffix}],
            temperature=0,max_tokens=300)
        times.append(time.time()-t0)
        import re
        txt=re.sub(r"<think>.*?</think>","",r["choices"][0]["message"]["content"],flags=re.S);m=re.search(r"\{.*\}|\[.*\]",txt,re.S)
        try:o=json.loads(m.group(0));got=o.get("items",[]) if isinstance(o,dict) else o
        except Exception:got=[]
        g={norm(x.get("word","")):x.get("kind","") for x in got if isinstance(x,dict) and x.get("word")}
        w={a:b for a,b in s["want"]}
        for k in g:
            if k in w:
                hit+=1
                if g[k]==w[k] or g[k] in w[k]:kind_ok+=1
            else:extra+=1
        miss+=len([k for k in w if k not in g])
        rows.append((s["text"][:22],g))
    print(f"\n== {name} ==")
    for t,g in rows:print(f"  {t}… → {g}")
    tot=sum(len(s['want']) for s in S)
    print(f"맞음 {hit}/{tot} · 종류도 맞음 {kind_ok} · 놓침 {miss} · 엉뚱함 {extra} · 글 1편 평균 {sum(times)/len(times):.1f}초")
which=sys.argv[1]
if which=="qwen":run("Qwen3 4B","/home/claude/models/qwen3-4b.gguf"," /no_think")
else:run("Kanana 1.5 2.1B","/home/claude/models/kanana-2b.gguf")
