#!/usr/bin/env python3
from __future__ import annotations
"""
Script: simu_trf.py
Purpose: Simulates detector showers from generated events using Geant4.
Usage:
    simu_trf.py -i input.EVT.root -o output.HIT.root [options]
"""

import os
from pathlib import Path
from typing import Union
from typing_extensions import Annotated
import typer

from GaugiKernel import file_parallel_job, LoggingLevel
from GaugiKernel.constants import MINUTES
from G4Kernel import EventReader, ComponentAccumulator
from RootStreamBuilder import recordable, clear_recorded_items, RootStreamHITMaker
from CaloHitBuilder import CaloHitBuilder, CaloHitFlags, FreeRunningFlags
from geometry.v1 import DetectorConstruction_v1
from geometry.v2 import DetectorConstruction_v2, AtlasGeometryFlags
from magfield import MagFieldFlags


def keep_only_collection_tree(path: Union[str, Path]) -> None:
    """
    Keeps only the CollectionTree in the output file of free-running ATLAS format,
    removing the monitoring directories (Event/, Expert/) as in the ATLAS HITS ntuple.
    The tree is cloned with identical compression settings.
    """
    import ROOT

    path_str = str(path)
    src = ROOT.TFile.Open(path_str)
    if not src or src.IsZombie():
        return
    tree = src.Get("CollectionTree")
    if not tree:
        src.Close()
        return
    tmp = path_str + ".tmp"
    dst = ROOT.TFile(tmp, "RECREATE", "", src.GetCompressionSettings())
    tree.CloneTree(-1, "fast").Write()
    dst.Close()
    src.Close()
    os.replace(tmp, path_str)


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

    # 3. Resolve defaults para cada domínio
    AtlasGeometryFlags.apply_defaults(is_v2=is_v2)
    CaloHitFlags.apply_defaults(is_v2=is_v2)
    FreeRunningFlags.apply_defaults(is_v2=is_v2)
    MagFieldFlags.apply_defaults(is_v2=is_v2)

    # 4. Validações de consistência para free-running hits
    if FreeRunningFlags.Enable:
        if not (AtlasGeometryFlags.TileAtlasGeometry and AtlasGeometryFlags.TileAtlasCells):
            raise typer.BadParameter("free-running hits require TileAtlasGeometry and TileAtlasCells in AtlasGeometryFlags")
        if not (AtlasGeometryFlags.AtlasEmbCells and AtlasGeometryFlags.AtlasHec and AtlasGeometryFlags.AtlasEmec):
            raise typer.BadParameter("free-running hits require AtlasEmbCells, AtlasHec, and AtlasEmec in AtlasGeometryFlags")
        if not AtlasGeometryFlags.TileAtlasGap:
            raise typer.BadParameter("free-running hits require TileAtlasGap in AtlasGeometryFlags")
        if not AtlasGeometryFlags.AtlasFcalCells:
            raise typer.BadParameter("free-running hits require AtlasFcalCells in AtlasGeometryFlags")
        if not AtlasGeometryFlags.AtlasFcalFrozenShowers:
            raise typer.BadParameter("free-running hits require AtlasFcalFrozenShowers in AtlasGeometryFlags")
        if not AtlasGeometryFlags.AtlasG4:
            raise typer.BadParameter("free-running hits require AtlasG4 in AtlasGeometryFlags")
        if not AtlasGeometryFlags.AtlasRun4:
            raise typer.BadParameter("free-running hits require AtlasRun4 in AtlasGeometryFlags")

        if FreeRunningFlags.AtlasFormat:
            if not AtlasGeometryFlags.AtlasEmecArgonFraction:
                raise typer.BadParameter("FreeRunningFlags.AtlasFormat requires AtlasGeometryFlags.AtlasEmecArgonFraction")
            if not AtlasGeometryFlags.TileAtlasRun4:
                raise typer.BadParameter("FreeRunningFlags.AtlasFormat requires AtlasGeometryFlags.TileAtlasRun4")
            if not AtlasGeometryFlags.AtlasBarrelGapServices:
                raise typer.BadParameter("FreeRunningFlags.AtlasFormat requires AtlasGeometryFlags.AtlasBarrelGapServices")
            if not AtlasGeometryFlags.AtlasFullField:
                raise typer.BadParameter("FreeRunningFlags.AtlasFormat requires AtlasGeometryFlags.AtlasFullField")
            if not AtlasGeometryFlags.AtlasForwardShielding:
                raise typer.BadParameter("FreeRunningFlags.AtlasFormat requires AtlasGeometryFlags.AtlasForwardShielding")
            if not FreeRunningFlags.EmecChargeCollection:
                raise typer.BadParameter("FreeRunningFlags.AtlasFormat requires FreeRunningFlags.EmecChargeCollection")

        if FreeRunningFlags.EmecChargeCollection:
            for f in (FreeRunningFlags.EmecTables, FreeRunningFlags.EmecFieldMap, FreeRunningFlags.EmecHVMap):
                if not os.path.isfile(f):
                    raise typer.BadParameter(f"EMEC charge collection file '{f}' not found")

        CaloHitFlags.ActiveEnergyOnly = True
        CaloHitFlags.BirksLaw = True
        CaloHitFlags.TileDualReadout = True
        CaloHitFlags.TilePmtSplit = "ushape"
        CaloHitFlags.NeutronTimeCut = 150.0

    # 5. Instancia a geometria correspondente
    if is_v2:
        geo_dict = AtlasGeometryFlags.to_dict()
        geo_dict["UseMagneticField"] = MagFieldFlags.EnableField
        geo_dict["UseSolenoidField"] = MagFieldFlags.EnableSolenoidOnly
        det = DetectorConstruction_v2("ATLAS", **geo_dict)
    else:
        det = DetectorConstruction_v1("ATLAS", UseMagneticField=MagFieldFlags.EnableField)

    gun = EventReader(
        "EventReader",
        input_file,
        OutputEventKey=recordable("Events"),
        OutputTruthKey=recordable("Particles"),
        OutputSeedKey=recordable("Seeds"),
    )

    fast_sim = (AtlasGeometryFlags.AtlasFcalFrozenShowers or AtlasGeometryFlags.AtlasRun4) if is_v2 else False

    acc = ComponentAccumulator(
        "ComponentAccumulator",
        det,
        gun,
        NumberOfThreads=number_of_threads,
        OutputFile=output_file,
        Timeout=timeout * MINUTES,
        NeutronTimeCut=CaloHitFlags.NeutronTimeCut or 0.0,
        FastSimulation=fast_sim,
        AtlasG4=AtlasGeometryFlags.AtlasG4 if is_v2 else False,
    )

    tile_dual_readout_val = 0
    if CaloHitFlags.TileDualReadout:
        tile_dual_readout_val = 1 if CaloHitFlags.TilePmtSplit == "ushape" else 2

    calorimeter = CaloHitBuilder(
        "CaloHitBuilder",
        HistogramPath="Expert/Hits",
        OutputLevel=outputLevel,
        OutputHitsKey=recordable("Hits"),
        OnlyRoI=not CaloHitFlags.SaveAllHits,
        ActiveEnergyOnly=CaloHitFlags.ActiveEnergyOnly,
        BirksLaw=CaloHitFlags.BirksLaw,
        AtlasHitTime=CaloHitFlags.AtlasHitTime,
        TileDualReadout=tile_dual_readout_val,
        FreeRunningHits=FreeRunningFlags.Enable,
        FreeRunningBinning=not FreeRunningFlags.NoBinning,
        FreeRunningNtupleName=("FreeRunningTree" if FreeRunningFlags.KeepHits else "CollectionTree"),
        FreeRunningAtlasFormat=FreeRunningFlags.AtlasFormat,
        EmecChargeCollection=FreeRunningFlags.EmecChargeCollection,
        EmecChargeTables=FreeRunningFlags.EmecTables,
        EmecChargeFieldMap=FreeRunningFlags.EmecFieldMap,
        EmecChargeHVMap=FreeRunningFlags.EmecHVMap,
        InputEventKey=recordable("Events"),
    )
    calorimeter.merge(acc)

    if not (FreeRunningFlags.Enable and not FreeRunningFlags.KeepHits):
        HIT = RootStreamHITMaker(
            "RootStreamHITMaker",
            OutputLevel=outputLevel,
            OnlyRoI=not CaloHitFlags.SaveAllHits,
            InputHitsKey=recordable("Hits"),
            InputEventKey=recordable("Events"),
            InputTruthKey=recordable("Particles"),
            InputSeedsKey=recordable("Seeds"),
        )
        acc += HIT

    exec(pre_exec)
    acc.run(number_of_events)
    exec(post_exec)

    if FreeRunningFlags.AtlasFormat:
        keep_only_collection_tree(output_file)


if __name__ == "__main__":
    main()
