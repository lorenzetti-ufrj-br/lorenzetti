
__all__ = ["getLArEMECCfg", "getAtlasEmecVolumesCfg", "atlasEmecRings", "atlasEmecCompartmentCells"]

from GaugiKernel.constants import mm,MeV,pi
from CaloCell.CaloDefs import Detector, CaloSampling

from .Calorimeter import Calorimeter
from .PhysicalVolume import PhysicalVolume, Plates
from .SensitiveDetector import SensitiveDetector, atlasLArPhiShift


import os
import math




def getLArEMECCfg(left_side=False, atlas_emec=False):
    """
    EM end-cap and end-cap presampler of one side.

    Args:
        left_side (bool): If True, the B side (negative z).
        atlas_emec (bool): If True, the EMEC as in ATLAS (two wheels, nominal z, composition and cells of ATLAS; see
                           _getAtlasEmecCfg and the notes below). Its volumes come from getAtlasEmecVolumesCfg. The
                           presampler keeps its segmentation and goes to just in front of the EMEC (provisional).
                           Off by default: the default EMEC is unchanged.
    """

    sign = -1 if left_side else 1
    side_name = 'B' if left_side else 'A'
    basepath = os.environ['LORENZETTI_GEOMETRY_DATA_DIR']

    endcap_start    = 3704.*mm
    ps_endcap_start = endcap_start + 31*mm
    if atlas_emec:
        # PROVISIONAL position (F41 conserto 16): with the ATLAS-like EMEC the presampler is moved to just in front of
        # the EMEC face, with the same thickness and radii and the same segmentation rule; at its default place
        # (3735-3740 mm) it would be inside the new EMEC. Its position as in ATLAS is left for a later change.
        ps_endcap_start = EMEC_ATLAS_Z_FRONT - (0.01*mm + 4.99*mm)


    #
    # PSE
    #
    pse_pv      =  PhysicalVolume( Name               = "LAr::PSE::"+side_name, 
                                   Plates             = Plates.Vertical, # Logical type
                                   AbsorberMaterial   = "Vacuum", # absorber
                                   GapMaterial        = "liquidArgon", # gap
                                   NofLayers          = 1, # 16s
                                   AbsorberThickness  = 0.01*mm, # abso
                                   GapThickness       = 4.99*mm, # gap
                                   RMin               = 1232*mm, # radio min,
                                   RMax               = 1700*mm, # radio max 
                                   ZSize              = 1*(0.01*mm + 4.99*mm) ,
                                   X=0,Y=0,Z=sign*(ps_endcap_start + 0.5*(1*(0.01*mm + 4.99*mm))), # x,y,z 
                                   Visualization = True,
                                   Color         = 'orange'
                                )


    pde_sv = SensitiveDetector( pse_pv, DeltaEta = 0.025  , DeltaPhi = pi/32  )


    # Configure the electronic frontend and the detector parameters
    pse_det  = Calorimeter( pde_sv, -21, 3, -2, # sensitive volume, bunch start, bunch end, sampling start,
                        CollectionKey   = "Collection_PSE_"+ side_name, # collection key
                        Detector        = Detector.TTEM, # detector type
                        Sampling        = CaloSampling.PSE, # sampling type
                        Shaper          = basepath + "/pulseLar.dat", # pulse shaper
                        Noise           = 26*MeV, # electronic noise
                        Samples         = 5, # how many samples
                        OFWeightsEnergy = [-0.0000853580,    0.265132,    0.594162,     0.389505,     0.124353], # optimal filter parameters for energy estimation
                        OFWeightsTime   = [-0.0000853580,   -12.870312690734863, -27.39136505126953, 8.075883865356445, 13.768877029418945] # EMB1 ATLAS sample to test (fake first number to add to 5) 
                        
                      )



    if atlas_emec:
        return [[pse_det]] + _getAtlasEmecCfg(left_side)

    #
    # EMEC1
    #
    nlayers = 16; absorber=2.27*mm; gap=3.73*mm; zsize=nlayers*(absorber+gap)
    emec1_pv   =  PhysicalVolume( Name               = "LAr::EMEC1::"+side_name, 
                                  Plates             = Plates.Vertical, # Logical type
                                  AbsorberMaterial   = "G4_Pb", # absorber
                                  GapMaterial        = "liquidArgon", # gap
                                  NofLayers          = nlayers, # 16s (max 16)
                                  AbsorberThickness  = absorber, # abso
                                  GapThickness       = gap, # gap
                                  RMin               = 302*mm,# radio min,
                                  RMax               = 2042*mm,# radio max 
                                  ZSize              = zsize,
                                  X=0, Y=0, Z= (pse_pv.ZMin - zsize/2) if left_side else (pse_pv.ZMax + zsize/2),
                                  Visualization = True,
                                  Color         = 'aquamarine'
                              ) 

    emec1_sv0 = SensitiveDetector( emec1_pv, EtaMax = sign*1.80                           , Segment = 0, DeltaEta = 0.00325, DeltaPhi = pi/32 )
    emec1_sv1 = SensitiveDetector( emec1_pv, EtaMin = emec1_sv0.EtaMax, EtaMax = sign*2.00, Segment = 1, DeltaEta = 0.025  , DeltaPhi = pi/32 )
    emec1_sv2 = SensitiveDetector( emec1_pv, EtaMin = emec1_sv1.EtaMax, EtaMax = sign*2.37, Segment = 2, DeltaEta = 0.006  , DeltaPhi = pi/32 )
    emec1_sv3 = SensitiveDetector( emec1_pv, EtaMin = emec1_sv2.EtaMax                    , Segment = 3, DeltaEta = 0.1    , DeltaPhi = pi/32 )

    # Configure the electronic frontend and the detector parameters
    emec1_det0  = Calorimeter( emec1_sv0, -21, 3, -2, # sensitive volume, bunch start, bunch end, sampling start,
                              CollectionKey   = "Collection_EMEC1_0" + side_name, # collection key
                              Detector        = Detector.TTEM, # detector type
                              Sampling        = CaloSampling.EMEC1, # sampling type
                              Shaper          = basepath + "/pulseLar.dat", # pulse shaper
                              Noise           = 26*MeV, # electronic noise
                              Samples         = 5, # how many samples
                              OFWeightsEnergy = [-0.0000853580,    0.265132,    0.594162,     0.389505,     0.124353], # optimal filter parameters for energy estimation
                              OFWeightsTime   = [-0.0000853580,   -12.870312690734863, -27.39136505126953, 8.075883865356445, 13.768877029418945] # EMB1 ATLAS sample to test (fake first number to add to 5) 
                            )
    # Configure the electronic frontend and the detector parameters
    emec1_det1  = Calorimeter( emec1_sv1, -21, 3, -2, # sensitive volume, bunch start, bunch end, sampling start,
                              CollectionKey   = "Collection_EMEC1_1"+ side_name, # collection key
                              Detector        = Detector.TTEM, # detector type
                              Sampling        = CaloSampling.EMEC1, # sampling type
                              Shaper          = basepath + "/pulseLar.dat", # pulse shaper
                              Noise           = 26*MeV, # electronic noise
                              Samples         = 5, # how many samples
                              OFWeightsEnergy = [-0.0000853580,    0.265132,    0.594162,     0.389505,     0.124353], # optimal filter parameters for energy estimation
                              OFWeightsTime   = [-0.0000853580,   -12.870312690734863, -27.39136505126953, 8.075883865356445, 13.768877029418945] # EMB1 ATLAS sample to test (fake first number to add to 5) 
                            )
    # Configure the electronic frontend and the detector parameters
    emec1_det2  = Calorimeter( emec1_sv2, -21, 3, -2, # sensitive volume, bunch start, bunch end, sampling start,
                              CollectionKey   = "Collection_EMEC1_2"+ side_name, # collection key
                              Detector        = Detector.TTEM, # detector type
                              Sampling        = CaloSampling.EMEC1, # sampling type
                              Shaper          = basepath + "/pulseLar.dat", # pulse shaper
                              Noise           = 26*MeV, # electronic noise
                              Samples         = 5, # how many samples
                              OFWeightsEnergy = [-0.0000853580,    0.265132,    0.594162,     0.389505,     0.124353], # optimal filter parameters for energy estimation
                              OFWeightsTime   = [-0.0000853580,   -12.870312690734863, -27.39136505126953, 8.075883865356445, 13.768877029418945] # EMB1 ATLAS sample to test (fake first number to add to 5) 
                            )
    # Configure the electronic frontend and the detector parameters
    emec1_det3  = Calorimeter( emec1_sv3, -21, 3, -2, # sensitive volume, bunch start, bunch end, sampling start,
                              CollectionKey   = "Collection_EMEC1_3"+ side_name, # collection key
                              Detector        = Detector.TTEM, # detector type
                              Sampling        = CaloSampling.EMEC1, # sampling type
                              Shaper          = basepath + "/pulseLar.dat", # pulse shaper
                              Noise           = 26*MeV, # electronic noise
                              Samples         = 5, # how many samples
                              OFWeightsEnergy = [-0.0000853580,    0.265132,    0.594162,     0.389505,     0.124353], # optimal filter parameters for energy estimation
                              OFWeightsTime   = [-0.0000853580,   -12.870312690734863, -27.39136505126953, 8.075883865356445, 13.768877029418945] # EMB1 ATLAS sample to test (fake first number to add to 5) 
                            )


    #
    # EMEC2
    #
    nlayers=55; absorber=2.27*mm; gap=3.73*mm; zsize=nlayers*(absorber+gap)
    emec2_pv   =  PhysicalVolume( Name               = "LAr::EMEC2::"+side_name, 
                                  Plates             = Plates.Vertical, # Logical type
                                  AbsorberMaterial   = "G4_Pb", # absorber
                                  GapMaterial        = "liquidArgon", # gap
                                  NofLayers          = nlayers, # 16s (max 16)
                                  AbsorberThickness  = absorber, # abso
                                  GapThickness       = gap, # gap
                                  RMin               = 302*mm,# radio min,
                                  RMax               = 2042*mm,# radio max 
                                  ZSize              = zsize ,
                                  X=0,Y=0,Z=(emec1_pv.ZMin - zsize/2) if left_side else (emec1_pv.ZMax + zsize/2), # x,y,z 
                                  Visualization = True,
                                  Color         = 'cornflowerblue'
                              ) 
 
    emec2_sv0 = SensitiveDetector( emec2_pv, EtaMax = sign*2.50                    , Segment = 0, DeltaEta = 0.025, DeltaPhi = pi/128 )
    emec2_sv1 = SensitiveDetector( emec2_pv, EtaMin = emec2_sv0.EtaMax             , Segment = 1, DeltaEta = 0.1  , DeltaPhi = pi/32  )


    # Configure the electronic frontend and the detector parameters
    emec2_det0  = Calorimeter( emec2_sv0, -21, 3, -2, # sensitive volume, bunch start, bunch end, sampling start,
                              CollectionKey   = "Collection_EMEC2_0" + side_name, # collection key
                              Detector        = Detector.TTEM, # detector type
                              Sampling        = CaloSampling.EMEC2, # sampling type
                              Shaper          = basepath + "/pulseLar.dat", # pulse shaper
                              Noise           = 60*MeV, # electronic noise
                              Samples         = 5, # how many samples
                              OFWeightsEnergy = [-0.0000853580,    0.265132,    0.594162,     0.389505,     0.124353], # optimal filter parameters for energy estimation
                              OFWeightsTime   = [-0.0000853580,   -12.870312690734863, -27.39136505126953, 8.075883865356445, 13.768877029418945] # EMB1 ATLAS sample to test (fake first number to add to 5) 
                            )
    # Configure the electronic frontend and the detector parameters
    emec2_det1  = Calorimeter( emec2_sv1, -21, 3, -2, # sensitive volume, bunch start, bunch end, sampling start,
                              CollectionKey   = "Collection_EMEC2_1"+ side_name, # collection key
                              Detector        = Detector.TTEM, # detector type
                              Sampling        = CaloSampling.EMEC2, # sampling type
                              Shaper          = basepath + "/pulseLar.dat", # pulse shaper
                              Noise           = 60*MeV, # electronic noise
                              Samples         = 5, # how many samples
                              OFWeightsEnergy = [-0.0000853580,    0.265132,    0.594162,     0.389505,     0.124353], # optimal filter parameters for energy estimation
                              OFWeightsTime   = [-0.0000853580,   -12.870312690734863, -27.39136505126953, 8.075883865356445, 13.768877029418945] # EMB1 ATLAS sample to test (fake first number to add to 5) 
                            )





    #
    # EMEC3
    #
    nlayers=9; absorber=2.41*mm; gap=3.59*mm; zsize=nlayers*(absorber+gap)
    emec3_pv   =  PhysicalVolume( Name               = "LAr::EMEC3::"+side_name, 
                                  Plates             = Plates.Vertical, # Logical type
                                  AbsorberMaterial   = "G4_Pb", # absorber
                                  GapMaterial        = "liquidArgon", # gap
                                  NofLayers          = nlayers, # 16s (max 16)
                                  AbsorberThickness  = absorber, # abso
                                  GapThickness       = gap, # gap
                                  RMin               = 302*mm,# radio min,
                                  RMax               = 2042*mm,# radio max 
                                  ZSize              = zsize ,
                                  X=0,Y=0,Z=(emec2_pv.ZMin - zsize/2) if left_side else (emec2_pv.ZMax + zsize/2), # x,y,z 
                                  Visualization = True,
                                  Color         = 'cyan'
                              ) 
 
    emec3_sv0 = SensitiveDetector( emec3_pv, EtaMax = sign*2.50                    , Segment = 0, DeltaEta = 0.050 , DeltaPhi = pi/128 )
    emec3_sv1 = SensitiveDetector( emec3_pv, EtaMin = emec3_sv0.EtaMax             , Segment = 1, DeltaEta = 0.1   , DeltaPhi = pi/32 )


    # Configure the electronic frontend and the detector parameters
    emec3_det0  = Calorimeter( emec3_sv0, -21, 3, -2, # sensitive volume, bunch start, bunch end, sampling start,
                              CollectionKey   = "Collection_EMEC3_0" + side_name, # collection key
                              Detector        = Detector.TTEM, # detector type
                              Sampling        = CaloSampling.EMEC3, # sampling type
                              Shaper          = basepath + "/pulseLar.dat", # pulse shaper
                              Noise           = 40*MeV, # electronic noise
                              Samples         = 5, # how many samples
                              OFWeightsEnergy = [-0.0000853580,    0.265132,    0.594162,     0.389505,     0.124353], # optimal filter parameters for energy estimation
                              OFWeightsTime   = [-0.0000853580,   -12.870312690734863, -27.39136505126953, 8.075883865356445, 13.768877029418945] # EMB1 ATLAS sample to test (fake first number to add to 5) 
                            )
    # Configure the electronic frontend and the detector parameters
    emec3_det1  = Calorimeter( emec3_sv1, -21, 3, -2, # sensitive volume, bunch start, bunch end, sampling start,
                              CollectionKey   = "Collection_EMEC3_1"+ side_name, # collection key
                              Detector        = Detector.TTEM, # detector type
                              Sampling        = CaloSampling.EMEC3, # sampling type
                              Shaper          = basepath + "/pulseLar.dat", # pulse shaper
                              Noise           = 40*MeV, # electronic noise
                              Samples         = 5, # how many samples
                              OFWeightsEnergy = [-0.0000853580,    0.265132,    0.594162,     0.389505,     0.124353], # optimal filter parameters for energy estimation
                              OFWeightsTime   = [-0.0000853580,   -12.870312690734863, -27.39136505126953, 8.075883865356445, 13.768877029418945] # EMB1 ATLAS sample to test (fake first number to add to 5) 
                            )

    pse   = [pse_det]
    emec1 = [emec1_det0, emec1_det1, emec1_det2, emec1_det3]
    emec2 = [emec2_det0, emec2_det1]
    emec3 = [emec3_det0, emec3_det1]

    return [pse,emec1,emec2,emec3]



