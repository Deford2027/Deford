#!/usr/bin/env bash
# Обращение к API SEO-админки от имени пользователя claude (пароль – в netrc, не в командной строке).
#   api.sh GET  /api/status
#   api.sh POST /api/sync/webmaster '{}'
#   api.sh POST /api/estimates '{"kind":"demand","selection":{"mode":"priority"}}'
# Адрес: TEYES_SEO_ADMIN_URL (по умолчанию https://admin.teyes-sibir.ru).
# Пока DNS admin.teyes-sibir.ru не готов – туннель (см. SKILL.md) и TEYES_SEO_ADMIN_URL=http://127.0.0.1:18080.
set -euo pipefail
method="${1:?метод}"; path="${2:?путь}"; body="${3:-}"
base="${TEYES_SEO_ADMIN_URL:-https://admin.teyes-sibir.ru}"
netrc="$HOME/.config/teyes-seo-admin/netrc"
host="$(python3 -c "import sys, urllib.parse; print(urllib.parse.urlparse(sys.argv[1]).hostname)" "$base")"
# netrc привязан к имени хоста; для туннеля подставляем ту же учётку под 127.0.0.1 во временный файл.
# Учётка уходит только на admin.teyes-sibir.ru или на локальный туннель – никуда больше.
case "$host" in
  admin.teyes-sibir.ru|127.0.0.1|localhost) ;;
  *) echo "Отказ: адрес $base – не админка и не локальный туннель" >&2; exit 2 ;;
esac
if [ "$host" != "admin.teyes-sibir.ru" ]; then
  tmp="$(mktemp)"; trap 'rm -f "$tmp"' EXIT; chmod 600 "$tmp"
  sed "s/^machine admin.teyes-sibir.ru /machine $host /" "$netrc" > "$tmp"; netrc="$tmp"
fi
args=(-sS --max-time 60 --netrc-file "$netrc" -H "X-Admin-Client: teyes-seo-sbor" -X "$method")
[ -n "$body" ] && args+=(-H "Content-Type: application/json" --data "$body")
curl "${args[@]}" -w '\n' "$base$path"
