"""
Parallel execution engine and CLI generator using Typer and isolated subprocesses.

This module provides high-performance parallel execution for Lorenzetti physics
generators and event processors while maintaining total memory, C++, and ROOT
decoupling across processes.

Architecture Overview:
----------------------
Traditional Python multiprocessing often fails when interacting with heavy C++
frameworks (such as ROOT, Geant4, or Pythia8) due to pickling limitations,
shared global state, or symbol collisions (e.g., `_Py_HashPointer`).
`GaugiKernel.Parallel` solves this through a dual-mode Orchestrator/Worker pattern:

1. **Orchestrator Mode** (Invoked when running from CLI without internal worker flags):
   - Computes event partitions (chunks) and generates isolated pseudo-random seeds.
   - Prints a formatted execution plan (using `rich`) displaying jobs, seeds, and ranges.
   - Dispatches independent worker subprocesses concurrently via `ThreadPoolExecutor`.
   - Optionally streams worker logs in real time (`--show-output` / `-v`).
   - Automatically merges chunk outputs (`.0.root`, `.1.root`, ...) using ROOT `hadd`.

2. **Worker Mode** (Invoked internally by subprocesses with `--is-worker`):
   - Receives chunk-specific parameters (`--output-file`, `--nov`, `--seed`, etc.).
   - Directly executes the decorated user function in a clean, isolated memory space.
   - Exits cleanly upon completion with standard Unix exit codes.

Examples:
---------
Basic usage in a generator script:

    from typing import List
    from typing_extensions import Annotated
    import typer
    from GaugiKernel import parallel_job

    @parallel_job(ntuple_name="particles")
    def main(
        events: List[int],
        output_file: str,
        seed: int,
        energy: Annotated[float, typer.Option("--energy", help="Beam energy in GeV")] = 50.0,
    ):
        \"\"\"Generate single particle events.\"\"\"
        print(f"Generating {len(events)} events with seed {seed} into {output_file}")
        # Initialize EventTape, configure Pythia/Geant4, and process events:
        # tape = EventTape("Tape", OutputFile=output_file)
        # tape.run(events)

    if __name__ == "__main__":
        main()

Command-Line Usage:
-------------------
Run 100 events across 4 parallel processes:
    $ python3 gen_script.py -o output.root --nov 100 -nw 4

View execution plan without running (Dry Run):
    $ python3 gen_script.py -o output.root --nov 100 -nw 4 --dry-run

Enable real-time log streaming from worker processes:
    $ python3 gen_script.py -o output.root --nov 100 -nt 4 -v
"""

from __future__ import annotations

import glob
import inspect
import json
import os
import random
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from math import ceil
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
from typing_extensions import Annotated

import typer
import ROOT

from GaugiKernel import Logger, LoggingLevel


__all__ = [
    "ParallelJob",
    "parallel_job",
    "FileParallelJob",
    "file_parallel_job",
    "append_index_to_file",
    "check_file_exists",
    "merge_root_files",
    "merge_parquet_files",
]


def append_index_to_file(output_file: Union[str, Path], index: int) -> str:
    """
    Inserts a numerical chunk index before the file extension.

    Args:
        output_file: The destination filename or Path (e.g. 'output.root').
        index: The chunk index (e.g. 0).

    Returns:
        The modified file path as a string (e.g. 'output.0.root').

    Example:
        >>> append_index_to_file("data/events.root", 2)
        'data/events.2.root'
    """
    p = Path(output_file)
    suffix = p.suffix
    if suffix:
        return str(p.parent / f"{p.stem}.{index}{suffix}")
    return f"{str(p)}.{index}"


def check_file_exists(path: Union[str, Path], ntuple_name: str = "") -> bool:
    """
    Checks if a ROOT file exists, is non-empty, and contains valid entries.

    Args:
        path: Path to the ROOT file to verify.
        ntuple_name: Optional TTree or TObject name to inspect for entries.
                     If empty, only verifies that the file exists and is > 0 bytes.

    Returns:
        True if the file is valid and contains entries, False otherwise.
    """
    path_str = str(path)
    if not os.path.exists(path_str):
        return False
    if not ntuple_name or path_str.endswith(".parquet"):
        if path_str.endswith(".parquet"):
            try:
                import pyarrow.parquet as pq
                meta = pq.read_metadata(path_str)
                return meta.num_rows > 0
            except Exception:
                return os.path.getsize(path_str) > 0
        return os.path.getsize(path_str) > 0
    try:
        f = ROOT.TFile.Open(path_str, "READ")
        if not f or f.IsZombie():
            return False
        obj = f.Get(ntuple_name)
        entries = obj.GetEntries() if obj else 0
        f.Close()
        return entries > 0
    except Exception:
        return False


def merge_parquet_files(output_file: Union[str, Path], chunk_files: List[str]) -> None:
    """
    Merges intermediate chunk Parquet files into a single destination file via PyArrow.

    Upon successful merge, the intermediate chunk files are automatically cleaned up.
    """
    output_str = str(output_file)
    if not chunk_files:
        return
    if len(chunk_files) == 1:
        if chunk_files[0] != output_str:
            shutil.move(chunk_files[0], output_str)
        return

    import pyarrow as pa
    import pyarrow.parquet as pq

    tables = [pq.read_table(f) for f in chunk_files]
    merged = pa.concat_tables(tables)
    pq.write_table(merged, output_str)

    for f in chunk_files:
        if os.path.exists(f) and f != output_str:
            try:
                os.remove(f)
            except OSError:
                pass


