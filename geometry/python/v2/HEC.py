

__all__ = ["getHECCfg", "getAtlasHecPassiveCfg", "getAtlasHecCells"]


from GaugiKernel.constants import mm,MeV,pi
from CaloCell.CaloDefs import Detector, CaloSampling

from .Calorimeter import Calorimeter
from .PhysicalVolume import PhysicalVolume, Plates
from .SensitiveDetector import SensitiveDetector

import os

# Birks constant of the liquid argon of the HEC, as ATLAS (LArG4HECConfig.py, BirksConstant = 0.0486; the barrel and the EMEC use
# 0.05832); read by CaloHitMaker with --birks-law (F41 conserto 19, decision of 11/10/2026)
HEC_BIRKS_K = 0.0486



def getHECCfg(left_side=False, atlas_hec=False):
    """
    Hadronic end-cap of one side.

    Args:
        left_side (bool): If True, the B side (negative z).
        atlas_hec (bool): If True, the HEC as in ATLAS (four samplings HEC0-HEC3 in two wheels, nominal z, plates and
                          cells of ATLAS; see _getAtlasHecCfg and the notes below). The passive volumes that go with it
                          come from getAtlasHecPassiveCfg. Off by default: the default HEC is unchanged.
    """
    if atlas_hec:
        return _getAtlasHecCfg(left_side)

    sign = -1 if left_side else 1
    side_name = 'B' if left_side else 'A'
    
    basepath = os.environ['LORENZETTI_GEOMETRY_DATA_DIR']
    hec_start = 4262*mm

    #
    # HEC1
    #
    nlayers=9; absorber=12.5*mm; gap=8.5*mm; zsize=nlayers*(absorber+gap)
    hec1_zsize = zsize
    hec1_pv    =  PhysicalVolume(  Name               = "FCal::HEC1::"+side_name, 
                                   Plates             = Plates.Vertical, # Logical type
                                   AbsorberMaterial   = "G4_Cu", # absorber
                                   GapMaterial        = "liquidArgon", # gap
                                   NofLayers          = nlayers, # 16s (max 16)
                                   AbsorberThickness  = absorber, # abso
                                   GapThickness       = gap, # gap
                                   RMin               = 372*mm,# radio min,
                                   RMax               = 2030*mm,# radio max 
                                   ZSize              = zsize ,
                                   X=0,Y=0,Z= sign * (hec_start + zsize/2), # x,y,z 
                                   Visualization = True,
                                   Color         = 'salmon'
                                  ) 

   
    hec1_sv0 = SensitiveDetector( hec1_pv, EtaMax = sign*2.50         , Segment = 0, DeltaEta = 0.1, DeltaPhi = pi/32 )

   
    hec1_sv0.BirksLArK = HEC_BIRKS_K
    hec1_sv1 = SensitiveDetector( hec1_pv, EtaMin = hec1_sv0.EtaMax   , Segment = 1, DeltaEta = 0.2, DeltaPhi = pi/16 )
    hec1_sv1.BirksLArK = HEC_BIRKS_K



    # Configure the electronic frontend and the detector parameters
    hec1_det0  = Calorimeter( hec1_sv0, -21, 3, -2, # sensitive volume, bunch start, bunch end, sampling start,
                              CollectionKey = "Collection_HEC1_0" + side_name, # collection key
                              Detector        = Detector.TTHEC, # detector type
                              Sampling        = CaloSampling.HEC1, # sampling type
                              Shaper          = basepath + "/pulseLar.dat", # pulse shaper
                              Noise           = 250*MeV, # electronic noise
                              Samples         = 5, # how many samples
                              OFWeightsEnergy = [-0.0000853580,    0.265132,    0.594162,     0.389505,     0.124353], # optimal filter parameters for energy estimation
                              OFWeightsTime   = [-0.0000853580,   -12.870312690734863, -27.39136505126953, 8.075883865356445, 13.768877029418945] # EMB1 ATLAS sample to test (fake first number to add to 5) 
                            )
    # Configure the electronic frontend and the detector parameters
    hec1_det1  = Calorimeter( hec1_sv1, -21, 3, -2, # sensitive volume, bunch start, bunch end, sampling start,
                              CollectionKey = "Collection_HEC1_1"+ side_name, # collection key
                              Detector        = Detector.TTHEC, # detector type
                              Sampling        = CaloSampling.HEC1, # sampling type
                              Shaper          = basepath + "/pulseLar.dat", # pulse shaper
                              Noise           = 250*MeV, # electronic noise
                              Samples         = 5, # how many samples
                              OFWeightsEnergy = [-0.0000853580,    0.265132,    0.594162,     0.389505,     0.124353], # optimal filter parameters for energy estimation
                              OFWeightsTime   = [-0.0000853580,   -12.870312690734863, -27.39136505126953, 8.075883865356445, 13.768877029418945] # EMB1 ATLAS sample to test (fake first number to add to 5) 
                            )



    #
    # HEC2
    #
    nlayers=16; absorber=12.5*mm; gap=8.5*mm; zsize=nlayers*(absorber+gap)
    hec2_zsize = zsize
    hec2_pv  =  PhysicalVolume(  Name               = "FCal::HEC2::"+side_name, 
                                 Plates             = Plates.Vertical, # Logical type
                                 AbsorberMaterial   = "G4_Cu", # absorber
                                 GapMaterial        = "liquidArgon", # gap
                                 NofLayers          = nlayers, # 16s (max 16)
                                 AbsorberThickness  = absorber, # abso
                                 GapThickness       = gap, # gap
                                 RMin               = 475*mm,# radio min,
                                 RMax               = 2030*mm,# radio max 
                                 ZSize              = zsize ,
                                 X=0,Y=0,Z= sign * (hec_start + hec1_zsize + hec1_zsize +zsize/2), # x,y,z 
                                 Visualization = True,
                                 Color         = 'violetred'
                             ) 


    hec2_sv0 = SensitiveDetector( hec2_pv, EtaMax = sign*2.50         , Segment = 0, DeltaEta = 0.1, DeltaPhi = pi/32 )


    hec2_sv0.BirksLArK = HEC_BIRKS_K
    hec2_sv1 = SensitiveDetector( hec2_pv, EtaMin = hec2_sv0.EtaMax   , Segment = 1, DeltaEta = 0.2, DeltaPhi = pi/16 )
    hec2_sv1.BirksLArK = HEC_BIRKS_K


    # Configure the electronic frontend and the detector parameters
    hec2_det0  = Calorimeter( hec2_sv0, -21, 3, -2, # sensitive volume, bunch start, bunch end, sampling start,
                              CollectionKey = "Collection_HEC2_0" + side_name, # collection key
                              Detector        = Detector.TTHEC, # detector type
                              Sampling        = CaloSampling.HEC2, # sampling type
                              Shaper          = basepath + "/pulseLar.dat", # pulse shaper
                              Noise           = 400*MeV, # electronic noise
                              Samples         = 5, # how many samples
                              OFWeightsEnergy = [-0.0000853580,    0.265132,    0.594162,     0.389505,     0.124353], # optimal filter parameters for energy estimation
                              OFWeightsTime   = [-0.0000853580,   -12.870312690734863, -27.39136505126953, 8.075883865356445, 13.768877029418945] # EMB1 ATLAS sample to test (fake first number to add to 5) 
                            )
    # Configure the electronic frontend and the detector parameters
    hec2_det1  = Calorimeter( hec2_sv1, -21, 3, -2, # sensitive volume, bunch start, bunch end, sampling start,
                              CollectionKey = "Collection_HEC2_1"+ side_name, # collection key
                              Detector        = Detector.TTHEC, # detector type
                              Sampling        = CaloSampling.HEC2, # sampling type
                              Shaper          = basepath + "/pulseLar.dat", # pulse shaper
                              Noise           = 400*MeV, # electronic noise
                              Samples         = 5, # how many samples
                              OFWeightsEnergy = [-0.0000853580,    0.265132,    0.594162,     0.389505,     0.124353], # optimal filter parameters for energy estimation
                              OFWeightsTime   = [-0.0000853580,   -12.870312690734863, -27.39136505126953, 8.075883865356445, 13.768877029418945] # EMB1 ATLAS sample to test (fake first number to add to 5) 
                            )





    #
    # HEC3
    #
    nlayers=16; absorber=50*mm; gap=8.5*mm; zsize=nlayers*(absorber+gap)
    hec3_zsize = zsize
    hec3_pv  =  PhysicalVolume(  Name               = "FCal::HEC3::"+side_name, 
                                 Plates             = Plates.Vertical, # Logical type
                                 AbsorberMaterial   = "G4_Cu", # absorber
                                 GapMaterial        = "liquidArgon", # gap
                                 NofLayers          = nlayers, # 16s (max 16)
                                 AbsorberThickness  = absorber, # abso
                                 GapThickness       = gap, # gap
                                 RMin               = 475*mm,# radio min,
                                 RMax               = 2030*mm,# radio max 
                                 ZSize              = zsize ,
                                 X=0,Y=0,Z= sign * (hec_start + hec1_zsize + hec1_zsize + hec2_zsize + zsize/2), # x,y,z 
                                 Visualization = True,
                                 Color         = 'orangered'
                             ) 


    hec3_sv0 = SensitiveDetector( hec3_pv, EtaMax = sign*2.50         , Segment = 0, DeltaEta = 0.1, DeltaPhi = pi/32 )


    hec3_sv0.BirksLArK = HEC_BIRKS_K
    hec3_sv1 = SensitiveDetector( hec3_pv, EtaMin = hec3_sv0.EtaMax   , Segment = 1, DeltaEta = 0.2, DeltaPhi = pi/16 )
    hec3_sv1.BirksLArK = HEC_BIRKS_K

    # Configure the electronic frontend and the detector parameters
    hec3_det0  = Calorimeter( hec3_sv0, -21, 3, -2, # sensitive volume, bunch start, bunch end, sampling start,
                              CollectionKey = "Collection_HEC3_0" + side_name, # collection key
                              Detector        = Detector.TTHEC, # detector type
                              Sampling        = CaloSampling.HEC3, # sampling type
                              Shaper          = basepath + "/pulseLar.dat", # pulse shaper
                              Noise           = 250*MeV, # electronic noise
                              Samples         = 5, # how many samples
                              OFWeightsEnergy = [-0.0000853580,    0.265132,    0.594162,     0.389505,     0.124353], # optimal filter parameters for energy estimation
                              OFWeightsTime   = [-0.0000853580,   -12.870312690734863, -27.39136505126953, 8.075883865356445, 13.768877029418945] # EMB1 ATLAS sample to test (fake first number to add to 5) 
                            )
    # Configure the electronic frontend and the detector parameters
    hec3_det1  = Calorimeter( hec3_sv1, -21, 3, -2, # sensitive volume, bunch start, bunch end, sampling start,
                              CollectionKey = "Collection_HEC3_1"+ side_name, # collection key
                              Detector        = Detector.TTHEC, # detector type
                              Sampling        = CaloSampling.HEC3, # sampling type
                              Shaper          = basepath + "/pulseLar.dat", # pulse shaper
                              Noise           = 250*MeV, # electronic noise
                              Samples         = 5, # how many samples
                              OFWeightsEnergy = [-0.0000853580,    0.265132,    0.594162,     0.389505,     0.124353], # optimal filter parameters for energy estimation
                              OFWeightsTime   = [-0.0000853580,   -12.870312690734863, -27.39136505126953, 8.075883865356445, 13.768877029418945] # EMB1 ATLAS sample to test (fake first number to add to 5) 
                            )
    
    hec1 = [hec1_det0, hec1_det1]
    hec2 = [hec2_det0, hec2_det1]
    hec3 = [hec3_det0, hec3_det1]

    return [hec1, hec2, hec3]
   



