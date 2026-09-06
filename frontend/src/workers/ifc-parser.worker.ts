/**
 * IFC Parser Web Worker (REAL-01)
 *
 * Runs web-ifc entirely off the main thread so the UI stays responsive
 * during IFC model loading. Three phases per LOAD_MODEL:
 *
 *   Phase 1 — OpenModel + StreamAllMeshes (the heavy WASM work).
 *              Geometry is batched and sent via Transferable typed arrays
 *              (zero-copy). The main thread builds Three.js meshes from
 *              each batch for progressive rendering.
 *
 *   Phase 2 — Spatial index (storey list + element→storey containment).
 *
 *   Phase 3 — Element props cache (guid/typeName/name for every element
 *              that has geometry). Sent so main-thread getElementProps()
 *              remains synchronous — no async round-trip on click/select.
 *
 * Message ordering guarantee (FIFO within a single Worker):
 *   MESH_BATCH* → SPATIAL_INDEX → ELEMENT_PROPS_CACHE → LOAD_COMPLETE
 */

/// <reference lib="webworker" />

import {
  IfcAPI,
  IFCBUILDINGSTOREY,
  IFCRELCONTAINEDINSPATIALSTRUCTURE,
} from "web-ifc";
import {
  indexContainedInStorey,
  iterateIdVector,
  unwrapString,
  type SpatialRelationLine,
} from "../lib/ifc-element-props";
import type {
  SerializedMesh,
  WorkerInMsg,
  WorkerOutMsg,
} from "../lib/ifc-worker-protocol";

// ── Constants ───────────────────────────────────────────────────────────────────

/** Flush geometry to the main thread every N placed-geometry instances. */
const MESH_BATCH_SIZE = 64;

// ── Helpers ───────────────────────────────────────────────────────────────────

/** O(n) max-scan — avoids Math.max(...spread) stack overflow on large meshes. */
function maxIndexValue(indices: Uint32Array): number {
  let max = 0;
  for (let i = 0; i < indices.length; i++) {
    if (indices[i] > max) max = indices[i];
  }
  return max;
}

/** Infer interleaved vertex stride (typically 6: xyz + nxnynz). */
function getVertexStride(vertices: Float32Array, indices: Uint32Array): number {
  if (indices.length === 0) return 6;
  const vertexCount = maxIndexValue(indices) + 1;
  const stride = vertices.length / vertexCount;
  return Number.isInteger(stride) && stride >= 3 ? stride : 6;
}

function postMsg(msg: WorkerOutMsg, transfer?: Transferable[]): void {
  if (transfer && transfer.length > 0) {
    self.postMessage(msg, transfer);
  } else {
    self.postMessage(msg);
  }
}

/**
 * Transfer a mesh batch to the main thread.
 * The underlying ArrayBuffers of positions/normals/indices are Transferred
 * (moved, not copied). The typed arrays in `batch` are detached after this call.
 */
function flushBatch(batch: SerializedMesh[]): void {
  if (batch.length === 0) return;
  const transfers: Transferable[] = [];
  for (const m of batch) {
    transfers.push(m.positions.buffer, m.normals.buffer, m.indices.buffer);
  }
  postMsg({ type: "MESH_BATCH", meshes: batch }, transfers);
}

// ── Worker state ───────────────────────────────────────────────────────────────

let ifcApi: IfcAPI | null = null;
let modelId: number | null = null;

// ── Message handler ─────────────────────────────────────────────────────────────

