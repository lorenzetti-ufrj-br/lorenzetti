#!/usr/bin/env python3
from __future__ import annotations
"""
Script: simu_trf.py
Purpose: Simulates detector showers from generated events using Geant4.
Usage:
    simu_trf.py -i input.EVT.root -o output.HIT.root [options]
"""

from pathlib import Path
from typing_extensions import Annotated
import typer

from GaugiKernel import file_parallel_job, LoggingLevel
from GaugiKernel.constants import MINUTES
from G4Kernel import EventReader, ComponentAccumulator
from RootStreamBuilder import recordable, clear_recorded_items, RootStreamHITMaker
from CaloHitBuilder import CaloHitBuilder, CaloHitFlags, FreeRunningFlags
from GeoBase import DetectorConstructionCfg
from GeoV2 import AtlasGeometryFlags
from magfield import MagFieldFlags


@file_parallel_job(ntuple_name="CollectionTree", output_replace=(".EVT.", ".HIT."))
def main(
    input_file: Annotated[str | Path, typer.Option("-i", "--input-file", help="Input EVT file or directory")],
    output_file: Annotated[str | Path, typer.Option("-o", "--output-file", help="Destination HIT file or directory")],
    number_of_threads: Annotated[int, typer.Option("-nt", "--number-of-threads", help="Threads allocated per worker")] = 1,
    number_of_events: Annotated[int, typer.Option("--nov", "--number-of-events", help="The total number of events to run.")] = -1,
    output_level: Annotated[str, typer.Option("-l", "--output-level", help="The output level messenger.")] = "INFO",
    detector: Annotated[str, typer.Option("--detector", help="Detector version ('v1' or 'v2').")] = "v1",
    enable_magnetic_field: Annotated[bool, typer.Option("--enable-magnetic-field", help="Enable the magnetic field.")] = False,
    free_running_hits: Annotated[bool, typer.Option("--free-running-hits", help="Write hits in ATLAS HITS ntuple layout.")] = False,
    save_all_hits: Annotated[bool, typer.Option("--save-all-hits", help="Save all hits into the output file.")] = False,
    timeout: Annotated[int, typer.Option("--timeout", help="Timeout in minutes.")] = 10,
    pre_init: Annotated[str, typer.Option("--pre-init", help="The preinit command")] = "''",
    pre_exec: Annotated[str, typer.Option("--pre-exec", help="The preexec command")] = "''",
    post_exec: Annotated[str, typer.Option("--post-exec", help="The postexec command")] = "''",
):
    clear_recorded_items()

    input_file = str(input_file)
    output_file = str(output_file)
    outputLevel = LoggingLevel.toC(output_level)

    # 1. Aplica flags de atalho passadas via CLI
    if enable_magnetic_field:
        MagFieldFlags.EnableField = True
    if free_running_hits:
        FreeRunningFlags.Enable = True
    if save_all_hits:
        CaloHitFlags.SaveAllHits = True

    # 2. Executa pre_init (customizações do usuário via Python)
    exec(pre_init)

    is_v2 = (detector == "v2")

    # 3. Resolve defaults e validações dos domínios
    CaloHitFlags.apply_defaults(is_v2=is_v2)
    FreeRunningFlags.apply_defaults(is_v2=is_v2)
    if is_v2:
        from AtlasCaloHitBuilderTools import validate_atlas_hit_flags
        try:
            validate_atlas_hit_flags(flags=CaloHitFlags, fr_flags=FreeRunningFlags, geo_flags=AtlasGeometryFlags)
        except ValueError as e:
            raise typer.BadParameter(str(e))

    # 4. Instancia a geometria via Factory Cfg
    det = DetectorConstructionCfg("ATLAS", version=detector)

    gun = EventReader(
        "EventReader",
        input_file,
        OutputEventKey=recordable("Events"),
        OutputTruthKey=recordable("Particles"),
        OutputSeedKey=recordable("Seeds"),
    )

    acc = ComponentAccumulator(
        "ComponentAccumulator",
        det,
        gun,
        NumberOfThreads=number_of_threads,
        OutputFile=output_file,
        Timeout=timeout * MINUTES,
        NeutronTimeCut=CaloHitFlags.NeutronTimeCut or 0.0,
        FastSimulation=(AtlasGeometryFlags.AtlasFcalFrozenShowers or AtlasGeometryFlags.AtlasRun4) if is_v2 else False,
        AtlasG4=AtlasGeometryFlags.AtlasG4 if is_v2 else False,
    )

    calorimeter = CaloHitBuilder(
        "CaloHitBuilder",
        HistogramPath="Expert/Hits",
        OutputLevel=outputLevel,
        OutputHitsKey=recordable("Hits"),
        OnlyRoI=not CaloHitFlags.SaveAllHits,
        flags=CaloHitFlags,
        fr_flags=FreeRunningFlags,
        FreeRunningNtupleName=("FreeRunningTree" if FreeRunningFlags.KeepHits else "CollectionTree"),
        InputEventKey=recordable("Events"),
    )
    calorimeter.merge(acc)

    if not (FreeRunningFlags.Enable and not FreeRunningFlags.KeepHits):
        HIT = RootStreamHITMaker(
            "RootStreamHITMaker",
            OutputLevel=outputLevel,
        )
        acc += HIT

    exec(pre_exec)
    acc.run(number_of_events)
    exec(post_exec)

    if FreeRunningFlags.AtlasFormat:
        from AtlasCaloHitBuilderTools import keep_only_collection_tree
        keep_only_collection_tree(output_file)


if __name__ == "__main__":
    main()
