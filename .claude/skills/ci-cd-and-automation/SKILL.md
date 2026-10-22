---
name: ci-cd-and-automation
description: "Создавай или исправляй CI/CD, проверки pull request, сборку, артефакты и автоматизацию доставки, когда меняется pipeline или нужен воспроизводимый quality gate. Не применяй к ручной локальной проверке без повторяемого процесса и не навязывай deploy каждому репозиторию."
metadata:
  version: 1.0.0-owner-adapted
  upstream_url: https://github.com/addyosmani/agent-skills/tree/6ca0cd7db39b41b1c37e26d335c507ee92382c6d/skills/ci-cd-and-automation
  upstream_commit: 6ca0cd7db39b41b1c37e26d335c507ee92382c6d
  upstream_sha256: a6ed8ed56456b01ff8314c44eefc69897d9905ae4e06bb2b7036286efb79b5f0
  adapted: "2026-09-10"
---

# CI/CD и автоматизация

Ты превращаешь повторяемую проверку или доставку в воспроизводимый, минимально привилегированный pipeline.

## Порядок

1. Найди действующий package/build manager, lockfile, CI provider, команды проекта, protected branches и способ релиза. Не изобретай команды по шаблону.
2. Определи trigger и минимальные risk-based gates: build/static, focused tests, security, artifact/release — только применимые к изменению. Нельзя считать зелёный lint заменой runtime-теста.
3. Пинуй runtime/action/tool версии; используй frozen/immutable dependency install. До lifecycle scripts изучи точный пакет и политику менеджера; не запускай плавающий installer.
4. Ограничь permissions job/token, не печатай secrets, не передавай credentials в fork/untrusted context. Production environment и deploy требуют отдельного разрешения/защиты владельца.
5. Кэшируй только восстанавливаемые dependencies/build artifacts по ключу lockfile+runtime; не кэшируй secrets и непроверенное состояние.
6. Сделай failures наблюдаемыми: понятный exit status, сохранённый тестовый отчёт/артефакт и причина. Не маскируй сбой `continue-on-error`, если gate обязателен.
7. Проверь pipeline безопасно: syntax/lint конфигурации, локальная эквивалентная команда и, если разрешён push/PR, реальный run. Без реального run статус интеграции — `INCONCLUSIVE`.

Изменение CI — runtime/config изменение; соблюдай лимиты шага, делай точный diff и независимый review до коммита.

## Выход

Дай trigger, jobs/dependencies, permissions/secrets boundary, cache/artifacts, gates, rollback и ссылки на run/exit status.

- **PASS** — pipeline реально запущен на целевом trigger, применимые gates выполняются и обязательный сбой останавливает процесс.
- **FAIL** — невоспроизводимая установка, лишние permissions, утечка secret, пропущенный обязательный gate или ложнозелёный run.
- **INCONCLUSIVE** — конфигурация статически валидна, но целевой provider/run недоступен.

| Запрещено | Разрешено |
|---|---|
| Копировать workflow без проверки проекта | Вывести команды из manifest/lockfile/существующего CI |
| Плавающие actions/images/packages | Пиновать версию или digest и зафиксировать источник |
| Давать write-token всем jobs | Выдать минимальные permissions конкретному job |
| Делать все gates обязательными всегда | Выбрать обязательные gates по риску и политике ветки |

Правильно: PR запускает frozen install, build и затронутые тесты с read-only token; release job отделён и защищён. Неправильно: `npm install`, latest action и production deploy на любой push.

Пример владельца: успешный save/queue flag не означает завершение — pipeline должен проверять consumer и физический результат, если именно это является критериями задачи.

Главное: автоматизация воспроизводит доказанную ручную проверку и не получает лишних полномочий.
