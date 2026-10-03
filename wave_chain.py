# wave_chain.py — waits for current mass_seed shards to die, then launches next wave
# with the expanded pool. Loops forever (pool grows from hunters/merge every 15 min).
import json, os, subprocess, sys, time

BASE = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE)

def running_shards():
    # psutil instead of PowerShell CIM (CIM hangs on this machine)
    try:
        import psutil
        n = 0
        for p in psutil.process_iter(['cmdline']):
            try:
                cl = ' '.join(p.info['cmdline'] or [])
                if ('shard_worker' in cl or 'mass_seed.py' in cl) and 'process_iter' not in cl and 'wave_chain' not in cl:
                    n += 1
            except Exception:
                pass
        return n
    except Exception:
        return 0

def pool_size():
    try: return len(json.load(open("pool_merged.json", encoding="utf-8")))
    except Exception: return 0

wave = 0
while True:
    n = running_shards()
    if n == 0:
        wave += 1
        p = pool_size()
        log = f"wave_{wave}.log"
        cmd = [sys.executable, "mass_seed.py", "--shards", "8",
               "--pairs-per-group", "1", "--replies-per-group", "1"]
        with open(log, "w", encoding="utf-8") as f:
            f.write(f"# wave {wave} started {time.strftime('%H:%M')} pool={p}\n")
        subprocess.Popen(cmd, stdout=open(log, "a", encoding="utf-8"),
                         stderr=subprocess.STDOUT)
        print(f"[chain] wave {wave} launched, pool={p}, log={log}", flush=True)
        time.sleep(600)  # give shards time to spin up before checking again
    else:
        time.sleep(300)
