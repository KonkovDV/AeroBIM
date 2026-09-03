import { useState, type DragEvent } from "react";
import { UI_COPY } from "../lib/ui-copy";
import { useUploads } from "../hooks/useUploads";

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
  const { status, detail, progress, honesty, startFile, cancel } = useUploads({ onUploadedPath });
  const [dragging, setDragging] = useState(false);

  function onDrop(event: DragEvent<HTMLDivElement>): void {
    event.preventDefault();
    setDragging(false);
    void startFile(event.dataTransfer.files?.[0]);
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
              void startFile(event.target.files?.[0]);
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
          <button type="button" className="toolbar-button" aria-label={UI_COPY.cancelUpload} onClick={cancel}>
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
