#!/usr/bin/env python3

from pathlib import Path
from typing_extensions import Annotated
import typer

from GaugiKernel import file_parallel_job, ComponentAccumulator, LoggingLevel
from RootStreamBuilder import RootStreamESDReader, recordable, clear_recorded_items, RootStreamAODMaker
from CaloClusterBuilder import CaloClusterMaker
from CaloRingsBuilder import CaloRingsBuilderCfg
from EgammaBuilder import ElectronBuilderCfg


@file_parallel_job(ntuple_name="CollectionTree", output_replace=(".ESD.", ".AOD."))
def main(
    input_file: Annotated[str | Path, typer.Option("-i", "--input-file", help="Path to input ESD file or directory")],
    output_file: Annotated[str | Path, typer.Option("-o", "--output-file", help="Path to output AOD file or directory")],
    number_of_threads: Annotated[int, typer.Option("-nt", "--number-of-threads", help="Threads allocated per worker")] = 1,
    nov: Annotated[int, typer.Option("--nov", "--number-of-events", help="The total number of events to run.")] = -1,
    output_level: Annotated[str, typer.Option("-l", "--output-level", help="Logging verbosity.")] = "INFO",
    filter_by_sigma: Annotated[bool, typer.Option("--filter-by-sigma/--no-filter-by-sigma", help="Filter cells by noise sigma threshold.")] = False,
    sigma_threshold: Annotated[float, typer.Option("--sigma-threshold", help="Noise sigma threshold for cell filtering (E > threshold * sigma).")] = 2.0,
    preexec: Annotated[str, typer.Option("-p", "--preexec", help="The preexec command to run before reconstruction.")] = "''",
):
    """
    Executes the offline reconstruction chain.
    Reads digitized cells (ESD), builds calorimeter clusters, computes
    ring variables (Rings), and reconstructs electron candidates.
    """
    clear_recorded_items()

    input_file = str(input_file)
    output_file = str(output_file)
    outputLevel = LoggingLevel.toC(output_level)

    exec(preexec)


    ESD = RootStreamESDReader(
        "ESDReader",
        InputFile=input_file,
        OutputCellsKey=recordable("Cells"),
        OutputCellsTruthKey=recordable("TruthCells"),
        OutputEventKey=recordable("Events"),
        OutputTruthKey=recordable("Particles"),
        OutputSeedsKey=recordable("Seeds"),
        FilterBySigma=filter_by_sigma,
        SigmaThreshold=sigma_threshold,
        OutputLevel=outputLevel,
    )

    acc = ComponentAccumulator("ComponentAccumulator", output_file, ESD)

    cluster = CaloClusterMaker(
        "CaloClusterMaker",
        InputCellsKey=recordable("Cells"),
        InputSeedsKey=recordable("Seeds"),
        OutputClusterKey=recordable("Clusters"),
        HistogramPath="Expert/Clusters",
        OutputLevel=outputLevel,
    )

    hypo = ElectronBuilderCfg(
        "ElectronBuilder",
        InputClusterKey=recordable("Clusters"),
        OutputElectronKey=recordable("Electrons"),
        OutputLevel=outputLevel,
    )

    acc_rings = CaloRingsBuilderCfg(
        "CaloRingsBuilder",
        InputClusterKey=recordable("Clusters"),
        OutputRingerKey=recordable("Rings"),
        HistogramPath="Expert/Rings",
        OutputLevel=outputLevel,
    )

    AOD = RootStreamAODMaker(
        "RootStreamAODMaker",
        OutputLevel=outputLevel,
    )

    acc += cluster
    acc += acc_rings
    acc += hypo
    acc += AOD
    acc.run(nov)


if __name__ == "__main__":
    main()
