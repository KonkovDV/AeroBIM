import { useRef, useState, type DragEvent } from "react";
import { uploadDocument } from "../lib/api";
import { UI_COPY } from "../lib/ui-copy";
import { detectPackKind, packKindHonesty, packKindVerdict } from "../lib/pack-kind";

export type PackUploadPanelProps = {
  onUploadedPath?: (path: string, filename: string) => void;
  onContinueToRun?: () => void;
  /** HD14-FE-01: slot replacement / not-in-draft. Not a pack-processed claim. */
  draftApplyNote?: string | null;
};

export default function PackUploadPanel({
  onUploadedPath,
  onContinueToRun,
  draftApplyNote,
}: PackUploadPanelProps) {
  const [honesty, setHonesty] = useState<string | null>(null);
  const [status, setStatus] = useState<"idle" | "blocked" | "uploading" | "ok" | "failed">(
    "idle",
  );
  const [detail, setDetail] = useState<string | null>(null);
  const [progress, setProgress] = useState<number | null>(null);
  const [dragging, setDragging] = useState(false);
  const abortRef = useRef<AbortController | null>(null);

  async function onFile(file: File | undefined): Promise<void> {
    if (!file) {
      return;
    }
    const kind = detectPackKind(file.name);
    const message = packKindHonesty(kind);
    setHonesty(message);
    if (packKindVerdict(kind) === "fail_closed") {
      setStatus("blocked");
      setDetail(UI_COPY.failClosedBefore(file.name));
      setProgress(null);
      return;
    }
    setStatus("uploading");
    setDetail(null);
    setProgress(0);
    const controller = new AbortController();
    abortRef.current = controller;
    try {
      const result = await uploadDocument(file, {
        onProgress: (percent) => setProgress(percent),
        signal: controller.signal,
      });
      setStatus("ok");
      setProgress(100);
      setDetail(`${result.filename} → ${result.path}`);
      onUploadedPath?.(result.path, result.filename);
    } catch (error: unknown) {
      setStatus("failed");
      setProgress(null);
      setDetail(error instanceof Error ? error.message : UI_COPY.uploadFailed);
    } finally {
      abortRef.current = null;
    }
  }

  function cancelUpload(): void {
    abortRef.current?.abort();
  }

  function onDrop(event: DragEvent<HTMLDivElement>): void {
    event.preventDefault();
    setDragging(false);
    void onFile(event.dataTransfer.files?.[0]);
  }

  return (
    <section className="panel upload-panel" data-testid="pack-upload-panel">
      <div className="panel-header">
        <div>
          <p className="panel-kicker">{UI_COPY.uploadKicker}</p>
          <h2>{UI_COPY.uploadTitle}</h2>
        </div>
      </div>
      <p className="compact-copy">{UI_COPY.uploadHint}</p>
      <div
        className={`pack-dropzone ${dragging ? "dragging" : ""}`}
        data-testid="pack-dropzone"
        onDragEnter={(event) => {
          event.preventDefault();
          setDragging(true);
        }}
        onDragOver={(event) => {
          event.preventDefault();
          setDragging(true);
        }}
        onDragLeave={(event) => {
          event.preventDefault();
          setDragging(false);
        }}
        onDrop={onDrop}
      >
        <p>{UI_COPY.dropHint}</p>
        <label className="toolbar-button preset-file-upload">
          {UI_COPY.chooseFile}
          <input
            type="file"
            aria-label={UI_COPY.packFileUpload}
            onChange={(event) => {
              void onFile(event.target.files?.[0]);
              event.target.value = "";
            }}
          />
        </label>
      </div>
      {status === "uploading" && progress !== null ? (
        <p className="compact-copy" data-testid="upload-progress" role="status">
          {UI_COPY.uploading} {progress}%
          <progress max={100} value={progress} aria-label={UI_COPY.uploadProgress}>
            {progress}%
          </progress>
          <button type="button" className="toolbar-button" aria-label={UI_COPY.cancelUpload} onClick={cancelUpload}>
            {UI_COPY.cancelUpload}
          </button>
        </p>
      ) : null}
      {honesty ? (
        <p className="upload-honesty" role="status" data-testid="pack-kind-honesty">
          {honesty}
        </p>
      ) : null}
      {draftApplyNote ? (
        <p className="pack-draft-apply-note" role="status" data-testid="pack-draft-apply-note">
          {draftApplyNote}
        </p>
      ) : null}
      {status === "uploading" && progress === null ? <p className="compact-copy">{UI_COPY.uploading}</p> : null}
      {status === "ok" ? (
        <p className="compact-copy">
          Файл принят. Путь для анализа, не «пакет обработан».
          {onContinueToRun ? (
            <>
              {" "}
              <button type="button" className="toolbar-button" onClick={onContinueToRun}>
                К прогону
              </button>
            </>
          ) : null}
        </p>
      ) : null}
      {detail ? <p className="compact-copy">{detail}</p> : null}
    </section>
  );
}
