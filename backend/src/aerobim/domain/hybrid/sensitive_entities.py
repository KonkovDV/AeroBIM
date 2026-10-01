"""Local sensitive-entity detection (целевой поток: шаг «локальное обнаружение
чувствительных сущностей»; P2, domain-pure).

Детерминированный детектор (regex/stdlib; БЕЗ ML и БЕЗ сети). По тексту или по
mapping полей находит виды чувствительных сущностей (sensitive entities) и выводит
**fail-closed** правила маскирования для :class:`PrivacyGuard`:

- поле с обнаруженным СЕКРЕТОМ (api-key/token) -> ``remove`` (секрет не отправляется
  наружу даже в токенизированном виде);
- поле с обнаруженной сущностью (GlobalId, координаты, email, телефон, IP, путь) ->
  ``tokenize:<kind>`` (псевдонимизация — движок ещё может связать, raw скрыт);
- «чистый» скаляр без обнаружений -> ``remove`` по умолчанию (fail-closed: не
  выпускать нелистованное); ``keep`` только при явном ``keep_clean_scalars=True``;
- не-скаляр (dict/list) -> ``remove``.

ЧЕСТНЫЕ ГРАНИЦЫ: это **эвристический детектор-базлайн**, НЕ ML-классификатор
чувствительности и НЕ анонимизатор — маскирование не равно анонимности. Высокая
точность важнее полноты: пропущенное поле по умолчанию удаляется (fail-closed), а
не утекает. Названия организаций и «связь ревизий» надёжно ловятся только словарём
(P2 «расширение словаря сущностей») и здесь НЕ детектируются.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
from typing import Any


class EntityKind(Enum):
    """Виды чувствительных сущностей, надёжно детектируемые по шаблону."""

    SECRET = "secret"  # api-key / token / authorization
    GLOBAL_ID = "global_id"  # IfcGloballyUniqueId (22 base64-ish chars)
    COORDINATE = "coordinate"  # высокоточная десятичная координата/измерение
    EMAIL = "email"
    PHONE = "phone"
    IP = "ip"
    FILE_PATH = "file_path"


# Порядок важен: СЕКРЕТ проверяется первым (самое строгое действие — remove).
_PATTERNS: tuple[tuple[EntityKind, re.Pattern[str]], ...] = (
    (
        EntityKind.SECRET,
        re.compile(
            r"(sk-[A-Za-z0-9]{16,})"
            r"|(Bearer\s+[A-Za-z0-9._\-]{16,})"
            r"|(AKIA[0-9A-Z]{16})"
            r"|(\b[0-9a-fA-F]{32,}\b)",
        ),
    ),
    (EntityKind.EMAIL, re.compile(r"\b[\w.+\-]+@[\w\-]+\.[\w.\-]+\b")),
    (EntityKind.IP, re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")),
    (EntityKind.PHONE, re.compile(r"(?:\+7|\b8)\d{10}\b|\+\d{7,15}\b")),
    (
        EntityKind.FILE_PATH,
        re.compile(r"[A-Za-z]:\\[^\s\"']+|\\\\[^\s\"']+|/(?:[\w.\-]+/){2,}[\w.\-]+"),
    ),
    # IfcGloballyUniqueId: ровно 22 символа из base64-набора IFC (эвристика).
    (EntityKind.GLOBAL_ID, re.compile(r"\b[0-9A-Za-z_$]{22}\b")),
    # Высокоточная десятичная (>=4 знаков) — вероятная координата/измерение (эвристика).
    (EntityKind.COORDINATE, re.compile(r"-?\d+\.\d{4,}")),
)


@dataclass(frozen=True)
class DetectedEntity:
    """Находка детектора. Хранит ВИД и ПОЛЕ, но НЕ сырое значение (безопасность)."""

    kind: EntityKind
    field: str | None = None


def detect_entities(text: str) -> tuple[EntityKind, ...]:
    """Виды сущностей, встречающиеся в тексте (без хранения сырых значений)."""
    if not text:
        return ()
    found: list[EntityKind] = []
    for kind, pattern in _PATTERNS:
        if pattern.search(text):
            found.append(kind)
    return tuple(found)


def scan_payload(payload: Mapping[str, Any]) -> tuple[DetectedEntity, ...]:
    """Просканировать поля payload; вернуть находки (вид+поле), без сырых значений."""
    findings: list[DetectedEntity] = []
    for key, value in payload.items():
        if isinstance(value, Mapping | list | tuple | set):
            # Вложенные контейнеры не разбираем здесь — они fail-closed удаляются.
            continue
        for kind in detect_entities(str(value)):
            findings.append(DetectedEntity(kind=kind, field=str(key)))
    return tuple(findings)


def suggest_mask_rules(
    payload: Mapping[str, Any],
    *,
    keep_clean_scalars: bool = False,
) -> dict[str, str]:
    """Вывести fail-closed правила для :meth:`PrivacyGuard.mask_payload`.

    SECRET -> ``remove``; иная сущность -> ``tokenize:<kind>``; чистый скаляр ->
    ``remove`` (или ``keep`` при ``keep_clean_scalars``); не-скаляр -> ``remove``.
    """
    by_field: dict[str, set[EntityKind]] = {}
    for finding in scan_payload(payload):
        if finding.field is not None:
            by_field.setdefault(finding.field, set()).add(finding.kind)

    rules: dict[str, str] = {}
    for key, value in payload.items():
        field = str(key)
        kinds = by_field.get(field, set())
        if EntityKind.SECRET in kinds:
            rules[field] = "remove"  # секрет никогда не выпускаем наружу
        elif kinds:
            # Детерминированный выбор вида при нескольких совпадениях.
            kind = sorted(kinds, key=lambda k: k.value)[0]
            rules[field] = f"tokenize:{kind.value}"
        elif isinstance(value, Mapping | list | tuple | set):
            rules[field] = "remove"  # не-скаляр — fail-closed
        elif keep_clean_scalars:
            rules[field] = "keep"
        else:
            rules[field] = "remove"  # по умолчанию fail-closed
    return rules


__all__ = [
    "DetectedEntity",
    "EntityKind",
    "detect_entities",
    "scan_payload",
    "suggest_mask_rules",
]
