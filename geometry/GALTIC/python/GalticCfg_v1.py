"""
GalticCfg_v1.py - Canonical v1 configuration registry for all GALTIC subdetectors.

Faithfully implements the original parametric detector geometry from:
- v1 (a32691874ab042e7d8759f6f33141ac60b88e3da): geometry/python/v1
- v2 default (master branch with atlas flags disabled): geometry/python/v2
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
    """Returns the 4 active sampling layers of the central LAr Barrel (EMB) in v1 configuration."""
    return [
        # -------------------------------------------------------------------------
        # LAr::PSB (Presampler Barrel)
        # -------------------------------------------------------------------------
        # NOTE: PSB está CONFORME em dimensões, segmentação e ruído.
        # - No v1: RMin=1460.0 mm, RMax=1471.01 mm, ZSize=6800.0 mm, nof_layers=1, abso=0.01 mm, gap=11.0 mm,
        #   Noise=90 MeV, deta=0.025, dphi=pi/32, AbsorberMaterial="Vacuum".
        #   v1 link: https://github.com/lorenzetti-ufrj-br/lorenzetti/blob/a32691874ab042e7d8759f6f33141ac60b88e3da/geometry/python/v1/ECAL.py#L34-L47
        #   v1 SensitiveDetector: https://github.com/lorenzetti-ufrj-br/lorenzetti/blob/a32691874ab042e7d8759f6f33141ac60b88e3da/geometry/python/v1/ECAL.py#L97
        #   v1 Calorimeter (Electronics): https://github.com/lorenzetti-ufrj-br/lorenzetti/blob/a32691874ab042e7d8759f6f33141ac60b88e3da/geometry/python/v1/ECAL.py#L105-L114
        # - No v2 (master): Default (atlas_emb_cells=False) é idêntico ao v1:
        #   v2 default link: https://github.com/lorenzetti-ufrj-br/lorenzetti/blob/master/geometry/python/v2/ECAL.py#L48-L61
        #   No modo atlas_emb_cells=True, raios mudam para 1430-1441 mm e Z=3165 mm:
        #   v2 ATLAS mode link: https://github.com/lorenzetti-ufrj-br/lorenzetti/blob/master/geometry/python/v2/ECAL.py#L371-L385
        LArBarrelBuilder("LAr::PSB", CaloSampling.PSB)
        .radii(1460.0, 1471.01)  # NOTE: Conforme com v1 (ECAL.py#L43) e v2 default.
        .z_length(6800.0)  # NOTE: Conforme com v1 (ECAL.py#L44) e v2 default.
        .segmentation(nof_layers=1, absorber_th=0.01, gap_th=11.0)  # NOTE: Conforme com v1 (ECAL.py#L41-L42).
        .materials(absorber="Vacuum", gap="liquidArgon")  # NOTE: Antes: omitido (default "G4_Pb"). No v1: "Vacuum" (ECAL.py#L38). No v2: default "Vacuum" (v2:ECAL.py#L52).
        .granularity(delta_eta=0.025, delta_phi=np.pi / 32.0)  # NOTE: Conforme com v1 (ECAL.py#L97) e v2 default.
        .electronics(noise_mev=90.0, pulse_file=_lar_pulse())  # NOTE: Conforme com v1 (ECAL.py#L110) e v2 default.
        .build(),

        # -------------------------------------------------------------------------
        # LAr::EMB1 (Electromagnetic Barrel Layer 1 - Strips)
        # -------------------------------------------------------------------------
        # NOTE: DIVERGÊNCIA CORRIGIDA DEVIDO A CONTAMINAÇÃO CRUZADA com atlas_emb e atlas_emb_cells de v2.
        # - No v1: RMin=1500.0 mm, RMax=1596.0 mm (1500 + 16*(1.51 + 4.49)), nof_layers=16,
        #   absorber_th=1.51 mm de chumbo, gap_th=4.49 mm de LAr. Granularidade deta=0.00325, dphi=pi/32. Ruído=26 MeV.
        #   v1 link: https://github.com/lorenzetti-ufrj-br/lorenzetti/blob/a32691874ab042e7d8759f6f33141ac60b88e3da/geometry/python/v1/ECAL.py#L50-L63
        #   v1 SensitiveDetector: https://github.com/lorenzetti-ufrj-br/lorenzetti/blob/a32691874ab042e7d8759f6f33141ac60b88e3da/geometry/python/v1/ECAL.py#L98
        # - No v2 (master): Default é idêntico ao v1 (nof_layers=16, abso=1.51 mm, gap=4.49 mm, deta=0.00325):
        #   v2 default link: https://github.com/lorenzetti-ufrj-br/lorenzetti/blob/master/geometry/python/v2/ECAL.py#L64-L77
        #   No modo atlas_emb=True, usa período de 6.962 mm, 14 camadas e chumbo de 1.53 mm:
        #   v2 atlas_emb link: https://github.com/lorenzetti-ufrj-br/lorenzetti/blob/master/geometry/python/v2/ECAL.py#L118-L138
        #   No modo atlas_emb_cells=True, deta passa a 0.003125 em EMB_ATLAS_REGIONS:
        #   v2 EMB_ATLAS_REGIONS link: https://github.com/lorenzetti-ufrj-br/lorenzetti/blob/master/geometry/python/v2/ECAL.py#L233
        LArBarrelBuilder("LAr::EMB1", CaloSampling.EMB1)
        .radii(1500.0, 1596.0)  # NOTE: Antes: (1500.0, 1575.0). No v1: (1500.0, 1596.0) (ECAL.py#L58). No v2: default (1500.0, 1596.0), atlas_emb: (1500.0, 1597.47).
        .z_length(6800.0)  # NOTE: Conforme com v1 (ECAL.py#L59) e v2 default (6800.0 mm).
        .segmentation(nof_layers=16, absorber_th=1.51, gap_th=4.49)  # NOTE: Antes: nof_layers=16, absorber_th=1.53, gap_th=4.5 (contaminação atlas_emb v2:ECAL.py#L118). No v1: 16 cam, 1.51 mm Pb, 4.49 mm LAr (ECAL.py#L55-L56). No v2: default idêntico a v1 (16 cam, 1.51/4.49 mm).
        .granularity(delta_eta=0.00325, delta_phi=np.pi / 32.0)  # NOTE: Antes: delta_eta=0.003125 (contaminação EMB_ATLAS_REGIONS v2:ECAL.py#L233). No v1: delta_eta=0.00325 (ECAL.py#L98). No v2: default 0.00325 (v2:ECAL.py#L71).
        .electronics(noise_mev=26.0, pulse_file=_lar_pulse())  # NOTE: Conforme com v1 (ECAL.py#L119) e v2 default (26.0 MeV).
        .build(),

        # -------------------------------------------------------------------------
        # LAr::EMB2 (Electromagnetic Barrel Layer 2 - Middle)
        # -------------------------------------------------------------------------
        # NOTE: DIVERGÊNCIA CORRIGIDA DEVIDO A SIMPLIFICAÇÃO INDEVIDA de camadas e ruído.
        # - No v1: RMin=1596.0 mm, RMax=1926.0 mm (1596 + 55*(1.7 + 4.3)), NOF_LAYERS=55 CAMADAS,
        #   absorber_th=1.70 mm, gap_th=4.30 mm. Granularidade deta=0.025, dphi=pi/128. Ruído=60 MeV.
        #   v1 link: https://github.com/lorenzetti-ufrj-br/lorenzetti/blob/a32691874ab042e7d8759f6f33141ac60b88e3da/geometry/python/v1/ECAL.py#L65-L78
        #   v1 Calorimeter (Noise=60 MeV): https://github.com/lorenzetti-ufrj-br/lorenzetti/blob/a32691874ab042e7d8759f6f33141ac60b88e3da/geometry/python/v1/ECAL.py#L127-L136
        # - No v2 (master): Default é idêntico ao v1 (55 camadas de 1.7/4.3 mm, ruído 60 MeV):
        #   v2 default link: https://github.com/lorenzetti-ufrj-br/lorenzetti/blob/master/geometry/python/v2/ECAL.py#L79-L92
        #   No modo atlas_emb=True, passa para 47 camadas de 6.962 mm:
        #   v2 atlas_emb link: https://github.com/lorenzetti-ufrj-br/lorenzetti/blob/master/geometry/python/v2/ECAL.py#L119
        LArBarrelBuilder("LAr::EMB2", CaloSampling.EMB2)
        .radii(1596.0, 1926.0)  # NOTE: Antes: (1575.0, 1875.0). No v1: (1596.0, 1926.0) (ECAL.py#L72). No v2: default (1596.0, 1926.0), atlas_emb: (1597.5, 1924.7).
        .z_length(6800.0)  # NOTE: Conforme com v1 (ECAL.py#L73) e v2 default (6800.0 mm).
        .segmentation(nof_layers=55, absorber_th=1.70, gap_th=4.30)  # NOTE: Antes: nof_layers=16, absorber_th=1.53, gap_th=4.5. No v1: 55 cam, 1.70 mm Pb, 4.30 mm LAr (ECAL.py#L69-L70). No v2: default 55 cam, 1.70/4.30 mm (v2:ECAL.py#L83).
        .granularity(delta_eta=0.025, delta_phi=np.pi / 128.0)  # NOTE: Conforme com v1 (ECAL.py#L99) e v2 default.
        .electronics(noise_mev=60.0, pulse_file=_lar_pulse())  # NOTE: Antes: noise_mev=40.0. No v1: 60.0 MeV (ECAL.py#L129). No v2: default 60.0 MeV (v2:ECAL.py#L254).
        .build(),

        # -------------------------------------------------------------------------
        # LAr::EMB3 (Electromagnetic Barrel Layer 3 - Back)
        # -------------------------------------------------------------------------
        # NOTE: DIVERGÊNCIA CORRIGIDA DEVIDO A SIMPLIFICAÇÃO INDEVIDA de camadas, raios e ruído.
        # - No v1: RMin=1926.0 mm, RMax=1980.0 mm (1926 + 9*(1.7 + 4.3)), NOF_LAYERS=9 CAMADAS,
        #   absorber_th=1.70 mm, gap_th=4.30 mm. Granularidade deta=0.050, dphi=pi/128. Ruído=40 MeV.
        #   v1 link: https://github.com/lorenzetti-ufrj-br/lorenzetti/blob/a32691874ab042e7d8759f6f33141ac60b88e3da/geometry/python/v1/ECAL.py#L80-L93
        #   v1 Calorimeter (Noise=40 MeV): https://github.com/lorenzetti-ufrj-br/lorenzetti/blob/a32691874ab042e7d8759f6f33141ac60b88e3da/geometry/python/v1/ECAL.py#L138-L147
        # - No v2 (master): Default é idêntico ao v1 (9 camadas de 1.7/4.3 mm, ruído 40 MeV):
        #   v2 default link: https://github.com/lorenzetti-ufrj-br/lorenzetti/blob/master/geometry/python/v2/ECAL.py#L94-L107
        #   No modo atlas_emb=True, passa para 7 camadas de 6.962 mm:
        #   v2 atlas_emb link: https://github.com/lorenzetti-ufrj-br/lorenzetti/blob/master/geometry/python/v2/ECAL.py#L119
        LArBarrelBuilder("LAr::EMB3", CaloSampling.EMB3)
        .radii(1926.0, 1980.0)  # NOTE: Antes: (1875.0, 1960.0). No v1: (1926.0, 1980.0) (ECAL.py#L86). No v2: default (1926.0, 1980.0), atlas_emb: (1924.7, 1973.4).
        .z_length(6800.0)  # NOTE: Conforme com v1 (ECAL.py#L87) e v2 default (6800.0 mm).
        .segmentation(nof_layers=9, absorber_th=1.70, gap_th=4.30)  # NOTE: Antes: nof_layers=16, absorber_th=1.53, gap_th=4.5. No v1: 9 cam, 1.70 mm Pb, 4.30 mm LAr (ECAL.py#L84-L85). No v2: default 9 cam (1.70/4.30 mm).
        .granularity(delta_eta=0.05, delta_phi=np.pi / 128.0)  # NOTE: Conforme com v1 (ECAL.py#L100) e v2 default.
        .electronics(noise_mev=40.0, pulse_file=_lar_pulse())  # NOTE: Antes: noise_mev=20.0. No v1: 40.0 MeV (ECAL.py#L143). No v2: default 40.0 MeV (v2:ECAL.py#L268).
        .build(),
    ]


def getGalticTileBarrelCfg() -> List[CaloSamplingLayer]:
    """Returns the 3 radial sampling layers of the central TileCal Barrel in v1 configuration."""
    # -------------------------------------------------------------------------
    # TileCal Barrel (TileCal1, TileCal2, TileCal3)
    # -------------------------------------------------------------------------
    # NOTE: DIVERGÊNCIA CORRIGIDA DEVIDO A CONTAMINAÇÃO DIRETA da opção TileAtlasGeometry de v2!
    # - No v1:
    #   1. Orientação das placas: Plates.Horizontal (camadas cilíndricas concêntricas radiais).
    #   2. Comprimento total Z: ZSize = 6048.0 mm (2 * (3704 - 680 mm)).
    #   3. Granularidade em phi: dphi = pi/32 = 0.09817 rad.
    #   4. Ruído eletrônico: 20 MeV constante para TileCal1, TileCal2 e TileCal3.
    #   5. Estrutura radial:
    #      - TileCal1: RMin=2283.0, RMax=2683.0 mm (4 camadas de 60 mm Fe + 40 mm Scint = 100 mm).
    #      - TileCal2: RMin=2683.0, RMax=3783.0 mm (11 camadas de 62 mm Fe + 38 mm Scint = 100 mm).
    #      - TileCal3: RMin=3783.0, RMax=4283.0 mm (5 camadas de 62 mm Fe + 38 mm Scint = 100 mm).
    #   v1 PhysicalVolume link: https://github.com/lorenzetti-ufrj-br/lorenzetti/blob/a32691874ab042e7d8759f6f33141ac60b88e3da/geometry/python/v1/TILE.py#L40-L85
    #   v1 SensitiveDetector: https://github.com/lorenzetti-ufrj-br/lorenzetti/blob/a32691874ab042e7d8759f6f33141ac60b88e3da/geometry/python/v1/TILE.py#L91-L93
    #   v1 Calorimeter (Noise=20 MeV): https://github.com/lorenzetti-ufrj-br/lorenzetti/blob/a32691874ab042e7d8759f6f33141ac60b88e3da/geometry/python/v1/TILE.py#L99-L134
    # - No v2 (master):
    #   Default (TileAtlasGeometry=False) é idêntico ao v1 (Plates.Horizontal, Z=6048 mm, ruído 20 MeV):
    #   v2 default link: https://github.com/lorenzetti-ufrj-br/lorenzetti/blob/master/geometry/python/v2/TILE.py#L273-L330
    #   No modo TileAtlasGeometry=True, passa a usar placas verticais em Z (Plates.Vertical),
    #   período de 18 mm (14 mm Fe + 3 mm Scint + 1 mm folga), e Z=2*2808=5616 mm:
    #   v2 TileAtlasGeometry link: https://github.com/lorenzetti-ufrj-br/lorenzetti/blob/master/geometry/python/v2/TILE.py#L27-L38
    return [
        TileCalBuilder("TILE::TileCal1", CaloSampling.TileCal1)
        .radii(2283.0, 2683.0)  # NOTE: Conforme com v1 (TILE.py#L53) e v2 default.
        .length_and_center(z_size=6048.0, z_center=0.0)  # NOTE: Antes: z_size=5640.0 mm (contaminação TileAtlasGeometry de v2:TILE.py#L27). No v1: z_size=6048.0 mm (TILE.py#L42). No v2: default 6048.0 mm, atlas: 5616.0 mm.
        .segmentation(nof_layers=4, absorber_th=60.0, gap_th=40.0)  # NOTE: Antes: omitido (default builder 1 cam, 14/3 mm). No v1: 4 cam, 60.0 mm Fe, 40.0 mm Scint (TILE.py#L50-L52). No v2: default 4 cam (60/40 mm).
        .granularity(delta_eta=0.1, delta_phi=np.pi / 32.0)  # NOTE: Antes: delta_phi=0.1 float. No v1: delta_phi=pi/32 rad (TILE.py#L91). No v2: pi/32 rad.
        .electronics(noise_mev=20.0, pulse_file=_tile_pulse())  # NOTE: Antes: noise_mev=25.0. No v1: 20.0 MeV constante para todos (TILE.py#L103). No v2: default 20.0 MeV.
        .build(),

        TileCalBuilder("TILE::TileCal2", CaloSampling.TileCal2)
        .radii(2683.0, 3783.0)  # NOTE: Conforme com v1 (TILE.py#L67) e v2 default.
        .length_and_center(z_size=6048.0, z_center=0.0)  # NOTE: Antes: z_size=5640.0 mm. No v1: z_size=6048.0 mm (TILE.py#L42). No v2: default 6048.0 mm.
        .segmentation(nof_layers=11, absorber_th=62.0, gap_th=38.0)  # NOTE: Antes: omitido. No v1: 11 cam, 62.0 mm Fe, 38.0 mm Scint (TILE.py#L64-L66). No v2: default 11 cam (62/38 mm).
        .granularity(delta_eta=0.1, delta_phi=np.pi / 32.0)  # NOTE: Antes: delta_phi=0.1 float. No v1: delta_phi=pi/32 rad (TILE.py#L92). No v2: pi/32 rad.
        .electronics(noise_mev=20.0, pulse_file=_tile_pulse())  # NOTE: Antes: noise_mev=30.0. No v1: 20.0 MeV (TILE.py#L117). No v2: default 20.0 MeV.
        .build(),

        TileCalBuilder("TILE::TileCal3", CaloSampling.TileCal3)
        .radii(3783.0, 4283.0)  # NOTE: Conforme com v1 (TILE.py#L81) e v2 default.
        .length_and_center(z_size=6048.0, z_center=0.0)  # NOTE: Antes: z_size=5640.0 mm. No v1: z_size=6048.0 mm (TILE.py#L42). No v2: default 6048.0 mm.
        .segmentation(nof_layers=5, absorber_th=62.0, gap_th=38.0)  # NOTE: Antes: omitido. No v1: 5 cam, 62.0 mm Fe, 38.0 mm Scint (TILE.py#L78-L80). No v2: default 5 cam (62/38 mm).
        .granularity(delta_eta=0.2, delta_phi=np.pi / 32.0)  # NOTE: Antes: delta_phi=0.1 float. No v1: delta_phi=pi/32 rad (TILE.py#L93). No v2: pi/32 rad.
        .electronics(noise_mev=20.0, pulse_file=_tile_pulse())  # NOTE: Antes: noise_mev=35.0. No v1: 20.0 MeV (TILE.py#L131). No v2: default 20.0 MeV.
        .build(),
    ]


def getGalticTileExtendedCfg(side_a: bool = True) -> List[CaloSamplingLayer]:
    """Returns the 3 sampling layers of TileCal Extended Barrel for Side A or Side B in v1 configuration."""
    # -------------------------------------------------------------------------
    # TileCal Extended Barrel (TileExt1, TileExt2, TileExt3)
    # -------------------------------------------------------------------------
    # NOTE: DIVERGÊNCIAS CORRIGIDAS DE GRANULARIDADE E RUÍDO.
    # - No v1:
    #   1. Orientação: Plates.Horizontal.
    #   2. Comprimento: ZSize = 2830.0 mm (2.83 m).
    #   3. Centro em Z: ZCenter = +- 5119.0 mm (+- (3704 + 2830/2)).
    #   4. Granularidade: dphi = pi/32 = 0.09817 rad.
    #   5. Ruído eletrônico: 20 MeV para todos os módulos (Ext1, Ext2, Ext3).
    #   v1 link: https://github.com/lorenzetti-ufrj-br/lorenzetti/blob/a32691874ab042e7d8759f6f33141ac60b88e3da/geometry/python/v1/TILE.py#L159-L215
    #   v1 Calorimeter (Noise=20 MeV): https://github.com/lorenzetti-ufrj-br/lorenzetti/blob/a32691874ab042e7d8759f6f33141ac60b88e3da/geometry/python/v1/TILE.py#L223-L256
    # - No v2 (master):
    #   Default é idêntico ao v1 (ZSize=2830 mm, ZCenter=+-5119 mm, ruído 20 MeV):
    #   v2 default link: https://github.com/lorenzetti-ufrj-br/lorenzetti/blob/master/geometry/python/v2/TILE.py#L400-L450
    #   No modo TileAtlasGeometry=True: ZSize = 6110 - 3554 = 2556 mm, ZCenter = +-4832 mm:
    #   v2 TileAtlasGeometry link: https://github.com/lorenzetti-ufrj-br/lorenzetti/blob/master/geometry/python/v2/TILE.py#L37-L38
    z_center = 5119.0 if side_a else -5119.0
    side_tag = "A" if side_a else "B"
    return [
        TileCalBuilder(f"TILE::TileCalExt1::{side_tag}", CaloSampling.TileExt1)
        .radii(2283.0, 2683.0)  # NOTE: Conforme com v1 (TILE.py#L178) e v2 default.
        .length_and_center(z_size=2830.0, z_center=z_center)  # NOTE: z_size=2830.0 mm e z_center=+-5119.0 mm CONFORMES com v1 (TILE.py#L159-L161).
        .segmentation(nof_layers=4, absorber_th=60.0, gap_th=40.0)  # NOTE: Antes: omitido (default builder 1 cam, 14/3 mm). No v1: 4 cam, 60.0 mm Fe, 40.0 mm Scint (TILE.py#L173-L177). No v2: default 4 cam (60/40 mm).
        .granularity(delta_eta=0.1, delta_phi=np.pi / 32.0)  # NOTE: Antes: delta_phi=0.1 float. No v1: delta_phi=pi/32 rad (TILE.py#L218). No v2: pi/32 rad.
        .electronics(noise_mev=20.0, pulse_file=_tile_pulse())  # NOTE: Antes: noise_mev=25.0. No v1: 20.0 MeV (TILE.py#L229). No v2: default 20.0 MeV.
        .build(),

        TileCalBuilder(f"TILE::TileCalExt2::{side_tag}", CaloSampling.TileExt2)
        .radii(2683.0, 3783.0)  # NOTE: Conforme com v1 (TILE.py#L192) e v2 default.
        .length_and_center(z_size=2830.0, z_center=z_center)  # NOTE: z_size=2830.0 mm e z_center=+-5119.0 mm CONFORMES com v1 (TILE.py#L159-L161).
        .segmentation(nof_layers=11, absorber_th=62.0, gap_th=38.0)  # NOTE: Antes: omitido. No v1: 11 cam, 62.0 mm Fe, 38.0 mm Scint (TILE.py#L187-L191). No v2: default 11 cam (62/38 mm).
        .granularity(delta_eta=0.1, delta_phi=np.pi / 32.0)  # NOTE: Antes: delta_phi=0.1 float. No v1: delta_phi=pi/32 rad (TILE.py#L219). No v2: pi/32 rad.
        .electronics(noise_mev=20.0, pulse_file=_tile_pulse())  # NOTE: Antes: noise_mev=30.0. No v1: 20.0 MeV (TILE.py#L243). No v2: default 20.0 MeV.
        .build(),

        TileCalBuilder(f"TILE::TileCalExt3::{side_tag}", CaloSampling.TileExt3)
        .radii(3783.0, 4283.0)  # NOTE: Conforme com v1 (TILE.py#L206) e v2 default.
        .length_and_center(z_size=2830.0, z_center=z_center)  # NOTE: z_size=2830.0 mm e z_center=+-5119.0 mm CONFORMES com v1 (TILE.py#L159-L161).
        .segmentation(nof_layers=5, absorber_th=62.0, gap_th=38.0)  # NOTE: Antes: omitido. No v1: 5 cam, 62.0 mm Fe, 38.0 mm Scint (TILE.py#L201-L205). No v2: default 5 cam (62/38 mm).
        .granularity(delta_eta=0.2, delta_phi=np.pi / 32.0)  # NOTE: Antes: delta_phi=0.1 float. No v1: delta_phi=pi/32 rad (TILE.py#L220). No v2: pi/32 rad.
        .electronics(noise_mev=20.0, pulse_file=_tile_pulse())  # NOTE: Antes: noise_mev=35.0. No v1: 20.0 MeV (TILE.py#L257). No v2: default 20.0 MeV.
        .build(),
    ]


def getGalticLArEMECCfg(side_a: bool = True) -> List[CaloSamplingLayer]:
    """Returns the active sampling layers of LAr EMEC for Side A or Side B in v1 configuration."""
    # -------------------------------------------------------------------------
    # LAr EMEC (PSE, EMEC1, EMEC2, EMEC3)
    # -------------------------------------------------------------------------
    # NOTE: DIVERGÊNCIAS CORRIGIDAS DE RUÍDO, MATERIAL E SEGMENTAÇÕES.
    # - No v1:
    #   1. PSE: RMin=1232, RMax=1700, ZSize=5.0, ZCenter=+-3737.5 mm. Absorber="Vacuum". Ruído=26 MeV.
    #      v1 link: https://github.com/lorenzetti-ufrj-br/lorenzetti/blob/a32691874ab042e7d8759f6f33141ac60b88e3da/geometry/python/v1/EMEC.py#L30-L60
    #   2. EMEC1: 16 camadas (2.27 mm Pb + 3.73 mm LAr), ZSize=96 mm, ZCenter=+-3788 mm. Ruído=26 MeV.
    #      POSSUI 4 SEGMENTOS EM ETA (4 samplings no readout de v1):
    #      - Seg 0: |eta| < 1.80, deta=0.00325, dphi=pi/32, Key="Collection_EMEC1_0"
    #      - Seg 1: 1.80 < |eta| < 2.00, deta=0.025, dphi=pi/32, Key="Collection_EMEC1_1"
    #      - Seg 2: 2.00 < |eta| < 2.37, deta=0.006, dphi=pi/32, Key="Collection_EMEC1_2"
    #      - Seg 3: |eta| > 2.37, deta=0.1, dphi=pi/32, Key="Collection_EMEC1_3"
    #      v1 link: https://github.com/lorenzetti-ufrj-br/lorenzetti/blob/a32691874ab042e7d8759f6f33141ac60b88e3da/geometry/python/v1/EMEC.py#L68-L135
    #   3. EMEC2: 55 camadas (2.27 mm Pb + 3.73 mm LAr), ZSize=330 mm, ZCenter=+-4001 mm. Ruído=60 MeV.
    #      POSSUI 2 SEGMENTOS EM ETA (2 samplings):
    #      - Seg 0: |eta| < 2.50, deta=0.025, dphi=pi/128, Key="Collection_EMEC2_0"
    #      - Seg 1: |eta| > 2.50, deta=0.1, dphi=pi/32, Key="Collection_EMEC2_1"
    #      v1 link: https://github.com/lorenzetti-ufrj-br/lorenzetti/blob/a32691874ab042e7d8759f6f33141ac60b88e3da/geometry/python/v1/EMEC.py#L138-L185
    #   4. EMEC3: 9 camadas (2.41 mm Pb + 3.59 mm LAr), ZSize=54 mm, ZCenter=+-4193 mm. Ruído=40 MeV.
    #      POSSUI 2 SEGMENTOS EM ETA (2 samplings):
    #      - Seg 0: |eta| < 2.50, deta=0.050, dphi=pi/128, Key="Collection_EMEC3_0"
    #      - Seg 1: |eta| > 2.50, deta=0.1, dphi=pi/32, Key="Collection_EMEC3_1"
    #      v1 link: https://github.com/lorenzetti-ufrj-br/lorenzetti/blob/a32691874ab042e7d8759f6f33141ac60b88e3da/geometry/python/v1/EMEC.py#L188-L235
    # - No v2 (master): Default é idêntico ao v1 com todos os 9 samplings:
    #   v2 default link: https://github.com/lorenzetti-ufrj-br/lorenzetti/blob/master/geometry/python/v2/EMEC.py#L87-L255
    #   No modo atlas_emec=True, implementa duas rodas com sanfona e compartimentos DC3:
    #   v2 atlas_emec link: https://github.com/lorenzetti-ufrj-br/lorenzetti/blob/master/geometry/python/v2/EMEC.py#L259-L345
    return [
        LArEMECBuilder("LAr::PSE", CaloSampling.PSE, side_a=side_a)
        .geometry(rmin=1232.0, rmax=1700.0, z_size=5.0, z_center=3737.5)  # NOTE: Conforme com v1 (EMEC.py#L43-L45) e v2 default.
        .materials(absorber="Vacuum", gap="liquidArgon")  # NOTE: Antes: default builder "G4_Pb". No v1: "Vacuum" (EMEC.py#L38). No v2: default "Vacuum" (v2:EMEC.py#L52).
        .segmentation(nof_layers=1, absorber_th=0.01, gap_th=4.99)  # NOTE: Antes: default builder (1 cam, 1.75/4.5 mm). No v1: 1 cam, 0.01 mm Vacuum, 4.99 mm LAr (EMEC.py#L40-L42). No v2: default 1 cam (0.01/4.99 mm).
        .granularity(delta_eta=0.025, delta_phi=np.pi / 32.0)  # NOTE: Conforme com v1 (EMEC.py#L49) e v2 default.
        .electronics(noise_mev=26.0, pulse_file=_lar_pulse())  # NOTE: Antes: noise_mev=90.0. No v1: 26.0 MeV (EMEC.py#L56). No v2: default 26.0 MeV.
        .build(),

        LArEMECBuilder("LAr::EMEC1", CaloSampling.EMEC1, side_a=side_a)
        .geometry(rmin=302.0, rmax=2042.0, z_size=96.0, z_center=3788.0)  # NOTE: Conforme com v1 (EMEC.py#L76-L79) e v2 default.
        .materials(absorber="G4_Pb", gap="liquidArgon")
        .segmentation(nof_layers=16, absorber_th=2.27, gap_th=3.73)  # NOTE: Antes: default builder (1 cam, 1.75/4.5 mm). No v1: 16 cam, 2.27 mm Pb, 3.73 mm LAr (EMEC.py#L74-L75). No v2: default 16 cam (2.27/3.73 mm).
        .electronics(noise_mev=26.0, pulse_file=_lar_pulse())  # NOTE: Antes: noise_mev=35.0. No v1: 26.0 MeV (EMEC.py#L96). No v2: default 26.0 MeV.
        # NOTE: EMEC1 possui 4 segmentos em eta no v1 (EMEC.py#L88-L135) e v2 default (v2:EMEC.py#L100-L147):
        .add_segment(segment=0, eta_min=None, eta_max=1.80, delta_eta=0.00325, delta_phi=np.pi / 32.0)
        .add_segment(segment=1, eta_min=1.80, eta_max=2.00, delta_eta=0.025, delta_phi=np.pi / 32.0)
        .add_segment(segment=2, eta_min=2.00, eta_max=2.37, delta_eta=0.006, delta_phi=np.pi / 32.0)
        .add_segment(segment=3, eta_min=2.37, eta_max=None, delta_eta=0.100, delta_phi=np.pi / 32.0)
        .build(),

        LArEMECBuilder("LAr::EMEC2", CaloSampling.EMEC2, side_a=side_a)
        .geometry(rmin=302.0, rmax=2042.0, z_size=330.0, z_center=4001.0)  # NOTE: Conforme com v1 (EMEC.py#L137-L140) e v2 default.
        .materials(absorber="G4_Pb", gap="liquidArgon")
        .segmentation(nof_layers=55, absorber_th=2.27, gap_th=3.73)  # NOTE: Antes: default builder (1 cam, 1.75/4.5 mm). No v1: 55 cam, 2.27 mm Pb, 3.73 mm LAr (EMEC.py#L135-L136). No v2: default 55 cam (2.27/3.73 mm).
        .electronics(noise_mev=60.0, pulse_file=_lar_pulse())  # NOTE: Antes: noise_mev=45.0. No v1: 60.0 MeV (EMEC.py#L158). No v2: default 60.0 MeV.
        # NOTE: EMEC2 possui 2 segmentos em eta no v1 (EMEC.py#L149-L185) e v2 default (v2:EMEC.py#L170-L206):
        .add_segment(segment=0, eta_min=None, eta_max=2.50, delta_eta=0.025, delta_phi=np.pi / 128.0)
        .add_segment(segment=1, eta_min=2.50, eta_max=None, delta_eta=0.100, delta_phi=np.pi / 32.0)
        .build(),

        LArEMECBuilder("LAr::EMEC3", CaloSampling.EMEC3, side_a=side_a)
        .geometry(rmin=302.0, rmax=2042.0, z_size=54.0, z_center=4193.0)  # NOTE: Conforme com v1 (EMEC.py#L184-L187) e v2 default.
        .materials(absorber="G4_Pb", gap="liquidArgon")
        .segmentation(nof_layers=9, absorber_th=2.41, gap_th=3.59)  # NOTE: Antes: default builder (1 cam, 1.75/4.5 mm). No v1: 9 cam, 2.41 mm Pb, 3.59 mm LAr (EMEC.py#L182-L183). No v2: default 9 cam (2.41/3.59 mm).
        .electronics(noise_mev=40.0, pulse_file=_lar_pulse())  # NOTE: Antes: noise_mev=25.0. No v1: 40.0 MeV (EMEC.py#L205). No v2: default 40.0 MeV.
        # NOTE: EMEC3 possui 2 segmentos em eta no v1 (EMEC.py#L196-L235) e v2 default (v2:EMEC.py#L220-L255):
        .add_segment(segment=0, eta_min=None, eta_max=2.50, delta_eta=0.050, delta_phi=np.pi / 128.0)
        .add_segment(segment=1, eta_min=2.50, eta_max=None, delta_eta=0.100, delta_phi=np.pi / 32.0)
        .build(),
    ]


def getGalticHECCfg(side_a: bool = True) -> List[CaloSamplingLayer]:
    """Returns the 3 longitudinal sampling layers of HEC for Side A or Side B in v1 configuration."""
    # -------------------------------------------------------------------------
    # HEC (Hadronic Endcap Calorimeter: HEC1, HEC2, HEC3)
    # -------------------------------------------------------------------------
    # NOTE: DIVERGÊNCIAS CORRIGIDAS: PULSO LAR RESTAURADO, RUÍDO E SEGMENTAÇÃO.
    # - No v1:
    #   1. Formato de Pulso: pulseLar.dat (HEC é um detector LAr com placas de cobre!).
    #   2. Ruído eletrônico: 250 MeV para HEC1 e HEC3; 400 MeV para HEC2.
    #   3. Cada um dos 3 módulos possui 2 SEGMENTOS EM ETA (total 6 samplings por lado no readout):
    #      - Seg 0: |eta| < 2.50, deta=0.1, dphi=pi/32
    #      - Seg 1: |eta| > 2.50, deta=0.2, dphi=pi/16
    #   4. Estrutura dos blocos:
    #      - HEC1: 9 cam. (12.5 mm Cu + 8.5 mm LAr), ZSize=189 mm, ZCenter=+-4356.5 mm, R: 372->2030 mm.
    #      - HEC2: 16 cam. (12.5 mm Cu + 8.5 mm LAr), ZSize=336 mm, ZCenter=+-4808.0 mm, R: 475->2030 mm.
    #      - HEC3: 16 cam. (50.0 mm Cu + 8.5 mm LAr), ZSize=936 mm, ZCenter=+-5444.0 mm, R: 475->2030 mm.
    #   v1 PhysicalVolume link: https://github.com/lorenzetti-ufrj-br/lorenzetti/blob/a32691874ab042e7d8759f6f33141ac60b88e3da/geometry/python/v1/HEC.py#L30-L145
    #   v1 SensitiveDetector: https://github.com/lorenzetti-ufrj-br/lorenzetti/blob/a32691874ab042e7d8759f6f33141ac60b88e3da/geometry/python/v1/HEC.py#L46-L47
    #   v1 Calorimeter (Noise 250/400 MeV e pulseLar.dat): https://github.com/lorenzetti-ufrj-br/lorenzetti/blob/a32691874ab042e7d8759f6f33141ac60b88e3da/geometry/python/v1/HEC.py#L52-L175
    # - No v2 (master):
    #   Default é idêntico ao v1 (pulseLar.dat, ruído 250/400 MeV, 6 samplings por lado):
    #   v2 default link: https://github.com/lorenzetti-ufrj-br/lorenzetti/blob/master/geometry/python/v2/HEC.py#L45-L200
    #   No modo atlas_hec=True, implementa HEC0..HEC3 com 7 blocos e gap de roda:
    #   v2 atlas_hec link: https://github.com/lorenzetti-ufrj-br/lorenzetti/blob/master/geometry/python/v2/HEC.py#L212-L260
    return [
        HECBuilder("FCal::HEC1", CaloSampling.HEC1, side_a=side_a)
        .geometry(rmin=372.0, rmax=2030.0, z_size=189.0, z_center=4356.5)  # NOTE: Conforme com v1 (HEC.py#L36-L39) e v2 default.
        .materials(absorber="G4_Cu", gap="liquidArgon")
        .segmentation(nof_layers=9, absorber_th=12.5, gap_th=8.5)  # NOTE: Antes: default builder (1 cam, 25.0/8.5 mm). No v1: 9 cam, 12.5 mm Cu, 8.5 mm LAr, z_size=189 mm (HEC.py#L32-L34). No v2: default 9 cam (12.5/8.5 mm).
        .electronics(noise_mev=250.0, pulse_file=_lar_pulse())  # NOTE: Antes: noise_mev=80.0 e pulse_file=pulseTile.dat (erro grave). No v1: noise=250.0 MeV e pulse_file=pulseLar.dat (HEC.py#L52-L53). No v2: default 250.0 MeV e pulseLar.dat.
        # NOTE: HEC1 possui 2 segmentos em eta no v1 (HEC.py#L46-L47) e v2 default (v2:HEC.py#L59-L63):
        .add_segment(segment=0, eta_min=None, eta_max=2.50, delta_eta=0.1, delta_phi=np.pi / 32.0)
        .add_segment(segment=1, eta_min=2.50, eta_max=None, delta_eta=0.2, delta_phi=np.pi / 16.0)
        .build(),

        HECBuilder("FCal::HEC2", CaloSampling.HEC2, side_a=side_a)
        .geometry(rmin=475.0, rmax=2030.0, z_size=336.0, z_center=4808.0)  # NOTE: Antes: rmin=372.0 mm (copiado de HEC1), z_center=4619.0 mm. No v1: rmin=475.0 mm, z_center=4808.0 mm (4262 + 189 + 189 + 168) (HEC.py#L102-L104). No v2: default 475.0 mm e z_center=4808.0 mm.
        .materials(absorber="G4_Cu", gap="liquidArgon")
        .segmentation(nof_layers=16, absorber_th=12.5, gap_th=8.5)  # NOTE: Antes: default builder (1 cam, 25.0/8.5 mm). No v1: 16 cam, 12.5 mm Cu, 8.5 mm LAr, z_size=336 mm (HEC.py#L91-L93). No v2: default 16 cam (12.5/8.5 mm).
        .electronics(noise_mev=400.0, pulse_file=_lar_pulse())  # NOTE: Antes: noise_mev=100.0 e pulse_file=pulseTile.dat. No v1: noise=400.0 MeV e pulse_file=pulseLar.dat (HEC.py#L111-L112). No v2: default 400.0 MeV e pulseLar.dat.
        # NOTE: HEC2 possui 2 segmentos em eta no v1 (HEC.py#L105-L106) e v2 default (v2:HEC.py#L114-L118):
        .add_segment(segment=0, eta_min=None, eta_max=2.50, delta_eta=0.1, delta_phi=np.pi / 32.0)
        .add_segment(segment=1, eta_min=2.50, eta_max=None, delta_eta=0.2, delta_phi=np.pi / 16.0)
        .build(),

        HECBuilder("FCal::HEC3", CaloSampling.HEC3, side_a=side_a)
        .geometry(rmin=475.0, rmax=2030.0, z_size=936.0, z_center=5444.0)  # NOTE: Antes: rmin=372.0 mm, z_center=5255.0 mm. No v1: rmin=475.0 mm, z_center=5444.0 mm (4262 + 189 + 189 + 336 + 468) (HEC.py#L155-L157). No v2: default 475.0 mm e z_center=5444.0 mm.
        .materials(absorber="G4_Cu", gap="liquidArgon")
        .segmentation(nof_layers=16, absorber_th=50.0, gap_th=8.5)  # NOTE: Antes: default builder (1 cam, 25.0/8.5 mm). No v1: 16 cam, 50.0 mm Cu, 8.5 mm LAr, z_size=936 mm (HEC.py#L143-L145). No v2: default 16 cam (50.0/8.5 mm).
        .electronics(noise_mev=250.0, pulse_file=_lar_pulse())  # NOTE: Antes: noise_mev=120.0 e pulse_file=pulseTile.dat. No v1: noise=250.0 MeV e pulse_file=pulseLar.dat (HEC.py#L163-L164). No v2: default 250.0 MeV e pulseLar.dat.
        # NOTE: HEC3 possui 2 segmentos em eta no v1 (HEC.py#L158-L159) e v2 default (v2:HEC.py#L170-L174):
        .add_segment(segment=0, eta_min=None, eta_max=2.50, delta_eta=0.1, delta_phi=np.pi / 32.0)
        .add_segment(segment=1, eta_min=2.50, eta_max=None, delta_eta=0.2, delta_phi=np.pi / 16.0)
        .build(),
    ]


def getGalticDeadMaterialsCfg() -> List[DeadMaterialVolume]:
    """Returns all passive dead material volumes (cryostats and crack supports) in v1 configuration."""
    # -------------------------------------------------------------------------
    # Dead Materials (Matéria Morta)
    # -------------------------------------------------------------------------
    # NOTE: DIVERGÊNCIA EM NOMENCLATURAS E OMISSÃO DE VOLUME TOTALMENTE CORRIGIDAS.
    # - No v1:
    #   1. DM::PS::Boundary: RMin=1380 mm, RMax=1460 mm, ZSize=6800 mm, Plates.Horizontal, G4_Al.
    #   2. DM::LAr::Boundary: RMin=1980 mm, RMax=2083 mm, ZSize=6800 mm, Plates.Horizontal, G4_Al.
    #   3. DM::TILE::Boundary: RMin=2180 mm, RMax=2283 mm, ZSize=6048 mm, Plates.Horizontal, G4_Al.
    #   4. DM::Crack::EM::A/B: RMin=900 mm, RMax=2232 mm, ZSize=300 mm, ZCenter=+-3567.5 mm, Plates.Vertical, G4_Al, Gap=liquidArgon.
    #   5. DM::Crack::TILE::A/B: RMin=2283 mm, RMax=4284 mm, ZSize=680 mm, ZCenter=+-3364.0 mm, Plates.Horizontal, G4_Al, Gap=Vacuum.
    #   Total = 7 volumes canônicos.
    #   v1 link: https://github.com/lorenzetti-ufrj-br/lorenzetti/blob/a32691874ab042e7d8759f6f33141ac60b88e3da/geometry/python/v1/DeadMaterials.py#L20-L130
    # - No v2 (master):
    #   Default é idêntico ao v1 com os 7 volumes canônicos:
    #   v2 default link: https://github.com/lorenzetti-ufrj-br/lorenzetti/blob/master/geometry/python/v2/DeadMaterials.py#L62-L105 e L379-L430
    # NOTE: Volume espúrio "DM::Cryo::Inner1" (rmin=1200, rmax=1250) REMOVIDO: não existia no v1 nem no v2.
    return [
        DeadMaterialBuilder("DM::PS::Boundary")  # NOTE: Antes: renomeado para "DM::Cryo::Inner2" com rmin=1440, rmax=1455 mm. No v1: "DM::PS::Boundary", rmin=1380.0, rmax=1460.0, z_size=6800.0 mm (DeadMaterials.py#L59-L72). No v2: default idêntico a v1.
        .geometry(rmin=1380.0, rmax=1460.0, z_size=6800.0)
        .materials(absorber="G4_Al", gap="Vacuum", plates=Plates.Horizontal)
        .build(),

        DeadMaterialBuilder("DM::LAr::Boundary")  # NOTE: Antes: renomeado para "DM::Cryo::Outer". No v1: "DM::LAr::Boundary", rmin=1980.0, rmax=2083.0, z_size=6800.0 mm (DeadMaterials.py#L76-L89). No v2: default idêntico a v1.
        .geometry(rmin=1980.0, rmax=2083.0, z_size=6800.0)
        .materials(absorber="G4_Al", gap="Vacuum", plates=Plates.Horizontal)
        .build(),

        DeadMaterialBuilder("DM::TILE::Boundary")  # NOTE: Antes: OMITIDO no branch atual. No v1: "DM::TILE::Boundary", rmin=2180.0, rmax=2283.0, z_size=6048.0 mm (DeadMaterials.py#L92-L105). No v2: default idêntico a v1.
        .geometry(rmin=2180.0, rmax=2283.0, z_size=6048.0)
        .materials(absorber="G4_Al", gap="Vacuum", plates=Plates.Horizontal)
        .build(),

        DeadMaterialBuilder("DM::Crack::EM::A")
        .geometry(rmin=900.0, rmax=2232.0, z_size=300.0, center=(0.0, 0.0, 3567.5))  # NOTE: Conforme com v1 (DeadMaterials.py#L27-L30).
        .materials(absorber="G4_Al", gap="liquidArgon", plates=Plates.Vertical)  # NOTE: Antes: gap="Vacuum". No v1: gap="liquidArgon" (DeadMaterials.py#L25). No v2: default "liquidArgon".
        .build(),

        DeadMaterialBuilder("DM::Crack::EM::B")
        .geometry(rmin=900.0, rmax=2232.0, z_size=300.0, center=(0.0, 0.0, -3567.5))  # NOTE: Conforme com v1 (DeadMaterials.py#L27-L30).
        .materials(absorber="G4_Al", gap="liquidArgon", plates=Plates.Vertical)  # NOTE: Antes: gap="Vacuum". No v1: gap="liquidArgon" (DeadMaterials.py#L25). No v2: default "liquidArgon".
        .build(),

        DeadMaterialBuilder("DM::Crack::TILE::A")
        .geometry(rmin=2283.0, rmax=4284.0, z_size=680.0, center=(0.0, 0.0, 3364.0))  # NOTE: Conforme com v1 (DeadMaterials.py#L42-L45).
        .materials(absorber="G4_Al", gap="Vacuum", plates=Plates.Horizontal)  # NOTE: Antes: plates=Plates.Vertical, abso="G4_Fe". No v1: plates=Plates.Horizontal, abso="G4_Al" (DeadMaterials.py#L38-L39). No v2: default Plates.Horizontal.
        .build(),

        DeadMaterialBuilder("DM::Crack::TILE::B")
        .geometry(rmin=2283.0, rmax=4284.0, z_size=680.0, center=(0.0, 0.0, -3364.0))  # NOTE: Conforme com v1 (DeadMaterials.py#L42-L45).
        .materials(absorber="G4_Al", gap="Vacuum", plates=Plates.Horizontal)  # NOTE: Antes: plates=Plates.Vertical, abso="G4_Fe". No v1: plates=Plates.Horizontal, abso="G4_Al" (DeadMaterials.py#L38-L39). No v2: default Plates.Horizontal.
        .build(),
    ]


def getGalticAllSamplings() -> List[CaloSamplingLayer]:
    """Returns the full list of active calorimeter sampling layers for GALTIC (v1)."""
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
    """Returns all passive dead material volumes for GALTIC (v1)."""
    return getGalticDeadMaterialsCfg()
