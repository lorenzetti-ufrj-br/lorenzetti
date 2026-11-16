#!/usr/bin/env python3
"""
Script: run_reco_sequence.py
Purpose: Executes an end-to-end simulation and reconstruction pipeline in Lorenzetti:
         1. Generates and simulates 10 MinBias pileup events (2 files x 5 events) [EVT -> HIT]
         2. Generates and reconstructs 10 clean Zee events (2 files x 5 events) [EVT -> HIT -> ESD -> AOD -> NTUPLE -> PARQUET]
         3. Overlays MinBias pileup (mu=10) onto Zee HIT files and reconstructs the full pipeline [HIT_Merged -> ESD -> AOD -> NTUPLE -> PARQUET]

Parallelization:
         - 2 worker processes (-nw 2) across all file-parallel stages
         - 5 threads (-nt 5) per worker during Geant4 detector simulation
"""

import os
import sys
import time
import shutil
import subprocess
from pathlib import Path
from typing import List, Optional
from typing_extensions import Annotated
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()
app = typer.Typer(help="Lorenzetti End-to-End Simulation & Reconstruction Workflow Runner", pretty_exceptions_enable=False)


def setup_environment(repo_root: Path) -> dict:
    """Prepares execution environment variables pointing to Lorenzetti build artifacts."""
    env = os.environ.copy()
    build_dir = repo_root / "build"

    python_paths = [
        str(build_dir / "python"),
        str(repo_root / "kernel" / "GaugiKernel" / "python"),
        str(repo_root / "generator" / "filters" / "python"),
        str(repo_root / "reconstruction" / "calorimeter" / "CaloHitBuilder" / "python"),
        str(repo_root / "reconstruction" / "calorimeter" / "CaloCellBuilder" / "python"),
        str(repo_root / "reconstruction" / "calorimeter" / "CaloClusterBuilder" / "python"),
        str(repo_root / "reconstruction" / "calorimeter" / "CaloRingsBuilder" / "python"),
        str(repo_root / "reconstruction" / "physics" / "EgammaBuilder" / "python"),
        str(repo_root / "reconstruction" / "io" / "RootStreamBuilder" / "python"),
        str(repo_root / "geometry" / "python"),
    ]
    current_py = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = ":".join(python_paths + ([current_py] if current_py else []))

    bin_paths = [
        str(build_dir / "scripts" / "filters"),
        str(build_dir / "scripts" / "reco"),
        str(repo_root / "generator" / "filters" / "scripts"),
        str(repo_root / "reconstruction" / "reco" / "scripts"),
        str(build_dir / "lib"),
    ]
    current_path = env.get("PATH", "")
    env["PATH"] = ":".join(bin_paths + ([current_path] if current_path else []))

    ld_paths = [str(build_dir / "lib")]
    current_ld = env.get("LD_LIBRARY_PATH", "")
    env["LD_LIBRARY_PATH"] = ":".join(ld_paths + ([current_ld] if current_ld else []))

    env["LORENZETTI_EVTGEN_DATA_DIR"] = str(build_dir / "data" / "evtgen")
    env["LORENZETTI_GEOMETRY_DATA_DIR"] = str(build_dir / "data" / "geometry")

    return env


def run_stage(cmd: List[str], desc: str, env: dict, check_dir: Optional[Path] = None, skip_existing: bool = False):
    """Executes a command stage with timing and error handling."""
    if skip_existing and check_dir and check_dir.exists():
        valid_files = [f for f in check_dir.glob("*") if f.is_file() and f.stat().st_size > 0]
        if len(valid_files) >= 2:
            console.print(f"[yellow]Skipping {desc} - {len(valid_files)} files already present in {check_dir}[/yellow]\n")
            return

    console.print(Panel(f"[bold cyan]{desc}[/bold cyan]\n[dim]{' '.join(cmd)}[/dim]", expand=False))
    start_time = time.time()
    res = subprocess.run(cmd, env=env)
    elapsed = time.time() - start_time
    if res.returncode != 0:
        console.print(f"[bold red]Stage failed with exit code {res.returncode}[/bold red]")
        sys.exit(res.returncode)
    console.print(f"[bold green]Stage completed in {elapsed:.2f}s[/bold green]\n")


