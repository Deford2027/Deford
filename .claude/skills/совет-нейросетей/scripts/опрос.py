#!/usr/bin/env python3
"""
Опрос совета нейросетей через OpenRouter.

Задача скрипта — гарантировать ПОЛНОТУ ответа. Обрыв по max_tokens это лишь
один из полутора десятков способов получить огрызок; здесь ловятся все
известные, а недописанный ответ ДОПИСЫВАЕТСЯ (не перезапрашивается заново).

  python3 опрос.py --вопрос q.md
  python3 опрос.py --вопрос q.md --разделы "1),2),3),4)"
  python3 опрос.py --вопрос q.md --модели grok --роль оппонент
"""
import argparse, json, os, re, sys, time, urllib.error, urllib.parse, urllib.request, concurrent.futures

URL = "https://openrouter.ai/api/v1/chat/completions"
ПОЛ_ЛИМИТА = 4000        # ниже этого ризонинг-модели не выживают
МИН_ВИДИМЫХ = 40         # токенов видимого текста; меньше — размышления съели ответ
ДОПИСОК = 3              # сколько раз продолжаем оборванный ответ
# Поисковые модели берут за веб-запросы СВЕРХ токенов, в usage этого не видно.
# Цифры из поля pricing.web_search каталога, сверены с фактическим счётом 09.09.2026.
ПОИСК_НАДБАВКА = {"perplexity": 0.018, "ppx-pro": 0.005,
                  "ppx-reasoning": 0.005, "ppx-deep": 0.005}

СОВЕТ = {
    "gpt":        ("openai/gpt-5.6-sol",            2.00, 10.00),
    "gemini":     ("google/gemini-3.8-flash",       0.75,  3.75),
    "grok":       ("x-ai/grok-4.6",                 2.00,  6.00),
    "deepseek":   ("deepseek/deepseek-v4-pro-0813", 1.05,  3.15),   # скидка плавает, сверять
    "perplexity": ("perplexity/sonar-pro-search",   3.00, 15.00),   # +поиск, см. ПОИСК_НАДБАВКА
}
РЕЗЕРВ = {   # звать по нужде: дублируют школы основного состава или дороги
    "qwen":  ("qwen/qwen3.8-max-0902",      2.00,  6.00),   # 24 мин на большом входе
    "kimi":  ("moonshotai/kimi-k3",         2.40, 12.00),
    # Варианты Perplexity. Замер 09.09.2026 на вопросе с проверяемым ответом:
    # pro пропустил GPT-6 Astra и Opus 5; reasoning пропустил Fable 5.1 и выдумал
    # несуществующую модель; sonar не нашёл ничего. Дешевле — но дырявее.
    "ppx-pro":       ("perplexity/sonar-pro",           3.00, 15.00),
    "ppx-reasoning": ("perplexity/sonar-reasoning-pro", 2.00,  8.00),
    # Deep research: $0.75 и 4.5 минуты за ОДИН запрос, при 6000 лимита обрывается.
    "ppx-deep":      ("perplexity/sonar-deep-research", 2.00,  8.00),
}
ТЯЖЁЛЫЙ = {
    "astra": ("openai/gpt-6-astra",         10.00, 50.00),
    "fable": ("anthropic/claude-fable-5.1", 10.00, 50.00),
    "opus":  ("anthropic/claude-opus-5",     5.00, 25.00),
}

РОЛИ = {
    "оппонент": "Твоя работа — найти слабые места, а не согласиться. Что упущено, что "
                "развалится на практике, какие допущения не проверены. Не смягчай.",
    "ревизор":  "Найди: что пропущено, что лишнее, где допущение выдано за факт. "
                "Не пересказывай исходное — только находки.",
    "фактчек":  "Проверяй фактическую сторону. По каждому утверждению: подтверждается, "
                "устарело или не проверяется. Давай источник и его дату. Не рассуждай.",
    "логика":   "Проверь рассуждение на прочность. Ищи логические разрывы и контрпримеры. "
                "Если вывод не следует из посылок — покажи, где именно.",
    "альтернатива": "Предложи решение, которое обычно не рассматривают. Не критикуй "
                    "чужое — дай другой рабочий путь и честно назови его цену.",
}
# Разным школам — разные задачи по одному предмету. Шесть одинаковых «ревизоров»
# дают шесть однотипных придирок и убивают смысл разных школ.
БРИФ_ПО_УМОЛЧАНИЮ = {
    "grok": "оппонент", "deepseek": "логика", "qwen": "логика",
    
    "gpt": "альтернатива", "gemini": "альтернатива", "perplexity": "фактчек",
}

