/**
 * controls.js - Application coordinator, UI event bindings, and Layer Tree generation for Visualizer.
 */

document.addEventListener("DOMContentLoaded", async () => {
  const visualizer = new Visualizer3D("canvas-container");
  const inspector = new GridInspector(visualizer);
  const pdfExporter = new VectorPdfExport();

  let geometryData = null;
  try {
    const res = await fetch("/api/geometry");
    if (!res.ok) {
      throw new Error(`Failed to load geometry: HTTP ${res.status}`);
    }
    geometryData = await res.json();
    visualizer.loadGeometry(geometryData);
    buildLayerTree(geometryData.volumes, visualizer, inspector);
  } catch (err) {
    const treeContainer = document.getElementById("layer-tree-container");
    if (treeContainer) {
      treeContainer.innerHTML = `<div style="color:#f85149; padding:10px;">Error loading geometry: ${err.message}</div>`;
    }
    console.error("Visualizer init error:", err);
    return;
  }

  // Wedge Cut Slider
  const wedgeCutSlider = document.getElementById("wedge-cut-slider");
  const wedgeCutVal = document.getElementById("wedge-cut-val");
  if (wedgeCutSlider && wedgeCutVal) {
    wedgeCutSlider.addEventListener("input", (e) => {
      const angle = parseInt(e.target.value, 10);
      wedgeCutVal.innerHTML = `${angle}&deg;`;
      visualizer.setWedgeCut(angle);
    });
  }

  // Axial Cut Toggle
  const axialCutToggle = document.getElementById("axial-cut-toggle");
  if (axialCutToggle) {
    axialCutToggle.addEventListener("change", (e) => {
      visualizer.setAxialCut(e.target.checked);
    });
  }

  // Opacity Slider
  const opacitySlider = document.getElementById("opacity-slider");
  const opacityVal = document.getElementById("opacity-val");
  if (opacitySlider && opacityVal) {
    opacitySlider.addEventListener("input", (e) => {
      const val = parseInt(e.target.value, 10);
      opacityVal.textContent = `${val}%`;
      visualizer.setGlobalOpacity(val / 100.0);
    });
  }

  // Cell Grid Toggle
  const gridToggle = document.getElementById("grid-toggle");
  if (gridToggle) {
    gridToggle.addEventListener("change", (e) => {
      visualizer.setGridVisible(e.target.checked);
    });
  }

  // Axes Toggle
  const axesToggle = document.getElementById("axes-toggle");
  if (axesToggle) {
    axesToggle.addEventListener("change", (e) => {
      visualizer.setAxesVisible(e.target.checked);
    });
  }

  // Camera Toolbar Buttons
  const camButtons = [
    { id: "btn-cam-iso", view: "iso" },
    { id: "btn-cam-rz", view: "rz" },
    { id: "btn-cam-rphi", view: "rphi" },
    { id: "btn-cam-top", view: "top" },
    { id: "btn-cam-reset", view: "reset" }
  ];

  camButtons.forEach(({ id, view }) => {
    const btn = document.getElementById(id);
    if (btn) {
      btn.addEventListener("click", () => visualizer.setCameraView(view));
    }
  });

  // Show All / Hide All
  const btnShowAll = document.getElementById("btn-show-all");
  const btnHideAll = document.getElementById("btn-hide-all");

  if (btnShowAll) {
    btnShowAll.addEventListener("click", (e) => {
      e.preventDefault();
      setAllVolumesVisible(true, visualizer);
    });
  }

  if (btnHideAll) {
    btnHideAll.addEventListener("click", (e) => {
      e.preventDefault();
      setAllVolumesVisible(false, visualizer);
    });
  }
});

