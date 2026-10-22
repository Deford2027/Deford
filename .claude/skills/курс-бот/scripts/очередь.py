#!/usr/bin/env python3
"""
Помощник для обработки курсов СВОИМИ СИЛАМИ (без OpenRouter).

Готовит очередь файлов и проверяет результат. Саму чистку делает агент:
читает файл, переписывает, сохраняет. Деньги OpenRouter при этом не тратятся.

  python3 очередь.py --папка "путь"            # что осталось обработать
  python3 очередь.py --папка "путь" --проверка  # метрики готового
"""
import argparse, glob, os, re, sys

ИНСТР = re.compile(r"\b(Ahrefs|Semrush|Screaming Frog|ChatGPT|Claude|Gemini|DeepSeek|Qwen|"
                   r"n8n|Perplexity|Keys\.?so|XMLRiver|Search Console|GSC|Firecrawl|Cursor|"
                   r"Notion|Python|Excel|Wordstat|Serpstat|Netpeak)\b", re.I)
ЧИСЛА = re.compile(r"\b\d+[.,]?\d*\s?(?:%|проц|сек|мин|час|шт|раз|тыс|млн|px|дн|руб)")


def пара(путь, папка):
    """Исходник → куда класть результат."""
    имя = os.path.basename(папка.rstrip("/"))
    return путь.replace(f"/{имя}/", f"/{имя} (чистое)/")


def расшифровка(путь):
    t = open(путь, encoding="utf-8", errors="replace").read()
    if "## Расшифровка видео" not in t:
        return None, t
    return t.split("## Расшифровка видео", 1)[1].split("\n## ")[0].strip(), t


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--папка", required=True)
    ap.add_argument("--проверка", action="store_true")
    ap.add_argument("--сколько", type=int, default=10, help="показать N файлов очереди")
    a = ap.parse_args()
    папка = os.path.expanduser(a.папка)

    файлы = sorted(f for f in glob.glob(os.path.join(папка, "*", "*.md"))
                   if "_КУРС_целиком" not in f)

    if a.проверка:
        иб = ис = чб = чс = было = стало = заг = корот = 0
        готово = 0
        for f in файлы:
            вых = пара(f, папка)
            if not os.path.exists(вых):
                continue
            готово += 1
            рас, _ = расшифровка(f)
            if not рас:
                continue
            n = open(вых, encoding="utf-8", errors="replace").read()
            было += len(рас); стало += len(n)
            заг += len(re.findall(r"^#{1,4} ", n, re.M))
            if len(n) < 400:
                корот += 1
            b = {x.lower() for x in ИНСТР.findall(рас)}
            s = {x.lower() for x in ИНСТР.findall(n)}
            иб += len(b); ис += len(b & s)
            cb = {m.group(0).lower() for m in ЧИСЛА.finditer(рас)}
            cs = {m.group(0).lower() for m in ЧИСЛА.finditer(n)}
            чб += len(cb); чс += len(cb & cs)
        print(f"готово файлов:        {готово} из {len(файлы)}")
        if иб:
            print(f"инструменты:          {ис}/{иб}  ({ис*100//иб}%)")
            print(f"значения:             {чс}/{чб}  ({чс*100//max(чб,1)}%)")
            print(f"объём:                {было/1e6:.2f} млн → {стало/1e6:.2f} млн "
                  f"({стало*100//max(было,1)}%)")
            print(f"заголовков на урок:   {заг//max(готово,1)}")
            print(f"подозрительно коротких: {корот}")
            print("\nОриентир (замер SEO Мясо): инструменты 98%, значения 95%, объём 103%,")
            print("14 заголовков на урок, коротких 0. Сильное отклонение — разбираться.")
        sys.exit()

    осталось = [f for f in файлы if not os.path.exists(пара(f, папка))]
    без_видео = 0
    очередь = []
    for f in осталось:
        рас, _ = расшифровка(f)
        if рас is None or len(рас) < 200:
            без_видео += 1
            continue
        очередь.append((len(рас), f))
    print(f"всего файлов:     {len(файлы)}")
    print(f"уже обработано:   {len(файлы)-len(осталось)}")
    print(f"без расшифровки:  {без_видео} (обрабатывать нечего)")
    print(f"В ОЧЕРЕДИ:        {len(очередь)}")
    if очередь:
        знаков = sum(n for n, _ in очередь)
        print(f"знаков суммарно:  {знаков/1e6:.2f} млн  (~{знаков//3500} тыс. токенов на чтение)")
        print(f"\nближайшие {min(a.сколько,len(очередь))}:")
        for n, f in очередь[:a.сколько]:
            print(f"  {n:>7,}  {os.path.relpath(f, папка)}")
