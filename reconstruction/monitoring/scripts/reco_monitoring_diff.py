#!/usr/bin/env python3
"""
Script: reco_monitoring_diff.py
Description: Compares two expert_monitoring.root files (test vs reference)
             histogram by histogram, performing Kolmogorov-Smirnov and Chi-squared
             goodness-of-fit tests, and produces interactive standalone HTML and optional PDF reports.
"""

from pathlib import Path
import base64
import io
import sys
from typing import Optional, List, Dict, Any
from typing_extensions import Annotated
import typer

import ROOT
ROOT.gROOT.SetBatch(True)
ROOT.gErrorIgnoreLevel = ROOT.kWarning

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from rich.console import Console
from rich.table import Table

console = Console()
app = typer.Typer(help="Compara dois arquivos expert_monitoring.root e gera relatórios HTML e PDF de DQM.")


def compare_histograms(
    h_test: Any,
    h_ref: Any,
    ks_fail: float = 0.01,
    ks_warn: float = 0.05,
    chi2_fail: float = 0.001,
    chi2_warn: float = 0.01,
) -> Dict[str, Any]:
    """Executa testes estatísticos entre o histograma de teste e o de referência."""
    entries_test = h_test.GetEntries()
    entries_ref = h_ref.GetEntries()

    if entries_test == 0 and entries_ref == 0:
        return {
            "status": "PASS",
            "ks_pvalue": 1.0,
            "chi2_pvalue": 1.0,
            "mean_test": 0.0,
            "mean_ref": 0.0,
            "rms_test": 0.0,
            "rms_ref": 0.0,
            "entries_test": 0,
            "entries_ref": 0,
        }

    if entries_test == 0 or entries_ref == 0:
        return {
            "status": "FAIL",
            "ks_pvalue": 0.0,
            "chi2_pvalue": 0.0,
            "mean_test": h_test.GetMean(),
            "mean_ref": h_ref.GetMean(),
            "rms_test": h_test.GetRMS(),
            "rms_ref": h_ref.GetRMS(),
            "entries_test": entries_test,
            "entries_ref": entries_ref,
        }

    try:
        ks_pvalue = float(h_test.KolmogorovTest(h_ref, ""))
    except Exception:
        ks_pvalue = 0.0

    try:
        chi2_pvalue = float(h_test.Chi2Test(h_ref, "UW"))
    except Exception:
        chi2_pvalue = 1.0

    mean_test = float(h_test.GetMean())
    mean_ref = float(h_ref.GetMean())
    rms_test = float(h_test.GetRMS())
    rms_ref = float(h_ref.GetRMS())

    status = "PASS"
    if ks_pvalue < ks_fail or chi2_pvalue < chi2_fail:
        status = "FAIL"
    elif ks_pvalue < ks_warn or chi2_pvalue < chi2_warn:
        status = "WARNING"

    return {
        "status": status,
        "ks_pvalue": ks_pvalue,
        "chi2_pvalue": chi2_pvalue,
        "mean_test": mean_test,
        "mean_ref": mean_ref,
        "rms_test": rms_test,
        "rms_ref": rms_ref,
        "entries_test": entries_test,
        "entries_ref": entries_ref,
    }