# ---------------------------------------------------------------------------------------------------------------------
# ATLAS-like hadronic end-cap (option atlas_hec; simu_trf.py and digit_trf.py --atlas-hec; off by default).
#
# Nominal construction values of the ATLAS HEC, without the shift of the installed detector (ZSHIFT of the table
# HadronicEndcap, 40 or 45 mm, left out on purpose). Source: the ATLAS geometry database (geomDB_sqlite, tables
# HadronicEndcap-00, HecLongitudinalBlock-00, HecNominals-00 and HecPad-00), the same numbers read by the ATLAS
# simulation (Athena, LArCalorimeter/LArGeoModel/LArReadoutGeometry/src/HECDetectorManager.cxx). Where the public
# description gives them they agree: copper plates of 25 mm (front wheel) and 50 mm (rear wheel), first plates of 12.5
# and 25 mm, 8.5 mm liquid argon gaps, front wheel 816.5 mm and rear wheel 961 mm deep (JINST 3 (2008) S08003, sec. 5.3).
#
# - Seven longitudinal blocks (HecLongitudinalBlock: IBLC, BLDPTH, BLMOD, PLATE0, BLRMN, BLRMX): the front wheel has
#   blocks 1-3 (8 gaps each), the rear wheel blocks 4-7 (4 gaps each); the first block of each wheel starts with a copper
#   plate (12.5 and 25 mm), then each layer is a gap followed by a plate. The HEC starts at z = 4277.0 mm (ZSTART of
#   HadronicEndcap) and the wheels are 40.5 mm apart (GAPWHL). Inner radius 372 mm (block 1) and 475 mm (blocks 2-7),
#   outer radius 2030 mm.
# - Samplings as in the ATLAS simulation (LArG4HEC/src/HECGeometry.cc: sampling = 0 for block 1, 1 for blocks 2-3,
#   2 for blocks 4-5, 3 for blocks 6-7): HEC0 4277.0-4557.5, HEC1 4557.5-5093.5, HEC2 5134.0-5627.0, HEC3
#   5627.0-6095.0 mm (HecNominals INDEPTH, OUTDEPTH). The first plates and the liquid argon between the wheels are
#   passive volumes (no cells).
# - Cells (ATLAS identifier dictionary, IdDictLArCalorimeter): per sampling, region 0 (delta eta 0.1, 64 phi slices) and
#   region 1 (delta eta 0.2, 32 phi slices), one Calorimeter each (Segment 0 and 1). Indices: HEC0 0-9 / 0-3, HEC1 0-9 /
#   0-2, HEC2 1-9 / 0-2, HEC3 2-9 / 0-3. Nominal eta of a cell: 1.5 + 0.1 (i + 0.5) in region 0 and 2.5 + 0.2 (i + 0.5)
#   in region 1 (negative on side B).
# - The cell of a step is found from its radius and z, as in the ATLAS simulation (HECGeometry::initialize and
#   CalculateIdentifier): in each block the cells are radial segments of the pads, [ETA_k, ETA_k+1] of the HecPad row of
#   the block (HECLongBlock constructor), numbered from the inside out by isegInner, isegOuter and nInReg, as in
#   HECGeometry::initialize; 2027 mm stands for the outer radius of the block and 375 mm (block 1) or 478 mm (blocks 2-7)
#   for its inner radius (the innermost box starts at r = 0, see atlasHecRadialSegments). The radius is measured on the axis of the module, r cos(phi - phi_c), with phi_c the centre of
#   the module (32 modules from phi = 0), as moduleY in HECGeometry (CaloHitMaker property CellRadiusModules).
# - The front-end parameters of HEC0 (pulse, noise, optimal filter) are those of HEC1; HEC1-HEC3 keep theirs.
# Not modelled: the 32 modules (phi cracks, tie rods, spacers), the electrodes (kapton) in the gaps, the readout pads.
#
HEC_ATLAS_Z_START   = 4277.0*mm                    # HadronicEndcap ZSTART 427.7 cm (HecNominals INDEPTH of HEC0)
HEC_ATLAS_WHEEL_GAP = 40.5*mm                      # HadronicEndcap GAPWHL 4.05 cm
HEC_ATLAS_R_OUTER   = 2030*mm                      # HecLongitudinalBlock BLRMX 203.0 cm
HEC_ATLAS_LAR_GAP   = 8.5*mm                       # HadronicEndcap LARG 0.85 cm
#                     depth       gaps  inner radius  plate      first plate   (HecLongitudinalBlock, HadronicEndcap)
HEC_ATLAS_BLOCKS = [ (280.5*mm,   8,    372*mm,       25*mm,     12.5*mm ),   # block 1: BLDPTH 28.05, BLMOD 8, PLATE0 1.25
                     (268.0*mm,   8,    475*mm,       25*mm,     0       ),   # block 2: 26.8, 8
                     (268.0*mm,   8,    475*mm,       25*mm,     0       ),   # block 3: 26.8, 8
                     (259.0*mm,   4,    475*mm,       50*mm,     25*mm   ),   # block 4: 25.9, 4, PLATE0 2.5
                     (234.0*mm,   4,    475*mm,       50*mm,     0       ),   # block 5: 23.4, 4
                     (234.0*mm,   4,    475*mm,       50*mm,     0       ),   # block 6: 23.4, 4
                     (234.0*mm,   4,    475*mm,       50*mm,     0       ) ]  # block 7: 23.4, 4
