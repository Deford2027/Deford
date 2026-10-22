---
name: scrapecreators
description: Справочник Scrape Creators API — все 183 ручки проверены боем, 178 работают. Сбор данных из TikTok, Instagram, YouTube, Telegram, Reddit, Threads, Pinterest, Twitter, LinkedIn, рекламных библиотек. Использовать, когда нужно что-то спарсить, выбрать эндпоинт, узнать точные параметры и цену в кредитах, сэкономить на кэше или понять, почему запрос не работает.
---

# Scrape Creators — как пользоваться

Три справочника рядом:
- `reference/все-ручки.md` — **таблица по всем 183 ручкам** (замер 14.09.2026:
  178 работают; проверялось вызовом каждой — повторить, если ручка отвалилась):
  статус, цена, что вернула,
  рабочие параметры
- `reference/проверено.md` — итоги прогона, находки, что не поддалось и почему
- `reference/эндпоинты.md` — реестр по площадкам из документации
- `reference/openapi.json` — **полная спека вендора**: точные параметры, enum'ы и примеры
  для каждой ручки. Грепать локально, это быстрее любых догадок

**Проверены боем ВСЕ 183 ручки спеки: 178 работают.**

## Базовое

```bash
curl "https://api.scrapecreators.com/v1/tiktok/profile?handle=garyvee" \
  -H "x-api-key: $SC_KEY"
```

- Ключ **только** в заголовке `x-api-key`.
  ⚠️ **Никогда не писать ключ в код, в скилл или в лог.**

### 🔑 Ключ лежит в ДВУХ местах — они должны совпадать

```
~/.claude/secrets/scrapecreators.key     ← берут скиллы
<проект>/.env → SCRAPECREATORS_API_KEY   ← берёт прод-сбор
```

Это **разные аккаунты с разными балансами**, если содержимое разойдётся. Тогда часть
расхода уедет на один счёт, часть на другой, и любые подсчёты бюджета станут враньём.
**Перед работой сверить оба:**

```bash
diff <(cat ~/.claude/secrets/scrapecreators.key) \
     <(grep SCRAPECREATORS_API_KEY <проект>/.env | cut -d= -f2) && echo "совпадают"
```
- Официальных лимитов нет, рекомендация вендора — до 500 одновременных запросов.
- Коды: 200 · 400 неверные параметры · 401 ключ · 402 кончились кредиты · 404 не найдено.

## 💰 Деньги: три правила, которые экономят больше всего

**1. Почти всё стоит РОВНО 1 кредит.** Проверено на всех 183 ручках.
Исключения: `/v1/tiktok/user/audience` — **26 кредитов**, `/v1/find-social-profiles` — **10 кредитов**.

**2. 🔑 Цена приходит В САМОМ ОТВЕТЕ.** У каждого успешного ответа есть поля
`credits_charged` и `credits_remaining` — проверено на всех ручках. Не надо ходить
в историю и тем более считать разницу баланса:

```bash
curl -s "https://api.scrapecreators.com/v1/youtube/video?url=..." -H "x-api-key: $K" \
  | python3 -c "import json,sys;d=json.load(sys.stdin);print(d.get('credits_charged'), d.get('cached'))"
```

**3. Ошибка почти всегда бесплатна — но форм ошибки три, и парсер должен пережить все:**

| Что случилось | Код | Тело | `credits_charged` |
|---|---|---|---|
| Пропущен обязательный параметр | 400 | JSON `{"success":false,...}` | `0` |
| Кривое значение параметра | 400 | JSON `{"success":false,...}` | `0` |
| Несуществующий путь | 404 | **`Not Found`, это не JSON** | поля нет |

⚠️ На третьей форме `json.loads` выбросит исключение. Разбирать тело только через
try/except, и **судить о цене по полю лишь тогда, когда оно есть** — иначе
`get-api-usage`. Подбирать параметры перебором безопасно: за ошибки не списывают.

**4. 🔑 `cache_max_age` делает повторы БЕСПЛАТНЫМИ.**

```
?handle=garyvee&cache_max_age=30d      значения: 1d · 3d · 7d · 14d · 30d
```

Ответ из кэша содержит `"cached": true` и `cached_at`, а `credits_charged` равен нулю.

⚠️ **Поддерживают НЕ все ручки, и закономерность обманчива.** Я сначала записал правило
«кэшируется профильное, не кэшируется ленточное» — оно **неверно**: транскрипт YouTube
кэшируется, а транскрипт TikTok нет. Проверять надо поручно. Замерено двумя вызовами
подряд:

