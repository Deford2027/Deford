#!/bin/bash
# Набор А — проверка срабатывания описания скилла.
#
# ВАЖНО: запускать в СВОЁМ терминале, не через Claude Code.
# Вложенный `claude -p` из песочницы отдаёт «Not logged in» — доступа к связке ключей нет.
# Проверено 2026-09-11 на 2.1.173.
#
# Каждый вызов `claude -p` — отдельная свежая сессия, организовывать чистоту не нужно.
#
# Осторожно: фразы, поднимающие codex по-настоящему, доходят до реального вызова
# и тратят окно подписки ChatGPT. Для регулярного прогона держать отрицательные
# фразы и одну-две положительных, а не весь список.

cd /tmp || exit 1
while IFS='|' read -r phrase expected; do
  [ -z "$phrase" ] && continue
  # < /dev/null обязателен, иначе claude съест список фраз из heredoc
  out=$(claude -p "$phrase" --output-format json < /dev/null 2>&1)
  sid=$(printf '%s' "$out" | python3 -c "import sys,json;print(json.load(sys.stdin).get('session_id',''))" 2>/dev/null)
  tr=$(find ~/.claude/projects -name "$sid.jsonl" 2>/dev/null | head -1)
  got=$(python3 - "$tr" <<'PY'
import json,sys
try: f=open(sys.argv[1],encoding="utf-8")
except Exception: print("—"); raise SystemExit
s=[]
for line in f:
    try: d=json.loads(line)
    except Exception: continue
    c=d.get("message",{}).get("content")
    if isinstance(c,list):
        for b in c:
            if isinstance(b,dict) and b.get("type")=="tool_use" and b.get("name")=="Skill":
                s.append(b.get("input",{}).get("skill"))
print(",".join(s) if s else "—")
PY
)
  [ "$got" = "$expected" ] && v="OK  " || v="FAIL"
  printf "%s %-55s ждали: %-18s подняли: %s\n" "$v" "$phrase" "$expected" "$got"
done <<'PHRASES'
спроси кодекса, что не так с этим кодом|codex
пусть кодекс нарисует логотип по этим двум референсам|codex
отдай кодексу этот PDF, пусть сравнит с прошлой версией|codex
опроси несколько нейросетей, что они думают про эту идею|совет-нейросетей
какая модель дешевле для длинного текста|openrouter
сгенерируй видео по этому кадру|segmind
что говорит кодекс об административной ответственности|—
PHRASES