# ---------------------------------------------------------------------------------------------------------------------
# ATLAS-like EM end-cap (option atlas_emec; simu_trf.py and digit_trf.py --atlas-emec; off by default).
#
# Nominal values of the ATLAS EMEC, without the shift of the installed detector (ZSHIFT of the table EmecGeometry, 40 or
# 45 mm, left out on purpose). Sources: JINST 3 (2008) S08003, sec. 5.2 (pdf pages 144, 147, 149); the LAr TDR
# (CERN/LHCC 96-41, pdf pages 206, 207, 253, 257); the ATLAS simulation (Athena, LArCalorimeter/LArG4/LArG4EC/src/
# EnergyCalculator.cc, FindIdentifier_Default and the table s_geometry; DetectorDescription/GeoModel/GeoSpecialShapes/
# src/LArWheelCalculator.cxx; LArCalorimeter/LArGeoModel/LArGeoEndcap/src/EMECConstruction.cxx) and the ATLAS geometry
# database (tables EmecGeometry-00, EmecSamplingSep-00, EmecWheelParameters-00).
#
# - Two wheels per side. Front face of the active part at z = 3702 mm (dMechFocaltoWRP 3691 mm + dWRPtoFrontFace 11 mm,
#   LArWheelCalculator.cxx; Z1 = 369.1 cm in EmecGeometry), 514 mm thick (WheelThickness, LArWheelCalculator.cxx; lead
#   width of TDR table 7-3), back at 4216 mm. Outer wheel 1.375 < eta < 2.5 up to r = 2034 mm (RLIMIT 203.4 cm); inner
#   wheel 2.5 < eta < 3.2; 3 mm between the wheels at eta = 2.5, 1.5 mm on each side of the cone (DCRACK 0.15 cm, used as
#   halfGapBetweenWheels in EMECConstruction.cxx; JINST pdf 147). Side B mirrored.
# - The cones (eta = 1.375, 2.5, 3.2) are measured from the electric focal point, 2 mm in front of the mechanical one
#   (dMechFocaltoWRP - dElecFocaltoWRP = 3691 - 3689 mm, LArWheelCalculator.cxx; Z1 - DCF of EmecGeometry; inference),
#   and approximated by steps: radial bands of 100 mm (on the grid r = 100 k mm, cut by the radial range of the wheel)
#   and, in the bands that a cone crosses, 20 slices of 25.7 mm in z, each a ring whose edge is the radius of the cone
#   in the middle of the slice. The other bands take the whole depth.
# - Composition: each band is made of layers normal to z, [equivalent absorber + liquid argon 2 g(r)], with g the gap on
#   each side of the electrode at the middle radius of the band. The equivalent absorber is a homogeneous mixture with
#   the masses per unit area of ATLAS (as the barrel absorber of conserto 12): lead 1.7 mm (outer wheel) or 2.2 mm (inner)
#   (JINST pdf 144; TDR table 7-3), two 0.2 mm stainless-steel sheets taken as iron (TDR pdf 253; JINST pdf 144), two
#   0.15 mm prepreg sheets taken as polyimide (TDR pdf 253) and the readout electrode of 0.275 mm (TDR fig. 6-16, pdf 207:
#   three copper layers of 35 um, 105 um of copper, and 170 um of polyimide and glue, taken as polyimide; the end-cap
#   electrodes are like those of the barrel, TDR sec. 7.3.1). The gap is linear in r (inference from JINST pdf 149, the
#   gap grows with the radius): outer wheel from 0.9 mm at the radius of the eta = 2.5 cone at mid depth to 2.8 mm at
#   r = 2034 mm; inner wheel from 1.8 mm at the radius of the eta = 3.2 cone at mid depth to 3.1 mm at that of the
#   eta = 2.5 cone. The number of layers of a volume is the nearest integer to depth / period, and the absorber and the
#   argon are scaled by the same factor to fill the depth, so the volume fraction of each material is that of ATLAS.
# - Cells of the ATLAS identifier dictionary, found as in the ATLAS simulation (EnergyCalculator::FindIdentifier_Default):
#   point pforcell = (x, y, |z| - 2 mm); eta = pseudorapidity of pforcell; compartment from eta and from z against the
#   tables ZIW (inner wheel), ZSEP12 and ZSEP23 (outer wheel) of EmecSamplingSep; eta index int(eta etaScale - etaOffset)
#   within [0, maxEta] of the table s_geometry. One CaloHitMaker per (sampling, region) of the dictionary, each taking
#   only the steps of its compartment inside its wheel (the union of the volumes of the wheel). EMEC3 only in the outer
#   wheel. The eta written in the hit is the nominal centre of the cell, eta0 + (i + 0.5) delta eta.
# - phi: 64 or 256 slices (maxPhi + 1 of s_geometry) from phi = 0 (approximation of the phi of the ATLAS electrodes).
# - Lorenzetti segment of each region (part of the hash): the region of the dictionary in the outer wheel; the inner
#   wheel takes the next free one (EMEC1: 6, EMEC2: 2).
# - The front-end parameters (pulse, noise, optimal filter) of each sampling are those of the default EMEC.
# - The end-cap presampler keeps its segmentation; with the option it is moved to just in front of the EMEC face
#   (PROVISIONAL position: its default place, 3735-3740 mm, would be inside the new EMEC).
# Not modelled: the accordion, the electrode phi of ATLAS, the rules at the edges of the ATLAS simulation (high-voltage
# buses, kapton at the edges of the wheels, validhit = false), the support rings and bars.
#
EMEC_ATLAS_Z_FRONT      = 3702.0*mm     # 3691 + 11 mm (LArWheelCalculator.cxx: dMechFocaltoWRP, dWRPtoFrontFace)
EMEC_ATLAS_THICKNESS    = 514.0*mm      # LArWheelCalculator.cxx (WheelThickness); TDR table 7-3 (lead width)
EMEC_ATLAS_FOCAL_SHIFT  = 2.0*mm        # 3691 - 3689 mm (dMechFocaltoWRP - dElecFocaltoWRP; EmecGeometry Z1 - DCF)
EMEC_ATLAS_R_OUTER      = 2034.0*mm     # EmecGeometry RLIMIT 203.4 cm; TDR pdf 252
EMEC_ATLAS_HALF_CRACK   = 1.5*mm        # EmecGeometry DCRACK 0.15 cm (half of the 3 mm between the wheels)
EMEC_ATLAS_ETA_LOW, EMEC_ATLAS_ETA_MID, EMEC_ATLAS_ETA_HIGH = 1.375, 2.5, 3.2   # EmecWheelParameters ETAEXT, ETAINT
EMEC_ATLAS_BAND         = 100.0*mm      # radial bands
EMEC_ATLAS_SLICES       = 20            # slices in z of the bands crossed by a cone (514 / 20 = 25.7 mm)
EMEC_ATLAS_LEAD         = {"outer": 1.7*mm, "inner": 2.2*mm}   # JINST pdf 144; TDR table 7-3
EMEC_ATLAS_STEEL        = 2*0.2*mm      # TDR pdf 253; JINST pdf 144
EMEC_ATLAS_PREPREG      = 2*0.15*mm     # TDR pdf 253
EMEC_ATLAS_ELECTRODE_CU = 3*0.035*mm    # TDR fig. 6-16 (pdf 207)
EMEC_ATLAS_ELECTRODE_PI = 0.275*mm - 3*0.035*mm   # the rest of the 0.275 mm electrode (TDR pdf 206, fig. 6-16)
EMEC_ATLAS_GAP          = {"outer": (0.9*mm, 2.8*mm), "inner": (1.8*mm, 3.1*mm)}  # JINST pdf 149 (linear in r: inference)
EMEC_ATLAS_ABSORBER_MATERIAL = {"outer": "ATLAS_EMEC_ABSORBER_OUTER", "inner": "ATLAS_EMEC_ABSORBER_INNER"}
# EmecSamplingSep-00, in cm as in the database, z from the electric focal point: ZIW_0..6 (inner wheel, per 0.1 in eta
# from 2.5), ZSEP12_0..43 (per 0.025 from 1.4), ZSEP23_0..21 (per 0.05 from 1.4; 999.999 = no EMEC3). They go to
# CaloHitMaker as integers in units of 1e-4 cm (the precision of the database) and are converted there as in the ATLAS
# simulation (value in cm times 10 mm), so that the comparison in z is the same as in ATLAS.
EMEC_ATLAS_ZIW_CM = [413.9337, 412.5181, 411.7915, 409.5447, 407.987, 407.5103, 404.7296]
EMEC_ATLAS_ZSEP12_CM = [378.398, 378.1372, 378.2765, 378.1665, 378.155, 378.1815, 378.1888, 378.1961, 378.2032, 378.2102, 378.217, 378.2237, 378.2303, 378.2367, 378.2429, 378.249, 378.2549, 378.2607, 378.2663, 378.2717, 378.2769, 378.2819, 378.2868, 378.2914, 378.2958, 378.3, 378.304, 378.3078, 378.344, 378.3531, 378.362, 378.3707, 378.3793, 378.3876, 378.3957, 378.3957, 376.1502, 376.1502, 376.0895, 376.0895, 375.768, 375.9073, 375.6465, 375.7857]
EMEC_ATLAS_ZSEP23_CM = [999.999, 999.999, 413.2054, 413.1076, 412.5357, 412.2458, 412.2612, 410.2924, 410.2924, 410.2656, 410.2525, 409.6982, 409.5067, 407.3844, 407.1565, 406.7029, 404.4463, 404.3643, 403.9716, 401.5903, 401.3216, 401.1531]
# Compartments of EnergyCalculator.cc (s_geometry): compartment -> (wheel, sampling 1-3, region, etaScale, etaOffset,
# maxEta, maxPhi). The nominal eta0 and delta eta of each region are etaOffset / etaScale and 1 / etaScale, the same as in
# the ATLAS identifier dictionary (checked in atlasEmecCompartmentCells).
EMEC_ATLAS_COMPARTMENTS = { 1: ("inner", 1, 0, 10, 25, 6, 63),     2: ("inner", 2, 0, 10, 25, 6, 63),
                            3: ("outer", 1, 5, 40, 96, 3, 63),     4: ("outer", 1, 4, 160, 320, 63, 63),
                            5: ("outer", 1, 3, 240, 432, 47, 63),  6: ("outer", 1, 2, 320, 480, 95, 63),
                            7: ("outer", 1, 1, 40, 57, 2, 63),     8: ("outer", 2, 1, 40, 57, 42, 255),
                            9: ("outer", 3, 0, 20, 30, 19, 255),  10: ("outer", 1, 0, 20, 27.5, 0, 63),
                           11: ("outer", 2, 0, 20, 27.5, 0, 255) }
