#!/usr/bin/env python3
"""Золотоискатель: поиск тем по всем банкам залетевшего контента.

Локальные банки (исследование 18.09.2026, бесплатно, мгновенно):
  yt   — 968 залетевших длинных YouTube (≥3× к медиане канала и к соседям по дате)
  car  — 474 карусели Instagram, размечены вслепую (208 залетевших ≥2×)
  reel — 194 рилса с расшифровкой (97 залетевших ≥3×)
Серверная база trend-watcher (по ssh, бесплатно):
  tt   — углы, снятые с залетевших TikTok/YouTube Shorts (content_angles)
  ask  — поисковые запросы людей (content_questions)
  radar— радар подтем (content_topics)

Примеры:
  python3 gold.py "money rich wealth деньги"             # всё по словам
  python3 gold.py "ai агент automation" --src yt,tt
  python3 gold.py --broad                                 # какие широкие темы залетают у многих авторов
  python3 gold.py --formulas car                          # шаблоны обложек залетевших каруселей
  python3 gold.py --formulas reel --type провокация       # шаблоны первых фраз рилсов
  python3 gold.py --demand "пассивный доход"               # спрос по любой нише, Google + Яндекс
"""
import argparse, csv, json, math, os, re, subprocess, sys, collections

R = os.path.expanduser("~/Research/carousels_reels_2026-09")
F_YT = f"{R}/банк_тем_youtube_выбросы.csv"
F_CAR = f"{R}/coded_car.json"
F_REEL = f"{R}/coded_reel.json"
SSH = ["ssh", "-o", "ConnectTimeout=25", "root@45.12.73.217"]

STOP = set("the a an and or of to in on for with is are be you your my i me how why what this that it at by from as "
           "и в на с по для как что это не а но к у о из за от до же ли то все всё".split())


def stems(s):
    """Грубая основа слова: первые 5 букв, без стоп-слов. Хватает для сравнения заголовков."""
    return {w[:5] for w in re.findall(r"[a-zа-яё0-9$]+", (s or "").lower()) if w not in STOP and len(w) > 2}


def need(path):
    if not os.path.exists(path):
        sys.exit(f"❌ Нет банка {path}. Банки лежат в {R} — без них поиск вернёт ноль, это не «тем нет».")


JUNK = re.compile(r"affirmation|\b\d{3} ?hz\b|sleep music|meditation music|asmr|compilation|full movie|"
                  r"highlights|reaction|аффирмац|медитац.*музык", re.I)


def match(q, *fields):
    """Сколько слов запроса нашлось. Слово ищется с начала слова: «ai» не цепляет «said»,
    а «богат» цепляет «богатство»."""
    text = " ".join(f or "" for f in fields).lower()
    def pat(w):
        if re.search("[а-яё]", w):
            return r"(?<![а-яё0-9])" + re.escape(w)                     # русское: по началу слова
        return r"(?<![a-z0-9])" + re.escape(w) + r"[a-z]{0,3}(?![a-z])"   # английское: + короткое окончание
    return sum(1 for w in q if re.search(pat(w), text))


def rank(m, bo):
    """Совпадение важно, но сильный залёт важнее лишнего совпавшего слова."""
    return m * 0.6 + math.log10(max(bo, 1))


def load_yt():
    need(F_YT)
    return list(csv.DictReader(open(F_YT)))


def search_yt(q, n, min_views):
    rows = [r for r in load_yt() if int(r["просмотры"]) >= min_views and not JUNK.search(r["заголовок"])
            and r["релевантно"] != "0"]
    hits = [(match(q, r["заголовок"], r["тема (разметка)"], r["категория"]), r) for r in rows]
    hits = [(m, r) for m, r in hits if m]
    hits.sort(key=lambda x: -rank(x[0], float(x[1]["пробитие канала"])))
    top = hits[:n]
    # повтор: у скольких РАЗНЫХ каналов залетали ролики с тем же ядром заголовка
    allr = load_yt()
    out = []
    for m, r in top:
        s = stems(r["заголовок"])
        rep = {x["канал"] for x in allr if len(s & stems(x["заголовок"])) >= 2}
        out.append((r, len(rep)))
    return out, len({r["канал"] for _, r in hits})


