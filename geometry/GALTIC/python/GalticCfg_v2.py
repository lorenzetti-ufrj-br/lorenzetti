"""
GalticCfg_v2.py - v2 configuration registry for all GALTIC subdetectors.

Represents the v2 branch geometry configuration featuring:
- Compact EMB geometry with 1.53 mm lead absorbers and finer eta segmentation.
- TileCal configuration with 5640 mm barrel length and 0.1 delta_phi.
- Unified single-segment readout for EMEC and HEC modules.
- Cryostat volumes (DM::Cryo::Inner1, DM::Cryo::Inner2, DM::Cryo::Outer).
Each volume contains exhaustive comparative notes (# NOTE:) mapping differences against:
- v1 (a32691874ab042e7d8759f6f33141ac60b88e3da): geometry/python/v1
- v2 (master branch): geometry/python/v2
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
    """Returns the 4 active sampling layers of the central LAr Barrel (EMB) in v2 configuration."""
    return [
        # -------------------------------------------------------------------------
        # LAr::PSB (Presampler Barrel)
        # -------------------------------------------------------------------------
        # NOTE: PSB está CONFORME em dimensões, segmentação e ruído.
        # - No v1: RMin=1460.0 mm, RMax=1471.01 mm, ZSize=6800.0 mm, nof_layers=1, abso=0.01 mm, gap=11.0 mm,
        #   Noise=90 MeV, deta=0.025, dphi=pi/32, AbsorberMaterial="Vacuum".
        #   v1 link: https://github.com/lorenzetti-ufrj-br/lorenzetti/blob/a32691874ab042e7d8759f6f33141ac60b88e3da/geometry/python/v1/ECAL.py#L34-L47
        # - No v2 (master): Default (atlas_emb_cells=False) é idêntico ao v1:
        #   v2 default link: https://github.com/lorenzetti-ufrj-br/lorenzetti/blob/master/geometry/python/v2/ECAL.py#L48-L61
        LArBarrelBuilder("LAr::PSB", CaloSampling.PSB)
        .radii(1460.0, 1471.01)  # NOTE: RMin=1460.0, RMax=1471.01 mm (v1 e v2 default).
        .z_length(6800.0)  # NOTE: ZSize=6800.0 mm (v1 e v2 default).
        .segmentation(nof_layers=1, absorber_th=0.01, gap_th=11.0)  # NOTE: 1 camada, 0.01 mm abso, 11.0 mm gap.
        .granularity(delta_eta=0.025, delta_phi=np.pi / 32.0)  # NOTE: deta=0.025, dphi=pi/32.
        .electronics(noise_mev=90.0, pulse_file=_lar_pulse())  # NOTE: Ruído=90.0 MeV.
        .build(),

        # -------------------------------------------------------------------------
        # LAr::EMB1 (Electromagnetic Barrel Layer 1 - Strips)
        # -------------------------------------------------------------------------
        # NOTE: Configuração v2 com parâmetros derivados de atlas_emb e atlas_emb_cells.
        # - No v2: RMin=1500.0, RMax=1575.0 mm; abso=1.53 mm Pb (copiado de v2:ECAL.py#L118); deta=0.003125 (v2:ECAL.py#L233).
        # - No v1: RMin=1500.0, RMax=1596.0 mm; abso=1.51 mm Pb; deta=0.00325 (ECAL.py#L50-L63).
        LArBarrelBuilder("LAr::EMB1", CaloSampling.EMB1)
        .radii(1500.0, 1575.0)  # NOTE: No v2: (1500.0, 1575.0). No v1: (1500.0, 1596.0) (ECAL.py#L58).
        .z_length(6800.0)  # NOTE: ZSize=6800.0 mm (v1 e v2 default).
        .segmentation(nof_layers=16, absorber_th=1.53, gap_th=4.5)  # NOTE: No v2: abso=1.53 mm, gap=4.5 mm (v2:ECAL.py#L118). No v1: abso=1.51 mm, gap=4.49 mm (ECAL.py#L55).
        .granularity(delta_eta=0.003125, delta_phi=np.pi / 32.0)  # NOTE: No v2: deta=0.003125 (EMB_ATLAS_REGIONS v2:ECAL.py#L233). No v1: deta=0.00325 (ECAL.py#L98).
        .electronics(noise_mev=26.0, pulse_file=_lar_pulse())  # NOTE: Ruído=26.0 MeV (v1 e v2).
        .build(),

        # -------------------------------------------------------------------------
        # LAr::EMB2 (Electromagnetic Barrel Layer 2 - Middle)
        # -------------------------------------------------------------------------
        # NOTE: Configuração v2 com 16 camadas de 1.53/4.5 mm e ruído de 40 MeV.
        # - No v2: RMin=1575.0, RMax=1875.0 mm, 16 camadas, ruído=40.0 MeV.
        # - No v1: RMin=1596.0, RMax=1926.0 mm, 55 camadas de 1.70/4.30 mm, ruído=60.0 MeV (ECAL.py#L65-L78).
        LArBarrelBuilder("LAr::EMB2", CaloSampling.EMB2)
        .radii(1575.0, 1875.0)  # NOTE: No v2: (1575.0, 1875.0). No v1: (1596.0, 1926.0) (ECAL.py#L72).
        .z_length(6800.0)  # NOTE: ZSize=6800.0 mm.
        .segmentation(nof_layers=16, absorber_th=1.53, gap_th=4.5)  # NOTE: No v2: 16 camadas de 1.53/4.5 mm. No v1: 55 camadas de 1.70/4.30 mm (ECAL.py#L69-L70).
        .granularity(delta_eta=0.025, delta_phi=np.pi / 128.0)  # NOTE: deta=0.025, dphi=pi/128.
        .electronics(noise_mev=40.0, pulse_file=_lar_pulse())  # NOTE: No v2: ruído=40.0 MeV. No v1: ruído=60.0 MeV (ECAL.py#L129).
        .build(),

        # -------------------------------------------------------------------------
        # LAr::EMB3 (Electromagnetic Barrel Layer 3 - Back)
        # -------------------------------------------------------------------------
        # NOTE: Configuração v2 com 16 camadas de 1.53/4.5 mm e ruído de 20 MeV.
        # - No v2: RMin=1875.0, RMax=1960.0 mm, 16 camadas, ruído=20.0 MeV.
        # - No v1: RMin=1926.0, RMax=1980.0 mm, 9 camadas de 1.70/4.30 mm, ruído=40.0 MeV (ECAL.py#L80-L93).
        LArBarrelBuilder("LAr::EMB3", CaloSampling.EMB3)
        .radii(1875.0, 1960.0)  # NOTE: No v2: (1875.0, 1960.0). No v1: (1926.0, 1980.0) (ECAL.py#L86).
        .z_length(6800.0)  # NOTE: ZSize=6800.0 mm.
        .segmentation(nof_layers=16, absorber_th=1.53, gap_th=4.5)  # NOTE: No v2: 16 camadas de 1.53/4.5 mm. No v1: 9 camadas de 1.70/4.30 mm (ECAL.py#L84-L85).
        .granularity(delta_eta=0.05, delta_phi=np.pi / 128.0)  # NOTE: deta=0.05, dphi=pi/128.
        .electronics(noise_mev=20.0, pulse_file=_lar_pulse())  # NOTE: No v2: ruído=20.0 MeV. No v1: ruído=40.0 MeV (ECAL.py#L143).
        .build(),
    ]


def getGalticTileBarrelCfg() -> List[CaloSamplingLayer]:
    """Returns the 3 radial sampling layers of the central TileCal Barrel in v2 configuration."""
    # -------------------------------------------------------------------------
    # TileCal Barrel (TileCal1, TileCal2, TileCal3)
    # -------------------------------------------------------------------------
    # NOTE: Configuração v2 com comprimento em Z derivado de TileAtlasGeometry (v2:TILE.py#L27).
    # - No v2: ZSize=5640.0 mm, delta_phi=0.1 float, ruídos 25, 30 e 35 MeV.
    # - No v1: ZSize=6048.0 mm, delta_phi=pi/32 rad, ruído=20.0 MeV para todos (TILE.py#L40-L134).
    return [
        TileCalBuilder("TILE::TileCal1", CaloSampling.TileCal1)
        .radii(2283.0, 2683.0)  # NOTE: RMin=2283.0, RMax=2683.0 mm.
        .length_and_center(z_size=5640.0, z_center=0.0)  # NOTE: No v2: z_size=5640.0 mm (aproximação ATLAS 5616 mm). No v1: 6048.0 mm (TILE.py#L42).
        .granularity(delta_eta=0.1, delta_phi=0.1)  # NOTE: No v2: delta_phi=0.1 float. No v1: delta_phi=pi/32 rad (TILE.py#L91).
        .electronics(noise_mev=25.0, pulse_file=_tile_pulse())  # NOTE: No v2: ruído=25.0 MeV. No v1: 20.0 MeV (TILE.py#L103).
        .build(),

        TileCalBuilder("TILE::TileCal2", CaloSampling.TileCal2)
        .radii(2683.0, 3783.0)  # NOTE: RMin=2683.0, RMax=3783.0 mm.
        .length_and_center(z_size=5640.0, z_center=0.0)  # NOTE: No v2: z_size=5640.0 mm. No v1: 6048.0 mm (TILE.py#L42).
        .granularity(delta_eta=0.1, delta_phi=0.1)  # NOTE: No v2: delta_phi=0.1 float. No v1: delta_phi=pi/32 rad (TILE.py#L92).
        .electronics(noise_mev=30.0, pulse_file=_tile_pulse())  # NOTE: No v2: ruído=30.0 MeV. No v1: 20.0 MeV (TILE.py#L117).
        .build(),

        TileCalBuilder("TILE::TileCal3", CaloSampling.TileCal3)
        .radii(3783.0, 4283.0)  # NOTE: RMin=3783.0, RMax=4283.0 mm.
        .length_and_center(z_size=5640.0, z_center=0.0)  # NOTE: No v2: z_size=5640.0 mm. No v1: 6048.0 mm (TILE.py#L42).
        .granularity(delta_eta=0.2, delta_phi=0.1)  # NOTE: No v2: delta_phi=0.1 float. No v1: delta_phi=pi/32 rad (TILE.py#L93).
        .electronics(noise_mev=35.0, pulse_file=_tile_pulse())  # NOTE: No v2: ruído=35.0 MeV. No v1: 20.0 MeV (TILE.py#L131).
        .build(),
    ]


def getGalticTileExtendedCfg(side_a: bool = True) -> List[CaloSamplingLayer]:
    """Returns the 3 sampling layers of TileCal Extended Barrel for Side A or Side B in v2 configuration."""
    # -------------------------------------------------------------------------
    # TileCal Extended Barrel (TileExt1, TileExt2, TileExt3)
    # -------------------------------------------------------------------------
    # NOTE: Configuração v2 com delta_phi=0.1 float e progressão de ruído 25, 30 e 35 MeV.
    # - No v2: ZSize=2830.0 mm, ZCenter=+-5119.0 mm, delta_phi=0.1, ruídos 25, 30 e 35 MeV.
    # - No v1: delta_phi=pi/32 rad, ruído=20.0 MeV constante para todos (TILE.py#L218-L257).
    z_center = 5119.0 if side_a else -5119.0
    side_tag = "A" if side_a else "B"
    return [
        TileCalBuilder(f"TILE::TileCalExt1::{side_tag}", CaloSampling.TileExt1)
        .radii(2283.0, 2683.0)
        .length_and_center(z_size=2830.0, z_center=z_center)
        .granularity(delta_eta=0.1, delta_phi=0.1)  # NOTE: No v2: delta_phi=0.1 float. No v1: delta_phi=pi/32 rad (TILE.py#L218).
        .electronics(noise_mev=25.0, pulse_file=_tile_pulse())  # NOTE: No v2: ruído=25.0 MeV. No v1: 20.0 MeV (TILE.py#L229).
        .build(),

        TileCalBuilder(f"TILE::TileCalExt2::{side_tag}", CaloSampling.TileExt2)
        .radii(2683.0, 3783.0)
        .length_and_center(z_size=2830.0, z_center=z_center)
        .granularity(delta_eta=0.1, delta_phi=0.1)  # NOTE: No v2: delta_phi=0.1 float. No v1: delta_phi=pi/32 rad (TILE.py#L219).
        .electronics(noise_mev=30.0, pulse_file=_tile_pulse())  # NOTE: No v2: ruído=30.0 MeV. No v1: 20.0 MeV (TILE.py#L243).
        .build(),

        TileCalBuilder(f"TILE::TileCalExt3::{side_tag}", CaloSampling.TileExt3)
        .radii(3783.0, 4283.0)
        .length_and_center(z_size=2830.0, z_center=z_center)
        .granularity(delta_eta=0.2, delta_phi=0.1)  # NOTE: No v2: delta_phi=0.1 float. No v1: delta_phi=pi/32 rad (TILE.py#L220).
        .electronics(noise_mev=35.0, pulse_file=_tile_pulse())  # NOTE: No v2: ruído=35.0 MeV. No v1: 20.0 MeV (TILE.py#L257).
        .build(),
    ]


def getGalticLArEMECCfg(side_a: bool = True) -> List[CaloSamplingLayer]:
    """Returns the active sampling layers of LAr EMEC for Side A or Side B in v2 configuration."""
    # -------------------------------------------------------------------------
    # LAr EMEC (PSE, EMEC1, EMEC2, EMEC3)
    # -------------------------------------------------------------------------
    # NOTE: Configuração v2 com multi-segmentação colapsada em 1 segmento por amostragem.
    # - No v2: PSE noise=90 MeV; EMEC1 deta=0.025, noise=35 MeV; EMEC2 noise=45 MeV; EMEC3 noise=25 MeV.
    # - No v1: PSE noise=26 MeV; EMEC1 possui 4 segmentos, noise=26 MeV; EMEC2 possui 2 segmentos, noise=60 MeV; EMEC3 possui 2 segmentos, noise=40 MeV (EMEC.py#L30-L235).
    return [
        LArEMECBuilder("LAr::PSE", CaloSampling.PSE, side_a=side_a)
        .geometry(rmin=1232.0, rmax=1700.0, z_size=5.0, z_center=3737.5)
        .granularity(delta_eta=0.025, delta_phi=np.pi / 32.0)
        .electronics(noise_mev=90.0, pulse_file=_lar_pulse())  # NOTE: No v2: ruído=90.0 MeV. No v1: 26.0 MeV (EMEC.py#L56).
        .build(),

        LArEMECBuilder("LAr::EMEC1", CaloSampling.EMEC1, side_a=side_a)
        .geometry(rmin=302.0, rmax=2042.0, z_size=96.0, z_center=3788.0)
        .granularity(delta_eta=0.025, delta_phi=np.pi / 32.0)  # NOTE: No v2: 1 segmento colapsado deta=0.025. No v1: 4 segmentos em eta (EMEC.py#L88).
        .electronics(noise_mev=35.0, pulse_file=_lar_pulse())  # NOTE: No v2: ruído=35.0 MeV. No v1: 26.0 MeV (EMEC.py#L96).
        .build(),

        LArEMECBuilder("LAr::EMEC2", CaloSampling.EMEC2, side_a=side_a)
        .geometry(rmin=302.0, rmax=2042.0, z_size=330.0, z_center=4001.0)
        .granularity(delta_eta=0.025, delta_phi=np.pi / 128.0)  # NOTE: No v2: 1 segmento colapsado. No v1: 2 segmentos (EMEC.py#L149-L150).
        .electronics(noise_mev=45.0, pulse_file=_lar_pulse())  # NOTE: No v2: ruído=45.0 MeV. No v1: 60.0 MeV (EMEC.py#L158).
        .build(),

        LArEMECBuilder("LAr::EMEC3", CaloSampling.EMEC3, side_a=side_a)
        .geometry(rmin=302.0, rmax=2042.0, z_size=54.0, z_center=4193.0)
        .granularity(delta_eta=0.05, delta_phi=np.pi / 128.0)  # NOTE: No v2: 1 segmento colapsado. No v1: 2 segmentos (EMEC.py#L196-L197).
        .electronics(noise_mev=25.0, pulse_file=_lar_pulse())  # NOTE: No v2: ruído=25.0 MeV. No v1: 40.0 MeV (EMEC.py#L205).
        .build(),
    ]


def getGalticHECCfg(side_a: bool = True) -> List[CaloSamplingLayer]:
    """Returns the 3 longitudinal sampling layers of HEC for Side A or Side B in v2 configuration."""
    # -------------------------------------------------------------------------
    # HEC (Hadronic Endcap Calorimeter: HEC1, HEC2, HEC3)
    # -------------------------------------------------------------------------
    # NOTE: Configuração v2 com pulso pulseTile.dat, ruídos 80/100/120 MeV e delta_phi=0.1 float.
    # - No v2: pulse_file=_tile_pulse(), delta_phi=0.1, ruídos 80, 100 e 120 MeV.
    # - No v1: pulse_file=_lar_pulse(), delta_phi=pi/32 e pi/16, ruídos 250 e 400 MeV (HEC.py#L30-L175).
    return [
        HECBuilder("FCal::HEC1", CaloSampling.HEC1, side_a=side_a)
        .geometry(rmin=372.0, rmax=2030.0, z_size=189.0, z_center=4356.5)
        .granularity(delta_eta=0.1, delta_phi=0.1)  # NOTE: No v2: delta_phi=0.1 float. No v1: Seg 0 pi/32, Seg 1 pi/16 (HEC.py#L46-L47).
        .electronics(noise_mev=80.0, pulse_file=_tile_pulse())  # NOTE: No v2: pulseTile.dat e ruído=80.0 MeV. No v1: pulseLar.dat e ruído=250.0 MeV (HEC.py#L52-L53).
        .build(),

        HECBuilder("FCal::HEC2", CaloSampling.HEC2, side_a=side_a)
        .geometry(rmin=475.0, rmax=2030.0, z_size=336.0, z_center=4619.0)  # NOTE: No v2: z_center=4619.0 mm. No v1: 4808.0 mm (HEC.py#L104).
        .granularity(delta_eta=0.1, delta_phi=0.1)  # NOTE: No v2: delta_phi=0.1 float. No v1: Seg 0 pi/32, Seg 1 pi/16.
        .electronics(noise_mev=100.0, pulse_file=_tile_pulse())  # NOTE: No v2: pulseTile.dat e ruído=100.0 MeV. No v1: pulseLar.dat e ruído=400.0 MeV (HEC.py#L111-L112).
        .build(),

        HECBuilder("FCal::HEC3", CaloSampling.HEC3, side_a=side_a)
        .geometry(rmin=475.0, rmax=2030.0, z_size=936.0, z_center=5255.0)  # NOTE: No v2: z_center=5255.0 mm. No v1: 5444.0 mm (HEC.py#L157).
        .granularity(delta_eta=0.2, delta_phi=0.1)  # NOTE: No v2: delta_phi=0.1 float. No v1: Seg 0 pi/32, Seg 1 pi/16.
        .electronics(noise_mev=120.0, pulse_file=_tile_pulse())  # NOTE: No v2: pulseTile.dat e ruído=120.0 MeV. No v1: pulseLar.dat e ruído=250.0 MeV (HEC.py#L163-L164).
        .build(),
    ]


def getGalticDeadMaterialsCfg() -> List[DeadMaterialVolume]:
    """Returns all passive dead material volumes in v2 configuration (cryostats and crack supports)."""
    # -------------------------------------------------------------------------
    # Dead Materials (Matéria Morta)
    # -------------------------------------------------------------------------
    # NOTE: Configuração v2 com volumes de criostato (Inner1, Inner2, Outer) e suportes de crack.
    # - No v2: DM::Cryo::Inner1, DM::Cryo::Inner2, DM::Cryo::Outer, DM::Crack::EM (gap=Vacuum), DM::Crack::TILE (plates=Vertical, G4_Fe).
    # - No v1: DM::PS::Boundary, DM::LAr::Boundary, DM::TILE::Boundary, DM::Crack::EM (gap=liquidArgon), DM::Crack::TILE (plates=Horizontal, G4_Al) (DeadMaterials.py#L20-L130).
    return [
        DeadMaterialBuilder("DM::Cryo::Inner1")
        .geometry(rmin=1200.0, rmax=1250.0, z_size=6800.0)  # NOTE: No v2: volume artificial adicionado. No v1: inexistente.
        .materials(absorber="G4_Al", gap="Vacuum")
        .build(),

        DeadMaterialBuilder("DM::Cryo::Inner2")
        .geometry(rmin=1440.0, rmax=1455.0, z_size=6800.0)  # NOTE: No v2: renomeado de DM::PS::Boundary e encurtado para 1440-1455 mm. No v1: DM::PS::Boundary (1380-1460 mm) (DeadMaterials.py#L59-L72).
        .materials(absorber="G4_Al", gap="Vacuum")
        .build(),

        DeadMaterialBuilder("DM::Cryo::Outer")
        .geometry(rmin=1980.0, rmax=2083.0, z_size=6800.0)  # NOTE: No v2: renomeado de DM::LAr::Boundary. No v1: DM::LAr::Boundary (DeadMaterials.py#L76-L89).
        .materials(absorber="G4_Al", gap="Vacuum")
        .build(),

        DeadMaterialBuilder("DM::Crack::EM::A")
        .geometry(rmin=900.0, rmax=2232.0, z_size=300.0, center=(0.0, 0.0, 3567.5))
        .materials(absorber="G4_Al", gap="Vacuum", plates=Plates.Vertical)  # NOTE: No v2: gap="Vacuum". No v1: gap="liquidArgon" (DeadMaterials.py#L25).
        .build(),

        DeadMaterialBuilder("DM::Crack::EM::B")
        .geometry(rmin=900.0, rmax=2232.0, z_size=300.0, center=(0.0, 0.0, -3567.5))
        .materials(absorber="G4_Al", gap="Vacuum", plates=Plates.Vertical)  # NOTE: No v2: gap="Vacuum". No v1: gap="liquidArgon" (DeadMaterials.py#L25).
        .build(),

        DeadMaterialBuilder("DM::Crack::TILE::A")
        .geometry(rmin=2283.0, rmax=4284.0, z_size=680.0, center=(0.0, 0.0, 3364.0))
        .materials(absorber="G4_Fe", gap="Vacuum", plates=Plates.Vertical)  # NOTE: No v2: plates=Plates.Vertical, abso="G4_Fe". No v1: plates=Plates.Horizontal, abso="G4_Al" (DeadMaterials.py#L38-L39).
        .build(),

        DeadMaterialBuilder("DM::Crack::TILE::B")
        .geometry(rmin=2283.0, rmax=4284.0, z_size=680.0, center=(0.0, 0.0, -3364.0))
        .materials(absorber="G4_Fe", gap="Vacuum", plates=Plates.Vertical)  # NOTE: No v2: plates=Plates.Vertical, abso="G4_Fe". No v1: plates=Plates.Horizontal, abso="G4_Al" (DeadMaterials.py#L38-L39).
        .build(),
    ]


def getGalticAllSamplings() -> List[CaloSamplingLayer]:
    """Returns the full list of active calorimeter sampling layers for GALTIC (v2)."""
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
    """Returns all passive dead material volumes for GALTIC (v2)."""
    return getGalticDeadMaterialsCfg()