# eta0 and delta eta of the regions in the ATLAS identifier dictionary (IdDictLArCalorimeter_DC3-05-Comm-01.xml)
EMEC_ATLAS_DICTIONARY = { ("outer", 1, 0): (1.375, 0.05), ("outer", 1, 1): (1.425, 0.025), ("outer", 1, 2): (1.5, 0.003125),
                          ("outer", 1, 3): (1.8, 0.0041666666667), ("outer", 1, 4): (2.0, 0.00625),
                          ("outer", 1, 5): (2.4, 0.025), ("outer", 2, 0): (1.375, 0.05), ("outer", 2, 1): (1.425, 0.025),
                          ("outer", 3, 0): (1.5, 0.05), ("inner", 1, 0): (2.5, 0.1), ("inner", 2, 0): (2.5, 0.1) }
EMEC_ATLAS_SEGMENT = { ("outer", 1, r): r for r in range(6) }
EMEC_ATLAS_SEGMENT.update({ ("outer", 2, 0): 0, ("outer", 2, 1): 1, ("outer", 3, 0): 0, ("inner", 1, 0): 6, ("inner", 2, 0): 2 })


def atlasEmecConeRadius(eta, z):
    """Radius (mm) of the cone of pseudorapidity eta from the electric focal point at |z| (mm, side A)."""
    return (z - EMEC_ATLAS_FOCAL_SHIFT) / math.sinh(eta)


