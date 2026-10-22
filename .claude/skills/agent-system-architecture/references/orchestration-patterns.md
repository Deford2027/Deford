# Паттерны оркестрации

Читай этот reference, когда single loop недостаточен, нужен multi-node graph, параллельные workers или независимая проверка. Это адаптация учебных паттернов из `ai-agents.zip`, а не копия его runtime или разрешение запускать внешние API.

## 1. Single agent tool loop

```text
request → model decision → validate call → execute tool → record result
                    ↑                                      ↓
                    └────── until success/stop ───────────────────┘
```

Используй, когда одна роль может выбирать из небольшого allowlist tools. Каждый цикл имеет max steps, deadline и budget. Tool result — typed envelope `{ok, data, error, evidence, retryable}`; модель не получает raw exception или secrets.

Не подходит, если нужны hard ordering, независимый review, высокая параллельность или строгая isolation.

## 2. Chain / pipeline

```text
normalize → research → draft → validate → publish candidate
```

Используй для фиксированной последовательности с typed handoff. Каждый шаг читает только нужные state fields и пишет свой output. Ошибка не пропускается вперёд без explicit degraded-mode policy.

Если шаг deterministic, он должен быть обычной функцией, а не LLM-agent.

## 3. Validated router → specialist

Модель может классифицировать intent, но runtime принимает только enum из allowlist:

```text
model output → schema parser → policy/allowlist → exact node ID
                              └→ unknown/invalid: stop or explicit safe fallback
```

Не используй конкатенацию вида `model_text + "_worker"`. Не отправляй unknown intent в случайную ветку: это скрытая ошибка маршрутизации.

## 4. Supervisor и worker set

Применяй, когда состав специалистов зависит от задачи. Supervisor выдаёт не следующее имя в свободном тексте, а plan:

```json
{
  "workers": ["evidence_researcher", "risk_reviewer"],
  "join_policy": "all_required",
  "deadline_ms": 30000,
  "max_parallel": 2
}
```

Runtime валидирует worker IDs, deduplicates и отслеживает каждый planned ID до terminal state. Агрегация стартует по join policy, а не по ненадёжному счётчику.

### Исправление both-workers bug

В учебном `supervisor_aggregator` intent `both` терялся: supervisor сохранял только первый worker в `next`, а `worker_route` искал значение `both`, которого уже не было. Более того, ветка возвращала weather worker вместо отсутствующего time worker.

Исправление: храни `planned_worker_ids`, `pending_worker_ids` и result/status по ID. После completion удали ровно завершённый ID; выбирай следующий из pending или переходи к join. Для независимых workers лучше bounded fan-out, чем имитация последовательного `next`.

## 5. Bounded fan-out / fan-in

Используй только для независимых задач, когда latency win выше цены fan-out. Ограничь:

- `max_parallel` semaphore/task group;
- per-worker и overall deadline;
- per-worker и total token/money budget;
- input/output size;
- cancellation policy и partial-result policy;
- deterministic ordering/deduplication при merge.

Наличие нескольких tool calls в одном ответе модели не означает concurrency. Цикл `for` с последовательным `await` — последовательное исполнение.

## 6. Shared tool executor

Агенты не исполняют arbitrary function names сами. Они производят typed intent. Один центральный executor:

1. проверяет tool name по role-specific allowlist;
2. валидирует аргументы и отклоняет unknown fields;
3. применяет authorization, tenant/scope и approval gate;
4. назначает timeout, idempotency key и trace ID;
5. выполняет вызов;
6. возвращает redacted typed envelope и evidence receipt.

`return_to` или continuation node тоже валидируется по allowlist; его нельзя слепо брать из shared state.

## 7. Producer → critic/verifier → bounded revision

Используй, когда цена ложного PASS оправдывает независимый контекст. Critic получает task, criteria, primary artifacts и candidate result, но не желаемый вердикт. Он возвращает findings с evidence; producer исправляет только подтверждённое. Число revision rounds ограничено; далее `INCONCLUSIVE` или owner decision.

Debate «ради баланса» без primary evidence обычно умножает стоимость и уверенность, а не истину.

## 8. State graph

Задай:

- versioned typed state и migration policy;
- поле-issuer: какой node может писать какое поле;
- immutable append-only events для аудита и derived state для работы;
- deterministic merge для parallel results;
- allowlisted edges и route predicates;
- terminal states и no-progress detection;
- checkpoint boundary до/after side effect.

Не смешивай in-place mutation и reducer-append одних и тех же событий: так история дублируется. Summary не является compaction, если исходная история продолжает передаваться в модель.

## Минимальная проверка topology

- Все node достижимы только по allowlisted edges.
- Unknown route не запускает worker и side effect.
- Каждый planned worker завершён или имеет explicit terminal error.
- Join policy корректна при zero, one, all, partial и failed workers.
- Cancellation освобождает resources; retry не дублирует side effects.
- Граф завершается по success, failure, deadline, budget, no-progress и cancellation.

Главное: multi-agent topology нужна только когда её isolation, parallelism или independent evidence дают измеримую пользу.
