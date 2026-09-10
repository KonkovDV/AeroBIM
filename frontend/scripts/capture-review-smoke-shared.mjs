/**
 * Shared helpers for the expert-workplace rehearsal scripts.
 *
 * Local Vite-dev stack only. Not the KT#3 jury CLI (`run_kt3_jury`).
 * Not a customer pack, not SSO, not product accuracy.
 */
import { readFile } from "node:fs/promises";
import path from "node:path";
import process from "node:process";
import { inflateRawSync } from "node:zlib";
import { chromium } from "playwright";

export const LOOPBACK_HOSTS = new Set(["127.0.0.1", "localhost", "[::1]"]);

/** Unsaved-card warning — must match UI_COPY.exportUnsavedConfirm (FE-DRIFT-01). */
export const EXPORT_UNSAVED_CONFIRM =
  "В карточке есть несохранённый текст. В файл попадёт последняя записанная на сервере версия, не текущий черновик. Продолжить выгрузку?";

/** Confirm button of the same dialog — must match UI_COPY.exportUnsavedContinue (FE-DRIFT-01). */
export const EXPORT_UNSAVED_CONTINUE = "Продолжить выгрузку";

/**
 * FE-CRUFT-02: the warning is a page element now, not a browser modal, so the
 * rehearsal addresses it by markup hooks. The pairing with the component is
 * pinned by src/export-confirm-copy-drift.test.ts — a renamed hook would make
 * this script silently accept a dirty export.
 */
export const EXPORT_UNSAVED_DIALOG = "export-unsaved-dialog";
export const EXPORT_UNSAVED_MESSAGE = "export-unsaved-message";

/** Saved expert text used as the OA-21 needle. Must not leak into the dirty export. */
export const OA21_NEEDLE = "Репетиция стенда";

export const FORBIDDEN_FIXED = "исправлено";

export const STACK_VITE_DEV = "vite-dev";

/** Overlay fixture from seed_smoke_report. The call-path demo seed must not reuse this id. */
export const SMOKE_REPORT_ID = "9".repeat(32);

export const COPY = {
  projects: "Проекты",
  demoSeed: "Загрузить демонстрационный комплект",
  demoSeededNeedle: "Учебный комплект, не комплект заказчика",
  trainingNeedle: "ещё не согласован",
  engineFlagNeedle: "Результат формирует сервер",
  pdfHintNeedle: "Черновик карты покрытия",
  roleBannerNeedle: "не предоставляет права доступа",
  rehearsalNeedle: "изучите доказательство",
  keyboardHelp: "Справка и клавиши",
  keyboardHelpTitle: "Справка клавиатуры триажа",
  viewerReady: "готов",
  hitlConfirmed: "Подтверждено экспертом",
};

export function hideSaveFilePicker() {
  Object.defineProperty(window, "showSaveFilePicker", {
    value: undefined,
    configurable: true,
  });
}

export async function launchChromium() {
  const launchOptions = { headless: true };
  try {
    return await chromium.launch(launchOptions);
  } catch (error) {
    if (process.platform === "win32") {
      return chromium.launch({ ...launchOptions, channel: "msedge" });
    }
    throw new Error(
      "Playwright Chromium is missing. From frontend/: npx playwright install chromium",
      { cause: error },
    );
  }
}

export function attachNetworkGuards(context) {
  const requestOrigins = new Set();
  const failedResponses = [];
  const consoleErrors = [];
  context.on("request", (request) => {
    try {
      const url = new URL(request.url());
      requestOrigins.add(url.host ? `${url.protocol}//${url.host}` : url.protocol);
    } catch {
      requestOrigins.add("<unparsed>");
    }
  });
  context.on("response", (response) => {
    if (response.status() >= 400) {
      failedResponses.push({ status: response.status(), url: response.url() });
    }
  });
  return { requestOrigins, failedResponses, consoleErrors };
}

