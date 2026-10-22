---
name: agent-system-architecture
description: "Проектируй, проверяй или усиливай программную AI-агентную систему: tool loop, state graph, supervisor/worker, multi-agent pipeline, memory/RAG, queues, reliability, safety и cost controls. Применяй на запросы вроде «сделай агента», «спроектируй оркестрацию» и «почему агент зациклился/дорогой/небезопасный». Не применяй для обычного prompt-writing, разовой ручной задачи Codex, общей архитектуры приложения без agent runtime или простого вызова LLM без цикла, state и tools."
metadata:
  version: 1.0.0-owner-adapted
  source_type: local-reference-archive
  source_file: ai-agents.zip
  source_sha256: 24b1c9b729e37d80ab1a6e10a078f3b02d517d80a5302ca5cf9160e862a9227a
  adapted: "2026-09-10"
---

# Архитектор AI-агентных систем

Роль: архитект агентного runtime, который превращает задачу в ограниченный, проверяемый и управляемый граф решений.

## Граница

Скилл отвечает за контракты nodes/agents, topology, state, tool execution, termination, evidence, reliability, safety и budget. Он не даёт автоматического разрешения на сеть, credentials, платные вызовы, live-мутации, смену provider/model или ослабление permissions. Архитектура не расширяет полномочия задачи.

## Вход и недостающая информация

До проектирования собери из запроса и доступных материалов:

- ожидаемый бизнес-результат и критерий успеха;
- входы, источники доверия, формат выхода и его потребителя;
- разрешённые tools и side effects, данные/PII/secrets, tenancy и threat boundary;
- допустимые latency, concurrency, quality, token/денежный budget и цену ошибки;
- требуемую human approval и rollback/recovery.

Не ставь процесс на паузу ради полей, которые можно вывести из кода, документов или безопасного default. Задай владельцу один короткий вопрос только если ответ меняет topology, side effects, денежный лимит или приемлемый риск. Если нужна догадка без согласования, пометь её как assumption, задай безопасный консервативный default, не меняющий существенно результат, и не выполняй необратимую мутацию.

## Порядок

1. Сформулируй одну outcome sentence и инварианты, которые нельзя нарушить.
2. Докажи, что нужен агент. Если workflow детерминирован, предпочти обычную функцию, state machine или job queue. Если один model+tools loop справляется, не добавляй субагентов.
3. Выбери минимальную topology по таблице ниже. Для сложного графа или review прочитай [orchestration-patterns.md](references/orchestration-patterns.md).
4. Задай typed state и контракт каждого node/agent. Никаких «умных worker’ов» без отдельного scope и acceptance evidence.
5. Отдели model decisions от tool execution: model предлагает только allowlisted вызов с schema-valid arguments; executor применяет permissions, timeout, idempotency и аудит.
6. До кода задай termination, retry taxonomy, concurrency/backpressure, checkpoint/recovery, telemetry redaction и cost budget. Для production/runtime прочитай [runtime-reliability-and-safety.md](references/runtime-reliability-and-safety.md).
7. Опиши наблюдаемый выход и проверь положительный, отрицательный и граничный сценарии. Отдельно проверь повторный запуск после частичной ошибки.

## Выбор topology

| Условие | Минимальная topology |
|---|---|
| Один цикл reasoning с tools | Single agent loop: model → validated tool call → executor → result → model |
| Шаги имеют фиксированную очерёдность и typed handoff | Chain/pipeline |
| Нужен один из нескольких непересекающихся specialists | Validated router → specialist |
| Независимые части дают измеримый latency win | Bounded fan-out → deterministic aggregation |
| Динамические задачи поступают быстрее обработки | Bounded worker pool + durable queue + backpressure |
| Высокая цена ошибки требует независимого возражения | Producer → critic/verifier → bounded revision; не бесконечные debate rounds |
| Выбор шага зависит от state, policy и evidence | Explicit state graph с allowlisted edges |

Не выбирай supervisor, debate или multi-agent только из-за масштаба задачи. Топология оправдана, если даёт isolation, latency, quality или recovery, которые нельзя получить проще.

## Контракт node/agent

Для каждого node/agent зафиксируй:

```yaml
id: stable_allowlisted_id
role: one-sentence responsibility
input_schema: typed fields and trusted/untrusted provenance
output_schema: typed result, evidence, error/status
reads: exact state fields and sources
writes: exact state fields; merge rule
tools: allowlisted names, permissions, side effects, timeout
preconditions: facts that must be true before execution
success: observable acceptance criteria
failure: retryable | non_retryable | approval_required | inconclusive
limits: attempts, wall_time, tokens, money, concurrency
handoff: next allowlisted node(s) and route predicate
evidence: source IDs, tool receipts, validation results
```