def summarize_directory(dir_path: Path, title: str):
    """Prints a summary table of files in a directory."""
    table = Table(title=title, show_header=True, header_style="bold magenta")
    table.add_column("Filename", style="cyan")
    table.add_column("Size (Bytes)", justify="right")
    table.add_column("Entries", justify="right")

    if not dir_path.exists():
        console.print(f"[dim]Directory {dir_path} does not exist.[/dim]")
        return

    files = sorted(dir_path.glob("*"))
    for f in files:
        if f.is_dir():
            continue
        size_str = f"{f.stat().st_size:,}"
        entries_str = "-"
        if f.suffix == ".root":
            try:
                import ROOT
                tf = ROOT.TFile.Open(str(f))
                if tf and not tf.IsZombie():
                    for key in ["CollectionTree", "physics"]:
                        tree = tf.Get(key)
                        if tree:
                            entries_str = f"{tree.GetEntries():,}"
                            break
                    tf.Close()
            except Exception:
                pass
        elif f.suffix == ".parquet":
            try:
                import pyarrow.parquet as pq
                table_meta = pq.read_metadata(str(f))
                entries_str = f"{table_meta.num_rows:,}"
            except Exception:
                pass

        table.add_row(f.name, size_str, entries_str)
    console.print(table)


@app.command()
def main(
    output_dir: Annotated[Path, typer.Option("-o", "--output-dir", help="Base output directory for generated and reconstructed files")] = Path("examples/data_run"),
    number_of_workers: Annotated[int, typer.Option("-nw", "--number-of-workers", help="Number of worker processes")] = 2,
    simulation_threads: Annotated[int, typer.Option("-nt", "--simulation-threads", help="Geant4 simulation threads per worker")] = 5,
    events_per_dataset: Annotated[int, typer.Option("--nov", "--number-of-events", help="Total number of events to process per dataset")] = 10,
    pileup_avg: Annotated[float, typer.Option("--pileup-avg", help="Average pileup value <mu> for overlay")] = 10.0,
    clean: Annotated[bool, typer.Option("--clean/--no-clean", help="Remove existing output directory before running")] = True,
    skip_existing: Annotated[bool, typer.Option("--skip-existing/--no-skip-existing", help="Skip stages whose target directory already has completed output files")] = False,
):
    """
    Runs the complete Lorenzetti reconstruction pipeline from generation to analysis tiers.
    """
    repo_root = Path(__file__).resolve().parent.parent
    env = setup_environment(repo_root)

    out_base = (repo_root / output_dir).resolve() if not output_dir.is_absolute() else output_dir.resolve()
    if clean and not skip_existing and out_base.exists():
        console.print(f"[yellow]Cleaning existing directory: {out_base}[/yellow]")
        shutil.rmtree(out_base)

    out_base.mkdir(parents=True, exist_ok=True)

    # Directory layout
    mb_evt_dir = out_base / "minbias" / "evt"
    mb_hit_dir = out_base / "minbias" / "hit"

    zee_evt_dir = out_base / "zee" / "evt"
    zee_hit_dir = out_base / "zee" / "hit"
    zee_esd_dir = out_base / "zee" / "esd"
    zee_aod_dir = out_base / "zee" / "aod"
    zee_ntuple_dir = out_base / "zee" / "ntuple"
    zee_parquet_dir = out_base / "zee" / "parquet"

    zee_pu_hit_dir = out_base / "zee_pileup" / "hit"
    zee_pu_esd_dir = out_base / "zee_pileup" / "esd"
    zee_pu_aod_dir = out_base / "zee_pileup" / "aod"
    zee_pu_ntuple_dir = out_base / "zee_pileup" / "ntuple"
    zee_pu_parquet_dir = out_base / "zee_pileup" / "parquet"

    for d in [mb_evt_dir, mb_hit_dir, zee_evt_dir, zee_hit_dir, zee_esd_dir, zee_aod_dir, zee_ntuple_dir, zee_parquet_dir,
              zee_pu_hit_dir, zee_pu_esd_dir, zee_pu_aod_dir, zee_pu_ntuple_dir, zee_pu_parquet_dir]:
        d.mkdir(parents=True, exist_ok=True)

    total_start = time.time()
    console.print(Panel(f"[bold green]Starting Lorenzetti Full Reconstruction Sequence[/bold green]\n"
                        f"Target Directory: {out_base}\n"
                        f"Workers: {number_of_workers} | Simu Threads: {simulation_threads}\n"
                        f"Events: {events_per_dataset} (2 files x 5 events) | Pileup <mu>: {pileup_avg}", expand=False))

    # =========================================================================
    # Phase 1: Minimum Bias Pileup Library (EVT -> HIT)
    # =========================================================================
    console.rule("[bold yellow]Phase 1: Minimum Bias Library (10 events: 2 files x 5 events)[/bold yellow]")

    # 1.1 Generation
    run_stage(
        ["gen_minbias.py", "-o", str(mb_evt_dir / "minbias.EVT.root"),
         "--nov", str(events_per_dataset), "-nw", str(number_of_workers), "--no-merge"],
        "1.1 MinBias Pythia8 Event Generation",
        env,
        check_dir=mb_evt_dir,
        skip_existing=skip_existing,
    )

    # 1.2 Simulation
    run_stage(
        ["simu_trf.py", "-i", str(mb_evt_dir), "-o", str(mb_hit_dir),
         "-nw", str(number_of_workers), "-nt", str(simulation_threads)],
        "1.2 MinBias Geant4 Calorimeter Simulation",
        env,
        check_dir=mb_hit_dir,
        skip_existing=skip_existing,
    )

    # =========================================================================
    # Phase 2: Clean Zee Hard-Scatter Signal (EVT -> HIT -> ESD -> AOD -> NTUPLE -> PARQUET)
    # =========================================================================
    console.rule("[bold yellow]Phase 2: Clean Zee Signal (10 events: 2 files x 5 events)[/bold yellow]")

    # 2.1 Generation
    run_stage(
        ["gen_zee.py", "-o", str(zee_evt_dir / "zee.EVT.root"),
         "--nov", str(events_per_dataset), "-nw", str(number_of_workers), "--no-merge"],
        "2.1 Zee Pythia8 Event Generation",
        env,
        check_dir=zee_evt_dir,
        skip_existing=skip_existing,
    )

    # 2.2 Simulation
    run_stage(
        ["simu_trf.py", "-i", str(zee_evt_dir), "-o", str(zee_hit_dir),
         "-nw", str(number_of_workers), "-nt", str(simulation_threads)],
        "2.2 Zee Geant4 Calorimeter Simulation",
        env,
        check_dir=zee_hit_dir,
        skip_existing=skip_existing,
    )

    # 2.3 Digitization (CaloCellBuilder)
    run_stage(
        ["digit_trf.py", "-i", str(zee_hit_dir), "-o", str(zee_esd_dir),
         "-nw", str(number_of_workers)],
        "2.3 Zee Digitization & Pulse Shaping (HIT -> ESD)",
        env,
        check_dir=zee_esd_dir,
        skip_existing=skip_existing,
    )

    # 2.4 Reconstruction (CaloCluster, CaloRings, Electron)
    run_stage(
        ["reco_trf.py", "-i", str(zee_esd_dir), "-o", str(zee_aod_dir),
         "-nw", str(number_of_workers)],
        "2.4 Zee Offline Reconstruction (ESD -> AOD)",
        env,
        check_dir=zee_aod_dir,
        skip_existing=skip_existing,
    )

    # 2.5 Ntuple Generation
    run_stage(
        ["ntuple_trf.py", "-i", str(zee_aod_dir), "-o", str(zee_ntuple_dir),
         "-nw", str(number_of_workers)],
        "2.5 Zee Analysis Flat Ntuple (AOD -> NTUPLE)",
        env,
        check_dir=zee_ntuple_dir,
        skip_existing=skip_existing,
    )

    # 2.6 Parquet Generation
    run_stage(
        ["parquet_trf.py", "-i", str(zee_aod_dir), "-o", str(zee_parquet_dir),
         "-nw", str(number_of_workers)],
        "2.6 Zee ML Parquet Serialization (AOD -> PARQUET)",
        env,
        check_dir=zee_parquet_dir,
        skip_existing=skip_existing,
    )

    # =========================================================================
    # Phase 3: Zee + MinBias Pileup Superposition (<mu> = 10) & Full Reconstruction
    # =========================================================================
    console.rule(f"[bold yellow]Phase 3: Zee + MinBias Pileup Overlay (<mu> = {pileup_avg}) & Reconstruction[/bold yellow]")

    # 3.1 Hit-level Pileup Merge
    minbias_pattern = str(mb_hit_dir / "*.root")
    run_stage(
        ["merge_trf.py", "-i", str(zee_hit_dir), "-o", str(zee_pu_hit_dir),
         "--pileup-files", minbias_pattern,
         "--pileup-avg", str(pileup_avg),
         "-nw", str(number_of_workers)],
        f"3.1 Pileup Superposition (Zee + MinBias with <mu> = {pileup_avg})",
        env,
        check_dir=zee_pu_hit_dir,
        skip_existing=skip_existing,
    )

    # 3.2 Digitization with Pileup
    run_stage(
        ["digit_trf.py", "-i", str(zee_pu_hit_dir), "-o", str(zee_pu_esd_dir),
         "-nw", str(number_of_workers)],
        "3.2 Pileup Digitization & Pulse Shaping (HIT_Merged -> ESD)",
        env,
        check_dir=zee_pu_esd_dir,
        skip_existing=skip_existing,
    )

    # 3.3 Reconstruction with Pileup
    run_stage(
        ["reco_trf.py", "-i", str(zee_pu_esd_dir), "-o", str(zee_pu_aod_dir),
         "-nw", str(number_of_workers)],
        "3.3 Pileup Offline Reconstruction (ESD -> AOD)",
        env,
        check_dir=zee_pu_aod_dir,
        skip_existing=skip_existing,
    )

    # 3.4 Ntuple Generation with Pileup
    run_stage(
        ["ntuple_trf.py", "-i", str(zee_pu_aod_dir), "-o", str(zee_pu_ntuple_dir),
         "-nw", str(number_of_workers)],
        "3.4 Pileup Analysis Flat Ntuple (AOD -> NTUPLE)",
        env,
        check_dir=zee_pu_ntuple_dir,
        skip_existing=skip_existing,
    )

    # 3.5 Parquet Generation with Pileup
    run_stage(
        ["parquet_trf.py", "-i", str(zee_pu_aod_dir), "-o", str(zee_pu_parquet_dir),
         "-nw", str(number_of_workers)],
        "3.5 Pileup ML Parquet Serialization (AOD -> PARQUET)",
        env,
        check_dir=zee_pu_parquet_dir,
        skip_existing=skip_existing,
    )

    # =========================================================================
    # Final Summary Table
    # =========================================================================
    total_elapsed = time.time() - total_start
    console.rule("[bold green]Pipeline Execution Completed Successfully![/bold green]")
    console.print(f"Total time elapsed: [bold]{total_elapsed:.2f} seconds[/bold]\n")

    summarize_directory(mb_evt_dir, "MinBias EVT Files")
    summarize_directory(mb_hit_dir, "MinBias HIT Files")
    summarize_directory(zee_evt_dir, "Clean Zee EVT Files")
    summarize_directory(zee_hit_dir, "Clean Zee HIT Files")
    summarize_directory(zee_esd_dir, "Clean Zee ESD Files")
    summarize_directory(zee_aod_dir, "Clean Zee AOD Files")
    summarize_directory(zee_ntuple_dir, "Clean Zee NTUPLE Files")
    summarize_directory(zee_parquet_dir, "Clean Zee PARQUET Files")
    summarize_directory(zee_pu_hit_dir, "Pileup Zee HIT Files")
    summarize_directory(zee_pu_esd_dir, "Pileup Zee ESD Files")
    summarize_directory(zee_pu_aod_dir, "Pileup Zee AOD Files")
    summarize_directory(zee_pu_ntuple_dir, "Pileup Zee NTUPLE Files")
    summarize_directory(zee_pu_parquet_dir, "Pileup Zee PARQUET Files")


if __name__ == "__main__":
    app()
