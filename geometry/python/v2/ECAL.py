
__all__ = ["getLArBarrelCfg", "getAtlasEmbVolumesCfg", "atlasEmbCells", "atlasEmbLayers", "getAtlasPseCfg",
           "getAtlasEmbEndCfg", "atlasEmbConeSteps", "PSE_ATLAS_R", "PSE_ATLAS_Z", "PSB_ATLAS_Z"]


import os
import numpy as np
from CaloCell.CaloDefs import Detector, CaloSampling
from GaugiKernel.constants import m,cm,mm,MeV,pi

from .Calorimeter import Calorimeter
from .PhysicalVolume import PhysicalVolume, Plates, ProductionCuts
from .SensitiveDetector import SensitiveDetector, atlasLArPhiShift


def getLArBarrelCfg(atlas_emb=False, atlas_emb_cells=False):
  """
  Defines the geometry and readout configuration for the Liquid Argon (LAr) Barrel Calorimeter.

  Args:
      atlas_emb (bool): If True, the three layers have the absorber composition and the depth of the ATLAS barrel
                        (see the comment before the ATLAS layers below); the presampler and the readout do not change.
      atlas_emb_cells (bool): Needs atlas_emb. The three layers end at |z| = 3165 mm as in ATLAS, with steps that follow
                        |eta| = 1.475 near the inner radius, and have the cells of the ATLAS identifier dictionary (see
                        _getAtlasEmbCellsCfg and the notes before it). Their volumes come from getAtlasEmbVolumesCfg.
                        The barrel presampler is that of ATLAS (_getAtlasPsbCfg); the end-cap presampler and the
                        volumes behind the end of the barrel come from getAtlasPseCfg and getAtlasEmbEndCfg.

  Constructs the physical volumes (PreSampler, Back, Middle, Strips) and assigns
  readout parameters such as pulse shapes, noise levels, and Optimal Filter weights.

  Returns:
      List[Calorimeter]: A list of configured Calorimeter detector objects for the LAr Barrel.
  """


  if atlas_emb_cells and not atlas_emb:
    raise ValueError("atlas_emb_cells needs atlas_emb.")

  basepath = os.environ['LORENZETTI_GEOMETRY_DATA_DIR']

  # ECal
  ecal_barrel_start = 0*m
  ecal_barrel_end   = 3.4*m
  ecal_barrel_z     = (ecal_barrel_start + ecal_barrel_end) * 2


  psb_pv =  PhysicalVolume( Name               = "LAr::PSB",
                            Plates             = Plates.Horizontal, # Logical type
                            AbsorberMaterial   = "Vacuum", # absorber
                            GapMaterial        = "liquidArgon", # gap
                            NofLayers          = 1, # layers
                            AbsorberThickness  =  0.01*mm, # abso
                            GapThickness       = 1.1*cm, # gap
                            RMin               = 146*cm, # radio min,
                            RMax               = 146*cm + 1*(0.01*mm + 1.1*cm), # radio max 
                            ZSize              = ecal_barrel_z ,# z (3.4 left and 3.4 right)
                            X=0,Y=0,Z=0, # x,y,z (center in 0,0,0)
                            # Visualization
                            Visualization = True,
                            Color         = 'orange'
                          )

  emb1_pv = PhysicalVolume( Name               = "LAr::EMB1", 
                            Plates             = Plates.Horizontal, # Logical type
                            AbsorberMaterial   = "G4_Pb", # absorber
                            GapMaterial        = "liquidArgon", # gap
                            NofLayers          = 16, # layers
                            AbsorberThickness  = 1.51*mm, # abso
                            GapThickness       = 4.49*mm, # gap
                            RMin               = 150*cm, # radio min,
                            RMax               = 150*cm + 16*(1.51*mm + 4.49*mm), # radio max 
                            ZSize              = ecal_barrel_z ,# z (3.4 left and 3.4 right)
                            X=0,Y=0,Z=0, # x,y,z (center in 0,0,0)
                            Visualization = True,
                            Color         = 'aquamarine'
                          )

  emb2_pv = PhysicalVolume( Name               = "LAr::EMB2", 
                            Plates             = Plates.Horizontal, # Logical type
                            AbsorberMaterial   = "G4_Pb", # absorber
                            GapMaterial        = "liquidArgon", # gap
                            NofLayers          = 55, # layers
                            AbsorberThickness  = 1.7*mm, # abso
                            GapThickness       = 4.3*mm, # gap
                            RMin               = emb1_pv.RMax, # radio min,
                            RMax               = emb1_pv.RMax + 55*(1.7*mm + 4.3*mm), # radio max 
                            ZSize              = ecal_barrel_z ,# z (3.4 left and 3.4 right)
                            X=0,Y=0,Z=0, # x,y,z (center in 0,0,0)
                            Visualization = True,
                            Color         = 'cornflowerblue'
                          )

  emb3_pv = PhysicalVolume( Name               = "LAr::EMB3", 
                            Plates             = Plates.Horizontal, # Logical type
                            AbsorberMaterial   = "G4_Pb", # absorber
                            GapMaterial        = "liquidArgon", # gap
                            NofLayers          = 9, # layers
                            AbsorberThickness  = 1.7*mm, # abso
                            GapThickness       = 4.3*mm, # gap
                            RMin               = emb2_pv.RMax, # radio min,
                            RMax               = emb2_pv.RMax + 9*(1.7*mm + 4.3*mm), # radio max 
                            ZSize              = ecal_barrel_z ,# z (3.4 left and 3.4 right)
                            X=0,Y=0,Z=0, # x,y,z (center in 0,0,0)
                            Visualization = True,
                            Color         = 'cyan'
                          )



  # ATLAS-like barrel layers (option atlas_emb). Absorber of ATLAS (JINST 3 (2008) S08003, sec. 5.2.1): lead of 1.53 mm
  # for |eta| < 0.8 and 1.13 mm for |eta| > 0.8, two 0.2 mm stainless-steel sheets (as iron) and the glue and the readout
  # electrode as 0.832 mm of polyimide, fitted to the X0 of the accordion at eta = 0 in fig. 5.1 (22.4 X0); liquid argon of
  # 2 x 2.1 mm (sec. 5.2.2). Radial shells with a period of 6.962 mm (the accordion is not modelled); where the lead is
  # thinner the argon takes the room (the number of absorbers and the folds are fixed). The change of lead at |eta| = 0.8
  # is a cut in z at the mean radius of each layer, z = r * sinh(0.8) (about +-0.04 in eta at the inner and outer
  # radius). Layers as in the default geometry (14, 47 and 7 periods), ending at 1973.4 mm (470 mm of depth in fig. 5.4).
  if atlas_emb:
    period = 6.962*mm; abso153 = (1.53 + 0.4 + 0.832)*mm; abso113 = (1.13 + 0.4 + 0.832)*mm
    rmin = 150*cm; layers = []
    for name, nlayers, color in (("LAr::EMB1", 14, 'aquamarine'), ("LAr::EMB2", 47, 'cornflowerblue'), ("LAr::EMB3", 7, 'cyan')):
      rmax = rmin + nlayers*period
      layers.append( PhysicalVolume( Name               = name,
                                     Plates             = Plates.Horizontal,
                                     AbsorberMaterial   = "ATLAS_EMB_ABSORBER_153",
                                     GapMaterial        = "liquidArgon",
                                     NofLayers          = nlayers,
                                     AbsorberThickness  = abso153,
                                     GapThickness       = period - abso153,
                                     AbsorberSplitZ     = 0.5*(rmin + rmax)*np.sinh(0.8),
                                     AbsorberMaterial2  = "ATLAS_EMB_ABSORBER_113",
                                     AbsorberThickness2 = abso113,
                                     RMin               = rmin,
                                     RMax               = rmax,
                                     ZSize              = ecal_barrel_z,
                                     X=0,Y=0,Z=0,
                                     Visualization = True,
                                     Color         = color ) )
      rmin = rmax
    emb1_pv, emb2_pv, emb3_pv = layers

  psb_sv  = SensitiveDetector( psb_pv , DeltaEta = 0.025  , DeltaPhi = pi/32  )
  emb1_sv = SensitiveDetector( emb1_pv, DeltaEta = 0.00325, DeltaPhi = pi/32  )
  emb2_sv = SensitiveDetector( emb2_pv, DeltaEta = 0.025  , DeltaPhi = pi/128 )
  emb3_sv = SensitiveDetector( emb3_pv, DeltaEta = 0.050  , DeltaPhi = pi/128 )



  # Configure the electronic frontend and the detector parameters
  psb_det  = Calorimeter( psb_sv, -21, 3, -2, # sensitive volume, bunch start, bunch end, sampling start,
                          CollectionKey   = "Collection_PSB", # collection key
                          Detector        = Detector.TTEM, # detector type
                          Sampling        = CaloSampling.PSB, # sampling type
                          Shaper          = basepath + "/pulseLar.dat", # pulse shaper
                          Noise           = 90*MeV, # electronic noise
                          Samples         = 5, # how many samples
                          OFWeightsEnergy = [-0.0000853580,    0.265132,    0.594162,     0.389505,     0.124353], # optimal filter parameters for energy estimation
                          OFWeightsTime   = [-0.0000853580,   -12.870312690734863, -27.39136505126953, 8.075883865356445, 13.768877029418945] # EMB1 ATLAS sample to test (fake first number to add to 5) 
                        )
  # Configure the electronic frontend and the detector parameters
  emb1_det = Calorimeter( emb1_sv, -21, 3, -2, # sensitive volume, bunch start, bunch end, sampling start,
                          CollectionKey   = "Collection_EMB1", # collection key
                          Detector        = Detector.TTEM, # detector type
                          Sampling        = CaloSampling.EMB1, # sampling type
                          Shaper          = basepath + "/pulseLar.dat", # pulse shaper
                          Noise           = 26*MeV, # electronic noise
                          Samples         = 5, # how many samples
                          OFWeightsEnergy = [-0.0000853580,    0.265132,    0.594162,     0.389505,     0.124353], # optimal filter parameters for energy estimation
                          OFWeightsTime   = [-0.0000853580,   -12.870312690734863, -27.39136505126953, 8.075883865356445, 13.768877029418945] # EMB1 ATLAS sample to test (fake first number to add to 5) 
                        )
  # Configure the electronic frontend and the detector parameters
  emb2_det = Calorimeter( emb2_sv, -21, 3, -2, # sensitive volume, bunch start, bunch end, sampling start,
                          CollectionKey   = "Collection_EMB2", # collection key
                          Detector        = Detector.TTEM, # detector type
                          Sampling        = CaloSampling.EMB2, # sampling type
                          Shaper          = basepath + "/pulseLar.dat", # pulse shaper
                          Noise           = 60*MeV, # electronic noise
                          Samples         = 5, # how many samples
                          OFWeightsEnergy = [-0.0000853580,    0.265132,    0.594162,     0.389505,     0.124353], # optimal filter parameters for energy estimation
                          OFWeightsTime   = [-0.0000853580,   -12.870312690734863, -27.39136505126953, 8.075883865356445, 13.768877029418945] # EMB1 ATLAS sample to test (fake first number to add to 5) 
                        )
  # Configure the electronic frontend and the detector parameters
  emb3_det = Calorimeter( emb3_sv, -21, 3, -2, # sensitive volume, bunch start, bunch end, sampling start,
                          CollectionKey   = "Collection_EMB3", # collection key
                          Detector        = Detector.TTEM, # detector type
                          Sampling        = CaloSampling.EMB3, # sampling type
                          Shaper          = basepath + "/pulseLar.dat", # pulse shaper
                          Noise           = 40*MeV, # electronic noise
                          Samples         = 5, # how many samples
                          OFWeightsEnergy = [-0.0000853580,    0.265132,    0.594162,     0.389505,     0.124353], # optimal filter parameters for energy estimation
                          OFWeightsTime   = [-0.0000853580,   -12.870312690734863, -27.39136505126953, 8.075883865356445, 13.768877029418945] # EMB1 ATLAS sample to test (fake first number to add to 5) 
                        )


  if atlas_emb_cells:
    # ATLAS-like length and cells of the three layers (see _getAtlasEmbCellsCfg) and the ATLAS barrel presampler
    return _getAtlasPsbCfg() + _getAtlasEmbCellsCfg()
  return [psb_det, emb1_det, emb2_det, emb3_det]



