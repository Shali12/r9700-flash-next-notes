# Stage 3 (2026-10-02 and 2026-10-03): one real delegated job on each model

The same job was given to Hermes Agent twice: a small game built as four delegated tasks, two local workers at a time,
each worker's result checked by a cloud parent model. Run A used `27b-q5xl` (2 x 85,248); Run B used
`flash-next-q4-2x128k` (2 x 131,072, with the draft head). The rows are the owner's summary of the two Hermes reports;
the rollback warnings and the times of day are from the rig's server log. **One run each: indicative, not conclusive.**

|Item|Run A: 27B Q5_K_XL, 2 x 85k|Run B: Flash-Next Q4_K_M, 2 x 128k, draft head|
|---|---|---|
|When (server log)|2026-10-02, about 21:00-23:30|2026-10-03, about 06:50-10:50|
|Wall-clock|about 2 h 30 m (about 2 h effective: one compaction and an abandoned 41-minute worker)|about 4 h 10 m|
|Tasks that passed first review|3 of 4|4 of 4|
|Re-delegations|1 (the worker shipped a duplicate-identifier crash in the bundled game; the parent's browser check caught it)|0|
|New tests|26|37|
|Rollback warnings in the server log|1|1|
|RAM available on the rig under the real load|not limiting|about 1.7 GB (lowest seen 1.6 GB)|
|Result|game playable|game playable; the owner slightly preferred this one|

After this run the draft-head option was replaced for everyday use by `flash-next-q4-2x128k-plain` (no draft head,
`-ncmoe 41`): 15.5 GB of RAM available with both slots full in the Stage 1e test.