HEC_ATLAS_SAMPLING_BLOCKS = [ [0], [1, 2], [3, 4], [5, 6] ]   # HEC0..HEC3 (HECGeometry::CalculateIdentifier)
# HecPad-00, ETA_0 ... ETA_14 (mm): radial boundaries of the pads of each block, from eta 3.3 to 1.5
HEC_ATLAS_PAD = [
  [375.0, 398.23, 486.89, 595.58, 729.07, 806.96, 893.46, 989.66, 1096.76, 1216.2, 1349.69, 1499.23, 1667.28, 1856.82, 2027.0],
  [478.0, 478.0, 516.47, 631.76, 773.36, 855.98, 947.75, 1049.78, 1163.39, 1290.1, 1431.69, 1590.32, 1768.58, 1969.63, 2027.0],
  [478.0, 478.0, 546.05, 667.95, 817.66, 905.01, 1002.03, 1109.91, 1230.03, 1363.99, 1513.69, 1681.41, 1869.88, 2027.0, 2027.0],
  [478.0, 478.0, 579.61, 708.99, 867.91, 960.63, 1063.61, 1178.12, 1305.62, 1447.8, 1606.71, 1784.73, 1984.78, 2027.0, 2027.0],
  [478.0, 478.0, 605.44, 740.59, 906.58, 1003.43, 1111.01, 1230.62, 1363.8, 1512.33, 1678.31, 1864.27, 2027.0, 2027.0, 2027.0],
  [478.0, 516.32, 631.27, 772.19, 945.26, 1046.24, 1158.4, 1283.12, 1421.98, 1576.85, 1749.91, 1943.8, 2027.0, 2027.0, 2027.0],
  [478.0, 537.45, 657.1, 803.78, 983.93, 1089.05, 1205.8, 1335.62, 1480.16, 1641.36, 1821.51, 2027.0, 2027.0, 2027.0, 2027.0] ]