# ---------------------------------------------------------------------------------------------------------------------
# ATLAS-like length and cells of the barrel EM calorimeter (option atlas_emb_cells, needs atlas_emb; simu_trf.py and
# digit_trf.py --atlas-emb-cells; off by default). F41 conserto 17 / F45.
#
# - Length: the active EM barrel of ATLAS ends at |z| = 3165 mm (ATLAS geometry database, BarrelGeometry-03, ZMAX =
#   316.5 cm, read by the ATLAS geometry as LArEMBMotherZmax, LArGeoBarrel/src/BarrelConstruction.cxx; the ATLAS
#   simulation keeps 3150 mm as fiducial limit and notes that it "should be changed in database to become 3164",
#   LArG4Barrel/src/LArBarrelGeometry.cxx). Near the inner radius the edge follows |eta| = 1.475 (BarrelGeometry-03
#   ETACUT; RMINHIGHZ = 154.8 cm), approximated by steps of one layer (one period of 6.962 mm): where r sinh(1.475) is
#   below 3165 mm at the middle radius r of a layer, the layer ends at |z| = r sinh(1.475) (the first four layers of the
#   first sampling). The three layers keep the radii, the absorbers and the change of lead of atlas_emb (same cut in z).
# - Cells: the regions of the ATLAS identifier dictionary (IdDictLArCalorimeter_DC3-05-Comm-01.xml) in each half barrel:
#   EMB1 region 0, strips of 0.003125 with indices 1-447 (the strip 0 does not exist), 64 phi slices, and region 1, three
#   cells of 0.025 in 1.4-1.475, 256 phi slices; EMB2 region 0, 56 cells of 0.025 up to 1.4, and region 1, one cell of
#   0.075 in 1.4-1.475, 256 phi slices; EMB3, 27 cells of 0.05 up to 1.35, 256 phi slices. One hit maker per sampling,
#   region and side (Segment = region; side A z > 0, side B z < 0). The cell of a step comes from the pseudorapidity of
#   its point seen from the origin, with the index formulas of the ATLAS simulation (LArBarrelGeometry.cxx,
#   CalculateIdentifier), kept only within the dictionary (CaloHitMaker::embFindCell); the eta written in the hit is the
#   nominal centre of the cell, eta0 + (i - i_min + 0.5) delta eta. The radial boundaries between the samplings that follow
#   eta and the rule of ATLAS that sends the back sampling above |eta| = 1.325 to the middle one are not modelled: the
#   sampling is the layer of atlas_emb.
# - phi: slices of 2 pi / N on the -pi..pi grid of the Lorenzetti barrel (no half-absorber shift).
# The presamplers and the volumes behind the end of the barrel: see the notes before _getAtlasPsbCfg.
#
EMB_ATLAS_Z_MAX   = 3165*mm      # BarrelGeometry-03 ZMAX 316.5 cm
EMB_ATLAS_ETA_CUT = 1.475        # BarrelGeometry-03 ETACUT
EMB_ATLAS_Z_EPS   = 1e-6*mm      # the hit makers of side A take z > EMB_ATLAS_Z_EPS, those of side B z <= -EMB_ATLAS_Z_EPS
EMB_ATLAS_RMIN    = 150*cm       # as atlas_emb
EMB_ATLAS_PERIOD  = 6.962*mm     # as atlas_emb
EMB_ATLAS_LAYERS  = ( ("LAr::EMB1", 14, 'aquamarine'), ("LAr::EMB2", 47, 'cornflowerblue'), ("LAr::EMB3", 7, 'cyan') )
#                     sampling region eta0      delta eta first last  phi slices   (identifier dictionary, per side)
EMB_ATLAS_REGIONS = [ (1,       0,     0.003125, 0.003125, 1,    447,  64 ),
                      (1,       1,     1.4,      0.025,    0,    2,    256),
                      (2,       0,     0.0,      0.025,    0,    55,   256),
                      (2,       1,     1.4,      0.075,    0,    0,    256),
                      (3,       0,     0.0,      0.05,     0,    26,   256) ]


