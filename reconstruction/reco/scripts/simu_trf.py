#!/usr/bin/env python3


import typer

from typing import Annotated
from pathlib                import Path
from GaugiKernel.constants  import MINUTES
from G4Kernel               import ComponentAccumulator, EventReader, LoggingLevel
from RootStreamBuilder      import recordable
from CaloHitBuilder         import CaloHitBuilder
from RootStreamBuilder      import RootStreamHITMaker
from geometry import DetectorConstruction_v1


app = typer.Typer(add_completion=False)

@app.command()
def main(
         logging_level          : Annotated[str,           typer.Option("-l", "--output-level", help="The output level messenger.")],
         input_file             : Annotated[str | Path,    typer.Option("-i", "--input-file", help="The input file or folder to run the job.")],
         output_file            : Annotated[str | Path,    typer.Option("-o", "--output-file", help="The output file.")],
         pre_init               : Annotated[str,           typer.Option("--pre-init", help="The preinit command")],
         pre_exec               : Annotated[str,           typer.Option("--pre-exec", help="The preexec command")],
         post_exec              : Annotated[str,           typer.Option("--post-exec", help="The postexec command")],
         enable_magnetic_field  : Annotated[bool,          typer.Option("--enable-magnetic-field", help="Enable the magnetic field.")],
         save_all_hits          : Annotated[bool,          typer.Option("--save-all-hits", help="Save all hits into the output file.")],
         timeout                : Annotated[int,           typer.Option("--timeout", help="Timeout in minutes.")],
         number_of_events       : Annotated[int,           typer.Option("--nov", "--number-of-events", help="The total number of events to run.")],
         number_of_threads      : Annotated[int,           typer.Option("-nt", "--number-of-threads", help="The number of threads.")],
         dry_run                : Annotated[bool,          typer.Option("--dry-run", help="Perform a dry run without executing jobs.")],
         
         ):

    if isinstance(input_file, Path):
        input_file = str(input_file)
    if isinstance(output_file, Path):
        output_file = str(output_file)

    
    outputLevel = LoggingLevel.toC(logging_level)
    exec(pre_init)

    acc = ComponentAccumulator("ComponentAccumulator", 
                               DetectorConstruction_v1( "ATLAS", UseMagneticField=enable_magnetic_field),
                               NumberOfThreads=number_of_threads,
                               OutputFile=output_file,
                               Timeout=timeout * MINUTES)

    gun = EventReader("EventReader", input_file,
                      # outputs
                      OutputEventKey=recordable("Events"),
                      OutputTruthKey=recordable("Particles"),
                      OutputSeedKey=recordable("Seeds"),
                      )
    calorimeter = CaloHitBuilder("CaloHitBuilder",
                                 HistogramPath="Expert/Hits",
                                 OutputLevel=outputLevel,
                                 OutputHitsKey=recordable("Hits")
                                 )
    
    gun.merge(acc)
    calorimeter.merge(acc)
    HIT = RootStreamHITMaker("RootStreamHITMaker",
                             OutputLevel=outputLevel,
                             OnlyRoI= not save_all_hits,
                             InputHitsKey=recordable("Hits"),
                             InputEventKey=recordable("Events"),
                             InputTruthKey=recordable("Particles"),
                             InputSeedsKey=recordable("Seeds"),
                             )
    acc += HIT
    
    exec(pre_exec)
    if not dry_run:
        acc.run(number_of_events)
        exec(post_exec)



if __name__ == "__main__":
    app()