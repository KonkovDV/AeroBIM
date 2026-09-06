import { useCallback, useRef, useState } from "react";
import { uploadDocument } from "../lib/api";
import { detectPackKind, packKindHonesty, packKindVerdict } from "../lib/pack-kind";
import { UI_COPY } from "../lib/ui-copy";

export type UploadStatus = "idle" | "blocked" | "uploading" | "ok" | "failed";

export type UploadsState = {
  status: UploadStatus;
  detail: string | null;
  progress: number | null;
  honesty: string | null;
  startFile: (file: File | undefined) => Promise<void>;
  cancel: () => void;
};

/** Загрузка файла комплекта: fail-closed детект по типу, XHR с прогрессом, отмена. */
export function useUploads(options?: {
  onUploadedPath?: (path: string, filename: string) => void;
}): UploadsState {
  const [honesty, setHonesty] = useState<string | null>(null);
  const [status, setStatus] = useState<UploadStatus>("idle");
  const [detail, setDetail] = useState<string | null>(null);
  const [progress, setProgress] = useState<number | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  /**
   * Защита от второго startFile поверх первого. Без неё повторный бросок файла
   * запускал второй XHR, перезаписывал abortRef и делал первую загрузку
   * неотменяемой: «Отменить загрузку» останавливала только последнюю.
   */
  const inFlight = useRef(false);
  const onUploadedPathRef = useRef(options?.onUploadedPath);
  onUploadedPathRef.current = options?.onUploadedPath;

  const startFile = useCallback(async (file: File | undefined) => {
    if (!file || inFlight.current) {
      return;
    }
    const kind = detectPackKind(file.name);
    setHonesty(packKindHonesty(kind));
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
    inFlight.current = true;
    try {
      const result = await uploadDocument(file, {
        onProgress: (percent) => setProgress(percent),
        signal: controller.signal,
      });
      setStatus("ok");
      setProgress(100);
      setDetail(`${result.filename} → ${result.path}`);
      onUploadedPathRef.current?.(result.path, result.filename);
    } catch (error: unknown) {
      if (controller.signal.aborted) {
        // Отмена эксперта — не сбой загрузки, красный текст здесь врёт.
        setStatus("idle");
        setDetail(null);
        setProgress(null);
        return;
      }
      setStatus("failed");
      setProgress(null);
      setDetail(error instanceof Error ? error.message : UI_COPY.uploadFailed);
    } finally {
      inFlight.current = false;
      abortRef.current = null;
    }
  }, []);

  const cancel = useCallback(() => {
    abortRef.current?.abort();
  }, []);

  return { status, detail, progress, honesty, startFile, cancel };
}