def atlasEmbLayers():
    """(name, periods, colour, rmin, rmax, z of the change of lead) of the three layers of atlas_emb."""
    out = []; rmin = EMB_ATLAS_RMIN
    for name, n, color in EMB_ATLAS_LAYERS:
        rmax = rmin + n*EMB_ATLAS_PERIOD
        out.append( (name, n, color, rmin, rmax, 0.5*(rmin + rmax)*np.sinh(0.8)) )
        rmin = rmax
    return out


def atlasEmbLayerZ(r):
    """End in |z| of a period whose middle radius is r: 3165 mm, or r sinh(1.475) where this is smaller."""
    return min(EMB_ATLAS_Z_MAX, r*np.sinh(EMB_ATLAS_ETA_CUT))


def getAtlasEmbVolumesCfg():
    """
    Volumes of the three layers of the ATLAS-like barrel (see above): |z| up to 3165 mm, and the first periods of EMB1
    as steps that follow |eta| = 1.475. Built in place of the layers of atlas_emb; their cells come from the samplings.
    """
    abso153 = (1.53 + 0.4 + 0.832)*mm; abso113 = (1.13 + 0.4 + 0.832)*mm
    vols = []
    for name, n, color, rmin, rmax, zsplit in atlasEmbLayers():
        edges = [rmin + k*EMB_ATLAS_PERIOD for k in range(n)] + [rmax]
        groups = []   # [first period, |z| end, number of periods]
        for k in range(n):
            z = atlasEmbLayerZ(0.5*(edges[k] + edges[k+1]))
            if groups and groups[-1][1] == z: groups[-1][2] += 1
            else: groups.append([k, z, 1])
        for i, (k0, z, nk) in enumerate(groups):
            pvname = name if z == EMB_ATLAS_Z_MAX else f"{name}::Step{i+1}"
            vols.append( PhysicalVolume( Name               = pvname,
                                         Plates             = Plates.Horizontal,
                                         AbsorberMaterial   = "ATLAS_EMB_ABSORBER_153",
                                         GapMaterial        = "liquidArgon",
                                         NofLayers          = nk,
                                         AbsorberThickness  = abso153,
                                         GapThickness       = EMB_ATLAS_PERIOD - abso153,
                                         AbsorberSplitZ     = zsplit,
                                         AbsorberMaterial2  = "ATLAS_EMB_ABSORBER_113",
                                         AbsorberThickness2 = abso113,
                                         RMin               = edges[k0],
                                         RMax               = edges[k0 + nk],
                                         ZSize              = 2*z,
                                         X=0,Y=0,Z=0,
                                         Visualization = True,
                                         Color         = color ) )
    return vols


