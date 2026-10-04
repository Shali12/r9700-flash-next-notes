# Stage 1 (2026-10-02): Flash-Next ISTA IQ3_XXS against the 27B

Tables are copied unchanged from the rig's setup guide, where each was written down at the time of the test. All speeds are tokens per second. Every configuration was text-checked before any speed was measured (three fixed prompts with known answers); a configuration that failed was rejected and has no speed.

Effort: the chat template's default (xhigh) for both models in this table, and llama.cpp's default `min_p` 0.05.
The like-for-like numbers at medium effort are in [speed-stage1d-quants-and-draft-head.md](speed-stage1d-quants-and-draft-head.md).
One GPU (R9700, 220 W cap). `27b-q5xl` ran on the r20 build with its built-in draft head; `flash-next` on the r30 build
with `GGML_SCHED_DEVGATHER=0`, a 4 GB expert cache and no drafting.

## Result

|Measure|27B Q5_K_XL (`27b-q5xl`)|Flash-Next (`flash-next`)|
|---|---|---|
|Slots x context|2 x 85,248|1 x 131,072|
|Writing, short prompt (three runs)|45.0, 36.1, 47.6 tok/s|38.8, 39.0, 38.8 tok/s|
|Writing after an 8k-token prompt|34.2|38.3|
|Writing after a 32k-token prompt|37.3|36.4 (on candidate A, see below)|
|Writing after a 64k-token prompt|34.0|33.6 (on candidate A)|
|Writing after a full-context prompt|not applicable (85k slots)|28.0 after 129,654 tokens|
|Reading a prompt|816-973 tok/s|614-639 tok/s|
|Server down during a `rig-model` switch|4-14 s|about 28 s|
|Process RAM|about 2 GB once loaded|29.4 GB after load, 34.1 GB peak|
|Lowest available RAM|not limiting|28.5 GB|
|VRAM free at full context|about 1.4 GB (two full slots)|1,721 MB after the 129,654-token prompt|
|Drafting|on (acceptance about 0.33-0.47)|off|
|Coding test at medium (what Hermes sends)|6,081 thinking tokens, 130 s, 29 of 29 correct|4,645 thinking tokens, 134 s, 29 of 29 correct|
|Coding test at xhigh|32,913 thinking tokens, 15.1 min, 29 of 29 correct|28,022 thinking tokens, then a loop; 25.2 min; no answer|

Two requests at once were measured only in an earlier 70k configuration (2 slots x 35k): Flash-Next 30.6 + 30.6 = 61.2 tok/s
combined, 27B 19.6 + 20.3 = 39.9 on the same pair of prompts.

## Every configuration tried, in order of discovery

"rejected" means a reply failed the text check. Speeds are tok/s writing after a prompt of the given size.

|Configuration (r30 build unless said)|Text check|Short|8k|32k|64k|Full|Lowest available RAM|Verdict|
|---|---|---|---|---|---|---|---|---|
|Gather on (the default), with or without the expert cache|**rejected**: `////////`|not valid|||||9.4 GB|Every number measured this way on 2026-10-01 (17-19 tok/s plain, 48 tok/s with the cache, "0 drafts accepted") is void|
|r20 production build, no cache|pass|16.8-17.0|16.9||||8.3 GB|correct but slow|
|Gather off, no cache|pass|not measured|||||9.5 GB|correct|
|Gather off, draft sidecar (fixed depth 3), no cache|pass|17.8-19.6|18.1||||7.9 GB|drafting adds almost nothing|
|Gather off, 2 GB cache, table in RAM, 28 layers in RAM, 70k|pass|40.3-40.6|39.5|37.1|33.9||8.3 GB|only 92 MB VRAM free at 64k|
|Same with 29 layers in RAM|pass|39.9-40.0|39.3|36.8|33.6||7.2 GB|1.2 GB VRAM free at 64k|
|Same, 2 slots x 35k|pass|39.8-40.3|||||7.0 GB|pair: 30.6 + 30.6|
|A: table on disk, 36 layers in RAM, 6 GB cache, 128k|pass|39.5-39.9|39.1|36.4|33.6|28.9 at 125k|27.1 GB|1,055 MB VRAM free at 125k|
|B: table on disk, all 48 layers in RAM, 16 GB cache, 128k|pass|40.6-42.0|41.0||34.9||15.9 GB|reads slower: 518-540 tok/s|
|**C: table on disk, 35 layers in RAM, 4 GB cache, 128k**|pass|38.8-39.1|38.2|||28.0 at 130k|28.5 GB|**the option**; 1,721 MB VRAM free at 130k|

## Loading modes

The rig has 61 GiB of RAM. The n-gram table is 26.8 GiB and the RAM-side experts 20-40 GiB.

|`--load-mode` / `--lazy-mode`|What happened|
|---|---|
|`mmap` / `on`|Process RAM climbed to 59.6 GB and swap grew by 1.7 GB. In mmap mode the RAM-side experts exist twice (the mapped file and the working copy). The build warns: "tensor overrides to CPU are used with mmap enabled - consider using --load-mode none"|
|`dio` / `off`|Steady at 49.6 GB, then jumped past 57 GB while reading the file data; stopped by the guard. Direct I/O appears to read through a temporary copy (inferred, not confirmed)|
|`none` / `off`|Works. The table is loaded into RAM: process 46.6 GB with 24 layers in RAM, up to 56.5 GB peak with 32 layers and a 6 GB cache (available RAM fell to 4.0 GB). Tight|
|**`none` / `on`**|**Works best.** The table stays on disk and only the rows needed are read; everything else loads with plain reads. Process 29.4 GB, 28 GB available, load in 27-29 s|

## Reasoning effort, one coding prompt

An arithmetic expression evaluator without `eval`, 29 hidden test cases, default sampling, seed 42, one run each.

|Model and effort|Thinking tokens|Total time|Hidden tests|Result|
|---|---|---|---|---|
|Flash-Next, xhigh|28,022, then 31,978 tokens of the digit 9|25.2 min (stopped by the 60,000-token cap)|no answer produced|fail|
|Flash-Next, medium|4,645|2.2 min|29 of 29|correct|
|27B, medium|6,081|2.2 min|29 of 29|correct|
|27B, xhigh|32,913|15.1 min|29 of 29|correct|
