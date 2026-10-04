# Findings

What went wrong, what fixed it, and the trade-offs, on one Radeon AI PRO R9700 (32 GB) with 64 GB of RAM.
Versions and hardware are in the [README](README.md). Every number is from the tables in [results/](results);
anything not measured says so.

Contents:
[1. The gather corruption](#1-the-gather-corruption) ·
[2. Loading modes](#2-loading-modes) ·
[3. The expert cache and the -ncmoe split](#3-the-expert-cache-and-the--ncmoe-split) ·
[4. The draft head trade-off](#4-the-draft-head-trade-off) ·
[5. Reasoning effort and the xhigh loop](#5-reasoning-effort-and-the-xhigh-loop) ·
[6. min_p](#6-min_p) ·
[7. The grammar error on TC-65, 66, 67 and 69](#7-the-grammar-error-on-tc-65-66-67-and-69) ·
[8. The TC-45 grading difference](#8-the-tc-45-grading-difference) ·
[ROCm 10 setup gotchas](#rocm-10-setup-gotchas) ·
[The 220 W power cap](#the-220-w-power-cap) ·
[Smaller things](#smaller-things)

## 1. The gather corruption

**Symptom.** Flash-Next on patch release r30 with default settings: the server loads, answers `/health`, and the
**first request after loading is answered correctly**. Every later request, even a one-line completion, is
`////////////` without end, at full speed.

**Where.** Releases r29 and r30 of the patch set added a faster way to copy expert weights from RAM to the GPU,
the "gather", on by default. It corrupted the output of all three quants tested, each in the same way:

| Quant | Result with the gather on |
|---|---|
| ISTA GSQ-RCO IQ3_XXS | rejected by the text check: `////////` |
| AtomicChat AD-4.27bpw Q4_K_M | given five requests in a row; failed at request 2 |
| Unsloth UD-IQ4_XS | given five requests in a row; failed at request 2 |

**Fix.** One environment variable: `GGML_SCHED_DEVGATHER=0`. It is in the `ENVS` line of every Flash-Next option in
[configs/](configs).

**Cost of the fix.** Not known. With the gather off, the ISTA quant reads prompts at about 630 tok/s. The gather-on
runs showed 1,300-1,500 tok/s, but those runs were corrupted, so that is not a valid comparison.

**Upstream.** Already known: [stew675/llama-cpp-rdna-boosts issue #85](https://github.com/stew675/llama-cpp-rdna-boosts/issues/85).
The maintainer describes the gather path as fast "up until the 2nd ubatch, where it then corrupts", and says r31
switched to the slower, correct staging path. Nothing newer than r30 was tested here, so whether the variable is
still needed on later releases is not known.

**How it was missed at first, and the lesson.** The speed tests counted tokens per second and never read the text.
Flash-Next was written down as "48 tok/s, pass" before anyone looked at a reply. Every number measured that way
(17-19 tok/s plain, 48 tok/s with the expert cache, "0 drafts accepted") is void. Two rules came out of it:

- **Text before speed.** [scripts/text-check.py](scripts/text-check.py) sends three fixed prompts with known answers
  (a one-line completion, a short Python function that is then executed, a summary of an 8k-token file) and fails on a
  wrong answer, `////`, or a run of 200 or more of one character. No speed is measured for a configuration that fails.
- **One test prompt proves nothing.** Because the first request is correct, the switch script
  ([scripts/rig-model](scripts/rig-model)) asks three known-answer questions after every model switch and rolls back
  to the previous option if any is wrong. A one-question version of that check passed on the broken server.

## 2. Loading modes

The n-gram embedding table is 26.8 GiB (35.8 GiB in the AtomicChat quant) and the RAM-side experts 20-40 GiB, on a
machine with 61 GiB. How the files are loaded decides whether it fits.

| `--load-mode` / `--lazy-mode` | What happened (ISTA quant) |
|---|---|
| `mmap` / `on` | Process RAM climbed to 59.6 GB and swap grew by 1.7 GB. The RAM-side experts exist twice: the mapped file and the working copy. The build itself warns to use `--load-mode none` |
| `dio` / `off` | Steady at 49.6 GB, then past 57 GB while reading the file data; stopped by the memory guard |
| `none` / `off` | Works, but the table is loaded into RAM: 46.6 GB with 24 layers of experts in RAM, 56.5 GB peak with 32 layers and a 6 GB cache (4.0 GB of RAM left) |
| **`none` / `on`** | **Works best.** The table stays on disk and only the rows needed are read. Process 29.4 GB, 28 GB available, load in 27-29 s |

- **Use `--lazy-mode on --load-mode none`.** It worked for all three quants, including Unsloth's, where the table
  shares a shard with other tensors.
- AtomicChat's model card recommends keeping mmap on. That advice is for a different machine (unified memory). On
  this rig mmap is the mode that ran out of RAM; it was tried with the ISTA quant only.
- Why dio overshoots was not established (a temporary copy is a guess).
- `vm.swappiness` was lowered from 60 to 10 after the first loads pushed the machine into swap, and stayed at 10;
  nothing was re-tested at 60.

## 3. The expert cache and the -ncmoe split

Flash-Next has 48 layers with 512 experts each (10 used per token). The experts do not fit in 32 GB, so
`-ncmoe N` keeps the experts of the first N layers in RAM and the rest on the GPU.

**The expert cache is what makes it usable.** `MOE_EXPERT_CACHE_MIB=4096` (with `MOE_EXPERT_CACHE_DEVMAP=1`) gives
4 GB of VRAM to the most-used RAM-side experts. ISTA quant, writing on a short prompt:

| Configuration | tok/s |
|---|---|
| r20 build, no cache | 16.8-17.0 |
| r30, gather off, draft head, no cache | 17.8-19.6 |
| r30, gather off, 2 GB cache | 40.3-40.6 |
| r30, gather off, 4 GB cache (the option) | 38.8-39.1 |
| r30, gather off, 16 GB cache, all 48 layers in RAM | 40.6-42.0, but reads prompts at 518-540 tok/s instead of 614-639 |

A bigger cache bought little; 4 GB was kept.

**Choosing N.** The rule used: with every slot holding a full prompt, at least 1 GB of VRAM free and at least 6 GB of
RAM available. Values that met it:

| Setup (AtomicChat Q4_K_M unless said) | `-ncmoe` | VRAM free, slots full | RAM available, slots full |
|---|---|---|---|
| ISTA IQ3_XXS, 1 x 131,072, no draft head | 35 | 1,721 MB | 28.5 GB |
| 1 x 131,072, draft head | 44 | 1,377 MB | 11.8 GB |
| 2 x 65,536, draft head | 40 | 1,764 MB | 16.3 GB |
| 2 x 131,072, no draft head | 41 | 3,370 MB | 15.5 GB |
| 2 x 131,072, draft head | 47 | 1,845 MB | 7.8 GB |
| 1 x 262,144, no draft head | 45 | 2,373 MB | 11.3 GB |

- **One layer of AtomicChat experts is about 1,138 MiB.** From the load logs: 12,533 MiB of model on the GPU at
  `-ncmoe 41`, 5,708 MiB at `-ncmoe 47`.
- **More experts in RAM reads prompts more slowly**: 463-510 tok/s with 44 layers in RAM against 526-589 with 38.
- **GPU working memory follows the deepest slot, not the total.** With two 131,072 slots, VRAM use was 29,246 MB with
  one slot full and the same with both full. What doubling the total context costs is the preallocated KV cache:
  3,672 MiB at 262,144 against 1,836 MiB at 131,072 (q8_0).
- On the ISTA quant, GPU working memory grew by about 36 MB per 1,000 tokens of prompt, on top of about 2.3 GB that
  appears with the first request.
- **1 x 262,144 works**: a 260,203-token prompt was read in 10.3 minutes (429 tok/s) and then written at about
  20 tok/s.

## 4. The draft head trade-off

None of the Flash-Next quant files contains a draft head. Unsloth's separate sidecar
(`mtp-Qwen3.8-Flash-Next-shared-Q8_0.gguf`) works on the r30 build with
`--spec-draft-model FILE --spec-draft-ngl 99 --spec-type draft-mtp --spec-draft-n-max 3`.

**Speed.**

- **Without the expert cache it is nearly useless**: 17.8-19.6 tok/s against about 17 (ISTA quant).
- **With the cache it is worth 27-45% for one request** (AtomicChat, 1 x 131,072): 51.7-54.9 against 37.1-37.2 on a
  short prompt, 35.0 against 27.5 at full context. Draft acceptance 0.80-0.90.
- **With two requests writing at once the gain mostly disappears**: 56.5 against 52.1 combined at 2 x 65,536; at
  2 x 131,072, 48.2 against 50.1 on short prompts and 37.7 against 34.8 at full context.
- **Depth 3 beat depth 5**: depth 5 gave 48-54 tok/s short with acceptance 0.63-0.81.

**Cost.**

- **VRAM.** About 3 GB for one slot, growing with the prompt. With two slots at about 130k tokens each it took about
  8.4 GB: the draft model 2.6 GB, its recurrent-state buffer 0.9 GB, its own KV cache 0.6 GB, and memory that grows
  with prompt depth.
- **RAM, indirectly.** That VRAM comes out of the experts' share, so more layers move to RAM: `-ncmoe 47` instead
  of 41 at 2 x 131,072, which is 47 of 48 layers.
- **Reading is about 12% slower** for the same reason.

**The synthetic test underestimated the RAM cost.** At 2 x 131,072 with the draft head, the test with both slots full
left 7.8 GB of RAM available. Under a real four-hour agent job the same option was down to **about 1.7 GB**
(lowest seen 1.6 GB). Swap did not grow and nothing failed, but that is too thin for unattended work. About 2 GB of
the difference is the server's prompt cache (`--cache-ram 2048`), which the test barely used; the rest was not
identified.

**What was done.** The everyday option dropped the draft head (`flash-next-q4-2x128k-plain`): 15.5 GB available in
the test, and never below 11.5 GB during a day of benchmarks. It costs one-request speed (36 tok/s instead of 48-52)
and almost nothing when both workers write.

Upstream has since worked on the draft context's memory (for example
[#98](https://github.com/stew675/llama-cpp-rdna-boosts/pull/98)); not tested here.

## 5. Reasoning effort and the xhigh loop

- **The chat template defaults to xhigh**, for both models. With nothing sent, the prompt begins with a system line
  "Reasoning effort is set to xhigh. ...". `high` is treated as `xhigh`; the others are `medium` and `low`.
- **The agent sends medium.** Hermes sends `"reasoning_effort":"medium"` with every request (captured on the wire),
  and llama-server honours it as a top-level field. `/apply-template` shows what any request renders to without
  generating: with `medium`, the xhigh system line is absent.
- **So a test with nothing sent is not what the agent gets.** An early comparison here was wrong for this reason: the
  27B had been measured at the template default and Flash-Next at medium. At medium the 27B's draft acceptance is
  higher (0.44-0.58 against 0.33-0.47) and it is faster (43-74 tok/s short against 36-48).

One coding prompt (an expression evaluator, 29 hidden tests, seed 42, one run each):

| Model and effort | Thinking tokens | Total time | Hidden tests |
|---|---|---|---|
| Flash-Next IQ3_XXS, xhigh | 28,022, then 31,978 tokens of the digit 9 | 25.2 min, stopped by the 60,000-token cap | no answer |
| Flash-Next IQ3_XXS, medium | 4,645 | 2.2 min | 29 of 29 |
| 27B Q5_K_XL, medium | 6,081 | 2.2 min | 29 of 29 |
| 27B Q5_K_XL, xhigh | 32,913 | 15.1 min | 29 of 29 |

- **The xhigh loop.** Flash-Next's thinking was coherent for 28,022 tokens; while writing an example of a very large
  number it began emitting `9` and never stopped. This is not the `////` corruption. **It happened in one test**;
  whether it is typical is unknown. The 27B wrote a similar number at xhigh and carried on.
- **ISTA's position.** The quant's authors say it was calibrated with xhigh traces and that "when the reasoning effort
  is reduced the performance gap can become noticeably larger"
  ([discussion 14](https://huggingface.co/ISTA-DASLab/Qwen3.8-Flash-Next-GSQ-RCO-GGUF/discussions/14)). That is one
  reason the AtomicChat quant became the main one here. No quality difference between the quants was measured.
- **Not tested:** `--reasoning-budget N`, which caps thinking and might make xhigh usable; a second xhigh run.

## 6. min_p

- Hermes sends no sampling settings, so the server's defaults decide.
- Temperature 1.0, top_p 0.95 and top_k 20 are stored in the model files and match the model card. `min_p` is not:
  llama.cpp's own default is 0.05, and the card says 0.0 for thinking mode.
- `--min-p 0` is in every option file for that reason.
- **Measured difference: none to speak of.** One coding prompt on the 27B at medium was correct both ways (6,081
  thinking tokens and 130 s at 0.05; 5,985 and 137 s at 0.0). The change is for consistency with the card.

## 7. The grammar error on TC-65, 66, 67 and 69

Four tool-eval-bench scenarios combine tools with a JSON schema for the answer. On both servers, in every run, the
request is refused before the model runs:

```
HTTP 400  Failed to initialize samplers: failed to parse grammar
server log:  parse: error parsing grammar: expecting newline or end at ::= | " " | "\n"{1,2} [ \t]{0,20}
```

- Same result on the r20 and r30 builds (same llama.cpp base, `84e76d8a2`). The unpatched llama.cpp was not tested,
  so whether the patch set is involved is not known.
- TC-64, a schema without tools, works.
- tool-eval-bench recognises this as a serving failure and removes those scenarios from the score. **Neither model was
  tested on tools combined with structured output**, and both scores are "out of" fewer than 69 scenarios.
- Each refusal leaves a pair of `E` lines in the server log. They are expected during this benchmark.

## 8. The TC-45 grading difference

TC-45 sends `tool_choice="required"`. The tool first probes whether the endpoint enforces it.

| Server | What happened |
|---|---|
| Flash-Next, r30 build | Probe says the endpoint does not enforce it; TC-45 is left out. Graded on 64 scenarios |
| 27B, r20 build | TC-45 is graded; the 27B failed it in the three full runs ("No tool calls despite tool_choice='required'") and passed it in the context-pressure run. Graded on 65 |

So the tool's two headline scores have different denominators (128 and 130 points). The comparison in
[results/tool-eval-main.md](results/tool-eval-main.md) uses the 64 scenarios graded for both. Why the probe comes out
differently on the two builds was not investigated.

## ROCm 10 setup gotchas

- **`apt full-upgrade` moved the kernel to 7.0.** ROCm 10 with `amdgpu-dkms` was used on 6.17 here, so 6.17.0-42 was
  reinstalled and pinned with `GRUB_DEFAULT`. Check `uname -r` after any upgrade.
- **The `--no-dkms` shortcut in some guides is for Ryzen APUs**, not a discrete card. A discrete card needs
  `amdgpu-dkms` first, then ROCm from its own repo.
- **Secure Boot.** At the blue "Perform MOK management" screen choose Enroll MOK, Continue, Yes, the password, then
  **Reboot**. "Continue boot" leaves the key untrusted and the driver silently fails to load (`dmesg`: "Loading of
  module with unavailable key is rejected"). The key file on Ubuntu is `/var/lib/shim-signed/mok/MOK.der`.
  Check with `lsmod | grep amdgpu`.
- **ROCm 10 installs to `/opt/rocm/core-10.0`.** `amd-smi` replaces `rocm-smi`.
- **`llama-server` fails at runtime with a missing `libhipblas.so.3`** until `/opt/rocm/core-10.0/lib` is added to
  `/etc/ld.so.conf.d/` and `ldconfig` is run.
- **cmake does not find the compiler** without
  `HIPCXX="$(hipconfig -l)/clang" HIP_PATH="$(hipconfig -R)"` in front of the configure command.
- **The CPU's built-in graphics shows up as a second GPU.** Run with `HIP_VISIBLE_DEVICES=0`.
- **The patch script needs a git identity.** `git am` stops with "Committer identity unknown" and leaves an empty
  `rdna-boosts` branch; set `user.name` and `user.email`, check out the base commit, delete the branch, run it again.
- **The default of 4 server slots ties up about 3 GiB of VRAM.** Set `-np` to the number of agents.

## The 220 W power cap

`sudo amd-smi set -g 0 -o 220`, applied at every server start by an `ExecStartPre` line in the systemd unit.
Measured on the 27B with two workers:

| Measure | 300 W (default) | 220 W |
|---|---|---|
| Temperature under load | 87-89 °C | 78 °C |
| Power | 290-295 W | 219 W |
| Prompt reading | 794 tok/s | 769 tok/s |
| Writing per worker | 21.9 tok/s (119k tokens) | 26.3 tok/s (7k tokens, small sample) |

- **Reading lost about 3%; writing did not drop.** The two writing figures are from different amounts of work and
  should not be read as a gain.
- **Single sensor readings above 220 W do not mean the cap failed.** Read 20 times a second, the mean was 220.7 W
  while reading a 59k-token prompt and 219.6 W with two requests writing, with single readings up to 306 W lasting
  about 0.05 s. Judge the cap by an average.
- The allowed range on this card is 210-300 W. `THROTTLE_STATUS` reads `THROTTLED` all the time, even idle.

Full tables: [results/power-cap.md](results/power-cap.md).

## Smaller things

- **A 90-second stop.** With llama-server started as a child of a bash script, systemd's stop signal reached it
  twice and it hung until the timeout. `exec` on the script's last line fixed it (0.17 s for the next stop).
- **`seq_rm: rollback crossed a batch boundary`** is logged now and then when one slot reads a large prompt while the
  other is generating with drafting. `GGML_CUDA_GDN_CHUNKED=0` did not stop it. One such warning in each of the two
  real agent jobs; no wrong answer was traced to it.
- **While one slot reads a very large prompt, the other slot's writing drops to a few tok/s.** Expected with two
  slots on one card.
- **A text check can be too strict.** An early rule, "25 identical characters in a row", matched 28 spaces of code
  indentation and a number with 39 zeros. It now ignores whitespace and needs a run of 200; real failures were
  thousands long.
- **Sizing a test prompt by characters fails** when part of the source text has twice the tokens per character.
  Find the length by bisection against the server's tokenizer.
