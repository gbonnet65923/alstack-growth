# -*- coding: utf-8 -*-
"""
Context-aware responder for AI discussion groups.
Reads recent messages, replies in-topic as a human (LLM: aurora gateway),
mentions @AlStack only when context fits (~organic).
State: responder_state.json (seen msg ids per group, daily quotas).
Usage: python responder.py [--groups 5] [--replies-per-group 2] [--dry]
"""
import asyncio, json, os, random, re, sys, time, datetime

import httpx
from telethon import TelegramClient, errors
from telethon.tl.functions.channels import JoinChannelRequest, GetFullChannelRequest
from telethon.tl.functions.messages import GetDiscussionMessageRequest
from telethon.tl.types import PeerChannel

API_ID = 2040
API_HASH = "b18441a1ff607e10a989891a5462e627"
BASE = r"C:/Users/User/tmp/tg_chat_grow"
SRC = r"C:/Users/User/Desktop/CLEAN_ALIVE_SESSIONS"
WORK = os.path.join(BASE, "responders")
STATE = os.path.join(BASE, "responder_state.json")
os.makedirs(WORK, exist_ok=True)

LLM = "http://127.0.0.1:16432/v1/chat/completions"
def _load_key():
    import re, yaml
    # dashscope via hermes custom provider (local proxy :16432) — MiniMax-M2.1
    try:
        cfg = yaml.safe_load(open(r"C:/Users/User/AppData/Local/hermes/config.yaml", encoding="utf-8"))
        for p in cfg.get("custom_providers") or []:
            if p.get("name") == "dashscope" and p.get("api_key"):
                return str(p["api_key"]).strip("\"'")
    except Exception:
        pass
    for p in [r"C:/Users/User/aurora-gateway/.env", r"C:/Users/User/aurora-gateway/config.env"]:
        if os.path.exists(p):
            m = re.search(r"(?:MASTER_KEY|API_KEY|AURORA_KEY|KEY)\s*=\s*(\S+)", open(p, encoding="utf-8", errors="ignore").read())
            if m: return m.group(1).strip("\"'")
    return os.environ.get("AURORA_KEY", "")

AUTH = _load_key()
MODEL = "MiniMax-M2.1"

SYS = """Ты обычный человек в телеграм-чате про нейросети/AI. Отвечаешь на сообщение по теме.
ПРАВИЛА СТИЛЯ (жёстко):
- коротко: 3-12 слов, изредка до 25. НИКАКИХ списков, эмодзи максимум 1, без точек в конце часто
- с маленькой буквы, разговорный русский, допустимы сокращения (щас, норм, хз, мб, спс, го)
- по делу: ответ на вопрос / реакция / свой опыт ("у меня так было", "пробовал, норм")
- БЕЗ канцелярита, БЕЗ «как ИИ», БЕЗ вежливых вступлений
- @AlStack упоминай ТОЛЬКО если тема про: бесплатные ключи/api, абузы, халяву, прокси, раздачи — и то максимум в 1 случае из 5, естественно ("там в @AlStack раздачу видел")
- если вопрос не про AI/технологии или непонятен — верни ровно: SKIP
Контекст чата: последние сообщения перед целевым. Ответ ТОЛЬКО текстом ответа, ничего больше."""

def load_state():
    if os.path.exists(STATE): return json.load(open(STATE, encoding="utf-8"))
    return {"seen": {}, "daily": {}, "history": []}

def save_state(st): json.dump(st, open(STATE, "w", encoding="utf-8"), ensure_ascii=False)

def today(): return datetime.date.today().isoformat()

def gen_reply(context_msgs, target_text):
    convo = "\n".join(f"{n}: {t}" for n, t in context_msgs[-6:])
    prompt = f"Контекст:\n{convo}\n\nОтветь на это сообщение: «{target_text}»"
    for a in range(2):
        try:
            r = httpx.post(LLM, headers={"Authorization": f"Bearer {AUTH}"}, json={
                "model": MODEL,
                "messages": [{"role": "system", "content": SYS}, {"role": "user", "content": prompt}],
                "temperature": 0.95, "max_tokens": 70}, timeout=90)
            r.raise_for_status()
            out = r.json()["choices"][0]["message"]["content"].strip().strip('"').strip()
            out = out.split("\n")[0][:220]
            if not out or out == "SKIP": return None
            return out
        except Exception as e:
            print(f"    LLM ERR {str(e)[:60]}"); time.sleep(3)
    return None

def humanize(t):
    # drop model artifacts
    t = t.strip()
    if t.lower().startswith(("ответ:", "reply:")): t = t.split(":", 1)[1].strip()
    t = re.sub(r"[*_#`]", "", t)
    return t

def pick_accounts(n, banned=()):
    clean = set(json.load(open(os.path.join(BASE, "spambot_classified.json"), encoding="utf-8"))["ok"]) - set(banned)
    files = [f for f in os.listdir(SRC) if f.endswith(".session") and f[:-8] in clean]
    random.shuffle(files)
    import shutil
    out = []
    for f in files:
        if len(out) >= n: break
        stem = f[:-8]
        dst = os.path.join(WORK, stem)
        if not os.path.exists(dst + ".session"):
            try: shutil.copy(os.path.join(SRC, f), dst + ".session")
            except Exception: continue
        out.append(dst)
    return out