# Cell indices of the ATLAS identifier dictionary, per sampling: (region 0, region 1)
HEC_ATLAS_CELL_INDICES = [ (range(0, 10), range(0, 4)), (range(0, 10), range(0, 3)),
                           (range(1, 10), range(0, 3)), (range(2, 10), range(0, 4)) ]
HEC_ATLAS_MODULES = 32


def atlasHecBlockZ():
    """(z start, z end) of the seven blocks on side A (mm), from HEC_ATLAS_Z_START, the depths and the wheel gap."""
    z = HEC_ATLAS_Z_START; out = []
    for b, blk in enumerate(HEC_ATLAS_BLOCKS):
        if b == 3: z += HEC_ATLAS_WHEEL_GAP
        out.append((z, z + blk[0])); z += blk[0]
    return out


def atlasHecRadialSegments(block):
    """
    Cells of one block (0-6) as in HECGeometry::initialize: list of (region, ieta, rmin, rmax), from the inside out.
    The segments are those of the HECLongBlock constructor (segment k = [ETA_k, ETA_k+1] of the HecPad row, absent where
    the two are equal).
    """
    pad = HEC_ATLAS_PAD[block]
    num_blk = block + 1
    r_inner, r_outer = HEC_ATLAS_BLOCKS[block][2], HEC_ATLAS_R_OUTER
    iseg_inner, iseg_outer, n_in_reg = 0, len(pad) - 1, 4
    if 1 < num_blk < 6: iseg_inner, n_in_reg = 1, 3
    if num_blk > 6:   iseg_outer = 11
    elif num_blk > 4: iseg_outer = 12
    elif num_blk > 2: iseg_outer = 13
    ieta, region, out = n_in_reg, 1, []
    for iseg in range(iseg_inner, iseg_outer):
        ieta -= 1
        if ieta < 0: region, ieta = 0, 9
        lo, hi = pad[iseg], pad[iseg + 1]
        if lo == hi:
            raise RuntimeError(f"HEC block {num_blk}: empty radial segment {iseg}")
        if hi == 2027.: hi = r_outer
        # Innermost cell of the block from r = 0 (decision of 06/10/2026, F45 conserto 15 point 1): a step inside the
        # volume (true radius above the inner radius) whose radius on the module axis falls below the inner radius goes to
        # the innermost cell, as ietaMin in HECGeometry::CalculateIdentifier, instead of being dropped.
        if (lo == 375. and block == 0) or (lo == 478. and block > 0): lo = 0.0
        out.append((region, ieta, lo, hi))
    return out


