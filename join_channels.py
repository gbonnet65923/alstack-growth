# -*- coding: utf-8 -*-
"""Mass-join AI channels with clean sessions (looks organic: feed subscriptions).
Each account joins K channels from ai_groups.json parent channels + top AI channels.
Usage: python join_channels.py [--accounts 8] [--per-acc 12]
"""
import asyncio, json, os, random, shutil, sys

from telethon import TelegramClient, errors
from telethon.tl.functions.channels import JoinChannelRequest

API_ID = 2040
API_HASH = "b18441a1ff607e10a989891a5462e627"
BASE = r"C:/Users/User/tmp/tg_chat_grow"
SRC = r"C:/Users/User/Desktop/CLEAN_ALIVE_SESSIONS"
WORK = os.path.join(BASE, "joiners")
os.makedirs(WORK, exist_ok=True)

# extra big AI channels beyond harvested parents
EXTRA = ["hiaimedia","GPTMainNews","gpt_news","gptpublic","neuraldvig","balahninaII","prompts_ai_channel","vistehno","pro_ai_novosti","dailyprompts","generalov_ai_agents","Shutter","ai_nox","vibecoding_tg","ChatGPTrue","svodkaai_ai","neyrosetkapic","pro100_python","LLMScience","ai_python","zrabota","slidy_ai","n2d2ai","mdjrny","Midjourney_A1","codex_resets","vshai_io","kuznicon","neirobarsik","AI_artz"]

def clean_accounts(n):
    clean = json.load(open(os.path.join(BASE, "spambot_classified.json"), encoding="utf-8"))["ok"]
    files = [f for f in os.listdir(SRC) if f.endswith(".session") and f[:-8] in clean]
    random.shuffle(files)
    out = []
    for f in files:
        if len(out) >= n: break
        stem = f[:-8]
        if any(x in stem for x in ("7448683285","809951394","8348347899")): continue
        dst = os.path.join(WORK, stem)
        if not os.path.exists(dst + ".session"):
            try: shutil.copy(os.path.join(SRC, f), dst + ".session")
            except Exception: continue
        out.append(dst)
    return out

def target_channels():
    chs = []
    gf = os.path.join(BASE, "ai_groups.json")
    if os.path.exists(gf):
        for g in json.load(open(gf, encoding="utf-8")):
            if g.get("channel"): chs.append(g["channel"])
    chs += EXTRA
    # dedupe preserve order
    seen=set(); out=[]
    for c in chs:
        if c not in seen: seen.add(c); out.append(c)
    return out

async def main():
    args = sys.argv[1:]
    nacc = int(args[args.index("--accounts")+1]) if "--accounts" in args else 8
    per = int(args[args.index("--per-acc")+1]) if "--per-acc" in args else 12
    accs = clean_accounts(nacc)
    chs = target_channels()
    print(f"accounts={len(accs)} channels={len(chs)} per_acc={per}")
    total_ok = 0
    for ap in accs:
        stem = os.path.basename(ap)
        try:
            c = TelegramClient(ap, API_ID, API_HASH, connection_retries=1)
            await c.connect()
            if not await c.is_user_authorized():
                await c.disconnect(); print(f"  {stem}: NOT AUTH"); continue
            me = await c.get_me()
            sample = random.sample(chs, min(per, len(chs)))
            ok = 0
            for ch in sample:
                try:
                    ent = await c.get_entity(ch)
                    await c(JoinChannelRequest(ent))
                    ok += 1
                except errors.FloodWaitError as e:
                    print(f"  {stem}: FLOOD {e.seconds}s on {ch} — stop"); break
                except Exception:
                    pass
                await asyncio.sleep(random.uniform(4, 12))
            total_ok += ok
            print(f"  {stem} (id={me.id}): joined {ok}/{len(sample)}")
            await c.disconnect()
            await asyncio.sleep(random.uniform(10, 30))
        except Exception as e:
            print(f"  {stem}: CRASH {str(e)[:70]}")
    print(f"TOTAL JOINS: {total_ok}")

asyncio.run(main())
