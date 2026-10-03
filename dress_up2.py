# -*- coding: utf-8 -*-
"""Dress-up upgrade for clean sessions: real bio, username if missing, 512px avatar.
Uses persona pools (CIS names) + avatars_big/. State: dress2_progress.json
Usage: python dress_up2.py [N]
"""
import asyncio, json, os, random, shutil, sys

from telethon import TelegramClient
from telethon.tl.functions.account import UpdateProfileRequest, UpdateUsernameRequest
from telethon.tl.functions.photos import UploadProfilePhotoRequest

API_ID = 2040
API_HASH = "b18441a1ff607e10a989891a5462e627"
BASE = r"C:/Users/User/tmp/tg_chat_grow"
SRC = r"C:/Users/User/Desktop/CLEAN_ALIVE_SESSIONS"
WORK = os.path.join(BASE, "dressers")
AVATARS = r"C:/Users/User/tmp/tg_session_ops/avatars_big"
PROG = os.path.join(BASE, "dress2_progress.json")
os.makedirs(WORK, exist_ok=True)

FIRST_M = ["Артём","Данил","Кирилл","Максим","Роман","Никита","Егор","Тимур","Марат","Арсений","Денис","Влад","Илья","Степан","Глеб","Руслан","Дамир","Лев"]
LAST_M = ["Ковалёв","Соколов","Морозов","Волков","Зайцев","Лебедев","Егоров","Фомин","Беляев","Тарасов","Жуков","Орлов","Савин","Крылов"]
FIRST_F = ["Алина","Дарья","Ксения","Полина","Мария","Вика","Настя","Лена","Соня","Амина","Арина","Валерия","Кристина","Милана"]
LAST_F = ["Смирнова","Иванова","Кузнецова","Попова","Васильева","Новикова","Фёдорова","Михайлова","Павлова","Андреева"]

BIOS = [
    "ai / нейросети / вайбкодинг",
    "интересуюсь ии, промптами и автоматизацией",
    "делаю контент с помощью нейросетей",
    "gpt, claude, midjourney — тестирую всё",
    "frontend dev, немного ml",
    "студент, пишу на python",
    "дизайнер, генерирую в миджорнике",
    "маркетинг + ai tools",
    "собираю промты, делюсь находками",
    "работаем с ии каждый день",
    "crypto / ai / memecoins",
    "фрилансер, нейросети помогают жить",
    "smm, контент, генерация",
    "просто интересуюсь технологиями",
    "video editor, ai tools enjoyer",
    "учу ml, параллельно работаю",
    "тг-каналы про ии — моя лента",
    "автоматизирую рутину скриптами",
]

def load_prog():
    if os.path.exists(PROG): return json.load(open(PROG, encoding="utf-8"))
    return {"done": [], "fail": {}}

def save_prog(p): json.dump(p, open(PROG, "w", encoding="utf-8"), indent=1)

def persona_for(seed):
    rnd = random.Random(seed)
    female = rnd.random() < 0.45
    if female:
        first, last = rnd.choice(FIRST_F), rnd.choice(LAST_F)
    else:
        first, last = rnd.choice(FIRST_M), rnd.choice(LAST_M)
    bio = rnd.choice(BIOS)
    return first, last, bio, female

async def dress(path):
    c = TelegramClient(path, API_ID, API_HASH, connection_retries=1)
    await c.connect()
    if not await c.is_user_authorized():
        await c.disconnect(); return "NOT AUTH"
    me = await c.get_me()
    first, last, bio, female = persona_for(me.id)
    changed = []
    try:
        await asyncio.wait_for(c(UpdateProfileRequest(first_name=first, last_name=last, about=bio)), timeout=15)
        changed.append("name+bio")
    except Exception as e:
        changed.append(f"name ERR {str(e)[:40]}")
    if not me.username:
        base = "".join(ch for ch in (first+last) if ch.isalpha())
        for _ in range(4):
            cand = (base[:12].lower() + str(random.randint(100, 9999)))
            cand = "".join(ch for ch in cand if ch.isalnum())
            try:
                await c(UpdateUsernameRequest(username=cand)); changed.append(f"@{cand}"); break
            except Exception:
                continue
    if not me.photo:
        avs = [f for f in os.listdir(AVATARS) if f.endswith(".jpg")]
        if avs:
            av = os.path.join(AVATARS, random.Random(me.id).choice(avs))
            try:
                up = await c.upload_file(av)
                await c(UploadProfilePhotoRequest(file=up)); changed.append("photo")
            except Exception as e:
                changed.append(f"photo ERR {str(e)[:40]}")
    await c.disconnect()
    return first + " " + last + " | " + ", ".join(changed)

async def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    clean = json.load(open(os.path.join(BASE, "spambot_classified.json"), encoding="utf-8"))["ok"]
    prog = load_prog()
    todo = [s for s in clean if s not in prog["done"] and s not in prog["fail"]][:n]
    print("to dress:", len(todo))
    for stem in todo:
        src_f = os.path.join(SRC, stem + ".session")
        dst = os.path.join(WORK, stem)
        if not os.path.exists(dst + ".session"):
            try: shutil.copy(src_f, dst + ".session")
            except Exception: continue
        try:
            r = await dress(dst)
            print(f"  {stem}: {r}")
            if "NOT AUTH" in r: prog["fail"][stem] = r
            else: prog["done"].append(stem)
        except Exception as e:
            print(f"  {stem}: CRASH {str(e)[:60]}"); prog["fail"][stem] = str(e)[:60]
        save_prog(prog)
        await asyncio.sleep(random.uniform(5, 15))
    print(f"DRESSED total: {len(prog['done'])}, fail: {len(prog['fail'])}")

asyncio.run(main())
