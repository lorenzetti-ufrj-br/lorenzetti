#!/usr/bin/env python3
import typer

from typing import Annotated, List
from pathlib import Path
from CaloCellBuilder    import CaloCellBuilder
from GaugiKernel        import ComponentAccumulator, LoggingLevel
from RootStreamBuilder  import RootStreamHITReader, recordable
from RootStreamBuilder  import RootStreamESDMaker
from geometry import DetectorConstruction_v1



app = typer.Typer(add_completion=False)


@app.command()
def main(
    input_file  : Annotated[Path|str      , typer.Option("-i", "--input-file", help="Path to input HIT file.")],
    output_file : Annotated[Path|str      , typer.Option("-o", "--output-file", help="Path to output ESD file.")],
    nov         : Annotated[List[int]|int , typer.Option("--nov", "--number-of-events", help="List of event indices to process.")] = None,
    output_level: Annotated[str           , typer.Option("-l", "--output-level", help="Logging verbosity level.")] = "INFO",
    pre_init    : Annotated[str           , typer.Option("--pre-init", help="Hook for pre-initialization code.")] = "''",
    pre_exec    : Annotated[str           , typer.Option("--pre-exec", help="Hook for pre-execution code.")] = "''",
    post_exec   : Annotated[str           , typer.Option("--post-exec", help="Hook for post-execution code.")] = "''",
):
    """
    Main function for the digitization process.

    Reads Hits from the input file, simulates the calorimeter readout electronics
    (CaloCellBuilder), and produces an Event Summary Data (ESD) file containing
    calorimeter cells.
    """
    if isinstance(input_file, Path):
        input_file = str(input_file)
    if isinstance(output_file, Path):
        output_file = str(output_file)

    outputLevel = LoggingLevel.toC(output_level)

    exec(pre_init)

    acc = ComponentAccumulator("ComponentAccumulator", output_file)

    # the reader must be first in sequence
    reader = RootStreamHITReader("HITReader",
                                 InputFile=input_file,
                                 OutputHitsKey=recordable("Hits"),
                                 OutputEventKey=recordable("Events"),
                                 OutputTruthKey=recordable("Particles"),
                                 OutputSeedsKey=recordable("Seeds"),
                                 OutputLevel=outputLevel,
                                 )
    reader.merge(acc)

    # digitalization!    
    calorimeter = CaloCellBuilder("CaloCellBuilder", 
                                  DetectorConstruction_v1("ATLAS"),
                                  HistogramPath="Expert/Cells",
                                  OutputLevel=outputLevel,
                                  InputHitsKey=recordable("Hits"),
                                  OutputCellsKey=recordable("Cells"),
                                  OutputTruthCellsKey=recordable("TruthCells"),
                                  InputEventKey=recordable("Events"),
    )
    calorimeter.merge(acc)

    ESD = RootStreamESDMaker("RootStreamESDMaker",
                             InputCellsKey=recordable("Cells"),
                             InputCellsTruthKey=recordable("TruthCells"),
                             InputEventKey=recordable("Events"),
                             InputTruthKey=recordable("Particles"),
                             InputSeedsKey=recordable("Seeds"),
                             OutputLevel=outputLevel)
    acc += ESD
    
    exec(pre_exec)
    acc.run(nov)
    exec(post_exec)


if __name__ == "__main__":
    app()
