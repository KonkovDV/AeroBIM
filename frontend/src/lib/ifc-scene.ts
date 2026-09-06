/**
 * IfcSceneController — Three.js viewer controller (REAL-01 refactor).
 *
 * All web-ifc / WASM work (OpenModel, StreamAllMeshes, storey indexing,
 * element-props extraction) now runs inside ifc-parser.worker.ts.
 *
 * Main-thread responsibilities:
 *   • Three.js scene, meshes, camera, controls, ResizeObserver
 *   • Receiving geometry batches via postMessage (Transferable, zero-copy)
 *   • Synchronous GUID → expressId lookup via elementPropsCache
 *   • Selection highlight, storey filter, camera framing
 *
 * Public API is 100% backward-compatible with IfcViewerPanel.tsx:
 *   init(), loadModel(), clearModel(), setSelectedGuids(),
 *   setIsolateSelection(), listStoreys(), setStoreyFilter(),
 *   getElementProps(), resetView(), dispose()
 */

import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import webIfcWasmUrl from "web-ifc/web-ifc.wasm?url";
import { assertFitsIfcViewerCap } from "./wasm-cap";
import type {
  IfcElementProps,
  IfcStoreyOption,
} from "./ifc-element-props";
import type {
  SerializedMesh,
  WorkerInMsg,
  WorkerOutMsg,
} from "./ifc-worker-protocol";

// Vite resolves the worker URL and bundles it as a separate chunk.
// Using new URL(…) is the only form Vite understands for module workers.
const createIfcWorker = (): Worker =>
  new Worker(new URL("../workers/ifc-parser.worker.ts", import.meta.url), {
    type: "module",
  });

function expandSelectionBox(meshes: THREE.Mesh[]): THREE.Box3 {
  const box = new THREE.Box3();
  for (const mesh of meshes) {
    box.expandByObject(mesh);
  }
  return box;
}

export class IfcSceneController {
  // ─ Three.js ───────────────────────────────────────────────────────────────
  private readonly container: HTMLElement;
  private readonly renderer: THREE.WebGLRenderer;
  private readonly scene: THREE.Scene;
  private readonly camera: THREE.PerspectiveCamera;
  private readonly controls: OrbitControls;
  private readonly modelRoot = new THREE.Group();
  private readonly resizeObserver: ResizeObserver;
  private animationHandle: number | null = null;
  private readonly reducedMotion: boolean;

  // ─ Selection state ─────────────────────────────────────────────────────
  private selectedExpressIds: number[] = [];
  private isolateSelection = false;
  private readonly expressMeshes = new Map<number, THREE.Mesh[]>();
  private storeyVisibleIds: Set<number> | null = null;

  // ─ Spatial / element data (populated from Worker) ───────────────────────
  private storeys: IfcStoreyOption[] = [];
  private elementToStorey = new Map<number, number>();
  /**
   * GUID → IfcElementProps cache built during LOAD_MODEL (Phase 3).
   * Allows getElementProps() to remain synchronous after the model is loaded.
   */
  private readonly elementPropsCache = new Map<string, IfcElementProps>();

  // ─ Worker ───────────────────────────────────────────────────────────────
  private worker: Worker | null = null;
  private workerReady = false;
  private pendingInit: { resolve: () => void; reject: (e: Error) => void } | null = null;
  private pendingLoad: { resolve: () => void; reject: (e: Error) => void } | null = null;

  constructor(container: HTMLElement) {
    this.container = container;
    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color("#f4f0e8");

    this.camera = new THREE.PerspectiveCamera(52, 1, 0.1, 5000);
    this.camera.position.set(12, 10, 12);

    this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
    this.renderer.outputColorSpace = THREE.SRGBColorSpace;
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.domElement.className = "viewer-canvas";
    this.container.appendChild(this.renderer.domElement);

    this.controls = new OrbitControls(this.camera, this.renderer.domElement);
    this.reducedMotion =
      typeof window !== "undefined" &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    this.controls.enableDamping = !this.reducedMotion;
    this.controls.target.set(0, 1.5, 0);

    const ambientLight = new THREE.HemisphereLight("#ffffff", "#94a3b8", 1.4);
    const keyLight = new THREE.DirectionalLight("#fff7ed", 1.1);
    keyLight.position.set(12, 16, 9);
    const fillLight = new THREE.DirectionalLight("#cbd5e1", 0.45);
    fillLight.position.set(-10, 8, -6);
    const grid = new THREE.GridHelper(40, 40, "#cbd5e1", "#e2e8f0");
    grid.position.y = -0.01;

    this.scene.add(ambientLight, keyLight, fillLight, grid, this.modelRoot);

    this.resizeObserver = new ResizeObserver(() => {
      this.resize();
    });
    this.resizeObserver.observe(this.container);
    this.resize();
  }

