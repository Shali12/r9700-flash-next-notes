#!/usr/bin/env python3
"""Text check for the rig's model server. Run it BEFORE any speed test (rule in ~/rig/CLAUDE.md).

Three fixed prompts at temperature 0, seed 42:
  a. a one-line raw completion ("The capital of France is" must give Paris)
  b. a short Python question (the returned function is executed and must reverse strings)
  c. a summary of an 8k-token source file (must be about sampling and name real functions from it)
Any reply containing "////" or a run of 200 or more of one character fails. Replies are saved under
~/rig/tools/check/CONFIG_NAME/ (a.txt, b.txt, c.txt, verdict.json).

usage: text-check.py URL MODEL_NAME CONFIG_NAME [--kill]
  e.g. python3 ~/rig/tools/text-check.py http://$(tailscale ip -4):8080 qwen3.8_local my-test
  --kill: also stop llama-server if available RAM falls below 6 GB during the check (hand-run tuning only)
exit code 0 = all three pass, 1 = at least one fails."""
import json, os, re, sys, time, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fnmon

url, model, name = sys.argv[1].rstrip("/"), sys.argv[2], sys.argv[3]
S = os.path.dirname(os.path.abspath(__file__)); OUT = f"{S}/check/{name}"; os.makedirs(OUT, exist_ok=True)
fnmon.start(kill="--kill" in sys.argv)

PC = f"{S}/check/prompt-c-source.txt"          # the same 8k-token source text for every configuration
if not os.path.exists(PC):
    open(PC, "w").write(open(os.path.expanduser("~/llama.cpp-rdna/src/llama-sampler.cpp"), errors="replace").read()[:28000])
source = open(PC).read()
idents = set(re.findall(r"\b(?:llama_sampler_[a-z0-9_]+|llama_perf_[a-z0-9_]+|llama_token_data[a-z_]*|ring_buffer|get_rng_seed)\b", source))

def post(path, body):
    req = urllib.request.Request(url + path, json.dumps(body).encode(), {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=900) as r:
        return json.load(r)
def garbage(t):
    if "////" in t: return "contains a //// run"
    if re.search(r"(\S)\1{199,}", t): return "contains a run of 200+ of one character"
    return None
def save(tag, prompt_desc, thinking, answer, verdict, extra):
    with open(f"{OUT}/{tag}.txt", "w") as f:
        f.write(f"CONFIG: {name}\nPROMPT: {prompt_desc}\nVERDICT: {verdict}\n{extra}\n\n--- thinking ---\n{thinking}\n\n--- answer ---\n{answer}\n")
def show(tag, title, thinking, answer, verdict, extra, n=700):
    print(f"\n[{tag}] {title}\n    verdict: {verdict}   {extra}")
    if thinking.strip(): print("    thinking (start): " + " ".join(thinking.split())[:160])
    body = answer.strip() or "(empty)"
    print("    answer:\n" + "\n".join("      | " + l for l in body[:n].splitlines()[:22]), flush=True)

results = {}
# (a) raw completion
t = time.time()
r = post("/completion", {"prompt": "The capital of France is", "n_predict": 24, "temperature": 0, "seed": 42, "cache_prompt": False})
txt = r.get("content", "")
v = garbage(txt) or ("PASS" if "Paris" in txt else "does not say Paris")
results["a"] = v == "PASS"; ex = f"{time.time()-t:.0f} s"
save("a", '"The capital of France is" (raw completion, 24 tokens)', "", txt, v, ex); show("a", '"The capital of France is"', "", txt, v, ex)

def chat(content, max_tokens):
    t = time.time()
    r = post("/v1/chat/completions", {"model": model, "max_tokens": max_tokens, "temperature": 0, "seed": 42, "cache_prompt": False, **fnmon.extra(sampling=False),
                                      "messages": [{"role": "user", "content": content}]})
    m = r["choices"][0]["message"]; tm = r.get("timings", {})
    return (m.get("reasoning_content") or ""), (m.get("content") or ""), f"{r['usage']['completion_tokens']} reply tokens, {r['usage']['prompt_tokens']} prompt tokens, {time.time()-t:.0f} s, finish: {r['choices'][0].get('finish_reason')}"

# (b) short Python question
th, ans, ex = chat("Write a Python function that reverses a string. Reply with the code in one Python code block.", 2000)
v = garbage(th + ans)
if not v:
    m = re.search(r"```(?:python)?\s*\n(.*?)```", ans, re.S); code = m.group(1) if m else ans
    try:
        ns = {}; exec(code, ns)
        fs = [f for k, f in ns.items() if callable(f) and not k.startswith("_")]
        ok = any(all(f(x) == x[::-1] for x in ("hello", "", "ab", "Flash-Next")) for f in fs) if fs else False
        v = "PASS" if ok else "code runs but does not reverse strings correctly"
    except Exception as e:
        v = f"code does not run: {repr(e)[:80]}"
results["b"] = v == "PASS"
save("b", "Write a Python function that reverses a string.", th, ans, v, ex); show("b", "Python: reverse a string", th, ans, v, ex)

# (c) summary of an 8k-token prompt
th, ans, ex = chat("Here is the start of a C++ source file:\n\n" + source + "\n\nSummarize in three sentences what this file is for, then list three functions that are defined in it.", 2000)
v = garbage(th + ans)
if not v:
    named = sorted(i for i in idents if i in ans)
    if not ans.strip(): v = "empty answer"
    elif not re.search(r"sampl", ans, re.I): v = "summary does not mention sampling"
    elif len(named) < 2: v = f"names fewer than two real identifiers from the file ({named})"
    else: v = "PASS"; ex += f"; real identifiers named: {', '.join(named[:5])}"
results["c"] = v == "PASS"
save("c", "Summary of an 8k-token source file", th, ans, v, ex); show("c", "Summary of an 8k-token prompt", th, ans, v, ex, 900)

ok = all(results.values())
print(f"\n=== {name}: {'PASS' if ok else 'REJECTED'} (a {'ok' if results['a'] else 'FAIL'}, b {'ok' if results['b'] else 'FAIL'}, c {'ok' if results['c'] else 'FAIL'}); {fnmon.summary()}; replies saved in check/{name}/")
json.dump({"name": name, "results": results, "lowest_available_mb": fnmon.lowest[0]}, open(f"{OUT}/verdict.json", "w"))
sys.exit(0 if ok else 1)
