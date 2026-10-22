#!/usr/bin/env python3
"""Проверка доступов для раздела «Метрика» в админке – без вывода секретов.

Что проверяет:
  1. токен Яндекса (файл со строкой YANDEX_METRIKA_TOKEN=…): права файла,
     доступ к счётчику Метрики, визиты за 28 дней (только люди);
  2. ключ сервисного аккаунта Google: читается ли, есть ли доступ к ресурсу
     Search Console и с каким уровнем;
  3. доступность API Яндекс Вебмастера по сети.

Запуск:
  python3 check_access.py --counter 98718529 --token-file ~/.config/yandex-metrika/metrika.env \
      --gsc-key ~/.config/gsc/teyes-sa.json --gsc-site sc-domain:example.ru

Токен и ключ никогда не печатаются: только «есть / нет / код ответа».
Нужен openssl (подпись JWT для Google). На маке с python.org может не быть
корневых сертификатов – скрипт берёт certifi, если он установлен.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import pathlib
import ssl
import stat
import subprocess
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request

try:
    import certifi
    CTX = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    CTX = ssl.create_default_context()


def http(url, data=None, headers=None, method=None, timeout=20):
    req = urllib.request.Request(url, data=data, headers=headers or {}, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=CTX) as r:
            return r.status, r.read().decode("utf-8", "ignore")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "ignore")
    except (urllib.error.URLError, OSError) as e:
        return 0, f"{type(e).__name__}: {getattr(e, 'reason', e)}"


def read_token(path: pathlib.Path) -> str:
    for line in path.read_text(encoding="utf-8").splitlines():
        key, _, val = line.partition("=")
        if key.strip() == "YANDEX_METRIKA_TOKEN" and val.strip():
            return val.strip().strip("'\"")
    return ""


def check_yandex(counter: int, token_file: str) -> None:
    path = pathlib.Path(os.path.expanduser(token_file))
    if not path.is_file():
        print(f"Яндекс: файла токена нет ({path})")
        return
    mode = stat.S_IMODE(path.stat().st_mode)
    print(f"Яндекс: файл токена есть, права {oct(mode)}" + ("" if mode == 0o600 else " – сделать chmod 600"))
    tok = read_token(path)
    if not tok:
        print("Яндекс: в файле нет строки YANDEX_METRIKA_TOKEN=")
        return
    h = {"Authorization": f"OAuth {tok}"}
    code, text = http(f"https://api-metrika.yandex.net/management/v1/counter/{counter}", headers=h)
    site = json.loads(text).get("counter", {}).get("site") if code == 200 else None
    print(f"Метрика: счётчик {counter} – ответ {code}" + (f", сайт {site}" if site else ""))
    q = urllib.parse.urlencode({"ids": counter, "metrics": "ym:s:visits", "date1": "28daysAgo",
                                "date2": "yesterday", "filters": "ym:s:isRobot=='No'"})
    code, text = http(f"https://api-metrika.yandex.net/stat/v1/data?{q}", headers=h)
    if code == 200:
        print(f"Метрика: визиты за 28 дней, только люди – {json.loads(text).get('totals')}")
    else:
        print(f"Метрика: отчёт – ответ {code}")
    code, _ = http("https://api.webmaster.yandex.net/v4/user", headers=h, timeout=15)
    print(f"Вебмастер: ответ {code}" + (" (сеть не достучалась – не про токен)" if code == 0 else ""))


def check_google(key_file: str, site: str) -> None:
    path = pathlib.Path(os.path.expanduser(key_file))
    if not path.is_file():
        print(f"Google: ключа нет ({path})")
        return
    try:
        sa = json.loads(path.read_text(encoding="utf-8"))
        email, key = sa["client_email"], sa["private_key"]
    except (OSError, ValueError, KeyError):
        print("Google: ключ не читается")
        return
    print(f"Google: сервисный аккаунт {email}")
    b64 = lambda b: base64.urlsafe_b64encode(b).rstrip(b"=")
    now = int(time.time())
    msg = b64(b'{"alg":"RS256","typ":"JWT"}') + b"." + b64(json.dumps({
        "iss": email, "scope": "https://www.googleapis.com/auth/webmasters.readonly",
        "aud": "https://oauth2.googleapis.com/token", "iat": now, "exp": now + 3600}).encode())
    k = tempfile.NamedTemporaryFile("w", delete=False)
    try:
        with k:
            k.write(key)
        sig = subprocess.run(["openssl", "dgst", "-sha256", "-sign", k.name], input=msg,
                             capture_output=True, check=True).stdout
    except (OSError, subprocess.CalledProcessError):
        print("Google: не удалось подписать запрос (нужен openssl)")
        return
    finally:
        os.unlink(k.name)
    data = urllib.parse.urlencode({"grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
                                   "assertion": (msg + b"." + b64(sig)).decode()}).encode()
    code, text = http("https://oauth2.googleapis.com/token", data)
    tok = json.loads(text).get("access_token") if code == 200 else None
    if not tok:
        print(f"Google: токен не выдан, ответ {code}")
        return
    code, text = http("https://www.googleapis.com/webmasters/v3/sites", headers={"Authorization": f"Bearer {tok}"})
    sites = {s["siteUrl"]: s["permissionLevel"] for s in json.loads(text).get("siteEntry", [])} if code == 200 else {}
    level = sites.get(site)
    print(f"Search Console: {site} – " + (f"доступ {level}" if level else
          "доступа нет: добавить аккаунт в Настройки → Пользователи и разрешения"))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--counter", type=int, required=True, help="номер счётчика Метрики")
    ap.add_argument("--token-file", default="~/.config/yandex-metrika/metrika.env")
    ap.add_argument("--gsc-key", default="~/.config/gsc/teyes-sa.json")
    ap.add_argument("--gsc-site", help="ресурс Search Console, например sc-domain:example.ru")
    a = ap.parse_args()
    check_yandex(a.counter, a.token_file)
    if a.gsc_site:
        check_google(a.gsc_key, a.gsc_site)


if __name__ == "__main__":
    main()
