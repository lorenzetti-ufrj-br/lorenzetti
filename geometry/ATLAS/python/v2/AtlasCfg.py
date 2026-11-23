"""
AtlasCfg.py - Canonical configuration of all 24 ATLAS calorimeter samplings and dead materials for v2.
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

    # 1. Presampler Barril (PSB)
    samplings.append(
        AtlasEmbBuilder("LAr::PSB", CaloSampling.PSB)
        .radii(1430.0, 1441.0)
        .z_length(6330.0)
        .accordion(lead_th=0.01, lar_gap=11.0, n_layers=1)
        .granularity(d_eta=0.025, d_phi=np.pi / 32.0)
        .electronics(noise_mev=90.0, pulse_file="pulseLar.dat")
        .build()
    )

    # 2. Barril Eletromagnético (EMB1, EMB2, EMB3)
    samplings.append(
        AtlasEmbBuilder("LAr::EMB1", CaloSampling.EMB1)
        .radii(1500.0, 1580.0)
        .z_length(6330.0)
        .accordion(lead_th=1.53, lar_gap=4.5, n_layers=16)
        .granularity(d_eta=0.003125, d_phi=0.02454)  # Tiras finas
        .electronics(noise_mev=40.0, pulse_file="pulseLar.dat")
        .build()
    )
    samplings.append(
        AtlasEmbBuilder("LAr::EMB2", CaloSampling.EMB2)
        .radii(1590.0, 1860.0)
        .z_length(6330.0)
        .accordion(lead_th=1.53, lar_gap=4.5, n_layers=16)
        .granularity(d_eta=0.025, d_phi=0.02454)
        .electronics(noise_mev=30.0, pulse_file="pulseLar.dat")
        .build()
    )
    samplings.append(
        AtlasEmbBuilder("LAr::EMB3", CaloSampling.EMB3)
        .radii(1870.0, 1960.0)
        .z_length(6330.0)
        .accordion(lead_th=1.13, lar_gap=4.5, n_layers=16)
        .granularity(d_eta=0.05, d_phi=0.02454)
        .electronics(noise_mev=25.0, pulse_file="pulseLar.dat")
        .build()
    )

    # 3. Calorímetro de Telhas Barril (TileBar0, TileBar1, TileBar2)
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

    # 4. Calorímetro de Telhas Estendido (TileExt0, TileExt1, TileExt2) - Lados A e B
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

    # 5. Endcap Eletromagnético (EMEC1, EMEC2, EMEC3) - Lados A e B
    for side, sign, suffix in [("A", 1.0, "::A"), ("B", -1.0, "::B")]:
        zmin = min(sign * 3680.0, sign * 4320.0)
        zmax = max(sign * 3680.0, sign * 4320.0)

        samplings.append(
            AtlasEmecBuilder("LAr::EMEC1" + suffix, CaloSampling.EMEC1)
            .radii(330.0, 2034.0)
            .z_span(zmin, zmax)
            .layers_and_absorber(n_layers=12, lead_th=1.7, lar_gap=2.0)
            .granularity(d_eta=0.025, d_phi=0.025)
            .electronics(noise_mev=45.0, pulse_file="pulseLar.dat")
            .build()
        )
        samplings.append(
            AtlasEmecBuilder("LAr::EMEC2" + suffix, CaloSampling.EMEC2)
            .radii(330.0, 2034.0)
            .z_span(zmin, zmax)
            .layers_and_absorber(n_layers=12, lead_th=1.7, lar_gap=2.0)
            .granularity(d_eta=0.025, d_phi=0.025)
            .electronics(noise_mev=35.0, pulse_file="pulseLar.dat")
            .build()
        )
        samplings.append(
            AtlasEmecBuilder("LAr::EMEC3" + suffix, CaloSampling.EMEC3)
            .radii(330.0, 2034.0)
            .z_span(zmin, zmax)
            .layers_and_absorber(n_layers=12, lead_th=1.7, lar_gap=2.0)
            .granularity(d_eta=0.05, d_phi=0.025)
            .electronics(noise_mev=30.0, pulse_file="pulseLar.dat")
            .build()
        )

    # 6. Calorímetro Hadrônico de Tampão (HEC0, HEC1, HEC2, HEC3) - Lados A e B
    for side, sign, suffix in [("A", 1.0, "::A"), ("B", -1.0, "::B")]:
        zmin1 = min(sign * 4277.0, sign * 4797.0)
        zmax1 = max(sign * 4277.0, sign * 4797.0)
        zmin2 = min(sign * 4797.0, sign * 6095.0)
        zmax2 = max(sign * 4797.0, sign * 6095.0)

        samplings.append(
            AtlasHecBuilder("LAr::HEC0" + suffix, CaloSampling.HEC0)
            .radii(372.0, 2030.0)
            .z_span(zmin1, zmax1)
            .copper_plates(copper_th=25.0, lar_gap=8.5, n_layers=8)
            .granularity(d_eta=0.1, d_phi=0.1)
            .electronics(noise_mev=50.0, pulse_file="pulseLar.dat")
            .build()
        )
        samplings.append(
            AtlasHecBuilder("LAr::HEC1" + suffix, CaloSampling.HEC1)
            .radii(372.0, 2030.0)
            .z_span(zmin1, zmax1)
            .copper_plates(copper_th=25.0, lar_gap=8.5, n_layers=8)
            .granularity(d_eta=0.1, d_phi=0.1)
            .electronics(noise_mev=45.0, pulse_file="pulseLar.dat")
            .build()
        )
        samplings.append(
            AtlasHecBuilder("LAr::HEC2" + suffix, CaloSampling.HEC2)
            .radii(372.0, 2030.0)
            .z_span(zmin2, zmax2)
            .copper_plates(copper_th=50.0, lar_gap=8.5, n_layers=8)
            .granularity(d_eta=0.1, d_phi=0.1)
            .electronics(noise_mev=55.0, pulse_file="pulseLar.dat")
            .build()
        )
        samplings.append(
            AtlasHecBuilder("LAr::HEC3" + suffix, CaloSampling.HEC3)
            .radii(372.0, 2030.0)
            .z_span(zmin2, zmax2)
            .copper_plates(copper_th=50.0, lar_gap=8.5, n_layers=8)
            .granularity(d_eta=0.2, d_phi=0.1)
            .electronics(noise_mev=60.0, pulse_file="pulseLar.dat")
            .build()
        )

    # 7. Calorímetro Para Frente (FCAL1, FCAL2, FCAL3) - Lados A e B
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
    """Retorna a lista canônica de materiais passivos (solenoide, criostatos, blindagens e gaps) do ATLAS."""
    dead_materials: List[DeadMaterialVolume] = []

    # 1. Solenoide Central do ATLAS (Polycone com campo de 2T)
    dead_materials.append(
        AtlasDeadMaterialBuilder("DM::Solenoid")
        .polycone(
            z_planes=[-2900.0, 2900.0],
            r_min=[1229.0, 1229.0],
            r_max=[1275.0, 1275.0],
            material="G4_Al",
            in_solenoid_field=True,
        )
        .build()
    )

    # 2. Parede Quente Interna do Criostato do Barril
    dead_materials.append(
        AtlasDeadMaterialBuilder("DM::Cryo::Barrel::InnerWarm")
        .tubular(rmin=1250.0, rmax=1260.0, z_size=6800.0, material="G4_Al")
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
