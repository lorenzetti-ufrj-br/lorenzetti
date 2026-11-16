#!/usr/bin/env python3
"""
Script: simu_trf.py
Purpose: Simulates detector showers from generated events using Geant4.
Usage:
    simu_trf.py -i input.EVT.root -o output.HIT.root [options]
"""

import os
from pathlib import Path
from typing import Optional
from typing_extensions import Annotated
import typer

from GaugiKernel import file_parallel_job, LoggingLevel
from GaugiKernel.constants import MINUTES
from G4Kernel import EventReader, ComponentAccumulator
from RootStreamBuilder import recordable, clear_recorded_items, RootStreamHITMaker
from CaloHitBuilder import CaloHitBuilder
from geometry import DetectorConstruction_v1, DetectorConstruction_v2


@file_parallel_job(ntuple_name="CollectionTree", output_replace=(".EVT.", ".HIT."))
def main(
    input_file: Annotated[str | Path, typer.Option("-i", "--input-file", help="Input EVT file or directory")],
    output_file: Annotated[str | Path, typer.Option("-o", "--output-file", help="Destination HIT file or directory")],
    number_of_threads: Annotated[int, typer.Option("-nt", "--number-of-threads", help="Threads allocated per worker")] = 1,
    output_level: Annotated[str, typer.Option("-l", "--output-level", help="The output level messenger.")] = "INFO",
    pre_init: Annotated[str, typer.Option("--pre-init", help="The preinit command")] = "''",
    pre_exec: Annotated[str, typer.Option("--pre-exec", help="The preexec command")] = "''",
    post_exec: Annotated[str, typer.Option("--post-exec", help="The postexec command")] = "''",
    enable_magnetic_field: Annotated[bool, typer.Option("--enable-magnetic-field", help="Enable the magnetic field.")] = False,
    enable_solenoid_field: Annotated[bool, typer.Option("--enable-solenoid-field", help="Enable solenoid field.")] = False,
    save_all_hits: Annotated[bool, typer.Option("--save-all-hits", help="Save all hits into the output file.")] = False,
    timeout: Annotated[int, typer.Option("--timeout", help="Timeout in minutes.")] = 10,
    number_of_events: Annotated[int, typer.Option("--nov", "--number-of-events", help="The total number of events to run.")] = -1,
    detector: Annotated[str, typer.Option("--detector", help="Detector version ('v1' or 'v2').")] = "v1",
    tile_atlas_geometry: Annotated[Optional[bool], typer.Option("--tile-atlas-geometry/--no-tile-atlas-geometry", help="Use ATLAS tile geometry.")] = None,
    tile_atlas_cells: Annotated[Optional[bool], typer.Option("--tile-atlas-cells/--no-tile-atlas-cells", help="Use ATLAS tile cells.")] = None,
    atlas_material_in_front: Annotated[Optional[bool], typer.Option("--atlas-material-in-front/--no-atlas-material-in-front", help="Material in front of barrel EM.")] = None,
    tile_atlas_itc: Annotated[Optional[bool], typer.Option("--tile-atlas-itc/--no-tile-atlas-itc", help="ATLAS ITC gap.")] = None,
    atlas_emb: Annotated[Optional[bool], typer.Option("--atlas-emb/--no-atlas-emb", help="Barrel EM with ATLAS composition.")] = None,
    atlas_emb_cells: Annotated[Optional[bool], typer.Option("--atlas-emb-cells/--no-atlas-emb-cells", help="Barrel EM with ATLAS cells.")] = None,
    atlas_hec: Annotated[Optional[bool], typer.Option("--atlas-hec/--no-atlas-hec", help="HEC as in ATLAS.")] = None,
    atlas_emec: Annotated[Optional[bool], typer.Option("--atlas-emec/--no-atlas-emec", help="EMEC as in ATLAS.")] = None,
    atlas_fcal: Annotated[Optional[bool], typer.Option("--atlas-fcal/--no-atlas-fcal", help="FCAL as in ATLAS.")] = None,
    atlas_fcal_cells: Annotated[Optional[bool], typer.Option("--atlas-fcal-cells/--no-atlas-fcal-cells", help="FCAL cells as in ATLAS.")] = None,
    atlas_fcal_frozen_showers: Annotated[Optional[bool], typer.Option("--atlas-fcal-frozen-showers/--no-atlas-fcal-frozen-showers", help="FCAL frozen showers.")] = None,
    atlas_g4: Annotated[Optional[bool], typer.Option("--atlas-g4/--no-atlas-g4", help="ATLAS Geant4 physics.")] = None,
    tile_atlas_gap: Annotated[Optional[bool], typer.Option("--tile-atlas-gap/--no-tile-atlas-gap", help="ATLAS tile gap/crack.")] = None,
    atlas_endcap_cryostat: Annotated[Optional[bool], typer.Option("--atlas-endcap-cryostat/--no-atlas-endcap-cryostat", help="ATLAS end-cap cryostats.")] = None,
    atlas_barrel_cryostat: Annotated[Optional[bool], typer.Option("--atlas-barrel-cryostat/--no-atlas-barrel-cryostat", help="ATLAS barrel cryostat.")] = None,
    atlas_run4: Annotated[Optional[bool], typer.Option("--atlas-run4/--no-atlas-run4", help="ATLAS Run 4 geometry.")] = None,
    atlas_forward_shielding: Annotated[Optional[bool], typer.Option("--atlas-forward-shielding/--no-atlas-forward-shielding", help="ATLAS forward shielding.")] = None,
    atlas_full_field: Annotated[Optional[bool], typer.Option("--atlas-full-field/--no-atlas-full-field", help="ATLAS full field map.")] = None,
    atlas_barrel_gap_services: Annotated[Optional[bool], typer.Option("--atlas-barrel-gap-services/--no-atlas-barrel-gap-services", help="ATLAS barrel gap services.")] = None,
    tile_atlas_run4: Annotated[Optional[bool], typer.Option("--tile-atlas-run4/--no-tile-atlas-run4", help="ATLAS Tile Run 4.")] = None,
    atlas_emec_argon_fraction: Annotated[Optional[bool], typer.Option("--atlas-emec-argon-fraction/--no-atlas-emec-argon-fraction", help="ATLAS EMEC argon fraction.")] = None,
    atlas_run4_geometry: Annotated[str, typer.Option("--atlas-run4-geometry", help="Path to Run 4 SQLite DB.")] = "",
    atlas_field_map: Annotated[str, typer.Option("--atlas-field-map", help="Path to ATLAS field map.")] = "",
    atlas_fcal_electrodes: Annotated[str, typer.Option("--atlas-fcal-electrodes", help="Path to FCAL electrodes CSV.")] = "",
    active_energy_only: Annotated[Optional[bool], typer.Option("--active-energy-only/--no-active-energy-only", help="Keep only active medium energy.")] = None,
    birks_law: Annotated[Optional[bool], typer.Option("--birks-law/--no-birks-law", help="Apply Birks law.")] = None,
    atlas_hit_time: Annotated[Optional[bool], typer.Option("--atlas-hit-time/--no-atlas-hit-time", help="ATLAS hit time TOF.")] = None,
    tile_dual_readout: Annotated[int, typer.Option("--tile-dual-readout", help="Dual readout for tile cells (0=off, 1=U-shape, 2=linear).")] = 0,
    neutron_time_cut: Annotated[float, typer.Option("--neutron-time-cut", help="Neutron kill time in ns.")] = 0.0,
):
    clear_recorded_items()

    input_file = str(input_file)
    output_file = str(output_file)
    outputLevel = LoggingLevel.toC(output_level)

    exec(pre_init)

    is_v2 = (detector == "v2")
    get_val = lambda v: is_v2 if v is None else v

    if is_v2:
        atlas_kwargs = {
            "UseMagneticField": enable_magnetic_field,
            "UseSolenoidField": enable_solenoid_field,
            "TileAtlasGeometry": get_val(tile_atlas_geometry),
            "TileAtlasCells": get_val(tile_atlas_cells),
            "AtlasMaterialInFront": get_val(atlas_material_in_front),
            "TileAtlasItc": get_val(tile_atlas_itc),
            "AtlasEmb": get_val(atlas_emb),
            "AtlasEmbCells": get_val(atlas_emb_cells),
            "AtlasHec": get_val(atlas_hec),
            "AtlasEmec": get_val(atlas_emec),
            "AtlasFcal": get_val(atlas_fcal),
            "AtlasFcalCells": get_val(atlas_fcal_cells),
            "AtlasFcalElectrodes": atlas_fcal_electrodes,
            "AtlasFcalFrozenShowers": get_val(atlas_fcal_frozen_showers),
            "AtlasG4": get_val(atlas_g4),
            "TileAtlasGap": get_val(tile_atlas_gap),
            "AtlasEndcapCryostat": get_val(atlas_endcap_cryostat),
            "AtlasBarrelCryostat": get_val(atlas_barrel_cryostat),
            "AtlasRun4": get_val(atlas_run4),
            "AtlasRun4Geometry": atlas_run4_geometry,
            "AtlasForwardShielding": get_val(atlas_forward_shielding),
            "AtlasFullField": get_val(atlas_full_field),
            "AtlasBarrelGapServices": get_val(atlas_barrel_gap_services),
            "TileAtlasRun4": get_val(tile_atlas_run4),
            "AtlasEmecArgonFraction": get_val(atlas_emec_argon_fraction),
            "AtlasFieldMap": atlas_field_map,
        }
        det = DetectorConstruction_v2("ATLAS", **atlas_kwargs)
    else:
        det = DetectorConstruction_v1("ATLAS", UseMagneticField=enable_magnetic_field)

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
        NeutronTimeCut=neutron_time_cut,
        FastSimulation=(get_val(atlas_fcal_frozen_showers) or get_val(atlas_run4)) if is_v2 else False,
        AtlasG4=get_val(atlas_g4) if is_v2 else False,
    )

    calorimeter = CaloHitBuilder(
        "CaloHitBuilder",
        HistogramPath="Expert/Hits",
        OutputLevel=outputLevel,
        OutputHitsKey=recordable("Hits"),
        OnlyRoI=not save_all_hits,
        ActiveEnergyOnly=get_val(active_energy_only),
        BirksLaw=get_val(birks_law),
        AtlasHitTime=get_val(atlas_hit_time),
        TileDualReadout=tile_dual_readout,
    )
    calorimeter.merge(acc)

    HIT = RootStreamHITMaker(
        "RootStreamHITMaker",
        OutputLevel=outputLevel,
    )
    acc += HIT

    exec(pre_exec)
    acc.run(number_of_events)
    exec(post_exec)


if __name__ == "__main__":
    main()