async def resolve_group(client, g):
    ent = None
    try:
        if g.get("direct"):
            ent = await client.get_entity(g["channel"])
            try: await client(JoinChannelRequest(ent))
            except Exception: pass
            await asyncio.sleep(random.uniform(2, 5))
            return await client.get_input_entity(ent)
        chan = await client.get_entity(g["channel"])
        try: await client(JoinChannelRequest(chan))
        except Exception: pass
        async for m in client.iter_messages(chan, limit=25):
            if m.replies is not None and getattr(m.replies, "grouped_id", None):
                try:
                    await client(GetDiscussionMessageRequest(channel=chan, msg_id=m.id)); break
                except Exception: continue
        ent = await client.get_input_entity(PeerChannel(channel_id=g["linked_id"]))
        try: await client(JoinChannelRequest(ent))  # join discussion group itself
        except Exception: pass
        await asyncio.sleep(random.uniform(2, 5))
    except Exception:
        pass
    return ent

async def process_group(acc_path, g, st, max_replies, dry):
    stem = os.path.basename(acc_path)
    client = TelegramClient(acc_path, API_ID, API_HASH, connection_retries=2)
    await client.connect()
    if not await client.is_user_authorized():
        await client.disconnect(); return 0
    me = await client.get_me()
    ent = await resolve_group(client, g)
    if ent is None:
        await client.disconnect(); return 0
    msgs = await client.get_messages(ent, limit=25)
    if not msgs:
        await client.disconnect(); return 0
    msgs = list(reversed(msgs))  # oldest first
    seen = set(st["seen"].get(g["channel"], [])[-300:])
    td = today()
    dk = f"{td}:{stem}"
    acc_room = 8 - st["daily"].get(dk, 0)
    if acc_room <= 0:
        await client.disconnect(); return 0
    # candidates: human messages that look like questions/discussion, not from us
    candidates = []
    for i, m in enumerate(msgs):
        if not m.text or m.sender_id is None or m.sender_id == me.id: continue
        if m.id in seen: continue
        t = m.text.strip()
        if len(t) < 12 or len(t) > 400: continue
        if t.startswith(("/", "!")) or "http" in t: continue
        if m.sender_id and m.sender_id < 0: continue
        candidates.append((i, m))
    candidates = candidates[-8:]
    random.shuffle(candidates)
    sent = 0
    for i, m in candidates:
        if sent >= max_replies or sent >= acc_room: break
        context = []
        for j in range(max(0, i - 5), i + 1):
            mm = msgs[j]
            if mm.sender_id and mm.text:
                context.append((str(mm.sender_id)[-4:], mm.text[:120]))
        reply = gen_reply(context, m.text[:250])
        if not reply: continue
        reply = humanize(reply)
        if not reply or len(reply) < 3: continue
        if dry:
            print(f"    [dry] {g['channel']}: reply -> {reply[:90]}")
        else:
            try:
                await client.send_message(ent, reply, reply_to=m.id)
                print(f"    {g['channel']} ({me.first_name}): {reply[:80]}")
            except errors.FloodWaitError as e:
                print(f"    FLOOD {e.seconds}s — stop acc"); break
            except errors.UserBannedInChannelError:
                print(f"    BANNED — retire acc"); st.setdefault("banned_accs", []).append(stem); break
            except Exception as e:
                print(f"    send err {str(e)[:70]}"); break
            st["daily"][dk] = st["daily"].get(dk, 0) + 1
            sent += 1
            await asyncio.sleep(random.uniform(25, 90))
        seen.add(m.id)
        st["seen"][g["channel"]] = list(seen)[-300:]
        if not dry:
            st["history"].append({"ts": time.time(), "g": g["channel"], "acc": me.id, "r": reply[:100]})
            st["history"] = st["history"][-500:]
            save_state(st)
    save_state(st)
    await client.disconnect()
    return sent

async def main():
    args = sys.argv[1:]
    ng = int(args[args.index("--groups") + 1]) if "--groups" in args else 5
    mr = int(args[args.index("--replies-per-group") + 1]) if "--replies-per-group" in args else 2
    dry = "--dry" in args
    lf = os.path.join(BASE, "ai_groups_live.json")
    groups = json.load(open(lf if os.path.exists(lf) else os.path.join(BASE, "ai_groups.json"), encoding="utf-8"))
    df = os.path.join(BASE, "live_groups_found.json")
    if os.path.exists(df):
        groups = groups + json.load(open(df, encoding="utf-8"))
    groups = [g for g in groups if (g.get("direct") or g.get("linked_id")) and (g.get("members") or 0) >= 20]
    groups.sort(key=lambda g: (g.get("direct", False), g.get("recent_human") or 0, g.get("members") or 0), reverse=True)
    groups = groups[:ng]
    st = load_state()
    accs = pick_accounts(8, st.get("banned_accs", []))
    print(f"responder run: groups={len(groups)} accs={len(accs)} dry={dry}")
    total = 0
    for idx, g in enumerate(groups):
        acc = accs[idx % len(accs)]
        print(f"  {g['channel']} <- {os.path.basename(acc)}")
        try:
            n = await process_group(acc, g, st, mr, dry)
            total += n
        except Exception as e:
            print(f"    CRASH {str(e)[:80]}")
        await asyncio.sleep(random.uniform(30, 90))
    print(f"RESPONDER TOTAL: {total} replies")

if __name__ == "__main__":
    asyncio.run(main())
