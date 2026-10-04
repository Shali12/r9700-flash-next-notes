# Stage 1e (2026-10-02): 2 x 131,072 and 1 x 262,144 on AtomicChat Q4_K_M

Tables are copied unchanged from the rig's setup guide, where each was written down at the time of the test. All speeds are tokens per second. Every configuration was text-checked before any speed was measured (three fixed prompts with known answers); a configuration that failed was rejected and has no speed.

Medium effort, temperature 1.0, top_p 0.95, top_k 20, min_p 0; gather off; 4 GB expert cache; r30 build.
"Every slot full" means a prompt of about 129,500 tokens pinned to each slot (260,203 tokens for the single 262,144 slot).

|Measure|2 x 131,072, no draft head|**2 x 131,072, draft head depth 3**|1 x 262,144, no draft head|
|---|---|---|---|
|Expert layers in RAM (`-ncmoe`, of 48)|41|47|45|
|Text check, three questions, five in a row|pass|pass|pass|
|Largest prompt held|129,088 and 129,017 tokens at once|the same|260,203 tokens|
|VRAM free with every slot full|3,370 MB|1,845 MB|2,373 MB|
|RAM available with every slot full (lowest)|15.5 GB|7.8 GB|11.3 GB|
|Process RAM peak|48.7 GB|56.3 GB|52.5 GB|
|Writing, short prompt, one agent|36.1-36.4 tok/s|48.2-52.1|34.9-35.2|
|Writing, short prompt, both at once|25.0 + 25.0 = 50.1|25.9 + 22.3 = 48.2|n/a|
|Writing at full context, one agent|27.0|34.2-34.4|20.4-20.5|
|Writing at full context, both at once|17.3 + 17.5 = 34.8|18.8 + 18.9 = 37.7|n/a|
|Reading a full prompt|496-504 tok/s|436-441|429|
|Time to read one full prompt|about 4.5 min|about 5 min|10.3 min|
|Swap|251 MB, unchanged|250 MB|250 MB|

The first column is the option `flash-next-q4-2x128k-plain`; the second is `flash-next-q4-2x128k`. No option was made
for 1 x 262,144. The draft head was not tried at 1 x 262,144.
