/**
 * vectorExport.js - Handles 100% mathematically vectorized PDF export via Visualizer API.
 */

class VectorPdfExport {
  constructor() {
    this.btnExportRZ = document.getElementById("btn-export-rz");
    this.btnExportRPhi = document.getElementById("btn-export-rphi");

    this.init();
  }

  init() {
    if (this.btnExportRZ) {
      this.btnExportRZ.addEventListener("click", () => this.exportPdf("rz"));
    }
    if (this.btnExportRPhi) {
      this.btnExportRPhi.addEventListener("click", () => this.exportPdf("rphi"));
    }
  }

  async exportPdf(viewType) {
    const btn = viewType === "rz" ? this.btnExportRZ : this.btnExportRPhi;
    const originalText = btn.innerHTML;

    try {
      btn.disabled = true;
      btn.innerHTML = `
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="spin">
          <circle cx="12" cy="12" r="10"></circle>
        </svg>
        Generating Vector PDF...
      `;

      const url = `/api/export_pdf?view=${encodeURIComponent(viewType)}&cells=1`;
      const response = await fetch(url);

      if (!response.ok) {
        throw new Error(`Export failed with status ${response.status}`);
      }

      const blob = await response.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = downloadUrl;
      a.download = `detector_${viewType}_cut.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(downloadUrl);
      a.remove();
    } catch (err) {
      alert(`PDF Export Error: ${err.message}`);
    } finally {
      btn.disabled = false;
      btn.innerHTML = originalText;
    }
  }
}
