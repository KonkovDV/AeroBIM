/**
 * IFC Parser Worker — shared message protocol types.
 *
 * Messages main thread → worker : WorkerInMsg subtypes.
 * Messages worker → main thread : WorkerOutMsg subtypes.
 *
 * Geometry buffers in MESH_BATCH are Transferable and are moved (zero-copy)
 * from the worker to the main thread via postMessage transfer list.
 */

import type { IfcElementProps, IfcStoreyOption } from "./ifc-element-props";

export type { IfcElementProps, IfcStoreyOption };

// ─── Main → Worker ───────────────────────────────────────────────────────────

/** Initialise IfcAPI + WASM inside the worker. */
export type WorkerInitMsg = {
  type: "INIT";
  /** URL of web-ifc.wasm — imported on the main thread and forwarded here. */
  wasmUrl: string;
};

/**
 * Open and parse an IFC file.
 * `buffer` is an ArrayBuffer **transferred** to the worker (zero-copy).
 * The caller's Uint8Array becomes detached after postMessage.
 */
export type WorkerLoadModelMsg = {
  type: "LOAD_MODEL";
  buffer: ArrayBuffer;
  /** WASM memory cap in bytes (aligned with backend default: 256 MiB). */
  memoryLimit: number;
};

/** Close the current model and free WASM memory. */
export type WorkerClearModelMsg = {
  type: "CLEAR_MODEL";
};

export type WorkerInMsg =
  | WorkerInitMsg
  | WorkerLoadModelMsg
  | WorkerClearModelMsg;

// ─── Worker → Main ───────────────────────────────────────────────────────────

/**
 * One placed geometry extracted from the IFC WASM heap.
 *
 * `positions`, `normals`, and `indices` are typed arrays whose underlying
 * ArrayBuffers are **Transferred** (not copied) when posted — the main
 * thread receives them at zero cost.
 */
export type SerializedMesh = {
  expressId: number;
  /** XYZ per vertex (Float32, transferred). */
  positions: Float32Array;
  /** NxNyNz per vertex (Float32, transferred). */
  normals: Float32Array;
  /** Triangle indices (Uint32, transferred). */
  indices: Uint32Array;
  colorR: number;
  colorG: number;
  colorB: number;
  colorA: number;
  /** Column-major 4×4 transform matrix (16 numbers). Small — not transferred. */
  flatTransformation: number[];
};

export type WorkerOutMsg =
  | { type: "INIT_OK" }
  | { type: "INIT_ERROR"; message: string }
  /**
   * Streamed geometry batch — emitted repeatedly during LOAD_MODEL.
   * Main thread should create Three.js meshes from each batch for
   * progressive rendering while the rest of the model loads.
   */
  | { type: "MESH_BATCH"; meshes: SerializedMesh[] }
  /**
   * Storey list and element→storey containment map.
   * Sent after all MESH_BATCH messages, before ELEMENT_PROPS_CACHE.
   */
  | {
      type: "SPATIAL_INDEX";
      storeys: IfcStoreyOption[];
      /** Serialised Map<expressId, storeyExpressId> as entry pairs. */
      elementToStorey: [number, number][];
    }
  /**
   * Compact element props for every geometry-bearing element.
   * Sent after SPATIAL_INDEX so storeyName can be resolved on the main
   * thread before building the cache.
   *
   * Tuple layout: [expressId, guid, typeName, name | null].
   */
  | {
      type: "ELEMENT_PROPS_CACHE";
      entries: [number, string, string, string | null][];
    }
  | { type: "LOAD_COMPLETE" }
  | { type: "LOAD_ERROR"; message: string }
  | { type: "CLEAR_OK" }
  /** Unhandled worker-side exception — should never happen in normal use. */
  | { type: "WORKER_ERROR"; message: string };
