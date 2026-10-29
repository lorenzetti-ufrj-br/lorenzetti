#!/usr/bin/env python3

from pathlib import Path
from typing_extensions import Annotated
import typer

from GaugiKernel import file_parallel_job, ComponentAccumulator, LoggingLevel
from RootStreamBuilder import RootStreamAODReader, recordable, RootStreamParquetMaker


@file_parallel_job(ntuple_name="", output_replace=(".AOD.root", ".parquet"))
def main(
    input_file: Annotated[str | Path, typer.Option("-i", "--input-file", help="The input file or folder to run the job.")],
    output_file: Annotated[str | Path, typer.Option("-o", "--output-file", help="The output file or folder.")],
    number_of_threads: Annotated[int, typer.Option("-nt", "--number-of-threads", help="Threads allocated per worker")] = 1,
    nov: Annotated[int, typer.Option("--nov", "--number-of-events", help="The total number of events to run.")] = -1,
    output_level: Annotated[str, typer.Option("-l", "--output-level", help="Logging verbosity.")] = "INFO",
    preexec: Annotated[str, typer.Option("-p", "--preexec", help="The preexec command to run before execution.")] = "''",
    schema_file: Annotated[str, typer.Option("-s", "--schema", help="Path to JSON file with branch schema dictionary.")] = "",
):
    """
    Creates an analysis flat Parquet file from AOD input files.
    """
    input_file = str(input_file)
    output_file = str(output_file)
    outputLevel = LoggingLevel.toC(output_level)

    exec(preexec)

    schema_dict = {}
    if schema_file:
        import json
        with open(schema_file, "r") as f:
            schema_dict = json.load(f)

    AOD = RootStreamAODReader(
        "AODReader",
        InputFile=input_file,
        TreeName="CollectionTree",
        OutputLevel=outputLevel,
    )

    acc = ComponentAccumulator("ComponentAccumulator", output_file, AOD)

    parquet = RootStreamParquetMaker(
        "ParquetMaker",
        OutputFile=output_file,
        OutputLevel=outputLevel,
        InputEventKey=recordable("Events"),
        InputTruthKey=recordable("Particles"),
        InputSeedsKey=recordable("Seeds"),
        InputClusterKey=recordable("Clusters"),
        InputElectronKey=recordable("Electrons"),
        InputRingerKeys=[recordable("Rings")],
        Schema=schema_dict,
    )
    acc += parquet
    print(acc)
    acc.run(nov)


if __name__ == "__main__":
    main()
