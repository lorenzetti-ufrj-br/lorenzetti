#!/usr/bin/env python3

import argparse
import json
import sys
import os
from math        import ceil
from typing      import List
from pathlib     import Path
from joblib      import Parallel, delayed
from evtgen      import Pythia8
from filters     import Zee
from pprint      import pprint

from GenKernel   import EventTape
from GaugiKernel import get_argparser_formatter
from GaugiKernel import LoggingLevel
from GaugiKernel import GeV

from reco.gen_job import merge_args, update_args, create_parallel_job

datapath    = os.environ["LORENZETTI_EVTGEN_DATA_DIR"]
ZEE_FILE    = f'{datapath}/zee_config.cmnd'


"""
Script: gen_zee.py
Purpose: Generates Z boson decay to electron-positron pair (Zee) events using Pythia8.
Usage:
    gen_zee.py -o output.root --nov 100 [options]
"""

def parse_args():
    """
    Parses command-line arguments for the Zee event generation script.

    Returns:
        argparse.Namespace: Parsed arguments including run number, output level,
                            kinematic cuts (eta_max), and generation options.
    """

    parser = argparse.ArgumentParser(
        description='',
        formatter_class=get_argparser_formatter(),
        add_help=False)

    parser.add_argument('--run-number', action='store',
                        dest='run_number', required=False,
                        type=int, default=0,
                        help="The run number.")
    parser.add_argument('--output-level', action='store',
                        dest='output_level', required=False,
                        type=str, default="INFO",
                        help="The output level messenger.")
    parser.add_argument('--eta-max', action='store',
                        dest='eta_max', required=False,
                        type=float, default=3.2,
                        help="The eta max used in generator.")
    parser.add_argument('--force-forward-electron', action='store_true',
                        dest='force_forward_electron', required=False,
                        help="Force at least one electron "
                        "into forward region.")
    parser.add_argument('--zero-vertex-particles', action='store_true',
                        dest='zero_vertex_particles', required=False,
                        help="Fix the z vertex position in "
                        "simulation to zero for all selected particles. "
                        "It is applied only at G4 step, not in generation.")
    parser.add_argument('--zee-file', action='store',
                        dest='zee_file', required=False,
                        type=str, default=ZEE_FILE,
                        help="The pythia zee file configuration.")
   
    return merge_args(parser)


def main(events: List[int],
         logging_level: str,
         output_file: str,
         run_number: int,
         seed: int,
         zee_file: str,
         zero_vertex_particles: bool,
         force_forward_electron: bool,
         eta_max: float
        ):
    """
    Main function to execute the Zee event generation.

    Configures the EventTape and the Zee filter (wrapping Pythia8) to generate
    Z -> ee events. Supports filtering for forward electrons and zeroing
    vertex positions.

    Args:
        events (List[int]): List of event indices to generate in this job/chunk.
        logging_level (str): Logging level (e.g., 'INFO', 'DEBUG').
        output_file (str): Path to the output ROOT file.
        run_number (int): The run number identifier.
        seed (int): Random seed for Pythia8.
        zee_file (str): Path to Pythia8 configuration file.
        zero_vertex_particles (bool): If True, forces particle production vertex to (0,0,0).
        force_forward_electron (bool): If True, filters for events with at least one forward electron.
        eta_max (float): Maximum absolute pseudorapidity for electrons.
    """

    outputLevel = LoggingLevel.toC(logging_level)

    tape = EventTape("EventTape", OutputFile=output_file,
                     RunNumber=run_number)

    zee = Zee("Zee",
              Pythia8("Generator",
                      File=zee_file,
                      Seed=seed),
              EtaMax=eta_max,
              MinPt=15*GeV,
              # calibration use only.
              ZeroVertexParticles=zero_vertex_particles,
              ForceForwardElectron=force_forward_electron,
              OutputLevel=outputLevel
              )
    tape += zee

    tape.run(events)





if __name__ == "__main__":
    parser=parse_args()
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)
    args = parser.parse_args()
    args = update_args(args)
    pool = create_parallel_job(args)
    pool(main, 
        logging_level=args.output_level,
        run_number=args.run_number,
        zee_file=args.zee_file,
        zero_vertex_particles=args.zero_vertex_particles,
        force_forward_electron=args.force_forward_electron,
        eta_max=args.eta_max
    )