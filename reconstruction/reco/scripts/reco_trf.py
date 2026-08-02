#!/usr/bin/env python3
import argparse
import sys
import os

from pathlib import Path
from typing import List
from expand_folders import expand_folders
from GaugiKernel import LoggingLevel, get_argparser_formatter
from GaugiKernel import ComponentAccumulator
from RootStreamBuilder import RootStreamESDReader, recordable
from CaloClusterBuilder import CaloClusterMaker
from CaloRingsBuilder import CaloRingsBuilderCfg
from EgammaBuilder import ElectronBuilderCfg
from RootStreamBuilder import RootStreamAODMaker
from RootStreamBuilder.RootStreamFlags import RootStreamAODFlags as flags

from reco.reco_job import merge_args, update_args, create_parallel_job

"""
Script: reco_trf.py
Purpose: Executes the offline reconstruction chain.
         Reads digitized cells (ESD), builds calorimeter clusters, computes
         ring variables (Rings), and reconstructs electron candidates.
Usage:
    reco_trf.py -i input.ESD.root -o output.AOD.root
"""
TOPOLOGY_MAP = {
    "doStdRings": ("std", "Rings"),
    "doCornerRings": ("corner", "CornerRings"),
    "doAsymRings": ("asym", "AsymRings"),
    "doStripsRings": ("strips", "StripsRings"),
    "doCrossRings": ("cross", "CrossRings"),
    "doCustomRings": ("custom", "CustomRings"),
}


def parse_args():
    """
    Parses command-line arguments for the reconstruction job.

    Returns:
        argparse.Namespace: Arguments for reconstruction configuration.
    """
    # create the top-level parser
    parser = argparse.ArgumentParser(
        description="", formatter_class=get_argparser_formatter(), add_help=False
    )

    parser.add_argument(
        "-l",
        "--output-level",
        action="store",
        dest="output_level",
        required=False,
        type=str,
        default="INFO",
        help="The output level messenger.",
    )
    parser.add_argument(
        "-c",
        "--command",
        action="store",
        dest="command",
        required=False,
        default="''",
        help="The preexec command",
    )

    return merge_args(parser)


