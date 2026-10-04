#!/bin/bash
# tool-eval-bench comparison blocks (2026-10-03). One block = every step below against whichever model
# option is running now. It runs in its own detached tmux session, so it survives a closed SSH window.
#   teb.sh start          start a block for the running option (refuses if Hermes is using the server)
#   teb.sh start trials   only the two extra full runs (seeds 43 and 44), for the 3-trial comparison
#   teb.sh start hardmode only Hard Mode (--hardmode-only, TC-70 to TC-88), seeds 42, 43 and 44, after steps 0 and 1
#   teb.sh status         one screen: what is done, what is running, RAM
#   teb.sh stop           stop the benchmark (the model server is NOT touched)
# Steps of a block: 0 correctness (rig-model check + text-check.py), 1 proof that medium effort is applied,
# 2 --short (15 scenarios), 3 full 69 scenarios, 4 the same with --context-pressure 0.75 on an 85,248-token
# window, 5 IFEval (100 prompts). Settings are identical for every option: seed 42, temperature 1.0,
# top_p 0.95, top_k 20, min_p 0 (what Hermes gets), "reasoning_effort":"medium" (what Hermes sends).
# Guard: if swap use passes 1024 MB or available RAM falls below 6144 MB, the benchmark stops and says so.
# Results: blocks/OPTION-DATE-TIME/ (summary.txt first), reports in runs/, database in data/.
D=$(dirname "$(readlink -f "$0")"); T=$(dirname "$D"); cd "$D" || exit 1
TEB=$HOME/.local/bin/tool-eval-bench; RIGMODEL=$HOME/.local/bin/rig-model
URL="http://$(tailscale ip -4):8080"; MODEL=qwen3.8_local; SESSION=teb
OPT=$(cat ~/model-options/current)
avail() { awk '/^MemAvailable/{print int($2/1024)}' /proc/meminfo; }
swapmb() { free -m | awk '/^Swap/{print $3}'; }
busy() { curl -s -m 5 "$URL/metrics" | awk '/^llamacpp:requests_processing/{print int($2)}'; }

case "$1" in
start)
  tmux has-session -t "=$SESSION" 2>/dev/null && { echo "A benchmark block is already running. See: $0 status"; exit 1; }
  [ "$(curl -s -m 5 -o /dev/null -w '%{http_code}' "$URL/health")" = 200 ] || { echo "The model server does not answer. Nothing started."; exit 1; }
  B=$(busy); [ "${B:-1}" = 0 ] || { echo "The server is busy (${B:-?} request(s) running): Hermes must be idle. Nothing started."; exit 1; }
  tmux has-session -t ram-watch 2>/dev/null || tmux new-session -d -s ram-watch "$T/ram-watch.sh 48"
  tmux new-session -d -s $SESSION "$D/teb.sh _run ${2:-block}"
  echo "Started a ${2:-block} run for option $OPT in tmux session '$SESSION'. Check it with: $0 status"
  ;;
stop)
  [ -f blocks/current/pid ] && kill -INT "$(cat blocks/current/pid)" 2>/dev/null
  touch blocks/current/STOP 2>/dev/null; echo "Asked the benchmark to stop (the model server keeps running). See: $0 status"
  ;;
status)
  B=$(readlink -f blocks/current 2>/dev/null); [ -d "$B" ] || { echo "No block has been started yet."; exit 0; }
  tmux has-session -t "=$SESSION" 2>/dev/null && echo "RUNNING: $(basename "$B")" || echo "NOT RUNNING. Last block: $(basename "$B")"
  cat "$B/summary.txt" 2>/dev/null
  S=$(cat "$B/state" 2>/dev/null)
  if [ -n "$S" ] && [ -f "$B/$S.events" ]; then
    echo "now: $S, $(grep -c '"scenario_result"' "$B/$S.events") scenario(s) finished, running for $(( ($(date +%s) - $(stat -c %Y "$B/$S.started")) / 60 )) min"
    grep -a -o -E '"scenario_id": *"[^"]+", *"status": *"[^"]+"' "$B/$S.events" | tail -3 | tr -d '"' | sed 's/^/   /'
    tail -c 300 "$B/$S.out" 2>/dev/null | tr -d '\r' | grep -v '^ *$' | tail -2 | cut -c1-150 | sed 's/^/   /'
  fi
  echo "RAM available $(avail) MB, swap used $(swapmb) MB, VRAM $(( $(cat /sys/bus/pci/devices/0000:03:00.0/mem_info_vram_used) / 1048576 )) of 32624 MB; running option: $OPT"
  ;;
