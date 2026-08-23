#!/usr/bin/env python3
import typer

from pathlib import Path
from typing import List
from typing import Annotated
from GaugiKernel import LoggingLevel, ComponentAccumulator
from RootStreamBuilder import RootStreamAODReader, recordable
from RootStreamBuilder import RootStreamNtupleMaker

app = typer.Typer()

@app.command()
def main(
    nov             : Annotated[List[int]   , typer.Option("--nov", "--number-of-events", help="The total number of events to run.")] = -1,
    logging_level   : Annotated[str         , typer.Option("-l", "--log-level", help="Logging verbosity.")] = "INFO",
    input_file      : Annotated[str | Path  , typer.Option("-i", "--input-file", help="The input file or folder to run the job.")],
    output_file     : Annotated[str | Path  , typer.Option("-o", "--output-file", help="The output file.")],
):
    if isinstance(input_file, Path):
        input_file = str(input_file)
    if isinstance(output_file, Path):
        output_file = str(output_file)

    outputLevel = LoggingLevel.toC(logging_level)

    acc = ComponentAccumulator("ComponentAccumulator", output_file)

    aod = RootStreamAODReader(
        "AODReader",
        InputFile=input_file,
        OutputLevel=outputLevel,
        OutputEventKey=recordable("Events"),
        OutputTruthKey=recordable("Particles"),
        OutputClusterKey=recordable("Clusters"),
        #OutputRingerKeys=[recordable(k) for k in ring_keys],
        OutputElectronKey=recordable("Electrons"),
        OutputSeedsKey=recordable("Seeds"),
        OutputTruthClusterKey=recordable("TruthClusters"),
        #OutputTruthRingerKeys=[recordable(k) for k in truth_ring_keys],
        OutputRingerL0Key=recordable("RingsL0"),
        OutputTruthElectronKey=recordable("TruthElectrons"),
        NtupleName="CollectionTree",
    )
    aod.merge(acc)

    ntuple = RootStreamNtupleMaker(
        "NtupleMaker",
        OutputLevel=outputLevel,
        InputEventKey=recordable("Events"),
        InputTruthKey=recordable("Particles"),
        InputClusterKey=recordable("Clusters"),
        #InputRingerKeys=[recordable(k) for k in ring_keys],
        InputRingerL0Key=recordable("RingsL0"),
        InputElectronKey=recordable("Electrons"),
        InputSeedsKey=recordable("Seeds"),
        InputTruthClusterKey=recordable("TruthClusters"),
        #InputTruthRingerKeys=[recordable(k) for k in truth_ring_keys],
        InputTruthElectronKey=recordable("TruthElectrons"),
        OutputNtupleName="physics",
    )
    acc += ntuple
    acc.run(nov)


if __name__ == "__main__":
    app()