def render_plot_figure(h_test: Any, h_ref: Any, title: str) -> plt.Figure:
    """Gera uma figura matplotlib contendo a distribuição e o painel de razão (ratio)."""
    fig, (ax_main, ax_ratio) = plt.subplots(
        2, 1, figsize=(7, 5.5), gridspec_kw={"height_ratios": [3, 1]}, sharex=True, dpi=100
    )

    nbins = h_test.GetNbinsX()
    bins = [h_test.GetBinLowEdge(i) for i in range(1, nbins + 2)]
    centers = [h_test.GetBinCenter(i) for i in range(1, nbins + 1)]

    vals_test = [h_test.GetBinContent(i) for i in range(1, nbins + 1)]
    errs_test = [h_test.GetBinError(i) for i in range(1, nbins + 1)]

    vals_ref = [h_ref.GetBinContent(i) for i in range(1, nbins + 1)]
    errs_ref = [h_ref.GetBinError(i) for i in range(1, nbins + 1)]

    # Painel Superior
    ax_main.step(bins[:-1], vals_ref, where="post", color="#1f77b4", label="Referência", lw=1.5)
    ax_main.fill_between(bins[:-1], vals_ref, step="post", alpha=0.15, color="#1f77b4")
    ax_main.errorbar(
        centers, vals_test, yerr=errs_test, fmt="o", color="#d62728", label="Atual", markersize=4, capsize=2
    )
    ax_main.set_ylabel("Contagens / Bin", fontsize=10)
    ax_main.set_title(title, fontsize=11, fontweight="bold")
    ax_main.legend(frameon=False, loc="upper right")
    ax_main.grid(True, linestyle=":", alpha=0.6)

    # Painel Inferior (Ratio)
    ratios = []
    ratio_errs = []
    for vt, vr, et in zip(vals_test, vals_ref, errs_test):
        if vr > 0:
            ratios.append(vt / vr)
            ratio_errs.append(et / vr)
        else:
            ratios.append(np.nan)
            ratio_errs.append(0.0)

    ax_ratio.errorbar(centers, ratios, yerr=ratio_errs, fmt="o", color="black", markersize=3)
    ax_ratio.axhline(1.0, color="gray", linestyle="--", lw=1)
    ax_ratio.axhspan(0.95, 1.05, color="#2ca02c", alpha=0.15)
    ax_ratio.set_ylim(0.7, 1.3)
    ax_ratio.set_ylabel("Atual / Ref", fontsize=9)
    x_title = h_test.GetXaxis().GetTitle() or "Grandeza Física"
    ax_ratio.set_xlabel(x_title, fontsize=10)
    ax_ratio.grid(True, linestyle=":", alpha=0.6)

    plt.tight_layout()
    return fig