def atlasEmbCells(sampling, region, side=1):
    """
    Cell table of one region of one sampling of the ATLAS-like barrel for CaloHitMaker and CaloCellMaker: the nominal eta
    and delta eta of each cell (first to last index of the dictionary), the eta edges of the region and the sampling and
    region read by CaloHitMaker::embFindCell. side: +1 (A) or -1 (B). Returns (table, number of phi slices).
    """
    for s, reg, eta0, deta, first, last, nphi in EMB_ATLAS_REGIONS:
        if (s, reg) == (sampling, region): break
    else:
        raise RuntimeError(f"EMB{sampling} region {region}: not in the dictionary")
    # AtlasLArPart ... AtlasEtaIndex: the ATLAS identifier of the cells, for the free-running hits (F41 conserto 19); part and
    # barrel_ec also choose the point of the step for the ATLAS time of the hits (CaloHitMaker::larHitTime)
    # EmbSampSeg: the sampling of each step from the boundaries and rules of the ATLAS simulation (F41 conserto 18)
    table = dict(Names=[], Eta=[], DeltaEta=[], EmbMode=1, EmbSampling=sampling, EmbRegion=region, EmbSampSeg=True,
                 AtlasLArPart=1, AtlasBarrelEc=1 if side > 0 else -1, AtlasLArSampling=sampling, AtlasLArRegion=region,
                 AtlasEtaIndex=list(range(first, last + 1)))
    for i in range(first, last + 1):
        table['Names'].append(f"EMB{sampling}/{region}/{i}{'+' if side > 0 else '-'}")
        table['Eta'].append(side * (eta0 + deta * (i - first + 0.5))); table['DeltaEta'].append(deta)
    edges = [eta0 + deta * k for k in range(last - first + 2)]
    table['EtaEdges'] = edges if side > 0 else sorted(-e for e in edges)
    return table, nphi


