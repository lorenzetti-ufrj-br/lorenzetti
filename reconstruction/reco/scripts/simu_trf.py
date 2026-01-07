#!/usr/bin/env python3

import multiprocessing
import argparse
import sys

from pathlib                import Path
from GaugiKernel.constants  import MINUTES
from GaugiKernel            import LoggingLevel, get_argparser_formatter
from G4Kernel               import ComponentAccumulator, EventReader
from RootStreamBuilder      import recordable
from CaloHitBuilder         import CaloHitBuilder
from RootStreamBuilder      import RootStreamHITMaker

from geometry import DetectorConstruction_v1
from reco import update_args_from_file,merge_args_from_file


def parse_args():
    parser = argparse.ArgumentParser(
        description='',
        add_help=False,
        formatter_class=get_argparser_formatter())

    parser.add_argument('-i', '--input-file', action='store',
                            dest='input_file', required=True,
                            help="The input file or folder to run the job")
    parser.add_argument('-o', '--output-file', action='store',
                        dest='output_file', required=True,
                        help="The output file.")
    parser.add_argument('--nov', '--number-of-events', action='store',
                        dest='number_of_events', required=False,
                        type=int, default=-1,
                        help="The total number of events to run.")
    parser.add_argument('-nt', '--number-of-threads', action='store',
                        dest='number_of_threads', required=False,
                        type=int, default=multiprocessing.cpu_count(),
                        help="The number of threads")
    parser.add_argument('--enable-magnetic-field', action='store_true',
                        dest='enable_magnetic_field', required=False,
                        help="Enable the magnetic field.")
    parser.add_argument('-t', '--timeout', action='store',
                        dest='timeout', required=False, type=int, default=120,
                        help="Event timeout in minutes")
    parser.add_argument('-l', '--output-level', action='store',
                        dest='output_level', required=False,
                        type=str, default='INFO',
                        help="The output level messenger.")
    parser.add_argument('--pre-init', action='store',
                        dest='pre_init', required=False, default="''",
                        help="The preinit command")
    parser.add_argument('--pre-exec', action='store',
                        dest='pre_exec', required=False, default="''",
                        help="The preexec command")
    parser.add_argument('--post-exec', action='store',
                        dest='post_exec', required=False, default="''",
                        help="The postexec command")
    parser.add_argument('--save-all-hits', action='store_true',
                        dest='save_all_hits', required=False,
                        help="Save all hits into the output file.")
    parser.add_argument('--dry-run', action='store_true',
                        dest='dry_run', required=False,
                        help="Run the script without executing the main logic.")
    return merge_args_from_file(parser)


def main(logging_level: str,
         input_file: str | Path,
         output_file: str | Path,
         pre_init: str,
         pre_exec: str,
         post_exec: str,
         enable_magnetic_field: bool,
         save_all_hits : bool,
         timeout: int,
         number_of_events: int,
         number_of_threads: int,
         dry_run: bool,
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
    parser=parse_args()
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    args = parser.parse_args()

    if Path(args.input_file).is_dir():
        raise IsADirectoryError(f"Input file '{args.input_file}' was expected to be a file, "
                                 "but it is a directory. Please provide a list of files instead.")
    
    args = update_args_from_file(args)
    print(f"input file: {args.input_file}")
    print(f"output file: {args.output_file}")
    print(f"number of threads: {args.number_of_threads}")

    main(
             logging_level         = args.output_level,
             input_file            = args.input_file,
             output_file           = args.output_file,
             pre_init              = args.pre_init,
             pre_exec              = args.pre_exec,
             post_exec             = args.post_exec,
             enable_magnetic_field = args.enable_magnetic_field,
             save_all_hits         = args.save_all_hits,
             timeout               = args.timeout,
             number_of_events      = args.number_of_events,
             number_of_threads     = args.number_of_threads,
             dry_run               = args.dry_run,
        )