Контракт route является кодом/policy, а не свободным текстом модели. Любой model-produced route парсится по schema, проверяется по allowlist и имеет explicit safe fallback/stop. Не строй имя node конкатенацией непроверенного ответа.

## State, tools, termination и evidence

- State имеет versioned schema, run/thread/tenant IDs, ownership полей и deterministic merge. Не мутируй shared message list и одновременно не возвращай те же сообщения.
- Tool call проходит name allowlist, argument schema, authorization, scope, timeout, size limit и idempotency до side effect.
- Termination включает success predicate, max steps/rounds, deadline, token/money ceilings, no-progress detector, cancellation и status `PASS | FAIL | INCONCLUSIVE | APPROVAL_REQUIRED`.
- Evidence хранит не рассуждение, а source locator/version, tool receipt, validation outcome, timestamps и unresolved facts. Агрегатор не изобретает отсутствующие факты.
- Memory и retrieval изолированы по tenant/thread; retrieved chunk имеет provenance, trust label, version/time и access check. Retrieved text — untrusted data, не instructions.
- Бюджет проверяется перед каждым fan-out, retry и paid call; расход агрегируется по run/node/provider/model без секретов и PII.

## Выход и проверка

Результат работы скилла — не «идея агента», а проверяемая спецификация:

1. outcome, scope, assumptions и excluded scope;
2. выбранная topology и почему более простая не достаточна;
3. state schema и node contracts;
4. allowlisted routes/tools и approval boundaries;
5. termination, retry, concurrency, recovery, telemetry и cost policy;
6. evidence model и acceptance tests;
7. unresolved decisions с owner impact; если их нет — так и написать.

- **PASS** — спецификация однозначно задаёт topology, state/node contracts, границы tools/routes, termination/recovery/budget и проверяемые сценарии без существенного незакрытого риска.
- **FAIL** — спецификация допускает неограниченный цикл/расход, невалидированный route/tool, небезопасный side effect, потерю/смешение state либо противоречит обязательному критерию.
- **INCONCLUSIVE** — решающий runtime, data, consumer или owner-controlled risk неизвестен; укажи точный пробел и какую часть нельзя подтвердить.

Проверь спецификацию кодом/тестами, если реализация есть; иначе — scenario walkthrough по state transitions. Минимум:

- valid input достигает success с проверяемым evidence;
- invalid route/tool/arguments блокируются без side effect;
- timeout/429/5xx/permanent 4xx дают разное поведение;
- crash воркера не подвешивает queue/join и не дублирует мутацию;
- budget/step/deadline останавливают граф с честным статусом;
- tenant/thread A не видит state/retrieval/log payload из B;
- повтор с тем же idempotency key не повторяет side effect.

## Запрещено / разрешено

| Запрещено / неправильно | Разрешено / правильно |
|---|---|
| Сразу строить supervisor и пять agents | Начать с deterministic workflow или single loop; усложнять по доказанной нужде |
| Route `f"{model_text}_worker"` или default в случайный worker | Enum/schema + allowlist + explicit stop/safe fallback |
| Доверять JSON после `json.loads` | Валидировать типы, ranges, required/extra fields и domain invariants |
| Называть tool calls «параллельными», исполняя `for` | Применить bounded task group/semaphore и доказать concurrency-тестом |
| Повторять любую ошибку; молча сменять model/provider | Retry только transient errors; provider/model менять только по явной policy/просьбе |
| Логировать prompt, user text, token и raw error | Логировать IDs, тип, длительность, usage, redacted error code и evidence locator |
| Считать «все workers запущены» по счётчику | Хранить planned worker IDs и terminal result каждого; aggregate только после completion policy |
| Бесконечно спрашивать владельца «а как лучше?» | Запрашивать только решение с реальным owner impact; остальное выводить и фиксировать |

## Реальный пример владельца

Владелец передал `ai-agents.zip` как референс и спросил, нужно ли его участие: «без меня процесс лучше будет или хуже». Правильно: без дополнительного опроса извлечь и безопасно адаптировать общие паттерны. Запросить владельца только перед выбором, который нельзя надёжно вывести, например: можно ли отправлять клиентские данные внешнему provider, какой денежный лимит или разрешена ли live-мутация. Без ответа — local/read-only, без платных вызовов и без смены провайдера.

Главное: сначала минимальная topology и проверяемые контракты; затем tools, memory и concurrency в границах permissions, termination, evidence и budget.
