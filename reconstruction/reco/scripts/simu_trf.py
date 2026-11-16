#!/usr/bin/env python3
"""
Script: simu_trf.py
Purpose: Simulates detector showers from generated events using Geant4.
Usage:
    simu_trf.py -i input.EVT.root -o output.HIT.root [options]
"""

import os
import sys
from pathlib import Path
from typing import Optional, Union
from typing_extensions import Annotated
import typer

from GaugiKernel import file_parallel_job, LoggingLevel
from GaugiKernel.constants import MINUTES
from G4Kernel import EventReader, ComponentAccumulator
from RootStreamBuilder import recordable, clear_recorded_items, RootStreamHITMaker
from CaloHitBuilder import CaloHitBuilder
from geometry.v1 import DetectorConstruction_v1
from geometry.v2 import DetectorConstruction_v2


def _get_geometry_v2_data_dir() -> str:
    """Returns the directory containing geometry v2 data files."""
    for p in (
        os.environ.get("LORENZETTI_GEOMETRY_V2_DATA_DIR"),
        os.environ.get("LORENZETTI_GEOMETRY_DATA_DIR"),
        str(Path(__file__).resolve().parents[3] / "geometry" / "v2" / "data"),
    ):
        if p and os.path.isdir(p):
            return p
    return ""


