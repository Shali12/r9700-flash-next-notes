# Model option files

One file per server setup, exactly as used on the rig. `scripts/start-server.sh` reads the one named in
`~/model-options/current` and starts `llama-server` with its `ARGS`, adding `--metrics --alias qwen3.8_local --host ... --port 8080`
to every option. `scripts/rig-model` lists them and switches between them.

| File | Model | Slots x context | Notes |
|---|---|---|---|
| `flash-next-q4-2x128k-plain.conf` | Flash-Next AtomicChat Q4_K_M | 2 x 131,072 | no draft head; the everyday setup since 2026-10-04 |
| `flash-next-q4-2x128k.conf` | Flash-Next AtomicChat Q4_K_M | 2 x 131,072 | draft head depth 3; short of RAM under real work |
| `flash-next-q4-2x64k.conf` | Flash-Next AtomicChat Q4_K_M | 2 x 65,536 | draft head depth 3 |
| `flash-next-q4.conf` | Flash-Next AtomicChat Q4_K_M | 1 x 131,072 | draft head depth 3 |
| `flash-next.conf` | Flash-Next ISTA IQ3_XXS | 1 x 131,072 | no draft head; lightest on RAM |
| `27b-q5xl.conf` | 27B Q5_K_XL | 2 x 85,000 | vision, built-in draft head; the fallback |
| `27b-q5xl-1agent.conf` | 27B Q5_K_XL | 1 x 170,000 | |
| `27b-q6xl.conf` | 27B Q6_K_XL | 1 x 90,000 | |
| `27b-q4xl.conf` | 27B Q4_K_XL | 3 x 70,000 | |

In every Flash-Next file, keep `GGML_SCHED_DEVGATHER=0`, the expert cache variables, and
`--lazy-mode on --load-mode none`; see [FINDINGS.md](../FINDINGS.md). The comments at the top of each file give the
measurements that option was accepted on. `HERMES_CONTEXT` is the context length to set in the agent, a little below
the per-slot size. Paths start with `~`; adjust them to where your model files are.
