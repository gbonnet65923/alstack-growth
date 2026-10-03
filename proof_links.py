import asyncio, json, os, shutil
from telethon import TelegramClient

API_ID=2040; API_HASH="b18441a1ff607e10a989891a5462e627"
BASE=r"C:/Users/User/tmp/tg_chat_grow"
SRC=r"C:/Users/User/Desktop/CLEAN_ALIVE_SESSIONS"

async def main():
    stem="igfhngp_633874480"
    dst=os.path.join(BASE,"verify",stem)
    if not os.path.exists(dst+".session"): shutil.copy(os.path.join(SRC,stem+".session"),dst+".session")
    c=TelegramClient(dst,API_ID,API_HASH)
    await c.connect()
    targets=["vakansii_chatgpt","pythonstepikchat","python_chatt","chat_IY","RixAiHub","osenya_marketing","matvei_vibecoding","claudenews","technology_AI_program_IT","chatpythonua","Oloid_X_AI"]
    for un in targets:
        try:
            ent=await c.get_entity(un)
            hits=[]
            async for m in c.iter_messages(ent,limit=80):
                if m.text and ("alstack" in m.text.lower()):
                    nm=""
                    try:
                        u=await c.get_entity(m.sender_id); nm=u.first_name or "?"
                    except Exception: nm="?"
                    link=m.link or f"https://t.me/{un}/{m.id}"
                    hits.append(f"  {nm}: {m.text[:70]} | {link}")
            print(f"{un}: {len(hits)} hits")
            for h in hits: print(h)
        except Exception as e:
            print(f"{un}: ERR {str(e)[:50]}")
        await asyncio.sleep(1)
    await c.disconnect()
asyncio.run(main())
