# Scripts

As used on the rig, unchanged apart from removing machine-specific names. They assume this layout:
option files in `~/model-options/`, `start-server.sh` in `~`, the test tools in `~/rig/tools/`, and `teb.sh` in
`~/rig/tools/tool-eval/`. Adjust the paths at the top of each script if yours differ.

| Script | What it does | Needs |
|---|---|---|
| `start-server.sh` | Started by a systemd service. Reads the option named in `~/model-options/current` and `exec`s `llama-server` with it. `--print NAME` shows the command without starting anything | `tailscale` (it binds to the machine's private address; replace `$(tailscale ip -4)` to bind elsewhere) |
| `rig-model` | Lists the options, previews one, or switches: restarts the service, waits for `/health`, asks three known-answer questions, and rolls back to the previous option if the start or the answers fail | `sudo` for `systemctl restart`, `curl`, `jq` |
| `text-check.py` | Three fixed prompts at temperature 0 with known answers; fails on a wrong answer, `////`, or a run of 200 of one character. Run it before any speed test | `fnmon.py` beside it; on first run it copies 28,000 characters of `~/llama.cpp-rdna/src/llama-sampler.cpp` as the text to summarise |
| `fnmon.py` | Small RAM-floor monitor imported by `text-check.py` | |
| `teb.sh` | Runs tool-eval-bench blocks against the running option in a detached tmux session: `start`, `start trials`, `start hardmode`, `status`, `stop`. Checks the text first; stops the benchmark, never the server, if swap passes 1 GB or available RAM falls below 6 GB | `tool-eval-bench` 2.7.0, `tmux`, `jq`, `text-check.py` and `ram-watch.sh` one folder up |
| `ram-watch.sh` | Logs available RAM, the server's memory, swap and VRAM once a minute. Reads `/proc` and sysfs only | the GPU at PCI address `0000:03:00.0`; change the path for another slot |
| `gguf_multi.py` | Reads GGUF headers, including from partial downloads of multi-shard files, and reports what must be in memory, the n-gram table, and the expert quant types | Python 3 |

The systemd unit that runs `start-server.sh`:

```ini
[Unit]
Description=llama.cpp server
After=network-online.target tailscaled.service
Wants=network-online.target

[Service]
Type=simple
User=YOUR-USER
ExecStartPre=+/usr/bin/amd-smi set -g 0 -o 220
ExecStart=/home/YOUR-USER/start-server.sh
Restart=on-failure
RestartSec=15

[Install]
WantedBy=multi-user.target
```
