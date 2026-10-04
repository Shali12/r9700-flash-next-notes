#!/usr/bin/env python3
"""Read-only: summarise a (possibly multi-shard) GGUF model from header files, which may be partial downloads.
usage: gguf_multi.py LABEL  HEADER_FILE:REAL_SIZE [HEADER_FILE:REAL_SIZE ...]      (shards in order)"""
import collections, hashlib, re, struct, sys

SZ = {0: "B", 1: "b", 2: "H", 3: "h", 4: "I", 5: "i", 6: "f", 7: "?", 10: "Q", 11: "q", 12: "d"}
TYPES = {0:"F32",1:"F16",2:"Q4_0",3:"Q4_1",6:"Q5_0",7:"Q5_1",8:"Q8_0",9:"Q8_1",10:"Q2_K",11:"Q3_K",12:"Q4_K",13:"Q5_K",14:"Q6_K",15:"Q8_K",16:"IQ2_XXS",17:"IQ2_XS",18:"IQ3_XXS",19:"IQ1_S",20:"IQ4_NL",21:"IQ3_S",22:"IQ2_S",23:"IQ4_XS",24:"I8",25:"I16",26:"I32",27:"I64",28:"F64",29:"IQ1_M",30:"BF16",34:"TQ1_0",35:"TQ2_0",39:"MXFP4",40:"NVFP4",41:"Q1_0",42:"Q2_0"}
GiB = 1 << 30

def parse(path, real_size):
    f = open(path, "rb")
    def rd(fmt):
        b = f.read(struct.calcsize("<" + fmt))
        if len(b) < struct.calcsize("<" + fmt): raise EOFError
        return struct.unpack("<" + fmt, b)[0]
    def rstr():
        n = rd("Q"); b = f.read(n)
        if len(b) < n: raise EOFError
        return b.decode("utf-8", "replace")
    def rval(t):
        if t in SZ: return rd(SZ[t])
        if t == 8: return rstr()
        if t == 9:
            et = rd("I"); n = rd("Q")
            if et in SZ:
                if n <= 64: return [rd(SZ[et]) for _ in range(n)]
                f.seek(n * struct.calcsize("<" + SZ[et]), 1); return f"[{n} items]"
            for _ in range(n): rval(et)
            return f"[{n} items]"
        raise ValueError(f"unknown GGUF value type {t}")
    assert f.read(4) == b"GGUF", path
    rd("I"); n_t = rd("Q"); n_kv = rd("Q"); meta = {}; tensors = []
    for _ in range(n_kv):
        k = rstr(); t = rd("I"); meta[k] = rval(t)
    for _ in range(n_t):
        name = rstr(); nd = rd("I"); dims = [rd("Q") for _ in range(nd)]; ty = rd("I"); off = rd("Q")
        tensors.append([name, dims, ty, off])
    end = f.tell(); align = meta.get("general.alignment", 32); start = (end + align - 1) // align * align
    order = sorted(tensors, key=lambda x: x[3])
    for i, t in enumerate(order):
        t.append((order[i + 1][3] if i + 1 < len(order) else real_size - start) - t[3])
    return meta, tensors, end

label = sys.argv[1]; meta = {}; allt = []; per_shard = []
for i, arg in enumerate(sys.argv[2:], 1):
    path, size = arg.rsplit(":", 1)
    try:
        m, ts, end = parse(path, int(size))
    except EOFError:
        sys.exit(f"shard {i}: header longer than the fetched part; fetch more of {path}")
    if i == 1: meta = m
    for t in ts: t.append(i)
    allt += ts; per_shard.append((i, int(size), len(ts), sum(t[4] for t in ts)))

def kind(n):
    if n.startswith("per_layer_token_embd"): return "n-gram table (per_layer_token_embd)"
    if "nextn" in n or "mtp" in n.lower(): return "draft head (nextn / MTP)"
    if re.search(r"_exps\.", n): return "MoE expert weights"
    if n.startswith("blk."): return "other per-layer weights"
    return "non-layer weights (token_embd, output, ...)"