| Ручка | Кэш |
|---|---|
| `/v1/tiktok/profile` | ✅ |
| `/v2/tiktok/video` | ✅ |
| `/v1/instagram/profile` | ✅ |
| `/v1/youtube/video` | ✅ |
| `/v1/youtube/video/transcript` | ✅ ← исключение из «правила» |
| `/v1/reddit/subreddit` | ✅ |
| `/v1/telegram/channel/posts` | ✅ |
| `/v3/tiktok/profile/videos` | ❌ |
| `/v1/tiktok/search/keyword` · `/search/hashtag` | ❌ |
| `/v1/tiktok/video/transcript` | ❌ ← а этот НЕ кэшируется |
| `/v1/tiktok/get-trending-feed` | ❌ |
| `/v1/instagram/user/reels` · `/v2/instagram/reels/search` | ❌ |
| `/v1/youtube/channel-videos` · `/v1/youtube/search` | ❌ |

**Проверить любую другую ручку — два вызова подряд:** если у второго
`credits_charged: 0`, кэш есть. Результат дописать в эту таблицу.

⚠️ **Кэш ОБЩИЙ на стороне сервиса:** ноль списывается даже на первом запросе, если этот
handle недавно тянул кто угодно. На 10 случайных аккаунтах из нашей базы вышло
**10 из 10 бесплатно** с окном 30d.

⚠️ **Окно выбирать по задаче.** Замер на свежих аккаунтах: `1d` — попаданий 0 из 7,
`3d` — 1 из 7, `7d` — 4 из 7. Большое окно экономит сильнее, но отдаёт старые данные:
для поиска новых аутлайеров это значит пропустить свежие посты. Для профилей, где важен
только baseline, берите `30d`; где нужна свежая лента — не кэшируйте вовсе.

## 📊 Куда смотреть, сколько потрачено

| Ручка | Что даёт |
|---|---|
| `/v1/account/credit-balance` | остаток, поле `creditCount` |
| `/v1/account/get-api-usage` | **история с `credits` по каждому запросу** — точный источник |
| `/v1/account/get-daily-usage-count` | по дням: `total_credits`, `request_count` |
| `/v1/account/get-most-used-routes` | агрегат по ручкам |

⚠️ **Стоимость НЕ мерить разницей баланса** — он обновляется асинхронно и врёт.
Я так намерил «10 кредитов» там, где реально был 1. Мерить только по `get-api-usage`.

## Что брать под задачу

| Задача | Эндпоинт |
|---|---|
| Ролики по теме | `/v1/tiktok/search/keyword` · `/v1/youtube/search` |
| Лучшее у автора за всё время | `/v3/tiktok/profile/videos?sort_by=popular` |
| Последнее у автора | `/v3/tiktok/profile/videos` (по умолчанию) |
| Лента рекомендаций | `/v1/tiktok/get-trending-feed?region=US` |
| По хэштегу | `/v1/tiktok/search/hashtag` · `/v1/instagram/search/hashtag` |
| Найти авторов ниши | `/v1/tiktok/search/users` · `/v1/instagram/search/profiles` |
| Метрики одного ролика | `/v2/tiktok/video` (сохранения, просмотры, репосты) |
| Текст ролика | `/v1/tiktok/video/transcript` · `/v1/youtube/video/transcript` |
| Instagram: посты автора | `/v1/instagram/profile` (12 постов **с просмотрами**) |
| Instagram: только рилсы | `/v1/instagram/user/reels` |
| Instagram: вся история | `/v2/instagram/user/posts` (курсор `next_max_id`) |
| **Тексты с метриками** | `/v1/telegram/channel/posts` — 20 постов, кэшируется |
| Обсуждения и боли | `/v1/reddit/subreddit` · `/v1/reddit/search` |
| Спрос (подсказки) | `/v1/tiktok/search/suggestions` · `/v1/youtube/search/typeahead` |
| Визуальные референсы | `/v1/pinterest/search` |
| **Реклама конкурентов** | `/v1/facebook/adLibrary/search/ads` · `/v1/tiktok/ad-library/search` |
| Поисковая выдача | `/v1/google/search` |
| Реклама внутри ролика | `/v1/youtube/video/sponsors` — отдаёт `suspectedSponsors` и `sponsorDetection`, годится для чистки рекламных вставок |

## Готовые вызовы — проверены, копируются как есть

Спека содержит примеры не для всех ручек (13 из 124 без них), поэтому ходовые
зафиксированы здесь. Все выполнялись и возвращали 200.