/** Only network schemes can leave the laptop. blob: and data: stay on-device. */
export function externalOrigins(origins) {
  return [...origins].filter((origin) => {
    if (!origin.startsWith("http:") && !origin.startsWith("https:")) {
      return false;
    }
    const host = origin.replace(/^https?:\/\//, "").replace(/:\d+$/, "");
    return !LOOPBACK_HOSTS.has(host);
  });
}

/** GET /v1/auth/bff = 501 is the documented default (not customer SSO). */
export function isExpectedHonestyFailure(row) {
  if (row.status !== 501) {
    return false;
  }
  try {
    return new URL(row.url).pathname === "/v1/auth/bff";
  } catch {
    return /\/v1\/auth\/bff(?:\?|$)/.test(String(row.url));
  }
}

export function unexpectedHttpFailures(rows) {
  return rows.filter((row) => !isExpectedHonestyFailure(row));
}

export function unexpectedConsoleErrors(messages) {
  return messages.filter((text) => {
    if (/501/.test(text) && /auth\/bff|Failed to load resource/i.test(text)) {
      return false;
    }
    if (/frame-ancestors/.test(text)) {
      return false;
    }
    return true;
  });
}

export function assertLoopbackAndQuiet({ requestOrigins, failedResponses, consoleErrors }) {
  const external = externalOrigins(requestOrigins);
  if (external.length > 0) {
    throw new Error(`Rehearsal must stay on loopback, saw: ${external.join(", ")}`);
  }
  const unexpected = unexpectedHttpFailures(failedResponses);
  if (unexpected.length > 0) {
    throw new Error(`Unexpected HTTP failures: ${JSON.stringify(unexpected)}`);
  }
  const noisy = unexpectedConsoleErrors(consoleErrors);
  if (noisy.length > 0) {
    throw new Error(`Unexpected console errors: ${JSON.stringify(noisy)}`);
  }
  return { externalOrigins: external };
}

export function assertNoFalseFixed(label, text) {
  if (String(text).includes(FORBIDDEN_FIXED)) {
    throw new Error(`${label} contains forbidden «${FORBIDDEN_FIXED}»`);
  }
}

export function reviewProjection(json) {
  const issue = json?.issues?.[0];
  if (!issue || typeof issue !== "object") {
    throw new Error("export JSON missing issues[0]");
  }
  return issue.review ?? null;
}

export function assertDraftReview(json, needle = OA21_NEEDLE) {
  if (json?.summary?.passed === true) {
    throw new Error("draft export flipped summary.passed — UI must not own the verdict");
  }
  const review = reviewProjection(json);
  if (review !== null && typeof review === "object") {
    if (review.state != null) {
      throw new Error(`draft review.state should be null, got ${JSON.stringify(review.state)}`);
    }
    if (review.actor != null) {
      throw new Error(`draft review.actor should be null, got ${JSON.stringify(review.actor)}`);
    }
    if (review.event_id != null) {
      throw new Error(`draft review.event_id should be null, got ${JSON.stringify(review.event_id)}`);
    }
  }
  const blob = JSON.stringify(json);
  if (blob.includes(needle)) {
    throw new Error("unsaved draft leaked into JSON export");
  }
  assertNoFalseFixed("draft json", blob);
}

export function assertAcceptedReview(json, needle = OA21_NEEDLE) {
  if (json?.summary?.passed === true) {
    throw new Error("confirmed export flipped summary.passed — HITL must not write the verdict");
  }
  const review = reviewProjection(json);
  if (review?.state !== "accepted") {
    throw new Error(`confirmed review.state should be accepted, got ${JSON.stringify(review)}`);
  }
  if (!String(review.effective_text ?? "").includes(needle)) {
    throw new Error("confirmed JSON missing saved expert text in review.effective_text");
  }
  if (!review.actor || !review.event_id) {
    throw new Error("confirmed review is missing actor or event_id");
  }
  assertNoFalseFixed("confirmed json", JSON.stringify(json));
}

/**
 * Read local-file ZIP entries (STORE / DEFLATE). Data-descriptor zips are
 * rejected so a silent miss cannot pass OA-21.
 */
export function zipLocalEntries(buffer) {
  const bytes = Buffer.isBuffer(buffer) ? buffer : Buffer.from(buffer);
  const entries = [];
  let offset = 0;
  while (offset + 30 <= bytes.length) {
    const signature = bytes.readUInt32LE(offset);
    if (signature !== 0x04034b50) {
      break;
    }
    const flags = bytes.readUInt16LE(offset + 6);
    const method = bytes.readUInt16LE(offset + 8);
    const compressedSize = bytes.readUInt32LE(offset + 18);
    const nameLen = bytes.readUInt16LE(offset + 26);
    const extraLen = bytes.readUInt16LE(offset + 28);
    const name = bytes.subarray(offset + 30, offset + 30 + nameLen).toString("utf8");
    if (flags & 0x8) {
      throw new Error(`zip data descriptor not supported: ${name}`);
    }
    const dataStart = offset + 30 + nameLen + extraLen;
    const compressed = bytes.subarray(dataStart, dataStart + compressedSize);
    let data;
    if (compressedSize === 0) {
      data = Buffer.alloc(0);
    } else if (method === 0) {
      data = Buffer.from(compressed);
    } else if (method === 8) {
      data = inflateRawSync(compressed);
    } else {
      throw new Error(`zip method ${method} unsupported for ${name}`);
    }
    entries.push({ name, bytes: data, text: data.toString("utf8") });
    offset = dataStart + compressedSize;
  }
  if (entries.length === 0) {
    throw new Error("BCF zip contained no local file entries");
  }
  return entries;
}

export function bcfMarkupText(bcfBytes) {
  const entries = zipLocalEntries(bcfBytes);
  const markup = entries.filter((entry) => entry.name.endsWith("markup.bcf"));
  if (markup.length === 0) {
    throw new Error("BCF zip has no markup.bcf");
  }
  return markup.map((entry) => entry.text).join("\n");
}

export function inspectExportBundle({ json, html, bcfBytes, pdfBytes, phase, needle = OA21_NEEDLE }) {
  const bcfText = bcfMarkupText(bcfBytes);
  assertNoFalseFixed(`${phase} html`, html);
  assertNoFalseFixed(`${phase} bcf`, bcfText);
  if (!pdfBytes || pdfBytes.length < 64) {
    throw new Error(`${phase} PDF is missing or empty`);
  }
  assertNoFalseFixed(`${phase} pdf-utf8-bytes`, Buffer.from(pdfBytes).toString("utf8"));

  if (phase === "draft") {
    assertDraftReview(json, needle);
    if (html.includes(needle)) {
      throw new Error("unsaved draft leaked into HTML export");
    }
    if (bcfText.includes(needle)) {
      throw new Error("unsaved draft leaked into BCF export");
    }
  } else if (phase === "confirmed") {
    assertAcceptedReview(json, needle);
    if (!html.includes(needle)) {
      throw new Error("confirmed HTML missing saved expert text");
    }
    if (!html.includes("state=accepted")) {
      throw new Error("confirmed HTML missing state=accepted");
    }
    if (!bcfText.includes(needle)) {
      throw new Error("confirmed BCF missing saved expert text");
    }
  } else {
    throw new Error(`unknown export phase ${phase}`);
  }

  return {
    phase,
    pdfBytes: pdfBytes.length,
    jsonPassed: json?.summary?.passed === true,
    reviewState: reviewProjection(json)?.state ?? null,
  };
}

/**
 * FE-CRUFT-02: the unsaved-card warning is now an in-app dialog, so the
 * rehearsal reads it instead of intercepting a browser modal.
 *
 * Absence of the dialog is not an error here: on a saved card the shell must
 * not ask anything at all. Whether the warning was required is decided by the
 * caller through assertUnsavedDialogs, exactly as before.
 */
export async function settleUnsavedExportDialog(page, messages = [], { timeout = 2_000 } = {}) {
  const dialog = page.getByTestId(EXPORT_UNSAVED_DIALOG);
  try {
    await dialog.waitFor({ state: "visible", timeout });
  } catch {
    return null;
  }
  const message = ((await dialog.getByTestId(EXPORT_UNSAVED_MESSAGE).textContent()) ?? "").trim();
  messages.push(message);
  await dialog.getByRole("button", { name: EXPORT_UNSAVED_CONTINUE, exact: true }).click();
  await dialog.waitFor({ state: "hidden", timeout: 15_000 });
  return message;
}

/**
 * Native modals cannot be styled, cannot be labelled and print the bench origin
 * in the window title. After FE-CRUFT-02 any of them is a rehearsal failure,
 * not an expected step of the scenario.
 */
export function assertNoNativeDialogs(messages) {
  if (messages.length > 0) {
    throw new Error(`shell raised a native browser dialog: ${JSON.stringify(messages)}`);
  }
}

export async function downloadNamedExport(page, { name, target, unsavedMessages }) {
  const button = page.getByTestId("export-actions").getByRole("button", {
    name,
    exact: typeof name === "string",
  });
  const downloadPromise = page.waitForEvent("download", { timeout: 30_000 });
  await button.click();
  await settleUnsavedExportDialog(page, unsavedMessages ?? []);
  const download = await downloadPromise;
  await download.saveAs(target);
  const errorBanner = page.getByTestId("export-error");
  if ((await errorBanner.count()) > 0) {
    throw new Error(`Export reported a failure: ${await errorBanner.first().textContent()}`);
  }
  return target;
}

export async function captureExportBundle(page, dir, tag, { unsavedMessages } = {}) {
  const jsonPath = path.join(dir, `export-${tag}.json`);
  const htmlPath = path.join(dir, `export-${tag}.html`);
  const bcfPath = path.join(dir, `export-${tag}.bcfzip`);
  const pdfPath = path.join(dir, `export-${tag}.pdf`);
  await downloadNamedExport(page, { name: "JSON", target: jsonPath, unsavedMessages });
  await downloadNamedExport(page, { name: "HTML", target: htmlPath, unsavedMessages });
  await downloadNamedExport(page, { name: "BCF", target: bcfPath, unsavedMessages });
  await downloadNamedExport(page, { name: /PDF/, target: pdfPath, unsavedMessages });
  const json = JSON.parse(await readFile(jsonPath, "utf8"));
  const html = await readFile(htmlPath, "utf8");
  const bcfBytes = await readFile(bcfPath);
  const pdfBytes = await readFile(pdfPath);
  return { json, html, bcfBytes, pdfBytes, jsonPath, htmlPath, bcfPath, pdfPath };
}

export async function assertForcedLight(page) {
  const scheme = await page.evaluate(() => getComputedStyle(document.documentElement).colorScheme);
  if (!/^light\b/i.test(String(scheme)) || /\bdark\b/i.test(String(scheme))) {
    throw new Error(`expected forced light color-scheme under dark OS, got ${JSON.stringify(scheme)}`);
  }
  return scheme;
}

export async function waitForViewerReady(page, timeout = 45_000) {
  const ready = page.locator(".viewer-status-ready");
  const error = page.locator(".viewer-status-error");
  await Promise.race([
    ready.waitFor({ state: "visible", timeout }),
    error.waitFor({ state: "visible", timeout }),
  ]);
  if ((await error.count()) > 0) {
    throw new Error(`IFC viewer failed: ${(await error.textContent())?.trim() ?? "error"}`);
  }
  if ((await ready.count()) === 0) {
    throw new Error("IFC viewer did not become ready");
  }
  return { status: COPY.viewerReady };
}

export async function assertNoXlsx(page) {
  const xlsx = page.getByTestId("export-actions").getByRole("button", { name: /XLSX/ });
  if ((await xlsx.count()) !== 0) {
    throw new Error("XLSX must not render at all (no endpoint, not MVP)");
  }
}

export async function assertDemoSeedButton(page) {
  const panel = page.getByTestId("demo-fixture-panel");
  await panel.waitFor({ state: "visible", timeout: 15_000 });
  await page.getByRole("button", { name: COPY.demoSeed }).waitFor({ state: "visible" });
}

export async function assertHonestyOnExpertScreen(page, { expectDemo = true } = {}) {
  const training = page.getByTestId("training-rules-banner");
  await training.waitFor({ state: "visible", timeout: 15_000 });
  const trainingText = (await training.textContent()) ?? "";
  if (!trainingText.includes(COPY.trainingNeedle)) {
    throw new Error(`training banner missing honesty needle, got: ${trainingText}`);
  }

  const split = page.getByTestId("machine-human-split");
  await split.waitFor({ state: "visible", timeout: 15_000 });
  const splitText = (await split.textContent()) ?? "";
  if (!splitText.includes(COPY.engineFlagNeedle)) {
    throw new Error("machine/human strip missing engine-flag honesty");
  }
  const passBadge = split.locator(".outcome-badge.outcome-pass");
  if ((await passBadge.count()) > 0) {
    throw new Error("fixture must not show a pass badge");
  }

  const role = page.getByTestId("role-honesty-banner");
  await role.waitFor({ state: "visible" });
  const roleText = (await role.textContent()) ?? "";
  if (!roleText.includes(COPY.roleBannerNeedle)) {
    throw new Error(`role banner missing honesty needle, got: ${roleText}`);
  }

  const rehearsal = page.getByTestId("rehearsal-one-click");
  await rehearsal.waitFor({ state: "visible" });
  const rehearsalText = (await rehearsal.textContent()) ?? "";
  if (!rehearsalText.includes(COPY.rehearsalNeedle)) {
    throw new Error("rehearsal one-click copy missing");
  }

  const exportBar = page.getByTestId("export-actions");
  await exportBar.waitFor({ state: "visible", timeout: 15_000 });
  const exportText = (await exportBar.textContent()) ?? "";
  if (!exportText.includes(COPY.pdfHintNeedle)) {
    throw new Error("PDF coverage-draft hint missing from export bar");
  }
  await assertNoXlsx(page);
  if (expectDemo) {
    await assertDemoSeedButton(page);
  }

  return {
    training: trainingText.trim(),
    outcome: ((await split.locator(".outcome-badge").first().textContent()) ?? "").trim(),
    demoVisible: expectDemo,
  };
}

export async function exerciseTriageKeys(page) {
  const findingsHeading = page.getByTestId("expert-findings-pane").getByRole("heading");
  await findingsHeading.click();
  await page.keyboard.press("j");
  await page.keyboard.press("k");
  await page.getByRole("button", { name: COPY.keyboardHelp }).click();
  const helpTitle = page.getByRole("heading", { name: COPY.keyboardHelpTitle });
  await helpTitle.waitFor({ state: "visible" });
  await page.keyboard.press("Escape");
  try {
    await helpTitle.waitFor({ state: "hidden", timeout: 3_000 });
  } catch {
    await page.getByRole("button", { name: "Закрыть" }).click();
    await helpTitle.waitFor({ state: "hidden", timeout: 5_000 });
  }
  await findingsHeading.click();
  await page.keyboard.press("e");
  const focused = await page.evaluate(() => document.activeElement?.id);
  if (focused !== "remark-editor") {
    throw new Error(`E should focus #remark-editor, got ${JSON.stringify(focused)}`);
  }
  return { help: COPY.keyboardHelpTitle, editorFocused: true };
}

export function assertUnsavedDialogs(messages) {
  if (messages.length === 0) {
    throw new Error("dirty export did not raise the unsaved-card warning");
  }
  const mismatch = messages.filter((message) => message !== EXPORT_UNSAVED_CONFIRM);
  if (mismatch.length > 0) {
    throw new Error(`unsaved confirm copy drifted: ${JSON.stringify(mismatch)}`);
  }
}

export function assertDemoSeedPayload(body) {
  if (!body || typeof body !== "object") {
    throw new Error("demo seed returned an empty body");
  }
  if (body.fixture !== true) {
    throw new Error("demo seed missing fixture:true");
  }
  if (body.closes_rt001 !== false || body.closes_rt002 !== false || body.closes_rt003 !== false) {
    throw new Error("demo seed must keep RT-001/002/003 open");
  }
  if (body.report_id === SMOKE_REPORT_ID) {
    throw new Error("demo seed reused the overlay fixture id — POST did not analyze");
  }
  if (!/^[a-f0-9]{32}$/.test(String(body.report_id ?? ""))) {
    throw new Error(`demo seed report_id is not a report id: ${JSON.stringify(body.report_id)}`);
  }
  if (!Number.isInteger(body.issue_count) || body.issue_count < 1) {
    throw new Error("demo seed must produce at least one finding");
  }
  return body;
}
