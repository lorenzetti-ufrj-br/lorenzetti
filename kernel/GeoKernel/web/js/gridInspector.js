/**
 * gridInspector.js - Volume raycasting and interactive HUD inspector for Lorenzetti Visualizer.
 */

class GridInspector {
  constructor(visualizer) {
    this.visualizer = visualizer;
    this.raycaster = new THREE.Raycaster();
    this.mouse = new THREE.Vector2();

    this.card = document.getElementById("inspector-card");
    this.closeBtn = document.getElementById("inspector-close");

    this.titleEl = document.getElementById("inspector-title");
    this.nameEl = document.getElementById("inspector-name");
    this.subdetEl = document.getElementById("inspector-subdet");
    this.samplingEl = document.getElementById("inspector-sampling");
    this.rEl = document.getElementById("inspector-r");
    this.zEl = document.getElementById("inspector-z");
    this.granularityEl = document.getElementById("inspector-granularity");
    this.noiseEl = document.getElementById("inspector-noise");
    this.materialsEl = document.getElementById("inspector-materials");

    this.hoveredMesh = null;
    this.hoveredOriginalEmissive = null;

    this.init();
  }

  init() {
    const dom = this.visualizer.renderer.domElement;

    dom.addEventListener("mousemove", (e) => this.onMouseMove(e));
    dom.addEventListener("click", (e) => this.onClick(e));

    if (this.closeBtn) {
      this.closeBtn.addEventListener("click", () => {
        this.hideCard();
      });
    }
  }

  onMouseMove(e) {
    const rect = this.visualizer.renderer.domElement.getBoundingClientRect();
    this.mouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
    this.mouse.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;

    this.raycaster.setFromCamera(this.mouse, this.visualizer.camera);
    const intersects = this.raycaster.intersectObjects(this.visualizer.interactiveMeshes);

    if (intersects.length > 0) {
      const hitMesh = intersects[0].object;
      if (this.hoveredMesh !== hitMesh) {
        this.clearHover();
        this.hoveredMesh = hitMesh;
        if (hitMesh.material && hitMesh.material.emissive) {
          this.hoveredOriginalEmissive = hitMesh.material.emissive.getHex();
          hitMesh.material.emissive.setHex(0x444444);
        }
        domTooltip(e.clientX, e.clientY, hitMesh.userData.volumeName);
      }
    } else {
      this.clearHover();
      domTooltipHide();
    }
  }

  onClick(e) {
    const rect = this.visualizer.renderer.domElement.getBoundingClientRect();
    this.mouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
    this.mouse.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;

    this.raycaster.setFromCamera(this.mouse, this.visualizer.camera);
    const intersects = this.raycaster.intersectObjects(this.visualizer.interactiveMeshes);

    if (intersects.length > 0) {
      const hit = intersects[0].object;
      this.showVolumeDetails(hit.userData.volumeData);
    }
  }

  clearHover() {
    if (this.hoveredMesh) {
      if (this.hoveredMesh.material && this.hoveredMesh.material.emissive) {
        this.hoveredMesh.material.emissive.setHex(this.hoveredOriginalEmissive || 0x000000);
      }
      this.hoveredMesh = null;
    }
  }

  showVolumeDetails(vol) {
    if (!vol) return;

    const geom = vol.geometry || {};
    const readout = vol.readout || {};
    const mats = vol.materials || {};
    const center = geom.center || [0, 0, 0];
    const zsize = geom.z_size || 0;
    const zmin = center[2] - zsize / 2.0;
    const zmax = center[2] + zsize / 2.0;

    this.nameEl.textContent = vol.name || "-";
    this.subdetEl.textContent = this.detectSubdetector(vol.name);
    this.samplingEl.textContent = readout.sampling !== undefined ? `Sampling ${readout.sampling}` : "Passive / DM";
    this.rEl.textContent = `${geom.rmin?.toFixed(1) || 0} - ${geom.rmax?.toFixed(1) || 0} mm`;
    this.zEl.textContent = `${zmin.toFixed(1)} to ${zmax.toFixed(1)} mm (\u0394Z: ${zsize.toFixed(1)} mm)`;

    if (readout.delta_eta && readout.delta_phi) {
      this.granularityEl.textContent = `${readout.delta_eta.toFixed(3)} \u00d7 ${readout.delta_phi.toFixed(4)} rad`;
    } else {
      this.granularityEl.textContent = "None (No readout)";
    }

    this.noiseEl.textContent = readout.noise ? `${readout.noise.toFixed(1)} MeV` : "N/A";
    this.materialsEl.textContent = `${mats.absorber || "-"} / ${mats.gap || "-"}`;

    if (this.card) {
      this.card.style.display = "block";
    }
  }

  hideCard() {
    if (this.card) {
      this.card.style.display = "none";
    }
  }

  detectSubdetector(name) {
    if (!name) return "Unknown";
    if (name.includes("PSB") || name.includes("EMB")) return "LAr Electromagnetic Barrel (EMB)";
    if (name.includes("PSE") || name.includes("EMEC")) return "LAr Electromagnetic Endcap (EMEC)";
    if (name.includes("TileCalExt")) return "Tile Calorimeter Extended (TILE Ext)";
    if (name.includes("TileCal")) return "Tile Calorimeter Barrel (TILE)";
    if (name.includes("HEC")) return "Hadronic Endcap Calorimeter (HEC)";
    if (name.startsWith("DM::")) return "Dead Material / Cryostat Support";
    return "Calorimeter";
  }
}

let tooltipEl = null;
function domTooltip(x, y, text) {
  if (!tooltipEl) {
    tooltipEl = document.createElement("div");
    tooltipEl.style.position = "fixed";
    tooltipEl.style.pointerEvents = "none";
    tooltipEl.style.padding = "4px 8px";
    tooltipEl.style.background = "rgba(13, 17, 23, 0.9)";
    tooltipEl.style.border = "1px solid #30363d";
    tooltipEl.style.color = "#58a6ff";
    tooltipEl.style.fontSize = "0.75rem";
    tooltipEl.style.borderRadius = "4px";
    tooltipEl.style.zIndex = "100";
    document.body.appendChild(tooltipEl);
  }
  tooltipEl.textContent = text;
  tooltipEl.style.left = (x + 12) + "px";
  tooltipEl.style.top = (y + 12) + "px";
  tooltipEl.style.display = "block";
}

function domTooltipHide() {
  if (tooltipEl) {
    tooltipEl.style.display = "none";
  }
}