```bash
K=$(cat ~/.claude/secrets/scrapecreators.key)
A="https://api.scrapecreators.com"

# ── поиск роликов по теме
curl -s "$A/v1/tiktok/search/keyword?query=deep+work"        -H "x-api-key: $K"
curl -s "$A/v1/youtube/search?query=deep+work"               -H "x-api-key: $K"
curl -s "$A/v1/tiktok/search/hashtag?hashtag=focus"          -H "x-api-key: $K"

# ── автор: лучшее за всё время против последнего
curl -s "$A/v3/tiktok/profile/videos?handle=garyvee&sort_by=popular" -H "x-api-key: $K"
curl -s "$A/v1/tiktok/profile?handle=garyvee&cache_max_age=30d"      -H "x-api-key: $K"

# ── метрики и текст одного ролика
curl -s "$A/v2/tiktok/video?url=<ссылка>&cache_max_age=30d"  -H "x-api-key: $K"
curl -s "$A/v1/tiktok/video/transcript?url=<ссылка>"         -H "x-api-key: $K"
curl -s "$A/v1/youtube/video/transcript?url=<ссылка>&cache_max_age=30d" -H "x-api-key: $K"

# ── Instagram
curl -s "$A/v1/instagram/profile?handle=garyvee&cache_max_age=30d"   -H "x-api-key: $K"
curl -s "$A/v1/instagram/user/reels?handle=garyvee"                  -H "x-api-key: $K"
curl -s "$A/v2/instagram/reels/search?query=marketing+tips"          -H "x-api-key: $K"

# ── звуковые тренды: ТОЛЬКО clipId, и в спеке для него примера НЕТ
curl -s "$A/v1/tiktok/song?clipId=7439295283975702544"        -H "x-api-key: $K"
curl -s "$A/v1/tiktok/song/videos?clipId=7439295283975702544" -H "x-api-key: $K"

# ── обсуждения и спрос
curl -s "$A/v1/reddit/subreddit?subreddit=productivity&cache_max_age=7d" -H "x-api-key: $K"
curl -s "$A/v1/tiktok/search/suggestions?query=morning+routine"          -H "x-api-key: $K"
curl -s "$A/v1/youtube/search/typeahead?query=how+to"                    -H "x-api-key: $K"

# ── реклама конкурентов
curl -s "$A/v1/facebook/adLibrary/search/ads?query=fitness" -H "x-api-key: $K"
curl -s "$A/v1/linkedin/ads/search?keyword=marketing"       -H "x-api-key: $K"
```

⚠️ **Не полагаться слепо на `example` из спеки** — у части ручек он пустой, и подстановка
`None` даёт 404, который легко спутать с «ручка не работает». Порядок: сначала таблица
выше, потом `example` из спеки, потом документация ручки, потом цепочка из соседней.

## ⚠️ Грабли

- **Версии путей разные** — `/v1`, `/v2`, `/v3`. Клиент обязан брать путь как есть,
  а не подставлять базовый `/v1`. На этом мы получали ложные 404.
- **Instagram меняет имена полей.** Были `GraphVideo`/`video_view_count`, стали
  `XDTGraphVideo`/`video_play_count`. Парсер молча клал всё в `other` и терял просмотры.
  Раз в пару месяцев сверять сырой ответ с тем, что читает код.
- **Не фильтровать по полю, которого в источнике может не быть.** Поиск аккаунтов
  Instagram не отдаёт подписчиков — условие «меньше 3000» отсекало 100%.
- **«Эндпоинта нет» — вывод, который надо перепроверять.** Мы месяцами держали в памяти
  «баланс кредитов недоступен», потому что угадывали адреса. Реальный нашёлся в доках.
- **Мёртвые аккаунты ломают метрику пробития.** У профиля с почти нулевым вовлечением
  медиана стремится к нулю, и один залетевший пост даёт ×8000. Порог: медиана ≥50.

## Зависимые ручки решаются цепочкой

Ручку вида «детали по id» бесполезно дёргать наугад — она вернёт 400. Сначала взять id
из соседней работающей: объявление из поиска объявлений, пост из ленты профиля,
плейлист из списка плейлистов. Так добиты 4 ручки, которые перебор параметров не брал.

## Не угадывать параметры — брать из спеки

Имена параметров у вендора непредсказуемы: у `song` это `clipId`, а не `songId`;
у `youtube/playlist` — `playlist_id` в snake_case; `detect-age-gender` хочет ссылку
на профиль, а не на фото. Перебором это ловится долго.

```bash
python3 -c "import json;s=json.load(open('reference/openapi.json'));\
p=s['paths']['/v1/tiktok/song']['get'];print([(x['name'],x.get('required'),\
(x.get('schema') or {}).get('example')) for x in p.get('parameters',[])])"
```

## Проверка перед тем, как строить сбор

1. Дёрнуть ручку руками с минимальными параметрами — ошибки бесплатны.
2. Посмотреть, что реально в ответе: какие поля, сколько элементов.
3. Только потом писать парсер — и сверять имена полей с сырым ответом, а не с памятью.