def figure_to_base64(fig: plt.Figure) -> str:
    """Converte uma figura matplotlib em string Base64 PNG."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    buf.seek(0)
    img_b64 = base64.b64encode(buf.read()).decode("utf-8")
    buf.close()
    return img_b64


def extract_histograms(tfile: Any, base_dir: str = "") -> Dict[str, Any]:
    """Extrai recursivamente todos os TH1 de um TFile ou TDirectory."""
    hists = {}
    directory = tfile.GetDirectory(base_dir) if base_dir else tfile
    if not directory:
        return hists

    for key in directory.GetListOfKeys():
        obj = key.ReadObj()
        name = key.GetName()
        path = f"{base_dir}/{name}" if base_dir else name

        if obj.InheritsFrom("TDirectory"):
            hists.update(extract_histograms(tfile, path))
        elif obj.InheritsFrom("TH1") and not obj.InheritsFrom("TH2"):
            hists[path] = obj
    return hists


def generate_html_report(
    results: List[Dict[str, Any]], test_path: str, ref_path: str
) -> str:
    """Gera relatório HTML standalone, moderno, com cards, filtros e busca instantânea."""
    pass_count = sum(1 for r in results if r["status"] == "PASS")
    warn_count = sum(1 for r in results if r["status"] == "WARNING")
    fail_count = sum(1 for r in results if r["status"] == "FAIL")
    total = len(results)

    cards_html = []
    for r in results:
        badge_class = r["status"].lower()
        card = f"""
        <div class="card {badge_class}" data-status="{r['status']}" data-name="{r['name']}">
            <div class="card-header">
                <span class="card-title">{r['name']}</span>
                <span class="badge {badge_class}">{r['status']}</span>
            </div>
            <div class="card-body">
                <div class="metric-row">
                    <span><strong>KS p-value:</strong> {r['ks_pvalue']:.4e}</span>
                    <span><strong>Chi2 p-value:</strong> {r['chi2_pvalue']:.4e}</span>
                </div>
                <div class="metric-row">
                    <span><strong>Média:</strong> {r['mean_test']:.4f} (Ref: {r['mean_ref']:.4f})</span>
                    <span><strong>RMS:</strong> {r['rms_test']:.4f} (Ref: {r['rms_ref']:.4f})</span>
                </div>
                <img src="data:image/png;base64,{r['plot_b64']}" alt="{r['name']}" class="plot-img"/>
            </div>
        </div>
        """
        cards_html.append(card)

    cards_joined = "\n".join(cards_html)

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Lorenzetti DQM - Relatório de Validação de Monitoramento</title>
    <style>
        * {{ box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background: #f4f6f9;
            color: #2c3e50;
            margin: 0;
            padding: 24px;
        }}
        .header {{
            background: linear-gradient(135deg, #1f2d3d 0%, #34495e 100%);
            color: #ffffff;
            padding: 28px;
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            margin-bottom: 24px;
        }}
        .header h1 {{ margin: 0 0 10px 0; font-size: 1.8rem; }}
        .header p {{ margin: 4px 0; font-size: 0.95rem; opacity: 0.9; }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
            margin-bottom: 24px;
        }}
        .summary-card {{
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            color: #ffffff;
            box-shadow: 0 4px 6px rgba(0,0,0,0.06);
        }}
        .summary-card .number {{ font-size: 2rem; font-weight: 700; margin-top: 4px; }}
        .summary-card .label {{ font-size: 0.9rem; text-transform: uppercase; letter-spacing: 0.5px; opacity: 0.9; }}
        .total-bg {{ background: #4b6584; }}
        .pass-bg {{ background: #20bf6b; }}
        .warn-bg {{ background: #f7b731; color: #2d3436; }}
        .fail-bg {{ background: #eb3b5a; }}
        .controls {{
            display: flex;
            gap: 16px;
            margin-bottom: 24px;
            flex-wrap: wrap;
        }}
        .controls input, .controls select {{
            padding: 12px 16px;
            font-size: 1rem;
            border-radius: 8px;
            border: 1px solid #dcdde1;
            background: #ffffff;
            outline: none;
            transition: border-color 0.2s;
        }}
        .controls input:focus, .controls select:focus {{ border-color: #3867d6; }}
        .cards-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(460px, 1fr));
            gap: 20px;
        }}
        .card {{
            background: #ffffff;
            border-radius: 10px;
            border-left: 6px solid #dcdde1;
            box-shadow: 0 2px 8px rgba(0,0,0,0.06);
            overflow: hidden;
            display: flex;
            flex-direction: column;
        }}
        .card.pass {{ border-left-color: #20bf6b; }}
        .card.warning {{ border-left-color: #f7b731; }}
        .card.fail {{ border-left-color: #eb3b5a; }}
        .card-header {{
            padding: 14px 18px;
            background: #f8f9fa;
            border-bottom: 1px solid #edf2f7;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .card-title {{ font-weight: 600; font-size: 1rem; word-break: break-all; }}
        .badge {{
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .badge.pass {{ background: #e8f8f0; color: #20bf6b; border: 1px solid #20bf6b; }}
        .badge.warning {{ background: #fef9e7; color: #f7b731; border: 1px solid #f7b731; }}
        .badge.fail {{ background: #fde8ec; color: #eb3b5a; border: 1px solid #eb3b5a; }}
        .card-body {{ padding: 16px; flex: 1; display: flex; flex-direction: column; }}
        .metric-row {{
            display: flex;
            justify-content: space-between;
            font-size: 0.85rem;
            margin-bottom: 6px;
            color: #4b6584;
        }}
        .plot-img {{
            width: 100%;
            border-radius: 6px;
            border: 1px solid #edf2f7;
            margin-top: 10px;
        }}
    </style>
    <script>
        function filterCards() {{
            const filterText = document.getElementById("searchBox").value.toLowerCase();
            const filterStatus = document.getElementById("statusFilter").value;
            const cards = document.querySelectorAll(".card");
            cards.forEach(card => {{
                const name = card.getAttribute("data-name").toLowerCase();
                const status = card.getAttribute("data-status");
                const matchName = name.includes(filterText);
                const matchStatus = (filterStatus === "ALL" || status === filterStatus);
                card.style.display = (matchName && matchStatus) ? "flex" : "none";
            }});
        }}
    </script>
</head>
<body>
    <div class="header">
        <h1>Lorenzetti - Relatório de Monitoramento Especialista (DQM)</h1>
        <p><strong>Arquivo de Teste:</strong> {test_path}</p>
        <p><strong>Arquivo de Referência:</strong> {ref_path}</p>
    </div>

    <div class="summary">
        <div class="summary-card total-bg">
            <div class="label">Total Comparados</div>
            <div class="number">{total}</div>
        </div>
        <div class="summary-card pass-bg">
            <div class="label">Aprovados (PASS)</div>
            <div class="number">{pass_count}</div>
        </div>
        <div class="summary-card warn-bg">
            <div class="label">Alertas (WARNING)</div>
            <div class="number">{warn_count}</div>
        </div>
        <div class="summary-card fail-bg">
            <div class="label">Falhas (FAIL)</div>
            <div class="number">{fail_count}</div>
        </div>
    </div>

    <div class="controls">
        <input type="text" id="searchBox" placeholder="Filtrar por nome da variável..." onkeyup="filterCards()" style="flex: 2;"/>
        <select id="statusFilter" onchange="filterCards()" style="flex: 1;">
            <option value="ALL">Todos os Status</option>
            <option value="FAIL">Apenas Falhas (FAIL)</option>
            <option value="WARNING">Apenas Alertas (WARNING)</option>
            <option value="PASS">Apenas Aprovados (PASS)</option>
        </select>
    </div>

    <div class="cards-grid">
        {cards_joined}
    </div>
</body>
</html>
"""


