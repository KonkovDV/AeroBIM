---
title: "Гигиена Git — один автор коммита"
status: active
version: "1.1.0"
last_updated: "2026-05-20"
---

# Гигиена Git (2026)

## Проблема

Некоторые IDE при автоматических коммитах добавляют в сообщение трейлеры соавторства (`Co-authored-by:`). GitHub отображает их как второго автора в истории и в Contributors.

## Рекомендуемый способ коммитов

Не поручайте коммит встроенному ассистенту IDE. Используйте локальный скрипт или задачу VS Code:

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

Если в прошлых коммитах уже есть `Co-authored-by`:

```powershell
$env:FILTER_BRANCH_SQUELCH_WARNING = "1"
git filter-branch -f --msg-filter "python scripts/strip_coauthor_msgfilter.py" -- main
git push --force-with-lease origin main
```

Перед переписыванием истории согласуйте force-push с владельцем ветки.

### Устаревший автор `KonkovaElena` / `test@example.com`

На `main` (2026-05-20) ранние коммиты переписаны на `KonkovDV <KonkovDV@users.noreply.github.com>`.

```bash
bash scripts/rewrite-author-konkovdv.sh
git update-ref -d refs/original/refs/heads/main
git push --force-with-lease origin main
```

## CI и публикация

**Tasks: AeroBIM: quality gate** → ручной коммит через `scripts/git_commit.ps1` → `git push`.
