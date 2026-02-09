#!/usr/bin/env python3
import argparse
import sys
import os

from pathlib            import Path
from typing             import List
from expand_folders     import expand_folders
from GaugiKernel        import LoggingLevel, get_argparser_formatter
from GaugiKernel        import ComponentAccumulator
from RootStreamBuilder  import RootStreamAODReader, recordable
from GaugiKernel        import ComponentAccumulator
from RootStreamBuilder  import RootStreamNtupleMaker 

from reco.reco_job import merge_args, update_args, create_parallel_job

from reco.reco_job import merge_args, update_args, create_parallel_job

"""
Script: ntuple_trf.py
Purpose: Dumps reconstructed objects into a flat Ntuple (TTree) for analysis.
         Converts the hierarchical AOD format into a simpler tabular format suitable
         for ROOT macros or Python analysis (e.g., pandas/uproot).
Usage:
    ntuple_trf.py -i input.AOD.root -o output.NTUPLE.root
"""

def parse_args():
    """
    Parses command-line arguments for the ntuple dumping job.

    Returns:
        argparse.Namespace: Arguments for input/output files and logging.
    """
    # create the top-level parser
    parser = argparse.ArgumentParser(
        description='',
        formatter_class=get_argparser_formatter(),
        add_help=False)

    parser.add_argument('-l', '--output-level', action='store',
                        dest='output_level', required=False,
                        type=str, default='INFO',
                        help="The output level messenger.")
   
    return merge_args(parser)


def main(events : List[int],
         logging_level: str,
         input_file: str | Path,
         output_file: str | Path,
        ):
    """
    Main function for Ntuple generation.

    Reads the Analysis Object Data (AOD) containing reconstructed electrons,
    clusters, and rings, and creates a "physics" TTree in the output file
    where each entry corresponds to a reconstructed object or event.

    Args:
        events (List[int]): List of event indices to process.
        logging_level (str): Logging verbosity.
        input_file (str | Path): Path to input AOD file.
        output_file (str | Path): Path to output Ntuple file.
    """

    if isinstance(input_file, Path):
        input_file = str(input_file)
    if isinstance(output_file, Path):
        output_file = str(output_file)

    outputLevel = LoggingLevel.toC(logging_level)

  
    acc = ComponentAccumulator("ComponentAccumulator", output_file)


  
    aod = RootStreamAODReader("AODReader", 
                              InputFile            = input_file,
                              OutputLevel          = outputLevel,
                              OutputEventKey       = recordable("Events"),
                              OutputTruthKey       = recordable("Particles"),
                              OutputClusterKey     = recordable("Clusters"),
                              OutputRingerKey      = recordable("Rings"),
                              OutputElectronKey    = recordable("Electrons"),
                              OutputSeedsKey       = recordable("Seeds"),
                              NtupleName           = "CollectionTree",
                              )

    aod.merge(acc)

    ntuple = RootStreamNtupleMaker("NtupleMaker",
                                  OutputLevel          = outputLevel,
                                  InputEventKey        = recordable("Events"),
                                  InputTruthKey        = recordable("Particles"),
                                  InputClusterKey      = recordable("Clusters"),
                                  InputRingerKey       = recordable("Rings"),
                                  InputElectronKey     = recordable("Electrons"),
                                  InputSeedsKey        = recordable("Seeds"),
                                  OutputNtupleName     = "physics",
                                  )

    acc+=ntuple

    acc.run(events)


       



if __name__ == "__main__":
    parser=parse_args()
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)
    args = parser.parse_args()
    args = update_args(args)
    pool = create_parallel_job(args)
    pool( main, 
         logging_level    = args.output_level,
         )
