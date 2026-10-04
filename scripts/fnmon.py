"""RAM floor monitor: samples MemAvailable every 2 s; below the floor it stops llama-server (if allowed) and exits."""
import os, signal, subprocess, threading, time

FLOOR_MB = int(os.environ.get("RAM_FLOOR_MB", "6000"))
lowest = [10**9]
tripped = [False]

def avail_mb():
    for line in open("/proc/meminfo"):
        if line.startswith("MemAvailable"):
            return int(line.split()[1]) // 1024
def swap_mb():
    return int(subprocess.run("free -m | awk '/^Swap/{print $3}'", shell=True, capture_output=True, text=True).stdout or 0)

def start(kill=True):
    def loop():
        while True:
            a = avail_mb(); lowest[0] = min(lowest[0], a)
            if a < FLOOR_MB and not tripped[0]:
                tripped[0] = True
                print(f"\n!! available RAM fell to {a} MB (floor {FLOOR_MB}): " + ("stopping the server; this configuration is rejected" if kill else "below the floor"), flush=True)
                if kill:
                    subprocess.run(["pkill", "-TERM", "-x", "llama-server"])
                    time.sleep(1); os.kill(os.getpid(), signal.SIGTERM)
            time.sleep(2)
    threading.Thread(target=loop, daemon=True).start()

def summary():
    return f"lowest available RAM {lowest[0]} MB, swap {swap_mb()} MB"


RECOMMENDED = {"temperature": 1.0, "top_p": 0.95, "top_k": 20, "min_p": 0.0, "presence_penalty": 0.0, "frequency_penalty": 0.0, "repeat_penalty": 1.0}

def extra(sampling=True):
    """Request fields set by the environment: FN_EFFORT=medium|low|xhigh (unset: send none),
    FN_SAMPLING=recommended (the model card's thinking-mode settings; unset: server defaults)."""
    e = {}
    if os.environ.get("FN_EFFORT"): e["reasoning_effort"] = os.environ["FN_EFFORT"]
    if sampling and os.environ.get("FN_SAMPLING") == "recommended": e.update(RECOMMENDED)
    return e

def describe():
    return f"effort sent: {os.environ.get('FN_EFFORT') or 'none (template default xhigh)'}; sampling: {'recommended (temp 1.0, top_p 0.95, top_k 20, min_p 0)' if os.environ.get('FN_SAMPLING') == 'recommended' else 'server defaults'}"
