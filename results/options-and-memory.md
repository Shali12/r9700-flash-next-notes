# Every option: settings and measured free memory

Tables are copied unchanged from the rig's setup guide, where each was written down at the time of the test. The option files themselves are in [`configs/`](../configs).

|Option|Model file|`SLOTS`|`CTX`|`HERMES_CONTEXT`|Expected free memory|
|---|---|---|---|---|---|
|`27b-q5xl`|Q5_K_XL (19,909 MB)|2|170000|82000|about 1.5 GB (measured)|
|`27b-q5xl-1agent`|Q5_K_XL|1|170000|165000|2.9 GB (measured 2026-10-01 after one 148,559-token prompt; 3.7 GB after load)|
|`27b-q6xl`|Q6_K_XL (24,127 MB, +4,218)|1|90000|87000|2.1 GB (measured 2026-10-01 after one 85,796-token prompt; the estimate was 1.6 GB)|
|`27b-q4xl`|Q4_K_XL (16,745 MB, -3,164)|3|210000|67000|1.4 GB (measured 2026-10-01 after three ~65,700-token prompts at once; the estimate was 1.6 GB)|
|`flash-next`|Flash-Next IQ3_XXS (two files, 75.8 GB; another model, another build)|1|131072|125000|1.7 GB of VRAM (measured 2026-10-02 after one 129,654-token prompt); RAM: 28.5 GB available|
|`flash-next-q4`|Flash-Next AtomicChat Q4_K_M (33 files, 94.5 GB) plus the draft head|1|131072|125000|1.4 GB of VRAM (after one 129,612-token prompt); RAM: 11.8 GB available|
|`flash-next-q4-2x64k`|the same|2|131072|62000|1.8 GB of VRAM (both slots holding about 60,000 tokens); RAM: 16.3 GB available|
|`flash-next-q4-2x128k`|the same|2|262144|125000|1.8 GB of VRAM (both slots holding about 129,000 tokens); RAM: 7.8 GB available in the test, about 1.7 GB under a real Hermes run (2026-10-03)|
|`flash-next-q4-2x128k-plain`|the same without the draft head|2|262144|125000|3.4 GB of VRAM (both slots holding about 129,000 tokens, hand-run 2026-10-02); RAM: 15.5 GB available. First switch through `rig-model` 2026-10-03: 48 s, three questions correct, 7,974 MB of VRAM free after loading|

The card has 32,624 MB. Rules of thumb measured on the 27B: each slot costs about 1.4-1.5 GB up front, each 1,000
tokens of context about 38 MB, the vision encoder about 0.9 GB.

## Sampling

Hermes sends no sampling settings, so the server's defaults apply to all its work.

|Setting|Server default before|Recommended|Where it comes from|
|---|---|---|---|
|temperature|1.0|1.0|stored in every model file (`general.sampling.temp`)|
|top_p|0.95|0.95|stored in every model file|
|top_k|20|20|stored in every model file|
|min_p|0.05|0.0|not in the files; llama.cpp's own default|
|presence penalty, repetition penalty|off|off|llama.cpp's defaults|

`--min-p 0` is in every option file. Measured difference on one coding prompt at medium (27B): correct both ways,
6,081 thinking tokens and 130 s at `min_p` 0.05, 5,985 and 137 s at 0.0.
