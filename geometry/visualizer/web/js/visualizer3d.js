/**
 * visualizer3d.js - Interactive 3D WebGL Detector Visualizer for Lorenzetti.
 *
 * Built with Three.js. Renders parametric hollow cylindrical calorimeters,
 * dynamic azimuthal wedge cuts, axial longitudinal sections, and cell grid wireframes.
 */

class Visualizer3D {
  constructor(containerId) {
    this.container = document.getElementById(containerId);
    this.scene = null;
    this.camera = null;
    this.renderer = null;
    this.controls = null;
    this.axesHelper = null;

    this.volumeObjects = new Map();
    this.meshToVolumeMap = new Map();
    this.interactiveMeshes = [];

    this.globalOpacity = 0.75;
    this.wedgeAngle = 90;
    this.axialCutEnabled = false;
    this.gridVisible = true;

    this.wedgePlane1 = new THREE.Plane(new THREE.Vector3(0, -1, 0), 0);
    this.wedgePlane2 = new THREE.Plane(new THREE.Vector3(0, 1, 0), 0);
    this.axialPlane = new THREE.Plane(new THREE.Vector3(0, -1, 0), 0);

    this.activeClippingPlanes = [];

    this.colorPalette = {
      "PSB": 0x4dd0e1,
      "EMB1": 0x26a69a,
      "EMB2": 0x43a047,
      "EMB3": 0x2e7d32,
      "TileCal1": 0xffb74d,
      "TileCal2": 0xfb8c00,
      "TileCal3": 0xe65100,
      "TileExt1": 0xffa726,
      "TileExt2": 0xf57c00,
      "TileExt3": 0xd84315,
      "PSE": 0xab47bc,
      "EMEC1": 0x7e57c2,
      "EMEC2": 0x5e35b1,
      "EMEC3": 0x4527a0,
      "HEC1": 0x8d6e63,
      "HEC2": 0x6d4c41,
      "HEC3": 0x4e342e,
      "DM": 0x78909c,
      "Default": 0x607d8b
    };

    this.init();
  }

  init() {
    const width = this.container.clientWidth || window.innerWidth - 360;
    const height = this.container.clientHeight || window.innerHeight;

    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color(0x12151b);

    this.camera = new THREE.PerspectiveCamera(45, width / height, 10, 50000);
    this.camera.position.set(6500, 4800, 8000);
    this.camera.up.set(0, 1, 0);

    this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
    this.renderer.setSize(width, height);
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.localClippingEnabled = true;
    this.container.appendChild(this.renderer.domElement);

    this.controls = new THREE.OrbitControls(this.camera, this.renderer.domElement);
    this.controls.enableDamping = true;
    this.controls.dampingFactor = 0.08;
    this.controls.maxDistance = 35000;
    this.controls.minDistance = 200;

    const ambientLight = new THREE.AmbientLight(0xffffff, 0.7);
    this.scene.add(ambientLight);

    const dirLight1 = new THREE.DirectionalLight(0xffffff, 0.6);
    dirLight1.position.set(5000, 8000, 6000);
    this.scene.add(dirLight1);

    const dirLight2 = new THREE.DirectionalLight(0xffffff, 0.4);
    dirLight2.position.set(-5000, -4000, -6000);
    this.scene.add(dirLight2);

    this.axesHelper = new THREE.AxesHelper(3000);
    this.scene.add(this.axesHelper);

    this.updateClippingPlanes();

    window.addEventListener("resize", () => this.onWindowResize());
    this.animate();
  }

  onWindowResize() {
    const width = this.container.clientWidth;
    const height = this.container.clientHeight;
    this.camera.aspect = width / height;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(width, height);
  }

  animate() {
    requestAnimationFrame(() => this.animate());
    this.controls.update();
    this.renderer.render(this.scene, this.camera);
  }