arch = meta.get("general.architecture")
print(f"===== {label}: {len(sys.argv) - 2} shard(s), {sum(s for _, s, _, _ in per_shard)/1e9:.1f} GB on disk, {len(allt)} tensors, arch {arch}")
for k in ("general.name", "general.quantized_by", "general.file_type", f"{arch}.block_count", f"{arch}.expert_count", f"{arch}.expert_used_count", f"{arch}.context_length", f"{arch}.nextn_predict_layers", f"{arch}.nextn_shared_target_tensors", "quantize.imatrix.file", "split.count"):
    if k in meta: print(f"  {k} = {meta[k]}")
tpl = meta.get("tokenizer.chat_template")
if isinstance(tpl, str): print(f"  chat template: {len(tpl)} chars, sha {hashlib.sha256(tpl.encode()).hexdigest()[:12]}; default effort line: {[l.strip() for l in tpl.splitlines() if 'resolved_reasoning_effort = ' in l][:1]}")
bykind = collections.defaultdict(int); bytype = collections.defaultdict(int); shards_of = collections.defaultdict(set)
for name, dims, ty, off, size, sh in allt:
    k = kind(name); bykind[k] += size; bytype[(k, TYPES.get(ty, f"type{ty}"))] += size; shards_of[k].add(sh)
print("  --- by kind (GiB) ---")
for k, b in sorted(bykind.items(), key=lambda x: -x[1]):
    types = ", ".join(f"{t} {v/GiB:.2f}" for (kk, t), v in sorted(bytype.items(), key=lambda x: -x[1]) if kk == k and v > 0.004 * GiB)
    sh = sorted(shards_of[k]); shs = f"shard {sh[0]}" if len(sh) == 1 else f"shards {sh[0]}-{sh[-1]}"
    print(f"  {b/GiB:7.2f}  {k}  ({shs})  [{types}]")
ple = bykind["n-gram table (per_layer_token_embd)"]; total = sum(bykind.values())
print(f"  must be in memory (everything except the n-gram table): {(total - ple)/GiB:.2f} GiB = {(total - ple)/1e9:.1f} GB;  n-gram table: {ple/GiB:.2f} GiB = {ple/1e9:.1f} GB")
for name, dims, ty, off, size, sh in allt:
    if name.startswith("per_layer_token_embd"): print(f"  n-gram tensor: {name} {dims} type {TYPES.get(ty, ty)}, {size/GiB:.2f} GiB, alone in its shard: {sum(1 for t in allt if t[5] == sh) == 1} (shard {sh})")
exp = collections.defaultdict(int); oth = collections.defaultdict(int)
for name, dims, ty, off, size, sh in allt:
    m = re.match(r"blk\.(\d+)\.", name)
    if m: (exp if kind(name) == "MoE expert weights" else oth)[int(m.group(1))] += size
layers = sorted(set(exp) | set(oth))
if layers:
    e = [exp[L] for L in layers]
    print(f"  layers {layers[0]}..{layers[-1]}: expert weights per layer min {min(e)/GiB:.2f} max {max(e)/GiB:.2f} GiB; other per-layer weights total {sum(oth.values())/GiB:.2f} GiB")
    acc = 0; row = []
    for i, L in enumerate(layers, 1):
        acc += exp[L]
        if i % 4 == 0 or i == len(layers): row.append(f"N={i}:{acc/GiB:.1f}")
    print("  experts kept in RAM with -ncmoe N (GiB): " + "  ".join(row))
nn = [t[0] for t in allt if kind(t[0]).startswith("draft head")]
print(f"  draft-head tensors: {len(nn)} {nn[:4]}")
print("  largest non-table tensors: " + "; ".join(f"{t[0]} {TYPES.get(t[2], t[2])} {t[4]/GiB:.2f}" for t in sorted([t for t in allt if not t[0].startswith('per_layer')], key=lambda x: -x[4])[:3]))
