import { useEffect, useState } from "react";
import type { PresetTransferState } from "../features/reports/ReportListPanel";
import {
  persistFilterPresets,
  readPersistedFilterPresets,
  type PersistedReportFilters,
  type PresetScope,
  type ReportFilterPreset,
  normalizePresetScope,
  normalizeStatus,
} from "../lib/report-filters";

export function useFilterPresets() {
  const [filterPresets, setFilterPresets] = useState<ReportFilterPreset[]>(readPersistedFilterPresets);
  const [presetTransferState, setPresetTransferState] = useState<PresetTransferState>("idle");
  const [presetTransferDraft, setPresetTransferDraft] = useState("");
  const [presetNameDraft, setPresetNameDraft] = useState("");
  const [presetScopeDraft, setPresetScopeDraft] = useState<PresetScope>("browser");

  useEffect(() => {
    persistFilterPresets(filterPresets);
  }, [filterPresets]);

  const mergePresetPayload = (rawPayload: string): boolean => {
    const raw = rawPayload.trim();
    if (!raw) {
      return false;
    }

    try {
      const parsed = JSON.parse(raw) as Array<{
        name?: unknown;
        scope?: unknown;
        filters?: Partial<PersistedReportFilters>;
      }>;

      if (!Array.isArray(parsed)) {
        throw new Error("Preset payload must be an array");
      }

      const normalized = parsed
        .filter((entry) => typeof entry.name === "string" && entry.filters)
        .map((entry) => {
          const filters = entry.filters as Partial<PersistedReportFilters>;
          return {
            name: (entry.name as string).trim(),
            scope: normalizePresetScope(entry.scope, "browser"),
            filters: {
              project: typeof filters.project === "string" ? filters.project : "",
              discipline: typeof filters.discipline === "string" ? filters.discipline : "",
              status: normalizeStatus(filters.status),
            },
          };
        })
        .filter((entry) => entry.name.length > 0);

      if (normalized.length === 0) {
        throw new Error("Preset payload has no valid entries");
      }

      setFilterPresets((current) => {
        const merged = [...current];

        normalized.forEach((incoming) => {
          const existingIndex = merged.findIndex(
            (preset) => preset.name.toLowerCase() === incoming.name.toLowerCase(),
          );
          if (existingIndex >= 0) {
            merged[existingIndex] = {
              ...merged[existingIndex],
              name: incoming.name,
              scope: incoming.scope,
              filters: incoming.filters,
            };
            return;
          }

          merged.push({
            id: `preset-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
            name: incoming.name,
            scope: incoming.scope,
            filters: incoming.filters,
          });
        });

        return merged;
      });

      return true;
    } catch {
      return false;
    }
  };

  const saveCurrentPreset = (currentFilters: PersistedReportFilters) => {
    const name = presetNameDraft.trim();
    if (!name) {
      return;
    }

    setFilterPresets((current) => {
      const existingIndex = current.findIndex((preset) => preset.name.toLowerCase() === name.toLowerCase());
      if (existingIndex >= 0) {
        const updated = [...current];
        updated[existingIndex] = {
          ...updated[existingIndex],
          name,
          scope: presetScopeDraft,
          filters: currentFilters,
        };
        return updated;
      }

      return [
        ...current,
        {
          id: `preset-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
          name,
          scope: presetScopeDraft,
          filters: currentFilters,
        },
      ];
    });
    setPresetNameDraft("");
  };

  const removePreset = (presetId: string) => {
    setFilterPresets((current) => current.filter((preset) => preset.id !== presetId));
  };

  const copyPresetPayload = async () => {
    if (typeof window === "undefined" || !window.navigator.clipboard) {
      setPresetTransferState("failed");
      return;
    }

    const payload = filterPresets.map((preset) => ({
      name: preset.name,
      scope: preset.scope,
      filters: preset.filters,
    }));

    try {
      await window.navigator.clipboard.writeText(JSON.stringify(payload, null, 2));
      setPresetTransferState("exported");
    } catch {
      setPresetTransferState("failed");
    }
  };

  const downloadPresetPayload = () => {
    if (typeof window === "undefined" || filterPresets.length === 0) {
      setPresetTransferState("failed");
      return;
    }

    try {
      const payload = filterPresets.map((preset) => ({
        name: preset.name,
        scope: preset.scope,
        filters: preset.filters,
      }));
      const blob = new Blob([JSON.stringify(payload, null, 2)], {
        type: "application/json",
      });
      const objectUrl = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = objectUrl;
      anchor.download = "aerobim-report-filter-presets.json";
      document.body.appendChild(anchor);
      anchor.click();
      document.body.removeChild(anchor);
      URL.revokeObjectURL(objectUrl);
      setPresetTransferState("downloaded");
    } catch {
      setPresetTransferState("failed");
    }
  };

  const importPresetPayload = () => {
    if (!presetTransferDraft.trim()) {
      return;
    }

    const imported = mergePresetPayload(presetTransferDraft);
    if (imported) {
      setPresetTransferDraft("");
      setPresetTransferState("imported");
      return;
    }

    setPresetTransferState("failed");
  };

  const importPresetFile = async (event: { target: HTMLInputElement }) => {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }

    try {
      const raw = await file.text();
      setPresetTransferDraft(raw);
      const imported = mergePresetPayload(raw);
      setPresetTransferState(imported ? "imported" : "failed");
    } catch {
      setPresetTransferState("failed");
    } finally {
      event.target.value = "";
    }
  };

  return {
    filterPresets,
    presetTransferState,
    presetTransferDraft,
    presetNameDraft,
    presetScopeDraft,
    setPresetNameDraft,
    setPresetScopeDraft,
    setPresetTransferDraft,
    setPresetTransferState,
    saveCurrentPreset,
    removePreset,
    copyPresetPayload,
    downloadPresetPayload,
    importPresetPayload,
    importPresetFile,
  };
}
