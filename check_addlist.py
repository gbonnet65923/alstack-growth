# -*- coding: utf-8 -*-
"""Resolve t.me/addlist/<slug> chatlist invite -> channels inside.
Output: addlist_resolved.json [{title, username, id, members, linked_id}]
Usage: python check_addlist.py <slug>
"""
import asyncio, json, os, shutil, sys

from telethon import TelegramClient
from telethon.tl.functions.chatlists import CheckChatlistInviteRequest
from telethon.tl.functions.channels import GetFullChannelRequest
from telethon.tl.types import Channel

API_ID = 2040
API_HASH = "b18441a1ff607e10a989891a5462e627"
BASE = r"C:/Users/User/tmp/tg_chat_grow"
SRC = r"C:/Users/User/Desktop/CLEAN_ALIVE_SESSIONS"
WORK = os.path.join(BASE, "addlist")
os.makedirs(WORK, exist_ok=True)
PROTECTED = ("7448683285", "809951394")

async def main():
    slug = sys.argv[1] if len(sys.argv) > 1 else "1R6yXdAEgokxZTcy"
    # pick first clean account copy
    clean = set(json.load(open(os.path.join(BASE, "spambot_classified.json"), encoding="utf-8"))["ok"])
    stem = None
    for f in sorted(os.listdir(SRC)):
        if not f.endswith(".session"): continue
        s = f[:-8]
        if s not in clean: continue
        if any(x in s for x in PROTECTED): continue
        stem = s; break
    if not stem:
        print("NO ACCOUNT"); return
    dst = os.path.join(WORK, stem)
    if not os.path.exists(dst + ".session"):
        shutil.copy(os.path.join(SRC, stem + ".session"), dst + ".session")
    print("account:", stem, "slug:", slug)

    async with TelegramClient(dst, API_ID, API_HASH, connection_retries=2) as c:
        res = await c(CheckChatlistInviteRequest(slug=slug))
        print("type:", type(res).__name__)
        title = getattr(res, "title", "")
        if not isinstance(title, str):
            title = getattr(title, "text", str(title))
        peers = getattr(res, "peers", []) or []
        print("list title:", title, "| peers:", len(peers))
        out = []
        for p in peers:
            ch = p if isinstance(p, Channel) else getattr(p, "channel", None)
            if ch is None:
                # peer object -> resolve
                try:
                    ent = await c.get_entity(p)
                    ch = ent
                except Exception as e:
                    out.append({"err": str(e)[:60], "raw": str(p)[:80]})
                    continue
            rec = {"title": getattr(ch, "title", ""),
                   "username": getattr(ch, "username", None),
                   "id": ch.id,
                   "megagroup": bool(getattr(ch, "megagroup", False)),
                   "linked_id": None, "members": None}
            if not isinstance(rec["title"], str):
                rec["title"] = getattr(rec["title"], "text", str(rec["title"]))
            try:
                full = await c(GetFullChannelRequest(channel=p))
                fc = full.full_chat
                rec["members"] = fc.participants_count
                rec["linked_id"] = getattr(fc, "linked_chat_id", None)
            except Exception as e:
                rec["err"] = str(e)[:60]
            out.append(rec)
            print(f"@{rec['username']} | {rec['title']!r} | members={rec['members']} linked={rec['linked_id']}")
        json.dump({"slug": slug, "title": title, "channels": out},
                  open(os.path.join(BASE, "addlist_resolved.json"), "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
        print("SAVED addlist_resolved.json:", len(out))

asyncio.run(main())