def getAtlasHecCells(sampling, region, side=1):
    """
    Cells of one region (0 or 1) of one sampling (0-3, HEC0-HEC3) of the ATLAS-like HEC, as the (r, z) boxes read by
    CaloHitMaker: one box per cell and block of the sampling, cells in increasing dictionary index. side: +1 (A) or -1 (B).
    """
    indices = list(HEC_ATLAS_CELL_INDICES[sampling][region])
    zblocks = atlasHecBlockZ()
    boxes = {i: [] for i in indices}
    for block in HEC_ATLAS_SAMPLING_BLOCKS[sampling]:
        z0, z1 = zblocks[block]
        if side < 0: z0, z1 = -z1, -z0
        for reg, ieta, rmin, rmax in atlasHecRadialSegments(block):
            if reg != region: continue
            if ieta not in boxes:
                raise RuntimeError(f"HEC{sampling} region {region}: cell {ieta} of block {block+1} not in the dictionary")
            boxes[ieta].append((rmin, rmax, z0, z1))
    eta0, deta = (1.5, 0.1) if region == 0 else (2.5, 0.2)
    table = dict(Names=[], Eta=[], DeltaEta=[], BoxRMin=[], BoxRMax=[], BoxZMin=[], BoxZMax=[], BoxCell=[],
                 RadiusModules=HEC_ATLAS_MODULES,
                 # ATLAS identifier (F41 conserto 19): LArHEC, pos_neg +-2, the dictionary eta index of each cell
                 AtlasLArPart=2, AtlasBarrelEc=2 * side, AtlasLArSampling=sampling, AtlasLArRegion=region,
                 AtlasEtaIndex=[int(i) for i in indices])
    for cell, i in enumerate(indices):
        if not boxes[i]:
            raise RuntimeError(f"HEC{sampling} region {region}: cell {i} has no box")
        table['Names'].append(f"HEC{sampling}/{region}/{i}{'+' if side > 0 else '-'}")
        table['Eta'].append(round(side * (eta0 + deta * (i + 0.5)), 5)); table['DeltaEta'].append(deta)
        for rmin, rmax, z0, z1 in boxes[i]:
            table['BoxRMin'].append(rmin); table['BoxRMax'].append(rmax)
            table['BoxZMin'].append(z0); table['BoxZMax'].append(z1); table['BoxCell'].append(cell)
    # eta edges of the region (monitoring histograms only; the cells come from the boxes)
    edges = [round(eta0 + deta * k, 4) for k in range(indices[0], indices[-1] + 2)]
    table['EtaEdges'] = edges if side > 0 else sorted(-e for e in edges)
    return table


