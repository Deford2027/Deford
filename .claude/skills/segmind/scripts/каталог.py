#!/usr/bin/env python3
"""
Выгрузка каталога Segmind из официального llms.txt — машиночитаемого каталога,
который сервис публикует специально для агентов.

Один запрос вместо 512 обходов страниц. Отдаёт: название, slug, описание,
категорию, цену за генерацию и латентность.

  python3 каталог.py                # обновить справочник
  python3 каталог.py --что-нового   # что появилось с прошлого раза
"""
import argparse, html as _html, json, os, re, time, urllib.request

БАЗА = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "references")
СНИМОК = os.path.join(БАЗА, ".снимок.json")
ИСТОЧНИК = "https://www.segmind.com/llms.txt"
SITEMAP = "https://www.segmind.com/sitemap.xml"


def достать():
    req = urllib.request.Request(ИСТОЧНИК, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=90) as r:
        return r.read().decode("utf-8", "replace")


def из_sitemap():
    """Второй источник. Замерено 09.09.2026: в sitemap есть 3 модели, которых
    в llms.txt нет. Полагаться на один источник — терять модели."""
    try:
        req = urllib.request.Request(SITEMAP, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=90) as r:
            xml = r.read().decode("utf-8", "replace")
    except Exception:
        return set()
    из = set()
    for u in re.findall(r"<loc>([^<]+)</loc>", xml):
        m = re.match(r"https://www\.segmind\.com/models/([^/]+)/?$", u)
        if m and m.group(1) not in ("all", "tags"):
            из.add(m.group(1))
    return из


def разобрать(txt):
    """Строки вида: | Название | slug | описание | категория | $цена | латентность |"""
    модели, категория = [], ""
    for ln in txt.splitlines():
        s = ln.strip()
        if s.startswith("## "):
            категория = s[3:].strip()
            continue
        if not s.startswith("|"):
            continue
        ч = [x.strip() for x in s.strip("|").split("|")]
        if len(ч) < 4:
            continue
        slug = ч[1]
        # Отсечь служебные строки таблиц: шапку, разделитель, сдвинутые колонки.
        if (not slug or " " in slug or slug.lower() in ("slug", "model", "name")
                or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", slug)):
            continue
        цена = ""
        m = re.search(r"\$\s*([0-9]*\.?[0-9]+)", s)
        if m:
            v = float(m.group(1))
            цена = f"{v:.4f}".rstrip("0").rstrip(".") if v < 1 else f"{v:.2f}"
        лат = ""
        m = re.search(r"([0-9]+\.?[0-9]*)s\b", s)
        if m:
            лат = f"{float(m.group(1)):.0f}с"
        опис = re.sub(r"\s+", " ", _html.unescape(ч[2])).strip()
        модели.append({"имя": ч[0], "slug": slug, "описание": опис[:200],
                       "категория": (ч[3] if len(ч) > 3 else "") or категория,
                       "цена": цена, "латентность": лат})
    return модели


def записать(модели):
    os.makedirs(БАЗА, exist_ok=True)
    по_кат = {}
    for m in модели:
        по_кат.setdefault(m["категория"] or "без категории", []).append(m)
    строк = [
        "# Segmind — полный каталог моделей\n",
        f"Выгружено {time.strftime('%d.%m.%Y')} скриптом `scripts/каталог.py` из "
        f"официального `segmind.com/llms.txt` — машиночитаемого каталога сервиса. "
        f"Моделей: **{len(модели)}**.\n",
        "Цена — за одну генерацию. Латентность — заявленное время работы. "
        "Категория и описание — от самого сервиса.\n",
        "⚠️ **Качество моделей здесь не измерено и не сравнивается.** Что подойдёт "
        "под конкретную задачу, показывает только прогон на своём материале. "
        "Порядок в списках — по цене, а не по «качеству».\n",
        "Детальная спека любой модели: `segmind.com/models/{slug}/llms.txt`\n",
    ]
    for кат in sorted(по_кат, key=lambda k: -len(по_кат[k])):
        сп = sorted(по_кат[кат], key=lambda m: float(m["цена"] or 0))
        строк.append(f"\n## {кат} — {len(сп)} шт\n")
        for m in сп:
            ц = f"**${m['цена']}**" if m["цена"] else "цена не указана"
            л = f" · {m['латентность']}" if m["латентность"] else ""
            строк.append(f"- `{m['slug']}` · {ц}{л} — {m['имя']}. {m['описание']}")
    open(os.path.join(БАЗА, "все-модели.md"), "w", encoding="utf-8").write("\n".join(строк))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--что-нового", action="store_true")
    a = ap.parse_args()

    модели = разобрать(достать())
    есть = {m["slug"] for m in модели}
    добор = sorted(из_sitemap() - есть)
    for s in добор:
        модели.append({"имя": s, "slug": s, "описание": "нет в llms.txt, найдена в sitemap",
                       "категория": "только в sitemap", "цена": "", "латентность": ""})
    if добор:
        print(f"добрано из sitemap (нет в llms.txt): {len(добор)} — {', '.join(добор)}")
    записать(модели)
    цен = sum(1 for m in модели if m["цена"])
    print(f"моделей: {len(модели)} (с ценой {цен}) → references/все-модели.md")

    новый = {m["slug"]: m["цена"] for m in модели}
    старый = json.load(open(СНИМОК)) if os.path.exists(СНИМОК) else {}
    if isinstance(старый, list):
        старый = {s: "" for s in старый}
    появились = [s for s in новый if s not in старый]
    ушли = [s for s in старый if s not in новый]
    сдвиг = []
    for s in новый:
        a1, b1 = старый.get(s), новый[s]
        if a1 and b1 and a1 != b1:
            try:
                if abs(float(b1) - float(a1)) / float(a1) > 0.05:
                    сдвиг.append(f"{s}: ${a1} → ${b1}")
            except Exception:
                pass
    json.dump(новый, open(СНИМОК, "w"))
    if появились:
        print(f"\nНОВЫХ: {len(появились)}")
        for s in появились[:30]:
            print("  +", s)
    if ушли:
        print(f"УБРАЛИ: {len(ушли)}")
        for s in ушли[:15]:
            print("  −", s)
    if сдвиг:
        print(f"ЦЕНА ИЗМЕНИЛАСЬ: {len(сдвиг)}")
        for s in сдвиг[:12]:
            print("   ", s)
