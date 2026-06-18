#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path
from typing import List

import ROOT as _ROOT
from expand_folders import expand_folders
from GaugiKernel import LoggingLevel, get_argparser_formatter, ComponentAccumulator
from RootStreamBuilder import RootStreamAODReader, recordable
from RootStreamBuilder import RootStreamNtupleMaker
from reco.reco_job import merge_args, update_args, create_parallel_job


def _detect_ring_keys(input_file: str) -> tuple[list, list]:
    """Scan AOD CollectionTree to find every CaloRingsContainer_* branch."""
    f = _ROOT.TFile.Open(input_file)
    if not f or f.IsZombie():
        return ["Rings"], ["TruthRings"]
    tree = f.Get("CollectionTree")
    if not tree:
        f.Close()
        return ["Rings"], ["TruthRings"]

    ring_keys, truth_ring_keys = [], []
    for branch in tree.GetListOfBranches():
        name = branch.GetName()
        if not name.startswith("CaloRingsContainer_"):
            continue
        key = name[len("CaloRingsContainer_") :]
        if key == "RingsL0":
            continue
        if key.startswith("Truth"):
            truth_ring_keys.append(key)
        else:
            ring_keys.append(key)

    f.Close()
    return ring_keys or ["Rings"], truth_ring_keys or ["TruthRings"]


def parse_args():
    parser = argparse.ArgumentParser(
        description="", formatter_class=get_argparser_formatter(), add_help=False
    )
    parser.add_argument(
        "-l",
        "--output-level",
        dest="output_level",
        default="INFO",
        help="Logging verbosity.",
    )
    return merge_args(parser)


def main(
    events: List[int],
    logging_level: str,
    input_file: str | Path,
    output_file: str | Path,
):
    if isinstance(input_file, Path):
        input_file = str(input_file)
    if isinstance(output_file, Path):
        output_file = str(output_file)

    outputLevel = LoggingLevel.toC(logging_level)

    ring_keys, truth_ring_keys = _detect_ring_keys(input_file)

    acc = ComponentAccumulator("ComponentAccumulator", output_file)

    aod = RootStreamAODReader(
        "AODReader",
        InputFile=input_file,
        OutputLevel=outputLevel,
        OutputEventKey=recordable("Events"),
        OutputTruthKey=recordable("Particles"),
        OutputClusterKey=recordable("Clusters"),
        OutputRingerKeys=[recordable(k) for k in ring_keys],
        OutputElectronKey=recordable("Electrons"),
        OutputSeedsKey=recordable("Seeds"),
        OutputTruthClusterKey=recordable("TruthClusters"),
        OutputTruthRingerKeys=[recordable(k) for k in truth_ring_keys],
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
        InputRingerKeys=[recordable(k) for k in ring_keys],
        InputRingerL0Key=recordable("RingsL0"),
        InputElectronKey=recordable("Electrons"),
        InputSeedsKey=recordable("Seeds"),
        InputTruthClusterKey=recordable("TruthClusters"),
        InputTruthRingerKeys=[recordable(k) for k in truth_ring_keys],
        InputTruthElectronKey=recordable("TruthElectrons"),
        OutputNtupleName="physics",
    )
    acc += ntuple
    acc.run(events)


if __name__ == "__main__":
    parser = parse_args()
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)
    args = parse_args().parse_args()
    args = update_args(args)
    pool = create_parallel_job(args)
    pool(
        main,
        logging_level=args.output_level,
    )
