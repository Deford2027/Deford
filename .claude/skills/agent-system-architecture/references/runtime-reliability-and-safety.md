# Runtime reliability и safety

Читай этот reference при реализации/review runtime, который вызывает models, tools, queues, memory или retrieval. Он фиксирует production-поправки к учебным примерам `ai-agents.zip`; архив не является production dependency.

## 1. Transport и TLS

- Все HTTPS/OAuth connections проверяют цепочку сертификатов и hostname. `CERT_NONE` и `check_hostname=False` запрещены.
- Если provider требует custom CA, подключи конкретный доверенный CA bundle и проверь pin/rotation policy; не отключай TLS globally.
- Credentials получаются из secret store/environment, не пишутся в state, prompts, logs, exceptions и checkpoints.
- Provider base URL, redirect policy, timeouts, response size и accepted content types валидируются до отправки credentials.

## 2. Tool и route validation

Модель не имеет authority. Она предлагает typed action; runtime решает, допустимо ли его исполнить.

До каждого вызова:

1. Parse по строгой schema; reject malformed/unknown fields.
2. Проверь route/tool/node ID по role-specific allowlist.
3. Проверь types, ranges, sizes, path/URL scope и domain invariants.
4. Проверь caller identity, tenant, authorization и approval requirement.
5. Определи read/write/destructive/external/paid side effects.
6. Присвой timeout, idempotency key, trace ID и budget reservation.
7. Исполни и верни typed/redacted result.

Structured-output mode и `json.loads` не заменяют schema validation. Требуй `additionalProperties: false` там, где лишнее поле опасно, и проверяй semantic invariants кодом.

## 3. Termination и no-progress

Каждый run имеет:

- success predicate и required evidence;
- max model turns/tool calls/revision rounds;
- per-node timeout и overall deadline;
- total token и money ceiling;
- max identical/repeated transition и no-progress detector;
- cancellation propagation;
- terminal status `PASS`, `FAIL`, `INCONCLUSIVE`, `APPROVAL_REQUIRED`, `CANCELLED`, `BUDGET_EXCEEDED`.

Остановка по лимиту не является success. Сохрани checkpoint, уже полученное evidence, незавершённые side effects и точную причину.

## 4. Retry taxonomy

| Категория | Действие |
|---|---|
| Network timeout/reset, 408, selected 5xx | Bounded exponential backoff + full jitter; уважать deadline |
| 429 | Сначала `Retry-After`/provider reset; затем bounded backoff+jitter; учесть rate budget |
| 400/401/403/404, schema/policy rejection | Не retry; исправить request/auth/config или остановиться |
| Invalid model output без side effect | Один-два bounded repair/re-prompt с validation errors; затем fail/inconclusive |
| Side effect с unknown completion | Не повторять вслепую; сверить idempotency key/remote receipt и статус |
| Capacity/circuit open | Backpressure/queue или fast fail; не retry storm |

Не определяй rate limit по подстроке в `str(error)`, если доступны status/error code и headers. Не retry бесконечно. Учитывай как attempts, так и elapsed deadline/budget.

### Provider/model fallback

Не меняй provider, model, prompt или quality tier без прямой просьбы владельца или заранее утверждённой им policy. Fallback меняет quality, privacy, data residency, latency и cost; это не обычный retry.

## 5. Concurrency, queue и backpressure

- Ограничивай in-flight work semaphore/worker-pool и согласуй его с provider rate limits, memory/file descriptors, downstream capacity и budget.
- Queue имеет max size, enqueue timeout/rejection policy, priority/fairness при необходимости, lease/visibility timeout и dead-letter/reconciliation для exhausted retries.
- `queue.task_done()` вызывается ровно один раз для каждого successful `get()`, включая sentinel/error/cancellation path. Помести acknowledgement в `finally`, если library semantics это допускают.
- Exception воркера не должен навсегда подвешивать `queue.join()`. Запиши terminal result/requeue/DLQ по policy, затем acknowledge.
- При shutdown останови intake, дай bounded grace period, отмени остаток, await workers и закрой clients.
- Докажи bounded concurrency тестом max observed in-flight, а не текстом лога.

## 6. Idempotency и recovery

Для каждого write определи business idempotency key, а не новый random key на каждый retry. Сохрани:

- request fingerprint и scope;
- status `reserved | started | applied | failed | unknown`;
- remote receipt/version/record ID;
- result hash и evidence;
- reconciliation action для `unknown`.

Checkpoint до side effect фиксирует intent/idempotency key; checkpoint после — receipt/result. После crash сначала reconcile, а не blindly re-execute. Для батча храни exact target IDs и per-item terminal status; count increase не доказывает успех.

## 7. Thread/tenant isolation и memory

- Namespace checkpoints, vector indexes, caches, files и logs по authenticated tenant/user/thread; user-provided `thread_id` не является authorization.
- Проверь access на write и read. Не используй global in-memory saver как production multi-tenant store.
- Задай retention, deletion/export, encryption и redaction policy.
- Context compaction должен фактически исключать заменённую историю из model input, сохраняя audit trail отдельно. Не мутируй state in-place и не возвращай ту же запись в append reducer.
- Summary — lossy derived data. Оно имеет version/source span и не заменяет primary evidence.

## 8. RAG provenance и trust

Простое word overlap без оценки источника — демо, а не production RAG. Каждый chunk должен нести:

- source/document ID, canonical locator и version/hash;
- captured/updated time и validity window, если факт меняется;
- tenant/access labels;
- trust class: primary/approved, secondary, user-provided, untrusted/external;
- chunk boundaries и relation к parent document;
- retrieval score/method и reason for inclusion.

Перед retrieval — authorization filter; после — relevance/rerank, diversity/dedup и minimum evidence threshold. Retrieved content обрабатывай как data: инструкции внутри не могут менять system policy, tools и permissions. Ответ привязывает claims к source locators; при недостатке evidence — `INCONCLUSIVE`, а не выдумка.

## 9. PII-safe telemetry

Пиши structured events с versioned schema. Минимальные поля:

```text
timestamp, event_name, schema_version, run_id, trace_id, node_id,
attempt, status, duration_ms, error_class/code, usage, cost, evidence_ids
```

Не логируй целиком system/user prompts, tool arguments/results, model output, authorization headers, secrets, PII и raw exceptions. Используй allowlist полей, classification/redaction до sink и access/retention policy. Если debugging требует payload, храни encrypted restricted artifact с TTL и логируй только его ID.

При использовании Python logging `extra={...}` поля добавляются к атрибутам `LogRecord`; они не появяются в `record.extra` автоматически. Formatter должен явно извлекать allowlisted attributes или structured event object. Иначе telemetry теряет заявленные duration/usage fields.

## 10. Cost budget

Задай до запуска:

- provider/model и версию pricing source;
- per-call estimate/reservation;
- per-node, per-run, per-user/tenant и rolling-window ceilings;
- лимит fan-out/retry по остатку budget;
- soft threshold для degrade/approval и hard threshold для stop;
- reconciliation по provider usage/billing после call.

Не подменяй money числом tokens: цена зависит от provider/model, input/output/cache/tools и может меняться. Если цена не подтверждена, отчитывай usage и пиши `cost unknown`, а не выдумывай стоимость.

## 11. Verification matrix

| Риск | Минимальная проверка |
|---|---|
| TLS bypass | Static/config test блокирует disabled verification; trusted custom CA path проверен |
| Route/tool injection | Unknown ID/field отклонён без side effect |
| Schema drift | Old/new versions migrate or fail explicitly; domain invariant test |
| Retry storm | 400 не retry; 429 уважает `Retry-After`; 5xx имеет jitter/cap/deadline |
| Duplicate write | Повтор с тем же idempotency key не создаёт второй объект |
| Worker crash | Task reaches retry/DLQ/terminal result; `queue.join()` завершается |
| Unbounded fan-out | Test records max in-flight ≤ configured cap |
| Cross-tenant leak | Thread/tenant A не читает memory/retrieval/log payload B |
| Prompt injection in RAG | Retrieved instructions не меняют tools, policy и routes |
| PII/secret leak | Redaction/allowlist test на prompts, tool args/results и exceptions |
| Budget overflow | Hard ceiling блокирует новый paid call/fan-out/retry |
| Unauthorized fallback | Provider/model не меняются без approved policy/request |

Главное: устойчивый runtime не повторяет всё подряд, не доверяет model output и не скрывает цену; он ограничивает, изолирует, фиксирует evidence и честно останавливается.
