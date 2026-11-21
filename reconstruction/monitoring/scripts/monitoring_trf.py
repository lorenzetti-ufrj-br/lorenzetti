#!/usr/bin/env python3

from pathlib import Path
from typing_extensions import Annotated
import typer

from GaugiKernel import file_parallel_job, ComponentAccumulator, LoggingLevel
from RootStreamBuilder import RootStreamAODReader, recordable
from EgammaMonitoring import EgammaMonitoringMakerCfg


@file_parallel_job(ntuple_name="", output_replace=(".AOD", ".expert_monitoring"))
def main(
    input_file: Annotated[str | Path, typer.Option("-i", "--input-file", help="The input AOD file or folder to run the job.")],
    output_file: Annotated[str | Path, typer.Option("-o", "--output-file", help="The output expert monitoring ROOT file or folder.")] = "expert_monitoring.root",
    number_of_threads: Annotated[int, typer.Option("-nt", "--number-of-threads", help="Threads allocated per worker")] = 1,
    nov: Annotated[int, typer.Option("--nov", "--number-of-events", help="The total number of events to run.")] = -1,
    output_level: Annotated[str, typer.Option("-l", "--output-level", help="Logging verbosity.")] = "INFO",
    preexec: Annotated[str, typer.Option("-p", "--preexec", help="The preexec command to run before execution.")] = "''",
    hist_dir: Annotated[str, typer.Option("-d", "--hist-dir", help="Base directory name inside ROOT file.")] = "Expert-Monitoring",
):
    """
    Extracts expert monitoring histograms (expert_monitoring.root) from AOD input files.
    """
    input_file = str(input_file)
    output_file = str(output_file)
    outputLevel = LoggingLevel.toC(output_level)

    exec(preexec)

    AOD = RootStreamAODReader(
        "AODReader",
        InputFile=input_file,
        TreeName="CollectionTree",
        OutputLevel=outputLevel,
    )

    acc = ComponentAccumulator("ComponentAccumulator", output_file, AOD)

    mon = EgammaMonitoringMakerCfg(
        "EgammaMonitoringMaker",
        Directory=hist_dir,
        InputEventInfoKey=recordable("Events"),
        InputClusterKey=recordable("Clusters"),
        InputElectronKey=recordable("Electrons"),
        InputRingsKey=recordable("Rings"),
        InputRingsKeys=[
            recordable("Rings"),
            recordable("Rings_Asym"),
            recordable("Rings_Cross"),
            recordable("Rings_Corner"),
            recordable("Rings_Strips"),
            recordable("Rings_Custom"),
        ],
        OutputLevel=outputLevel,
    )
    acc += mon
    print(acc)
    acc.run(nov)


if __name__ == "__main__":
    main()
