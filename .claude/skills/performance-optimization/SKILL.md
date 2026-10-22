---
name: performance-optimization
description: "Диагностируй и исправляй измеренную проблему скорости, latency, throughput, памяти, bundle/rendering, запросов или очередей. Не оптимизируй по догадке, не применяй фиксированные web-бюджеты к любому продукту и не меняй архитектуру без baseline и профиля bottleneck."
metadata:
  version: 1.0.0-owner-adapted
  upstream_url: https://github.com/addyosmani/agent-skills/tree/6ca0cd7db39b41b1c37e26d335c507ee92382c6d/skills/performance-optimization
  upstream_commit: 6ca0cd7db39b41b1c37e26d335c507ee92382c6d
  upstream_sha256: 00694d0c69bbde674d0e39de24052d90afea32d9fef9553eaee21a50a7e9b8cf
  adapted: "2026-09-10"
---

# Оптимизация производительности

Ты находишь фактическое узкое место, меняешь одну причинную переменную и доказываешь выигрыш сопоставимым измерением.

## Порядок

1. Зафиксируй пользовательский/операционный симптом, workload, среду, версии, dataset, concurrency и метрику. Выбери целевой budget из SLA/SLO, field data или требований владельца; числа upstream/Web Vitals — ориентиры для подходящих web-задач, не универсальный контракт.
2. Получи baseline несколькими сопоставимыми прогонами и сохрани распределение: median и p95/p99, errors, resource saturation; для UI — field/RUM при наличии и lab profile на одинаковом устройстве/сети.
3. Профилируй до изменения. Раздели время по границам: network/server/DB/external dependency/queue или input delay/JS/render/layout/assets. Не выбирай cache/index/memoization до доказательства bottleneck.
4. Сформулируй одну гипотезу: `если изменить X, метрика Y улучшится, потому что профиль показывает Z`; укажи guardrail для correctness, memory, cost и accessibility.
5. Сделай минимальную правку. Для DB сохрани query plan до/после и учти write cost; для cache определи key, staleness, invalidation, capacity, negative caching и stampede protection; для frontend проверь LCP/INP/CLS, bundle и main-thread work по применимости.
6. Повтори тот же benchmark с теми же условиями, сравни распределение и errors. Если план/профиль не изменился или выигрыш внутри шума — откати собственную оптимизацию.
7. Запусти correctness/regression checks и проверь реальный сценарий. Добавь бюджет/наблюдаемость только если они устойчиво защищают выявленный риск.

Не запускай нагрузку против production, платного API или внешнего сервиса без явного разрешения и лимита. Не публикуй чувствительные профили/данные.

## Выход

Верни таблицу `метрика → baseline → изменение → after → delta → guardrail`, профиль bottleneck, команду/условия измерения и остаточный риск.

- **PASS** — bottleneck доказан, измерение сопоставимо, целевая метрика улучшилась без нарушения guardrails.
- **FAIL** — метрика не улучшилась, errors/cost/correctness ухудшились или изменение не влияет на профиль.
- **INCONCLUSIVE** — среда/данные нестабильны, выборка мала или профиль недоступен; вывод о выигрыше не делается.

| Запрещено | Разрешено |
|---|---|
| «Оптимизировать» без baseline/profile | Сначала измерить и локализовать bottleneck |
| Выдать среднее за latency distribution | Сравнить median и tail percentiles |
| Добавить cache без staleness/key/invalidation | Зафиксировать correctness contract и hit-rate |
| Сохранить индекс, не изменивший query plan | Удалить лишний write cost |
| Считать один быстрый прогон доказательством | Повторить одинаковый workload и оценить шум |

Правильно: `EXPLAIN ANALYZE` показывает scan; подходящий индекс меняет план и p95, write overhead допустим. Неправильно: добавить memoization во все компоненты, потому что «React медленный».

Пример владельца: нельзя приравнивать `tokens_used` к расходу подписочного лимита; performance/cost вывод строится только по реально измеряемой метрике и подтверждённой цене.

Главное: оптимизация — причинно доказанное улучшение метрики при сохранении корректности.
