#!/usr/bin/env python3
import argparse
import sys
import os

from pathlib            import Path
from typing             import List
from CaloCellBuilder    import CaloCellBuilder
from GaugiKernel        import LoggingLevel, get_argparser_formatter
from GaugiKernel        import ComponentAccumulator
from RootStreamBuilder  import RootStreamHITReader, recordable
from RootStreamBuilder  import RootStreamESDMaker

from reco.reco_job import merge_args, update_args, create_parallel_job
from geometry import DetectorConstruction_v1

def parse_args():
    # create the top-level parser
    parser = argparse.ArgumentParser(
        description='',
        formatter_class=get_argparser_formatter(),
        add_help=False)

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

   
    parser = merge_args(parser)

    return parser


def main(events : List[int],
         logging_level: str,
         input_file: str | Path,
         output_file: str | Path,
         pre_init: str,
         pre_exec: str,
         post_exec: str,
        ):

    if isinstance(input_file, Path):
        input_file = str(input_file)
    if isinstance(output_file, Path):
        output_file = str(output_file)

    outputLevel = LoggingLevel.toC(logging_level)

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
                             InputEventKey=recordable("Events"),
                             InputTruthKey=recordable("Particles"),
                             InputSeedsKey=recordable("Seeds"),
                             OutputLevel=outputLevel)
    acc += ESD
    
    exec(pre_exec)
    acc.run(events)
    exec(post_exec)


    


if __name__ == "__main__":
    parser=parse_args()
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)
    args = parser.parse_args()
    args = update_args(args)
    pool  = create_parallel_job(args)
    pool( main, 
         logging_level    = args.output_level,
         pre_init         = args.pre_init,
         pre_exec         = args.pre_exec,
         post_exec        = args.post_exec,
         )
