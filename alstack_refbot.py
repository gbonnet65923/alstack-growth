# alstack_refbot.py — реферальный бот @AlStack (deep-link start=REF)
# База: svtcore/telegram-referral-bot (MIT) + raf (Apache) паттерны.
#   /start REF_CODE -> фиксирует реферера, выдаёт личную ссылку
#   проверка подписки реферера на @AlStack (бот должен быть админом канала)
#   Тиры: 3 = Прокси-пак, 10 = Консультация, 25 = Софт из репо; /top лидерборд
#   Антифрод: 1 акк = 1 реф
# Setup: создать рядом refbot_token.txt с токеном BotFather; бот — админ @AlStack
# Run: env -u PYTHONPATH python alstack_refbot.py
import asyncio, hashlib, os, sqlite3, time
from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart, Command
from aiogram.types import Message

HERE = os.path.dirname(os.path.abspath(__file__))
TOKFILE = os.path.join(HERE, "refbot_token.txt")
if not os.path.exists(TOKFILE):
    raise SystemExit("create refbot_token.txt with BotFather token next to this script")
TOKEN = open(TOKFILE, encoding="utf-8").read().strip()
CHANNEL = "AlStack"
CHANNEL_ID = -1004420835850
DB = os.path.join(HERE, "refbot.db")
TIERS = [(3, "Прокси-пак"), (10, "Консультация"), (25, "Софт из репо")]

def db_init():
    con = sqlite3.connect(DB)
    con.execute("CREATE TABLE IF NOT EXISTS refs(referrer INTEGER, referee INTEGER PRIMARY KEY, ts REAL)")
    con.execute("CREATE TABLE IF NOT EXISTS codes(user_id INTEGER PRIMARY KEY, code TEXT UNIQUE)")
    con.commit(); return con

def get_code(con, uid):
    row = con.execute("SELECT code FROM codes WHERE user_id=?", (uid,)).fetchone()
    if row: return row[0]
    code = hashlib.sha256((str(uid) + str(time.time())).encode()).hexdigest()[:8]
    con.execute("INSERT INTO codes(user_id,code) VALUES(?,?)", (uid, code)); con.commit()
    return code

def add_ref(con, referrer, referee):
    if con.execute("SELECT 1 FROM refs WHERE referee=?", (referee,)).fetchone(): return None
    if referrer == referee: return None
    con.execute("INSERT INTO refs(referrer,referee,ts) VALUES(?,?,?)", (referrer, referee, time.time()))
    con.commit()
    return con.execute("SELECT COUNT(*) FROM refs WHERE referrer=?", (referrer,)).fetchone()[0]

def tier_for(n):
    return [name for th, name in TIERS if n >= th]

async def is_sub(bot, uid):
    try:
        m = await bot.get_chat_member(CHANNEL_ID, uid)
        return m.status in ("member", "administrator", "creator")
    except Exception:
        return None

async def main():
    bot = Bot(token=TOKEN)
    dp = Dispatcher()
    con = db_init()

    @dp.message(CommandStart())
    async def start(m: Message, command):
        uid = m.from_user.id
        args = (command.args or "").strip()
        code = get_code(con, uid)
        me = await bot.get_me()
        link = "https://t.me/" + me.username + "?start=" + code
        added = None
        referrer_row = None
        if args and len(args) == 8:
            referrer_row = con.execute("SELECT user_id FROM codes WHERE code=?", (args,)).fetchone()
            if referrer_row and await is_sub(bot, referrer_row[0]):
                added = add_ref(con, referrer_row[0], uid)
        n = con.execute("SELECT COUNT(*) FROM refs WHERE referrer=?", (uid,)).fetchone()[0]
        tiers = tier_for(n)
        txt = ("🔁 Рефералка @AlStack\n\nТвоя ссылка:\n" + link + "\n\nРефералов: " + str(n) + "\n")
        if tiers: txt += "Открыто: " + ", ".join(tiers) + "\n"
        txt += "\nТиры: 3 = Прокси-пак, 10 = Консультация, 25 = Софт из репо\n/top — лидерборд"
        if added is not None and referrer_row:
            try:
                await bot.send_message(referrer_row[0], "➕ Новый реферал по твоей ссылке! Всего: " + str(added))
            except Exception:
                pass
        await m.answer(txt)

    @dp.message(Command("top"))
    async def top(m: Message):
        rows = con.execute("SELECT r.referrer, COUNT(*) c FROM refs r GROUP BY r.referrer ORDER BY c DESC LIMIT 10").fetchall()
        if not rows: return await m.answer("Лидерборд пуст")
        lines = []
        for i, (uid, c) in enumerate(rows):
            uname = None
            try:
                ch = await bot.get_chat(uid)
                uname = ch.username or ch.first_name
            except Exception:
                pass
            lines.append(str(i+1) + ". " + (uname or ("id"+str(uid))) + " — " + str(c))
        await m.answer("🏆 Топ-10 рефереров\n" + "\n".join(lines))

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
