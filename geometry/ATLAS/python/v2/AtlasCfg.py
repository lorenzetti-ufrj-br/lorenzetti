"""
AtlasCfg.py - Canonical configuration of all 24 ATLAS calorimeter samplings and dead materials for v2.

NOTE on geometry comparison (v1 vs v2):
- v1 detectors are defined in `geometry/ATLAS/python/v1/detectors/` (ECAL.py, EMEC.py, HEC.py, TILE.py, FCAL.py, DeadMaterials.py).
- v2 centralizes all definitions into this file and exports them to JSON (`geometry/ATLAS/data/atlas_geometry.json`).
"""

from typing import List
import numpy as np
from CaloCell.CaloDefs import CaloSampling
from ATLAS.v2.Layer import (
    CaloSamplingLayer,
    DeadMaterialVolume,
    AtlasEmbBuilder,
    AtlasTileBuilder,
    AtlasEmecBuilder,
    AtlasHecBuilder,
    AtlasFcalBuilder,
    AtlasDeadMaterialBuilder,
)

__all__ = ["getAtlasAllSamplings", "getAtlasAllDeadMaterials"]


def getAtlasAllSamplings() -> List[CaloSamplingLayer]:
    """Retorna a lista canônica das camadas de amostragem ativas do calorímetro ATLAS."""
    samplings: List[CaloSamplingLayer] = []

    # =========================================================================
    # 1. Presampler Barril (PSB)
    # NOTE: v1 em `geometry/ATLAS/python/v1/detectors/ECAL.py#L46-L60`:
    #   PhysicalVolume LAr::PSB: RMin=1460 mm, RMax=1471.01 mm, ZSize=6800 mm,
    #   AbsorberMaterial="Vacuum" (0.01 mm), Gap="liquidArgon" (11.0 mm), NofLayers=1.
    #   No v2: RMin=1430 mm, RMax=1441 mm, ZLength=6330 mm.
    # =========================================================================
    samplings.append(
        AtlasEmbBuilder("LAr::PSB", CaloSampling.PSB)
        .radii(1430.0, 1441.0)
        .z_length(6330.0)
        .accordion(lead_th=0.01, lar_gap=11.0, n_layers=1)
        .granularity(d_eta=0.025, d_phi=np.pi / 32.0)
        .electronics(noise_mev=90.0, pulse_file="pulseLar.dat")
        .build()
    )

    # =========================================================================
    # 2. Barril Eletromagnético (EMB1, EMB2, EMB3)
    # NOTE: v1 em `geometry/ATLAS/python/v1/detectors/ECAL.py#L62-L105`:
    #   EMB1: RMin=1500 mm, RMax=1596 mm, lead=1.51 mm, gap=4.49 mm, N=16, d_eta=0.003125, d_phi=0.02454, noise=40 MeV.
    #   EMB2: RMin=1596 mm, RMax=1926 mm, lead=1.70 mm, gap=4.30 mm, N=55, d_eta=0.025, d_phi=0.02454, noise=30 MeV.
    #   EMB3: RMin=1926 mm, RMax=1980 mm, lead=1.70 mm, gap=4.30 mm, N=9, d_eta=0.05, d_phi=0.02454, noise=25 MeV.
    #   Limites contíguos sem overlap: 1500 -> 1596 -> 1926 -> 1980 mm.
    # =========================================================================
    samplings.append(
        AtlasEmbBuilder("LAr::EMB1", CaloSampling.EMB1)
        .radii(1500.0, 1596.0)
        .z_length(6330.0)
        .accordion(lead_th=1.51, lar_gap=4.49, n_layers=16)
        .granularity(d_eta=0.003125, d_phi=0.02454)  # Tiras finas
        .electronics(noise_mev=40.0, pulse_file="pulseLar.dat")
        .build()
    )
    samplings.append(
        AtlasEmbBuilder("LAr::EMB2", CaloSampling.EMB2)
        .radii(1596.0, 1926.0)
        .z_length(6330.0)
        .accordion(lead_th=1.70, lar_gap=4.30, n_layers=55)
        .granularity(d_eta=0.025, d_phi=0.02454)
        .electronics(noise_mev=30.0, pulse_file="pulseLar.dat")
        .build()
    )
    samplings.append(
        AtlasEmbBuilder("LAr::EMB3", CaloSampling.EMB3)
        .radii(1926.0, 1980.0)
        .z_length(6330.0)
        .accordion(lead_th=1.70, lar_gap=4.30, n_layers=9)
        .granularity(d_eta=0.05, d_phi=0.02454)
        .electronics(noise_mev=25.0, pulse_file="pulseLar.dat")
        .build()
    )

    # =========================================================================
    # 3. Calorímetro de Telhas Barril (TileBar0, TileBar1, TileBar2)
    # NOTE: v1 em `geometry/ATLAS/python/v1/detectors/TILE.py#L35-L55`:
    #   Tile Barrel se estende por |Z| <= 2820 mm com 3 camadas radiais (A, BC, D).
    #   No v2: TileBar0 (2280-2600 mm), TileBar1 (2600-3140 mm), TileBar2 (3140-3820 mm).
    # =========================================================================
    samplings.append(
        AtlasTileBuilder("Tile::Bar0", CaloSampling.TileCal1)
        .radii(2280.0, 2600.0)
        .z_span(-2820.0, 2820.0)
        .cells(d_eta=0.1, d_phi=0.1)
        .electronics(noise_mev=30.0, pulse_file="pulseTile.dat")
        .build()
    )
    samplings.append(
        AtlasTileBuilder("Tile::Bar1", CaloSampling.TileCal2)
        .radii(2600.0, 3140.0)
        .z_span(-2820.0, 2820.0)
        .cells(d_eta=0.1, d_phi=0.1)
        .electronics(noise_mev=30.0, pulse_file="pulseTile.dat")
        .build()
    )
    samplings.append(
        AtlasTileBuilder("Tile::Bar2", CaloSampling.TileCal3)
        .radii(3140.0, 3820.0)
        .z_span(-2820.0, 2820.0)
        .cells(d_eta=0.2, d_phi=0.1)
        .electronics(noise_mev=35.0, pulse_file="pulseTile.dat")
        .build()
    )

    # =========================================================================
    # 4. Calorímetro de Telhas Estendido (TileExt0, TileExt1, TileExt2) - Lados A e B
    # NOTE: v1 em `geometry/ATLAS/python/v1/detectors/TILE.py#L35-L36`:
    #   TILE_ATLAS_EXTENDED_Z_START = 3554 mm, TILE_ATLAS_EXTENDED_Z_END = 6110 mm.
    #   No v2: Z entre 3530 mm e 6170 mm.
    # =========================================================================
    for side, sign, suffix in [("A", 1.0, "::A"), ("B", -1.0, "::B")]:
        z_start = sign * 3530.0
        z_end = sign * 6170.0
        zmin = min(z_start, z_end)
        zmax = max(z_start, z_end)

        samplings.append(
            AtlasTileBuilder("Tile::Ext0" + suffix, CaloSampling.TileExt1)
            .radii(2280.0, 2600.0)
            .z_span(zmin, zmax)
            .cells(d_eta=0.1, d_phi=0.1)
            .electronics(noise_mev=30.0, pulse_file="pulseTile.dat")
            .build()
        )
        samplings.append(
            AtlasTileBuilder("Tile::Ext1" + suffix, CaloSampling.TileExt2)
            .radii(2600.0, 3140.0)
            .z_span(zmin, zmax)
            .cells(d_eta=0.1, d_phi=0.1)
            .electronics(noise_mev=30.0, pulse_file="pulseTile.dat")
            .build()
        )
        samplings.append(
            AtlasTileBuilder("Tile::Ext2" + suffix, CaloSampling.TileExt3)
            .radii(3140.0, 3820.0)
            .z_span(zmin, zmax)
            .cells(d_eta=0.2, d_phi=0.1)
            .electronics(noise_mev=35.0, pulse_file="pulseTile.dat")
            .build()
        )

    # =========================================================================
    # 5. Presampler Endcap (PSE) e Endcap Eletromagnético (EMEC1, EMEC2, EMEC3) - Lados A e B
    # NOTE: v1 em `geometry/ATLAS/python/v1/detectors/EMEC.py`:
    #   - PSE (L44-L75): RMin=1232 mm, RMax=1700 mm, Z=[3735, 3740] mm (ZSize=5 mm),
    #     Vacuum=0.01 mm, LAr=4.99 mm, N=1, d_eta=0.025, d_phi=pi/32, noise=26 MeV.
    #     No v2 inicial: PSE havia sido omitido. Aqui adicionamos PSE::A e PSE::B.
    #   - EMEC1 (L84-L149): RMin=302 mm, RMax=2042 mm, Z=[3740, 3836] mm (ZSize=96 mm),
    #     Pb=2.27 mm, LAr=3.73 mm, N=16.
    #     Segmentação em eta (4 segmentos):
    #       Seg 0: |eta| < 1.80, d_eta=0.00325, d_phi=pi/32
    #       Seg 1: 1.80 <= |eta| < 2.00, d_eta=0.025, d_phi=pi/32
    #       Seg 2: 2.00 <= |eta| < 2.37, d_eta=0.006, d_phi=pi/32
    #       Seg 3: 2.37 <= |eta| < 3.20, d_eta=0.100, d_phi=pi/32
    #   - EMEC2 (L154-L197): RMin=302 mm, RMax=2042 mm, Z=[3836, 4166] mm (ZSize=330 mm),
    #     Pb=2.27 mm, LAr=3.73 mm, N=55.
    #     Segmentação em eta (2 segmentos):
    #       Seg 0: |eta| < 2.50, d_eta=0.025, d_phi=pi/128
    #       Seg 1: 2.50 <= |eta| < 3.20, d_eta=0.100, d_phi=pi/32
    #   - EMEC3 (L204-L245): RMin=302 mm, RMax=2042 mm, Z=[4166, 4220] mm (ZSize=54 mm),
    #     Pb=2.41 mm, LAr=3.59 mm, N=9.
    #     Segmentação em eta (2 segmentos):
    #       Seg 0: |eta| < 2.50, d_eta=0.050, d_phi=pi/128
    #       Seg 1: 2.50 <= |eta| < 3.20, d_eta=0.100, d_phi=pi/32
    #
    #   No v2 inicial: EMEC1, EMEC2 e EMEC3 compartilhavam o mesmo z_span(3680, 4320) mm,
    #   gerando sobreposição (volume encapsulation) no Geant4.
    #   Aqui corrigimos os limites contíguos Z e configuramos os readout segments canônicos.
    # =========================================================================
    for side, sign, suffix in [("A", 1.0, "::A"), ("B", -1.0, "::B")]:
        # Presampler Endcap (PSE)
        z_pse_min = min(sign * 3735.0, sign * 3740.0)
        z_pse_max = max(sign * 3735.0, sign * 3740.0)
        samplings.append(
            AtlasEmecBuilder("LAr::PSE" + suffix, CaloSampling.PSE)
            .radii(1232.0, 1700.0)
            .z_span(z_pse_min, z_pse_max)
            .materials(absorber="Vacuum", gap="liquidArgon")
            .layers_and_absorber(n_layers=1, lead_th=0.01, lar_gap=4.99)
            .granularity(d_eta=0.025, d_phi=np.pi / 32.0)
            .electronics(noise_mev=26.0, pulse_file="pulseLar.dat")
            .build()
        )

        # EMEC1
        z_emec1_min = min(sign * 3740.0, sign * 3836.0)
        z_emec1_max = max(sign * 3740.0, sign * 3836.0)
        samplings.append(
            AtlasEmecBuilder("LAr::EMEC1" + suffix, CaloSampling.EMEC1)
            .radii(302.0, 2042.0)
            .z_span(z_emec1_min, z_emec1_max)
            .layers_and_absorber(n_layers=16, lead_th=2.27, lar_gap=3.73)
            .granularity(d_eta=0.00325, d_phi=np.pi / 32.0)
            .electronics(noise_mev=26.0, pulse_file="pulseLar.dat")
            .add_segment(segment=0, delta_eta=0.00325, delta_phi=np.pi / 32.0, eta_min=None, eta_max=1.80)
            .add_segment(segment=1, delta_eta=0.025, delta_phi=np.pi / 32.0, eta_min=1.80, eta_max=2.00)
            .add_segment(segment=2, delta_eta=0.006, delta_phi=np.pi / 32.0, eta_min=2.00, eta_max=2.37)
            .add_segment(segment=3, delta_eta=0.100, delta_phi=np.pi / 32.0, eta_min=2.37, eta_max=3.20)
            .build()
        )

        # EMEC2
        z_emec2_min = min(sign * 3836.0, sign * 4166.0)
        z_emec2_max = max(sign * 3836.0, sign * 4166.0)
        samplings.append(
            AtlasEmecBuilder("LAr::EMEC2" + suffix, CaloSampling.EMEC2)
            .radii(302.0, 2042.0)
            .z_span(z_emec2_min, z_emec2_max)
            .layers_and_absorber(n_layers=55, lead_th=2.27, lar_gap=3.73)
            .granularity(d_eta=0.025, d_phi=np.pi / 128.0)
            .electronics(noise_mev=60.0, pulse_file="pulseLar.dat")
            .add_segment(segment=0, delta_eta=0.025, delta_phi=np.pi / 128.0, eta_min=None, eta_max=2.50)
            .add_segment(segment=1, delta_eta=0.100, delta_phi=np.pi / 32.0, eta_min=2.50, eta_max=3.20)
            .build()
        )

        # EMEC3
        z_emec3_min = min(sign * 4166.0, sign * 4220.0)
        z_emec3_max = max(sign * 4166.0, sign * 4220.0)
        samplings.append(
            AtlasEmecBuilder("LAr::EMEC3" + suffix, CaloSampling.EMEC3)
            .radii(302.0, 2042.0)
            .z_span(z_emec3_min, z_emec3_max)
            .layers_and_absorber(n_layers=9, lead_th=2.41, lar_gap=3.59)
            .granularity(d_eta=0.050, d_phi=np.pi / 128.0)
            .electronics(noise_mev=40.0, pulse_file="pulseLar.dat")
            .add_segment(segment=0, delta_eta=0.050, delta_phi=np.pi / 128.0, eta_min=None, eta_max=2.50)
            .add_segment(segment=1, delta_eta=0.100, delta_phi=np.pi / 32.0, eta_min=2.50, eta_max=3.20)
            .build()
        )

    # =========================================================================
    # 6. Calorímetro Hadrônico de Tampão (HEC0, HEC1, HEC2, HEC3) - Lados A e B
    # NOTE: v1 em `geometry/ATLAS/python/v1/detectors/HEC.py#L240-L320`:
    #   HEC_ATLAS_Z_START = 4277.0 mm, WHEEL_GAP = 40.5 mm, R_OUTER = 2030 mm, LAR_GAP = 8.5 mm.
    #   - HEC0: Z=[4277.0, 4557.5] mm (depth 280.5 mm), 8 gaps, Cu 25 mm, RMin=372 mm (em frente ao FCAL).
    #   - HEC1: Z=[4557.5, 5093.5] mm (depth 536.0 mm), 16 gaps, Cu 25 mm, RMin=475 mm (para abrigar FCAL RMax=450 mm).
    #   - Wheel gap: 5093.5 -> 5134.0 mm (+40.5 mm)
    #   - HEC2: Z=[5134.0, 5627.0] mm (depth 493.0 mm), 8 gaps, Cu 50 mm, RMin=475 mm (para abrigar FCAL RMax=450 mm).
    #   - HEC3: Z=[5627.0, 6095.0] mm (depth 468.0 mm), 8 gaps, Cu 50 mm, RMin=475 mm (para abrigar FCAL RMax=450 mm).
    #   Segmentação canônica em eta do HEC (2 segmentos):
    #     Seg 0: |eta| < 2.50, DeltaEta=0.1, DeltaPhi=pi/32
    #     Seg 1: 2.50 <= |eta| < 3.30, DeltaEta=0.2, DeltaPhi=pi/16
    # =========================================================================
    for side, sign, suffix in [("A", 1.0, "::A"), ("B", -1.0, "::B")]:
        z_hec0_min = min(sign * 4277.0, sign * 4557.5)
        z_hec0_max = max(sign * 4277.0, sign * 4557.5)

        z_hec1_min = min(sign * 4557.5, sign * 5093.5)
        z_hec1_max = max(sign * 4557.5, sign * 5093.5)

        z_hec2_min = min(sign * 5134.0, sign * 5627.0)
        z_hec2_max = max(sign * 5134.0, sign * 5627.0)

        z_hec3_min = min(sign * 5627.0, sign * 6095.0)
        z_hec3_max = max(sign * 5627.0, sign * 6095.0)

        samplings.append(
            AtlasHecBuilder("LAr::HEC0" + suffix, CaloSampling.HEC0)
            .radii(372.0, 2030.0)
            .z_span(z_hec0_min, z_hec0_max)
            .copper_plates(copper_th=25.0, lar_gap=8.5, n_layers=8)
            .granularity(d_eta=0.1, d_phi=np.pi / 32.0)
            .electronics(noise_mev=250.0, pulse_file="pulseLar.dat")
            .add_segment(segment=0, delta_eta=0.1, delta_phi=np.pi / 32.0, eta_min=None, eta_max=2.50)
            .add_segment(segment=1, delta_eta=0.2, delta_phi=np.pi / 16.0, eta_min=2.50, eta_max=3.30)
            .build()
        )
        samplings.append(
            AtlasHecBuilder("LAr::HEC1" + suffix, CaloSampling.HEC1)
            .radii(475.0, 2030.0)
            .z_span(z_hec1_min, z_hec1_max)
            .copper_plates(copper_th=25.0, lar_gap=8.5, n_layers=16)
            .granularity(d_eta=0.1, d_phi=np.pi / 32.0)
            .electronics(noise_mev=250.0, pulse_file="pulseLar.dat")
            .add_segment(segment=0, delta_eta=0.1, delta_phi=np.pi / 32.0, eta_min=None, eta_max=2.50)
            .add_segment(segment=1, delta_eta=0.2, delta_phi=np.pi / 16.0, eta_min=2.50, eta_max=3.30)
            .build()
        )
        samplings.append(
            AtlasHecBuilder("LAr::HEC2" + suffix, CaloSampling.HEC2)
            .radii(475.0, 2030.0)
            .z_span(z_hec2_min, z_hec2_max)
            .copper_plates(copper_th=50.0, lar_gap=8.5, n_layers=8)
            .granularity(d_eta=0.1, d_phi=np.pi / 32.0)
            .electronics(noise_mev=250.0, pulse_file="pulseLar.dat")
            .add_segment(segment=0, delta_eta=0.1, delta_phi=np.pi / 32.0, eta_min=None, eta_max=2.50)
            .add_segment(segment=1, delta_eta=0.2, delta_phi=np.pi / 16.0, eta_min=2.50, eta_max=3.30)
            .build()
        )
        samplings.append(
            AtlasHecBuilder("LAr::HEC3" + suffix, CaloSampling.HEC3)
            .radii(475.0, 2030.0)
            .z_span(z_hec3_min, z_hec3_max)
            .copper_plates(copper_th=50.0, lar_gap=8.5, n_layers=8)
            .granularity(d_eta=0.2, d_phi=np.pi / 16.0)
            .electronics(noise_mev=250.0, pulse_file="pulseLar.dat")
            .add_segment(segment=0, delta_eta=0.1, delta_phi=np.pi / 32.0, eta_min=None, eta_max=2.50)
            .add_segment(segment=1, delta_eta=0.2, delta_phi=np.pi / 16.0, eta_min=2.50, eta_max=3.30)
            .build()
        )

    # =========================================================================
    # 7. Calorímetro Para Frente (FCAL1, FCAL2, FCAL3) - Lados A e B
    # NOTE: v1 em `geometry/ATLAS/python/v1/detectors/FCAL.py`:
    #   FCAL1 (cobre), FCAL2 (tungstênio), FCAL3 (tungstênio).
    #   No v2: camadas cilíndricas com material e gap equivalentes:
    #   FCAL1: [4668, 5118] mm, G4_Cu
    #   FCAL2: [5128, 5578] mm, G4_W
    #   FCAL3: [5588, 6038] mm, G4_W
    # =========================================================================
    for side, sign, suffix in [("A", 1.0, "::A"), ("B", -1.0, "::B")]:
        zmin1 = min(sign * 4668.0, sign * 5118.0)
        zmax1 = max(sign * 4668.0, sign * 5118.0)
        zmin2 = min(sign * 5128.0, sign * 5578.0)
        zmax2 = max(sign * 5128.0, sign * 5578.0)
        zmin3 = min(sign * 5588.0, sign * 6038.0)
        zmax3 = max(sign * 5588.0, sign * 6038.0)

        samplings.append(
            AtlasFcalBuilder("LAr::FCAL1" + suffix, CaloSampling.FCAL1)
            .radii(72.0, 450.0)
            .z_span(zmin1, zmax1)
            .material_and_gap(absorber_mat="G4_Cu", abso_th=20.0, lar_gap=1.0, n_layers=15)
            .granularity(d_eta=0.2, d_phi=0.2)
            .electronics(noise_mev=80.0, pulse_file="pulseLar.dat")
            .build()
        )
        samplings.append(
            AtlasFcalBuilder("LAr::FCAL2" + suffix, CaloSampling.FCAL2)
            .radii(72.0, 450.0)
            .z_span(zmin2, zmax2)
            .material_and_gap(absorber_mat="G4_W", abso_th=20.0, lar_gap=1.0, n_layers=15)
            .granularity(d_eta=0.2, d_phi=0.2)
            .electronics(noise_mev=90.0, pulse_file="pulseLar.dat")
            .build()
        )
        samplings.append(
            AtlasFcalBuilder("LAr::FCAL3" + suffix, CaloSampling.FCAL3)
            .radii(72.0, 450.0)
            .z_span(zmin3, zmax3)
            .material_and_gap(absorber_mat="G4_W", abso_th=20.0, lar_gap=1.0, n_layers=15)
            .granularity(d_eta=0.2, d_phi=0.2)
            .electronics(noise_mev=100.0, pulse_file="pulseLar.dat")
            .build()
        )

    return samplings


