"""
GalticCfg.py - Canonical single-file configuration registry for all GALTIC subdetectors.

Consolidates 100% of sampling layer definitions and parameters in one place.
"""

from typing import List
import os
import numpy as np
from CaloCell.CaloDefs import CaloSampling
from GALTIC.Layer import (
    CaloSamplingLayer,
    DeadMaterialVolume,
    LArBarrelBuilder,
    TileCalBuilder,
    LArEMECBuilder,
    HECBuilder,
    DeadMaterialBuilder,
    Plates,
)

__all__ = [
    "getGalticLArBarrelCfg",
    "getGalticTileBarrelCfg",
    "getGalticTileExtendedCfg",
    "getGalticLArEMECCfg",
    "getGalticHECCfg",
    "getGalticDeadMaterialsCfg",
    "getGalticAllSamplings",
    "getGalticAllDeadMaterials",
]

_DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../data"))


def _lar_pulse() -> str:
    return os.path.join(_DATA_DIR, "pulseLar.dat")


def _tile_pulse() -> str:
    return os.path.join(_DATA_DIR, "pulseTile.dat")


def getGalticLArBarrelCfg() -> List[CaloSamplingLayer]:
    """Returns the 4 active sampling layers of the central LAr Barrel (EMB)."""
    return [
        LArBarrelBuilder("LAr::PSB", CaloSampling.PSB)
        .radii(1460.0, 1471.01)
        .z_length(6800.0)
        .segmentation(nof_layers=1, absorber_th=0.01, gap_th=11.0)
        .granularity(delta_eta=0.025, delta_phi=np.pi / 32.0)
        .electronics(noise_mev=90.0, pulse_file=_lar_pulse())
        .build(),
        LArBarrelBuilder("LAr::EMB1", CaloSampling.EMB1)
        .radii(1500.0, 1575.0)
        .z_length(6800.0)
        .segmentation(nof_layers=16, absorber_th=1.53, gap_th=4.5)
        .granularity(delta_eta=0.003125, delta_phi=np.pi / 32.0)
        .electronics(noise_mev=26.0, pulse_file=_lar_pulse())
        .build(),
        LArBarrelBuilder("LAr::EMB2", CaloSampling.EMB2)
        .radii(1575.0, 1875.0)
        .z_length(6800.0)
        .segmentation(nof_layers=16, absorber_th=1.53, gap_th=4.5)
        .granularity(delta_eta=0.025, delta_phi=np.pi / 128.0)
        .electronics(noise_mev=40.0, pulse_file=_lar_pulse())
        .build(),
        LArBarrelBuilder("LAr::EMB3", CaloSampling.EMB3)
        .radii(1875.0, 1960.0)
        .z_length(6800.0)
        .segmentation(nof_layers=16, absorber_th=1.53, gap_th=4.5)
        .granularity(delta_eta=0.05, delta_phi=np.pi / 128.0)
        .electronics(noise_mev=20.0, pulse_file=_lar_pulse())
        .build(),
    ]


def getGalticTileBarrelCfg() -> List[CaloSamplingLayer]:
    """Returns the 3 radial sampling layers of the central TileCal Barrel."""
    return [
        TileCalBuilder("TILE::TileCal1", CaloSampling.TileCal1)
        .radii(2283.0, 2683.0)
        .length_and_center(z_size=5640.0, z_center=0.0)
        .granularity(delta_eta=0.1, delta_phi=0.1)
        .electronics(noise_mev=25.0, pulse_file=_tile_pulse())
        .build(),
        TileCalBuilder("TILE::TileCal2", CaloSampling.TileCal2)
        .radii(2683.0, 3783.0)
        .length_and_center(z_size=5640.0, z_center=0.0)
        .granularity(delta_eta=0.1, delta_phi=0.1)
        .electronics(noise_mev=30.0, pulse_file=_tile_pulse())
        .build(),
        TileCalBuilder("TILE::TileCal3", CaloSampling.TileCal3)
        .radii(3783.0, 4283.0)
        .length_and_center(z_size=5640.0, z_center=0.0)
        .granularity(delta_eta=0.2, delta_phi=0.1)
        .electronics(noise_mev=35.0, pulse_file=_tile_pulse())
        .build(),
    ]