def search_coded(path, q, n, kind):
    need(path)
    rows = json.load(open(path))
    hits = []
    for d in rows:
        if not d["_out"]:
            continue
        form = d.get("cover_formula") or d.get("hook_formula") or ""
        m = match(q, d.get("theme"), form, d.get("first_line"), d.get("cat"))
        if m:
            hits.append((m, d))
    hits.sort(key=lambda x: -rank(x[0], x[1]["_bo"]))
    return [d for _, d in hits[:n]], len({d["_h"] for _, d in hits})


def server(py):
    cmd = SSH + [f"cd /opt/startup-trend-watcher && docker compose exec -T app python -c {json.dumps(py)}"]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
    except subprocess.TimeoutExpired:
        return None, "таймаут ssh"
    if r.returncode != 0:
        return None, (r.stderr or r.stdout)[-300:]
    return r.stdout, None


def search_server(q, n, what):
    like = " OR ".join(["{col} LIKE ?"] * len(q))
    args = [f"%{w}%" for w in q]
    if what == "tt":
        sql = (f"SELECT angle, topic, views, save_pct, shares_pct, mechanic, url FROM content_angles "
               f"WHERE {like.format(col='(angle||topic||interest)')} ORDER BY views DESC LIMIT {n}")
    elif what == "ask":
        sql = (f"SELECT question, seed, source FROM content_questions WHERE {like.format(col='question')} "
               f"ORDER BY is_question DESC, id DESC LIMIT {n}")
    else:
        sql = (f"SELECT name, why_now, uses, last_seen FROM content_topics WHERE {like.format(col='(name||why_now)')} "
               f"ORDER BY uses DESC LIMIT {n}")
    py = ("import sqlite3,json;c=sqlite3.connect('data/trend_watcher.db');"
          f"print(json.dumps(c.execute({sql!r},{args!r}).fetchall(),ensure_ascii=False))")
    out, err = server(py)
    if err:
        return None, err
    return json.loads(out.strip().splitlines()[-1]), None


def suggest(q, lang):
    """Подсказки поисковиков: Google (ru/en) и Яндекс. Бесплатно, без ключей."""
    import urllib.request, urllib.parse
    urls = [("google", f"https://suggestqueries.google.com/complete/search?client=firefox&hl={lang}&q={urllib.parse.quote(q)}")]
    if lang == "ru":
        urls.append(("yandex", f"https://suggest.yandex.ru/suggest-ff.cgi?part={urllib.parse.quote(q)}&uil=ru"))
    out = []
    for name, u in urls:
        try:
            raw = urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=10).read()
            data = json.loads(raw.decode("utf-8", "ignore"))
            out += [(name, x) for x in data[1] if isinstance(x, str)]
        except Exception as e:
            out.append((name, f"⚠️ не ответил: {e}"))
    return out


