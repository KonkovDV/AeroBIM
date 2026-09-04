<!-- claims-lint: allow-file reason="Unsigned SP 63 IDS draft for signoff; not RT-002b; not a solver; NO_GO" -->
---
title: "Черновик samolet.ids по СП 63 — на согласование"
date: "2026-09-04"
last_updated: "2026-09-04"
status: draft_for_signoff
version: "0.1.0"
closes_rt001: false
closes_rt002: false
closes_rt003: false
claim_boundary: >
  Unsigned draft. approval is null. Not Samolet-signed profile (RT-002c OPEN).
  Not a structural solver. Not SP 63 table by exposure class. Checkpoint GO; customer_go false.
---

# Черновик профиля СП 63 (не продукт)

**Статус:** `draft_for_signoff`. Поле подписанта **пустое**. Это не RT-002c CLOSED.

Машинный каркас уже в git: [`../../samples/rule-packs/sp63-cover-template.json`](../../samples/rule-packs/sp63-cover-template.json)
(`approval: null`, `status: synthetic-template`). Пороги 20 мм — **шаблон**, не
таблица 8.1 по классу среды.

## Кто подписывает

| Поле | Значение |
|---|---|
| `signer_role` | *заполнить на колле* (ожидание: направление информационного моделирования) |
| `signer_name` | не в git |
| `version` | 0.1.0-draft |
| `supersedes` | нет |
| Что будет при смене ИТЗ | новый файл + `version++`; старый `pack_hash` остаётся в отчёте |

План Б, если подписи нет к 18.09: измерение на публичных IDS экспертизы
(Мособлгосэкспертиза, СПб ГАУ ЦГЭ). Это **не** профиль внедрения.

## IDS 1.0 (черновик спецификации)

Не подменять JSON-шаблон. Для показа «правило = переносимый артефакт»:

```xml
<?xml version="1.0" encoding="utf-8"?>
<ids xmlns="http://standards.buildingsmart.org/IDS"
     xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
     xsi:schemaLocation="http://standards.buildingsmart.org/IDS http://standards.buildingsmart.org/IDS/1.0/ids.xsd">
  <info>
    <title>AeroBIM SP 63 cover draft — UNSIGNED</title>
    <description>Draft for Samolet signoff. Not RT-002b. Not a solver. Template 20 mm IfcSlab cover.</description>
  </info>
  <specifications>
    <specification name="SP63-COVER-SLAB-DRAFT" ifcVersion="IFC2X3 IFC4 IFC4X3_ADD2">
      <applicability maxOccurs="unbounded">
        <entity>
          <name>
            <simpleValue>IFCSLAB</simpleValue>
          </name>
        </entity>
      </applicability>
      <requirements>
        <property dataType="IFCLENGTHMEASURE">
          <propertySet>
            <simpleValue>Pset_CoveringCommon</simpleValue>
          </propertySet>
          <baseName>
            <simpleValue>CoveringThickness</simpleValue>
          </baseName>
          <restriction>
            <xs:minInclusive xmlns:xs="http://www.w3.org/2001/XMLSchema" value="20"/>
          </restriction>
        </property>
      </requirements>
    </specification>
  </specifications>
</ids>
```

Fail-closed: запрошенный IDS, который не грузится, роняет комплект. Молчание ≠ успех.

## Что это не закрывает

Арматура в IFC, сети ОВ/ВК, независимый пересчёт, полный СП 63. Черновик — повод
назвать подписанта и состав, не «мы уже проверили конструкции».
