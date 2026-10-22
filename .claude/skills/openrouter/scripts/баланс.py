#!/usr/bin/env python3
"""Остаток на ключе OpenRouter. Показывать владельцу при каждом обращении к скиллу."""
import json, os, urllib.request

k = os.path.expanduser("~/.claude/secrets/openrouter.key")
key = open(k).read().strip() if os.path.exists(k) else os.environ.get("OPENROUTER_API_KEY", "")
if not key:
    raise SystemExit("нет ключа OpenRouter")
req = urllib.request.Request("https://openrouter.ai/api/v1/credits",
                             headers={"Authorization": "Bearer " + key})
d = (json.loads(urllib.request.urlopen(req, timeout=30).read()) or {}).get("data") or {}
лимит = float(d.get("total_credits", 0))
трата = float(d.get("total_usage", 0))
print(f"OpenRouter: ${лимит - трата:.2f} осталось  (пополнено ${лимит:.2f}, потрачено ${трата:.2f})")
