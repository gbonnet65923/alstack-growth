# -*- coding: utf-8 -*-
"""kill_camp.py — остановить масс-шилл + респондер (не трогает дашборд-бота)."""
import psutil, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
TARGETS = ["mass_seed.py", "shard_worker.py", "responder.py", "wave_chain.py",
           "merge_pool.py", "seed_alstack.py"]
SELF = ["kill_camp", "dashboard_bot", "dashboard"]
killed = []
for p in psutil.process_iter(["pid", "name", "cmdline"]):
    try:
        if "python" not in (p.info["name"] or "").lower():
            continue
        cl = " ".join(p.info["cmdline"] or [])
        if any(s in cl for s in SELF):
            continue
        if any(t in cl for t in TARGETS):
            p.kill()
            killed.append((p.pid, cl[:70]))
    except Exception:
        pass
print(f"killed {len(killed)}:")
for pid, cl in killed:
    print(f"  {pid}: {cl}")
if not killed:
    print("  (ничего не работало)")
