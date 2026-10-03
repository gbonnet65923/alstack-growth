# -*- coding: utf-8 -*-
"""pool_filter.py — shared AI-topic filter (two-tier drop rules)."""
import re

STRONG_AI_RE = re.compile(
    r"(?<![a-zа-яё])ai|ai(?![a-zа-яё])|нейр|neuro|(?<![a-zа-яё])gpt|chatgpt|claude|"
    r"gemini|grok|deepseek|gigachat|midjour|suno|prompt|(?<![a-zа-яё])llm(?![a-zа-яё])|"
    r"machine learning|chatbot|искусствен|openai|anthropic|diffusion|"
    r"(?<![a-zа-яё])ии(?![а-яё])|генератив|langchain|ollama|hugging|comfy|шедеврум|"
    r"kandinsky|yandexgpt|codex|vibecod|вайбкод|copilot|нейросет|qwen|mistral|perplexity",
    re.IGNORECASE)

WEAK_AI_RE = re.compile(r"техно|tech|digital|инструмент|автоматиз|no ?code|nocode", re.IGNORECASE)

# always block — never our audience
HARD_DROP_RE = re.compile(
    r"rabota|rabot|работа|ваканс|vakans|freelance|фриланс|podryad|подряд|"
    r"обмен|exchang|(?<![a-z])p2p(?![a-z])|крипт|crypto|bitcoin|(?<![a-z])btc(?![a-z])|"
    r"usdt|валют|дроп|(?<![a-z])drop(?![a-z])|biznes|продаж|(?<![a-z])sales(?![a-z])|"
    r"товар|склад|знаком|девуш|бухгалтер|юрист|недвиж|ремонт|строй|медицин|врач|"
    r"school|школ|егэ|огэ|репетитор|english|англий|(?<![a-z])tour(?![a-z])|travel|airbnb|"
    r"billieeilish|музык|music|кино|movie|(?<![a-z])game(?![a-z])|"
    r"взаимн|подписк|пиар|реферал|накрут|tyumen|klient|клиент|turkey|турци|"
    r"donetsk|донбасс|арбитраж|ставк|беттин|fonbet|казино|casino|tort|торт|"
    r"mamamojet|мама|родител|детск|кухн|готовк|рецепт|огород|дач|авто(?!матиз)|"
    r"спорт|футбол|хоккей|рыбал|охот|маникюр|красот|салон|парикмах|юмор|анекдот|прикол",
    re.IGNORECASE)

# block only when no STRONG AI match
SOFT_DROP_RE = re.compile(r"бизнес|контент|картинк|маркетинг|seo|заработок|деньг|блог", re.IGNORECASE)

def hay(e):
    return (str(e.get("title") or "") + " " + str(e.get("channel") or "")).lower()

def is_ai(e):
    h = hay(e)
    if HARD_DROP_RE.search(h):
        return False
    if STRONG_AI_RE.search(h):
        return True
    if SOFT_DROP_RE.search(h):
        return False
    return bool(WEAK_AI_RE.search(h))