def getAtlasAllDeadMaterials() -> List[DeadMaterialVolume]:
    """Retorna a lista canônica de materiais passivos (solenoide, criostatos, blindagens e gaps) do ATLAS.

    NOTE: v1 em `geometry/ATLAS/python/v1/detectors/DeadMaterials.py#L20-L130`:
      - DM::Solenoid: Polycone central R=[1229, 1275] mm, |Z|<=2900 mm.
      - DM::Cryo::Barrel::InnerWarm: R=[1250, 1260] mm.
      - DM::Cryo::Barrel::InnerCold: R=[1400, 1413] mm.
      - DM::Cryo::Barrel::Outer: R=[2150, 2180] mm.
      - DM::Crack::EM e DM::Crack::TILE: regiões de transição entre barril e endcap.
    """
    dead_materials: List[DeadMaterialVolume] = []

    # 1. Solenoide Central do ATLAS (Polycone fora do furo central de campo)
    # NOTE: v1 em `geometry/ATLAS/python/v1/detectors/AtlasBarrelFront.py#L60-L64` e `DeadMaterials.py#L534-L543`:
    #   O solenoide fica em R=[1229, 1275.35] mm, fora do volume de campo central (R < 1228 mm).
    dead_materials.append(
        AtlasDeadMaterialBuilder("DM::Solenoid")
        .polycone(
            z_planes=[-2900.0, 2900.0],
            r_min=[1229.0, 1229.0],
            r_max=[1275.0, 1275.0],
            material="G4_Al",
            in_solenoid_field=False,
        )
        .build()
    )

    # 2. Parede Quente Interna do Criostato do Barril (Warm Inner Wall)
    # NOTE: v1 em `geometry/ATLAS/python/v1/detectors/AtlasBarrelFront.py#L57`:
    #   DM::Barrel::WarmInnerWall::Central: R=[1150, 1160] mm, |Z|<=2900 mm, in_field=True.
    dead_materials.append(
        AtlasDeadMaterialBuilder("DM::Cryo::Barrel::InnerWarm")
        .tubular(rmin=1150.0, rmax=1160.0, z_size=5800.0, material="G4_Al")
        .in_solenoid_field(True)
        .build()
    )

    # 3. Parede Fria Interna do Criostato do Barril
    dead_materials.append(
        AtlasDeadMaterialBuilder("DM::Cryo::Barrel::InnerCold")
        .tubular(rmin=1400.0, rmax=1413.0, z_size=6800.0, material="G4_Al")
        .build()
    )

    # 4. Vaso Externo do Criostato do Barril
    dead_materials.append(
        AtlasDeadMaterialBuilder("DM::Cryo::Barrel::Outer")
        .tubular(rmin=2150.0, rmax=2180.0, z_size=6800.0, material="G4_Al")
        .build()
    )

    # 5. Gaps e Regiões de Crack entre Barril e Endcaps
    for side, sign, suffix in [("A", 1.0, "::A"), ("B", -1.0, "::B")]:
        z_center_em = sign * 3422.5
        z_size_em = 515.0
        dead_materials.append(
            AtlasDeadMaterialBuilder("DM::Crack::EM" + suffix)
            .tubular(rmin=1440.0, rmax=2030.0, z_size=z_size_em, material="G4_Al", center=(0.0, 0.0, z_center_em))
            .build()
        )

        z_center_tile = sign * 3175.0
        z_size_tile = 710.0
        dead_materials.append(
            AtlasDeadMaterialBuilder("DM::Crack::TILE" + suffix)
            .tubular(rmin=2280.0, rmax=3820.0, z_size=z_size_tile, material="G4_Al", center=(0.0, 0.0, z_center_tile))
            .build()
        )

    return dead_materials
