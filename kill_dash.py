# -*- coding: utf-8 -*-
"""kill_dash.py — leave ONE newest dashboard bot instance, kill the rest."""
import psutil, sys, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
TARGET = "dash" + "board_bot.py"
SELF = "kill" + "_dash.py"
cands = []
for p in psutil.process_iter(["pid", "name", "cmdline", "create_time"]):
    try:
        cl = " ".join(p.info["cmdline"] or [])
        if TARGET in cl and SELF not in cl:
            par = p.parent()
            pname = par.name() if par else "?"
            parcl = " ".join(par.cmdline())[:80] if par else ""
            cands.append((p.info["create_time"], p.pid, p, pname, parcl))
    except Exception:
        pass
cands.sort()
print(f"found {len(cands)}")
for ts, pid, p, pname, parcl in cands:
    print(f"  pid {pid} started {time.strftime('%H:%M:%S', time.localtime(ts))} parent={pname} [{parcl}]")
if len(cands) > 1:
    for ts, pid, p, pname, parcl in cands[:-1]:
        try:
            p.kill()
            print("killed", pid)
        except Exception as e:
            print("err", pid, e)
    print("KEPT", cands[-1][1])
else:
    print("single instance OK", cands[0][1] if cands else None)
