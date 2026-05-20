---
title: "Git hygiene — без соавтора Cursor"
status: active
version: "1.0.0"
last_updated: "2026-05-20"
---

# Git hygiene (2026)

## Проблема

При коммитах через **Cursor Agent** в сообщение может добавляться строка:

```text
Co-authored-by: Cursor <cursoragent@cursor.com>
```

GitHub показывает её как второго автора в истории и в Contributors.

## Отключить в Cursor (обязательно)

1. **Cursor Settings** → **Agent** → **Attribution**
2. Выключить **Commit attribution** и **PR attribution**
3. Перезапустить Cursor

Документация: [cursor.com/docs/integrations/git](https://cursor.com/docs/integrations/git)

Для CLI (если используете `cursor` в терминале): в `~/.cursor/cli-config.json` задать `"commitAttribution": false` и `"prAttribution": false`, либо выполнить `cursor /update-cli-config`.

## Рекомендуемый способ коммитов в этом репозитории

Не просить агента выполнять `git commit`. Используйте локальный скрипт или задачу VS Code:

```powershell
cd AeroBIM
powershell -ExecutionPolicy Bypass -File scripts/git_commit.ps1 -Message "docs: ваше сообщение"
```

Скрипт:

- фиксирует автора `KonkovDV`;
- отклоняет сообщения с `Co-authored-by:` до коммита;
- проверяет итоговый коммит после записи.

## Проверка истории

```powershell
git log -20 --format="%B---" | Select-String "Co-authored-by"
```

Пустой вывод — в последних 20 коммитах нет соавторских трейлеров.

## Очистка уже испорченной истории

Только если в прошлых коммитах уже есть `Co-authored-by` (на `main` в AeroBIM этого нет на 2026-05-20):

```powershell
$env:FILTER_BRANCH_SQUELCH_WARNING = "1"
git filter-branch -f --msg-filter "python scripts/strip_coauthor_msgfilter.py" -- main
git push --force-with-lease origin main
```

Перед переписыванием истории согласуйте force-push с владельцем ветки.

## CI и публикация

Предпочтительно: **Tasks: AeroBIM: quality gate** → ручной коммит через `scripts/git_commit.ps1` → `git push`.  
Так в GitHub остаётся один человеческий автор без ботов в истории коммитов.