  // ─────────────────────────────────────────────────────────────────────────────────
  // Public API
  // ─────────────────────────────────────────────────────────────────────────────────

  /**
   * Initialise the IFC Worker and WASM runtime.
   * Idempotent: safe to call multiple times. Awaits Worker INIT_OK.
   */
  async init(): Promise<void> {
    if (this.workerReady) {
      return;
    }
    await new Promise<void>((resolve, reject) => {
      this.pendingInit = { resolve, reject };
      const worker = createIfcWorker();
      this.worker = worker;

      worker.onmessage = (event: MessageEvent<WorkerOutMsg>) => {
        this.handleWorkerMessage(event.data);
      };
      worker.onerror = (event: ErrorEvent) => {
        const error = new Error(
          event.message || "IFC Worker failed to start",
        );
        this.pendingInit?.reject(error);
        this.pendingInit = null;
        this.pendingLoad?.reject(error);
        this.pendingLoad = null;
      };

      this.postWorkerMsg({ type: "INIT", wasmUrl: webIfcWasmUrl });
    });
    this.startRenderLoop();
  }

  /**
   * Load an IFC model. Transfers the ArrayBuffer to the Worker (zero-copy).
   * Resolves when LOAD_COMPLETE is received (all mesh batches + props cached).
   */
  async loadModel(ifcBytes: Uint8Array): Promise<void> {
    await this.init();
    this.clearThreeJsModel();
    assertFitsIfcViewerCap(ifcBytes.byteLength);

    // Slice to get an independently-owned buffer before transferring.
    const buffer = ifcBytes.buffer.slice(
      ifcBytes.byteOffset,
      ifcBytes.byteOffset + ifcBytes.byteLength,
    );

    return new Promise<void>((resolve, reject) => {
      this.pendingLoad = { resolve, reject };
      this.postWorkerMsg(
        { type: "LOAD_MODEL", buffer, memoryLimit: 256 * 1024 * 1024 },
        [buffer],
      );
    });
  }

  /**
   * Clear the current model.
   * Three.js state is reset synchronously; Worker CloseModel is fire-and-forget.
   */
  clearModel(): void {
    this.clearThreeJsModel();
    // Fire-and-forget — Worker handles CloseModel at the start of the next
    // LOAD_MODEL anyway, so CLEAR_MODEL is mostly for explicit idle resets.
    this.postWorkerMsg({ type: "CLEAR_MODEL" });
  }

  setSelectedGuids(guids: readonly string[]): void {
    if (guids.length === 0) {
      this.selectedExpressIds = [];
      this.applySelectionState();
      return;
    }

    const nextSelection: number[] = [];
    const seen = new Set<number>();

    for (const guid of guids) {
      // Synchronous O(1) lookup — no IfcAPI round-trip needed.
      const cached = this.elementPropsCache.get(guid);
      if (cached !== undefined && !seen.has(cached.expressId)) {
        seen.add(cached.expressId);
        nextSelection.push(cached.expressId);
      }
    }

    this.selectedExpressIds = nextSelection;
    this.applySelectionState();
    if (this.selectedExpressIds.length > 0) {
      this.frameExpressIds(this.selectedExpressIds);
    }
  }

  setIsolateSelection(isolate: boolean): void {
    this.isolateSelection = isolate;
    this.applySelectionState();
  }

  listStoreys(): IfcStoreyOption[] {
    return this.storeys;
  }

  setStoreyFilter(expressId: number | null): void {
    if (expressId === null) {
      this.storeyVisibleIds = null;
    } else {
      const visible = new Set<number>([expressId]);
      for (const [elementId, storeyId] of this.elementToStorey) {
        if (storeyId === expressId) {
          visible.add(elementId);
        }
      }
      this.storeyVisibleIds = visible;
    }
    this.applySelectionState();
  }

  /**
   * Returns element props synchronously from the in-memory cache.
   * Cache is populated during LOAD_MODEL (Worker Phase 3).
   * Returns null before the model is loaded or if GUID is unknown.
   */
  getElementProps(guid: string | null | undefined): IfcElementProps | null {
    if (!guid) {
      return null;
    }
    return this.elementPropsCache.get(guid) ?? null;
  }

  resetView(): void {
    if (this.selectedExpressIds.length > 0) {
      this.frameExpressIds(this.selectedExpressIds);
      return;
    }
    this.fitCameraToBox(new THREE.Box3().setFromObject(this.modelRoot));
  }

