# -*- coding: utf-8 -*-
"""react_latest.py — найти последние посты @AlStack с малым числом реакций и накрутить.
Usage: python react_latest.py [--n 40] [--posts 6] [--min 30]
"""
import asyncio, json, os, random, shutil, subprocess, sys, glob
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

API_ID = 2040
API_HASH = "b18441a1ff607e10a989891a5462e627"
BASE = r"C:/Users/User/tmp/tg_chat_grow"
os.chdir(BASE)

async def main():
    from telethon import TelegramClient
    # probe session: any free reactors copy
    src = None
    for f in sorted(glob.glob("reactors/*.session")):
        b = f[:-len(".session")]
        if not os.path.exists(b + "-journal") and not os.path.exists(b + "-wal"):
            src = f; break
    if src is None:
        src = sorted(glob.glob("reactors/*.session"))[0]
    probe = "reactors/_probe_latest.session"
    shutil.copyfile(src, probe)
    c = TelegramClient(probe[:-len(".session")], API_ID, API_HASH)
    await c.start()
    ids = []
    async for m in c.iter_messages("AlStack", limit=12):
        rc = len(m.reactions.results) if m.reactions else 0
        total = sum(r.count for r in m.reactions.results) if m.reactions else 0
        ids.append((m.id, total, rc))
        print(f"msg {m.id}: total={total} kinds={rc}")
    await c.disconnect()
    try: os.remove(probe); os.remove(probe + "-journal")
    except OSError: pass

    min_total = 30
    if "--min" in sys.argv: min_total = int(sys.argv[sys.argv.index("--min") + 1])
    weak = [i for i, t, _ in ids if t < min_total]
    print("weak posts:", weak)
    if not weak:
        print("all posts have enough reactions, nothing to do")
        return
    cmd = [sys.executable, "react_new.py", *[str(i) for i in weak]]
    if "--n" in sys.argv: cmd += ["--n", sys.argv[sys.argv.index("--n") + 1]]
    env = dict(os.environ); env.pop("PYTHONPATH", None)
    r = subprocess.run(cmd, env=env, capture_output=True, text=True, encoding="utf-8", errors="replace")
    print(r.stdout[-2000:])
    if r.stderr: print("STDERR:", r.stderr[-500:])

asyncio.run(main())