ОТКАЗ = re.compile(r"^\s*(я не могу|я не буду|к сожалению,? я|как (?:ии|ai|языковая)|"
                   r"i (?:cannot|can't|am unable)|as an ai)", re.I)
ЛЕНЬ = re.compile(r"(и так далее по аналогии|остальное аналогично|// ?TODO|"
                  r"вставьте (?:сюда|ваш)|to be continued|продолжу в следующ)", re.I)
ОБРЫВ_FR = {"length", "max_tokens", "MAX_TOKENS", "error", "ERROR"}


ПОТОЛКИ_КЭШ = os.path.expanduser("~/.claude/secrets/.or_limits.json")

def потолки(key):
    """max_completion_tokens по моделям. Просить больше физического потолка нельзя:
    провайдер всё равно режет и возвращает length, а попытка оплачена.
    Так у perplexity (потолок 8000) три дописки сожгли $0.34 впустую."""
    try:
        st = os.stat(ПОТОЛКИ_КЭШ)
        if time.time() - st.st_mtime < 86400:
            return json.load(open(ПОТОЛКИ_КЭШ))
    except Exception:
        pass
    try:
        r = urllib.request.urlopen(urllib.request.Request(
            "https://openrouter.ai/api/v1/models",
            headers={"Authorization": "Bearer " + key}), timeout=60)
        out = {}
        for m in (json.loads(r.read()) or {}).get("data", []):
            mc = (m.get("top_provider") or {}).get("max_completion_tokens")
            if mc: out[m["id"]] = int(mc)
        json.dump(out, open(ПОТОЛКИ_КЭШ, "w"))
        os.chmod(ПОТОЛКИ_КЭШ, 0o600)
        return out
    except Exception:
        return {}


def ключ():
    p = os.path.expanduser("~/.claude/secrets/openrouter.key")
    if os.path.exists(p):
        return open(p).read().strip()
    if os.environ.get("OPENROUTER_API_KEY"):
        return os.environ["OPENROUTER_API_KEY"].strip()
    sys.exit("Нет ключа: ни ~/.claude/secrets/openrouter.key, ни $OPENROUTER_API_KEY")


def факт_цена(key, gen_id):
    """Фактическая стоимость генерации у провайдера. Оценка по токенам×прайс врёт
    (скидки, кэш, роутинг), а баланс обновляется с задержкой — проверено, два
    захода подряд дали дельту $0.00 при реальной трате. Источник истины — этот."""
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/generation?id=" + urllib.parse.quote(gen_id),
        headers={"Authorization": "Bearer " + key})
    for _ in range(3):                       # запись появляется не мгновенно
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                d = (json.loads(r.read()) or {}).get("data") or {}
            if d.get("total_cost") is not None:
                return float(d["total_cost"])
        except Exception:
            pass
        time.sleep(1.5)
    return None


def баланс(key):
    """Остаток на ключе — для отчёта владельцу, не для сверки одного захода."""
    req = urllib.request.Request("https://openrouter.ai/api/v1/credits",
                                 headers={"Authorization": "Bearer " + key})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            d = (json.loads(r.read()) or {}).get("data") or {}
        return float(d.get("total_credits", 0)) - float(d.get("total_usage", 0))
    except Exception:
        return None