# Volume fraction of liquid argon of the ATLAS accordion per radial band of 100 mm (key: lower edge of the band, mm), averaged over the
# depth inside the wheel (outer 1.375 < |eta| < 2.5, inner 2.5 < |eta| < 3.2): the LArWheelCalculator of Athena 23.0.14 (ported in
# geometry/GeoSpecialShapes, F41 conserto 29), phi scanned over one period of the wheel at each (r, z) on a grid of 10 mm (F41 c36,
# c36_emec_frac.cxx, tables EmecTables-ATLAS-P2-RUN4-01-01-00). Used with EMEC_ATLAS_ARGON_FRACTION (conserto 37).
EMEC_ATLAS_ARGON_FRACTION_TABLE = {
    "outer": {600: 0.4692, 700: 0.5050, 800: 0.5437, 900: 0.5735, 1000: 0.5980, 1100: 0.6180, 1200: 0.6352, 1300: 0.6502,
              1400: 0.6628, 1500: 0.6738, 1600: 0.6832, 1700: 0.6914, 1800: 0.6986, 1900: 0.7054, 2000: 0.7102},
    "inner": {300: 0.5521, 400: 0.5974, 500: 0.6331, 600: 0.6530} }
# Set by DetectorConstruction_v1 before the EMEC is built (--atlas-emec-argon-fraction): the gap of each band from the table above
EMEC_ATLAS_ARGON_FRACTION = False


