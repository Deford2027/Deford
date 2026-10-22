#!/usr/bin/env python3
"""Остаток кредитов Segmind. Показывать владельцу при каждом обращении к скиллу.

Эндпоинт неочевидный: /v1/get-user-credits. Обычные догадки (v1/credits,
v1/balance, v1/user) отвечают 404 «Model information not found» — API принимает
любой путь за имя модели. Найдено в рабочем коде VideoOS.
"""
import json, os, urllib.request

k = os.path.expanduser("~/.claude/secrets/segmind.key")
key = open(k).read().strip() if os.path.exists(k) else os.environ.get("SEGMIND_API_KEY", "")
if not key:
    raise SystemExit("нет ключа Segmind")
req = urllib.request.Request("https://api.segmind.com/v1/get-user-credits",
                             headers={"x-api-key": key})
d = json.loads(urllib.request.urlopen(req, timeout=30).read()) or {}
кред = float(d.get("credits") or 0)
своб = float(d.get("free-credits") or 0)
print(f"Segmind: ${кред:.2f} кредитов" + (f" + ${своб:.2f} бесплатных" if своб else ""))
if кред < 1:
    print("  ⚠️ мало: серьёзной задачи не хватит. Пополнение — cloud.segmind.com/billing")
