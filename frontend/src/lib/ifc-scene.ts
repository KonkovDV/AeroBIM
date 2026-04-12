import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import { IfcAPI, type FlatMesh, type PlacedGeometry } from "web-ifc";
import webIfcWasmUrl from "web-ifc/web-ifc.wasm?url";

function getVertexStride(vertices: Float32Array, indices: Uint32Array): number {
  if (indices.length === 0) {
    return 6;
  }
  const vertexCount = Math.max(...indices) + 1;
  const stride = vertices.length / vertexCount;
  return Number.isInteger(stride) && stride >= 3 ? stride : 6;
}

function expandSelectionBox(meshes: THREE.Mesh[]): THREE.Box3 {
  const box = new THREE.Box3();
  for (const mesh of meshes) {
    box.expandByObject(mesh);
  }
  return box;
}

export class IfcSceneController {
  private readonly container: HTMLElement;
  private readonly renderer: THREE.WebGLRenderer;
  private readonly scene: THREE.Scene;
  private readonly camera: THREE.PerspectiveCamera;
  private readonly controls: OrbitControls;
  private readonly modelRoot = new THREE.Group();
  private readonly resizeObserver: ResizeObserver;
  private animationHandle: number | null = null;
  private ifcApi: IfcAPI | null = null;
  private modelId: number | null = null;
  private highlightedExpressId: number | null = null;
  private isolateSelection = false;
  private readonly expressMeshes = new Map<number, THREE.Mesh[]>();

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
    this.controls.enableDamping = true;
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

  async init(): Promise<void> {
    if (this.ifcApi !== null) {
      return;
    }
    const ifcApi = new IfcAPI();
    await ifcApi.Init((path, prefix) => (path.endsWith(".wasm") ? webIfcWasmUrl : `${prefix}${path}`), true);
    this.ifcApi = ifcApi;
    this.startRenderLoop();
  }

  async loadModel(ifcBytes: Uint8Array): Promise<void> {
    await this.init();
    this.clearModel();

    const ifcApi = this.ifcApi;
    if (ifcApi === null) {
      throw new Error("IFC API was not initialized.");
    }

    const modelId = ifcApi.OpenModel(ifcBytes, {
      COORDINATE_TO_ORIGIN: true,
      MEMORY_LIMIT: 1024 * 1024 * 1024,
    });
    if (modelId < 0) {
      throw new Error("web-ifc failed to open the selected model.");
    }
    this.modelId = modelId;

    ifcApi.StreamAllMeshes(modelId, (flatMesh) => {
      this.addFlatMesh(modelId, flatMesh);
      flatMesh.delete();
    });

    this.fitCameraToBox(new THREE.Box3().setFromObject(this.modelRoot));
  }

  clearModel(): void {
    if (this.ifcApi !== null && this.modelId !== null) {
      this.ifcApi.CloseModel(this.modelId);
    }
    this.modelId = null;
    this.highlightedExpressId = null;
    this.isolateSelection = false;
    this.expressMeshes.clear();

    for (const child of [...this.modelRoot.children]) {
      this.disposeObject(child);
      this.modelRoot.remove(child);
    }
  }

  highlightGuid(guid: string | null): void {
    if (this.ifcApi === null || this.modelId === null || guid === null) {
      this.highlightedExpressId = null;
      this.applySelectionState();
      return;
    }
    const expressId = this.ifcApi.GetExpressIdFromGuid(this.modelId, guid);
    this.highlightedExpressId = typeof expressId === "number" ? expressId : null;
    this.applySelectionState();
    if (this.highlightedExpressId !== null) {
      this.frameExpressId(this.highlightedExpressId);
    }
  }

  setIsolateSelection(isolate: boolean): void {
    this.isolateSelection = isolate;
    this.applySelectionState();
  }

  resetView(): void {
    if (this.highlightedExpressId !== null) {
      this.frameExpressId(this.highlightedExpressId);
      return;
    }
    this.fitCameraToBox(new THREE.Box3().setFromObject(this.modelRoot));
  }

  dispose(): void {
    this.clearModel();
    this.stopRenderLoop();
    this.resizeObserver.disconnect();
    this.controls.dispose();
    this.renderer.dispose();
    this.container.removeChild(this.renderer.domElement);
    if (this.ifcApi !== null) {
      this.ifcApi.Dispose();
      this.ifcApi = null;
    }
  }

