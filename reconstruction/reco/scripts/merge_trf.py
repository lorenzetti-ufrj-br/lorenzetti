#!/usr/bin/env python3

import os
import glob
from pathlib import Path
from typing import List
from typing_extensions import Annotated
import typer

import ROOT
from GaugiKernel import file_parallel_job, ComponentAccumulator, LoggingLevel
from RootStreamBuilder import RootStreamHITReader, recordable, clear_recorded_items, RootStreamHITMaker


@file_parallel_job(ntuple_name="CollectionTree", output_replace=(".HIT.", ".HIT_Merged."))
def main(
    input_file: Annotated[str | Path, typer.Option("-i", "--input-file", help="Input signal HIT file or directory")],
    output_file: Annotated[str | Path, typer.Option("-o", "--output-file", help="Output merged HIT file or directory")],
    low_pileup_files: Annotated[str, typer.Option("--low-pileup-files", help="Path or directory of low pileup HIT files")],
    high_pileup_files: Annotated[str, typer.Option("--high-pileup-files", help="Path or directory of high pileup HIT files")],
    pileup_avg: Annotated[int, typer.Option("--pileup-avg", help="Average pileup value")],
    pileup_sigma: Annotated[int, typer.Option("--pileup-sigma", help="Pileup sigma value")],
    number_of_threads: Annotated[int, typer.Option("-nt", "--number-of-threads", help="Threads allocated per worker")] = 1,
    nov: Annotated[int, typer.Option("--nov", "--number-of-events", help="The total number of events to run.")] = -1,
    output_level: Annotated[str, typer.Option("-l", "--output-level", help="Logging verbosity level.")] = "INFO",
    command: Annotated[str, typer.Option("-c", "--command", help="The preexec command")] = "''",
):
    """
    Simulates pileup superposition by overlaying minimum bias events onto signal events.
    """
    clear_recorded_items()

    input_file = str(input_file)
    output_file = str(output_file)
    outputLevel = LoggingLevel.toC(output_level)

    exec(command)

    def resolve_files(p_str: str) -> List[str]:
        p = Path(p_str)
        if p.is_dir():
            return [str(f) for f in sorted(p.glob("*.root"))]
        if any(c in p_str for c in ["*", "?", "["]):
            return sorted(glob.glob(p_str))
        return [str(p)]

    low_list = resolve_files(low_pileup_files)
    high_list = resolve_files(high_pileup_files)

    acc = ComponentAccumulator("ComponentAccumulator", output_file)

    reader = RootStreamHITReader(
        "HITReader",
        InputFile=input_file,
        OutputHitsKey=recordable("Hits"),
        OutputEventKey=recordable("Events"),
        OutputTruthKey=recordable("Particles"),
        OutputSeedsKey=recordable("Seeds"),
        OutputLevel=outputLevel,
    )
    reader.merge(acc)

    pileup = ROOT.PileupMerge(
        "PileupMerge",
        LowPileupInputFiles=low_list,
        HighPileupInputFiles=high_list,
        PileupAvg=pileup_avg,
        PileupSigma=pileup_sigma,
        InputHitsKey=recordable("Hits"),
        InputEventKey=recordable("Events"),
        OutputHitsKey="Hits_Merged",
        OutputEventKey="Events_Merged",
        OutputLevel=outputLevel,
    )
    acc += pileup

    HIT = RootStreamHITMaker(
        "RootStreamHITMaker",
        InputHitsKey="Hits_Merged",
        InputEventKey="Events_Merged",
        InputTruthKey=recordable("Particles"),
        InputSeedsKey=recordable("Seeds"),
        OutputLevel=outputLevel,
    )
    acc += HIT
    acc.run(nov)


if __name__ == "__main__":
    main()