def run_demand(a):
    seed = a.demand.strip()
    lang = "ru" if re.search("[а-яё]", seed.lower()) else "en"
    tails = ["", " как", " почему", " что делать", " если"] if lang == "ru" else ["", " how", " why", " what", " for beginners"]
    abc = "абвгдежзиклмнопрстуфхцчшэюя" if lang == "ru" else "abcdefghijklmnopqrstuvwxyz"
    seen, qs, errors = set(), [], []
    for t in tails + [" " + ch for ch in abc[: a.depth]]:
        for src, x in suggest(seed + t, lang):
            if x.startswith("⚠️"):
                errors.append(f"{src}: {x}"); continue
            if x.lower() not in seen:
                seen.add(x.lower()); qs.append(x)
    if errors and not qs:
        sys.exit("❌ Поисковики не ответили — это сбой сети, а не «спроса нет»:\n  " + "\n  ".join(errors[:3]))
    quest = [x for x in qs if re.search(r"\b(как|почему|зачем|что|можно ли|нужно ли|how|why|what|can|should|is)\b", x.lower())]
    print(f"━━ СПРОС по «{seed}»: {len(qs)} запросов, из них вопросов {len(quest)} ━━")
    print("\nВопросы (почти готовые первые фразы — это слова самого зрителя):")
    for x in quest[:a.n * 4]: print("  ", x)
    print("\nДлинный хвост (кому именно это нужно):")
    for x in [x for x in qs if x not in quest][:a.n * 4]: print("  ", x)


def fmt_k(x):
    x = int(float(x))
    return f"{x/1e6:.1f}млн" if x >= 1e6 else f"{x/1e3:.0f}тыс" if x >= 1e3 else str(x)


def run_search(a):
    q = [w.lower() for w in re.findall(r"[\w$]+", a.query) if len(w) > 1]
    if not q:
        sys.exit("Дай слова для поиска: по-английски и по-русски (банки YouTube и Instagram англоязычные)")
    src = a.src.split(",")
    if "yt" in src:
        res, authors = search_yt(q, a.n, a.min_views)
        print(f"\n━━ ДЛИННЫЙ YOUTUBE — залетевшие (≥3× канала), совпадений у {authors} каналов ━━")
        for r, rep in res:
            print(f"  ×{float(r['пробитие канала']):<6.1f} {fmt_k(r['просмотры']):>7}  {r['минут']:>3}м  «{r['заголовок'][:90]}»")
            extra = f"   тема: {r['тема (разметка)']}" if r["тема (разметка)"] else ""
            print(f"         канал: {r['канал'][:30]} · ядро заголовка залетало у {rep} каналов{extra}")
            if r["формула заголовка"]:
                print(f"         формула: {r['формула заголовка'][:110]}")
    if "car" in src:
        res, authors = search_coded(F_CAR, q, a.n, "car")
        print(f"\n━━ КАРУСЕЛИ INSTAGRAM — залетевшие (≥2× автора), совпадений у {authors} авторов ━━")
        for d in res:
            print(f"  ×{d['_bo']:<6.1f} [{d['hook']}, {d['emotion']}{', к моменту' if str(d['timely'])=='1' else ''}] {d['theme']}")
            if d.get("cover_formula"):
                print(f"         обложка: {d['cover_formula'][:120]}")
            print(f"         https://www.instagram.com/p/{d['_code']}/")
    if "reel" in src:
        res, authors = search_coded(F_REEL, q, a.n, "reel")
        print(f"\n━━ РИЛСЫ INSTAGRAM — залетевшие (≥3× автора), совпадений у {authors} авторов ━━")
        for d in res:
            print(f"  ×{d['_bo']:<6.1f} [{d['hook']}] {d['theme']}")
            print(f"         первая фраза: {d['first_line'][:110]}")
            print(f"         формула: {d['hook_formula'][:110]}")
    for what, title in (("tt", "УГЛЫ С ЗАЛЕТЕВШИХ TIKTOK/SHORTS (сервер)"), ("ask", "ЧТО ИЩУТ ЛЮДИ (сервер)"),
                        ("radar", "РАДАР ПОДТЕМ (сервер)")):
        if what not in src:
            continue
        rows, err = search_server(q, a.n, what)
        print(f"\n━━ {title} ━━")
        if err:
            print(f"  ⚠️ сервер не ответил: {err.strip()[:200]} — это сбой, а не «тем нет»")
            continue
        if not rows:
            print("  совпадений нет")
        for r in rows:
            if what == "tt":
                num = lambda v: float(v) if str(v).replace('.', '', 1).isdigit() else 0.0
                print(f"  {fmt_k(num(r[2])):>7} сохр {num(r[3]):.1f}% реп {num(r[4]):.1f}% · {r[0][:100]}  ({r[5] or ''})")
            elif what == "ask":
                print(f"  {r[0][:110]}   [{r[2]}]")
            else:
                print(f"  {r[0][:80]} · подтверждений {r[2]} · последнее {str(r[3])[:10]}")


