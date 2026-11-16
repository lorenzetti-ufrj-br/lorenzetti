#!/usr/bin/env python3
"""
Script: digit_trf.py
Purpose: Performs the digitization step in the simulation chain.
         Converts Geant4 energy hits into digital signals (cells) by simulating
         electronic logical pulses, noise, and cross-talk.
Usage:
    digit_trf.py -i input.HIT.root -o output.ESD.root
"""

from pathlib import Path
from typing import Optional
from typing_extensions import Annotated
import typer
import os

from GaugiKernel import file_parallel_job, ComponentAccumulator, LoggingLevel
from CaloCellBuilder import CaloCellBuilder
from RootStreamBuilder import (
    RootStreamHITReader,
    recordable,
    clear_recorded_items,
    RootStreamESDMaker,
    RootStreamESDFlags,
)
from geometry.v1 import DetectorConstruction_v1
from geometry.v2 import DetectorConstruction_v2


@file_parallel_job(ntuple_name="CollectionTree", output_replace=(".HIT", ".ESD"))
def main(
    input_file: Annotated[str | Path, typer.Option("-i", "--input-file", help="Path to input HIT file or directory")],
    output_file: Annotated[str | Path, typer.Option("-o", "--output-file", help="Path to output ESD file or directory")],
    number_of_threads: Annotated[int, typer.Option("-nt", "--number-of-threads", help="Threads allocated per worker")] = 1,
    nov: Annotated[int, typer.Option("--nov", "--number-of-events", help="Number of events to process.")] = -1,
    output_level: Annotated[str, typer.Option("-l", "--output-level", help="Logging verbosity level.")] = "INFO",
    pre_init: Annotated[str, typer.Option("--pre-init", help="Hook for pre-initialization code.")] = "''",
    pre_exec: Annotated[str, typer.Option("--pre-exec", help="Hook for pre-execution code.")] = "''",
    post_exec: Annotated[str, typer.Option("--post-exec", help="Hook for post-execution code.")] = "''",
    save_all_cells: Annotated[bool, typer.Option("--save-all-cells", help="Save all cells in the ESD.")] = False,
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
):
    clear_recorded_items()

    input_file = str(input_file)
    output_file = str(output_file)
    outputLevel = LoggingLevel.toC(output_level)

    exec(pre_init)

    HIT = RootStreamHITReader(
        "HITReader",
        InputFile=input_file,
        OutputHitsKey=recordable("Hits"),
        OutputEventKey=recordable("Events"),
        OutputTruthKey=recordable("Particles"),
        OutputSeedsKey=recordable("Seeds"),
        OutputLevel=outputLevel,
    )

    acc = ComponentAccumulator("ComponentAccumulator", output_file, HIT)

    if detector == "v2":
        is_v2 = True
        get_val = lambda v: is_v2 if v is None else v
        atlas_kwargs = {
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
            "AtlasFcalFrozenShowers": get_val(atlas_fcal_frozen_showers),
            "AtlasG4": get_val(atlas_g4),
            "TileAtlasGap": get_val(tile_atlas_gap),
            "AtlasEndcapCryostat": get_val(atlas_endcap_cryostat),
            "AtlasBarrelCryostat": get_val(atlas_barrel_cryostat),
            "AtlasRun4": get_val(atlas_run4),
            "AtlasForwardShielding": get_val(atlas_forward_shielding),
            "AtlasFullField": get_val(atlas_full_field),
            "AtlasBarrelGapServices": get_val(atlas_barrel_gap_services),
            "TileAtlasRun4": get_val(tile_atlas_run4),
            "AtlasEmecArgonFraction": get_val(atlas_emec_argon_fraction),
            "AtlasRun4Geometry": atlas_run4_geometry,
            "AtlasFieldMap": atlas_field_map,
            "AtlasFcalElectrodes": atlas_fcal_electrodes,
        }
        det = DetectorConstruction_v2("ATLAS", **atlas_kwargs)
    else:
        det = DetectorConstruction_v1("ATLAS")

    calorimeter = CaloCellBuilder(
        "CaloCellBuilder",
        det,
        HistogramPath="Expert/Cells",
        OutputLevel=outputLevel,
        InputHitsKey=recordable("Hits"),
        OutputCellsKey=recordable("Cells"),
        OutputTruthCellsKey=recordable("TruthCells"),
        InputEventKey=recordable("Events"),
    )
    calorimeter.merge(acc)

    RootStreamESDFlags.SaveAllCells = save_all_cells
    RootStreamESDFlags.OnlyRoI = not save_all_cells

    ESD = RootStreamESDMaker(
        "RootStreamESDMaker",
        OutputLevel=outputLevel,
    )
    acc += ESD

    exec(pre_exec)
    acc.run(nov)
    exec(post_exec)


if __name__ == "__main__":
    main()
