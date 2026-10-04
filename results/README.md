# Results

| File | What is in it |
|---|---|
| [speed-stage1-ista-vs-27b.md](speed-stage1-ista-vs-27b.md) | ISTA IQ3_XXS against the 27B; every configuration tried; loading modes; reasoning effort on one coding prompt |
| [speed-stage1d-quants-and-draft-head.md](speed-stage1d-quants-and-draft-head.md) | ISTA, AtomicChat and Unsloth quants at medium effort; the draft head; two slots x 65,536 |
| [speed-stage1e-more-context.md](speed-stage1e-more-context.md) | 2 x 131,072 with and without the draft head; 1 x 262,144 |
| [options-and-memory.md](options-and-memory.md) | Every option's settings and measured free memory; sampling defaults |
| [tool-eval-main.md](tool-eval-main.md) | tool-eval-bench main suite (three seeds), context pressure, IFEval, per-scenario table |
| [tool-eval-hard-mode.md](tool-eval-hard-mode.md) | Hard Mode (three seeds) with the per-scenario table and the grader's reasons |
| [stage3-hermes-job.md](stage3-hermes-job.md) | One real delegated job on each model |
| [power-cap.md](power-cap.md) | 300 W against 220 W; whether the cap holds |
| [raw/tool-eval/](raw/tool-eval) | The benchmark's JSON results, its Markdown reports with full traces, and each block's `summary.txt` |

Where the numbers come from:

- The speed, memory, power and real-job tables are copied unchanged from the setup guide kept on the rig, where each
  was written down at the time of the test.
- The two tool-eval files are computed from the JSON files in `raw/tool-eval/`.
- A value marked "estimate" or "about" was not measured exactly; everything else was.

In the raw files, the machine's host name, its file paths and the tool's endpoint identifier (a hash of the server address) were replaced; nothing else was edited. The server address
is masked by the tool itself (`http://***:8080`). Names and e-mail addresses inside the traces (for example in TC-79)
are the benchmark's own fictional test data.