def merge_files(output_file: Union[str, Path], chunk_files: List[str]) -> None:
    """
    Dispatches file merging based on output extension (.parquet vs ROOT).
    """
    if str(output_file).endswith(".parquet"):
        merge_parquet_files(output_file, chunk_files)
    else:
        merge_root_files(output_file, chunk_files)


def merge_root_files(output_file: Union[str, Path], chunk_files: List[str]) -> None:
    """
    Merges intermediate chunk ROOT files into a single destination file via ROOT `hadd`.

    Upon successful merge, the intermediate chunk files are automatically cleaned up.

    Args:
        output_file: Target merged ROOT file path.
        chunk_files: List of paths to existing chunk ROOT files.

    Raises:
        RuntimeError: If `hadd` fails with a non-zero exit code.
    """
    output_str = str(output_file)
    if not chunk_files:
        return
    if len(chunk_files) == 1:
        if chunk_files[0] != output_str:
            shutil.move(chunk_files[0], output_str)
        return

    cmd = f"hadd -f {output_str} {' '.join(chunk_files)}"
    ret = os.system(cmd)
    if ret != 0:
        raise RuntimeError(f"hadd failed with exit code {ret}: {cmd}")
    for f in chunk_files:
        if os.path.exists(f) and f != output_str:
            try:
                os.remove(f)
            except OSError:
                pass


class ParallelJob(Logger):
    """
    Manages event chunk partitioning, subprocess dispatching, and output merging.

    Attributes:
        output_file: Final merged output ROOT file path.
        seed: Base random seed used to deterministically generate chunk seeds.
        number_of_workers: Number of concurrent worker processes to launch.
        number_of_events: Total number of events requested.
        events_per_job: Number of events per chunk (-1 calculates automatically).
        event_numbers: Optional explicit list or comma-separated string of event IDs.
        merge: If True, merges chunk files with `hadd -f` after completion.
        ntuple_name: Name of TTree checked for file existence / validation.
        overwrite: If True, re-executes and overwrites already existing chunk files.
        dry_run: If True, plans execution and displays commands without running them.
        show_output: If True, streams worker stdout/stderr in real time.
    """

    def __init__(
        self,
        output_file: Union[str, Path],
        seed: int = 512,
        number_of_workers: int = 1,
        number_of_events: int = -1,
        events_per_job: int = -1,
        event_numbers: Optional[Union[str, List[int]]] = None,
        merge: bool = True,
        ntuple_name: str = "particles",
        overwrite: bool = True,
        dry_run: bool = False,
        show_output: bool = False,
        number_of_threads: Optional[int] = None,
    ):
        super().__init__()
        self.output_file = str(output_file)
        self.seed = seed
        if number_of_threads is not None:
            self.number_of_workers = number_of_threads
        else:
            self.number_of_workers = number_of_workers
        self.number_of_threads = self.number_of_workers  # backwards-compatibility alias
        self.number_of_events = number_of_events
        self.events_per_job = events_per_job
        self.event_numbers = event_numbers
        self.merge = merge
        self.ntuple_name = ntuple_name
        self.overwrite = overwrite
        self.dry_run = dry_run
        self.show_output = show_output

    def get_events_per_job(self) -> int:
        """
        Calculates the number of events allocated to each job partition.

        Returns:
            Events count per job.
        """
        if self.events_per_job > 0:
            return self.events_per_job
        if self.number_of_workers > 0 and self.number_of_events > 0:
            return ceil(self.number_of_events / self.number_of_workers)
        return max(1, self.number_of_events)

    def build_plan(self) -> Dict[str, Dict[str, Any]]:
        """
        Partitions the event domain into chunks and assigns unique random seeds.

        Returns:
            Dictionary mapping intermediate chunk output filenames to their configuration:
            {
                "output.0.root": {"events": [0, 1, ...], "seed": 1234567, "event_start": 0},
                ...
            }
        """
        def get_random_seed() -> int:
            return random.randint(1, 900_000_000)

        # Parse event list: explicit event numbers vs range(total)
        if self.event_numbers:
            if isinstance(self.event_numbers, str):
                events_list = [int(x.strip()) for x in self.event_numbers.split(",") if x.strip()]
            else:
                events_list = list(self.event_numbers)
            self.number_of_events = len(events_list)
        else:
            total = max(0, self.number_of_events)
            events_list = list(range(total))

        step = self.get_events_per_job()
        chunks = [events_list[i : i + step] for i in range(0, len(events_list), step)]

        plan: Dict[str, Dict[str, Any]] = {}
        random.seed(self.seed)

        for idx, chunk_events in enumerate(chunks):
            chunk_file = append_index_to_file(self.output_file, idx)
            cfg: Dict[str, Any] = {
                "events": chunk_events,
                "seed": get_random_seed(),
            }
            # Optimize continuous ranges by passing event_start offset
            if not self.event_numbers and chunk_events:
                cfg["event_start"] = chunk_events[0]
            plan[chunk_file] = cfg
        return plan

    def print_plan(self, plan: Dict[str, Dict[str, Any]]) -> None:
        """
        Displays a structured, elegant terminal table showing the execution plan.

        Follows a strict color palette: blue, green, and dark gray.

        Args:
            plan: The partitioned execution plan generated by `build_plan()`.
        """
        try:
            from rich.console import Console
            from rich.table import Table
            from rich import box

            console = Console()
            table = Table(
                title=(
                    f"\n[bold blue]Lorenzetti Parallel Execution Plan[/bold blue]\n"
                    f"[grey50]Output: {self.output_file}  │  Workers: {self.number_of_workers}  │  "
                    f"Total Events: {self.number_of_events}  │  Merge: {self.merge}[/grey50]\n"
                ),
                box=box.ROUNDED,
                border_style="grey50",
                header_style="bold blue",
                show_footer=True,
                footer_style="grey50",
            )

            table.add_column("Job", justify="center", style="bold blue", footer="Total", footer_style="bold blue")
            table.add_column("Output Chunk", style="green", footer=f"{len(plan)} job(s)", footer_style="green")
            table.add_column("Events", justify="right", style="bold green", footer=str(self.number_of_events), footer_style="bold green")
            table.add_column("Event Range", justify="center", style="grey50", footer="-")
            table.add_column("Seed", justify="right", style="blue", footer=f"base={self.seed}", footer_style="blue")
            table.add_column("Status", justify="center", footer="-")

            for idx, (chunk_file, cfg) in enumerate(plan.items()):
                events = cfg.get("events", [])
                n_evts = len(events)
                if "event_start" in cfg:
                    start = cfg["event_start"]
                    end = start + n_evts - 1 if n_evts > 0 else start
                    range_str = f"[{start} → {end}]"
                elif events:
                    if len(events) <= 4:
                        range_str = str(events)
                    else:
                        range_str = f"[{events[0]}, {events[1]}, ... {events[-1]}]"
                else:
                    range_str = "[]"

                exists = check_file_exists(chunk_file, self.ntuple_name)
                if exists and not self.overwrite:
                    status_str = "[grey50]Skip (exists)[/grey50]"
                else:
                    status_str = "[bold green]Ready[/bold green]"

                table.add_row(
                    str(idx),
                    Path(chunk_file).name,
                    str(n_evts),
                    range_str,
                    str(cfg["seed"]),
                    status_str,
                )

            console.print(table)
            print()
        except Exception:
            self._logger.info(f"Execution plan: {len(plan)} chunk(s) to process.")

    def run_commands(self, commands: List[Tuple[str, List[str]]]) -> None:
        """
        Executes a list of worker commands concurrently via isolated subprocesses.

        Args:
            commands: List of tuples where each element contains `(chunk_file, command_arguments)`.

        Raises:
            RuntimeError: If any subprocess fails with a non-zero exit code.
        """
        def _exec_cmd(item: Tuple[str, List[str]]) -> str:
            chunk_file, cmd = item
            cmd_str = " ".join(cmd)
            self._logger.debug(f"Starting chunk process: {cmd_str}")

            if self.show_output:
                chunk_name = Path(chunk_file).name
                proc = subprocess.Popen(
                    cmd,
                    env=os.environ,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                )
                if proc.stdout:
                    for line in iter(proc.stdout.readline, ""):
                        print(f"[{chunk_name}] {line}", end="", flush=True)
                proc.wait()
                if proc.returncode != 0:
                    self._logger.error(
                        f"Job failed for chunk: {chunk_file}\n"
                        f"Command: {cmd_str}\n"
                        f"Exit code: {proc.returncode}"
                    )
                    raise RuntimeError(f"Subprocess failed for {chunk_file} (exit code {proc.returncode})")
                return chunk_file

            res = subprocess.run(cmd, env=os.environ, capture_output=True, text=True)
            if res.returncode != 0:
                self._logger.error(
                    f"Job failed for chunk: {chunk_file}\n"
                    f"Command: {cmd_str}\n"
                    f"Exit code: {res.returncode}\n"
                    f"--- STDERR ---\n{res.stderr}\n"
                    f"--- STDOUT ---\n{res.stdout}"
                )
                raise RuntimeError(f"Subprocess failed for {chunk_file} (exit code {res.returncode})")
            if res.stdout:
                self._logger.debug(f"[{chunk_file} stdout]: {res.stdout.strip()}")
            return chunk_file

        with ThreadPoolExecutor(max_workers=max(1, self.number_of_workers)) as executor:
            list(executor.map(_exec_cmd, commands))