  createHollowCylinderGeometry(rmin, rmax, zsize, segments = 64) {
    const geom = new THREE.BufferGeometry();
    const halfZ = zsize / 2.0;

    const positions = [];
    const indices = [];

    for (let i = 0; i <= segments; i++) {
      const phi = (i / segments) * Math.PI * 2.0;
      const cosPhi = Math.cos(phi);
      const sinPhi = Math.sin(phi);

      positions.push(rmax * cosPhi, rmax * sinPhi, halfZ);
      positions.push(rmax * cosPhi, rmax * sinPhi, -halfZ);
      positions.push(rmin * cosPhi, rmin * sinPhi, halfZ);
      positions.push(rmin * cosPhi, rmin * sinPhi, -halfZ);
    }

    const stride = 4;
    for (let i = 0; i < segments; i++) {
      const curr = i * stride;
      const next = (i + 1) * stride;

      const oT1 = curr, oB1 = curr + 1, iT1 = curr + 2, iB1 = curr + 3;
      const oT2 = next, oB2 = next + 1, iT2 = next + 2, iB2 = next + 3;

      indices.push(oT1, oB1, oB2);
      indices.push(oT1, oB2, oT2);

      indices.push(iT1, iB2, iB1);
      indices.push(iT1, iT2, iB2);

      indices.push(oT1, oT2, iT2);
      indices.push(oT1, iT2, iT1);

      indices.push(oB1, iB2, oB2);
      indices.push(oB1, iB1, iB2);
    }

    geom.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
    geom.setIndex(indices);
    geom.computeVertexNormals();

    return geom;
  }

  createCellGridLines(volData) {
    const geom = volData.geometry || {};
    const readout = volData.readout;
    if (!readout || !readout.delta_eta || !readout.delta_phi) {
      return null;
    }

    const rmax = geom.rmax;
    const zsize = geom.z_size;
    const halfZ = zsize / 2.0;
    const deta = readout.delta_eta;
    const dphi = readout.delta_phi;
    const phiShift = readout.phi_shift || 0.0;

    const linePositions = [];
    const radius = rmax + 1.0;

    const numPhi = Math.round((Math.PI * 2.0) / dphi);
    for (let j = 0; j < numPhi; j++) {
      const phi = j * dphi + phiShift;
      const x = radius * Math.cos(phi);
      const y = radius * Math.sin(phi);

      linePositions.push(x, y, -halfZ);
      linePositions.push(x, y, halfZ);
    }

    const etaMax = 3.2;
    const numEta = Math.min(Math.round(etaMax / deta), 40);
    const zStep = zsize / (numEta > 0 ? numEta : 10);

    for (let z = -halfZ; z <= halfZ; z += zStep) {
      const ringSegments = 48;
      for (let s = 0; s < ringSegments; s++) {
        const p1 = (s / ringSegments) * Math.PI * 2.0;
        const p2 = ((s + 1) / ringSegments) * Math.PI * 2.0;

        linePositions.push(radius * Math.cos(p1), radius * Math.sin(p1), z);
        linePositions.push(radius * Math.cos(p2), radius * Math.sin(p2), z);
      }
    }

    const lineGeom = new THREE.BufferGeometry();
    lineGeom.setAttribute("position", new THREE.Float32BufferAttribute(linePositions, 3));

    const lineMat = new THREE.LineBasicMaterial({
      color: 0xffffff,
      transparent: true,
      opacity: 0.35,
      clippingPlanes: this.activeClippingPlanes,
      clipIntersection: true
    });

    return new THREE.LineSegments(lineGeom, lineMat);
  }

  getColorForVolume(vol) {
    const name = vol.name || "";
    const readout = vol.readout;

    if (name.startsWith("DM::")) {
      return this.colorPalette["DM"];
    }

    if (readout && readout.sampling) {
      const samp = String(readout.sampling);
      for (const [key, color] of Object.entries(this.colorPalette)) {
        if (name.includes(key) || samp === key) {
          return color;
        }
      }
    }

    for (const [key, color] of Object.entries(this.colorPalette)) {
      if (name.includes(key)) {
        return color;
      }
    }

    return this.colorPalette["Default"];
  }

