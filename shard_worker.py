# -*- coding: utf-8 -*-
"""
Shard worker: plays seed pairs + contextual replies for its slice of groups.
Reuses logic from seed_alstack.py and responder.py modules.
Usage (called by mass_seed.py):
python shard_worker.py --shard 0 --groups '[...]' --pairs-per-group 2 --replies-per-group 2 --accounts '[...]'
"""
import argparse, asyncio, json, os, random, sys, time, datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import seed_alstack as SA
import responder as RS

BASE = r"C:/Users/User/tmp/tg_chat_grow"
WORK = os.path.join(BASE, "mass")

SHILL_F = os.path.join(BASE, "shill_done.json")

def shill_registry():
    if os.path.exists(SHILL_F):
        return set(json.load(open(SHILL_F, encoding="utf-8")))
    return set()

def mark_shilled(gk):
    reg = shill_registry()
    reg.add(gk)
    tmp = SHILL_F + ".tmp"
    json.dump(sorted(reg), open(tmp, "w", encoding="utf-8"))
    os.replace(tmp, SHILL_F)

def load_state(shard):
    p = os.path.join(BASE, f"mass_state_{shard}.json")
    if os.path.exists(p):
        return json.load(open(p, encoding="utf-8"))
    return {"pairs": 0, "replies": 0, "done_groups": [], "fails": {}, "used_dialogs": [], "seen": {}, "daily": {}, "history": [], "log": []}

def save_state(shard, st):
    p = os.path.join(BASE, f"mass_state_{shard}.json")
    tmp = p + ".tmp"
    for attempt in range(5):
        try:
            json.dump(st, open(tmp, "w", encoding="utf-8"), ensure_ascii=False)
            os.replace(tmp, p)
            return
        except OSError as e:
            time.sleep(1.5 * (attempt + 1))
    # last resort: direct write, no tmp
    json.dump(st, open(p, "w", encoding="utf-8"), ensure_ascii=False)

def all_groups():
    groups = []
    for fn in ["pool_merged.json"]:
        p = os.path.join(BASE, fn)
        if os.path.exists(p):
            groups += json.load(open(p, encoding="utf-8"))
    by_key = {}
    for g in groups:
        by_key[g.get("channel")] = g
    return by_key

async def run_shard(shard, group_names, acc_stems, ppg, rpg):
    st = load_state(shard)
    by_key = all_groups()
    groups = [by_key[n] for n in group_names if n in by_key]
    accs = [os.path.join(WORK, s) for s in acc_stems]
    accs = [a for a in accs if os.path.exists(a + ".session")]
    if len(accs) < 2:
        print(f"shard {shard}: no accounts"); return
    today = datetime.date.today().isoformat()
    print(f"shard {shard}: {len(groups)} groups, {len(accs)} accounts", flush=True)

    # per-day dedupe of dialogs (global via seed_state used_dialogs + local)
    used = set(st.get("used_dialogs", []))

    for gi, g in enumerate(groups):
        gk = g["channel"]
        # ---- seed pair: ONE shill per group, ever ----
        if gk in shill_registry():
            print(f"  [pair] {gk}: already shilled, skip", flush=True)
            ppg = 0
        pairs_done = sum(1 for d in st.get("log", []) if d.get("g") == gk and d.get("kind") == "pair" and d.get("ok"))
        while pairs_done < min(ppg, 1):
            avail = [d for d in SA.DIALOGS if d[0] not in used]
            if not avail:
                avail = SA.DIALOGS
                used.clear()
            dialog = random.choice(avail)
            used.add(dialog[0])
            ap, rp = random.sample(accs, 2)
            ok, bad, why = await SA.play_dialog(ap, rp, g, dialog)
            if not ok and why == "banned" and bad:
                if bad in accs:
                    accs.remove(bad)
                    st["banned_accs"] = st.get("banned_accs", []) + [os.path.basename(bad)]
                    print(f"  retire banned acc: {os.path.basename(bad)}", flush=True)
                if len(accs) < 2:
                    print(f"shard {shard}: accounts exhausted"); break
            st["log"].append({"g": gk, "kind": "pair", "day": today, "ok": bool(ok), "why": why, "ts": time.time()})
            st["log"] = st["log"][-2000:]
            if ok:
                st["pairs"] += 1
                mark_shilled(gk)
                print(f"  [pair] {gk} OK (total {st['pairs']}) — group closed", flush=True)
            else:
                print(f"  [pair] {gk} fail: {why}", flush=True)
                if why in ("cant_write", "banned"):
                    st["fails"].setdefault(gk, 0)
                    st["fails"][gk] += 1
                    if st["fails"][gk] >= 3:
                        print(f"  {gk}: write-blocked, skipping group", flush=True)
                        break
            pairs_done += 1
            save_state(shard, st)
            await asyncio.sleep(random.uniform(30, 90))
        if st["fails"].get(gk, 0) >= 3:
            continue

        # ---- contextual replies ----
        try:
            n = await RS.process_group(random.choice(accs), g, st, rpg, False)
            st["replies"] += n or 0
            if n: print(f"  [resp] {gk}: +{n} (total {st['replies']})", flush=True)
        except Exception as e:
            print(f"  [resp] {gk}: ERR {str(e)[:60]}", flush=True)
        st.setdefault("used_dialogs", [])
        st["used_dialogs"] = list(used)[-500:]
        save_state(shard, st)
        await asyncio.sleep(random.uniform(30, 90))
    save_state(shard, st)
    print(f"shard {shard} DONE: pairs={st['pairs']} replies={st['replies']}", flush=True)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--shard", type=int, required=True)
    ap.add_argument("--groups", required=True)
    ap.add_argument("--accounts", required=True)
    ap.add_argument("--pairs-per-group", type=int, default=2)
    ap.add_argument("--replies-per-group", type=int, default=2)
    a = ap.parse_args()
    asyncio.run(run_shard(a.shard, json.loads(a.groups), json.loads(a.accounts), a.pairs_per_group, a.replies_per_group))

if __name__ == "__main__":
    main()