def keep_only_collection_tree(path: Union[str, Path]) -> None:
    """
    Keeps only the CollectionTree in the output file of --free-running-atlas-format,
    removing the monitoring directories (Event/, Expert/) as in the ATLAS ntuple.
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
    output_level: Annotated[str, typer.Option("-l", "--output-level", help="The output level messenger.")] = "INFO",
    pre_init: Annotated[str, typer.Option("--pre-init", help="The preinit command")] = "''",
    pre_exec: Annotated[str, typer.Option("--pre-exec", help="The preexec command")] = "''",
    post_exec: Annotated[str, typer.Option("--post-exec", help="The postexec command")] = "''",
    enable_magnetic_field: Annotated[bool, typer.Option("--enable-magnetic-field", help="Enable the magnetic field.")] = False,
    enable_solenoid_field: Annotated[Optional[bool], typer.Option("--enable-solenoid-field/--no-enable-solenoid-field", help="Enable solenoid field.")] = None,
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
    tile_dual_readout: Annotated[Optional[bool], typer.Option("--tile-dual-readout/--no-tile-dual-readout", help="Dual readout for tile cells.")] = None,
    tile_pmt_split: Annotated[str, typer.Option("--tile-pmt-split", help="Sharing between PMTs ('ushape' or 'linear').")] = "ushape",
    neutron_time_cut: Annotated[Optional[float], typer.Option("--neutron-time-cut", help="Neutron kill time in ns.")] = None,
    free_running_hits: Annotated[bool, typer.Option("--free-running-hits", help="Write hits in the layout of the ATLAS HITS ntuple.")] = False,
    free_running_atlas_format: Annotated[bool, typer.Option("--free-running-atlas-format", help="Write free-running hits as ATLAS HITS ntuple (compressed/filtered).")] = False,
    free_running_keep_hits: Annotated[bool, typer.Option("--free-running-keep-hits", help="Keep standard HIT stream and write free-running hits to FreeRunningTree.")] = False,
    free_running_no_binning: Annotated[bool, typer.Option("--free-running-no-binning", help="Free-running hits without time bins.")] = False,
    atlas_emec_charge_collection: Annotated[bool, typer.Option("--atlas-emec-charge-collection", help="EMEC charge collection as in ATLAS simulation.")] = False,
    atlas_emec_tables: Annotated[str, typer.Option("--atlas-emec-tables", help="Tables of the EMEC wheels.")] = "",
    atlas_emec_field_map: Annotated[str, typer.Option("--atlas-emec-field-map", help="Field map of the EMEC charge collection.")] = "",
    atlas_emec_hv_map: Annotated[str, typer.Option("--atlas-emec-hv-map", help="HV map of the EMEC.")] = "",
):
    clear_recorded_items()

    input_file = str(input_file)
    output_file = str(output_file)
    outputLevel = LoggingLevel.toC(output_level)

    exec(pre_init)

    is_v2 = (detector == "v2")
    get_val = lambda v: is_v2 if v is None else v

    if detector == "v1":
        v2_only_options = {
            "tile_atlas_geometry": tile_atlas_geometry,
            "tile_atlas_cells": tile_atlas_cells,
            "atlas_material_in_front": atlas_material_in_front,
            "tile_atlas_itc": tile_atlas_itc,
            "atlas_emb": atlas_emb,
            "atlas_emb_cells": atlas_emb_cells,
            "atlas_hec": atlas_hec,
            "atlas_emec": atlas_emec,
            "atlas_fcal": atlas_fcal,
            "atlas_fcal_cells": atlas_fcal_cells,
            "atlas_fcal_frozen_showers": atlas_fcal_frozen_showers,
            "atlas_g4": atlas_g4,
            "tile_atlas_gap": tile_atlas_gap,
            "atlas_endcap_cryostat": atlas_endcap_cryostat,
            "atlas_barrel_cryostat": atlas_barrel_cryostat,
            "atlas_run4": atlas_run4,
            "atlas_forward_shielding": atlas_forward_shielding,
            "atlas_full_field": atlas_full_field,
            "atlas_barrel_gap_services": atlas_barrel_gap_services,
            "tile_atlas_run4": tile_atlas_run4,
            "atlas_emec_argon_fraction": atlas_emec_argon_fraction,
        }
        for name, val in v2_only_options.items():
            if val is True:
                raise typer.BadParameter(
                    f"--{name.replace('_', '-')} is an option of the ATLAS geometry: it needs --detector v2"
                )

    if enable_magnetic_field and (is_v2 if enable_solenoid_field is None else enable_solenoid_field):
        raise typer.BadParameter(
            "--enable-magnetic-field and --enable-solenoid-field cannot be used together "
            "(with --detector v2 the solenoid field is on by default: --no-enable-solenoid-field)"
        )

    solenoid_field = False if enable_magnetic_field else get_val(enable_solenoid_field)
    tile_geom = get_val(tile_atlas_geometry)
    tile_cells = get_val(tile_atlas_cells)
    mat_in_front = get_val(atlas_material_in_front)
    tile_itc = get_val(tile_atlas_itc)
    emb = get_val(atlas_emb)
    emb_cells = get_val(atlas_emb_cells)
    hec = get_val(atlas_hec)
    emec = get_val(atlas_emec)
    fcal = get_val(atlas_fcal)
    fcal_cells = get_val(atlas_fcal_cells)
    fcal_frozen = get_val(atlas_fcal_frozen_showers)
    g4 = get_val(atlas_g4)
    tile_gap = get_val(tile_atlas_gap)
    endcap_cryo = get_val(atlas_endcap_cryostat)
    barrel_cryo = get_val(atlas_barrel_cryostat)
    run4 = get_val(atlas_run4)
    forward_shielding = get_val(atlas_forward_shielding)
    full_field = get_val(atlas_full_field)
    barrel_gap_services = get_val(atlas_barrel_gap_services)
    tile_run4 = get_val(tile_atlas_run4)
    emec_argon_frac = get_val(atlas_emec_argon_fraction)

    active_energy = get_val(active_energy_only)
    birks = get_val(birks_law)
    hit_time = get_val(atlas_hit_time)
    dual_readout = get_val(tile_dual_readout)

    if tile_cells and not tile_geom:
        raise typer.BadParameter("--tile-atlas-cells needs --tile-atlas-geometry")
    if dual_readout and not tile_cells:
        raise typer.BadParameter("--tile-dual-readout needs --tile-atlas-cells")
    if tile_itc and not tile_geom:
        raise typer.BadParameter("--tile-atlas-itc needs --tile-atlas-geometry")
    if tile_gap and not (tile_itc and tile_cells and emb_cells and mat_in_front and barrel_cryo):
        raise typer.BadParameter(
            "--tile-atlas-gap needs --tile-atlas-itc, --tile-atlas-cells, --atlas-emb-cells, "
            "--atlas-material-in-front and --atlas-barrel-cryostat"
        )
    if fcal_frozen and not fcal_cells:
        raise typer.BadParameter("--atlas-fcal-frozen-showers needs --atlas-fcal-cells")
    if fcal_cells and not fcal:
        raise typer.BadParameter("--atlas-fcal-cells needs --atlas-fcal")

    geom_data_dir = _get_geometry_v2_data_dir()
    if not atlas_fcal_electrodes:
        atlas_fcal_electrodes = os.environ.get(
            "LORENZETTI_FCAL_ELECTRODES",
            os.path.join(geom_data_dir, "LArFCalElectrodes-06.csv"),
        )
    if not atlas_emec_tables:
        atlas_emec_tables = os.path.join(geom_data_dir, "EmecTables-ATLAS-P2-RUN4-01-01-00.csv")
    if not atlas_emec_field_map:
        atlas_emec_field_map = os.path.join(geom_data_dir, "ec.fieldzv03")
    if not atlas_emec_hv_map:
        atlas_emec_hv_map = os.path.join(geom_data_dir, "HVEMECMap_v02.dat")

    if fcal_cells and not os.path.isfile(atlas_fcal_electrodes):
        raise typer.BadParameter(
            f"--atlas-fcal-cells needs the file of the FCal electrodes (--atlas-fcal-electrodes or "
            f"LORENZETTI_FCAL_ELECTRODES): '{atlas_fcal_electrodes}' not found"
        )

    if is_v2 and run4:
        for val, opt, env in (
            (atlas_run4_geometry, "--atlas-run4-geometry", "LORENZETTI_ATLAS_RUN4_GEOMETRY"),
            (atlas_field_map, "--atlas-field-map", "LORENZETTI_FIELD_MAP"),
        ):
            f = val or os.environ.get(env, "")
            if not os.path.isfile(f):
                raise typer.BadParameter(
                    f"--atlas-run4 (on by default with --detector v2) needs {opt} or the environment variable {env}: '{f}' not "
                    f"found; switch the Run 4 parts off with --no-atlas-run4 --no-tile-atlas-run4 "
                    f"--no-atlas-forward-shielding --no-atlas-full-field --no-atlas-barrel-gap-services"
                )

    if free_running_hits:
        if not (tile_geom and tile_cells):
            raise typer.BadParameter("--free-running-hits needs --tile-atlas-geometry and --tile-atlas-cells")
        if not (emb_cells and hec and emec):
            raise typer.BadParameter("--free-running-hits needs --atlas-emb-cells, --atlas-hec and --atlas-emec (the LAr cells of ATLAS)")
        if not tile_gap:
            raise typer.BadParameter("--free-running-hits needs --tile-atlas-gap (the E1-E4, C10 and D4 cells of ATLAS)")
        if not fcal_cells:
            raise typer.BadParameter("--free-running-hits needs --atlas-fcal-cells (the FCal cells of ATLAS)")
        if not fcal_frozen:
            raise typer.BadParameter("--free-running-hits needs --atlas-fcal-frozen-showers (the frozen showers of the ATLAS FCal)")
        if not g4:
            raise typer.BadParameter("--free-running-hits needs --atlas-g4 (the Geant4 settings of the ATLAS production)")
        if not run4:
            raise typer.BadParameter("--free-running-hits needs --atlas-run4 (the ATLAS Run 4 geometry and field of the simulation)")
        if free_running_atlas_format and not emec_argon_frac:
            raise typer.BadParameter("--free-running-atlas-format needs --atlas-emec-argon-fraction (the argon fraction of the ATLAS EMEC)")
        if free_running_atlas_format and not tile_run4:
            raise typer.BadParameter("--free-running-atlas-format needs --tile-atlas-run4 (the tile end-cap parts at the ATLAS simulation positions)")
        if free_running_atlas_format and not barrel_gap_services:
            raise typer.BadParameter("--free-running-atlas-format needs --atlas-barrel-gap-services (the ATLAS dead material of the barrel gap)")
        if free_running_atlas_format and not full_field:
            raise typer.BadParameter("--free-running-atlas-format needs --atlas-full-field (the field of the ATLAS simulation as in the production)")
        if free_running_atlas_format and not forward_shielding:
            raise typer.BadParameter("--free-running-atlas-format needs --atlas-forward-shielding (the ATLAS material outside the calorimeters)")
        if free_running_atlas_format and not atlas_emec_charge_collection:
            raise typer.BadParameter("--free-running-atlas-format needs --atlas-emec-charge-collection (the EMEC energy of the ATLAS simulation)")
        if atlas_emec_charge_collection:
            for f in (atlas_emec_tables, atlas_emec_field_map, atlas_emec_hv_map):
                if not os.path.isfile(f):
                    raise typer.BadParameter(f"--atlas-emec-charge-collection: file '{f}' not found")
        if dual_readout and tile_pmt_split != "ushape":
            raise typer.BadParameter("--free-running-hits uses the U-shape sharing of the ATLAS simulation (--tile-pmt-split ushape)")
        active_energy = True
        birks = True
        dual_readout = True
        tile_pmt_split = "ushape"
        if neutron_time_cut is None:
            neutron_time_cut = 150.0
    elif free_running_no_binning or free_running_keep_hits or free_running_atlas_format or atlas_emec_charge_collection:
        raise typer.BadParameter(
            "--free-running-no-binning, --free-running-keep-hits, --free-running-atlas-format and "
            "--atlas-emec-charge-collection need --free-running-hits"
        )

    if forward_shielding and not run4:
        raise typer.BadParameter("--atlas-forward-shielding needs --atlas-run4")
    if full_field and not forward_shielding:
        raise typer.BadParameter("--atlas-full-field needs --atlas-forward-shielding")
    if barrel_gap_services and not forward_shielding:
        raise typer.BadParameter("--atlas-barrel-gap-services needs --atlas-forward-shielding")
    if emec_argon_frac and not emec:
        raise typer.BadParameter("--atlas-emec-argon-fraction needs --atlas-emec")
    if tile_run4 and not (run4 and tile_gap):
        raise typer.BadParameter("--tile-atlas-run4 needs --atlas-run4 and --tile-atlas-gap")

    if neutron_time_cut is None:
        neutron_time_cut = 150.0 if is_v2 else 0.0

    tile_dual_readout_val = 0 if not dual_readout else (1 if tile_pmt_split == "ushape" else 2)

    if is_v2:
        atlas_kwargs = {
            "UseMagneticField": enable_magnetic_field,
            "UseSolenoidField": solenoid_field,
            "TileAtlasGeometry": tile_geom,
            "TileAtlasCells": tile_cells,
            "AtlasMaterialInFront": mat_in_front,
            "TileAtlasItc": tile_itc,
            "AtlasEmb": emb,
            "AtlasEmbCells": emb_cells,
            "AtlasHec": hec,
            "AtlasEmec": emec,
            "AtlasFcal": fcal,
            "AtlasFcalCells": fcal_cells,
            "AtlasFcalElectrodes": atlas_fcal_electrodes,
            "AtlasFcalFrozenShowers": fcal_frozen,
            "AtlasG4": g4,
            "TileAtlasGap": tile_gap,
            "AtlasEndcapCryostat": endcap_cryo,
            "AtlasBarrelCryostat": barrel_cryo,
            "AtlasRun4": run4,
            "AtlasRun4Geometry": atlas_run4_geometry,
            "AtlasForwardShielding": forward_shielding,
            "AtlasFullField": full_field,
            "AtlasBarrelGapServices": barrel_gap_services,
            "TileAtlasRun4": tile_run4,
            "AtlasEmecArgonFraction": emec_argon_frac,
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
        FastSimulation=(fcal_frozen or run4) if is_v2 else False,
        AtlasG4=g4 if is_v2 else False,
    )

    calorimeter = CaloHitBuilder(
        "CaloHitBuilder",
        HistogramPath="Expert/Hits",
        OutputLevel=outputLevel,
        OutputHitsKey=recordable("Hits"),
        OnlyRoI=not save_all_hits,
        ActiveEnergyOnly=active_energy,
        BirksLaw=birks,
        AtlasHitTime=hit_time,
        TileDualReadout=tile_dual_readout_val,
        FreeRunningHits=free_running_hits,
        FreeRunningBinning=not free_running_no_binning,
        FreeRunningNtupleName=("FreeRunningTree" if free_running_keep_hits else "CollectionTree"),
        FreeRunningAtlasFormat=free_running_atlas_format,
        EmecChargeCollection=atlas_emec_charge_collection,
        EmecChargeTables=atlas_emec_tables,
        EmecChargeFieldMap=atlas_emec_field_map,
        EmecChargeHVMap=atlas_emec_hv_map,
        InputEventKey=recordable("Events"),
    )
    calorimeter.merge(acc)

    if not (free_running_hits and not free_running_keep_hits):
        HIT = RootStreamHITMaker(
            "RootStreamHITMaker",
            OutputLevel=outputLevel,
            OnlyRoI=not save_all_hits,
            InputHitsKey=recordable("Hits"),
            InputEventKey=recordable("Events"),
            InputTruthKey=recordable("Particles"),
            InputSeedsKey=recordable("Seeds"),
        )
        acc += HIT

    exec(pre_exec)
    acc.run(number_of_events)
    exec(post_exec)

    if free_running_atlas_format:
        keep_only_collection_tree(output_file)


if __name__ == "__main__":
    main()
