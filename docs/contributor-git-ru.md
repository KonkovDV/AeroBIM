---
title: "Гигиена Git — один автор коммита"
status: active
version: "1.1.0"
last_updated: "2026-05-21"
---

# Гигиена Git (2026)

Английская версия: [`contributor-git-2026.md`](contributor-git-2026.md).

## Проблема

Некоторые средства коммита добавляют в сообщение трейлеры соавторства (`Co-authored-by:`). GitHub показывает второго автора в истории и в Contributors.

## Рекомендуемый способ

Коммить из терминала или задачи VS Code **AeroBIM: commit (single author)** — не через автоматическую подпись с соавторами.

```powershell
cd AeroBIM
powershell -ExecutionPolicy Bypass -File scripts/git_commit.ps1 -Message "docs: ваше сообщение"
```

Скрипт фиксирует автора `KonkovDV`, отклоняет `Co-authored-by:` до коммита и проверяет итоговое сообщение.

## Проверка истории

```powershell
git log -20 --format="%B---" | Select-String "Co-authored-by"
```

Пустой вывод — в последних 20 коммитах нет соавторских трейлеров.

## Очистка истории

Перед `filter-branch` и force-push согласуйте с владельцем ветки. См. английский раздел в [`contributor-git-2026.md`](contributor-git-2026.md).

## CI и публикация

**Tasks: AeroBIM: quality gate** → коммит через `scripts/git_commit.ps1` → `git push`.
