#!/usr/bin/env python3

from pathlib import Path
from typing_extensions import Annotated
import typer

from GaugiKernel import file_parallel_job, ComponentAccumulator, LoggingLevel
from CaloCellBuilder import CaloCellBuilder
from RootStreamBuilder import RootStreamHITReader, recordable, clear_recorded_items, RootStreamESDMaker
from geometry import DetectorConstruction_v1


@file_parallel_job(ntuple_name="CollectionTree", output_replace=(".HIT.", ".ESD."))
def main(
    input_file: Annotated[str | Path, typer.Option("-i", "--input-file", help="Path to input HIT file or directory")],
    output_file: Annotated[str | Path, typer.Option("-o", "--output-file", help="Path to output ESD file or directory")],
    number_of_threads: Annotated[int, typer.Option("-nt", "--number-of-threads", help="Threads allocated per worker")] = 1,
    nov: Annotated[int, typer.Option("--nov", "--number-of-events", help="Number of events to process.")] = -1,
    output_level: Annotated[str, typer.Option("-l", "--output-level", help="Logging verbosity level.")] = "INFO",
    filter_by_sigma: Annotated[bool, typer.Option("--filter-by-sigma/--no-filter-by-sigma", help="Filter cells by noise sigma threshold.")] = True,
    sigma_threshold: Annotated[float, typer.Option("--sigma-threshold", help="Noise sigma threshold for cell filtering (E > threshold * sigma).")] = 2.0,
    pre_init: Annotated[str, typer.Option("--pre-init", help="Hook for pre-initialization code.")] = "''",
    pre_exec: Annotated[str, typer.Option("--pre-exec", help="Hook for pre-execution code.")] = "''",
    post_exec: Annotated[str, typer.Option("--post-exec", help="Hook for post-execution code.")] = "''",
):
    """
    Main function for the digitization process.

    Reads Hits from the input file, simulates the calorimeter readout electronics
    (CaloCellBuilder), and produces an Event Summary Data (ESD) file containing
    calorimeter cells.
    """
    clear_recorded_items()

    input_file = str(input_file)
    output_file = str(output_file)
    outputLevel = LoggingLevel.toC(output_level)

    exec(pre_init)


    HIT = RootStreamHITReader(
        "HITReader",
        InputFile=input_file,
        OutputHitsKey=recordable("Hits"),
        OutputEventKey=recordable("Events"),
        OutputTruthKey=recordable("Particles"),
        OutputSeedsKey=recordable("Seeds"),
        OutputLevel=outputLevel,
    )

    acc = ComponentAccumulator("ComponentAccumulator", output_file, HIT)

    calorimeter = CaloCellBuilder(
        "CaloCellBuilder",
        DetectorConstruction_v1("ATLAS"),
        HistogramPath="Expert/Cells",
        OutputLevel=outputLevel,
        InputHitsKey=recordable("Hits"),
        OutputCellsKey=recordable("Cells"),
        OutputTruthCellsKey=recordable("TruthCells"),
        InputEventKey=recordable("Events"),
        FilterBySigma=filter_by_sigma,
        SigmaThreshold=sigma_threshold,
    )
    calorimeter.merge(acc)

    ESD = RootStreamESDMaker(
        "RootStreamESDMaker",
        OutputLevel=outputLevel,
    )
    acc += ESD

    exec(pre_exec)
    acc.run(nov)
    exec(post_exec)


if __name__ == "__main__":
    main()
