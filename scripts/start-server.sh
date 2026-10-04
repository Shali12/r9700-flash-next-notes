#!/bin/bash
# Starts llama-server with one of the model options in ~/model-options (one small .conf file each).
# Which one: the name saved in ~/model-options/current. Change it with: rig-model NAME
# To see the command for an option without starting anything: ~/start-server.sh --print NAME
OPTIONS=~/model-options
FALLBACK=27b-q5xl

NAME=$(cat "$OPTIONS/current" 2>/dev/null)
if [ "$1" = "--print" ]; then
  PRINT=1
  NAME=${2:-$NAME}
elif [ ! -f "$OPTIONS/$NAME.conf" ]; then
  echo "start-server: no model option '$NAME' in $OPTIONS; starting $FALLBACK instead" >&2
  NAME=$FALLBACK
fi
source "$OPTIONS/$NAME.conf" || exit 1

# An option may set BUILD (the llama.cpp folder to run from) and ENVS (environment variables).
# Without them it is the production build, ~/llama.cpp-rdna, and no extra variables.
cd "${BUILD:-$HOME/llama.cpp-rdna}" || exit 1
# ARGS comes from the option file (the model and its settings). The second line is the same for
# every option: Hermes and the status script rely on this name, address, port and --metrics.
CMD=(./build/bin/llama-server "${ARGS[@]}"
  --metrics --alias qwen3.8_local --host "$(tailscale ip -4)" --port 8080)

if [ -n "$PRINT" ]; then
  printf '%s\n' "${CMD[@]}"
  exit
fi
echo "start-server: model option $NAME ($LABEL), build $PWD${ENVS:+, env ${ENVS[*]}}"
for e in "${ENVS[@]}"; do export "$e"; done
# exec: this script becomes llama-server instead of waiting beside it. systemd then sends the
# stop signal once. Without exec the server got it twice, and often hung for 90 s on every stop.
HIP_VISIBLE_DEVICES=0 exec "${CMD[@]}"