def _getAtlasEmbCellsCfg():
    """Hit makers of the ATLAS-like barrel: [emb1, emb2, emb3], lists of Calorimeter, two sides each (see above)."""
    basepath = os.environ['LORENZETTI_GEOMETRY_DATA_DIR']
    noise = {1: 26*MeV, 2: 60*MeV, 3: 40*MeV}           # those of the default EMB1-3
    sampling_enum = {1: CaloSampling.EMB1, 2: CaloSampling.EMB2, 3: CaloSampling.EMB3}
    abso153 = (1.53 + 0.4 + 0.832)*mm
    out = []
    for s, (name, n, color, rmin, rmax, zsplit) in zip((1, 2, 3), atlasEmbLayers()):
        dets = []
        for sign, side_name in ((1, 'A'), (-1, 'B')):
            z0, z1 = (EMB_ATLAS_Z_EPS, EMB_ATLAS_Z_MAX) if sign > 0 else (-EMB_ATLAS_Z_MAX, -EMB_ATLAS_Z_EPS)
            # Limits of the hit makers of this sampling on this side (not built: the volumes come from
            # getAtlasEmbVolumesCfg); within them the cell comes from eta (CaloHitMaker::embFindCell).
            pv = PhysicalVolume( Name               = f"{name}::{side_name}",
                                 Plates             = Plates.Horizontal,
                                 AbsorberMaterial   = "ATLAS_EMB_ABSORBER_153",
                                 GapMaterial        = "liquidArgon",
                                 NofLayers          = n,
                                 AbsorberThickness  = abso153,
                                 GapThickness       = EMB_ATLAS_PERIOD - abso153,
                                 RMin               = rmin,
                                 RMax               = rmax,
                                 ZSize              = z1 - z0,
                                 X=0, Y=0, Z=0.5 * (z0 + z1),
                                 Visualization = False,
                                 Color         = color )
            pv.Envelope = True
            for s_, region, eta0, deta, first, last, nphi in EMB_ATLAS_REGIONS:
                if s_ != s: continue
                cells, nphi = atlasEmbCells(s, region, side=sign)
                edges = cells.pop('EtaEdges')
                lo, hi = sorted(abs(e) for e in (edges[0], edges[-1]))
                sv = SensitiveDetector( pv, EtaMin = sign*lo, EtaMax = sign*hi, Segment = region, DeltaEta = deta,
                                        DeltaPhi = 2*pi/nphi )
                if len(sv.PhiBins) - 1 != nphi:
                    raise RuntimeError(f"EMB{s} region {region}: {len(sv.PhiBins) - 1} phi slices, expected {nphi}")
                sv.EtaBins = edges; sv.EtaMin = edges[0]; sv.EtaMax = edges[-1]
                sv.Cells = cells
                atlasLArPhiShift(sv, -sign * pi / 1024)
                dets.append( Calorimeter( sv, -21, 3, -2,
                                  CollectionKey   = f"Collection_EMB{s}_{region}" + side_name,
                                  Detector        = Detector.TTEM,
                                  Sampling        = sampling_enum[s],
                                  Shaper          = basepath + "/pulseLar.dat",
                                  Noise           = noise[s],
                                  Samples         = 5,
                                  OFWeightsEnergy = [-0.0000853580,    0.265132,    0.594162,     0.389505,     0.124353],
                                  OFWeightsTime   = [-0.0000853580,   -12.870312690734863, -27.39136505126953, 8.075883865356445, 13.768877029418945]
                                ) )
        out.append(dets)
    return out





# ---------------------------------------------------------------------------------------------------------------------
# Presamplers and the end of the barrel with atlas_emb_cells (decisions of Luciano of 09/10/2026 on the items B, C and D of
# F41 conserto 17; only with the option).
#
# - Barrel presampler (C): active liquid argon of 13 mm from r = 1413.9 mm, as in the ATLAS simulation (the stack of the
#   module in LArGeoBarrel/src/BarrelPresamplerConstruction.cxx, larheight = 13 mm; LArG4Barrel findCell measures from
#   r0 = 1420.4 mm; RACTIVE of PresamplerGeometry-00 says 1413.3 mm; F41 conserto 17c, Luciano, 09/10/2026),
#   inside the ATLAS mother r = 1410-1447 mm, |z| = 3 to 3101 mm (mother of half length 1549 mm placed at z = 1549 + 3 mm,
#   LArGeoBarrel/src/BarrelCryostatConstruction.cxx). The rest of the mother (modules, motherboards) is not modelled. Cells of
#   the ATLAS identifier dictionary (LArEM-barrel-00): 61 cells of 0.025 up to 1.525, 64 phi slices, from the pseudorapidity of
#   the point seen from the origin, int(|eta|/0.025) (the ATLAS simulation finds the cell from the electrode gap in each module,
#   LArG4Barrel/src/LArBarrelPresamplerGeometry.cxx; not modelled).
# - End-cap presampler (D): liquid argon of 4 mm at |z| = 3622-3626 mm, r = 1231.74-1701.98 mm (PresamplerPosition-00 ZPOS
#   362.4 cm, TCK 0.4 cm, RMIN, RMAX; zEndcapPresamplerFrontFace and BackFace in LArG4EC/src/PresamplerGeometry.cc), in a cavity
#   of DM::Crack::EM (see geometry/python/v1/DeadMaterials.py). Cells as in the ATLAS simulation (PresamplerGeometry.cc,
#   CalculateIdentifier): etaBin = int(eta * 40 - 60), 12 -> 11 below 1.801, 0-11 (1.5-1.8), 64 phi slices.
# - Behind the end of the barrel (B): liquid argon from |z| = 3165 to 3205 mm in r = 1500-1980 mm and in the corner of the steps
#   of EMB1 (between the end of each step and 3165 mm); the mixture LArElectronics (1.58 g/cm3; copper 0.13, kapton 0.07, argon
#   0.80 in mass; LArMaterials-12) from 3205 to 3267 mm in r = 1565.5-2140 mm (CryoCylinders-09, Barrel::TotalLAr cylinder 21),
#   up to 1980 mm without atlas_barrel_cryostat; the conical part of the cold wall (CryoPcons-18, Barrel::OuterWall planes 26-27:
#   z 3101 -> 3267 mm, inner radius 1356.72 -> 1537.22 mm, outer 1385 -> 1565.5 mm, aluminium) in steps of z with the radii of the
#   cone at the middle of each step; with atlas_barrel_cryostat, the end wall of the cold vessel extended down to r = 1565.5 mm
#   (Barrel::OuterWall planes 27-30: z 3267-3287 mm).
#
PSB_ATLAS_R_ACTIVE  = 1413.9*mm     # inner radius of the active argon in the ATLAS simulation (BarrelPresamplerConstruction.cxx; findCell uses r0 = 1420.4 mm); RACTIVE of PresamplerGeometry-00 is 1413.3 mm
PSB_ATLAS_ACTIVE    = 13.0*mm       # PresamplerGeometry-00 HACTIVE; larheight in BarrelPresamplerConstruction.cxx
PSB_ATLAS_Z         = (3.0*mm, 3101.0*mm)
PSE_ATLAS_R         = (1231.74*mm, 1701.98*mm)   # PresamplerPosition-00 RMIN, RMAX
PSE_ATLAS_Z         = (3622.0*mm, 3626.0*mm)     # PresamplerPosition-00 ZPOS -+ TCK/2
EMB_ATLAS_END_LAR_Z = 3205.0*mm                  # CryoCylinders-09 cylinder 21 ZMIN 320.5 cm
EMB_ATLAS_END_Z     = 3267.0*mm                  # ZMIN + DZ (326.7 cm), cold wall (CryoPcons-18)
EMB_ATLAS_ELEC_RMIN = 1565.5*mm                  # RMIN 156.55 cm
EMB_ATLAS_ELEC_RMAX = 2140.0*mm                  # RMIN + DR (214.0 cm)
EMB_ATLAS_DEAD_RMAX = 1980.0*mm                  # up to the dead argon of the barrel cryostat (1980.05 mm)
EMB_ATLAS_CONE      = ((3101.0*mm, 1356.72*mm, 1385.0*mm), (3267.0*mm, 1537.22*mm, 1565.5*mm))   # (z, rmin, rmax)
EMB_ATLAS_CONE_STEPS = 12                        # steps of 13.83 mm in z (see the report of conserto 17)
EMB_ATLAS_COLD_WALL = (3267.0*mm, 3287.0*mm)     # Barrel::OuterWall planes 28-29
EMB_ATLAS_COLD_WALL_RMIN = 1565.5*mm             # plane 29