_run)
  MODE=$2; B=$D/blocks/$OPT-$([ "$MODE" = block ] || echo "$MODE-")$(date +%F-%H%M); mkdir -p "$B"; ln -sfn "$B" "$D/blocks/current"
  SUM=$B/summary.txt; SWAP0=$(swapmb)
  say() { echo "$(date '+%F %T') $*" | tee -a "$SUM"; }
  COMMON=(--base-url "$URL" --model $MODEL --backend llamacpp --temperature 1.0 --top-p 0.95 --top-k 20 --min-p 0
          --backend-kwargs '{"reasoning_effort":"medium"}' --timeout 600 --no-live --redact-url --label "$OPT")
  say "BLOCK ($MODE) for option $OPT; tool $($TEB --version 2>&1 | head -1); RAM available $(avail) MB, swap used $SWAP0 MB"
  # the guard: stops the benchmark, never the server
  ( while [ ! -f "$B/DONE" ]; do
      sleep 30
      if [ "$(swapmb)" -gt 1024 ] || [ "$(avail)" -lt 6144 ]; then
        echo "$(date '+%F %T') GUARD: swap $(swapmb) MB, RAM available $(avail) MB. Benchmark stopped." >> "$SUM"
        touch "$B/STOP"; kill -INT "$(cat "$B/pid" 2>/dev/null)" 2>/dev/null
      fi
    done ) &
  # step NAME HOURS command...: runs one tool command, saves its JSON, progress events and screen text
  step() {
    local name=$1 hours=$2; shift 2
    [ -f "$B/STOP" ] && { say "$name: skipped (the block was stopped)"; return 1; }
    echo "$name" > "$B/state"; touch "$B/$name.started"; local t0=$(date +%s)
    timeout --signal=INT "${hours}h" "$TEB" "$@" --json-file "$B/$name.json" > "$B/$name.out" 2> "$B/$name.events" &
    echo $! > "$B/pid"; wait $!; local rc=$?
    local mins=$(( ($(date +%s) - t0) / 60 ))
    local st; st=$(grep -a -o -E '"status": *"[^"]+"' "$B/$name.events" | sort | uniq -c | sed -E 's/"status": *"([^"]+)"/\1/' | awk '{printf "%s %s, ", $1, $2}')
    local top; top=$(jq -c 'with_entries(select((.value|type) != "object" and (.value|type) != "array")) | del(.schema_version, .run_id)' "$B/$name.json" 2>/dev/null | cut -c1-400)
    # text check on everything this step wrote: runs like "////" or 200 of one character
    local bad; bad=$(find runs "$B/$name.json" -newer "$B/$name.started" -type f 2>/dev/null | xargs -r python3 -c '
import re, sys
n = [f for f in sys.argv[1:] if (lambda t: "////" in t or re.search(r"(\S)\1{199,}", t))(open(f, errors="replace").read())]
print(len(n), " ".join(n))')
    say "$name: exit $rc, $mins min; scenarios: ${st:-none}text check: ${bad%% *} file(s) with garbage runs ${bad#* }"
    say "   $top"
    return $rc
  }
  finish() { say "BLOCK ENDED: $1; RAM available $(avail) MB, swap used $(swapmb) MB (was $SWAP0)"; touch "$B/DONE"; rm -f "$B/state"; exit 0; }

  # step 0: correctness before anything else (CLAUDE.md rule)
  echo step0 > "$B/state"
  "$RIGMODEL" check > "$B/step0-rig-model-check.txt" 2>&1; R1=$?
  python3 "$T/text-check.py" "$URL" $MODEL "teb-$OPT" > "$B/step0-text-check.txt" 2>&1; R2=$?
  say "step0 correctness: rig-model check exit $R1 ($(tail -1 "$B/step0-rig-model-check.txt" | cut -c1-80)); text-check exit $R2 ($(jq -c .results "$T/check/teb-$OPT/verdict.json" 2>/dev/null))"
  [ $R1 = 0 ] && [ $R2 = 0 ] || finish "correctness check failed, no benchmark run"

  # step 1: what the server does with "reasoning_effort":"medium" (it renders the prompt, generates nothing)
  echo step1 > "$B/state"
  python3 - "$URL" "$B" <<'EOF' >> "$SUM" 2>&1
import difflib, json, sys, urllib.request
url, out = sys.argv[1], sys.argv[2]
def render(extra):
    body = {"messages": [{"role": "user", "content": "What is 2+2?"}], **extra}
    req = urllib.request.Request(url + "/apply-template", json.dumps(body).encode(), {"Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=60))["prompt"]
plain, med = render({}), render({"reasoning_effort": "medium"})
open(out + "/step1-prompt-nothing-sent.txt", "w").write(plain); open(out + "/step1-prompt-medium.txt", "w").write(med)
diff = [l for l in difflib.unified_diff(plain.splitlines(), med.splitlines(), lineterm="", n=0) if l[:1] in "+-" and l[:3] not in ("+++", "---")]
print("step1 effort: prompt with nothing sent vs with medium:", "IDENTICAL (medium is NOT applied)" if not diff else "they differ")
for l in diff[:4]: print("   " + l[:230])
EOF

  if [ "$MODE" = trials ]; then
    step trial-seed43 5 run --seed 43 "${COMMON[@]}"
    step trial-seed44 5 run --seed 44 "${COMMON[@]}"
    finish "extra trials done"
  fi

  if [ "$MODE" = hardmode ]; then    # Hard Mode only: the 19 scenarios TC-70 to TC-88, three seeds
    for s in 42 43 44; do step hard-seed$s 3 run --hardmode-only --seed $s "${COMMON[@]}"; done
    [ -f "$B/STOP" ] && finish "stopped early (see the lines above)"
    finish "hard mode done"
  fi

  step step2-short 2 run --short --seed 42 "${COMMON[@]}" || finish "the short run failed; look at $B/step2-short.out"
  step step3-full 5 run --seed 42 "${COMMON[@]}"
  PRESS=(--context-pressure 0.75 --context-size 85248)
  if step step4a-pressure-probe 1 run --scenarios TC-01 TC-02 TC-03 --seed 42 "${PRESS[@]}" "${COMMON[@]}" &&
     [ "$(grep -c '"scenario_result"' "$B/step4a-pressure-probe.events")" = 3 ] &&
     ! grep -a -q -i -E '"status": *"(timeout|error|excluded|infra[a-z_]*)"' "$B/step4a-pressure-probe.events"; then
    step step4-pressure 9 run --seed 42 "${PRESS[@]}" "${COMMON[@]}"
  else
    say "step4-pressure: skipped, the 3-scenario probe did not complete cleanly"
  fi
  step step5-ifeval 5 plugin ifeval --limit 100 --seed 42 "${COMMON[@]}"
  grep -a -E "IFEval (Prompt|Instruction) Accuracy|Duration:" "$B/step5-ifeval.out" | tr -d '\r' | sed 's/^ */   /' | tee -a "$SUM"   # the plugin writes no JSON file

  # 3 trials only if the two models' full runs are within 5 points
  MINE=$(jq -r '.final_score // empty' "$B/step3-full.json" 2>/dev/null)
  # the newest block of a DIFFERENT option (blocks/current is a link to this block, so links are skipped)
  OB=$(for d in "$D"/blocks/*/; do d=${d%/}; [ -L "$d" ] && continue; case "$(basename "$d")" in "$OPT"-20*) ;; *) [ -f "$d/step3-full.json" ] && echo "$d";; esac; done | tail -1)
  OTHER=$([ -n "$OB" ] && jq -r '.final_score // empty' "$OB/step3-full.json" 2>/dev/null)
  if [ -n "$MINE" ] && [ -n "$OTHER" ]; then
    GAP=$(awk -v a="$MINE" -v b="$OTHER" 'BEGIN{d=a-b; if(d<0)d=-d; print d}')
    say "full-run scores: this option $MINE, the other model $OTHER, gap $GAP"
    if awk -v g="$GAP" 'BEGIN{exit !(g<=5)}'; then
      say "within 5 points: running two more full trials here (seeds 43, 44). The other model: $([ -f "$OB/trial-seed44.json" ] && echo "its two extra trials are already done" || echo "needs teb.sh start trials")"
      step trial-seed43 5 run --seed 43 "${COMMON[@]}"
      step trial-seed44 5 run --seed 44 "${COMMON[@]}"
    fi
  fi
  [ -f "$B/STOP" ] && finish "stopped early (see the lines above)"
  finish "all steps done"
  ;;
*) sed -n '2,7p' "$0";;
esac