def atlasEmecGap(wheel, r):
    """Liquid-argon gap g (mm) on each side of the electrode at radius r: linear in r (see above), or, with EMEC_ATLAS_ARGON_FRACTION,
    the equivalent gap that gives the volume fraction of argon of the ATLAS accordion in the band of r (2g / (t_abs + 2g) = f)."""
    if EMEC_ATLAS_ARGON_FRACTION:
        table = EMEC_ATLAS_ARGON_FRACTION_TABLE[wheel]
        key = int(math.floor(r / EMEC_ATLAS_BAND) * EMEC_ATLAS_BAND)
        key = min(max(key, min(table)), max(table))
        f = table[key]
        return 0.5 * f / (1. - f) * atlasEmecAbsorberThickness(wheel)
    zmid = EMEC_ATLAS_Z_FRONT + EMEC_ATLAS_THICKNESS / 2
    if wheel == "outer":
        r0, r1 = atlasEmecConeRadius(EMEC_ATLAS_ETA_MID, zmid), EMEC_ATLAS_R_OUTER
    else:
        r0, r1 = atlasEmecConeRadius(EMEC_ATLAS_ETA_HIGH, zmid), atlasEmecConeRadius(EMEC_ATLAS_ETA_MID, zmid)
    g0, g1 = EMEC_ATLAS_GAP[wheel]
    return g0 + (g1 - g0) * (r - r0) / (r1 - r0)