def getGalticTileExtendedCfg(side_a: bool = True) -> List[CaloSamplingLayer]:
    """Returns the 3 sampling layers of TileCal Extended Barrel for Side A or Side B."""
    z_center = 5119.0 if side_a else -5119.0
    side_tag = "A" if side_a else "B"
    return [
        TileCalBuilder(f"TILE::TileCalExt1::{side_tag}", CaloSampling.TileExt1)
        .radii(2283.0, 2683.0)
        .length_and_center(z_size=2830.0, z_center=z_center)
        .granularity(delta_eta=0.1, delta_phi=0.1)
        .electronics(noise_mev=25.0, pulse_file=_tile_pulse())
        .build(),
        TileCalBuilder(f"TILE::TileCalExt2::{side_tag}", CaloSampling.TileExt2)
        .radii(2683.0, 3783.0)
        .length_and_center(z_size=2830.0, z_center=z_center)
        .granularity(delta_eta=0.1, delta_phi=0.1)
        .electronics(noise_mev=30.0, pulse_file=_tile_pulse())
        .build(),
        TileCalBuilder(f"TILE::TileCalExt3::{side_tag}", CaloSampling.TileExt3)
        .radii(3783.0, 4283.0)
        .length_and_center(z_size=2830.0, z_center=z_center)
        .granularity(delta_eta=0.2, delta_phi=0.1)
        .electronics(noise_mev=35.0, pulse_file=_tile_pulse())
        .build(),
    ]


def getGalticLArEMECCfg(side_a: bool = True) -> List[CaloSamplingLayer]:
    """Returns the active sampling layers of LAr EMEC for Side A or Side B."""
    return [
        LArEMECBuilder("LAr::PSE", CaloSampling.PSE, side_a=side_a)
        .geometry(rmin=1232.0, rmax=1700.0, z_size=5.0, z_center=3737.5)
        .granularity(delta_eta=0.025, delta_phi=np.pi / 32.0)
        .electronics(noise_mev=90.0, pulse_file=_lar_pulse())
        .build(),
        LArEMECBuilder("LAr::EMEC1", CaloSampling.EMEC1, side_a=side_a)
        .geometry(rmin=302.0, rmax=2042.0, z_size=96.0, z_center=3788.0)
        .granularity(delta_eta=0.025, delta_phi=np.pi / 32.0)
        .electronics(noise_mev=35.0, pulse_file=_lar_pulse())
        .build(),
        LArEMECBuilder("LAr::EMEC2", CaloSampling.EMEC2, side_a=side_a)
        .geometry(rmin=302.0, rmax=2042.0, z_size=330.0, z_center=4001.0)
        .granularity(delta_eta=0.025, delta_phi=np.pi / 128.0)
        .electronics(noise_mev=45.0, pulse_file=_lar_pulse())
        .build(),
        LArEMECBuilder("LAr::EMEC3", CaloSampling.EMEC3, side_a=side_a)
        .geometry(rmin=302.0, rmax=2042.0, z_size=54.0, z_center=4193.0)
        .granularity(delta_eta=0.05, delta_phi=np.pi / 128.0)
        .electronics(noise_mev=25.0, pulse_file=_lar_pulse())
        .build(),
    ]


