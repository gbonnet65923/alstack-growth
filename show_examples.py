import asyncio, json, os, shutil
from telethon import TelegramClient
from telethon.tl.types import PeerChannel
from telethon.tl.functions.messages import GetDiscussionMessageRequest
from telethon.tl.functions.channels import JoinChannelRequest

API_ID = 2040; API_HASH = "b18441a1ff607e10a989891a5462e627"
BASE = r"C:/Users/User/tmp/tg_chat_grow"
SRC = r"C:/Users/User/Desktop/CLEAN_ALIVE_SESSIONS"

async def main():
    stem = "igfhngp_633874480"
    dst = os.path.join(BASE,"seeders",stem)
    if not os.path.exists(dst+".session"): shutil.copy(os.path.join(SRC,stem+".session"), dst+".session")
    c = TelegramClient(dst, API_ID, API_HASH)
    await c.connect()
    # profiles of the two seed accounts from the test pair
    for uid in [5566668127, 339921146]:
        try:
            u = await c.get_entity(uid)
            print(f"ACC {uid}: name={u.first_name!r} last={u.last_name!r} @{u.username} photo={'YES' if u.photo else 'NO'} bio_len={len(u.about or '')}")
        except Exception as e:
            print(f"ACC {uid}: err {str(e)[:60]}")
    # show dialogs in groups already seeded today (from state)
    st = json.load(open(os.path.join(BASE,"seed_state.json"),encoding="utf-8"))
    groups = {g["channel"]: g for g in json.load(open(os.path.join(BASE,"ai_groups.json"),encoding="utf-8"))}
    shown = 0
    for done in st.get("done", [])[-3:]:
        gname = done["group"]; g = groups.get(gname)
        if not g: continue
        try:
            chan = await c.get_entity(gname)
            async for m in c.iter_messages(chan, limit=25):
                if m.replies is not None and getattr(m.replies,"grouped_id",None):
                    await c(GetDiscussionMessageRequest(channel=chan, msg_id=m.id)); break
            ent = await c.get_input_entity(PeerChannel(channel_id=g["linked_id"]))
            msgs = await c.get_messages(ent, limit=6)
            print(f"\n=== {g['title']} ({g['members']} members) ===")
            for m in msgs:
                if m.text and 'alstack' in m.text.lower() or (m.text and len(m.text) > 10):
                    who = ""
                    if m.sender_id:
                        try:
                            su = await c.get_entity(m.sender_id); who = su.first_name or ""
                        except Exception: who = str(m.sender_id)
                    print(f"  {who}: {m.text[:100]}")
            shown += 1
        except Exception as e:
            print(f"  {gname}: err {str(e)[:60]}")
    await c.disconnect()
asyncio.run(main())
