# Софты для продвижения TG-канала — GitHub-скан 2026-10-03

Скан: 20 запросов → 336 репо → 295 релевантных → 14 скачано в combine-archive/opensource/, malware-скан CLEAN (0 danger hits).
Данные: tmp/gh_promo_repos.json (336), tmp/gh_promo_relevant.json (295).

## СКАЧАНО (локально, готово к адаптации)

### Реферальные боты (главный недостающий модуль)
| Репо | Звёзды | Лицензия | Что даёт |
|---|---|---|---|
| svtcore/telegram-referral-bot | 190* | MIT | Инвайт аккаунтов как рефералов по коду — пул-механика |
| galeone/raf | 30* | Apache-2.0 | Rust, реф-конкурсы для каналов (лидерборды, тиры) |
| itsAPK/Telegram-Referral-Bot | 43* | — | Генерация реф-ссылок + трекинг (не качал, слабее MIT-пары) |
| kevin-kidd/telegram-referral-bot | 26* | MIT | Трекинг инвайтов в канал/группу |
| AaronPemberton/Telegram-Referral-Bot | 28* | MIT | C#, очковая система рефов |

### Буст views/reactions (дополнение к нашему react_alstack)
| Репо | Звёзды | Лицензия | Что даёт |
|---|---|---|---|
| MarkSnaile/telegram-channel-views-boost | 93* | GPL-3.0 | Накрутка просмотров постов |
| djxda/telegram-views-increaser | 90* | MIT | То же, простой |
| Malith-Rukshan/Auto-Reaction-Bot | 120* | MIT | Авто-реакции в каналах/группах (JS) |
| kanewi11/telegram-reaction-bot | 43* | GPL | Реакции с tdata-поддержкой |
| TechifyBots/Auto-Reaction-Bot | 28* | MIT | Форк Malith, живой (push 03.10) |

### AI growth agent (самое свежее)
| Репо | Звёзды | Лицензия | Что даёт |
|---|---|---|---|
| SoCloseSociety/MiloAgent | 41* | MIT | Автономный AI growth-агент для Reddit/X/Telegram, self-learning, push 2026-06 |

### SMM-панель
| Репо | Звёзды | Лицензия | Что даёт |
|---|---|---|---|
| TegroTON/SMMPanel-SMOService-Telegram-Bot | 36* | — | Бот-SMM панель: подписчики/views/лайки, push СЕГОДНЯ (03.10) |

### Парсеры/аналитика
| Репо | Звёзды | Лицензия | Что даёт |
|---|---|---|---|
| artmih24/TeleParser | 153* | — | Парсер чатов/каналов с лемматизатором → JSON/CSV |
| Steelio/Telegram-Post-Scraper | 107* | BSD-2 | Скрейп постов через HTTP без Telethon |
| PeterWalchhofer/Telescrape | 48* | MIT | Сообщения+комменты comment.bot |
| alevikpes/telegram-parser | 77* | GPL | Парсер каналов и юзеров (не качал, дубль функционала) |

### Реклама/кросс-промо
| Репо | Звёзды | Лицензия | Что даёт |
|---|---|---|---|
| amiralirj/DarkAdvertizer | 55* | MIT | Бот рекламы с контролем аккаунтов |
| tgMember/tdAds | 54* | GPL | Bulk sender + auto joiner (Lua, старый) |
| viperadnan-git/force-subscribe-telegram-bot | 214* | GPL | Force-sub: подписка на канал до доступа в чат |

### Комментарии/постинг
| Репо | Звёзды | Лицензия | Что даёт |
|---|---|---|---|
| JogleLew/channel-helper-bot | 125* | GPL | Бот комментариев для каналов |
| SastaDev/Auto-Channel-Comment-Telegram-User-Bot | 25* | Apache-2.0 | Авто-комменты на новые посты |
| ShadowSlayer03/Post4U | 124* | MIT | Self-hosted планировщик X/TG (не качал) |

## НЕ СКАЧАНО, но в каталоге (295 репо в gh_promo_relevant.json)
- GitHub topics: telegram-members-adder-2025, telegramadder (масс-инвайтеры)
- ultrabot690-oswald/telegram-bot-growth-promotion-framework (growth-фреймворк)
- Reddit кейс: open-source bot для hashtag-видимости каналов

## ПЛАН СОФТОВ (адаптация под нашу инфру)
1. **ref_alstack.py** — реф-бот на базе svtcore MIT + raf Rust-паттерны: deep-link start-параметр, лидерборд, тиры (3 рефа = пак, 10 = консультация). Телепорт: наш @ai_boost_hub_bot уже умеет getChatMember-проверки.
2. **views_boost** — MarkSnaile GPL views-boost подключить к нашим 261 clean-сессиям (CLEAN_ALIVE_SESSIONS), вместо мёртвого smmway.
3. **MiloAgent-интеграция** — MIT AI-агент: Reddit/X мониторинг упоминаний AI-тем → авто-ответы с @AlStack где уместно.
4. **SMMPanel** — TegroTON панель как UI для заказов (views/likes), живой код от сегодня.
5. **DarkAdvertizer** — контроль рекламных аккаунтов для биржевых размещений (tagio/teletarget).