def _slab(name, plates, material, rmin, rmax, z0, z1, color='gray', dead=True):
    """One volume of a single material (absorber and gap both of it, half of the thickness each)."""
    t = (rmax - rmin) if plates == Plates.Horizontal else (z1 - z0)
    pv = PhysicalVolume( Name               = name,
                         Plates             = plates,
                         AbsorberMaterial   = material,
                         GapMaterial        = material,
                         NofLayers          = 1,
                         AbsorberThickness  = t/2,
                         GapThickness       = t/2,
                         RMin               = rmin,
                         RMax               = rmax,
                         ZSize              = z1 - z0,
                         X=0,Y=0,Z=0.5*(z0 + z1),
                         Visualization = True,
                         Color         = color )
    if dead: pv.Cuts = ProductionCuts(ElectronCut = 1, PositronCut = 1, GammaCut = 1)
    return pv


def _presamplerCalorimeter(pv, sign, side_name, sampling, eta0, ncells, emb_mode, key, noise):
    basepath = os.environ['LORENZETTI_GEOMETRY_DATA_DIR']
    deta = 0.025
    # ATLAS identifier (F41 conserto 19): barrel presampler = LArEM barrel_ec +-1, end-cap presampler = +-2; sampling 0,
    # region 0, eta index 0 to ncells - 1
    barrel = emb_mode != 2
    cells = dict(Names=[], Eta=[], DeltaEta=[], EmbMode=emb_mode, EmbSampling=0, EmbRegion=0,
                 AtlasLArPart=1, AtlasBarrelEc=sign * (1 if barrel else 2), AtlasLArSampling=0, AtlasLArRegion=0,
                 AtlasEtaIndex=list(range(ncells)))
    for i in range(ncells):
        cells['Names'].append(f"{key}/0/{i}{'+' if sign > 0 else '-'}")
        cells['Eta'].append(sign * (eta0 + deta * (i + 0.5))); cells['DeltaEta'].append(deta)
    edges = [eta0 + deta * k for k in range(ncells + 1)]
    edges = edges if sign > 0 else sorted(-e for e in edges)
    lo, hi = sorted(abs(e) for e in (edges[0], edges[-1]))
    sv = SensitiveDetector( pv, EtaMin = sign*lo, EtaMax = sign*hi, Segment = 0, DeltaEta = deta, DeltaPhi = 2*pi/64 )
    if len(sv.PhiBins) - 1 != 64:
        raise RuntimeError(f"{key}: {len(sv.PhiBins) - 1} phi slices, expected 64")
    sv.EtaBins = edges; sv.EtaMin = edges[0]; sv.EtaMax = edges[-1]
    sv.Cells = cells
    # no phi shift on the presamplers (F41 medida 30b/30c, 16/10/2026): in the ATLAS simulation (Athena 23.0.14, Sim_tf with 2 TeV
    # muons) the barrel and end-cap presampler phi edges are at k pi/32 on both sides; the half-absorber shift of the readout
    # geometry (conserto 19) holds for the accordion middle layers, not here
    atlasLArPhiShift(sv, 0.0)
    return Calorimeter( sv, -21, 3, -2,
                        CollectionKey   = f"Collection_{key}_0" + side_name,
                        Detector        = Detector.TTEM,
                        Sampling        = sampling,
                        Shaper          = basepath + "/pulseLar.dat",
                        Noise           = noise,
                        Samples         = 5,
                        OFWeightsEnergy = [-0.0000853580,    0.265132,    0.594162,     0.389505,     0.124353],
                        OFWeightsTime   = [-0.0000853580,   -12.870312690734863, -27.39136505126953, 8.075883865356445, 13.768877029418945] )


