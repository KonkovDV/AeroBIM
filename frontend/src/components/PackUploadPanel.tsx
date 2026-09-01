import { useState, type DragEvent } from "react";
import { uploadDocument } from "../lib/api";
import { detectPackKind, packKindHonesty, packKindVerdict } from "../lib/pack-kind";

export type PackUploadPanelProps = {
  onUploadedPath?: (path: string, filename: string) => void;
};

export default function PackUploadPanel({ onUploadedPath }: PackUploadPanelProps) {
  const [honesty, setHonesty] = useState<string | null>(null);
  const [status, setStatus] = useState<"idle" | "blocked" | "uploading" | "ok" | "failed">(
    "idle",
  );
  const [detail, setDetail] = useState<string | null>(null);
  const [progress, setProgress] = useState<number | null>(null);
  const [dragging, setDragging] = useState(false);

  async function onFile(file: File | undefined): Promise<void> {
    if (!file) {
      return;
    }
    const kind = detectPackKind(file.name);
    const message = packKindHonesty(kind);
    setHonesty(message);
    if (packKindVerdict(kind) === "fail_closed") {
      setStatus("blocked");
      setDetail(`${file.name}: fail-closed before upload.`);
      setProgress(null);
      return;
    }
    setStatus("uploading");
    setDetail(null);
    setProgress(0);
    try {
      const result = await uploadDocument(file, {
        onProgress: (percent) => setProgress(percent),
      });
      setStatus("ok");
      setProgress(100);
      setDetail(`${result.filename} → ${result.path}`);
      onUploadedPath?.(result.path, result.filename);
    } catch (error: unknown) {
      setStatus("failed");
      setProgress(null);
      setDetail(error instanceof Error ? error.message : "Upload failed");
    }
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
          <p className="panel-kicker">Загрузка комплекта</p>
          <h2>Dropzone</h2>
        </div>
      </div>
      <p className="compact-copy">
        Обмен КТ#3: IFC + PDF/A. Office — declared fields. Native RVT/NWD/DWG/.lir — fail-closed,
        не тихий пропуск. 1,5 ГБ в браузере не разбираем. Checkpoint NO_GO.
      </p>
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
        <p>Перетащите IFC/PDF/Office сюда или выберите файл. Native RVT/NWD/DWG не уйдут на сервер.</p>
        <label className="toolbar-button preset-file-upload">
          Выбрать файл
          <input
            type="file"
            aria-label="Pack file upload"
            onChange={(event) => {
              void onFile(event.target.files?.[0]);
              event.target.value = "";
            }}
          />
        </label>
      </div>
      {status === "uploading" && progress !== null ? (
        <p className="compact-copy" data-testid="upload-progress" role="status">
          Uploading… {progress}%
          <progress max={100} value={progress} aria-label="Upload progress">
            {progress}%
          </progress>
        </p>
      ) : null}
      {honesty ? (
        <p className="upload-honesty" role="status" data-testid="pack-kind-honesty">
          {honesty}
        </p>
      ) : null}
      {status === "uploading" && progress === null ? <p className="compact-copy">Uploading…</p> : null}
      {status === "ok" ? <p className="compact-copy">Uploaded. Path is for analyze, not a pack-processed claim.</p> : null}
      {detail ? <p className="compact-copy">{detail}</p> : null}
    </section>
  );
}
