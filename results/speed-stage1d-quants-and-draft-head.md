# Stage 1d (2026-10-02): three Flash-Next quants and the draft head

Tables are copied unchanged from the rig's setup guide, where each was written down at the time of the test. All speeds are tokens per second. Every configuration was text-checked before any speed was measured (three fixed prompts with known answers); a configuration that failed was rejected and has no speed.

Everything here is at medium effort with temperature 1.0, top_p 0.95, top_k 20, min_p 0, except ISTA's rows other than
"short" and the coding prompts, which are from the Stage 1 session (template-default effort, `min_p` 0.05).
Gather off (`GGML_SCHED_DEVGATHER=0`), 4 GB expert cache, r30 build. The 27B column was measured through the live
service on the r20 build.

## What the files contain

Read from the GGUF headers before downloading, with `scripts/gguf_multi.py`.

|Property|ISTA IQ3_XXS|AtomicChat AD-4.27bpw Q4_K_M|Unsloth UD-IQ4_XS|Unsloth UD-Q3_K_XL (not downloaded)|
|---|---|---|---|---|
|Files|2 shards, 75.8 GB|33 shards, 94.5 GB|3 shards, 93.7 GB|3 shards, 90.0 GB|
|Must be in memory|43.8 GiB|52.3 GiB|60.4 GiB|57.0 GiB|
|N-gram table|26.8 GiB, IQ4_NL, alone in shard 2|35.8 GiB, Q5_1, alone in shard 2|26.8 GiB, IQ4_NL, inside shard 2|26.8 GiB, IQ4_NL, inside shard 2|
|Expert quant types|seven types incl. Q2_0|IQ4_NL, IQ2_S, IQ3_S|IQ3_S, IQ4_NL, Q8_0, IQ4_XS|IQ3_XXS, IQ4_NL, Q8_0, IQ4_XS|
|Draft head inside|no|no|no|no|
|Chat template|standard|an older version|standard|standard|
|Where|`~/models/flash-next`|`~/models/flash-next-atomic`|`~/models/flash-next-unsloth` (deleted 2026-10-04)|n/a|

## One slot x 131,072

|Measure|27B Q5_K_XL|ISTA IQ3_XXS|AtomicChat, no draft head|**AtomicChat, draft head depth 3**|Unsloth IQ4_XS|
|---|---|---|---|---|---|
|Experts kept in RAM (`-ncmoe`)|n/a|35 layers|38 layers|44 layers|39 layers|
|Writing, short prompt|43-74 (six runs)|38.7-39.1|37.1-37.2|51.7-54.9|33.2-33.7|
|Writing after 8k|52.0|38.3|36.9|54.4|33.4|
|Writing after 64k|40.6|33.6|32.1|43.2|29.2|
|Writing at full context (about 130k)|n/a (85k slots)|28.0|27.5|35.0|25.4|
|Reading a prompt|815-990|614-639|526-589|463-510|487-542|
|Two requests at once (2 slots)|54.4|not run at 128k|52.1|56.5 (in the 2 x 65,536 option)|45.5|
|VRAM free at full context|about 1.4 GB|1,721 MB|2,147 MB|1,377 MB|2,176 MB|
|Lowest RAM available|not limiting|28.5 GB|19.0 GB|11.8 GB|10.4 GB|
|Coding prompt 1: thinking tokens, time, hidden tests|5,985, 2.3 min, 29/29|2,404, 1.3 min, 29/29|3,344, 1.8 min, 29/29|4,657, 1.8 min, 29/29|3,893, 2.2 min, 29/29|
|Coding prompt 2|1,337, 0.6 min, 16/16|1,081, 0.6 min, 16/16|1,756, 1.0 min, 16/16|1,398, 0.6 min, 16/16|1,026, 0.7 min, 16/16|
|Gather on|n/a|rejected|rejected|not tried|rejected|

Coding prompt 1 is the expression evaluator (29 hidden tests); prompt 2 groups tasks with dependencies into ordered
batches (16 hidden tests). Every model and quant passed both, so they show that nothing is broken at medium; they do
not rank the quants. Thinking-token counts vary from run to run at temperature 1.0; one run each.

Draft head, depth 3 against depth 5 (AtomicChat, one slot): depth 3 gave 52-55 tok/s short and 43.2 after 64k with
acceptance 0.80-0.90; depth 5 gave 48-54 short and 42.3 after 64k with acceptance 0.63-0.81.

## Two slots x 65,536, AtomicChat

"Both full" is two different prompts of about 60,000 tokens sent at the same time.

|Measure|No draft head, 38 layers in RAM|Draft head depth 3, 44 layers in RAM|**Draft head depth 3, 40 layers in RAM**|
|---|---|---|---|
|Two requests at once|26.1 + 26.1 = 52.1 tok/s|29.4 + 24.3 = 53.7|30.6 + 25.9 = 56.5|
|One request alone|about 37 (from the 1-slot load)|49.3-53.4|56.1-57.5|
|Reading with both slots busy|521-531 tok/s|453-460|482-489|
|VRAM free, both slots full|4,815 MB|6,442 MB|1,764 MB|
|Lowest RAM available|19.0 GB|11.7 GB|16.3 GB|

Unsloth IQ4_XS, 2 slots, no draft head: 22.8 + 22.8 = 45.5 tok/s combined; 4,863 MB of VRAM free and 10.6 GB of RAM
available with both slots full.

## The options that came out of it

|Option|Model|Slots x context|Draft head|`-ncmoe`|Role|
|---|---|---|---|---|---|
|`flash-next-q4`|AtomicChat Q4_K_M|1 x 131,072|depth 3|44|main Flash-Next option|
|`flash-next-q4-2x64k`|AtomicChat Q4_K_M|2 x 65,536|depth 3|40|two agents, faster reading|
|`flash-next-q4-2x128k`|AtomicChat Q4_K_M|2 x 131,072|depth 3|47|two agents, most room each (added in Stage 1e)|
|`flash-next-q4-2x128k-plain`|AtomicChat Q4_K_M|2 x 131,072|none|41|the same with RAM to spare, for long unattended work (added 2026-10-03 after Stage 3)|
|`flash-next`|ISTA IQ3_XXS|1 x 131,072|none|35|secondary choice (lightest on RAM)|
