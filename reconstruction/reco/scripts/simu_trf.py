#!/usr/bin/env python3

import multiprocessing
import argparse
import sys
import os

from pathlib                import Path
from GaugiKernel.constants  import MINUTES
from GaugiKernel            import LoggingLevel, get_argparser_formatter
from G4Kernel               import ComponentAccumulator, EventReader
from RootStreamBuilder      import recordable
from CaloHitBuilder         import CaloHitBuilder
from RootStreamBuilder      import RootStreamHITMaker

from geometry import DetectorConstruction_v1, DetectorConstruction_v2
from reco import update_args_from_file,merge_args_from_file


"""
Script: simu_trf.py
Purpose: Runs the full Geant4 simulation step in the Lorenzetti framework.
         Reads generated event files (EVT), simulates particle interactions with the detector,
         and produces Hit files (HIT).
Usage:
    simu_trf.py -i input.EVT.root -o output.HIT.root -nt <threads>
"""

def parse_args():
    """
    Parses command-line arguments for the simulation job.

    Returns:
        argparse.Namespace: Arguments specifying inputs/outputs, thread count,
                            magnetic field options, and execution hooks.
    """
    parser = argparse.ArgumentParser(
        description='',
        add_help=False,
        formatter_class=get_argparser_formatter())

    parser.add_argument('-i', '--input-file', action='store',
                            dest='input_file', required=True,
                            help="The input file or folder to run the job")
    parser.add_argument('-o', '--output-file', action='store',
                        dest='output_file', required=True,
                        help="The output file.")
    parser.add_argument('--nov', '--number-of-events', action='store',
                        dest='number_of_events', required=False,
                        type=int, default=-1,
                        help="The total number of events to run.")
    parser.add_argument('-nt', '--number-of-threads', action='store',
                        dest='number_of_threads', required=False,
                        type=int, default=multiprocessing.cpu_count(),
                        help="The number of threads")
    parser.add_argument('--enable-magnetic-field', action='store_true',
                        dest='enable_magnetic_field', required=False,
                        help="Enable the magnetic field.")
    parser.add_argument('--active-energy-only', action=argparse.BooleanOptionalAction, default=None,
                        dest='active_energy_only', required=False,
                        help="Keep only the energy deposited in the active medium of the calorimeters "
                             "(liquid argon, plastic scintillator), as in the ATLAS hits. By default the "
                             "whole energy deposited in the cell volume, absorber included, is kept. On by default with --detector v2 (--no-active-energy-only switches it off), off with v1.")
    parser.add_argument('--birks-law', action=argparse.BooleanOptionalAction, default=None,
                        dest='birks_law', required=False,
                        help="Apply Birks' law to the energy deposited in the plastic scintillator and in the "
                             "liquid argon, with the constants of the ATLAS simulation. Use it together with "
                             "--active-energy-only to follow the ATLAS hits. On by default with --detector v2 (--no-birks-law switches it off), off with v1.")
    parser.add_argument('--atlas-hit-time', action=argparse.BooleanOptionalAction, default=None,
                        dest='atlas_hit_time', required=False,
                        help="Choose the bunch crossing of each deposit in the hits by the time of the ATLAS simulation: the "
                             "global time minus the time of flight from the interaction point (liquid argon: minus |r|/c; tile "
                             "cells of ATLAS: the time of TileGeoG4SDCalc with the TOF correction, each PMT with its own delay). "
                             "Without it the global time of Geant4 is used, and the in-time energy of the end-cap, HEC and FCal "
                             "(more than 12.5 ns from the interaction point) falls in bunch crossing +1. The free-running hits "
                             "always use the ATLAS time. On by default with --detector v2 (--no-atlas-hit-time switches it off), off with v1.")
    parser.add_argument('--enable-solenoid-field', action=argparse.BooleanOptionalAction, default=None,
                        dest='enable_solenoid_field', required=False,
                        help="Enable a uniform 2 T axial field only inside the ATLAS central solenoid "
                             "(R < 1.23 m, |z| < 2.9 m), with no field in the calorimeters. "
                             "Cannot be combined with --enable-magnetic-field. "
                             "On by default with --detector v2 (--no-enable-solenoid-field switches it off), off with v1.")
    parser.add_argument('--tile-atlas-geometry', action=argparse.BooleanOptionalAction, default=None,
                        dest='tile_atlas_geometry', required=False,
                        help="Build the tile calorimeter as in ATLAS: scintillating tiles normal to the beam line, "
                             "stacked along z in periods of 18 mm (14 mm steel, 3 mm tile, 1 mm clearance), "
                             "with the ATLAS layer radii and z extent (long barrel |z| < 2808 mm, extended barrel "
                             "3554 < |z| < 6110 mm, the ITC aluminium block in between). Without --tile-atlas-cells "
                             "the cells keep the default eta x phi segmentation. On by default with --detector v2 (--no-tile-atlas-geometry switches it off), off with v1. Use the same option "
                             "in digit_trf.py.")
    parser.add_argument('--tile-atlas-cells', action=argparse.BooleanOptionalAction, default=None,
                        dest='tile_atlas_cells', required=False,
                        help="Use the ATLAS tile cells (A1-A16, BC1-BC8, B9, D0-D6; JINST 3 (2008) S08003, fig. 5.12) "
                             "instead of the eta x phi grid, so that every point of the tile volume belongs to a "
                             "cell. Needs --tile-atlas-geometry. Hits only: the digitization does not support these "
                             "cells yet. On by default with --detector v2 (--no-tile-atlas-cells switches it off), off with v1.")
    parser.add_argument('--tile-dual-readout', action=argparse.BooleanOptionalAction, default=None,
                        dest='tile_dual_readout', required=False,
                        help="Read each tile cell with two photomultipliers, as in ATLAS: the energy of each step is "
                             "shared between the PMT 0 and the PMT 1 (the one on the side of larger phi) according "
                             "to its azimuthal position across the module, and both are stored with the cell "
                             "(edep_pmt0, edep_pmt1). Needs --tile-atlas-cells. On by default with --detector v2 (--no-tile-dual-readout switches it off), off with v1.")
    parser.add_argument('--tile-pmt-split', action='store', choices=['ushape', 'linear'], default='ushape',
                        dest='tile_pmt_split', required=False,
                        help="Sharing between the two PMTs with --tile-dual-readout: 'ushape' (default), the "
                             "measured U-shape of the ATLAS simulation (Athena, TileGeoG4SDCalc::"
                             "Tile_1D_profileRescaled); 'linear', 0.5 +- 0.2 from the centre to the edges of the "
                             "module, the two PMTs adding up to the cell energy.")
    parser.add_argument('--atlas-material-in-front', action=argparse.BooleanOptionalAction, default=None,
                        dest='atlas_material_in_front', required=False,
                        help="Material in front of the barrel electromagnetic calorimeter as in ATLAS, in radiation "
                             "lengths at normal incidence: the solenoid (0.66 X0), the cryostat wall in front of the "
                             "presampler (0.76 X0 of aluminium instead of 0.45) and the material between the presampler "
                             "and the accordion (0.60 X0); JINST 3 (2008) S08003, fig. 5.1 and sec. 2.1.1. The inner "
                             "detector is not included. Simulation only (the cells do not change). On by default with --detector v2 (--no-atlas-material-in-front switches it off), off with v1.")
    parser.add_argument('--tile-atlas-itc', action=argparse.BooleanOptionalAction, default=None,
                        dest='tile_atlas_itc', required=False,
                        help="Build the gap between the tile barrel and the extended barrel as in ATLAS instead of the "
                             "aluminium block: the plug of the ITC (D4 and C10, steel and scintillator, passive) and the "
                             "cables and services (aluminium with 5%% of the volume); JINST 3 (2008) S08003, sec. 5.5 and "
                             "fig. 5.12. Needs --tile-atlas-geometry. Simulation only. On by default with --detector v2 (--no-tile-atlas-itc switches it off), off with v1.")
    parser.add_argument('--atlas-emb', action=argparse.BooleanOptionalAction, default=None,
                        dest='atlas_emb', required=False,
                        help="Barrel EM calorimeter with the ATLAS absorber composition: lead of 1.53 mm below "
                             "|eta| = 0.8 and 1.13 mm above, two 0.2 mm steel sheets, glue and electrode, liquid argon "
                             "of 2 x 2.1 mm, 470 mm of depth (JINST 3 (2008) S08003, sec. 5.2 and fig. 5.1). Radial "
                             "shells, not the accordion. Use the same option in digit_trf.py. On by default with --detector v2 (--no-atlas-emb switches it off), off with v1.")
    parser.add_argument('--atlas-emb-cells', action=argparse.BooleanOptionalAction, default=None,
                        dest='atlas_emb_cells', required=False,
                        help="Needs --atlas-emb. The barrel EM layers end at |z| = 3165 mm as in ATLAS (instead of "
                             "3400 mm), with steps of one layer that follow |eta| = 1.475 near the inner radius, and have "
                             "the cells of the ATLAS identifier dictionary: EMB1 strips of 0.003125 (indices 1-447, 64 phi) "
                             "and 3 cells of 0.025 in 1.4-1.475 (256 phi); EMB2 56 cells of 0.025 up to 1.4 and one of "
                             "0.075 in 1.4-1.475 (256 phi); EMB3 27 cells of 0.05 up to 1.35 (256 phi). The cell comes from "
                             "the eta of the point seen from the origin, as in the ATLAS simulation (Athena LArG4Barrel "
                             "LArBarrelGeometry); the eta of the hit is the nominal centre of the cell. The presamplers do "
                             "not change. Use the same option in digit_trf.py. On by default with --detector v2 (--no-atlas-emb-cells switches it off), off with v1.")
    parser.add_argument('--atlas-hec', action=argparse.BooleanOptionalAction, default=None,
                        dest='atlas_hec', required=False,
                        help="HEC as in ATLAS, with the nominal values of the ATLAS geometry (without the shift of the installed detector): "
                             "four samplings HEC0-HEC3 in two wheels (z = 4277-5093.5 and 5134-6095 mm), copper plates "
                             "of 25 and 50 mm with first plates of 12.5 and 25 mm, 8.5 mm gaps, and the cells of the "
                             "ATLAS identifier dictionary found from the radius of the readout pads of each block, as "
                             "in the ATLAS simulation (JINST 3 (2008) S08003, sec. 5.3; Athena HECGeometry). "
                             "Use the same option in digit_trf.py. On by default with --detector v2 (--no-atlas-hec switches it off), off with v1.")
    parser.add_argument('--tile-atlas-gap', action=argparse.BooleanOptionalAction, default=None,
                        dest='tile_atlas_gap', required=False,
                        help="Gap and crack scintillators E1-E4 (Run 3 geometry, the crack ones of polyvinyltoluene) and the "
                             "active ITC cells C10 and D4 as in ATLAS, with the extended barrel at the nominal ATLAS position "
                             "(front plate at |z| = 3519.5 mm, 140 periods of 18.25 mm, cells by the numbers of periods of "
                             "ATLAS); from the public ATLAS GeoModel geometry and the Tile tables of the ATLAS geometry database, "
                             "without the shift of the installed detector. Identifiers, PMTs and special modules as in ATLAS "
                             "(E cells with one PMT). Needs --tile-atlas-itc, --atlas-emb-cells, --atlas-material-in-front and "
                             "--atlas-barrel-cryostat. Simulation only. On by default with --detector v2 (--no-tile-atlas-gap switches it off), off with v1.")
    parser.add_argument('--atlas-fcal', action=argparse.BooleanOptionalAction, default=None,
                        dest='atlas_fcal', required=False,
                        help="Forward calorimeter of ATLAS as passive material, without cells: the three modules (copper, then "
                             "two of tungsten; r = 72-449.6 mm, z = 4668.5-6045.1 mm without the shift of the installed "
                             "detector) as tubes of the mean mixture of absorber, rods and liquid argon, from the public ATLAS "
                             "GeoModel geometry (JINST 3 (2008) S08003, Table 5.4). Simulation only. On by default with --detector v2 (--no-atlas-fcal switches it off), off with v1.")
    parser.add_argument('--atlas-fcal-cells', action=argparse.BooleanOptionalAction, default=None,
                        dest='atlas_fcal_cells', required=False,
                        help="The FCal of ATLAS with its electrodes and cells, instead of the mean mixture of --atlas-fcal: "
                             "each module is a tube of absorber with one liquid argon gap per electrode (12260, 10200 and 8224 "
                             "per side) and the cable troughs, from the public ATLAS GeoModel geometry; the cell of a deposit is "
                             "the tile of its electrode, as in the ATLAS simulation. The electrodes come from the file given by "
                             "--atlas-fcal-electrodes. The FCal cells go to the hit collection (samplings FCAL1-FCAL3, "
                             "one cell per ATLAS tile) and, with --free-running-hits, to LArHitFCAL. Needs --atlas-fcal. Simulation only. On by default with --detector v2 (--no-atlas-fcal-cells switches it off), off with v1.")
    parser.add_argument('--atlas-fcal-frozen-showers', action=argparse.BooleanOptionalAction, default=None,
                        dest='atlas_fcal_frozen_showers', required=False,
                        help="Frozen showers in the FCal of ATLAS, as the ATLAS simulation (FrozenShowersFCalOnly of the Athena "
                             "release 23.0.14): e- of 3 (FCal1) or 1 (FCal2, FCal3) to 1000 MeV, photons below 10 MeV and neutrons "
                             "below 100 MeV in the FCal modules are replaced by showers of the ATLAS libraries (MC23_v1, in "
                             "geometry/data/LArG4ShowerLibData). Needs --atlas-fcal-cells. Simulation only. On by default with --detector v2 (--no-atlas-fcal-frozen-showers switches it off), off with v1.")
    parser.add_argument('--atlas-g4', action=argparse.BooleanOptionalAction, default=None, dest='atlas_g4', required=False,
                        help="Geant4 settings of the ATLAS production (Athena release 23.0.14, campaign PhaseII): physics list "
                             "FTFP_BERT_ATL, production cuts of the ATLAS regions (0.1 mm in the EM barrel and endcap, 0.03 mm in the "
                             "FCal, 1 mm elsewhere), applyCuts, GammaGeneralProcess, the stacking action of ATLAS (neutron Russian "
                             "roulette below 2 MeV and photon Russian roulette below 0.5 MeV in the LAr, weight 10; neutrinos killed), "
                             "deposits multiplied by the track weight, the looper killer (1000100 steps, event aborted), the dead "
                             "material shower behind the FCal (|z| > 5698 mm in the endcap cryostat) and liquid argon of 1.396 g/cm3. "
                             "Simulation only. On by default with --detector v2 (--no-atlas-g4 switches it off), off with v1.")
    parser.add_argument('--atlas-run4', action=argparse.BooleanOptionalAction, default=None, dest='atlas_run4', required=False,
                        help="The ATLAS Run 4 geometry of the simulation of the reference production (ATLAS-P2-RUN4-01-01-00, Athena "
                             "23.0.14): the LAr end-cap (presampler, EMEC, HEC, FCal) 45 mm further from the interaction point, where the "
                             "ATLAS simulation places it, with its cells. Needs --atlas-emec, --atlas-hec, --atlas-emb-cells, "
                             "--atlas-fcal-cells and --atlas-endcap-cryostat, the GeoModel dump (--atlas-run4-geometry) and the field map "
                             "(--atlas-field-map). Imports the ITk, the HGTD, the beam pipe and the end-cap cryostats of ATLAS, with the "
                             "field, the regions and the beam pipe killer of the ATLAS simulation. Simulation only. On by default with --detector v2 (--no-atlas-run4 switches it off), off with v1.")
    parser.add_argument('--atlas-run4-geometry', action='store', dest='atlas_run4_geometry', required=False, type=str, default="",
                        help="GeoModel dump of the ATLAS geometry of the simulation for --atlas-run4 (written by "
                             "geometry/scripts/atlas_run4_dumpgeo.sh); default: the environment variable LORENZETTI_ATLAS_RUN4_GEOMETRY.")
    parser.add_argument('--atlas-field-map', action='store', dest='atlas_field_map', required=False, type=str, default="",
                        help="Field map of the ATLAS simulation for --atlas-run4 (bfieldmap_7730_20400_14m.root, from "
                             "/cvmfs/atlas.cern.ch/repo/sw/database/GroupData/MagneticFieldMaps); default: the environment variable "
                             "LORENZETTI_FIELD_MAP.")
    parser.add_argument('--atlas-forward-shielding', action=argparse.BooleanOptionalAction, default=None, dest='atlas_forward_shielding', required=False,
                        help="The ATLAS material outside the calorimeters, imported as passive material from the GeoModel dump of "
                             "--atlas-run4: the whole MuonSys (end-cap and barrel toroids, forward shielding JD/JT/JF with its borated "
                             "polyethylene, NSW, muon stations, calorimeter saddle) and the girders, fingers and extended-barrel saddles "
                             "of the tile calorimeter; world of 30 m. Needs --atlas-run4; needed by --free-running-atlas-format. Simulation only. "
                             "On by default with --detector v2 (--no-atlas-forward-shielding switches it off), off with v1.")
    parser.add_argument('--atlas-full-field', action=argparse.BooleanOptionalAction, default=None, dest='atlas_full_field', required=False,
                        help="The field of the ATLAS simulation as in the production: the map in the whole world (not only in the cylinder "
                             "of the calorimeters) and, as MuonFieldOnlyInCalo of ATLAS, only the muons in the field inside the barrel EM "
                             "calorimeter (the SwitchingFieldManager of Athena, 1500 < r < 1900 mm, |z| < 2000 mm). Needs "
                             "--atlas-forward-shielding; needed by --free-running-atlas-format. Simulation only. On by default with --detector v2 (--no-atlas-full-field switches it off), off with v1.")
    parser.add_argument('--atlas-barrel-gap-services', action=argparse.BooleanOptionalAction, default=None, dest='atlas_barrel_gap_services', required=False,
                        help="The dead material of ATLAS in the gap between the barrel and the extended barrel, imported from the GeoModel "
                             "dump of --atlas-run4 instead of the services of --tile-atlas-itc (DM::ITC::Services, 5%% of aluminium): the "
                             "LAr::DM::* volumes of the barrel cryostat (sector envelopes, bridges, base and sector plates, pedestals, front-end "
                             "boards, crates), the signal feedthroughs and their cables, and the saddles of the tile barrel. Needs "
                             "--atlas-forward-shielding; needed by --free-running-atlas-format. Simulation only. On by default with --detector v2 (--no-atlas-barrel-gap-services switches it off), off with v1.")
    parser.add_argument('--tile-atlas-run4', action=argparse.BooleanOptionalAction, default=None, dest='tile_atlas_run4', required=False,
                        help="The extended barrel, ITC, gap and crack of the tile calorimeter at the positions of the ATLAS simulation of "
                             "Run 4 (the GeoModel dump of --atlas-run4: 40 mm further on side A and 30 mm on side C than the nominal "
                             "positions of --tile-atlas-gap), with their cells; with --atlas-barrel-gap-services the sector and bridge "
                             "envelopes of the LAr services are then imported too. Needs --atlas-run4 and --tile-atlas-gap; needed by "
                             "--free-running-atlas-format. Simulation only. On by default with --detector v2 (--no-tile-atlas-run4 switches it off), off with v1.")
    parser.add_argument('--detector', action='store',
                        dest='detector', required=False,
                        type=str, default='v1', choices=['v1', 'v2'],
                        help="The detector construction: v1, the original geometry, or v2, the ATLAS geometry; the options of the "
                             "ATLAS geometry need v2.")
    parser.add_argument('--atlas-emec-argon-fraction', action=argparse.BooleanOptionalAction, default=None, dest='atlas_emec_argon_fraction', required=False,
                        help="The gap of each radial band of the ATLAS-like EMEC from the volume fraction of liquid argon of the ATLAS "
                             "accordion (LArWheelCalculator of Athena), instead of the gap linear in r of --atlas-emec. Needs --atlas-emec; "
                             "needed by --free-running-atlas-format. On by default with --detector v2 (--no-atlas-emec-argon-fraction switches it off), off with v1.")
    parser.add_argument('--free-running-atlas-format', action='store_true', dest='free_running_atlas_format', required=False,
                        help="Write the free-running hits as the ATLAS HITS ntuple: the LAr energy and time compressed as the ATLAS "
                             "HITS (LArHitContainerCnv_p2) and filtered as FilterHit_tf (LArHitFilter, including its layer cuts in the "
                             "HEC and FCAL), without the extra tglobal branches. Needs --free-running-hits. Off by default.")
    parser.add_argument('--atlas-emec-charge-collection', action='store_true', dest='atlas_emec_charge_collection', required=False,
                        help="Energy of the free-running hits of the EMEC as in the ATLAS simulation (Athena 23.0.14, LArG4::EC::"
                             "EnergyCalculator with EnergyCorrection = 8): Birks' law with the local field (HV / gap) and the current of "
                             "the charge collection (CalculateChargeCollection1, field map ec.fieldzv03, HV map HVEMECMap_v02.dat), with the "
                             "ported ATLAS code, on each step brought to the frame of the ATLAS wheel and moved in phi into the liquid argon "
                             "of the accordion. Needs --free-running-hits; needed by --free-running-atlas-format. Off by default.")
    parser.add_argument('--atlas-emec-tables', action='store', dest='atlas_emec_tables', required=False, type=str,
                        default=os.path.join(os.environ.get('LORENZETTI_GEOMETRY_DATA_DIR', ''), 'EmecTables-ATLAS-P2-RUN4-01-01-00.csv'),
                        help="Tables of the EMEC wheels for --atlas-emec-charge-collection (geometry/scripts/emec_tables_from_geomdb.py); "
                             "default: geometry/data/EmecTables-ATLAS-P2-RUN4-01-01-00.csv.")
    parser.add_argument('--atlas-emec-field-map', action='store', dest='atlas_emec_field_map', required=False, type=str,
                        default=os.path.join(os.environ.get('LORENZETTI_GEOMETRY_DATA_DIR', ''), 'ec.fieldzv03'),
                        help="Field map of the EMEC charge collection (LArG4EC/ec.fieldzv03 of ATLASCALDATA, CVMFS); default: "
                             "geometry/data/ec.fieldzv03.")
    parser.add_argument('--atlas-emec-hv-map', action='store', dest='atlas_emec_hv_map', required=False, type=str,
                        default=os.path.join(os.environ.get('LORENZETTI_GEOMETRY_DATA_DIR', ''), 'HVEMECMap_v02.dat'),
                        help="HV map of the EMEC (LArG4EC/HVEMECMap_v02.dat of ATLASCALDATA, CVMFS); default: "
                             "geometry/data/HVEMECMap_v02.dat.")
    parser.add_argument('--atlas-fcal-electrodes', action='store', dest='atlas_fcal_electrodes', required=False,
                        type=str, default=os.environ.get('LORENZETTI_FCAL_ELECTRODES',
                                  os.path.join(os.environ.get('LORENZETTI_GEOMETRY_DATA_DIR', ''), 'LArFCalElectrodes-06.csv')),
                        help="CSV file with the electrodes of the ATLAS FCal (table LArFCalElectrodes of the ATLAS geometry "
                             "database, as written by geometry/scripts/fcal_electrodes_from_geomdb.py). Default: the environment "
                             "variable LORENZETTI_FCAL_ELECTRODES, or geometry/data/LArFCalElectrodes-06.csv (the table of the "
                             "Run 3 geometry ATLAS-R3S-2021-03-00-03).")
    parser.add_argument('--atlas-emec', action=argparse.BooleanOptionalAction, default=None,
                        dest='atlas_emec', required=False,
                        help="EM end-cap as in ATLAS, with the nominal values of the ATLAS geometry (without the shift of the "
                             "installed detector): two wheels (1.375-2.5 and 2.5-3.2 in eta, 3 mm apart) from z = 3702 to "
                             "4216 mm, the cones approximated by steps; radial bands of 100 mm made of layers of an "
                             "equivalent absorber (lead of 1.7 or 2.2 mm, steel, prepreg and electrode) and liquid "
                             "argon with the gap of ATLAS at each radius; EMEC3 only in the outer wheel; the cells of "
                             "the ATLAS identifier dictionary found as in the ATLAS simulation (JINST 3 (2008) S08003, "
                             "sec. 5.2; Athena LArG4EC EnergyCalculator). The end-cap presampler is moved to just in "
                             "front of the EMEC (provisional). Use the same option in digit_trf.py. On by default with --detector v2 (--no-atlas-emec switches it off), off with v1.")
    parser.add_argument('--atlas-endcap-cryostat', action=argparse.BooleanOptionalAction, default=None,
                        dest='atlas_endcap_cryostat', required=False,
                        help="Outer cylinders of the end-cap cryostats as in ATLAS: warm vessel of 20 mm of aluminium "
                             "(r = 2260-2280 mm), cold vessel of 35 mm (r = 2140-2175 mm) and the liquid argon between "
                             "the EMEC and the cold vessel (dead material), from z = 3717.5 mm to the back of each vessel; "
                             "LAr calorimeter TDR, CERN/LHCC 96-41, fig. 3-3 and 5-i, and JINST 3 (2008) S08003, sec. "
                             "5.4. Simulation only (the cells do not change). On by default with --detector v2 (--no-atlas-endcap-cryostat switches it off), off with v1.")
    parser.add_argument('--atlas-barrel-cryostat', action=argparse.BooleanOptionalAction, default=None,
                        dest='atlas_barrel_cryostat', required=False,
                        help="Outer part of the barrel cryostat as in ATLAS instead of the two 100 mm aluminium shells: "
                             "cold and warm outer cylinders of 30 mm (r = 2140-2170 and 2220-2250 mm), end walls, the "
                             "steps for the feed-throughs and the dead liquid argon between the EM barrel and the cold "
                             "vessel; LAr calorimeter TDR, CERN/LHCC 96-41, fig. 3-2. Needs --tile-atlas-itc. "
                             "Simulation only (the cells do not change). On by default with --detector v2 (--no-atlas-barrel-cryostat switches it off), off with v1.")
    parser.add_argument('-t', '--timeout', action='store',
                        dest='timeout', required=False, type=int, default=240,
                        help="Event timeout in minutes")
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
    parser.add_argument('--save-all-hits', action='store_true',
                        dest='save_all_hits', required=False,
                        help="Save all hits into the output file.")
    parser.add_argument('--free-running-hits', action='store_true',
                        dest='free_running_hits', required=False,
                        help="Write the tile and LAr hits in the layout of the ATLAS HITS ntuple (tree CollectionTree: "
                             "EventNumber, TileCalHit_cellID/energy/time/eta/phi/sampling/side/module/tower and "
                             "LArHitEMB/EMEC/HEC_cellID/energy/time/eta/phi/region/sampling/barrel_ec (pos_neg in the HEC), "
                             "LArHitFCAL_cellID/energy/time/eta/phi/module, plus the extra *_tglobal) instead of the standard HIT "
                             "stream. Tile, as in the ATLAS simulation: one entry per PMT, with the ATLAS identifier (pmt_id, "
                             "64-bit), the visible energy (active medium and Birks' law, switched on by this option), the "
                             "time of TileGeoG4SDCalc (time of flight and fibre corrections, PMT delays, hits after "
                             "350.5 ns kept at 99995 ns) and its time bins (0.5 ns within +-75.25 ns, 5 ns outside). "
                             "LAr and FCal, as in the ATLAS simulation (LArG4SimpleSD): one entry per cell and time bin (2.5 ns up to "
                             "10 ns, 5 ns up to 50 ns, 25 ns up to 100 ns, one bin above), with the ATLAS identifier "
                             "(channel_id), the energy in the liquid argon with Birks' law, the global time minus r/c and no "
                             "time window; no energy threshold and full precision (the FilterHit_tf cuts and compression of "
                             "the ATLAS ntuples are applied outside). "
                             "Needs --tile-atlas-geometry, --tile-atlas-cells, --tile-atlas-gap, --atlas-emb-cells, --atlas-hec, "
                             "--atlas-emec, --atlas-fcal-cells, --atlas-fcal-frozen-showers, --atlas-g4 and --atlas-run4 (all on by "
                             "default with --detector v2); switches on --tile-dual-readout (U-shape). Off by default, also with "
                             "--detector v2.")
    parser.add_argument('--neutron-time-cut', action='store', type=float, default=None,
                        dest='neutron_time_cut', required=False,
                        help="Kill every neutron this time (ns) after the start of the event, as the ATLAS simulation does "
                             "with 150 ns (Sim.NeutronTimeCut; arXiv:1005.4568, sec. 5.5). Without it, the default of "
                             "Geant4 (10 us in FTFP_BERT). 150 ns by default with --detector v2 and with --free-running-hits.")
    parser.add_argument('--free-running-no-binning', action='store_true',
                        dest='free_running_no_binning', required=False,
                        help="With --free-running-hits: one entry per PMT and Geant4 step, without the time bins.")
    parser.add_argument('--free-running-keep-hits', action='store_true',
                        dest='free_running_keep_hits', required=False,
                        help="With --free-running-hits, for checks: keep also the standard HIT stream (tree "
                             "CollectionTree) and write the free-running hits in the tree FreeRunningTree.")
    parser.add_argument('--dry-run', action='store_true',
                        dest='dry_run', required=False,
                        help="Run the script without executing the main logic.")
    return merge_args_from_file(parser)


