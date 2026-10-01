---
title: "Лицензии AeroBIM, 2026"
status: active
version: "1.2.0"
date: "2026-08-14"
last_updated: "2026-09-22"
claim_boundary: "Инженерная политика, не юридическое заключение. LIC-001 требует юриста."
---

# Лицензии

Это инженерный учёт, не заключение юриста. Пока юрист не посмотрел распространение и сетевой сервис, LIC-001 остаётся открытым для права, даже если ядро PDF мы уже переложили.

В зале говорим так: **MIT — наш код**. Чужие компоненты остаются под своими лицензиями. Список — [`audit/dependency_license_inventory.json`](../audit/dependency_license_inventory.json). Продукт целиком под MIT не называем.

Так принято вести учёт: у каждого компонента своя лицензия (поля SPDX в реестре). Репозиторий с бейджем MIT чужой код не перелицензирует. Слабый copyleft (LGPL, MPL) держим немодифицированным и называем в уведомлении. Сильный (AGPL, GPL) в образ и в ядро не кладём. Это рамка сборки. Она не заменяет договор и не снимает `legal_review_required` там, где реестр его ставит.

Проверки: `backend/tests/test_dependency_license_gate.py` (нет записи или класс `unknown` — CI красный) и `backend/tests/test_license_isolation_guard.py` (copyleft-движки не выходят из `infrastructure/adapters` и `tools`).

## Что лежит в сборке

| Компонент | Лицензия в реестре | Где живёт |
|---|---|---|
| Код AeroBIM | MIT | Этот репозиторий |
| IfcOpenShell, IfcTester 0.8.5 | LGPL-3.0-or-later | Ядро разбора IFC и IDS. Импорт только из адаптеров и `tools`. Не модифицируем. Юридическая проверка рекомендована |
| web-ifc 0.0.77 | MPL-2.0 | Оболочка в браузере. Copyleft на файл: библиотеку не правим, в уведомлении называем |
| pypdfium2 5.12.1 | Apache-2.0 OR BSD-3-Clause | Боевой PDF: отрисовка и кадр. Плюс лицензии PDFium внутри колеса |
| pdfminer.six | MIT | Текст со слоя PDF |
| Pillow | MIT-CMU | Картинки для кадра PDF |
| ReportLab | BSD-3-Clause | PDF отчёта. Шрифт Liberation Sans — OFL, лежит у нас. Это не PyMuPDF |
| ezdxf | MIT, объявление автора, локально не сверяли (`verified: false`) | Необязательный DXF, extra `cad`. Чтение DWG из этого не следует |
| PyMuPDF 1.28.0 | AGPL-3.0-only OR коммерческая Artifex | Только extra `pdf-agpl`. В `requirements-lock.txt` и в образе Docker его нет |

Новая зависимость без строки в реестре красит CI. Классы риска в реестре: `permissive`, `weak_copyleft`, `strong_copyleft_or_commercial` (блокер выпуска, пока нет решения юриста), `unknown` (блокер всегда).

## Две полосы

Показ заказчику канала может читать copyleft-файлы локально. Публичный продукт, Docker, GitHub и остальные заказчики идут без GPL и без AGPL в поставке.

| Полоса | Где | Можно | Нельзя |
|---|---|---|---|
| **public_mit** (по умолчанию, CI, Docker, другие заказчики) | git и `requirements-lock.txt` | Наш MIT-код. LGPL IfcOpenShell за адаптерами и `tools`. Extra `pdf-agpl` в runtime lock не входит | Класть GPLv3 IFC в дерево. Линковать LibreDWG. Тащить AGPL в Docker |
| **customer_demo_local** | Каталог `.local/`, он в gitignore, только машина показа | Читать GPLv3 IFC-Bench (`4351`, `ettenheim_gis`, `hitos`, `samuel_macalister_sample_house`) | Коммитить эти файлы. Включать флаг в CI. Закрывать этим RT-001 |

```bash
python -m aerobim.tools.fetch_ifc_bench_v2 --from-dir <checkout> --include-gplv3 --demo-copyleft
python -m aerobim.tools.run_federated_mep_inventory --demo-copyleft
```

Вторая команда не пишет GPL-строки в `docs/evidence/`. LibreDWG не линкуем: GPL-3 не входит в MIT-ядро. На показе заказчик канала отдаёт IFC и PDF/A. Возможность `.dwg` остаётся FAILED.

Checkpoint **GO** (`regulatory_measurement_mvp`). `customer_go` **false**.

## LIC-001, PyMuPDF

На 31.07.2026 в замке стоял `pymupdf==1.28.0`, двойная лицензия AGPL-3.0 или коммерческая Artifex. В тот же день владелец выбрал **вариант B**. Боевой PDF — `pypdfium2` и `pdfminer.six` (и Pillow). ReportLab рисует выгрузку. PyMuPDF остался необязательным extra для инструментов разработки.

| Вариант | Цена | Что даёт | Статус |
|---|---|---|---|
| A. Договор Artifex | деньги и контракт | Блокер снимается, код не трогаем | не выбран |
| B. Уход на pypdfium2 и pdfminer.six | инженерия | Ядро PDF без AGPL | **выбран, инженерия сделана** |
| C. Вынести в необязательный extra | средняя | Ядро без AGPL, функция деградирует | перекрыт вариантом B. Extra `pdf-agpl` оставлен |
| D. Весь продукт под AGPL | открыть всё | Спорит с позицией MIT на наш код | отвергнут |

В реестре блокеров LIC-001 стоит **ENGINEERING_CLEARED_FOR_CORE_PDF**. Хвост: extra AGPL нельзя вернуть в runtime lock без решения владельца. Сторонние компоненты по-прежнему называют в уведомлении.

## Чего не говорим

«AeroBIM целиком под MIT». «Лицензионных рисков нет». «AGPL неприменим» без заключения юриста.

Можно: «MIT для нашего кода. Сторонние компоненты под своими лицензиями. Список в реестре».
