#!/bin/bash
# Пересобирает reference/данные.md из живых библиотек на сервере.
# Запускать раз в пару недель — библиотеки пополняются каждым прогоном.
set -e
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TMP="$(mktemp)"
ssh -o ConnectTimeout=60 root@45.12.73.217 \
  'cd /opt/startup-trend-watcher && docker compose exec -T app python export_skill_ref.py' > "$TMP"
if [ ! -s "$TMP" ] || ! grep -q "Базовая линия" "$TMP"; then
  echo "❌ Ответ пустой или битый — справочник НЕ тронут (старый лучше пустого)"
  rm -f "$TMP"; exit 1
fi
mv "$TMP" "$DIR/reference/данные.md"
echo "✅ Справочник обновлён: $(wc -l < "$DIR/reference/данные.md") строк"
