__all__ = [
    "Parallel",
    "job",
    "paralle",
]

import ROOT
import joblib
import traceback
import inspect
import functools
import json
import os
import sys
import typer
from typing import List, Dict, Annotated
from pathlib import Path
from pprint import pprint

from reco import append_index_to_file, check_file_exists, merge

app = typer.Typer(add_completion=False)


class Parallel:
    """
    A class to run event reconstruction jobs in parallel.
    It builds a plan by checking entries in ROOT files and splitting the work
    into smaller event chunks per job, executing them in parallel using joblib.
    """

    def __init__(self,
                 files             : List[str],
                 output_file       : str,
                 number_of_threads : int = 1,
                 number_of_events  : int = -1,
                 events_per_job    : int = -1,
                 merge             : bool = False,
                 ntuple_name       : str = "CollectionTree",
                 overwrite         : bool = False,
                 dry_run           : bool = False,
                ):  
        self.files             = files
        self.output_file       = output_file
        self.number_of_threads = number_of_threads
        self.number_of_events  = number_of_events
        self.events_per_job    = events_per_job
        self.merge_files       = merge
        self.ntuple_name       = ntuple_name
        self.overwrite         = overwrite
        self.dry_run           = dry_run

    def build_plan(self) -> List[tuple]:
        """
        Builds a list of job tuples: (input_file, output_file, event_range).
        """
        jobs = []
        total_events_scheduled = 0

        for file_idx, path in enumerate(self.files):
            try:
                f = ROOT.TFile.Open(path, "READ")
                if not f or f.IsZombie():
                    print(f"Error: Cannot open ROOT file {path}")
                    continue
                tree = f.Get(self.ntuple_name)
                entries = tree.GetEntries() if tree else 0
                f.Close()
            except Exception as e:
                traceback.print_exc()
                print(f"Error reading file {path}: {e}")
                continue

            if entries <= 0:
                continue

            # Determine chunking of event indices
            if self.events_per_job > 0:
                chunks_list = [list(range(i, min(i + self.events_per_job, entries)))
                               for i in range(0, entries, self.events_per_job)]
            else:
                chunks_list = [list(range(entries))]

            output_per_file = append_index_to_file(self.output_file, file_idx)
            
            for job_idx, events in enumerate(chunks_list):
                if 0 < self.number_of_events <= total_events_scheduled:
                    break

                # Trim the chunk if it exceeds the remaining number of requested events
                if self.number_of_events > 0 and (total_events_scheduled + len(events)) > self.number_of_events:
                    events = events[:self.number_of_events - total_events_scheduled]

                output_file_per_job = append_index_to_file(output_per_file, job_idx)

                # Skip job if output already exists and overwrite is False
                if self.overwrite or not check_file_exists(output_file_per_job, self.ntuple_name):
                    jobs.append((path, output_file_per_job, events))

                total_events_scheduled += len(events)

        return jobs

    def __call__(self, function, **args):
        jobs = self.build_plan()
        pprint(jobs)

        # Dynamic parameter mapping to adapt function signature
        sig = inspect.signature(function)
        
        def adapter_func(events, input_file, output_file, **kwargs):
            call_kwargs = {}
            if "events" in sig.parameters:
                call_kwargs["events"] = events
            if "input" in sig.parameters:
                call_kwargs["input"] = input_file
            elif "input_file" in sig.parameters:
                call_kwargs["input_file"] = input_file
            if "output" in sig.parameters:
                call_kwargs["output"] = output_file
            elif "output_file" in sig.parameters:
                call_kwargs["output_file"] = output_file
                
            for k, v in kwargs.items():
                if k in sig.parameters:
                    call_kwargs[k] = v
            return function(**call_kwargs)
        
        if not self.dry_run and jobs:
            pool = joblib.Parallel(n_jobs=self.number_of_threads)
            pool(
                joblib.delayed(adapter_func)(events=events, input_file=input_file, output_file=output_file, **args)
                for input_file, output_file, events in jobs
            )

        # Merge output files if requested
        if self.merge_files and jobs:
            output_files = [job[1] for job in jobs]
            merge(self.output_file, output_files)