  private addFlatMesh(modelId: number, flatMesh: FlatMesh): void {
    const placedGeometries = flatMesh.geometries;
    const expressId = flatMesh.expressID;

    for (let index = 0; index < placedGeometries.size(); index += 1) {
      const placedGeometry = placedGeometries.get(index);
      const mesh = this.createMeshFromGeometry(modelId, expressId, placedGeometry);
      this.modelRoot.add(mesh);

      const existingMeshes = this.expressMeshes.get(expressId) ?? [];
      existingMeshes.push(mesh);
      this.expressMeshes.set(expressId, existingMeshes);
    }
  }

  private createMeshFromGeometry(modelId: number, expressId: number, placedGeometry: PlacedGeometry): THREE.Mesh {
    const ifcApi = this.ifcApi;
    if (ifcApi === null) {
      throw new Error("IFC API is unavailable during geometry creation.");
    }

    const ifcGeometry = ifcApi.GetGeometry(modelId, placedGeometry.geometryExpressID);
    const vertices = ifcApi.GetVertexArray(ifcGeometry.GetVertexData(), ifcGeometry.GetVertexDataSize());
    const indices = ifcApi.GetIndexArray(ifcGeometry.GetIndexData(), ifcGeometry.GetIndexDataSize());
    const stride = getVertexStride(vertices, indices);
    const vertexCount = Math.floor(vertices.length / stride);

    const positions = new Float32Array(vertexCount * 3);
    const normals = new Float32Array(vertexCount * 3);
    for (let vertexIndex = 0; vertexIndex < vertexCount; vertexIndex += 1) {
      const sourceOffset = vertexIndex * stride;
      const targetOffset = vertexIndex * 3;
      positions[targetOffset] = vertices[sourceOffset];
      positions[targetOffset + 1] = vertices[sourceOffset + 1];
      positions[targetOffset + 2] = vertices[sourceOffset + 2];
      if (stride >= 6) {
        normals[targetOffset] = vertices[sourceOffset + 3];
        normals[targetOffset + 1] = vertices[sourceOffset + 4];
        normals[targetOffset + 2] = vertices[sourceOffset + 5];
      }
    }

    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute("position", new THREE.BufferAttribute(positions, 3));
    if (stride >= 6) {
      geometry.setAttribute("normal", new THREE.BufferAttribute(normals, 3));
    } else {
      geometry.computeVertexNormals();
    }
    geometry.setIndex(new THREE.BufferAttribute(indices, 1));

    const baseColor = new THREE.Color(placedGeometry.color.x, placedGeometry.color.y, placedGeometry.color.z);
    const material = new THREE.MeshStandardMaterial({
      color: baseColor,
      transparent: placedGeometry.color.w < 1,
      opacity: placedGeometry.color.w,
      metalness: 0.05,
      roughness: 0.9,
      side: THREE.DoubleSide,
    });

    const mesh = new THREE.Mesh(geometry, material);
    const matrix = new THREE.Matrix4();
    matrix.fromArray(placedGeometry.flatTransformation);
    mesh.matrix.copy(matrix);
    mesh.matrixAutoUpdate = false;
    mesh.userData = {
      expressId,
      baseColor,
    };

    ifcGeometry.delete();
    return mesh;
  }

  private applySelectionState(): void {
    for (const [expressId, meshes] of this.expressMeshes) {
      const isSelected = this.highlightedExpressId !== null && expressId === this.highlightedExpressId;
      for (const mesh of meshes) {
        const material = mesh.material as THREE.MeshStandardMaterial;
        const baseColor = mesh.userData.baseColor as THREE.Color;
        material.color.copy(baseColor);
        material.emissive.set(isSelected ? "#f59e0b" : "#000000");
        material.emissiveIntensity = isSelected ? 0.55 : 0;
        mesh.visible = !this.isolateSelection || this.highlightedExpressId === null || isSelected;
      }
    }
  }

  private frameExpressId(expressId: number): void {
    const meshes = this.expressMeshes.get(expressId);
    if (meshes === undefined || meshes.length === 0) {
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
    const distance = (maxDimension * 1.5) / Math.tan((Math.PI * this.camera.fov) / 360);
    const direction = new THREE.Vector3(1, 0.85, 1).normalize();

    this.camera.position.copy(center.clone().add(direction.multiplyScalar(distance)));
    this.camera.near = Math.max(distance / 1000, 0.1);
    this.camera.far = Math.max(distance * 20, 1000);
    this.camera.updateProjectionMatrix();
    this.controls.target.copy(center);
    this.controls.update();
  }

  private startRenderLoop(): void {
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