def _passiveVolume(name, material, rmin, z0, z1):
    # One layer of a single material (absorber and gap both of it, half of the thickness each), no cells.
    t = z1 - z0
    return PhysicalVolume( Name               = name,
                           Plates             = Plates.Vertical,
                           AbsorberMaterial   = material,
                           GapMaterial        = material,
                           NofLayers          = 1,
                           AbsorberThickness  = t/2,
                           GapThickness       = t/2,
                           RMin               = rmin,
                           RMax               = HEC_ATLAS_R_OUTER,
                           ZSize              = t,
                           X=0,Y=0,Z=(z0 + z1)/2,
                           Visualization = True,
                           Color         = 'gray' )


def getAtlasHecPassiveCfg(left_side=False):
    """
    Passive volumes of the ATLAS-like HEC (see above): the first copper plate of each wheel and the liquid argon between
    the wheels. Simulation and digitization use the same geometry.
    """
    sign = -1 if left_side else 1
    side_name = 'B' if left_side else 'A'
    zb = atlasHecBlockZ()
    vols = []
    for name, material, rmin, z0, z1 in (
            ("HEC0::FrontPlate", "G4_Cu",       HEC_ATLAS_BLOCKS[0][2], zb[0][0], zb[0][0] + HEC_ATLAS_BLOCKS[0][4]),
            ("WheelGap",         "liquidArgon", HEC_ATLAS_BLOCKS[1][2], zb[2][1], zb[3][0]),
            ("HEC2::FrontPlate", "G4_Cu",       HEC_ATLAS_BLOCKS[3][2], zb[3][0], zb[3][0] + HEC_ATLAS_BLOCKS[3][4])):
        za, zz = (z0, z1) if sign > 0 else (-z1, -z0)
        vols.append(_passiveVolume("DM::HEC::"+name+"::"+side_name, material, rmin, za, zz))
    return vols


