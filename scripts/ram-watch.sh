#!/bin/bash
# Logs RAM, swap and VRAM once a minute while a model serves real work. Reads /proc and sysfs only;
# sends nothing to the server. usage: ram-watch.sh [HOURS, default 12]   Log: fn-logs/ram-watch-DATE.log
L=$(dirname "$(readlink -f "$0")")/fn-logs/ram-watch-$(date +%F).log
END=$(( $(date +%s) + ${1:-12} * 3600 ))
while [ "$(date +%s)" -lt $END ]; do
  p=$(pgrep -x llama-server | head -1)
  echo "$(date '+%F %T') option $(cat ~/model-options/current) available $(awk '/^MemAvailable/{print int($2/1024)}' /proc/meminfo) MB, process anon $([ -n "$p" ] && awk '/RssAnon/{print int($2/1024)}' /proc/$p/status) MB, shared $([ -n "$p" ] && awk '/RssShmem/{print int($2/1024)}' /proc/$p/status) MB, swap used $(free -m | awk '/^Swap/{print $3}') MB, VRAM $(( $(cat /sys/bus/pci/devices/0000:03:00.0/mem_info_vram_used) / 1048576 )) MB" >> "$L"
  sleep 60
done
