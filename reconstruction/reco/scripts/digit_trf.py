#!/usr/bin/env python3
from __future__ import annotations
"""
Script: digit_trf.py
Purpose: Performs the digitization step in the simulation chain.
         Converts Geant4 energy hits into digital signals (cells) by simulating
         electronic logical pulses, noise, and cross-talk.
Usage:
    digit_trf.py -i input.HIT.root -o output.ESD.root [options]
"""

from pathlib import Path
from typing_extensions import Annotated
import typer

from GaugiKernel import file_parallel_job, ComponentAccumulator, LoggingLevel
from CaloCellBuilder import CaloCellBuilder
from RootStreamBuilder import (
    RootStreamHITReader,
    recordable,
    clear_recorded_items,
    RootStreamESDMaker,
    RootStreamESDFlags,
)
from GeoBase import DetectorConstructionCfg


@file_parallel_job(ntuple_name="CollectionTree", output_replace=(".HIT", ".ESD"))
def main(
    input_file: Annotated[str | Path, typer.Option("-i", "--input-file", help="Path to input HIT file or directory")],
    output_file: Annotated[str | Path, typer.Option("-o", "--output-file", help="Path to output ESD file or directory")],
    number_of_threads: Annotated[int, typer.Option("-nt", "--number-of-threads", help="Threads allocated per worker")] = 1,
    nov: Annotated[int, typer.Option("--nov", "--number-of-events", help="Number of events to process.")] = -1,
    output_level: Annotated[str, typer.Option("-l", "--output-level", help="Logging verbosity level.")] = "INFO",
    detector: Annotated[str, typer.Option("--detector", help="Detector version ('v1' or 'v2').")] = "v1",
    save_all_cells: Annotated[bool, typer.Option("--save-all-cells", help="Save all cells in the ESD.")] = False,
    pre_init: Annotated[str, typer.Option("--pre-init", help="Hook for pre-initialization code.")] = "''",
    pre_exec: Annotated[str, typer.Option("--pre-exec", help="Hook for pre-execution code.")] = "''",
    post_exec: Annotated[str, typer.Option("--post-exec", help="Hook for post-execution code.")] = "''",
):
    clear_recorded_items()

    input_file = str(input_file)
    output_file = str(output_file)
    outputLevel = LoggingLevel.toC(output_level)

    if save_all_cells:
        RootStreamESDFlags.SaveAllCells = True
        RootStreamESDFlags.OnlyRoI = False

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

    det = DetectorConstructionCfg("ATLAS", version=detector)

    calorimeter = CaloCellBuilder(
        "CaloCellBuilder",
        det,
        HistogramPath="Expert/Cells",
        OutputLevel=outputLevel,
        InputHitsKey=recordable("Hits"),
        OutputCellsKey=recordable("Cells"),
        OutputTruthCellsKey=recordable("TruthCells"),
        InputEventKey=recordable("Events"),
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