# The eight modules of the ATLAS barrel presampler (LArGeoBarrel/src/BarrelPresamplerConstruction.cxx, mod[8][6]: length,
# anodes, cathodes, tilt in degrees, pitch, position of the first cathode; LArG4Barrel/src/LArBarrelPresamplerGeometry.cxx for
# the positions in z, with the contraction cmm and the safety eps of the code). F41 conserto 17c, choice 3, 09/10/2026.
PSB_ATLAS_MODULES = ((286.4, 56, 56, -25., 4.987, 4.2), (295.74, 64, 64, -12., 4.621, 0.3), (321.1, 72, 72, 0., 4.46, 0.9),
                     (356.8, 80, 80, 0., 4.46, 0.9), (404.8, 88, 88, 0., 4.6, 0.9), (478.4, 104, 104, 0., 4.6, 0.95),
                     (563.2, 128, 128, 0., 4.4, 1.05), (380.6, 86, 87, 0., 4.4, 0.95))
PSB_ATLAS_CMM, PSB_ATLAS_EPS = 1 - 0.0026, 0.007*mm
PSB_ATLAS_CATHODE, PSB_ATLAS_ANODE = 0.270*mm, 0.330*mm
# mean electrode: LAr::CathodeMat (3.73 g/cm3) and LAr::AnodeMat (3.06 g/cm3) of the public GeoModel geometry, 0.27 : 0.33 in volume
ATLAS_PS_ELECTRODE_MIXTURE = {"ATLAS_PS_ELECTRODE": (3.361505, {"Cu": 0.551755, "H": 0.036312, "C": 0.247256, "O": 0.164677})}


def atlasPsbModules():
    """Per module (|z| in mm): start, end, first cathode, pitch, tilt (rad), cathodes, anodes, as in the ATLAS simulation."""
    cmm, eps = PSB_ATLAS_CMM, PSB_ATLAS_EPS
    out = []; end = PSB_ATLAS_Z[0]
    for i, (length, nano, ncat, tilt, pitch, first) in enumerate(PSB_ATLAS_MODULES):
        start = end
        end = (length*cmm + 2*eps) + start + eps
        out.append(dict(start=start, end=end, first=start + first*cmm + PSB_ATLAS_CATHODE*cmm/2 + 2*eps, pitch=pitch*cmm,
                        tilt=np.radians(tilt), ncat=int(ncat), nano=int(nano)))
    return out


def getAtlasPsbVolumesCfg():
    """The modules of the ATLAS barrel presampler, both sides: plates of the mean electrode, vertical where the electrodes
    cross the middle of the active layer, period half a pitch (cathode, anode, ...), thickness / cos(tilt); liquid argon of
    the active layer between them (see above)."""
    vols = []
    r0, r1 = PSB_ATLAS_R_ACTIVE, PSB_ATLAS_R_ACTIVE + PSB_ATLAS_ACTIVE
    mods = atlasPsbModules()
    for sign, side_name in ((1, 'A'), (-1, 'B')):
        def place(name, plates, z0, z1, **kw):
            za, zb = (z0, z1) if sign > 0 else (-z1, -z0)
            if plates is None or plates == "electrode":
                pv = _slab(f"LAr::PSB::{side_name}::{name}", Plates.Vertical,
                           "liquidArgon" if plates is None else "ATLAS_PS_ELECTRODE", r0, r1, za, zb, color='orange', dead=False)
            else:
                pv = PhysicalVolume( Name = f"LAr::PSB::{side_name}::{name}", Plates = Plates.Vertical,
                                     AbsorberMaterial = "ATLAS_PS_ELECTRODE", GapMaterial = "liquidArgon",
                                     RMin = r0, RMax = r1, ZSize = zb - za, X=0,Y=0,Z=0.5*(za + zb), Visualization = True,
                                     Color = 'orange', **kw )
            vols.append(pv)
        z = PSB_ATLAS_Z[0]
        for i, md in enumerate(mods):
            t = 0.5*(PSB_ATLAS_CATHODE + PSB_ATLAS_ANODE)*PSB_ATLAS_CMM/np.cos(md['tilt'])
            half = md['pitch']/2; n = md['ncat'] + md['nano']
            # the first cathode is a plate of its own; then n - 1 layers of half a pitch, in which the gap comes first and the
            # absorber sits at the far end (CreateVerticalPlates), so that each absorber is centred on its electrode. (Starting
            # the layers before the first cathode would cross into the previous module, where the space is < half a pitch.)
            zc0 = md['first'] - t/2
            if zc0 < z - 1e-9:
                raise RuntimeError(f"PSB module {i}: first cathode before the previous volume")
            if zc0 > z: place(f"Gap{i}", None, z, zc0)
            place(f"Cathode{i}", "electrode", zc0, zc0 + t)
            zp0 = zc0 + t
            place(f"Module{i}", True, zp0, zp0 + (n - 1)*half, NofLayers = n - 1, AbsorberThickness = t, GapThickness = half - t)
            z = zp0 + (n - 1)*half
        place("Gap8", None, z, PSB_ATLAS_Z[1])
    return vols