def job(
    input: Annotated[Path, typer.Option("-i", "--input-file", help="The input file or folder to run the job.")],
    output: Annotated[Path, typer.Option("-o", "--output-file", help="The output file.")],
    command: Annotated[str, typer.Option("-c", "--command", help="The preexec/shell command to run.")] = "''",
):
    """
    Main function to execute a shell command replacing %IN and %OUT
    """
    cmd = command.replace("%IN", str(input)).replace("%OUT", str(output))
    print(f"Executing command: {cmd}")
    ret = os.system(cmd)
    if ret != 0:
        raise RuntimeError(f"Command failed with code {ret}: {cmd}")


def paralle(
    job_func,
    nov: Annotated[int, typer.Option("--nov", "--number-of-events", help="The total number of events to run.")] = -1,
    threads: Annotated[int, typer.Option("-nt", "--number-of-threads", help="The number of threads.")] = 1,
    events_per_job: Annotated[int, typer.Option("--events-per-job", help="The number of events per job.")] = -1,
    merge: Annotated[bool, typer.Option("-m", "--merge", help="Merge all files.")] = False,
    ntuple_name: Annotated[str, typer.Option("--ntuple-name", help="The ntuple name.")] = "CollectionTree",
    overwrite: Annotated[bool, typer.Option("--overwrite", help="Overwrite existing files.")] = False,
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Perform a dry run without executing jobs.")] = False,
    job_file: Annotated[Path, typer.Option("--job-file", help="The JSON file used to configure this job automatically.")] = None,
    **job_kwargs
):
    args = {
        "nov": nov,
        "threads": threads,
        "events_per_job": events_per_job,
        "merge": merge,
        "ntuple_name": ntuple_name,
        "overwrite": overwrite,
        "dry_run": dry_run,
        **job_kwargs
    }

    if job_file:
        job_file = Path(job_file)
        if not job_file.exists():
            raise FileNotFoundError(f"Input job file {job_file} not found.")
        with open(str(job_file), 'r') as f:
            d = json.load(f)
            for k, v in d.items():
                json_key = k
                # Map old keys to new parameters
                if k == "number_of_threads": json_key = "threads"
                elif k == "number_of_events": json_key = "nov"
                elif k == "input_file": json_key = "input"
                elif k == "output_file": json_key = "output"
                
                if json_key in args:
                    if json_key in ["input", "output", "job_file"] and v is not None:
                        args[json_key] = Path(v)
                    else:
                        args[json_key] = v
                    print(f"overwriting {json_key} with value {v}")

    input_val = Path(args["input"])
    if not input_val.exists():
        raise FileNotFoundError(f"Input file {input_val} not found.")
    if input_val.is_dir():
        from expand_folders import expand_folders
        files = expand_folders(os.path.abspath(input_val))
    else:
        files = [os.path.abspath(input_val)]

    pool = Parallel(
        files=files,
        output_file=str(args["output"]),
        number_of_threads=args["threads"],
        number_of_events=args["nov"],
        events_per_job=args["events_per_job"],
        merge=args["merge"],
        ntuple_name=args["ntuple_name"],
        overwrite=args["overwrite"],
        dry_run=args["dry_run"],
    )
    
    # Run parallel execution using job_func
    job_args = {k: v for k, v in args.items() if k not in ["nov", "threads", "events_per_job", "merge", "ntuple_name", "overwrite", "dry_run", "job_file"]}
    pool(
        job_func,
        **job_args
    )


def fuse_menus(job_func, paralle_func):
    sig_job = inspect.signature(job_func)
    sig_para = inspect.signature(paralle_func)
    
    para_params = [p for p in sig_para.parameters.values() if p.name not in ["job_func", "job_kwargs", "kwargs"]]
    job_params = list(sig_job.parameters.values())
    
    existing_names = {p.name for p in para_params}
    new_params = list(para_params)
    for p in job_params:
        if p.name not in existing_names:
            new_params.append(p)
            
    non_defaults = [p for p in new_params if p.default is inspect.Parameter.empty]
    defaults = [p for p in new_params if p.default is not inspect.Parameter.empty]
    
    new_sig = inspect.Signature(parameters=non_defaults + defaults)
    
    def wrapper(**kwargs):
        return paralle_func(job_func, **kwargs)
        
    wrapper.__signature__ = new_sig
    return wrapper


if __name__ == "__main__":
    fused_cmd = fuse_menus(job, paralle)
    app.command()(fused_cmd)
    app()