  dispose(): void {
    this.clearThreeJsModel();
    this.stopRenderLoop();
    this.controls.removeEventListener("change", this.renderOnce);
    this.resizeObserver.disconnect();
    this.controls.dispose();
    this.renderer.dispose();
    if (this.renderer.domElement.parentElement === this.container) {
      this.container.removeChild(this.renderer.domElement);
    }
    if (this.worker !== null) {
      this.worker.terminate();
      this.worker = null;
    }
    this.workerReady = false;
  }

  // ─────────────────────────────────────────────────────────────────────────────────
  // Private — Worker communication
  // ─────────────────────────────────────────────────────────────────────────────────

  private postWorkerMsg(msg: WorkerInMsg, transfer?: Transferable[]): void {
    if (this.worker === null) return;
    if (transfer && transfer.length > 0) {
      this.worker.postMessage(msg, transfer);
    } else {
      this.worker.postMessage(msg);
    }
  }

  private handleWorkerMessage(msg: WorkerOutMsg): void {
    switch (msg.type) {
      case "INIT_OK":
        this.workerReady = true;
        this.pendingInit?.resolve();
        this.pendingInit = null;
        break;

      case "INIT_ERROR": {
        const initErr = new Error(msg.message);
        this.pendingInit?.reject(initErr);
        this.pendingInit = null;
        break;
      }

      case "MESH_BATCH":
        for (const serialized of msg.meshes) {
          this.addSerializedMesh(serialized);
        }
        // Render after each batch for progressive display.
        this.renderOnce();
        break;

      case "SPATIAL_INDEX":
        this.storeys = msg.storeys;
        this.elementToStorey = new Map(msg.elementToStorey);
        break;

      case "ELEMENT_PROPS_CACHE": {
        this.elementPropsCache.clear();
        for (const [expressId, guid, typeName, name] of msg.entries) {
          const storeyId = this.elementToStorey.get(expressId) ?? null;
          const storey =
            storeyId === null
              ? null
              : (this.storeys.find((s) => s.expressId === storeyId) ?? null);
          this.elementPropsCache.set(guid, {
            guid,
            expressId,
            typeName: typeName || "IFC",
            name,
            storeyName: storey?.name ?? null,
          });
        }
        break;
      }

      case "LOAD_COMPLETE":
        this.fitCameraToBox(new THREE.Box3().setFromObject(this.modelRoot));
        this.pendingLoad?.resolve();
        this.pendingLoad = null;
        break;

      case "LOAD_ERROR": {
        const loadErr = new Error(msg.message);
        this.pendingLoad?.reject(loadErr);
        this.pendingLoad = null;
        break;
      }

      case "CLEAR_OK":
        // Nothing to do — Three.js was already cleared synchronously.
        break;

      case "WORKER_ERROR": {
        const workerErr = new Error(msg.message);
        this.pendingInit?.reject(workerErr);
        this.pendingInit = null;
        this.pendingLoad?.reject(workerErr);
        this.pendingLoad = null;
        break;
      }

      default: {
        // TypeScript exhaustive check.
        const _exhaustive: never = msg;
        console.warn("[IfcSceneController] unknown worker message", _exhaustive);
      }
    }
  }

  // ─────────────────────────────────────────────────────────────────────────────────
  // Private — Three.js mesh creation from serialized Worker data
  // ─────────────────────────────────────────────────────────────────────────────────

  private addSerializedMesh(data: SerializedMesh): void {
    const {
      expressId,
      positions,
      normals,
      indices,
      colorR,
      colorG,
      colorB,
      colorA,
      flatTransformation,
    } = data;

    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute("position", new THREE.BufferAttribute(positions, 3));

    // Use transferred normals if non-zero, otherwise compute.
    if (normals.some((v) => v !== 0)) {
      geometry.setAttribute("normal", new THREE.BufferAttribute(normals, 3));
    } else {
      geometry.computeVertexNormals();
    }
    geometry.setIndex(new THREE.BufferAttribute(indices, 1));

    const baseColor = new THREE.Color(colorR, colorG, colorB);
    const material = new THREE.MeshStandardMaterial({
      color: baseColor,
      transparent: colorA < 1,
      opacity: colorA,
      metalness: 0.05,
      roughness: 0.9,
      side: THREE.DoubleSide,
    });

    const mesh = new THREE.Mesh(geometry, material);
    const matrix = new THREE.Matrix4();
    matrix.fromArray(flatTransformation);
    mesh.matrix.copy(matrix);
    mesh.matrixAutoUpdate = false;
    mesh.userData = { expressId, baseColor };

    this.modelRoot.add(mesh);

    const existing = this.expressMeshes.get(expressId) ?? [];
    existing.push(mesh);
    this.expressMeshes.set(expressId, existing);
  }