def _extract_cli_flags(typer_app: typer.Typer) -> Tuple[Dict[str, str], Dict[str, str]]:
    """
    Extracts mapping of parameter names to their primary long CLI option flags
    and negative boolean flags (if any) from a Typer application.
    """
    param_flags: Dict[str, str] = {}
    neg_flags: Dict[str, str] = {}
    try:
        from typer.main import get_command
        click_cmd = get_command(typer_app)
        for p in click_cmd.params:
            long_opts = [opt for opt in p.opts if opt.startswith("--")]
            param_flags[p.name] = long_opts[0] if long_opts else (p.opts[0] if p.opts else f"--{p.name.replace('_', '-')}")
            if getattr(p, "secondary_opts", None):
                neg_flags[p.name] = p.secondary_opts[0]
    except Exception:
        pass
    return param_flags, neg_flags


def parallel_job(_func: Optional[Callable] = None, *, ntuple_name: str = "particles"):
    """
    Decorator that transforms a worker function into a production Typer CLI application
    with subprocess-based parallel processing.

    The decorated function should accept the following standard framework parameters:
    - `events: List[int]`: The list of event indices allocated to this execution chunk.
    - `output_file: str`: The destination output ROOT file path for this chunk.
    - `seed: int`: The pseudo-random seed assigned for this chunk.

    Any additional parameters with `Annotated[..., typer.Option(...)]` will automatically
    be exposed as CLI arguments and passed to child workers.

    Args:
        _func: The worker function to decorate (when used without parentheses).
        ntuple_name: The name of the primary TTree or object in the ROOT file
                     used to check for existing entries and validate outputs.

    Returns:
        A callable Typer application launcher.
    """
    def decorator(fn: Callable):
        sig = inspect.signature(fn)
        injected = {"events", "output_file", "seed"}

        worker_params = []
        for name, p in sig.parameters.items():
            if name not in injected:
                worker_params.append(p.replace(kind=inspect.Parameter.KEYWORD_ONLY))

        def job_file_callback(ctx: typer.Context, value: Optional[Path]):
            """Loads overrides from a JSON configuration file if provided."""
            if value and value.exists():
                with open(value, "r") as f:
                    data = json.load(f)
                    if "number_of_threads" in data and "number_of_workers" not in data:
                        data["number_of_workers"] = data["number_of_threads"]
                    ctx.default_map = ctx.default_map or {}
                    ctx.default_map.update(data)
            return value

        # Standard options injected by the ParallelJob framework into the CLI
        framework_params = [
            inspect.Parameter(
                "is_worker",
                inspect.Parameter.KEYWORD_ONLY,
                default=False,
                annotation=Annotated[bool, typer.Option("--is-worker", hidden=True, help="Internal worker flag")],
            ),
            inspect.Parameter(
                "event_start",
                inspect.Parameter.KEYWORD_ONLY,
                default=0,
                annotation=Annotated[int, typer.Option("--event-start", hidden=True, help="Internal event start offset")],
            ),
            inspect.Parameter(
                "output_file",
                inspect.Parameter.KEYWORD_ONLY,
                annotation=Annotated[Path, typer.Option("-o", "--output-file", help="Destination ROOT output file")],
            ),
            inspect.Parameter(
                "nov",
                inspect.Parameter.KEYWORD_ONLY,
                default=-1,
                annotation=Annotated[int, typer.Option("--nov", "--number-of-events", help="Total number of events to run")],
            ),
            inspect.Parameter(
                "number_of_workers",
                inspect.Parameter.KEYWORD_ONLY,
                default=1,
                annotation=Annotated[int, typer.Option("-nw", "--number-of-workers", "-nt", "--number-of-threads", help="Number of parallel worker processes")],
            ),
            inspect.Parameter(
                "events_per_job",
                inspect.Parameter.KEYWORD_ONLY,
                default=-1,
                annotation=Annotated[int, typer.Option("--events-per-job", help="Number of events per chunk/job")],
            ),
            inspect.Parameter(
                "seed",
                inspect.Parameter.KEYWORD_ONLY,
                default=512,
                annotation=Annotated[int, typer.Option("-s", "--seed", help="Base random seed")],
            ),
            inspect.Parameter(
                "event_numbers",
                inspect.Parameter.KEYWORD_ONLY,
                default=None,
                annotation=Annotated[Optional[str], typer.Option("-e", "--event-numbers", help="Comma-separated event numbers")],
            ),
            inspect.Parameter(
                "merge",
                inspect.Parameter.KEYWORD_ONLY,
                default=True,
                annotation=Annotated[bool, typer.Option("-m", "--merge/--no-merge", help="Merge chunk files with hadd")],
            ),
            inspect.Parameter(
                "overwrite",
                inspect.Parameter.KEYWORD_ONLY,
                default=True,
                annotation=Annotated[bool, typer.Option("--overwrite/--no-overwrite", help="Overwrite existing output files")],
            ),
            inspect.Parameter(
                "dry_run",
                inspect.Parameter.KEYWORD_ONLY,
                default=False,
                annotation=Annotated[bool, typer.Option("--dry-run", help="Dry run without executing jobs")],
            ),
            inspect.Parameter(
                "show_output",
                inspect.Parameter.KEYWORD_ONLY,
                default=False,
                annotation=Annotated[bool, typer.Option("--show-output/--no-show-output", "-v", help="Display stdout/stderr from worker processes in real time")],
            ),
            inspect.Parameter(
                "job_file",
                inspect.Parameter.KEYWORD_ONLY,
                default=None,
                annotation=Annotated[Optional[Path], typer.Option("--job-file", callback=job_file_callback, is_eager=True, help="JSON configuration file to override options")],
            ),
        ]

        all_params = framework_params + worker_params
        new_sig = sig.replace(parameters=all_params)

        def cli_entry(**kwargs):
            is_worker = kwargs.pop("is_worker", False)
            event_start = kwargs.pop("event_start", 0)
            output_file = kwargs.pop("output_file")
            nov = kwargs.pop("nov")
            base_seed = kwargs.pop("seed")
            event_numbers_str = kwargs.pop("event_numbers", None)

            # Orchestrator-only options
            n_workers = kwargs.pop("number_of_workers", kwargs.pop("number_of_threads", 1))
            events_per_job = kwargs.pop("events_per_job", -1)
            merge = kwargs.pop("merge", True)
            overwrite = kwargs.pop("overwrite", True)
            dry_run = kwargs.pop("dry_run", False)
            show_output = kwargs.pop("show_output", False)
            kwargs.pop("job_file", None)

            if is_worker:
                # =============================================================
                # WORKER MODE: Execute this single partition in clean process
                # =============================================================
                if event_numbers_str:
                    events = [int(x.strip()) for x in event_numbers_str.split(",") if x.strip()]
                else:
                    events = list(range(event_start, event_start + max(0, nov)))

                fn(events=events, output_file=str(output_file), seed=base_seed, **kwargs)
                return

            # =================================================================
            # ORCHESTRATOR MODE: Plan, dispatch subprocesses, and merge results
            # =================================================================
            if Path(output_file).is_dir():
                raise IsADirectoryError(f"Output file '{output_file}' was expected to be a file, but it is a directory.")

            job = ParallelJob(
                output_file=output_file,
                seed=base_seed,
                number_of_workers=n_workers,
                number_of_events=nov,
                events_per_job=events_per_job,
                event_numbers=event_numbers_str,
                merge=merge,
                ntuple_name=ntuple_name,
                overwrite=overwrite,
                dry_run=dry_run,
                show_output=show_output,
            )

            plan = job.build_plan()
            job.print_plan(plan)

            script_path = shutil.which(sys.argv[0]) or os.path.abspath(sys.argv[0])

            param_flags, neg_flags = _extract_cli_flags(app)
            commands_to_run: List[Tuple[str, List[str]]] = []
            for chunk_file, config in plan.items():
                if not check_file_exists(chunk_file, ntuple_name) or overwrite:
                    cmd = [
                        sys.executable,
                        script_path,
                        "--is-worker",
                        "-o", str(chunk_file),
                        "-s", str(config["seed"]),
                    ]
                    if "event_start" in config:
                        cmd.extend([
                            "--nov", str(len(config["events"])),
                            "--event-start", str(config["event_start"]),
                        ])
                    else:
                        cmd.extend([
                            "--nov", str(len(config["events"])),
                            "--event-numbers", ",".join(str(x) for x in config["events"]),
                        ])

                    for k, v in kwargs.items():
                        cli_flag = param_flags.get(k, f"--{k.replace('_', '-')}")
                        if isinstance(v, bool):
                            if v:
                                cmd.append(cli_flag)
                            elif k in neg_flags:
                                cmd.append(neg_flags[k])
                        elif isinstance(v, (list, tuple)):
                            for item in v:
                                cmd.extend([cli_flag, str(item)])
                        elif v is not None:
                            cmd.extend([cli_flag, str(v)])

                    commands_to_run.append((chunk_file, cmd))
                else:
                    job._logger.info(f"Skipping existing output: {chunk_file}")

            if dry_run:
                job._logger.info(f"[Dry Run] {len(commands_to_run)} jobs planned:")
                for chunk_file, cmd in commands_to_run:
                    job._logger.info(f"  Command: {' '.join(cmd)}")
                return

            if not commands_to_run:
                job._logger.info("No jobs to run (all outputs already exist).")
                return

            job._logger.info(f"Executing {len(commands_to_run)} jobs across {n_workers} processes...")
            job.run_commands(commands_to_run)

            all_chunk_files = list(plan.keys())
            if merge or len(all_chunk_files) == 1:
                job._logger.info(f"Merging {len(all_chunk_files)} chunk(s) into {output_file}...")
                merge_files(output_file, all_chunk_files)

        cli_entry.__signature__ = new_sig
        cli_entry.__annotations__ = {p.name: p.annotation for p in all_params}
        cli_entry.__doc__ = fn.__doc__

        app = typer.Typer(
            pretty_exceptions_enable=False,
            context_settings={"help_option_names": ["-h", "--help"]},
        )
        app.command()(cli_entry)

        def launcher(*args, **kw):
            if args or kw:
                return fn(*args, **kw)
            return app()

        launcher.app = app
        launcher.fn = fn
        return launcher

    if _func is None:
        return decorator
    return decorator(_func)