def _getAtlasHecCfg(left_side=False):
    sign = -1 if left_side else 1
    side_name = 'B' if left_side else 'A'
    basepath = os.environ['LORENZETTI_GEOMETRY_DATA_DIR']
    zb = atlasHecBlockZ()
    # front-end parameters (HEC0 takes those of HEC1, see above)
    noise = [250*MeV, 250*MeV, 400*MeV, 250*MeV]
    sampling_enum = [CaloSampling.HEC0, CaloSampling.HEC1, CaloSampling.HEC2, CaloSampling.HEC3]
    colors = ['lightsalmon', 'salmon', 'violetred', 'orangered']
    out = []
    for s, blocks in enumerate(HEC_ATLAS_SAMPLING_BLOCKS):
        first = HEC_ATLAS_BLOCKS[blocks[0]]
        zstart = zb[blocks[0]][0] + first[4]      # after the first plate of the wheel
        zend = zb[blocks[-1]][1]
        nlayers = sum(HEC_ATLAS_BLOCKS[b][1] for b in blocks)
        plate = first[3]
        zsize = nlayers * (HEC_ATLAS_LAR_GAP + plate)
        if abs(zsize - (zend - zstart)) > 1e-6:
            raise RuntimeError(f"HEC{s}: {nlayers} layers of {HEC_ATLAS_LAR_GAP + plate} mm do not fill {zstart}-{zend} mm")
        # Plates.Vertical: in each layer the gap comes first, then the absorber, seen from the interaction point
        # (geometry/src/DetectorConstruction_v1.cxx, CreateVerticalPlates), as in ATLAS (gap, plate, gap, plate, ...).
        pv = PhysicalVolume( Name               = f"FCal::HEC{s}::"+side_name,
                             Plates             = Plates.Vertical,
                             AbsorberMaterial   = "G4_Cu",
                             GapMaterial        = "liquidArgon",
                             NofLayers          = nlayers,
                             AbsorberThickness  = plate,
                             GapThickness       = HEC_ATLAS_LAR_GAP,
                             RMin               = first[2],
                             RMax               = HEC_ATLAS_R_OUTER,
                             ZSize              = zsize,
                             X=0,Y=0,Z= sign * (zstart + zsize/2),
                             Visualization = True,
                             Color         = colors[s] )
        dets = []
        for region, (deta, dphi) in enumerate(((0.1, pi/32), (0.2, pi/16))):
            cells = getAtlasHecCells(s, region, side=sign)
            edges = cells.pop('EtaEdges')
            # eta x phi grid of the region (phi slices; the eta bins only for the monitoring histograms)
            lo, hi = sorted(abs(e) for e in (edges[0], edges[-1]))
            sv = SensitiveDetector( pv, EtaMin = sign*lo, EtaMax = sign*hi, Segment = region, DeltaEta = deta, DeltaPhi = dphi )
            sv.EtaBins = edges; sv.EtaMin = edges[0]; sv.EtaMax = edges[-1]
            sv.Cells = cells
            sv.BirksLArK = HEC_BIRKS_K
            dets.append( Calorimeter( sv, -21, 3, -2,
                              CollectionKey   = f"Collection_HEC{s}_{region}" + side_name,
                              Detector        = Detector.TTHEC,
                              Sampling        = sampling_enum[s],
                              Shaper          = basepath + "/pulseLar.dat",
                              Noise           = noise[s],
                              Samples         = 5,
                              OFWeightsEnergy = [-0.0000853580,    0.265132,    0.594162,     0.389505,     0.124353],
                              OFWeightsTime   = [-0.0000853580,   -12.870312690734863, -27.39136505126953, 8.075883865356445, 13.768877029418945]
                            ) )
        out.append(dets)
    return out