def сеть(key, model, messages, лимит, таймаут):
    """Сырой вызов. transforms:[] — иначе OpenRouter МОЛЧА режет длинный вход."""
    body = json.dumps({"model": model, "messages": messages,
                       "max_tokens": лимит, "transforms": []}).encode()
    req = urllib.request.Request(URL, data=body, headers={
        "Authorization": "Bearer " + key, "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=таймаут) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        тело = ""
        try:
            тело = e.read().decode("utf-8", "replace")
            j = json.loads(тело)
        except Exception:
            j = None
        # 403 в чужом формате = режет что-то по дороге (гео-фильтр), а не OpenRouter.
        # Замерено на сервере РФ: {"success": false, "error": "Access denied by security policy."}
        if e.code == 403 or "Access denied by security policy" in тело:
            return {"error": {"message": "ТРАНСПОРТ ЗАКРЫТ: прямой путь в OpenRouter "
                                         "режется по дороге (403, формат не OpenRouter). "
                                         "Нужен прокси — см. references/каталог-ключ-цены.md",
                              "транспорт": True}}
        if isinstance(j, dict) and j.get("error"):
            return {"error": j["error"]}
        return {"error": {"message": f"HTTP {e.code}: {тело[:160]}"}}


def текст_из(ch):
    """content бывает строкой, бывает массивом частей, бывает null."""
    m = ch.get("message") or {}
    c = m.get("content")
    if isinstance(c, list):
        return "".join(p.get("text", "") for p in c if isinstance(p, dict))
    return c or ""


def неполон(текст, ch, u, лимит):
    """Возвращает причину неполноты или None. Порядок — от дешёвых проверок к дорогим."""
    fr = ch.get("finish_reason")
    native = ch.get("native_finish_reason")
    вых = u.get("completion_tokens") or 0
    думал = (u.get("completion_tokens_details") or {}).get("reasoning_tokens", 0) or 0

    if native in ОБРЫВ_FR or fr in ОБРЫВ_FR:
        return f"обрыв ({native or fr})"
    if вых and лимит and вых >= лимит - 4:
        return "упёрлось в лимит (provider соврал stop)"   # часть провайдеров врёт
    if not текст.strip():
        return "пустой content"
    if вых and (вых - думал) < МИН_ВИДИМЫХ:
        return f"размышления съели ответ ({думал} из {вых})"
    if "<think>" in текст and "</think>" not in текст:
        return "оборван thinking-тег"
    if текст.count("```") % 2:
        return "незакрытый блок кода"
    if ЛЕНЬ.search(текст[-400:]):
        return "ленивая заглушка в хвосте"
    if not текст.rstrip().endswith((".", "!", "?", ":", ")", "»", "`", "—")):
        return "хвост без знака препинания"
    return None


def спросить(key, алиас, model, ц_вх, ц_вых, вопрос, система, лимит, таймаут, разделы, потолок=None):
    # Модель с низким потолком вывода не вместит многораздельный развёрнутый ответ:
    # замерено, perplexity (потолок 8000) на вопросах из 4-5 разделов раз за разом
    # приходил неполным или упирался в потолок. Ей — прямая инструкция ужаться,
    # иначе она рассыпается на первом же разделе и тратит деньги впустую.
    сист = система
    if потолок and потолок <= 8000 and len(разделы) >= 3:
        тесно = (f"ЖЁСТКОЕ ОГРАНИЧЕНИЕ: твой максимум ответа — {потолок} токенов, "
                 f"а разделов {len(разделы)}. Раскрой КАЖДЫЙ раздел, но сжато: "
                 f"по существу, без вступлений, повторов и воды. Лучше короткий "
                 f"ответ на все разделы, чем подробный на половину.")
        сист = (сист + "\n\n" + тесно) if сист else тесно
    messages = ([{"role": "system", "content": сист}] if сист else []) \
             + [{"role": "user", "content": вопрос}]
    итог = {"модель": алиас, "id": model, "стоимость": 0.0, "события": []}
    t0 = time.time()
    # Сразу максимум из возможного: max_tokens — потолок, а не счёт, платится
    # только сгенерированное. Скупой стартовый лимит и порождает обрывы.
    текущий = min(лимит, потолок) if потолок else лимит
    итог["потолок_модели"] = потолок
    накоплено = ""

    for шаг in range(ДОПИСОК + 1):
        d = сеть(key, model, messages, текущий, таймаут)

        if d.get("error"):                       # HTTP 200 с телом ошибки тоже сюда
            итог["события"].append(f"ошибка: {str(d['error'])[:120]}")
            if шаг == 0:
                continue
            итог.update(статус="выпал", причина=str(d["error"])[:160])
            break
        if not d.get("choices"):
            итог["события"].append("нет choices")
            итог.update(статус="выпал", причина="пустой ответ провайдера")
            break
        # Провайдер может молча подставить другую модель. Тогда весь смысл совета
        # (сравнение разных школ) рушится, а заметить это иначе нельзя.
        # ВСЕ попытки, а не последняя: при дописках оценка копит стоимость каждой,
        # и сверять её с ценой одной генерации — сравнивать разные вещи.
        if d.get("id"): итог.setdefault("gen_ids", []).append(d["id"])
        факт = d.get("model") or ""
        итог["факт_модель"] = факт
        if факт and model.split("/")[-1] not in факт:
            итог["подмена"] = факт
            итог["события"].append(f"ПОДМЕНА: просили {model}, ответил {факт}")

        ch = d["choices"][0]
        u = d.get("usage") or {}
        кусок = текст_из(ch)
        итог["стоимость"] += (u.get("prompt_tokens", 0) * ц_вх
                              + u.get("completion_tokens", 0) * ц_вых) / 1e6
        if шаг == 0:
            итог["стоимость"] += ПОИСК_НАДБАВКА.get(алиас, 0.0)
        накоплено += кусок
        беда = неполон(кусок, ch, u, текущий)
        итог["события"].append(
            f"лимит={текущий} fr={ch.get('finish_reason')}/{ch.get('native_finish_reason')} "
            f"вых={u.get('completion_tokens')} думал={(u.get('completion_tokens_details') or {}).get('reasoning_tokens',0)}"
            + (f" → {беда}" if беда else " → ок"))

        if not беда:
            итог.update(статус="ок", текст=накоплено)
            break

        if ch.get("finish_reason") == "content_filter":
            итог.update(статус="фильтр", текст=накоплено, причина="зарезал фильтр")
            break

        # ДОПИСЫВАЕМ, а не перезапрашиваем: перезапуск заново оплачивает размышления
        # и заново проходит ту же ветку. Сокращать ответ нельзя — нужна полнота.
        новый = max(текущий * 2, ПОЛ_ЛИМИТА)
        if потолок: новый = min(новый, потолок)
        if новый <= текущий:
            итог.update(статус="потолок", текст=накоплено,
                        причина=f"упёрлись в физический потолок модели ({потолок} токенов) — "
                                f"наращивать бесполезно, дробить вопрос")
            break
        текущий = новый
        # ИСКЛЮЧЕНИЕ: поисковые модели дописку игнорируют — на каждый запрос они идут
        # в веб заново и начинают ответ с нуля. Замерено: perplexity не дописался за
        # 3 продолжения, сжёг $0.34. Им — чистый перезапрос с большим лимитом.
        if алиас in ПОИСК_НАДБАВКА:
            накоплено = ""
            messages = [m for m in messages if m["role"] != "assistant"]
            continue
        if накоплено.strip():
            messages = messages[:len(messages) - (1 if messages[-1]["role"] == "assistant" else 0)]
            messages = [m for m in messages if m["role"] != "assistant"] + [
                {"role": "assistant", "content": накоплено},
                {"role": "user", "content": "Продолжай ровно с места обрыва. "
                                            "Без повторов, без вводных, без извинений."}]
    else:
        итог.update(статус="обрыв", текст=накоплено,
                    причина=f"не дописался за {ДОПИСОК} продолжений")

    итог.setdefault("статус", "обрыв")
    итог.setdefault("текст", накоплено)

    # Семантическая полнота: ответил ли на все пункты. finish_reason про это не знает.
    if итог["статус"] == "ок" and разделы:
        нет = [s for s in разделы if s not in итог["текст"]]
        if нет:
            итог.update(статус="неполный", причина="не раскрыты пункты: " + ", ".join(нет))
    if итог["статус"] == "ок" and ОТКАЗ.match(итог["текст"]):
        итог.update(статус="отказ", причина="модель уклонилась от ответа")

    итог["сек"] = round(time.time() - t0, 1)
    итог["стоимость"] = round(итог["стоимость"], 5)
    return итог


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--вопрос", required=True, help="файл с вопросом, или '-' для stdin")
    ap.add_argument("--модели", default="", help="алиасы через запятую; пусто = весь совет")
    ap.add_argument("--разделы", default="", help="через запятую: маркеры, которые ОБЯЗАНЫ быть в ответе")
    ap.add_argument("--брифы", action="store_true", help="дать каждой школе свою задачу (реком.)")
    ap.add_argument("--роль", choices=sorted(РОЛИ), help="одна роль всем (осторожно: убивает разнообразие)")
    ap.add_argument("--система", default="")
    ap.add_argument("--тяжёлый", action="store_true")
    ap.add_argument("--без-фактчека", action="store_true", help="убрать Perplexity — только осознанно")
    ap.add_argument("--лимит", type=int, default=32000, help="потолок; режется максимумом модели")
    ap.add_argument("--таймаут", type=int, default=600)
    ap.add_argument("--потолок", type=float, default=0.50, help="предупредить, если заход дороже, $")
    ap.add_argument("--вывод", default="")
    a = ap.parse_args()

    вопрос = sys.stdin.read() if a.вопрос == "-" else open(a.вопрос, encoding="utf-8").read()
    разделы = [s.strip() for s in a.разделы.split(",") if s.strip()]

    доступно = dict(СОВЕТ, **РЕЗЕРВ, **(ТЯЖЁЛЫЙ if a.тяжёлый else {}))
    if a.модели:
        имена = [x.strip() for x in a.модели.split(",") if x.strip()]
        плохие = [x for x in имена if x not in доступно]
        if плохие:
            sys.exit(f"Неизвестные: {', '.join(плохие)}. Есть: {', '.join(sorted(доступно))}")
    else:
        имена = list(СОВЕТ) + (list(ТЯЖЁЛЫЙ) if a.тяжёлый else [])   # РЕЗЕРВ — только явно

    # Perplexity — инвариант: у остальных знания с обрывом по дате обучения.
    if "perplexity" not in имена and not a.без_фактчека:
        имена.append("perplexity")
        print("[+] добавил perplexity: без него совет обсуждает позавчерашний мир")

    key = ключ()
    лимиты = потолки(key)
    было = баланс(key)
    тесные = [n for n in имена
              if (лимиты.get(доступно[n][0]) or 10**9) <= 8000 and len(разделы) >= 3]
    if тесные:
        print(f"⚠️  {', '.join(тесные)}: потолок ответа ({лимиты.get(доступно[тесные[0]][0])}) "
              f"мал для {len(разделы)} разделов — даю инструкцию отвечать сжато. "
              f"Нужен подробный разбор от них — дробить вопрос на два захода.")
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(имена)) as ex:
        futs = [ex.submit(спросить, key, n, *доступно[n], вопрос,
                          a.система or (РОЛИ[БРИФ_ПО_УМОЛЧАНИЮ[n]] if a.брифы and n in БРИФ_ПО_УМОЛЧАНИЮ
                                        else РОЛИ[a.роль] if a.роль else ""),
                          a.лимит, a.таймаут, разделы, лимиты.get(доступно[n][0])) for n in имена]
        res = [f.result() for f in concurrent.futures.as_completed(futs)]
    res.sort(key=lambda r: имена.index(r["модель"]))

    # Транспорт режется — сказать один раз внятно, а не шесть раз сырым 403
    if all(r.get("причина", "").startswith("ТРАНСПОРТ ЗАКРЫТ") for r in res if r["статус"] == "выпал") \
       and any(r["статус"] == "выпал" for r in res):
        print("\n🚫 Прямой путь в OpenRouter закрыт с этой машины. Нужен прокси.")

    print(f"\n{'МОДЕЛЬ':<11} {'статус':<10} {'сек':>6} {'$':>8}  знаков / причина")
    print("-" * 74)
    for r in res:
        хвост = f"{len(r.get('текст','')):>6}" if r["статус"] == "ок" else r.get("причина", "")[:38]
        print(f"{r['модель']:<11} {r['статус']:<10} {r['сек']:>6} {r['стоимость']:>8.5f}  {хвост}")
        if r.get("подмена"):
            print(f"{'':<11} ⚠️  ПОДМЕНА: просили {r['id']}, ответил {r['подмена']}")
    итого = sum(r["стоимость"] for r in res)
    плохо = [r["модель"] for r in res if r["статус"] != "ок"]
    print("-" * 74)
    print(f"ОЦЕНКА: ${итого:.4f}" + (f"   ПРОБЛЕМЫ: {', '.join(плохо)}" if плохо else "   все полные"))

    # Факт против оценки — по стоимости каждой генерации у провайдера.
    факты, всего_ген = [], 0
    for r in res:
        for gid in r.get("gen_ids", []):
            всего_ген += 1
            f = факт_цена(key, gid)
            if f is not None: факты.append(f)
    if факты:
        сумма = sum(факты)
        print(f"ФАКТ у провайдера: ${сумма:.4f}  (по {len(факты)} из {всего_ген} генераций)")
        if len(факты) < всего_ген:
            print(f"   ⚠️ {всего_ген - len(факты)} генераций не отдали цену — сверка неполная, "
                  f"расхождение ниже может быть мнимым")
        elif итого > 0 and not (0.7 <= сумма / итого <= 1.4):
            print(f"⚠️  оценка мимо в {сумма/итого:.1f}× — сверить прайс с каталогом "
                  f"(GET /models) и надбавку за поиск")
    if было is not None:
        print(f"Остаток на ключе: ${было:.2f} (до захода; баланс обновляется с задержкой)")
    if итого > a.потолок:
        print(f"⚠️  дороже потолка ${a.потолок:.2f} — сказать владельцу")

    подменены = [r for r in res if r.get("подмена")]
    if подменены:
        print(f"⚠️  ПОДМЕНА У {len(подменены)} МОДЕЛЕЙ — сравнение школ недостоверно, сказать владельцу")

    if a.вывод:
        json.dump(res, open(a.вывод, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(f"Ответы: {a.вывод}")
    else:
        for r in res:
            if r.get("текст"):
                print(f"\n{'='*74}\n{r['модель'].upper()}  [{r['статус']}]\n{'='*74}\n{r['текст']}")


if __name__ == "__main__":
    main()