def atlasEmecAbsorberThickness(wheel):
    """Thickness (mm) of the equivalent absorber: lead, steel, prepreg and electrode."""
    return (EMEC_ATLAS_LEAD[wheel] + EMEC_ATLAS_STEEL + EMEC_ATLAS_PREPREG + EMEC_ATLAS_ELECTRODE_CU +
            EMEC_ATLAS_ELECTRODE_PI)


# With the ATLAS Run 4 geometry of the simulation (--atlas-run4; F41 conserto 27) the crack between the wheels holds the inner transversal
# bars of ATLAS (LAr::EMEC::InnerTransversalBars, a conical shell of 1.5 mm in the middle of the 3 mm crack): the edges of the slices at the
# crack are then taken at the end of the slice where the wheel is narrower (inner wheel: front; outer wheel: back), so that no step reaches
# into the crack. Set by DetectorConstruction_v1 before the EMEC is built.
EMEC_ATLAS_CRACK_EDGES_INSIDE = False


def _atlasEmecSliceEdges(wheel, zmid):
    # inner and outer radius of the wheel at the middle z of a slice (side A)
    half = 0.5 * EMEC_ATLAS_THICKNESS / EMEC_ATLAS_SLICES
    if wheel == "outer":
        zc = zmid + half if EMEC_ATLAS_CRACK_EDGES_INSIDE else zmid
        return (atlasEmecConeRadius(EMEC_ATLAS_ETA_MID, zc) + EMEC_ATLAS_HALF_CRACK,
                min(atlasEmecConeRadius(EMEC_ATLAS_ETA_LOW, zmid), EMEC_ATLAS_R_OUTER))
    zc = zmid - half if EMEC_ATLAS_CRACK_EDGES_INSIDE else zmid
    return (atlasEmecConeRadius(EMEC_ATLAS_ETA_HIGH, zmid),
            atlasEmecConeRadius(EMEC_ATLAS_ETA_MID, zc) - EMEC_ATLAS_HALF_CRACK)


