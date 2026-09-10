import { deflateRawSync } from "node:zlib";
import { describe, expect, it } from "vitest";

import { parseArgs as parseDemoArgs } from "./capture-demo-seed-smoke.mjs";
import {
  COPY,
  EXPORT_UNSAVED_CONFIRM,
  FORBIDDEN_FIXED,
  OA21_NEEDLE,
  SMOKE_REPORT_ID,
  assertAcceptedReview,
  assertDemoSeedPayload,
  assertDraftReview,
  assertNoFalseFixed,
  assertUnsavedDialogs,
  bcfMarkupText,
  inspectExportBundle,
  zipLocalEntries,
} from "./capture-review-smoke-shared.mjs";

function storedZip(files) {
  const parts = [];
  for (const [name, content] of Object.entries(files)) {
    const nameBuf = Buffer.from(name);
    const data = Buffer.from(content);
    const header = Buffer.alloc(30);
    header.writeUInt32LE(0x04034b50, 0);
    header.writeUInt16LE(20, 4);
    header.writeUInt32LE(data.length, 18);
    header.writeUInt32LE(data.length, 22);
    header.writeUInt16LE(nameBuf.length, 26);
    parts.push(header, nameBuf, data);
  }
  return Buffer.concat(parts);
}

function deflatedZip(name, content) {
  const nameBuf = Buffer.from(name);
  const raw = Buffer.from(content);
  const compressed = deflateRawSync(raw);
  const header = Buffer.alloc(30);
  header.writeUInt32LE(0x04034b50, 0);
  header.writeUInt16LE(20, 4);
  header.writeUInt16LE(8, 8);
  header.writeUInt32LE(compressed.length, 18);
  header.writeUInt32LE(raw.length, 22);
  header.writeUInt16LE(nameBuf.length, 26);
  return Buffer.concat([header, nameBuf, compressed]);
}

const draftJson = {
  summary: { passed: false },
  issues: [{ review: { state: null, actor: null, event_id: null, effective_text: null } }],
};

const confirmedJson = {
  summary: { passed: false },
  issues: [
    {
      review: {
        state: "accepted",
        actor: "anonymous-dev",
        event_id: "evt-1",
        effective_text: `${OA21_NEEDLE}: saved`,
      },
    },
  ],
};

describe("OA-21 export inspectors", () => {
  it("accepts a stored and a deflated BCF markup", () => {
    const stored = storedZip({ "topic/markup.bcf": "<Description>hello</Description>" });
    expect(bcfMarkupText(stored)).toContain("hello");
    const deflated = deflatedZip("guid/markup.bcf", `<Description>${OA21_NEEDLE}</Description>`);
    expect(bcfMarkupText(deflated)).toContain(OA21_NEEDLE);
    expect(zipLocalEntries(deflated)[0].name).toBe("guid/markup.bcf");
  });

  it("rejects a leaked draft and a flipped verdict", () => {
    expect(() => assertDraftReview({
      summary: { passed: false },
      issues: [{ review: { state: null, effective_text: OA21_NEEDLE } }],
    })).toThrow(/leaked/);
    expect(() =>
      assertAcceptedReview({
        summary: { passed: true },
        issues: [{ review: { state: "accepted", actor: "a", event_id: "e", effective_text: OA21_NEEDLE } }],
      }),
    ).toThrow(/summary\.passed/);
  });

  it("passes the draft/confirmed pair without «исправлено»", () => {
    assertDraftReview(draftJson);
    assertAcceptedReview(confirmedJson);
    const pdf = Buffer.alloc(80, 1);
    inspectExportBundle({
      json: draftJson,
      html: "<html>machine</html>",
      bcfBytes: storedZip({ "t/markup.bcf": "<Description>machine</Description>" }),
      pdfBytes: pdf,
      phase: "draft",
    });
    inspectExportBundle({
      json: confirmedJson,
      html: `<html>state=accepted ${OA21_NEEDLE}</html>`,
      bcfBytes: storedZip({ "t/markup.bcf": `<Description>${OA21_NEEDLE}</Description>` }),
      pdfBytes: pdf,
      phase: "confirmed",
    });
  });

  it("fails when the forbidden claim word appears", () => {
    expect(() => assertNoFalseFixed("html", `дефект ${FORBIDDEN_FIXED}`)).toThrow(/исправлено/);
  });

  it("requires the exact unsaved-card confirm copy", () => {
    expect(() => assertUnsavedDialogs([])).toThrow(/did not raise/);
    assertUnsavedDialogs([EXPORT_UNSAVED_CONFIRM, EXPORT_UNSAVED_CONFIRM]);
    expect(() => assertUnsavedDialogs(["another warning"])).toThrow(/drifted/);
  });
});

describe("demo-seed smoke helpers", () => {
  it("keeps the seeded-status needle on the current honesty line", () => {
    expect(COPY.demoSeededNeedle).toBe("Учебный комплект, не комплект заказчика");
  });

  it("parses base url and output dir", () => {
    const options = parseDemoArgs([
      "--base-url",
      "http://127.0.0.1:5199",
      "--output-dir",
      "artifacts/demo-seed",
    ]);
    expect(options.baseUrl).toBe("http://127.0.0.1:5199");
    expect(options.outputDir.replace(/\\/g, "/")).toContain("artifacts/demo-seed");
  });

  it("rejects the overlay fixture id and closed RT flags", () => {
    expect(() =>
      assertDemoSeedPayload({
        fixture: true,
        closes_rt001: false,
        closes_rt002: false,
        closes_rt003: false,
        report_id: SMOKE_REPORT_ID,
        issue_count: 2,
      }),
    ).toThrow(/overlay fixture/);
    const body = assertDemoSeedPayload({
      fixture: true,
      closes_rt001: false,
      closes_rt002: false,
      closes_rt003: false,
      report_id: "ab".repeat(16),
      issue_count: 2,
    });
    expect(body.issue_count).toBe(2);
  });
});