def main(logging_level: str,
         input_file: str | Path,
         output_file: str | Path,
         pre_init: str,
         pre_exec: str,
         post_exec: str,
         enable_magnetic_field: bool,
         enable_solenoid_field: bool,
         tile_atlas_geometry: bool,
         tile_atlas_cells: bool,
         atlas_material_in_front: bool,
         tile_atlas_itc: bool,
         atlas_emb: bool,
         atlas_emb_cells: bool,
         atlas_hec: bool,
         atlas_emec: bool,
         atlas_fcal: bool,
         atlas_fcal_cells: bool,
         atlas_fcal_electrodes: str,
         atlas_fcal_frozen_showers: bool,
         atlas_g4: bool,
         atlas_run4: bool,
         atlas_run4_geometry: str,
         atlas_forward_shielding: bool,
         atlas_full_field: bool,
         atlas_barrel_gap_services: bool,
         tile_atlas_run4: bool,
         atlas_emec_argon_fraction: bool,
         atlas_field_map: str,
         free_running_atlas_format: bool,
         detector: str,
         atlas_emec_charge_collection: bool,
         atlas_emec_tables: str,
         atlas_emec_field_map: str,
         atlas_emec_hv_map: str,
         tile_atlas_gap: bool,
         atlas_endcap_cryostat: bool,
         atlas_barrel_cryostat: bool,
         tile_dual_readout: int,
         active_energy_only: bool,
         birks_law: bool,
         atlas_hit_time: bool,
         save_all_hits : bool,
         free_running_hits : bool,
         free_running_binning : bool,
         free_running_keep_hits : bool,
         neutron_time_cut : float,
         timeout: int,
         number_of_events: int,
         number_of_threads: int,
         dry_run: bool,
         ):
    """
    Main function to drive the Geant4 simulation.

    Constructs the simulation environment using `ComponentAccumulator`:
    1. Initializes Detector Construction (DetectorConstruction_v1).
    2. Sets up the Event Reader to stream events from input.
    3. Configures the CaloHitBuilder to collect energy deposits.
    4. Merges components and executes the run loop.

    Args:
        logging_level (str): Verbosity level.
        input_file (str | Path): Path to the input event file.
        output_file (str | Path): Path to the output hit file.
        pre_init (str): Python code to execute before initialization.
        pre_exec (str): Python code to execute before the run loop.
        post_exec (str): Python code to execute after the run loop.
        enable_magnetic_field (bool): Toggle for the detector magnetic field.
        enable_solenoid_field (bool): Toggle for the field confined to the solenoid volume.
        tile_atlas_geometry (bool): Build the ATLAS-like tile calorimeter.
        tile_atlas_cells (bool): Use the ATLAS tile cells (needs tile_atlas_geometry).
        atlas_material_in_front (bool): Material in front of the barrel EM calorimeter as in ATLAS.
        tile_atlas_itc (bool): The gap between the tile barrel and the extended barrel as in ATLAS.
        atlas_emb (bool): Barrel EM calorimeter with the ATLAS absorber composition.
        atlas_emb_cells (bool): Barrel EM with the ATLAS length (|z| < 3165 mm) and cells (needs atlas_emb).
        atlas_hec (bool): HEC as in ATLAS (four samplings, nominal geometry and cells of ATLAS).
        atlas_emec (bool): EM end-cap as in ATLAS (two wheels, nominal geometry, composition and cells of ATLAS).
        atlas_fcal (bool): Forward calorimeter of ATLAS as passive material (three modules, no cells).
        atlas_fcal_cells (bool): The FCal of ATLAS with its electrodes and cells (needs atlas_fcal).
        atlas_fcal_electrodes (str): CSV file of the electrodes of the ATLAS FCal (geometry/scripts/fcal_electrodes_from_geomdb.py).
        tile_atlas_gap (bool): Gap/crack scintillators E1-E4 and active ITC as in ATLAS, nominal extended barrel.
        atlas_endcap_cryostat (bool): Outer cylinders of the end-cap cryostats as in ATLAS.
        atlas_barrel_cryostat (bool): Outer part of the barrel cryostat as in ATLAS.
        tile_dual_readout (int): Two PMTs per tile cell: 0 = off, 1 = ATLAS U-shape, 2 = linear (needs tile_atlas_cells).
        active_energy_only (bool): Keep only the energy deposited in the active medium.
        birks_law (bool): Apply Birks' law in the scintillator and in the liquid argon.
        atlas_hit_time (bool): Bunch crossing of the hits from the time of the ATLAS simulation (time of flight taken out).
        save_all_hits (bool): If True, saves all hits regardless of Region of Interest (RoI).
        free_running_hits (bool): Write the tile, LAr and FCal hits in the layout of the ATLAS HITS ntuple instead of the HIT stream.
        free_running_binning (bool): Time bins of the ATLAS simulation for the free-running hits.
        free_running_keep_hits (bool): Keep also the standard HIT stream (free-running hits in the tree FreeRunningTree).
        neutron_time_cut (float): Time (ns) after which neutrons are killed; 0 keeps the Geant4 default.
        timeout (int): Timeout in minutes.
        number_of_events (int): Number of events to process.
        number_of_threads (int): Number of Geant4 threads.
        dry_run (bool): If True, sets up but does not execute the run.
    """

    if isinstance(input_file, Path):
        input_file = str(input_file)
    if isinstance(output_file, Path):
        output_file = str(output_file)

    
    outputLevel = LoggingLevel.toC(logging_level)
    exec(pre_init)

    acc = ComponentAccumulator("ComponentAccumulator", 
                               (DetectorConstruction_v2( "ATLAS", UseMagneticField=enable_magnetic_field,
                                                        UseSolenoidField=enable_solenoid_field,
                                                        TileAtlasGeometry=tile_atlas_geometry,
                                                        TileAtlasCells=tile_atlas_cells,
                                                        AtlasMaterialInFront=atlas_material_in_front,
                                                        TileAtlasItc=tile_atlas_itc,
                                                        AtlasEmb=atlas_emb,
                                                        AtlasEmbCells=atlas_emb_cells,
                                                        AtlasHec=atlas_hec,
                                                        AtlasEmec=atlas_emec,
                                                        AtlasFcal=atlas_fcal,
                                                        AtlasFcalCells=atlas_fcal_cells,
                                                        AtlasFcalElectrodes=atlas_fcal_electrodes,
                                                        AtlasFcalFrozenShowers=atlas_fcal_frozen_showers,
                                                        AtlasG4=atlas_g4,
                                                        TileAtlasGap=tile_atlas_gap,
                                                        AtlasEndcapCryostat=atlas_endcap_cryostat,
                                                        AtlasBarrelCryostat=atlas_barrel_cryostat,
                                                        AtlasRun4=atlas_run4,
                                                        AtlasRun4Geometry=atlas_run4_geometry,
                                                        AtlasForwardShielding=atlas_forward_shielding,
                                                        AtlasFullField=atlas_full_field,
                                                        AtlasBarrelGapServices=atlas_barrel_gap_services,
                                                        TileAtlasRun4=tile_atlas_run4,
                                                        AtlasEmecArgonFraction=atlas_emec_argon_fraction,
                                                        AtlasFieldMap=atlas_field_map)
                                if detector == 'v2' else DetectorConstruction_v1( "ATLAS", UseMagneticField=enable_magnetic_field)),
                               NumberOfThreads=number_of_threads,
                               OutputFile=output_file,
                               Timeout=timeout * MINUTES,
                               NeutronTimeCut=neutron_time_cut,
                               FastSimulation=(atlas_fcal_frozen_showers or atlas_run4),
                               AtlasG4=atlas_g4)

    gun = EventReader("EventReader", input_file,
                      # outputs
                      OutputEventKey=recordable("Events"),
                      OutputTruthKey=recordable("Particles"),
                      OutputSeedKey=recordable("Seeds"),
                      )
    calorimeter = CaloHitBuilder("CaloHitBuilder",
                                 HistogramPath="Expert/Hits",
                                 OutputLevel=outputLevel,
                                 OutputHitsKey=recordable("Hits"),
                                 ActiveEnergyOnly=active_energy_only,
                                 BirksLaw=birks_law,
                                 AtlasHitTime=atlas_hit_time,
                                 TileDualReadout=tile_dual_readout,
                                 FreeRunningHits=free_running_hits,
                                 FreeRunningBinning=free_running_binning,
                                 FreeRunningNtupleName=("FreeRunningTree" if free_running_keep_hits else "CollectionTree"),
                                 FreeRunningAtlasFormat=free_running_atlas_format,
                                 EmecChargeCollection=atlas_emec_charge_collection,
                                 EmecChargeTables=atlas_emec_tables,
                                 EmecChargeFieldMap=atlas_emec_field_map,
                                 EmecChargeHVMap=atlas_emec_hv_map,
                                 InputEventKey=recordable("Events")
                                 )
    
    gun.merge(acc)
    calorimeter.merge(acc)
    if free_running_hits and not free_running_keep_hits:
        # only the free-running hits (CaloFreeRunningHitWriter, added by the CaloHitBuilder)
        HIT = None
    else:
        HIT = RootStreamHITMaker("RootStreamHITMaker",
                                 OutputLevel=outputLevel,
                                 OnlyRoI= not save_all_hits,
                                 InputHitsKey=recordable("Hits"),
                                 InputEventKey=recordable("Events"),
                                 InputTruthKey=recordable("Particles"),
                                 InputSeedsKey=recordable("Seeds"),
                                 )
    if HIT is not None:
        acc += HIT
    
    exec(pre_exec)
    if not dry_run:
        acc.run(number_of_events)
        exec(post_exec)
        if free_running_atlas_format:
            keep_only_collection_tree(output_file)


