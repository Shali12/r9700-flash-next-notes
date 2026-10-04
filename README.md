# Qwen3.8-Flash-Next and Qwen3.8-27B on one Radeon AI PRO R9700: notes and results

Measurements, settings and lessons from running two local models on a single 32 GB AMD card with llama.cpp and
[stew675's RDNA4 patch set](https://github.com/stew675/llama-cpp-rdna-boosts), as workers for a coding agent
(Hermes Agent). Everything was measured between 2026-09-28 and 2026-10-04 on one machine.

**These are results for these quants on my rig, not a model ranking.** Read [Caveats](#caveats) before quoting a number.

## TL;DR

- **Flash-Next (a 125B mixture-of-experts model) runs usefully on one 32 GB card plus 64 GB of RAM.** With the
  AtomicChat Q4_K_M quant and patch release r30: two workers with 131,072 tokens of context each, 36 tok/s for one
  worker and 50 tok/s combined for two, without a draft head.
- **On r29/r30, set `GGML_SCHED_DEVGATHER=0` or the output is garbage.** With the default, the first request after
  loading is correct and every later one is `////////`, at full speed. Seen on all three quants tested. Upstream
  knows ([issue #85](https://github.com/stew675/llama-cpp-rdna-boosts/issues/85)) and says r31 changed the default;
  nothing newer than r30 was tested here.
- **Load with `--lazy-mode on --load-mode none`.** `mmap` and `dio` ran a 61 GiB machine out of RAM.
- **Check the text before you measure speed.** The corrupted server was first reported here as "48 tok/s, pass".
- **The expert cache is what makes it fast** (about 39 tok/s against 17-20 without it). The draft head adds
  27-45% for one request once the cache is on, but costs VRAM, pushes more of the model into RAM, and left only
  about 1.7 GB of RAM available under a real agent workload.
- **Tool calling: level on ordinary tasks, Flash-Next ahead on hard ones.** tool-eval-bench main suite 94.8 against
  95.3 (27B) on the scenarios graded for both; Hard Mode 93.9 against 79.8, three runs each.
- **The 27B is the faster model**: about 1.7 times as fast per turn in the benchmark, reads prompts 1.6 to 2 times
  as fast, and has working vision here.
- **A 220 W power cap costs almost nothing**: 78 °C instead of 87-89 °C, prompt reading about 3% slower.

Details and the reasoning: [FINDINGS.md](FINDINGS.md). All tables: [results/](results).

## Hardware

| Part | |
|---|---|
| GPU | AMD Radeon AI PRO R9700, 32 GB (gfx1201), capped at 220 W |
| CPU | AMD Ryzen 5 7600X (6 cores, 12 threads) |
| RAM | 64 GB DDR5 (61 GiB usable) |
| Motherboard | GIGABYTE B850 AI TOP |
| Storage | Kingston NV3 1 TB M.2 NVMe |
| Power supply, case | MONTECH CENTURY II 1200 W, Lian Li LANCOOL 217 |

Headless, used over SSH. One GPU; the CPU's built-in graphics is hidden from ROCm with `HIP_VISIBLE_DEVICES=0`.

## Software versions

| Piece | Version |
|---|---|
| OS | Ubuntu 24.04.4 |
| Kernel | 6.17.0-42-generic, pinned in GRUB (`apt full-upgrade` had moved it to 7.0) |
| GPU stack | ROCm 10.0.0 (`amdrocm-core-dev10.0-gfx1201`), `amdgpu-dkms` from the 31.50 repo, Secure Boot on |
| llama.cpp base | commit `84e76d8a2` (upstream tag `b11173`, 2026-09-24) |
| Patch set, 27B options | `v16-84e76d8a2-r20`, 16 blocks; server reports `b11189-6947b4e6f` |
| Patch set, Flash-Next options | `v16-84e76d8a2-r30`, 16 blocks, tree `0fe48395051775079fb18041142e3f22dbf82a72`; server reports `b11189-49565eec6` |
| Build flags | `-DGGML_HIP=ON -DGPU_TARGETS="gfx1201" -DCMAKE_BUILD_TYPE=Release` |
| Benchmark | [tool-eval-bench](https://github.com/SeraphimSerapis/tool-eval-bench) 2.7.0 |
| Agent | Hermes Agent on a separate mini PC, reaching the rig over a private network |

The patch repo is rebased often. On 2026-10-04 its head was `v16-a55e952b8-r10`, on a newer llama.cpp base. To
reproduce these numbers, use the patch repo at commit `f108261` (r30) or `72976d8` (r20).

## Model files

| Used as | File | Source |
|---|---|---|
| 27B, the fast worker with vision | `Qwen3.8-27B-UD-Q5_K_XL.gguf` (19,909 MB) and `mmproj-F16.gguf`; also Q4_K_XL and Q6_K_XL | [unsloth/Qwen3.8-27B-GGUF](https://huggingface.co/unsloth/Qwen3.8-27B-GGUF) |
| Flash-Next, main quant | `Qwen3.8-Flash-Next-AD-4.27bpw-Q4_K_M-M64-*.gguf` (33 shards, 94.5 GB) | [AtomicChat/Qwen3.8-Flash-Next-GGUF](https://huggingface.co/AtomicChat/Qwen3.8-Flash-Next-GGUF) |
| Flash-Next, lighter quant | `Qwen3.8-Flash-Next-GSQ-RCO-IQ3_XXS-*.gguf` (2 shards, 75.8 GB) | [ISTA-DASLab/Qwen3.8-Flash-Next-GSQ-RCO-GGUF](https://huggingface.co/ISTA-DASLab/Qwen3.8-Flash-Next-GSQ-RCO-GGUF) |
| Flash-Next, tested and dropped | UD-IQ4_XS (3 shards, 93.7 GB) | [unsloth/Qwen3.8-Flash-Next-GGUF](https://huggingface.co/unsloth/Qwen3.8-Flash-Next-GGUF) |
| Flash-Next draft head | `MTP/mtp-Qwen3.8-Flash-Next-shared-Q8_0.gguf` (2.8 GB) | the same Unsloth repo |
| Model card | | [Qwen/Qwen3.8-Flash-Next](https://huggingface.co/Qwen/Qwen3.8-Flash-Next) |

The AtomicChat files carry an older chat template; it is run with the standard one
(`--chat-template-file`, extracted from the ISTA file). None of the Flash-Next files contains a draft head.

## Results

All speeds are tokens per second at **medium reasoning effort**, temperature 1.0, top_p 0.95, top_k 20, min_p 0,
on a short prompt unless said, with the text checked first. Speeds fall as the context fills.

### The options

| Option ([configs/](configs)) | Model | Slots x context | Writing, one request | Writing, all slots at once (total) | Reading a prompt | Free with every slot full |
|---|---|---|---|---|---|---|
| `flash-next-q4-2x128k-plain` | Flash-Next Q4_K_M, no draft head | 2 x 131,072 | 36.1-36.4 (27.0 at full context) | 50.1 (34.8 at full context) | 496-504 | 3,370 MB VRAM, 15.5 GB RAM |
| `flash-next-q4-2x128k` | Flash-Next Q4_K_M, draft head depth 3 | 2 x 131,072 | 48.2-52.1 (34.2-34.4) | 48.2 (37.7) | 436-441 | 1,845 MB VRAM, 7.8 GB RAM |
| `flash-next-q4-2x64k` | Flash-Next Q4_K_M, draft head depth 3 | 2 x 65,536 | 56.1-57.5 | 56.5 | 482-489 | 1,764 MB VRAM, 16.3 GB RAM |
| `flash-next-q4` | Flash-Next Q4_K_M, draft head depth 3 | 1 x 131,072 | 51.7-54.9 (35.0) | one slot | 463-510 | 1,377 MB VRAM, 11.8 GB RAM |
| `flash-next` | Flash-Next IQ3_XXS, no draft head | 1 x 131,072 | 38.7-39.1 (28.0) | one slot | 614-639 | 1,721 MB VRAM, 28.5 GB RAM |
| `27b-q5xl` | 27B Q5_K_XL, built-in draft head, vision | 2 x 85,248 | 43-74 (40.6 after 64k) | 54.4 | 815-990 | about 1.4 GB VRAM; RAM not limiting |

The 27B's range is wide because its speed follows draft acceptance. The other three 27B options
(`27b-q5xl-1agent`, `27b-q6xl`, `27b-q4xl`) were measured for memory only: [results/options-and-memory.md](results/options-and-memory.md).
Under a real agent workload `flash-next-q4-2x128k` fell to about 1.7 GB of available RAM, against 7.8 GB in the test.

More: [Stage 1](results/speed-stage1-ista-vs-27b.md) (ISTA quant, every configuration tried, loading modes),
[Stage 1d](results/speed-stage1d-quants-and-draft-head.md) (three quants, the draft head),
[Stage 1e](results/speed-stage1e-more-context.md) (2 x 131,072 and 1 x 262,144).

### Tool calling (tool-eval-bench 2.7.0)

`flash-next-q4-2x128k-plain` against `27b-q5xl`, identical settings, seeds 42, 43 and 44.

| Test | Flash-Next Q4_K_M | 27B Q5_K_XL |
|---|---|---|
| Main suite, mean of three runs, on the 64 scenarios graded for both | 94.8 | 95.3 |
| Main suite, the three runs | 94.5, 95.3, 94.5 | 95.3, 93.8, 96.9 |
| Main suite with about 54,000 tokens of filler before every scenario (one run) | 89.8 | 92.2 |
| IFEval, first 100 prompts (one run) | 84 of 100 prompts, 89.6% of instructions | 84 of 100, 88.3% |
| Hard Mode, 19 scenarios, mean of three runs | 93.9 | 79.8 |
| Hard Mode, the three runs | 92, 97, 92 | 84, 76, 79 |
| Median time per turn, main suite | 5.0-5.1 s | 3.0-3.1 s |
| Time for one full main run | 18-19 min | 15-16 min |

In Hard Mode the 27B lost TC-74 and TC-84 in all three runs by sending a tool call that depended on an earlier call's
result in the same turn. Four main-suite scenarios (TC-65, 66, 67, 69) were rejected by both servers with a llama.cpp
grammar error and are in neither score; TC-45 was graded on one server and not the other.
Details: [results/tool-eval-main.md](results/tool-eval-main.md), [results/tool-eval-hard-mode.md](results/tool-eval-hard-mode.md),
raw reports in [results/raw/tool-eval/](results/raw/tool-eval).

### One real agent job on each model

A small game built as four delegated tasks, two workers at a time, checked by a cloud parent model.

| | 27B Q5_K_XL, 2 x 85k | Flash-Next Q4_K_M, 2 x 128k, draft head |
|---|---|---|
| Tasks that passed first review | 3 of 4 | 4 of 4 |
| Re-delegations | 1 | 0 |
| Wall-clock | about 2 h 30 m | about 4 h 10 m |
| New tests written | 26 | 37 |

One run each. [results/stage3-hermes-job.md](results/stage3-hermes-job.md)

## How to reproduce

1. **Driver stack.** Ubuntu 24.04.4 with kernel 6.17.0-42 pinned, `amdgpu-dkms`, ROCm 10.0.0. The traps are in
   [FINDINGS.md](FINDINGS.md#rocm-10-setup-gotchas).
2. **Build llama.cpp with the patch set** (r30 shown; the patch repo's `release.json` names the base commit):

   ```bash
   git clone https://github.com/stew675/llama-cpp-rdna-boosts ~/llama-cpp-rdna-boosts
   git -C ~/llama-cpp-rdna-boosts checkout f108261              # r30; 72976d8 for r20
   git clone https://github.com/ggml-org/llama.cpp ~/llama.cpp-rdna-r30
   cd ~/llama.cpp-rdna-r30
   git checkout "$(jq -r .base ~/llama-cpp-rdna-boosts/release.json)"     # 84e76d8a2
   git config user.name "Your Name"; git config user.email "you@example.com"   # git am needs an identity
   bash ~/llama-cpp-rdna-boosts/scripts/apply-all.sh .          # 16 commits, "rdna-boosts: block 00..15"
   git rev-parse HEAD^{tree}                                    # must equal .tree in release.json
   HIPCXX="$(hipconfig -l)/clang" HIP_PATH="$(hipconfig -R)" \
     cmake -B build -DGGML_HIP=ON -DGPU_TARGETS="gfx1201" -DCMAKE_BUILD_TYPE=Release
   cmake --build build -j6
   ```

3. **Start a server.** Each file in [configs/](configs) is one setup; [scripts/start-server.sh](scripts/start-server.sh)
   turns it into a `llama-server` command. The everyday Flash-Next setup, written out:

   ```bash
   cd ~/llama.cpp-rdna-r30
   MOE_EXPERT_CACHE_MIB=4096 MOE_EXPERT_CACHE_DEVMAP=1 GGML_SCHED_DEVGATHER=0 HIP_VISIBLE_DEVICES=0 \
   ./build/bin/llama-server \
     -m ~/models/flash-next-atomic/Qwen3.8-Flash-Next-AD-4.27bpw-Q4_K_M-M64-00001-of-00033.gguf \
     -ngl 99 -ncmoe 41 -c 262144 -np 2 -t 6 --flash-attn on --cache-type-k q8_0 --cache-type-v q8_0 \
     --lazy-mode on --load-mode none --cache-ram 2048 \
     --chat-template-file ~/models/flash-next/chat-template-standard.jinja \
     --min-p 0 --metrics --alias qwen3.8_local --host YOUR-ADDRESS --port 8080
   ```

4. **Check the text first.** `python3 scripts/text-check.py http://YOUR-ADDRESS:8080 qwen3.8_local NAME`
   sends three fixed prompts and fails on a wrong answer or on runs like `////`. Send more than one request: a
   corrupted server answers the first one correctly.
5. **Tool-calling benchmark.**

   ```bash
   uv tool install --python 3.12 "git+https://github.com/SeraphimSerapis/tool-eval-bench.git@v2.7.0"
   tool-eval-bench run --base-url http://YOUR-ADDRESS:8080 --model qwen3.8_local --backend llamacpp \
     --seed 42 --temperature 1.0 --top-p 0.95 --top-k 20 --min-p 0 \
     --backend-kwargs '{"reasoning_effort":"medium"}' --timeout 600 --no-live
   ```

   Add `--hardmode-only` for Hard Mode, or `--context-pressure 0.75 --context-size 85248` for the pressure run.
   [scripts/teb.sh](scripts/teb.sh) runs the whole sequence in a detached tmux session.

## What is in this repo

| Path | Contents |
|---|---|
| [FINDINGS.md](FINDINGS.md) | What went wrong, what fixed it, and the trade-offs, with the numbers behind each |
| [results/](results) | Speed and memory tables for every quant and option, the benchmark tables, the real-job comparison, the power cap |
| [results/raw/tool-eval/](results/raw/tool-eval) | The benchmark's own JSON results and Markdown reports with full conversation traces |
| [configs/](configs) | The nine model option files, as used |
| [scripts/](scripts) | `rig-model` (switch options, with a known-answer check and rollback), `start-server.sh`, `text-check.py`, `teb.sh`, `ram-watch.sh`, `gguf_multi.py` |
| [hermes/](hermes) | The delegation block and the parent's playbook, with placeholders |

## Caveats

- **One machine, one card.** Nothing here was repeated on other hardware, other drivers or other patch releases.
- **Medium reasoning effort and temperature 1.0 throughout**, because that is what the agent gets: Hermes sends
  `"reasoning_effort":"medium"` and no sampling settings, so the server's defaults apply (temperature 1.0, top_p 0.95,
  top_k 20, and `min_p` 0 from the option files). The chat template's own default is xhigh, and tool-eval-bench's
  default is temperature 0, so numbers from elsewhere may not be comparable. ISTA say their quant was calibrated at
  xhigh and loses quality at medium.
- **Run counts are small.** Speeds: three runs on the short prompt, one at each larger size. Main benchmark and Hard
  Mode: three runs per model. Context pressure, IFEval and the real agent job: one run per model.
- **These quants on this rig, not a model ranking.** A 4.27-bit Flash-Next quant is compared with a Q5_K_XL 27B quant
  because those are what fit. Different quants, engines or settings can change the order.
- **The benchmarked Flash-Next setup had no draft head.** It is assumed that drafting changes speed and not answers;
  that was not tested. The real agent job did use the draft head.
- **The two servers are different patch releases** (r20 for the 27B, r30 for Flash-Next). The 27B was not tested on r30.
- **Sampled, not greedy.** At temperature 1.0 runs differ; the three seeds show by how much.
- **Estimates are marked as estimates** in the tables. Everything else was measured.
- **Vision was not tested on Flash-Next.** The 27B's vision works on this rig.

## Licence

MIT, see [LICENSE](LICENSE). The files under `results/raw/tool-eval/` were produced by tool-eval-bench (MIT) and
contain its scenario texts.