  loadGeometry(geometryData) {
    for (const obj of this.volumeObjects.values()) {
      this.scene.remove(obj.group);
    }
    this.volumeObjects.clear();
    this.meshToVolumeMap.clear();
    this.interactiveMeshes = [];

    const volumes = geometryData.volumes || [];

    volumes.forEach((vol) => {
      const name = vol.name;
      const geom = vol.geometry || {};
      const center = geom.center || [0.0, 0.0, 0.0];
      const rmin = geom.rmin || 100.0;
      const rmax = geom.rmax || 200.0;
      const zsize = geom.z_size || 1000.0;

      const group = new THREE.Group();
      group.position.set(center[0], center[1], center[2]);

      const cylinderGeom = this.createHollowCylinderGeometry(rmin, rmax, zsize, 54);
      const color = this.getColorForVolume(vol);

      const material = new THREE.MeshStandardMaterial({
        color: color,
        roughness: 0.45,
        metalness: 0.25,
        transparent: true,
        opacity: this.globalOpacity,
        side: THREE.DoubleSide,
        clippingPlanes: this.activeClippingPlanes,
        clipIntersection: true
      });

      const mesh = new THREE.Mesh(cylinderGeom, material);
      mesh.userData = { volumeName: name, volumeData: vol };
      group.add(mesh);

      this.meshToVolumeMap.set(mesh, vol);
      this.interactiveMeshes.push(mesh);

      const gridMesh = this.createCellGridLines(vol);
      if (gridMesh) {
        gridMesh.visible = this.gridVisible;
        group.add(gridMesh);
      }

      this.scene.add(group);

      this.volumeObjects.set(name, {
        group: group,
        mesh: mesh,
        gridMesh: gridMesh,
        material: material,
        color: color,
        data: vol
      });
    });
  }

  updateClippingPlanes() {
    this.activeClippingPlanes = [];

    if (this.axialCutEnabled) {
      this.axialPlane.set(new THREE.Vector3(0, -1, 0), 0);
      this.activeClippingPlanes.push(this.axialPlane);
    } else if (this.wedgeAngle > 0) {
      const rad = (this.wedgeAngle * Math.PI) / 180.0;
      this.wedgePlane1.set(new THREE.Vector3(0, -1, 0), 0);
      this.wedgePlane2.set(new THREE.Vector3(-Math.sin(rad), Math.cos(rad), 0), 0);

      this.activeClippingPlanes.push(this.wedgePlane1);
      this.activeClippingPlanes.push(this.wedgePlane2);
    }

    for (const obj of this.volumeObjects.values()) {
      obj.material.clippingPlanes = this.activeClippingPlanes;
      obj.material.clipIntersection = true;
      obj.material.needsUpdate = true;

      if (obj.gridMesh) {
        obj.gridMesh.material.clippingPlanes = this.activeClippingPlanes;
        obj.gridMesh.material.clipIntersection = true;
        obj.gridMesh.material.needsUpdate = true;
      }
    }
  }

  setWedgeCut(angleDeg) {
    this.wedgeAngle = angleDeg;
    this.updateClippingPlanes();
  }

  setAxialCut(enabled) {
    this.axialCutEnabled = enabled;
    this.updateClippingPlanes();
  }

  setGlobalOpacity(val) {
    this.globalOpacity = val;
    for (const obj of this.volumeObjects.values()) {
      obj.material.opacity = val;
      obj.material.needsUpdate = true;
    }
  }

  setGridVisible(visible) {
    this.gridVisible = visible;
    for (const obj of this.volumeObjects.values()) {
      if (obj.gridMesh) {
        obj.gridMesh.visible = visible;
      }
    }
  }

  setAxesVisible(visible) {
    if (this.axesHelper) {
      this.axesHelper.visible = visible;
    }
  }

  setVolumeVisible(volumeName, visible) {
    const obj = this.volumeObjects.get(volumeName);
    if (obj) {
      obj.group.visible = visible;
    }
  }

  setCameraView(viewType) {
    switch (viewType) {
      case "iso":
        this.camera.position.set(6500, 4800, 8000);
        this.camera.up.set(0, 1, 0);
        break;
      case "rz":
        this.camera.position.set(11000, 0, 0);
        this.camera.up.set(0, 1, 0);
        break;
      case "rphi":
        this.camera.position.set(0, 0, 11000);
        this.camera.up.set(0, 1, 0);
        break;
      case "top":
        this.camera.position.set(0, 11000, 0);
        this.camera.up.set(0, 0, -1);
        break;
      case "reset":
      default:
        this.camera.position.set(6500, 4800, 8000);
        this.camera.up.set(0, 1, 0);
        break;
    }
    this.controls.target.set(0, 0, 0);
    this.controls.update();
  }
}