self.onmessage = async (event: MessageEvent<WorkerInMsg>): Promise<void> => {
  const msg = event.data;

  try {
    switch (msg.type) {
      // ── INIT ───────────────────────────────────────────────────────────────────
      case "INIT": {
        if (ifcApi !== null) {
          // Idempotent — already initialised.
          postMsg({ type: "INIT_OK" });
          return;
        }
        const api = new IfcAPI();
        await api.Init(
          (path: string, prefix: string) =>
            path.endsWith(".wasm") ? msg.wasmUrl : `${prefix}${path}`,
          /* multithreading= */ true,
        );
        ifcApi = api;
        postMsg({ type: "INIT_OK" });
        break;
      }

      // ── LOAD_MODEL ────────────────────────────────────────────────────────────
      case "LOAD_MODEL": {
        if (ifcApi === null) {
          postMsg({
            type: "LOAD_ERROR",
            message: "Worker not initialised — send INIT before LOAD_MODEL.",
          });
          return;
        }

        // Close any previously open model before starting a new one.
        if (modelId !== null) {
          try {
            ifcApi.CloseModel(modelId);
          } catch {
            /* no-op: model may already be closed */
          }
          modelId = null;
        }

        const bytes = new Uint8Array(msg.buffer);
        const id = ifcApi.OpenModel(bytes, {
          COORDINATE_TO_ORIGIN: true,
          // WASM memory cap — aligned with backend default 256 MiB (RT-ATOM-F07).
          MEMORY_LIMIT: msg.memoryLimit,
        });

        if (id < 0) {
          postMsg({
            type: "LOAD_ERROR",
            message: "web-ifc failed to open the model (OpenModel returned < 0).",
          });
          return;
        }
        modelId = id;

        // ── Phase 1: Stream geometry (the blocking WASM work) ─────────────────
        //
        // Track every expressId seen — reused in Phase 3 for the props cache.
        const allExpressIds = new Set<number>();
        let batch: SerializedMesh[] = [];

        ifcApi.StreamAllMeshes(id, (flatMesh) => {
          const expressId = flatMesh.expressID;
          allExpressIds.add(expressId);

          const geometries = flatMesh.geometries;
          for (let gi = 0; gi < geometries.size(); gi++) {
            const pg = geometries.get(gi);

            // Extract vertex and index data from the WASM heap.
            const geom = ifcApi!.GetGeometry(id, pg.geometryExpressID);
            const rawVerts = ifcApi!.GetVertexArray(
              geom.GetVertexData(),
              geom.GetVertexDataSize(),
            );
            const rawIdx = ifcApi!.GetIndexArray(
              geom.GetIndexData(),
              geom.GetIndexDataSize(),
            );

            // De-interleave XYZ + normal from the packed WASM vertex buffer.
            const stride = getVertexStride(rawVerts, rawIdx);
            const vertexCount = Math.floor(rawVerts.length / stride);
            const positions = new Float32Array(vertexCount * 3);
            const normals = new Float32Array(vertexCount * 3);

            for (let vi = 0; vi < vertexCount; vi++) {
              const src = vi * stride;
              const dst = vi * 3;
              positions[dst] = rawVerts[src];
              positions[dst + 1] = rawVerts[src + 1];
              positions[dst + 2] = rawVerts[src + 2];
              if (stride >= 6) {
                normals[dst] = rawVerts[src + 3];
                normals[dst + 1] = rawVerts[src + 4];
                normals[dst + 2] = rawVerts[src + 5];
              }
            }

            // Copy index data into a fresh Uint32Array so we own the buffer.
            const indices = new Uint32Array(rawIdx);

            batch.push({
              expressId,
              positions,    // transferred to main thread below
              normals,      // transferred to main thread below
              indices,      // transferred to main thread below
              colorR: pg.color.x,
              colorG: pg.color.y,
              colorB: pg.color.z,
              colorA: pg.color.w,
              // flatTransformation is a number[] (16 elements) — small, not transferred.
              flatTransformation: pg.flatTransformation,
            });

            geom.delete();
          }

          flatMesh.delete();

          // Flush to main thread every MESH_BATCH_SIZE instances.
          if (batch.length >= MESH_BATCH_SIZE) {
            flushBatch(batch);
            batch = [];
          }
        });

        // Flush the last partial batch.
        flushBatch(batch);

        // ── Phase 2: Spatial index (storeys + element containment) ───────────
        const storeyIds = iterateIdVector(
          ifcApi.GetLineIDsWithType(id, IFCBUILDINGSTOREY),
        );
        const storeySet = new Set(storeyIds);

        const storeys = storeyIds.map((sid) => {
          try {
            const line = ifcApi!.GetLine(id, sid) as {
              Name?: unknown;
              GlobalId?: unknown;
            };
            return {
              expressId: sid,
              name: unwrapString(line?.Name),
              guid: unwrapString(line?.GlobalId),
            };
          } catch {
            return { expressId: sid, name: null, guid: null };
          }
        });

        const relationIds = iterateIdVector(
          ifcApi.GetLineIDsWithType(id, IFCRELCONTAINEDINSPATIALSTRUCTURE),
        );
        const relations: SpatialRelationLine[] = relationIds.map((rid) => {
          try {
            return ifcApi!.GetLine(id, rid) as SpatialRelationLine;
          } catch {
            return {};
          }
        });

        const elementToStoreyMap = indexContainedInStorey(relations, storeySet);
        const elementToStorey: [number, number][] = [
          ...elementToStoreyMap.entries(),
        ];

        postMsg({ type: "SPATIAL_INDEX", storeys, elementToStorey });

        // ── Phase 3: Element props cache ───────────────────────────────────────
        //
        // Extract guid/typeName/name for every geometry-bearing element so
        // that getElementProps() on the main thread can stay synchronous.
        // We iterate only over elements seen in Phase 1 (allExpressIds),
        // not the entire IFC entity space.
        const entries: [number, string, string, string | null][] = [];

        for (const expressId of allExpressIds) {
          try {
            const typeCode = ifcApi.GetLineType(id, expressId);
            const typeName = ifcApi.GetNameFromTypeCode(typeCode) || "IFC";
            const line = ifcApi.GetLine(id, expressId) as {
              Name?: unknown;
              GlobalId?: unknown;
            };
            const guid = unwrapString(line?.GlobalId);
            if (guid === null) continue; // elements without GlobalId are not selectable by GUID
            const name = unwrapString(line?.Name);
            entries.push([expressId, guid, typeName, name]);
          } catch {
            // Silently skip elements that fail to deserialise.
            // A partial cache is acceptable — props show as null for missing entries.
          }
        }

        postMsg({ type: "ELEMENT_PROPS_CACHE", entries });

        // ── Done ───────────────────────────────────────────────────────────────────
        postMsg({ type: "LOAD_COMPLETE" });
        break;
      }

      // ── CLEAR_MODEL ────────────────────────────────────────────────────────────
      case "CLEAR_MODEL": {
        if (ifcApi !== null && modelId !== null) {
          try {
            ifcApi.CloseModel(modelId);
          } catch {
            /* no-op */
          }
        }
        modelId = null;
        postMsg({ type: "CLEAR_OK" });
        break;
      }

      default: {
        // TypeScript exhaustive check — `msg` is narrowed to `never` here.
        const _exhaustive: never = msg;
        postMsg({
          type: "WORKER_ERROR",
          message: `Unknown worker message type: ${JSON.stringify(_exhaustive)}`,
        });
      }
    }
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    postMsg({ type: "WORKER_ERROR", message });
  }
};
