# The 220 W power cap

Tables are copied unchanged from the rig's setup guide, where each was written down at the time of the test. Set with `sudo amd-smi set -g 0 -o 220`, and applied at every server start by an `ExecStartPre` line in the
systemd unit. Measured on the 27B, two workers, 2026-09-30 and 2026-10-01.

|Measure|Before (300 W)|After (220 W)|
|---|---|---|
|Temperature under load|87-89 °C|78 °C|
|Power|290-295 W|219 W|
|Writing speed per worker|21.9 tok/s (119k tokens)|26.3 tok/s (7k tokens, small sample)|
|Prompt reading|794 tok/s|769 tok/s|

The 220 W writing figure is from a small sample (7k tokens against 119k before the cap).

## Is the cap holding? Sensor read 20 times a second

|Load (everyday option)|Mean|Average over any 5 s|Readings above 225 W|Highest single reading|`amd-smi` at the same time|
|---|---|---|---|---|---|
|One slot reading a 59k-token prompt, 75 s|220.7 W|220-222 W|4%|306 W|217-221 W, with 240 and 258 once each|
|Two requests writing 1,500 tokens each at once, 68 s|219.6 W|219-222 W|11%|287 W|214-228 W|

"Everyday option" in this table is `27b-q5xl`. The high single readings are blips of about 0.05 s, plus a burst of up
to about 0.8 s when a load starts from idle. This card has one power limit: `PPT0`, allowed range 210-300 W.