def getGalticHECCfg(side_a: bool = True) -> List[CaloSamplingLayer]:
    """Returns the 3 longitudinal sampling layers of HEC for Side A or Side B."""
    return [
        HECBuilder("FCal::HEC1", CaloSampling.HEC1, side_a=side_a)
        .geometry(rmin=372.0, rmax=2030.0, z_size=189.0, z_center=4356.5)
        .granularity(delta_eta=0.1, delta_phi=0.1)
        .electronics(noise_mev=80.0, pulse_file=_tile_pulse())
        .build(),
        HECBuilder("FCal::HEC2", CaloSampling.HEC2, side_a=side_a)
        .geometry(rmin=475.0, rmax=2030.0, z_size=336.0, z_center=4619.0)
        .granularity(delta_eta=0.1, delta_phi=0.1)
        .electronics(noise_mev=100.0, pulse_file=_tile_pulse())
        .build(),
        HECBuilder("FCal::HEC3", CaloSampling.HEC3, side_a=side_a)
        .geometry(rmin=475.0, rmax=2030.0, z_size=936.0, z_center=5255.0)
        .granularity(delta_eta=0.2, delta_phi=0.1)
        .electronics(noise_mev=120.0, pulse_file=_tile_pulse())
        .build(),
    ]


def getGalticDeadMaterialsCfg() -> List[DeadMaterialVolume]:
    """Returns all passive dead material volumes (cryostats and crack supports)."""
    return [
        DeadMaterialBuilder("DM::Cryo::Inner1")
        .geometry(rmin=1200.0, rmax=1250.0, z_size=6800.0)
        .materials(absorber="G4_Al", gap="Vacuum")
        .build(),
        DeadMaterialBuilder("DM::Cryo::Inner2")
        .geometry(rmin=1440.0, rmax=1455.0, z_size=6800.0)
        .materials(absorber="G4_Al", gap="Vacuum")
        .build(),
        DeadMaterialBuilder("DM::Cryo::Outer")
        .geometry(rmin=1980.0, rmax=2083.0, z_size=6800.0)
        .materials(absorber="G4_Al", gap="Vacuum")
        .build(),
        DeadMaterialBuilder("DM::Crack::EM::A")
        .geometry(rmin=900.0, rmax=2232.0, z_size=300.0, center=(0.0, 0.0, 3567.5))
        .materials(absorber="G4_Al", gap="Vacuum", plates=Plates.Vertical)
        .build(),
        DeadMaterialBuilder("DM::Crack::EM::B")
        .geometry(rmin=900.0, rmax=2232.0, z_size=300.0, center=(0.0, 0.0, -3567.5))
        .materials(absorber="G4_Al", gap="Vacuum", plates=Plates.Vertical)
        .build(),
        DeadMaterialBuilder("DM::Crack::TILE::A")
        .geometry(rmin=2283.0, rmax=4284.0, z_size=680.0, center=(0.0, 0.0, 3364.0))
        .materials(absorber="G4_Fe", gap="Vacuum", plates=Plates.Vertical)
        .build(),
        DeadMaterialBuilder("DM::Crack::TILE::B")
        .geometry(rmin=2283.0, rmax=4284.0, z_size=680.0, center=(0.0, 0.0, -3364.0))
        .materials(absorber="G4_Fe", gap="Vacuum", plates=Plates.Vertical)
        .build(),
    ]


def getGalticAllSamplings() -> List[CaloSamplingLayer]:
    """Returns the full list of active calorimeter sampling layers for GALTIC."""
    layers: List[CaloSamplingLayer] = []
    layers.extend(getGalticLArBarrelCfg())
    layers.extend(getGalticTileBarrelCfg())
    layers.extend(getGalticTileExtendedCfg(side_a=True))
    layers.extend(getGalticTileExtendedCfg(side_a=False))
    layers.extend(getGalticLArEMECCfg(side_a=True))
    layers.extend(getGalticLArEMECCfg(side_a=False))
    layers.extend(getGalticHECCfg(side_a=True))
    layers.extend(getGalticHECCfg(side_a=False))
    return layers


def getGalticAllDeadMaterials() -> List[DeadMaterialVolume]:
    """Returns all passive dead material volumes for GALTIC."""
    return getGalticDeadMaterialsCfg()