class FileParallelJob(Logger):
    """
    Manages file and directory batch partitioning, worker subprocess dispatching,
    and output merging.

    Attributes:
        input_path: Input file path, directory path, comma-separated paths, or glob pattern.
        output_path: Destination output file or directory path.
        number_of_threads: Total CPU threads allocated across all workers.
        threads_per_job: Number of CPU threads assigned to each worker subprocess
                         (-1 automatically assigns `number_of_threads` if 1 file, or 1 if >1 file).
        file_pattern: Glob pattern used to filter files when `input_path` is a directory.
        output_replace: Optional tuple `(old, new)` used to transform file names when saving to a directory.
        merge: If True and destination is a file, merges output ROOT files via `hadd -f`.
        ntuple_name: Name of TTree checked for file validation / skipping.
        overwrite: If True, re-executes and overwrites existing output files.
        dry_run: If True, plans execution and displays commands without running them.
        show_output: If True, streams worker stdout/stderr in real time.
    """

    def __init__(
        self,
        input_path: Union[str, Path],
        output_path: Union[str, Path],
        number_of_threads: int = 1,
        number_of_workers: Optional[int] = None,
        threads_per_job: int = -1,
        file_pattern: str = "*.root",
        output_replace: Optional[Tuple[str, str]] = None,
        merge: bool = False,
        ntuple_name: str = "CollectionTree",
        overwrite: bool = True,
        dry_run: bool = False,
        show_output: bool = False,
    ):
        super().__init__()
        self.input_path = str(input_path)
        self.output_path = str(output_path)
        self.number_of_threads = max(1, number_of_threads)
        self.number_of_workers = number_of_workers
        self.threads_per_job = threads_per_job
        self.file_pattern = file_pattern
        self.output_replace = output_replace
        self.merge = merge
        self.ntuple_name = ntuple_name
        self.overwrite = overwrite
        self.dry_run = dry_run
        self.show_output = show_output

    def discover_files(self) -> List[Path]:
        """
        Discovers all matching input files from path, directory, or pattern.

        Returns:
            Sorted list of resolved Path objects.
        """
        raw = self.input_path.strip()
        if "," in raw:
            return [Path(x.strip()) for x in raw.split(",") if x.strip()]

        p = Path(raw)
        if p.is_dir():
            matched = sorted([f for f in p.glob(self.file_pattern) if f.is_file()])
            if not matched and self.file_pattern != "*.root":
                matched = sorted([f for f in p.glob("*.root") if f.is_file()])
            return matched

        if any(c in raw for c in ["*", "?", "["]):
            return [Path(f) for f in sorted(glob.glob(raw)) if os.path.isfile(f)]

        return [p]

    def get_threads_and_concurrency(self, total_files: int) -> Tuple[int, int]:
        """
        Calculates `(threads_per_job, max_workers)` based on total cores, workers, and file count.

        Returns:
            Tuple of (threads_per_job, concurrency).
        """
        if self.threads_per_job > 0:
            tpj = self.threads_per_job
        elif total_files == 1:
            tpj = self.number_of_threads
        elif self.number_of_workers is not None and self.number_of_workers > 0 and self.number_of_threads > 1 and self.number_of_threads >= self.number_of_workers:
            tpj = max(1, self.number_of_threads // self.number_of_workers)
        else:
            tpj = 1

        if self.number_of_workers is not None and self.number_of_workers > 0:
            concurrency = self.number_of_workers
        else:
            concurrency = max(1, self.number_of_threads // tpj)

        return tpj, concurrency

    def build_plan(self) -> Dict[str, Dict[str, Any]]:
        """
        Builds the file execution plan mapping output file paths to job configurations.

        Returns:
            Dictionary mapping destination output filenames to their configuration:
            {
                "/out/file.0.HIT.root": {
                    "input_file": "/in/file.0.EVT.root",
                    "threads_per_job": 4,
                    "index": 0,
                },
                ...
            }
        """
        files = self.discover_files()
        if not files:
            raise FileNotFoundError(
                f"No input files found matching '{self.input_path}' with pattern '{self.file_pattern}'."
            )

        tpj, _ = self.get_threads_and_concurrency(len(files))
        out_p = Path(self.output_path)
        is_out_dir = out_p.is_dir() or str(self.output_path).endswith("/") or not out_p.suffix

        plan: Dict[str, Dict[str, Any]] = {}
        for idx, in_file in enumerate(files):
            if is_out_dir:
                out_p.mkdir(parents=True, exist_ok=True)
                out_name = in_file.name
                if self.output_replace:
                    out_name = out_name.replace(self.output_replace[0], self.output_replace[1])
                elif ".EVT." in out_name:
                    out_name = out_name.replace(".EVT.", ".HIT.")
                dest_file = str(out_p / out_name)
            else:
                if len(files) == 1:
                    dest_file = str(out_p)
                else:
                    dest_file = append_index_to_file(out_p, idx)

            plan[dest_file] = {
                "input_file": str(in_file),
                "threads_per_job": tpj,
                "index": idx,
            }
        return plan

    def print_plan(self, plan: Dict[str, Dict[str, Any]]) -> None:
        """
        Displays a structured terminal table showing the file execution plan.
        """
        try:
            from rich.console import Console
            from rich.table import Table
            from rich import box

            files = list(plan.keys())
            tpj, workers = self.get_threads_and_concurrency(len(files))

            console = Console()
            table = Table(
                title=(
                    f"\n[bold blue]Lorenzetti File Parallel Execution Plan[/bold blue]\n"
                    f"[grey50]Input: {self.input_path}  │  Output: {self.output_path}  │  "
                    f"Workers: {workers} worker(s)  │  Threads/Job: {tpj}  │  "
                    f"Total Cores: {workers * tpj}  │  Merge: {self.merge}[/grey50]\n"
                ),
                box=box.ROUNDED,
                border_style="grey50",
                header_style="bold blue",
                show_footer=True,
                footer_style="grey50",
            )

            table.add_column("Job", justify="center", style="bold blue", footer="Total", footer_style="bold blue")
            table.add_column("Input File", style="cyan", footer=f"{len(plan)} file(s)", footer_style="cyan")
            table.add_column("Output File", style="green", footer=f"{workers} worker(s)", footer_style="green")
            table.add_column("Threads", justify="right", style="bold green", footer=f"{workers} x {tpj} = {workers * tpj} cores", footer_style="bold green")
            table.add_column("Status", justify="center", footer="-")

            for idx, (out_file, cfg) in enumerate(plan.items()):
                in_name = Path(cfg["input_file"]).name
                out_name = Path(out_file).name
                exists = check_file_exists(out_file, self.ntuple_name)
                if exists and not self.overwrite:
                    status_str = "[grey50]Skip (exists)[/grey50]"
                else:
                    status_str = "[bold green]Ready[/bold green]"

                table.add_row(
                    str(idx),
                    in_name,
                    out_name,
                    str(cfg["threads_per_job"]),
                    status_str,
                )

            console.print(table)
            print()
        except Exception:
            self._logger.info(f"File execution plan: {len(plan)} file(s) to process.")

    def run_commands(self, commands: List[Tuple[str, List[str]]], max_workers: int) -> None:
        """
        Executes a list of worker commands concurrently via isolated subprocesses.

        Args:
            commands: List of tuples where each element contains `(output_file, command_arguments)`.
            max_workers: Maximum number of concurrent worker processes.

        Raises:
            RuntimeError: If any subprocess fails with a non-zero exit code.
        """
        def _exec_cmd(item: Tuple[str, List[str]]) -> str:
            out_file, cmd = item
            cmd_str = " ".join(cmd)
            self._logger.debug(f"Starting file process: {cmd_str}")

            if self.show_output:
                out_name = Path(out_file).name
                proc = subprocess.Popen(
                    cmd,
                    env=os.environ,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                )
                if proc.stdout:
                    for line in iter(proc.stdout.readline, ""):
                        print(f"[{out_name}] {line}", end="", flush=True)
                proc.wait()
                if proc.returncode != 0:
                    self._logger.error(
                        f"Job failed for file: {out_file}\n"
                        f"Command: {cmd_str}\n"
                        f"Exit code: {proc.returncode}"
                    )
                    raise RuntimeError(f"Subprocess failed for {out_file} (exit code {proc.returncode})")
                return out_file

            res = subprocess.run(cmd, env=os.environ, capture_output=True, text=True)
            if res.returncode != 0:
                self._logger.error(
                    f"Job failed for file: {out_file}\n"
                    f"Command: {cmd_str}\n"
                    f"Exit code: {res.returncode}\n"
                    f"--- STDERR ---\n{res.stderr}\n"
                    f"--- STDOUT ---\n{res.stdout}"
                )
                raise RuntimeError(f"Subprocess failed for {out_file} (exit code {res.returncode})")
            if res.stdout:
                self._logger.debug(f"[{out_file} stdout]: {res.stdout.strip()}")
            return out_file

        with ThreadPoolExecutor(max_workers=max(1, max_workers)) as executor:
            list(executor.map(_exec_cmd, commands))


def file_parallel_job(
    _func: Optional[Callable] = None,
    *,
    ntuple_name: str = "CollectionTree",
    output_replace: Optional[Tuple[str, str]] = None,
    default_threads_per_job: int = -1,
):
    """
    Decorator that transforms a worker function into a production Typer CLI application
    with file-based batch parallel processing across isolated subprocesses.

    The decorated function should accept:
    - `input_file: Union[str, Path]`: Path to a single input ROOT file.
    - `output_file: Union[str, Path]`: Path to the corresponding output ROOT file.
    - `number_of_threads: int`: Threads allocated to this specific worker instance (e.g. for Geant4 MT).

    Any additional parameters with `Annotated[..., typer.Option(...)]` will automatically
    be exposed as CLI arguments and passed to child workers.

    Args:
        _func: The worker function to decorate.
        ntuple_name: The name of the primary TTree or object in the ROOT file
                     used to check for existing entries and validate outputs.
        output_replace: Optional tuple `(old_pattern, new_pattern)` to replace in file stems.
        default_threads_per_job: Default threads allocated per worker process (-1 for auto).

    Returns:
        A callable Typer application launcher.
    """
    def decorator(fn: Callable):
        sig = inspect.signature(fn)
        injected = {"input_file", "output_file", "number_of_threads", "input", "output", "threads"}

        worker_params = []
        for name, p in sig.parameters.items():
            if name not in injected:
                worker_params.append(p.replace(kind=inspect.Parameter.KEYWORD_ONLY))

        def job_file_callback(ctx: typer.Context, value: Optional[Path]):
            """Loads overrides from a JSON configuration file if provided."""
            if value and value.exists():
                with open(value, "r") as f:
                    data = json.load(f)
                    ctx.default_map = ctx.default_map or {}
                    ctx.default_map.update(data)
            return value

        framework_params = [
            inspect.Parameter(
                "is_worker",
                inspect.Parameter.KEYWORD_ONLY,
                default=False,
                annotation=Annotated[bool, typer.Option("--is-worker", hidden=True, help="Internal worker flag")],
            ),
            inspect.Parameter(
                "input_file",
                inspect.Parameter.KEYWORD_ONLY,
                annotation=Annotated[Path, typer.Option("-i", "--input-file", help="Input ROOT file or directory")],
            ),
            inspect.Parameter(
                "output_file",
                inspect.Parameter.KEYWORD_ONLY,
                annotation=Annotated[Path, typer.Option("-o", "--output-file", help="Destination ROOT output file or directory")],
            ),
            inspect.Parameter(
                "number_of_workers",
                inspect.Parameter.KEYWORD_ONLY,
                default=None,
                annotation=Annotated[Optional[int], typer.Option("-nw", "--number-of-workers", help="Number of concurrent worker processes to process files")],
            ),
            inspect.Parameter(
                "number_of_threads",
                inspect.Parameter.KEYWORD_ONLY,
                default=1,
                annotation=Annotated[int, typer.Option("-nt", "--number-of-threads", help="Total number of threads/cores (or threads per worker)")],
            ),
            inspect.Parameter(
                "threads_per_job",
                inspect.Parameter.KEYWORD_ONLY,
                default=default_threads_per_job,
                annotation=Annotated[int, typer.Option("--threads-per-job", help="Threads allocated per worker process (-1 for auto)")],
            ),
            inspect.Parameter(
                "file_pattern",
                inspect.Parameter.KEYWORD_ONLY,
                default="*.root",
                annotation=Annotated[str, typer.Option("--pattern", "--file-pattern", help="File pattern matching for directory input")],
            ),
            inspect.Parameter(
                "merge",
                inspect.Parameter.KEYWORD_ONLY,
                default=False,
                annotation=Annotated[bool, typer.Option("-m", "--merge/--no-merge", help="Merge output ROOT files with hadd")],
            ),
            inspect.Parameter(
                "overwrite",
                inspect.Parameter.KEYWORD_ONLY,
                default=True,
                annotation=Annotated[bool, typer.Option("--overwrite/--no-overwrite", help="Overwrite existing output files")],
            ),
            inspect.Parameter(
                "dry_run",
                inspect.Parameter.KEYWORD_ONLY,
                default=False,
                annotation=Annotated[bool, typer.Option("--dry-run", help="Dry run without executing jobs")],
            ),
            inspect.Parameter(
                "show_output",
                inspect.Parameter.KEYWORD_ONLY,
                default=False,
                annotation=Annotated[bool, typer.Option("--show-output/--no-show-output", "-v", help="Display stdout/stderr from worker processes in real time")],
            ),
            inspect.Parameter(
                "job_file",
                inspect.Parameter.KEYWORD_ONLY,
                default=None,
                annotation=Annotated[Optional[Path], typer.Option("--job-file", callback=job_file_callback, is_eager=True, help="JSON configuration file to override options")],
            ),
        ]

        all_params = framework_params + worker_params
        new_sig = sig.replace(parameters=all_params)

        def cli_entry(**kwargs):

            is_worker = kwargs.pop("is_worker", False)
            input_file = kwargs.pop("input_file")
            output_file = kwargs.pop("output_file")
            n_workers = kwargs.pop("number_of_workers", None)
            n_threads = kwargs.pop("number_of_threads", 1)
            tpj = kwargs.pop("threads_per_job", default_threads_per_job)
            file_pattern = kwargs.pop("file_pattern", "*.root")
            merge = kwargs.pop("merge", False)
            overwrite = kwargs.pop("overwrite", True)
            dry_run = kwargs.pop("dry_run", False)
            show_output = kwargs.pop("show_output", False)
            kwargs.pop("job_file", None)

            if is_worker:
                # WORKER MODE: Execute this single file in clean process
                call_kw = {}
                if "input_file" in sig.parameters:
                    call_kw["input_file"] = str(input_file)
                elif "input" in sig.parameters:
                    call_kw["input"] = str(input_file)
                if "output_file" in sig.parameters:
                    call_kw["output_file"] = str(output_file)
                elif "output" in sig.parameters:
                    call_kw["output"] = str(output_file)
                if "number_of_threads" in sig.parameters:
                    call_kw["number_of_threads"] = n_threads
                elif "threads" in sig.parameters:
                    call_kw["threads"] = n_threads

                for k, v in kwargs.items():
                    if k in sig.parameters:
                        call_kw[k] = v
                fn(**call_kw)
                return

            # ORCHESTRATOR MODE: Plan, dispatch subprocesses, and optionally merge
            job = FileParallelJob(
                input_path=input_file,
                output_path=output_file,
                number_of_threads=n_threads,
                number_of_workers=n_workers,
                threads_per_job=tpj,
                file_pattern=file_pattern,
                output_replace=output_replace,
                merge=merge,
                ntuple_name=ntuple_name,
                overwrite=overwrite,
                dry_run=dry_run,
                show_output=show_output,
            )

            plan = job.build_plan()
            job.print_plan(plan)

            script_path = shutil.which(sys.argv[0]) or os.path.abspath(sys.argv[0])
            actual_tpj, concurrency = job.get_threads_and_concurrency(len(plan))

            param_flags, neg_flags = _extract_cli_flags(app)
            commands_to_run: List[Tuple[str, List[str]]] = []
            for dest_file, cfg in plan.items():
                if not check_file_exists(dest_file, ntuple_name) or overwrite:
                    cmd = [
                        sys.executable,
                        script_path,
                        "--is-worker",
                        "-i", str(cfg["input_file"]),
                        "-o", str(dest_file),
                        "-nt", str(cfg["threads_per_job"]),
                    ]
                    for k, v in kwargs.items():
                        cli_flag = param_flags.get(k, f"--{k.replace('_', '-')}")
                        if isinstance(v, bool):
                            if v:
                                cmd.append(cli_flag)
                            elif k in neg_flags:
                                cmd.append(neg_flags[k])
                        elif isinstance(v, (list, tuple)):
                            for item in v:
                                cmd.extend([cli_flag, str(item)])
                        elif v is not None:
                            cmd.extend([cli_flag, str(v)])

                    commands_to_run.append((dest_file, cmd))
                else:
                    job._logger.info(f"Skipping existing output: {dest_file}")

            if dry_run:
                job._logger.info(f"[Dry Run] {len(commands_to_run)} file job(s) planned:")
                for dest_file, cmd in commands_to_run:
                    job._logger.info(f"  Command: {' '.join(cmd)}")
                return

            if not commands_to_run:
                job._logger.info("No jobs to run (all outputs already exist).")
                return

            job._logger.info(
                f"Executing {len(commands_to_run)} jobs across {concurrency} worker(s) ({actual_tpj} threads each)..."
            )
            job.run_commands(commands_to_run, max_workers=concurrency)

            out_p = Path(output_file)
            is_out_dir = out_p.is_dir() or str(output_file).endswith("/") or not out_p.suffix
            all_dest_files = list(plan.keys())
            if merge and not is_out_dir and len(all_dest_files) > 1:
                job._logger.info(f"Merging {len(all_dest_files)} file(s) into {output_file}...")
                merge_files(output_file, all_dest_files)

        cli_entry.__signature__ = new_sig
        cli_entry.__annotations__ = {p.name: p.annotation for p in all_params}
        cli_entry.__doc__ = fn.__doc__

        app = typer.Typer(
            pretty_exceptions_enable=False,
            context_settings={"help_option_names": ["-h", "--help"]},
        )
        app.command()(cli_entry)

        def launcher(*args, **kw):
            if args or kw:
                return fn(*args, **kw)
            return app()

        launcher.app = app
        launcher.fn = fn
        return launcher

    if _func is None:
        return decorator
    return decorator(_func)