def atlasEmecRings(wheel):
    """
    Volumes of one wheel on side A (see above), as a list of dicts: band (r min, r max of the band within the wheel),
    r min, r max, z min, z max, gap g at the middle radius of the band, layers, absorber and argon thickness.
    """
    z0 = EMEC_ATLAS_Z_FRONT; dz = EMEC_ATLAS_THICKNESS / EMEC_ATLAS_SLICES
    zmids = [z0 + (k + 0.5) * dz for k in range(EMEC_ATLAS_SLICES)]
    edges = [_atlasEmecSliceEdges(wheel, zm) for zm in zmids]
    rlo = min(e[0] for e in edges); rhi = max(e[1] for e in edges)
    tabs = atlasEmecAbsorberThickness(wheel)
    rings = []
    k0 = int(math.floor(rlo / EMEC_ATLAS_BAND))
    while k0 * EMEC_ATLAS_BAND < rhi:
        blo = max(k0 * EMEC_ATLAS_BAND, rlo); bhi = min((k0 + 1) * EMEC_ATLAS_BAND, rhi); k0 += 1
        g = atlasEmecGap(wheel, 0.5 * (blo + bhi))
        pieces = []
        for k, (ra, rb) in enumerate(edges):
            a, b = max(blo, ra), min(bhi, rb)
            if a < b: pieces.append((a, b, z0 + k * dz, z0 + (k + 1) * dz))
        full = len(pieces) == EMEC_ATLAS_SLICES and all(abs(p[0] - blo) < 1e-9 and abs(p[1] - bhi) < 1e-9 for p in pieces)
        if full: pieces = [(blo, bhi, z0, z0 + EMEC_ATLAS_THICKNESS)]
        for a, b, za, zb in pieces:
            depth = zb - za; period = tabs + 2 * g
            n = max(1, int(round(depth / period))); scale = depth / (n * period)
            rings.append(dict(band=(blo, bhi), rmin=a, rmax=b, zmin=za, zmax=zb, g=g, layers=n,
                              absorber=tabs * scale, argon=2 * g * scale, sliced=not full))
    return rings


def getAtlasEmecVolumesCfg(left_side=False):
    """
    The volumes of the two wheels of the ATLAS-like EMEC on one side (see above). They carry no cells by themselves: the
    cells come from the CaloHitMaker of each (sampling, region), whose limits are the union of the volumes of the wheel.
    """
    sign = -1 if left_side else 1
    side_name = 'B' if left_side else 'A'
    vols = []
    for wheel, color in (("outer", "aquamarine"), ("inner", "cornflowerblue")):
        for k, ring in enumerate(atlasEmecRings(wheel)):
            zsize = ring["layers"] * (ring["absorber"] + ring["argon"])
            name = "LAr::EMEC::%sWheel::R%04d_%04d" % (wheel.capitalize(), int(ring["band"][0]), int(math.ceil(ring["band"][1])))
            if ring["sliced"]: name += "::S%02d" % int(round((ring["zmin"] - EMEC_ATLAS_Z_FRONT) / (EMEC_ATLAS_THICKNESS / EMEC_ATLAS_SLICES)))
            vols.append(PhysicalVolume( Name               = name + "::" + side_name,
                                        Plates             = Plates.Vertical,
                                        AbsorberMaterial   = EMEC_ATLAS_ABSORBER_MATERIAL[wheel],
                                        GapMaterial        = "liquidArgon",
                                        NofLayers          = ring["layers"],
                                        AbsorberThickness  = ring["absorber"],
                                        GapThickness       = ring["argon"],
                                        RMin               = ring["rmin"],
                                        RMax               = ring["rmax"],
                                        ZSize              = zsize,
                                        X=0, Y=0, Z=sign * 0.5 * (ring["zmin"] + ring["zmax"]),
                                        Visualization = True,
                                        Color         = color ))
    return vols


def atlasEmecWheelBoxes(wheel, side=1):
    """(r min, r max, z min, z max) of the volumes of one wheel (mm; side = +1 for A, -1 for B)."""
    out = []
    for ring in atlasEmecRings(wheel):
        za, zb = (ring["zmin"], ring["zmax"]) if side > 0 else (-ring["zmax"], -ring["zmin"])
        out.append((ring["rmin"], ring["rmax"], za, zb))
    return out


def atlasEmecCompartmentCells(compartment, side=1):
    """
    Cell table of one compartment (one (sampling, region) of the dictionary) for CaloHitMaker and CaloCellMaker: the
    nominal eta and delta eta of each cell (index 0 to maxEta), the eta edges of the region, the wheel volumes (boxes)
    and the tables of the compartment logic of the ATLAS simulation. side: +1 (A) or -1 (B).
    """
    wheel, sampling, region, scale, offset, max_eta, max_phi = EMEC_ATLAS_COMPARTMENTS[compartment]
    eta0, deta = offset / scale, 1.0 / scale
    d_eta0, d_deta = EMEC_ATLAS_DICTIONARY[(wheel, sampling, region)]
    if abs(eta0 - d_eta0) > 1e-9 or abs(deta - d_deta) > 1e-9:
        raise RuntimeError(f"EMEC compartment {compartment}: s_geometry and the dictionary disagree")
    boxes = atlasEmecWheelBoxes(wheel, side)
    table = dict(Names=[], Eta=[], DeltaEta=[],
                 EmecCompartment=compartment, EmecEtaScale=scale, EmecEtaOffset=offset, EmecMaxEta=max_eta,
                 EmecFocalShift=EMEC_ATLAS_FOCAL_SHIFT,
                 EmecZSep12=[int(round(x * 1e4)) for x in EMEC_ATLAS_ZSEP12_CM],
                 EmecZSep23=[int(round(x * 1e4)) for x in EMEC_ATLAS_ZSEP23_CM],
                 EmecZInner=[int(round(x * 1e4)) for x in EMEC_ATLAS_ZIW_CM],
                 EmecWheelRMin=[b[0] for b in boxes], EmecWheelRMax=[b[1] for b in boxes],
                 EmecWheelZMin=[b[2] for b in boxes], EmecWheelZMax=[b[3] for b in boxes],
                 # ATLAS identifier (F41 conserto 19): LArEM, barrel_ec +-2 (outer wheel) or +-3 (inner wheel)
                 AtlasLArPart=1, AtlasBarrelEc=side * (3 if wheel == 'inner' else 2), AtlasLArSampling=sampling,
                 AtlasLArRegion=region, AtlasEtaIndex=list(range(max_eta + 1)))
    for i in range(max_eta + 1):
        table['Names'].append(f"EMEC{sampling}/{'IW' if wheel == 'inner' else 'OW'}/{region}/{i}{'+' if side > 0 else '-'}")
        table['Eta'].append(side * (eta0 + deta * (i + 0.5))); table['DeltaEta'].append(deta)
    edges = [eta0 + deta * k for k in range(max_eta + 2)]
    table['EtaEdges'] = edges if side > 0 else sorted(-e for e in edges)
    return table


