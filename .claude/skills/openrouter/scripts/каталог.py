#!/usr/bin/env python3
"""
Полная выгрузка каталога OpenRouter в файлы. Ничего не тянет через контекст агента:
пишет справочники на диск, агент их потом грепает.

  python3 каталог.py                  # обновить справочники
  python3 каталог.py --что-нового     # только изменения с прошлого раза
"""
import argparse, json, os, re, sys, time, urllib.request

БАЗА = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "references")
СНИМОК = os.path.join(БАЗА, ".снимок.json")
API = "https://openrouter.ai/api/v1/models"


def ключ():
    p = os.path.expanduser("~/.claude/secrets/openrouter.key")
    if os.path.exists(p):
        return open(p).read().strip()
    return os.environ.get("OPENROUTER_API_KEY", "").strip()


def ц(p, k):
    v = (p or {}).get(k)
    if isinstance(v, list) or v is None:
        return 0.0
    try:
        return float(v)
    except Exception:
        return 0.0


def умеет(m):
    """Что модель умеет — строго из полей каталога, без домыслов о качестве."""
    a = m.get("architecture") or {}
    вх = set(a.get("input_modalities") or [])
    вых = set(a.get("output_modalities") or [])
    par = set(m.get("supported_parameters") or [])
    t = []
    если = lambda c, s: t.append(s) if c else None
    если("image" in вых, "рисует картинки")
    если("audio" in вых, "синтезирует речь")
    если("image" in вх, "видит картинки")
    если("video" in вх, "понимает видео")
    если("audio" in вх, "слушает аудио")
    если("file" in вх, "читает PDF")
    если("tools" in par, "инструменты")
    если("structured_outputs" in par, "строгий JSON")
    если("reasoning" in par, "рассуждает")
    если(ц(m.get("pricing"), "web_search") > 0, "ищет в вебе")
    return ", ".join(t) or "текст"


def суть(m):
    """Первая фраза описания вендора. Это заявление производителя — факт того,
    что он сам заявляет, а не наша оценка качества."""
    d = (m.get("description") or "").strip().replace("\n", " ")
    d = re.sub(r"\s+", " ", d)
    m1 = re.split(r"(?<=[.!?])\s+", d)
    s = m1[0] if m1 else ""
    return s[:230]


def выгрузить():
    key = ключ()
    if not key:
        sys.exit("нет ключа OpenRouter")
    req = urllib.request.Request(API, headers={"Authorization": "Bearer " + key})
    d = json.loads(urllib.request.urlopen(req, timeout=90).read())["data"]
    d.sort(key=lambda m: -(m.get("created") or 0))
    os.makedirs(БАЗА, exist_ok=True)

    строк = ["# Полный каталог OpenRouter — все модели\n",
             f"Выгружено {time.strftime('%d.%m.%Y')} скриптом `scripts/каталог.py`. "
             f"Моделей: **{len(d)}**. Сортировка — от новых к старым.\n",
             "**Цена, контекст, потолок вывода и умения — факты из каталога.** "
             "Строка «вендор» — первая фраза описания производителя, то есть его "
             "собственное заявление о модели.\n",
             "⚠️ **Качество моделей здесь не измерено и не сравнивается.** Кто «лучше» "
             "зависит от задачи; сравнивать надо прогоном на своей задаче, а не по "
             "цене. Дорогая не значит подходящая.\n",
             "⚠️ Здесь только то, что отдаёт API. Эмбеддинги, реранк, транскрибация, "
             "видео и TTS — в `не-текстовые.md`.\n", "---\n"]
    for m in d:
        p = m.get("pricing") or {}
        вх, вых = ц(p, "prompt") * 1e6, ц(p, "completion") * 1e6
        tp = m.get("top_provider") or {}
        mc = tp.get("max_completion_tokens")
        ctx = m.get("context_length") or 0
        цена = "бесплатно" if (вх == 0 and вых == 0) else f"${вх:.3f} / ${вых:.3f} за 1М"
        доп = []
        if ц(p, "web_search"): доп.append(f"поиск +${ц(p,'web_search')}/запрос")
        if ц(p, "image_output"): доп.append(f"картинка ${ц(p,'image_output')}")
        if ц(p, "input_cache_read"): доп.append("есть кэш ввода")
        kc = m.get("knowledge_cutoff")
        строк.append(f"### `{m['id']}`")
        строк.append(f"{цена} · контекст {ctx:,} · потолок вывода "
                     f"{mc if mc else 'не указан'}" + (f" · знания до {kc}" if kc else ""))
        if доп: строк.append("Тарифицируется отдельно: " + "; ".join(доп))
        строк.append(f"Умеет: {умеет(m)}")
        s = суть(m)
        if s: строк.append(f"Вендор: {s}")
        строк.append("")
    open(os.path.join(БАЗА, "все-модели.md"), "w", encoding="utf-8").write("\n".join(строк))

    снимок = {m["id"]: {"created": m.get("created"),
                        "in": ц(m.get("pricing"), "prompt"),
                        "out": ц(m.get("pricing"), "completion")} for m in d}
    return d, снимок


def что_нового(новый):
    старый = {}
    if os.path.exists(СНИМОК):
        try:
            старый = json.load(open(СНИМОК))
        except Exception:
            pass
    появились = [k for k in новый if k not in старый]
    исчезли = [k for k in старый if k not in новый]
    подорожали, подешевели = [], []
    for k in новый:
        if k in старый:
            бы, ст = старый[k]["out"], новый[k]["out"]
            if бы and ст and abs(ст - бы) / бы > 0.05:
                (подорожали if ст > бы else подешевели).append(
                    f"{k}: ${бы*1e6:.2f} → ${ст*1e6:.2f} за 1М")
    json.dump(новый, open(СНИМОК, "w"))
    return появились, исчезли, подорожали, подешевели


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--что-нового", action="store_true")
    a = ap.parse_args()
    d, снимок = выгрузить()
    print(f"выгружено моделей: {len(d)} → references/все-модели.md")
    появились, исчезли, дороже, дешевле = что_нового(снимок)
    if a.что_нового or появились or исчезли:
        print(f"\nНОВЫХ: {len(появились)}")
        for k in появились[:25]:
            print("  +", k)
        if исчезли:
            print(f"ИСЧЕЗЛИ: {len(исчезли)}")
            for k in исчезли[:15]:
                print("  −", k)
        for имя, сп in (("ПОДОРОЖАЛИ", дороже), ("ПОДЕШЕВЕЛИ", дешевле)):
            if сп:
                print(f"{имя}: {len(сп)}")
                for s in сп[:10]:
                    print("   ", s)