def keep_only_collection_tree(path):
    """
    The file of --free-running-atlas-format as the ATLAS ntuple (F41 conserto 28): only the CollectionTree, without the monitoring
    directories of the framework (Event/, Expert/). The tree is copied as it is (fast clone, same compression settings).
    """
    import ROOT
    src = ROOT.TFile.Open(path)
    tree = src.Get("CollectionTree")
    if not tree:
        src.Close()
        return
    tmp = path + ".tmp"
    dst = ROOT.TFile(tmp, "RECREATE", "", src.GetCompressionSettings())
    tree.CloneTree(-1, "fast").Write()
    dst.Close(); src.Close()
    os.replace(tmp, path)



if __name__ == "__main__":
    parser=parse_args()
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    args = parser.parse_args()

    if Path(args.input_file).is_dir():
        raise IsADirectoryError(f"Input file '{args.input_file}' was expected to be a file, "
                                 "but it is a directory. Please provide a list of files instead.")
    
    args = update_args_from_file(args)
    # defaults of the ATLAS options (F41, 05/11/2026): on with --detector v2, off with v1 (the geometry of the collaboration)
    atlas_options = ['enable_solenoid_field', 'tile_atlas_geometry', 'tile_atlas_cells', 'atlas_material_in_front', 'tile_atlas_itc', 'atlas_emb', 'atlas_emb_cells', 'atlas_hec', 'atlas_emec', 'atlas_fcal', 'atlas_fcal_cells', 'atlas_fcal_frozen_showers', 'atlas_g4', 'tile_atlas_gap', 'atlas_endcap_cryostat', 'atlas_barrel_cryostat', 'atlas_run4', 'atlas_forward_shielding', 'atlas_full_field', 'atlas_barrel_gap_services', 'tile_atlas_run4', 'atlas_emec_argon_fraction']
    atlas_hit_options = ['active_energy_only', 'birks_law', 'tile_dual_readout', 'atlas_hit_time']
    if args.detector == 'v1':
        v2_only = [o for o in atlas_options if getattr(args, o)]
        if v2_only:
            parser.error('--' + v2_only[0].replace('_', '-') + ' is an option of the ATLAS geometry: it needs --detector v2')
    for o in atlas_options + atlas_hit_options:
        if getattr(args, o) is None:
            setattr(args, o, args.detector == 'v2')
    if args.detector == 'v2' and args.neutron_time_cut is None:
        args.neutron_time_cut = 150.
    if args.detector == 'v2' and args.atlas_run4:
        for value, option, env in ((args.atlas_run4_geometry, '--atlas-run4-geometry', 'LORENZETTI_ATLAS_RUN4_GEOMETRY'),
                                   (args.atlas_field_map, '--atlas-field-map', 'LORENZETTI_FIELD_MAP')):
            f = value or os.environ.get(env, '')
            if not os.path.isfile(f):
                parser.error("--atlas-run4 (on by default with --detector v2) needs %s or the environment variable %s: '%s' not "
                             "found; switch the Run 4 parts off with --no-atlas-run4 --no-tile-atlas-run4 "
                             "--no-atlas-forward-shielding --no-atlas-full-field --no-atlas-barrel-gap-services" % (option, env, f))
    print(f"input file: {args.input_file}")
    if args.enable_magnetic_field and args.enable_solenoid_field:
        parser.error("--enable-magnetic-field and --enable-solenoid-field cannot be used together (with --detector v2 the solenoid "
                     "field is on by default: --no-enable-solenoid-field)")
    if args.tile_atlas_cells and not args.tile_atlas_geometry:
        parser.error("--tile-atlas-cells needs --tile-atlas-geometry")
    if args.tile_dual_readout and not args.tile_atlas_cells:
        parser.error("--tile-dual-readout needs --tile-atlas-cells")
    if args.tile_atlas_itc and not args.tile_atlas_geometry:
        parser.error("--tile-atlas-itc needs --tile-atlas-geometry")
    if args.tile_atlas_gap and not (args.tile_atlas_itc and args.tile_atlas_cells and args.atlas_emb_cells and
                                    args.atlas_material_in_front and args.atlas_barrel_cryostat):
        parser.error("--tile-atlas-gap needs --tile-atlas-itc, --tile-atlas-cells, --atlas-emb-cells, --atlas-material-in-front "
                     "and --atlas-barrel-cryostat")
    if args.atlas_fcal_frozen_showers and not args.atlas_fcal_cells:
        parser.error("--atlas-fcal-frozen-showers needs --atlas-fcal-cells")
    if args.atlas_fcal_cells and not args.atlas_fcal:
        parser.error("--atlas-fcal-cells needs --atlas-fcal")
    if args.atlas_fcal_cells and not os.path.isfile(args.atlas_fcal_electrodes):
        parser.error("--atlas-fcal-cells needs the file of the FCal electrodes (--atlas-fcal-electrodes or "
                     "LORENZETTI_FCAL_ELECTRODES): '%s' not found" % args.atlas_fcal_electrodes)
    if args.free_running_hits:
        # free-running hits as in the ATLAS simulation: ATLAS tile cells, active medium, Birks' law, U-shape dual readout
        if not (args.tile_atlas_geometry and args.tile_atlas_cells):
            parser.error("--free-running-hits needs --tile-atlas-geometry and --tile-atlas-cells")
        # the LAr cells with the ATLAS identifier (F41 conserto 19)
        if not (args.atlas_emb_cells and args.atlas_hec and args.atlas_emec):
            parser.error("--free-running-hits needs --atlas-emb-cells, --atlas-hec and --atlas-emec (the LAr cells of ATLAS)")
        # the gap/crack and ITC cells of ATLAS (F41 conserto 21)
        if not args.tile_atlas_gap:
            parser.error("--free-running-hits needs --tile-atlas-gap (the E1-E4, C10 and D4 cells of ATLAS)")
        # the FCal cells of ATLAS (F41 conserto 22)
        if not args.atlas_fcal_cells:
            parser.error("--free-running-hits needs --atlas-fcal-cells (the FCal cells of ATLAS)")
        # the frozen showers of the ATLAS FCal (F41 conserto 23)
        if not args.atlas_fcal_frozen_showers:
            parser.error("--free-running-hits needs --atlas-fcal-frozen-showers (the frozen showers of the ATLAS FCal)")
        # the Geant4 settings of the ATLAS production (F41 conserto 24)
        if not args.atlas_g4:
            parser.error("--free-running-hits needs --atlas-g4 (the Geant4 settings of the ATLAS production)")
        # the ATLAS Run 4 geometry and field of the simulation (F41 conserto 27)
        if not args.atlas_run4:
            parser.error("--free-running-hits needs --atlas-run4 (the ATLAS Run 4 geometry and field of the simulation)")
        # the charge collection of the ATLAS EM end-cap (F41 conserto 29)
        # the ATLAS material outside the calorimeters (F41 conserto 32)
        # the field of the ATLAS simulation as in the production (F41 conserto 33)
        # the dead material of ATLAS in the gap between the barrel and the extended barrel (F41 conserto 34)
        # the tile extended barrel, ITC, gap and crack at the positions of the ATLAS simulation of Run 4 (F41 conserto 35)
        # the region of the hit makers at the midpoint of the step (F41 conserto 36)
        # the argon fraction of the ATLAS accordion in the EMEC (F41 conserto 37)
        if args.free_running_atlas_format and not args.atlas_emec_argon_fraction:
            parser.error("--free-running-atlas-format needs --atlas-emec-argon-fraction (the argon fraction of the ATLAS EMEC)")
        if args.free_running_atlas_format and not args.tile_atlas_run4:
            parser.error("--free-running-atlas-format needs --tile-atlas-run4 (the tile end-cap parts at the ATLAS simulation positions)")
        if args.free_running_atlas_format and not args.atlas_barrel_gap_services:
            parser.error("--free-running-atlas-format needs --atlas-barrel-gap-services (the ATLAS dead material of the barrel gap)")
        if args.free_running_atlas_format and not args.atlas_full_field:
            parser.error("--free-running-atlas-format needs --atlas-full-field (the field of the ATLAS simulation as in the production)")
        if args.free_running_atlas_format and not args.atlas_forward_shielding:
            parser.error("--free-running-atlas-format needs --atlas-forward-shielding (the ATLAS material outside the calorimeters)")
        if args.free_running_atlas_format and not args.atlas_emec_charge_collection:
            parser.error("--free-running-atlas-format needs --atlas-emec-charge-collection (the EMEC energy of the ATLAS simulation)")
        if args.atlas_emec_charge_collection:
            for f in (args.atlas_emec_tables, args.atlas_emec_field_map, args.atlas_emec_hv_map):
                if not os.path.isfile(f):
                    parser.error("--atlas-emec-charge-collection: file '%s' not found" % f)
        if args.tile_dual_readout and args.tile_pmt_split != 'ushape':
            parser.error("--free-running-hits uses the U-shape sharing of the ATLAS simulation (--tile-pmt-split ushape)")
        args.active_energy_only = True
        args.birks_law = True
        args.tile_dual_readout = True
        args.tile_pmt_split = 'ushape'
        if args.neutron_time_cut is None:
            args.neutron_time_cut = 150.
    elif args.free_running_no_binning or args.free_running_keep_hits or args.free_running_atlas_format or args.atlas_emec_charge_collection:
        parser.error("--free-running-no-binning, --free-running-keep-hits, --free-running-atlas-format and "
                     "--atlas-emec-charge-collection need --free-running-hits")
    if args.atlas_forward_shielding and not args.atlas_run4:
        parser.error("--atlas-forward-shielding needs --atlas-run4")
    if args.atlas_full_field and not args.atlas_forward_shielding:
        parser.error("--atlas-full-field needs --atlas-forward-shielding")
    if args.atlas_barrel_gap_services and not args.atlas_forward_shielding:
        parser.error("--atlas-barrel-gap-services needs --atlas-forward-shielding")
    if args.atlas_emec_argon_fraction and not args.atlas_emec:
        parser.error("--atlas-emec-argon-fraction needs --atlas-emec")
    if args.tile_atlas_run4 and not (args.atlas_run4 and args.tile_atlas_gap):
        parser.error("--tile-atlas-run4 needs --atlas-run4 and --tile-atlas-gap")
    print(f"output file: {args.output_file}")
    print(f"number of threads: {args.number_of_threads}")

    main(
             logging_level         = args.output_level,
             input_file            = args.input_file,
             output_file           = args.output_file,
             pre_init              = args.pre_init,
             pre_exec              = args.pre_exec,
             post_exec             = args.post_exec,
             enable_magnetic_field = args.enable_magnetic_field,
             enable_solenoid_field = args.enable_solenoid_field,
             tile_atlas_geometry   = args.tile_atlas_geometry,
             tile_atlas_cells      = args.tile_atlas_cells,
             atlas_material_in_front = args.atlas_material_in_front,
             tile_atlas_itc        = args.tile_atlas_itc,
             atlas_emb             = args.atlas_emb,
             atlas_emb_cells       = args.atlas_emb_cells,
             atlas_hec             = args.atlas_hec,
             atlas_emec            = args.atlas_emec,
             atlas_fcal            = args.atlas_fcal,
             atlas_fcal_cells      = args.atlas_fcal_cells,
             atlas_fcal_electrodes = args.atlas_fcal_electrodes,
             atlas_fcal_frozen_showers = args.atlas_fcal_frozen_showers,
             atlas_g4              = args.atlas_g4,
             atlas_run4            = args.atlas_run4,
             atlas_run4_geometry   = args.atlas_run4_geometry,
             atlas_forward_shielding = args.atlas_forward_shielding,
             atlas_full_field      = args.atlas_full_field,
             atlas_barrel_gap_services = args.atlas_barrel_gap_services,
             tile_atlas_run4       = args.tile_atlas_run4,
             atlas_emec_argon_fraction = args.atlas_emec_argon_fraction,
             atlas_field_map       = args.atlas_field_map,
             free_running_atlas_format = args.free_running_atlas_format,
             detector              = args.detector,
             atlas_emec_charge_collection = args.atlas_emec_charge_collection,
             atlas_emec_tables     = args.atlas_emec_tables,
             atlas_emec_field_map  = args.atlas_emec_field_map,
             atlas_emec_hv_map     = args.atlas_emec_hv_map,
             tile_atlas_gap        = args.tile_atlas_gap,
             atlas_endcap_cryostat = args.atlas_endcap_cryostat,
             atlas_barrel_cryostat = args.atlas_barrel_cryostat,
             tile_dual_readout     = (0 if not args.tile_dual_readout else
                                      (1 if args.tile_pmt_split == 'ushape' else 2)),
             active_energy_only    = args.active_energy_only,
             birks_law             = args.birks_law,
             atlas_hit_time        = args.atlas_hit_time,
             save_all_hits         = args.save_all_hits,
             free_running_hits     = args.free_running_hits,
             free_running_binning  = not args.free_running_no_binning,
             free_running_keep_hits = args.free_running_keep_hits,
             neutron_time_cut      = args.neutron_time_cut or 0,
             timeout               = args.timeout,
             number_of_events      = args.number_of_events,
             number_of_threads     = args.number_of_threads,
             dry_run               = args.dry_run,
        )