def main(
    events: List[int],
    logging_level: str,
    input_file: str | Path,
    output_file: str | Path,
    command: str,
):
    """
    Main function for the reconstruction workflow.

    Orchestrates the reconstruction sequence:
    1. Reads ESD file (Cells, Particles, Seeds).
    2. Runs CaloClusterMaker to group cells into clusters.
    3. Runs CaloRingsBuilder to extract concentric ring energy sums.
    4. Runs ElectronBuilder to create electron candidates.
    5. Writes the results to an Analysis Object Data (AOD) file.

    Args:
        events (List[int]): List of event indices.
        logging_level (str): Logging verbosity.
        input_file (str | Path): Path to input ESD file.
        output_file (str | Path): Path to output AOD file.
        command (str): Optional command to execute before the sequence.
    """
    if isinstance(input_file, Path):
        input_file = str(input_file)
    if isinstance(output_file, Path):
        output_file = str(object=output_file)

    outputLevel = LoggingLevel.toC(logging_level)

    exec(command)

    acc = ComponentAccumulator("ComponentAccumulator", output_file)

    ESD = RootStreamESDReader(
        "ESDReader",
        InputFile=input_file,
        OutputCellsKey=recordable("Cells"),
        OutputCellsTruthKey=recordable("TruthCells"),
        OutputEventKey=recordable("Events"),
        OutputTruthKey=recordable("Particles"),
        OutputSeedsKey=recordable("Seeds"),
        OutputLevel=outputLevel,
    )
    ESD.merge(acc)

    cluster = CaloClusterMaker(
        "CaloClusterMaker",
        InputCellsKey=recordable("Cells"),
        InputSeedsKey=recordable("Seeds"),
        # output as
        OutputClusterKey=recordable("Clusters"),
        # other configs
        HistogramPath="Expert/Clusters",
        OutputLevel=outputLevel,
    )

    cluster_truth = CaloClusterMaker(
        "CaloClusterMaker_Truth",
        InputCellsKey=recordable("TruthCells"),
        InputSeedsKey=recordable("Seeds"),
        # output as
        OutputClusterKey=recordable("TruthClusters"),
        # other configs
        HistogramPath="Expert/TruthClusters",
        OutputLevel=outputLevel,
    )
    ringsL0 = CaloRingsBuilderCfg(
        "CaloRingsBuilderL0",
        InputClusterKey=recordable("Clusters"),
        OutputRingerKey=recordable("RingsL0"),
        HistogramPath="Expert/RingsL0",
        OutputLevel=outputLevel,
        DoSigmaCut=True,
        SigmaCut=flags.SigmaCut,
    )

    hypo = ElectronBuilderCfg(
        "ElectronBuilder",
        InputClusterKey=recordable("Clusters"),
        OutputElectronKey=recordable("Electrons"),
        OutputLevel=outputLevel,
    )

    hypo_truth = ElectronBuilderCfg(
        "ElectronBuilder_Truth",
        InputClusterKey=recordable("TruthClusters"),
        OutputElectronKey=recordable("TruthElectrons"),
        OutputLevel=outputLevel,
    )

    ring_keys = []
    truth_ring_keys = []
    acc_rings = []
    acc_rings_truth = []

    for flag_name, (topology, key_suffix) in TOPOLOGY_MAP.items():
        if not getattr(flags, flag_name):
            continue

        extra = {}
        if topology == "corner":
            extra["CornerShift"] = flags.CornerShift
        elif topology == "cross":
            extra["CrossShift"] = flags.CrossShift
        elif topology == "custom":
            extra["RingsShiftEta"] = flags.CustomRingsShiftEta
            extra["RingsShiftPhi"] = flags.CustomRingsShiftPhi
        elif topology == "strips":
            extra["Axis"] = flags.StripsAxis

        acc_rings.append(
            CaloRingsBuilderCfg(
                f"CaloRingsBuilder_{topology}",
                InputClusterKey=recordable("Clusters"),
                OutputRingerKey=recordable(key_suffix),
                HistogramPath=f"Expert/{key_suffix}",
                OutputLevel=outputLevel,
                RingerTopology=topology,
                **extra,
            )
        )

        acc_rings_truth.append(
            CaloRingsBuilderCfg(
                f"CaloRingsBuilder_Truth_{topology}",
                InputClusterKey=recordable("TruthClusters"),
                OutputRingerKey=recordable(f"Truth{key_suffix}"),
                HistogramPath=f"Expert/Truth{key_suffix}",
                OutputLevel=outputLevel,
                RingerTopology=topology,
                **extra,
            )
        )

        ring_keys.append(recordable(key_suffix))
        truth_ring_keys.append(recordable(f"Truth{key_suffix}"))

    AOD = RootStreamAODMaker(
        "RootStreamAODMaker",
        InputEventKey=recordable("Events"),
        InputSeedsKey=recordable("Seeds"),
        InputTruthKey=recordable("Particles"),
        InputCellsKey=recordable("Cells"),
        InputTruthCellsKey=recordable("TruthCells"),
        InputClusterKey=recordable("Clusters"),
        InputTruthClusterKey=recordable("TruthClusters"),
        InputRingerKeys=ring_keys,
        InputTruthRingerKeys=truth_ring_keys,
        InputElectronKey=recordable("Electrons"),
        InputTruthElectronKey=recordable("TruthElectrons"),
        InputRingerL0Key=recordable("RingsL0"),
        OutputLevel=outputLevel,
    )

    # sequence
    acc += cluster
    for rings in acc_rings:
        acc += rings
    acc += ringsL0
    acc += hypo
    acc += cluster_truth
    for rings_truth in acc_rings_truth:
        acc += rings_truth
    acc += hypo_truth
    acc += AOD

    acc.run(events)


if __name__ == "__main__":
    parser = parse_args()
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)
    args = parser.parse_args()
    args = update_args(args)
    pool = create_parallel_job(args)
    pool(
        main,
        logging_level=args.output_level,
        command=args.command,
    )
