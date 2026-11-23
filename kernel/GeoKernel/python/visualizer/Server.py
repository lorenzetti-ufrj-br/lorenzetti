"""
Server.py - High-performance server for Lorenzetti Visualizer.
Supports FastAPI with Uvicorn when available, with automatic zero-dependency fallback
to standard Python http.server in headless/container environments.
"""

from typing import Any, Dict, Optional
import http.server
import json
import os
import socketserver
import tempfile
import urllib.parse
import webbrowser

try:
    from visualizer.VectorPdfExporter import VectorPdfExporter
except ImportError:
    from GeoKernel.visualizer.VectorPdfExporter import VectorPdfExporter

__all__ = ["launch_visualizer", "VisualizerHttpHandler"]

_DEFAULT_WEB_DIR = next(
    (
        d for d in [
            os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), "../../web")),
            os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), "../web")),
            os.path.abspath(os.path.join(os.path.dirname(__file__), "../../web")),
            os.path.abspath(os.path.join(os.path.dirname(__file__), "../web")),
        ]
        if os.path.isdir(d)
    ),
    os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), "../../web")),
)


class VisualizerHttpHandler(http.server.SimpleHTTPRequestHandler):
    """Zero-dependency HTTP handler for static assets, /api/geometry, and /api/export_pdf."""

    geometry_file: str = ""
    web_dir: str = _DEFAULT_WEB_DIR

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, directory=self.web_dir, **kwargs)

    def do_GET(self) -> None:
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        params = urllib.parse.parse_qs(parsed_url.query)

        if path == "/api/geometry":
            self._handle_api_geometry()
        elif path == "/api/export_pdf":
            self._handle_api_export_pdf(params)
        elif path == "/api/health":
            self._handle_api_health()
        elif path == "/api/cad/mesh":
            self._handle_api_cad_mesh()
        else:
            super().do_GET()

    def _handle_api_health(self) -> None:
        data = json.dumps({"status": "ok", "geometry_file": self.geometry_file}).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _handle_api_cad_mesh(self) -> None:
        data = json.dumps({"type": "Parametric", "status": "Ready for WebGL"}).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _handle_api_geometry(self) -> None:
        if not os.path.isfile(self.geometry_file):
            self.send_error(404, f"Geometry file not found: {self.geometry_file}")
            return

        with open(self.geometry_file, "r", encoding="utf-8") as f:
            data = f.read().encode("utf-8")

        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _handle_api_export_pdf(self, params: dict) -> None:
        view = params.get("view", ["rz"])[0]
        show_cells = params.get("cells", ["1"])[0] in ["1", "true", "True"]

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            temp_pdf = tmp.name

        try:
            exporter = VectorPdfExporter(self.geometry_file)
            if view == "rphi":
                z_plane = float(params.get("z", [0.0])[0])
                exporter.export_rphi_cut(temp_pdf, z_plane=z_plane, show_cells=show_cells)
            else:
                exporter.export_rz_cut(temp_pdf, show_cells=show_cells)

            with open(temp_pdf, "rb") as f:
                pdf_bytes = f.read()

            filename = f"detector_cut_{view}.pdf"
            self.send_response(200)
            self.send_header("Content-Type", "application/pdf")
            self.send_header("Content-Disposition", f"attachment; filename=\"{filename}\"")
            self.send_header("Content-Length", str(len(pdf_bytes)))
            self.end_headers()
            self.wfile.write(pdf_bytes)
        finally:
            if os.path.exists(temp_pdf):
                os.remove(temp_pdf)


def launch_visualizer(
    geometry_file: str,
    port: int = 8080,
    open_browser: bool = True,
) -> None:
    """
    Launches the visualizer web server on the specified port.

    Args:
        geometry_file: Path to canonical geometry JSON file.
        port: HTTP port (default: 8080).
        open_browser: Automatically open the browser (default: True).
    """
    geo_path = os.path.abspath(geometry_file)

    # Try FastAPI first if available
    try:
        import fastapi
        import uvicorn
        from fastapi import FastAPI, Response
        from fastapi.staticfiles import StaticFiles

        app = FastAPI(title="Lorenzetti Visualizer API")

        @app.get("/api/health")
        async def health():
            return {"status": "ok", "backend": "FastAPI", "geometry_file": geo_path}

        @app.get("/api/geometry")
        async def get_geometry():
            with open(geo_path, "r", encoding="utf-8") as f:
                return json.load(f)

        @app.get("/api/export_pdf")
        async def export_pdf(view: str = "rz", cells: bool = True, z: float = 0.0):
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                temp_pdf = tmp.name
            try:
                exporter = VectorPdfExporter(geo_path)
                if view == "rphi":
                    exporter.export_rphi_cut(temp_pdf, z_plane=z, show_cells=cells)
                else:
                    exporter.export_rz_cut(temp_pdf, show_cells=cells)
                with open(temp_pdf, "rb") as f:
                    pdf_bytes = f.read()
                return Response(
                    content=pdf_bytes,
                    media_type="application/pdf",
                    headers={"Content-Disposition": f"attachment; filename=\"detector_{view}.pdf\""}
                )
            finally:
                if os.path.exists(temp_pdf):
                    os.remove(temp_pdf)

        if os.path.isdir(_DEFAULT_WEB_DIR):
            app.mount("/", StaticFiles(directory=_DEFAULT_WEB_DIR, html=True), name="web")

        url = f"http://localhost:{port}"
        print(f"\n=======================================================")
        print(f"  Lorenzetti Visualizer (FastAPI) running at: {url}")
        print(f"  Geometry: {geo_path}")
        print(f"  Interactive API Docs: {url}/docs")
        print(f"=======================================================\n")
        if open_browser:
            webbrowser.open(url)
        uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
        return

    except ImportError:
        pass

    # Fallback to zero-dependency HTTP server
    VisualizerHttpHandler.geometry_file = geo_path
    VisualizerHttpHandler.web_dir = _DEFAULT_WEB_DIR

    server_address = ("", port)
    socketserver.TCPServer.allow_reuse_address = True

    with socketserver.ThreadingTCPServer(server_address, VisualizerHttpHandler) as httpd:
        url = f"http://localhost:{port}"
        print(f"\n=======================================================")
        print(f"  Lorenzetti Visualizer (HTTP Fallback) running at: {url}")
        print(f"  Geometry: {geo_path}")
        print(f"  Press Ctrl+C to stop the server.")
        print(f"=======================================================\n")

        if open_browser:
            webbrowser.open(url)

        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down Visualizer server...")