def _getAtlasPsbCfg():
    """Barrel presampler as in ATLAS, one hit maker per side (see above). The noise is that of the default presampler. The
    volume of the maker is an envelope (not built): the modules are built by getAtlasPsbVolumesCfg, and the cell comes from
    the gap of the electrode (EmbMode = 3, CaloHitMaker::embFindCell; F41 conserto 17c, choice 3)."""
    dets = []
    for sign, side_name in ((1, 'A'), (-1, 'B')):
        z0, z1 = PSB_ATLAS_Z if sign > 0 else (-PSB_ATLAS_Z[1], -PSB_ATLAS_Z[0])
        pv = _slab(f"LAr::PSB::{side_name}", Plates.Horizontal, "liquidArgon", PSB_ATLAS_R_ACTIVE,
                   PSB_ATLAS_R_ACTIVE + PSB_ATLAS_ACTIVE, z0, z1, color='orange', dead=False)
        pv.Envelope = True
        det = _presamplerCalorimeter(pv, sign, side_name, CaloSampling.PSB, 0.0, 61, 3, "PSB", 90*MeV)
        det.sensitive().Cells['PsbR0'] = PSB_ATLAS_R_ACTIVE + PSB_ATLAS_ACTIVE/2
        dets.append( det )
    return dets


def getAtlasPseCfg(left_side=False):
    """End-cap presampler as in ATLAS on one side (see above); its cavity in DM::Crack::EM is in DeadMaterials.py."""
    sign = -1 if left_side else 1
    side_name = 'B' if left_side else 'A'
    z0, z1 = PSE_ATLAS_Z if sign > 0 else (-PSE_ATLAS_Z[1], -PSE_ATLAS_Z[0])
    pv = _slab(f"LAr::PSE::{side_name}", Plates.Vertical, "liquidArgon", PSE_ATLAS_R[0], PSE_ATLAS_R[1], z0, z1,
               color='orange', dead=False)
    return [ _presamplerCalorimeter(pv, sign, side_name, CaloSampling.PSE, 1.5, 12, 2, "PSE", 26*MeV) ]


def atlasEmbConeSteps():
    """(z start, z end, rmin, rmax) of the steps of the conical cold wall: the radii of the cone at the middle of each step."""
    (za, ria, roa), (zb, rib, rob) = EMB_ATLAS_CONE
    dz = (zb - za) / EMB_ATLAS_CONE_STEPS; out = []
    for k in range(EMB_ATLAS_CONE_STEPS):
        z0 = za + k*dz; z1 = za + (k + 1)*dz if k < EMB_ATLAS_CONE_STEPS - 1 else zb
        f = (0.5*(z0 + z1) - za) / (zb - za)
        out.append( (z0, z1, ria + f*(rib - ria), roa + f*(rob - roa)) )
    return out


def getAtlasEmbEndCfg(atlas_barrel_cryostat=False, atlas_barrel_front=False):
    """Volumes behind the end of the ATLAS-like barrel, both sides (see above). With atlas_barrel_front (the ATLAS pieces in
    front of the accordion, DeadMaterials.getAtlasBarrelFrontCfg) the conical cold wall is the exact cone of that front, not
    the steps here, and the corner of the steps of EMB1 holds the high-eta cables of ATLAS (TELB, LAr::Cables, a cone from
    z = 3110.1 mm at r = 1500 mm to z = 3165 mm at r = 1546.63 mm; BarrelConstruction.cxx and the public GeoModel geometry)
    instead of liquid argon (F41 conserto 17c)."""
    vols = []
    steps = [v for v in getAtlasEmbVolumesCfg() if "::Step" in v.Name]
    for sign, side_name in ((1, 'A'), (-1, 'B')):
        def add(name, plates, material, rmin, rmax, z0, z1):
            za, zb = (z0, z1) if sign > 0 else (-z1, -z0)
            vols.append( _slab(f"DM::EMBEnd::{name}::{side_name}", plates, material, rmin, rmax, za, zb) )
        add("LAr", Plates.Vertical, "liquidArgon", EMB_ATLAS_RMIN, EMB_ATLAS_DEAD_RMAX, EMB_ATLAS_Z_MAX, EMB_ATLAS_END_LAR_Z)
        for v in steps:
            if atlas_barrel_front:
                add("CornerCables" + v.Name.split("::Step")[1], Plates.Vertical, "ATLAS_LAR_CABLES", v.RMin, v.RMax, v.ZSize/2,
                    EMB_ATLAS_Z_MAX)
            else:
                add("CornerLAr" + v.Name.split("::Step")[1], Plates.Vertical, "liquidArgon", v.RMin, v.RMax, v.ZSize/2,
                    EMB_ATLAS_Z_MAX)
        add("Electronics", Plates.Vertical, "ATLAS_LAR_ELECTRONICS", EMB_ATLAS_ELEC_RMIN,
            EMB_ATLAS_ELEC_RMAX if atlas_barrel_cryostat else EMB_ATLAS_DEAD_RMAX, EMB_ATLAS_END_LAR_Z, EMB_ATLAS_END_Z)
        for k, (z0, z1, r0, r1) in enumerate([] if atlas_barrel_front else atlasEmbConeSteps()):
            add(f"ColdCone{k+1}", Plates.Vertical, "G4_Al", r0, r1, z0, z1)
        if atlas_barrel_cryostat and not atlas_barrel_front:   # with the front, the end wall comes from the cryostat pieces
            add("ColdEndWall", Plates.Vertical, "G4_Al", EMB_ATLAS_COLD_WALL_RMIN, EMB_ATLAS_DEAD_RMAX,
                EMB_ATLAS_COLD_WALL[0], EMB_ATLAS_COLD_WALL[1])
    return vols