function buildLayerTree(volumes, visualizer, inspector) {
  const container = document.getElementById("layer-tree-container");
  if (!container) return;
  container.innerHTML = "";

  const groups = [
    {
      id: "ecal-barrel",
      name: "LAr ECAL Barrel",
      filter: (v) => v.name.includes("PSB") || v.name.includes("EMB"),
      items: []
    },
    {
      id: "tile-barrel",
      name: "TileCal Barrel",
      filter: (v) => v.name.includes("TileCal") && !v.name.includes("TileCalExt"),
      items: []
    },
    {
      id: "tile-ext",
      name: "TileCal Extended",
      filter: (v) => v.name.includes("TileCalExt"),
      items: []
    },
    {
      id: "emec-endcap",
      name: "LAr EMEC Endcap",
      filter: (v) => v.name.includes("PSE") || v.name.includes("EMEC"),
      items: []
    },
    {
      id: "hec-endcap",
      name: "Hadronic Endcap (HEC)",
      filter: (v) => v.name.includes("HEC"),
      items: []
    },
    {
      id: "dead-materials",
      name: "Dead Materials & Cryostats",
      filter: (v) => v.name.startsWith("DM::"),
      items: []
    }
  ];

  volumes.forEach((vol) => {
    let matched = false;
    for (const grp of groups) {
      if (grp.filter(vol)) {
        grp.items.push(vol);
        matched = true;
        break;
      }
    }
    if (!matched) {
      groups[groups.length - 1].items.push(vol);
    }
  });

  groups.forEach((grp) => {
    if (grp.items.length === 0) return;

    const groupDiv = document.createElement("div");
    groupDiv.className = "layer-group";

    const header = document.createElement("div");
    header.className = "group-header";
    header.innerHTML = `
      <div style="display:flex; align-items:center; gap:8px;">
        <span class="group-arrow">&#9662;</span>
        <span>${grp.name} (${grp.items.length})</span>
      </div>
      <input type="checkbox" class="group-toggle" checked title="Toggle all in ${grp.name}">
    `;

    const itemsList = document.createElement("div");
    itemsList.className = "group-items";

    const groupCheckbox = header.querySelector(".group-toggle");
    const arrow = header.querySelector(".group-arrow");

    header.addEventListener("click", (e) => {
      if (e.target === groupCheckbox) return;
      const isCollapsed = itemsList.style.display === "none";
      itemsList.style.display = isCollapsed ? "block" : "none";
      arrow.innerHTML = isCollapsed ? "&#9662;" : "&#9656;";
    });

    groupCheckbox.addEventListener("change", (e) => {
      const checked = e.target.checked;
      const childCheckboxes = itemsList.querySelectorAll(".layer-checkbox");
      childCheckboxes.forEach((cb) => {
        cb.checked = checked;
        const volName = cb.dataset.volume;
        visualizer.setVolumeVisible(volName, checked);
      });
    });

    grp.items.forEach((vol) => {
      const volObj = visualizer.volumeObjects.get(vol.name);
      const colorHex = volObj ? volObj.color.toString(16).padStart(6, "0") : "888888";

      const itemDiv = document.createElement("div");
      itemDiv.className = "layer-item";

      itemDiv.innerHTML = `
        <div class="layer-info" style="cursor:pointer;" title="Click to inspect ${vol.name}">
          <div class="color-dot" style="background-color: #${colorHex};"></div>
          <span class="layer-name">${vol.name}</span>
        </div>
        <div class="layer-actions">
          <input type="checkbox" class="layer-checkbox" data-volume="${vol.name}" checked>
        </div>
      `;

      const layerCb = itemDiv.querySelector(".layer-checkbox");
      layerCb.addEventListener("change", (e) => {
        visualizer.setVolumeVisible(vol.name, e.target.checked);
      });

      const layerInfo = itemDiv.querySelector(".layer-info");
      layerInfo.addEventListener("click", () => {
        inspector.showVolumeDetails(vol);
      });

      itemsList.appendChild(itemDiv);
    });

    groupDiv.appendChild(header);
    groupDiv.appendChild(itemsList);
    container.appendChild(groupDiv);
  });
}

function setAllVolumesVisible(visible, visualizer) {
  const checkboxes = document.querySelectorAll(".layer-checkbox, .group-toggle");
  checkboxes.forEach((cb) => {
    cb.checked = visible;
  });

  for (const name of visualizer.volumeObjects.keys()) {
    visualizer.setVolumeVisible(name, visible);
  }
}