def _getAtlasEmecCfg(left_side=False):
    """Hit makers of the ATLAS-like EMEC on one side: [emec1, emec2, emec3], lists of Calorimeter (see above)."""
    sign = -1 if left_side else 1
    side_name = 'B' if left_side else 'A'
    basepath = os.environ['LORENZETTI_GEOMETRY_DATA_DIR']
    noise = {1: 26*MeV, 2: 60*MeV, 3: 40*MeV}           # those of the default EMEC1-3
    sampling_enum = {1: CaloSampling.EMEC1, 2: CaloSampling.EMEC2, 3: CaloSampling.EMEC3}
    out = {1: [], 2: [], 3: []}
    envelopes = {}
    for compartment in sorted(EMEC_ATLAS_COMPARTMENTS, key=lambda c: (EMEC_ATLAS_COMPARTMENTS[c][1],
                              EMEC_ATLAS_COMPARTMENTS[c][0] == "inner", EMEC_ATLAS_COMPARTMENTS[c][2])):
        wheel, sampling, region, scale, offset, max_eta, max_phi = EMEC_ATLAS_COMPARTMENTS[compartment]
        key = (sampling, wheel)
        if key not in envelopes:
            # Limits of the hit makers of this sampling in this wheel (not built: the volumes come from
            # getAtlasEmecVolumesCfg); the makers then take only the steps inside the wheel volumes.
            boxes = atlasEmecWheelBoxes(wheel, sign)
            rmin, rmax = min(b[0] for b in boxes), max(b[1] for b in boxes)
            zmin, zmax = min(b[2] for b in boxes), max(b[3] for b in boxes)
            pv = PhysicalVolume( Name               = f"LAr::EMEC{sampling}::{wheel.capitalize()}Wheel::" + side_name,
                                 Plates             = Plates.Vertical,
                                 AbsorberMaterial   = EMEC_ATLAS_ABSORBER_MATERIAL[wheel],
                                 GapMaterial        = "liquidArgon",
                                 NofLayers          = 1,
                                 AbsorberThickness  = (zmax - zmin) / 2,
                                 GapThickness       = (zmax - zmin) / 2,
                                 RMin               = rmin,
                                 RMax               = rmax,
                                 ZSize              = zmax - zmin,
                                 X=0, Y=0, Z=0.5 * (zmin + zmax),
                                 Visualization = False,
                                 Color         = 'aquamarine' )
            pv.Envelope = True
            envelopes[key] = pv
        pv = envelopes[key]
        cells = atlasEmecCompartmentCells(compartment, side=sign)
        edges = cells.pop('EtaEdges')
        deta = 1.0 / scale
        dphi = 2 * pi / (max_phi + 1)
        segment = EMEC_ATLAS_SEGMENT[(wheel, sampling, region)]
        lo, hi = sorted(abs(e) for e in (edges[0], edges[-1]))
        sv = SensitiveDetector( pv, EtaMin = sign*lo, EtaMax = sign*hi, Segment = segment, DeltaEta = deta, DeltaPhi = dphi )
        if len(sv.PhiBins) - 1 != max_phi + 1:
            raise RuntimeError(f"EMEC compartment {compartment}: {len(sv.PhiBins) - 1} phi slices, expected {max_phi + 1}")
        sv.EtaBins = edges; sv.EtaMin = edges[0]; sv.EtaMax = edges[-1]
        sv.Cells = cells
        # half-absorber shift of the wheel: pi/768 in the outer wheel (768 absorbers), pi/256 in the inner wheel (256 absorbers);
        # measured in the ATLAS simulation (F41 medida 30d, 16/10/2026: inner EMEC1 about +-pi/256, outer EMEC2 +-pi/768)
        atlasLArPhiShift(sv, -sign * pi / (768 if wheel == "outer" else 256))
        out[sampling].append( Calorimeter( sv, -21, 3, -2,
                              CollectionKey   = f"Collection_EMEC{sampling}_{segment}" + side_name,
                              Detector        = Detector.TTEM,
                              Sampling        = sampling_enum[sampling],
                              Shaper          = basepath + "/pulseLar.dat",
                              Noise           = noise[sampling],
                              Samples         = 5,
                              OFWeightsEnergy = [-0.0000853580,    0.265132,    0.594162,     0.389505,     0.124353],
                              OFWeightsTime   = [-0.0000853580,   -12.870312690734863, -27.39136505126953, 8.075883865356445, 13.768877029418945]
                            ) )
    return [out[1], out[2], out[3]]