def run_broad(a):
    rows = load_yt()
    coded = json.load(open(F_YT.replace("банк_тем_youtube_выбросы.csv", "coded_yt.json"))) if os.path.exists(f"{R}/coded_yt.json") else []
    print("━━ ШИРОКИЕ ТЕМЫ ДЛИННОГО YOUTUBE: у скольких разных каналов залетали (размечено 463 из 968) ━━")
    by = collections.defaultdict(lambda: {"ch": set(), "n": 0, "views": []})
    for r in rows:
        if r["категория"] and r["релевантно"] == "1":
            g = by[r["категория"]]; g["ch"].add(r["канал"]); g["n"] += 1; g["views"].append(int(r["просмотры"]))
    for cat, g in sorted(by.items(), key=lambda x: -len(x[1]["ch"])):
        v = sorted(g["views"])[len(g["views"]) // 2]
        print(f"  {cat:34} каналов {len(g['ch']):3}  роликов {g['n']:3}  медиана просмотров {fmt_k(v)}")
    car = json.load(open(F_CAR))
    print("\n━━ КАРУСЕЛИ: доля залетевших по категории (сравнивать осторожно — между авторами) ━━")
    by = collections.defaultdict(lambda: [0, 0, set()])
    for d in car:
        g = by[d["cat"]]; g[0] += 1; g[1] += d["_out"]; g[2].add(d["_h"])
    for cat, (n, o, hs) in sorted(by.items(), key=lambda x: -x[1][1]):
        print(f"  {cat:34} залетевших {o:3} из {n:3} · авторов {len(hs)}")


def run_formulas(a):
    kind = a.formulas
    if kind == "yt":
        rows = [r for r in load_yt() if r["формула заголовка"]]
        rows.sort(key=lambda r: -float(r["пробитие канала"]))
        for r in rows[: a.n]:
            print(f"  ×{float(r['пробитие канала']):<6.1f} [{r['механизм']}] {r['формула заголовка'][:120]}")
        return
    path = F_CAR if kind == "car" else F_REEL
    need(path)
    rows = [d for d in json.load(open(path)) if d["_out"]]
    key = "cover_formula" if kind == "car" else "hook_formula"
    if a.type:
        rows = [d for d in rows if a.type in (d.get("hook") or "") or a.type in (d.get("hook2") or "")]
    rows = [d for d in rows if d.get(key)]
    rows.sort(key=lambda d: -d["_bo"])
    for d in rows[: a.n]:
        print(f"  ×{d['_bo']:<6.1f} [{d['hook']}] {d[key][:130]}")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("query", nargs="?", default="")
    p.add_argument("--src", default="yt,car,reel,tt,ask", help="yt,car,reel,tt,ask,radar")
    p.add_argument("-n", type=int, default=8)
    p.add_argument("--min-views", type=int, default=50000, help="порог просмотров для YouTube (абсолютный охват)")
    p.add_argument("--broad", action="store_true")
    p.add_argument("--formulas", choices=["car", "reel", "yt"])
    p.add_argument("--type", default="", help="фильтр по типу хука для --formulas")
    p.add_argument("--demand", default="", help="спрос по фразе через автодополнение Google/Яндекс (любая ниша)")
    p.add_argument("--depth", type=int, default=12, help="сколько букв алфавита перебирать для --demand")
    a = p.parse_args()
    if a.demand:
        run_demand(a)
    elif a.broad:
        run_broad(a)
    elif a.formulas:
        run_formulas(a)
    else:
        run_search(a)