  // ─────────────────────────────────────────────────────────────────────────────────
  // Private — Three.js scene management
  // ─────────────────────────────────────────────────────────────────────────────────

  /** Synchronously clear all Three.js model state. Does NOT touch the Worker. */
  private clearThreeJsModel(): void {
    this.selectedExpressIds = [];
    this.isolateSelection = false;
    this.expressMeshes.clear();
    this.storeyVisibleIds = null;
    this.storeys = [];
    this.elementToStorey.clear();
    this.elementPropsCache.clear();

    for (const child of [...this.modelRoot.children]) {
      this.disposeObject(child);
      this.modelRoot.remove(child);
    }
  }

  private applySelectionState(): void {
    const selectionPalette = ["#f59e0b", "#0f766e", "#2563eb", "#db2777"];

    for (const [expressId, meshes] of this.expressMeshes) {
      const selectionIndex = this.selectedExpressIds.indexOf(expressId);
      const isSelected = selectionIndex >= 0;
      for (const mesh of meshes) {
        const material = mesh.material as THREE.MeshStandardMaterial;
        const baseColor = mesh.userData.baseColor as THREE.Color;
        material.color.copy(baseColor);
        material.emissive.set(
          isSelected
            ? selectionPalette[selectionIndex % selectionPalette.length]
            : "#000000",
        );
        material.emissiveIntensity = isSelected ? 0.6 : 0;
        mesh.visible = this.isMeshVisible(expressId, isSelected);
      }
    }
    this.renderOnce();
  }

  private isMeshVisible(expressId: number, isSelected: boolean): boolean {
    if (
      this.isolateSelection &&
      this.selectedExpressIds.length > 0 &&
      !isSelected
    ) {
      return false;
    }
    if (this.storeyVisibleIds === null) {
      return true;
    }
    return this.storeyVisibleIds.has(expressId);
  }

  private frameExpressIds(expressIds: readonly number[]): void {
    const meshes = expressIds.flatMap(
      (expressId) => this.expressMeshes.get(expressId) ?? [],
    );
    if (meshes.length === 0) {
      return;
    }
    this.fitCameraToBox(expandSelectionBox(meshes));
  }

  private fitCameraToBox(box: THREE.Box3): void {
    if (box.isEmpty()) {
      return;
    }
    const center = box.getCenter(new THREE.Vector3());
    const size = box.getSize(new THREE.Vector3());
    const maxDimension = Math.max(size.x, size.y, size.z, 1);
    const distance =
      (maxDimension * 1.5) / Math.tan((Math.PI * this.camera.fov) / 360);
    const direction = new THREE.Vector3(1, 0.85, 1).normalize();

    this.camera.position.copy(
      center.clone().add(direction.multiplyScalar(distance)),
    );
    this.camera.near = Math.max(distance / 1000, 0.1);
    this.camera.far = Math.max(distance * 20, 1000);
    this.camera.updateProjectionMatrix();
    this.controls.target.copy(center);
    this.controls.update();
    this.renderOnce();
  }

  private renderOnce = (): void => {
    this.renderer.render(this.scene, this.camera);
  };

  private startRenderLoop(): void {
    if (this.reducedMotion) {
      this.controls.addEventListener("change", this.renderOnce);
      this.renderOnce();
      return;
    }
    if (this.animationHandle !== null) {
      return;
    }
    const render = () => {
      this.controls.update();
      this.renderer.render(this.scene, this.camera);
      this.animationHandle = window.requestAnimationFrame(render);
    };
    render();
  }

  private stopRenderLoop(): void {
    if (this.animationHandle === null) {
      return;
    }
    window.cancelAnimationFrame(this.animationHandle);
    this.animationHandle = null;
  }

  private resize(): void {
    const width = Math.max(this.container.clientWidth, 1);
    const height = Math.max(this.container.clientHeight, 1);
    this.camera.aspect = width / height;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(width, height, false);
    this.renderOnce();
  }

  private disposeObject(object: THREE.Object3D): void {
    object.traverse((node: THREE.Object3D) => {
      if (node instanceof THREE.Mesh) {
        node.geometry.dispose();
        const material = node.material;
        if (Array.isArray(material)) {
          for (const entry of material) {
            entry.dispose();
          }
        } else {
          material.dispose();
        }
      }
    });
  }
}