@app.command()
def main(
    test_file: Annotated[Path, typer.Option("-t", "--test-file", help="Arquivo expert_monitoring.root atual")],
    ref_file: Annotated[Path, typer.Option("-r", "--ref-file", help="Arquivo expert_monitoring_ref.root de referência")],
    output_html: Annotated[Path, typer.Option("-o", "--output-html", help="Caminho do relatório HTML")] = Path("monitoring_report.html"),
    pdf: Annotated[Optional[Path], typer.Option("--pdf", help="Caminho opcional do relatório PDF")] = None,
    ks_fail: Annotated[float, typer.Option("--ks-fail", help="Limite de p-value KS para FAIL")] = 0.01,
    ks_warn: Annotated[float, typer.Option("--ks-warn", help="Limite de p-value KS para WARN")] = 0.05,
    chi2_fail: Annotated[float, typer.Option("--chi2-fail", help="Limite de p-value Chi2 para FAIL")] = 0.001,
    chi2_warn: Annotated[float, typer.Option("--chi2-warn", help="Limite de p-value Chi2 para WARN")] = 0.01,
):
    """Executa a comparação cruzada histograma a histograma entre o arquivo de teste e o de referência."""
    if not test_file.exists():
        console.print(f"[red]Erro: Arquivo de teste não encontrado: {test_file}[/red]")
        raise typer.Exit(code=1)
    if not ref_file.exists():
        console.print(f"[red]Erro: Arquivo de referência não encontrado: {ref_file}[/red]")
        raise typer.Exit(code=1)

    f_test = ROOT.TFile.Open(str(test_file))
    f_ref = ROOT.TFile.Open(str(ref_file))

    if not f_test or f_test.IsZombie():
        console.print(f"[red]Erro ao abrir arquivo ROOT de teste: {test_file}[/red]")
        raise typer.Exit(code=1)
    if not f_ref or f_ref.IsZombie():
        console.print(f"[red]Erro ao abrir arquivo ROOT de referência: {ref_file}[/red]")
        raise typer.Exit(code=1)

    hists_test = extract_histograms(f_test)
    hists_ref = extract_histograms(f_ref)

    common_keys = sorted(set(hists_test.keys()) & set(hists_ref.keys()))

    if not common_keys:
        console.print("[yellow]Aviso: Nenhum histograma coincidente encontrado entre os dois arquivos.[/yellow]")
        raise typer.Exit(code=0)

    results = []
    figures_for_pdf = []

    table = Table(title="Lorenzetti - Auditoria de Monitoramento Especialista (DQM)")
    table.add_column("Histograma / Variável", justify="left")
    table.add_column("Status", justify="center")
    table.add_column("KS p-value", justify="right")
    table.add_column("Chi2 p-value", justify="right")
    table.add_column("Média Atual (Ref)", justify="right")

    for key in common_keys:
        h_t = hists_test[key]
        h_r = hists_ref[key]

        metrics = compare_histograms(
            h_t, h_r, ks_fail=ks_fail, ks_warn=ks_warn, chi2_fail=chi2_fail, chi2_warn=chi2_warn
        )
        fig = render_plot_figure(h_t, h_r, key)
        b64 = figure_to_base64(fig)

        metrics["name"] = key
        metrics["plot_b64"] = b64
        results.append(metrics)

        if pdf is not None:
            figures_for_pdf.append((key, metrics["status"], fig))
        else:
            plt.close(fig)

        color = "green" if metrics["status"] == "PASS" else ("yellow" if metrics["status"] == "WARNING" else "red")
        table.add_row(
            key,
            f"[{color}]{metrics['status']}[/{color}]",
            f"{metrics['ks_pvalue']:.4e}",
            f"{metrics['chi2_pvalue']:.4e}",
            f"{metrics['mean_test']:.3f} ({metrics['mean_ref']:.3f})"
        )

    console.print(table)

    # Gera HTML
    html_doc = generate_html_report(results, str(test_file), str(ref_file))
    with open(output_html, "w", encoding="utf-8") as f:
        f.write(html_doc)
    console.print(f"[green]Relatório HTML gerado em: {output_html}[/green]")

    # Gera PDF se solicitado
    if pdf is not None and figures_for_pdf:
        from matplotlib.backends.backend_pdf import PdfPages
        with PdfPages(str(pdf)) as pdf_pages:
            # Página 1: Capa e Sumário
            cover_fig, ax = plt.subplots(figsize=(8.5, 11))
            ax.axis("off")
            pass_c = sum(1 for r in results if r["status"] == "PASS")
            warn_c = sum(1 for r in results if r["status"] == "WARNING")
            fail_c = sum(1 for r in results if r["status"] == "FAIL")

            cover_text = f"""
            LORENZETTI DATA QUALITY MONITORING (DQM)
            =========================================

            Arquivo Atual: {test_file}
            Arquivo Referência: {ref_file}

            Resumo Executivo:
            -----------------
            Total de Histogramas Avaliados: {len(results)}
            Aprovados (PASS):     {pass_c}
            Alertas (WARNING):   {warn_c}
            Falhas (FAIL):       {fail_c}

            Critérios Estatísticos:
            - Kolmogorov-Smirnov Test (KS): p >= {ks_warn} (PASS), < {ks_fail} (FAIL)
            - Chi-Squared Test (Chi2):      p >= {chi2_warn} (PASS), < {chi2_fail} (FAIL)
            """
            ax.text(0.1, 0.5, cover_text, fontsize=12, family="monospace", va="center")
            pdf_pages.savefig(cover_fig)
            plt.close(cover_fig)

            # Páginas de Gráficos
            for _, _, fig_item in figures_for_pdf:
                pdf_pages.savefig(fig_item)
                plt.close(fig_item)

        console.print(f"[green]Relatório PDF executivo gerado em: {pdf}[/green]")

    f_test.Close()
    f_ref.Close()


if __name__ == "__main__":
    app()
