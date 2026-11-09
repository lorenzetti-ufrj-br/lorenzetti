
__all__ = ["getTileBarrelCfg","getTileExtendedCfg","getAtlasTileCells","getAtlasTileGapCfg","getAtlasTileGapVolumesCfg",
           "ATLAS_TILE_GAP_MIXTURES"]

from GaugiKernel.constants import m,cm,mm,MeV,pi
from CaloCell.CaloDefs import Detector, CaloSampling

from .Calorimeter import Calorimeter
from .PhysicalVolume import PhysicalVolume, Plates
from .SensitiveDetector import SensitiveDetector

import os
import math


# ATLAS-like tile calorimeter (option TileAtlasGeometry, off by default).
# In ATLAS the scintillating tiles are placed radially and normal to the beam line, stacked along z
# in periods of 18 mm: 5 mm master plate + 4 mm spacer plate + 5 mm master plate (14 mm steel), a
# 3 mm tile and 1 mm left by the 3 mm tile in its 4 mm pocket, steel:scintillator 4.67:1
# (TILECAL, hep-ex/9904032, sec. 2; JINST 3 (2008) S08003, sec. 5.3.1.2). Here each layer is built
# with vertical plates (Fe 14 mm + scintillator 3 mm + 1 mm empty clearance). The staggering of the
# tiles between radial rows is not modelled, nor the support girder at the outer radius.
# Layer radii (A, BC, D in the barrel; A, B, D in the extended barrel) from the ATLAS cell geometry;
# with this period they give 1.45/4.07/1.84 interaction lengths in the barrel and 1.45/2.62/3.30 in
# the extended barrel at normal incidence, against about 1.5/4.1/1.8 and 1.5/2.6/3.3 quoted in
# JINST 3 (2008) S08003 (sec. 5.3.1.4 and chap. 1). The cells keep the eta x phi segmentation below.
TILE_ATLAS_ABSORBER  = 14*mm
TILE_ATLAS_TILE      = 3*mm
TILE_ATLAS_CLEARANCE = 1*mm
TILE_ATLAS_BARREL_RADII   = [2300*mm, 2600*mm, 3440*mm, 3820*mm]
TILE_ATLAS_EXTENDED_RADII = [2300*mm, 2600*mm, 3140*mm, 3820*mm]
# Longitudinal extent of the ATLAS-like tile calorimeter, from the ATLAS cell layout (JINST 3 (2008) S08003,
# fig. 5.12: long barrel up to |z| = 2816 mm, extended barrel from 3554 to 6113 mm), rounded to whole 18 mm
# periods so that no tile is cut: long barrel |z| < 2808 mm (312 periods), extended barrel 3554 < |z| < 6110 mm
# (142 periods). The aluminium block that stands for the ITC fills the space in between (see DeadMaterials).
TILE_ATLAS_BARREL_HALF_Z     = 2808*mm
TILE_ATLAS_EXTENDED_Z_START  = 3554*mm
TILE_ATLAS_EXTENDED_Z_END    = 6110*mm


# ATLAS tile cells (option TileAtlasCells, off by default; needs TileAtlasGeometry). In ATLAS a cell is the group of
# tiles read out by the same photomultiplier, with fixed z boundaries in each radial row (JINST 3 (2008) S08003,
# sec. 5.3.1.4, "the fibre grouping is used to define a three-dimensional cell structure", and fig. 5.12). The
# boundaries below were read from fig. 5.12 (vector drawing, z scale from its ruler; about 2 mm precision), in mm, on
# the positive side; the negative side is the mirror image. Each boundary is moved to the nearest boundary between two
# 18 mm periods, so that every tile belongs to a single cell, as in ATLAS.
# Long barrel: A1-A10, B1-B9 and C1-C8 read together as BC1-BC8 (B9 only in the B row), D0 (across z = 0) to D3.
# Extended barrel: A12-A16, B11-B15, D5 and D6. The gap/crack cells (C10, D4, E1-E4) are not built.
TILE_ATLAS_CELLS_BARREL_A = [271.9, 510.4, 767.8, 1029.0, 1305.3, 1585.5, 1865.6, 2195.0, 2531.9]  # A1/A2 ... A9/A10
TILE_ATLAS_CELLS_BARREL_B = [306.0, 593.7, 870.0, 1169.1, 1468.1, 1797.5, 2138.2, 2505.4]          # B1/B2 ... B8/B9
TILE_ATLAS_CELLS_BARREL_C = [340.0, 669.4, 998.7, 1339.4, 1687.7, 2058.7, 2456.2]                  # C1/C2 ... C7/C8
TILE_ATLAS_CELLS_BARREL_D = [389.2, 1127.4, 1903.5]                                                # D0 half length, D1/D2, D2/D3
TILE_ATLAS_CELLS_BC_RADIUS = 2990*mm   # B/C row boundary inside the BC layer
TILE_ATLAS_CELLS_EXT_A = [3720.6, 4174.8, 4682.1, 5234.8]   # A12/A13 ... A15/A16
TILE_ATLAS_CELLS_EXT_B = [3803.8, 4320.2, 4886.5, 5473.3]   # B11/B12 ... B14/B15
TILE_ATLAS_CELLS_EXT_D = [4742.7]                           # D5/D6


# ATLAS gap and crack scintillators (E1-E4), active ITC (C10, D4) and the extended barrel at the nominal position of the ATLAS
# geometry (option TileAtlasGap, F41 conserto 21, 11/10/2026; needs TileAtlasItc). Sources: the public ATLAS geometry of the
# GeoModel project (geometry-ATLAS-R3S-2021-03-00-00.db, Run 3, with the crack scintillators of Run 3) and the Tile tables of
# the ATLAS geometry database (TILB-GEO-04, TICL-GEO-02, TileGlobals-09). The volumes of the GeoModel geometry carry the
# shift of the installed extended barrels and ITC (TileGlobals ZSHIFT, 40 mm on side A); the nominal positions are the
# ZOFFSET of TILB, as for the LAr end-caps (F45). On side A:
# - extended barrel (TILB section 2): front plate of 15 mm at z = 3519.5-3534.5 mm, 140 periods of 18.2536 mm (3534.5-6090 mm),
#   end plate of 20 mm (6090-6110 mm); cells by the number of periods of TICL: A12-A16 9/25/28/30/48, B11-B15 16/27/30/32/35,
#   D5/D6 65/75;
# - D4 (TILB section 3, Plug1): 17 periods of 18.1765 mm at z = 3210.5-3519.5 mm, steel r = 3440-3860 mm, tiles in two rows,
#   r = 3441.5-3818.5 mm (TICL: 17 tiles per row);
# - C10 (TILB section 4, Plug2): 5 periods of 18.1318 mm (z = 3424.8-3515.46 mm) and a last period of 4.04 mm with tiles only in
#   the first and third rows (TICL: 6/5/6 tiles per row), tiles r = 2991-3438 mm;
# - gap (TILB section 5): 12 mm scintillators at z = 3506-3518 mm in an aluminium box of 15 mm (z = 3504.5-3519.5 mm): E2 r =
#   2310.8-2650.8 mm (copy 0), E1 2652.8-2976.8 mm (copy 1);
# - crack (TILB section 6): 6 mm scintillators of polyvinyltoluene (Run 3) at z = 3493-3499 mm in an aluminium box of 8 mm
#   (3492-3500 mm): E4 r = 1317.8-1473.4 mm (copy 0), E3 1474.0-2313.4 mm (copy 1).
# Identifiers (ATLAS identifier dictionary, section 3): D4 tower 8 sampling 2, C10 tower 9 sampling 1, both two PMTs; E1-E4
# towers 10, 11, 13, 15, sampling 3, one PMT (pmt 0). Special modules (Athena TileGeoG4LookupBuilder): C10 with one PMT in
# modules 39-42 and 55-58 (pmt 0 on side C, pmt 1 on side A); D4 absent in EBA15 and EBC18, its energy going to D5.
# Not modelled: the support girders, the cable troughs, E4' and the MBTS.
TILE_ATLAS_GAP_EB_FRONT   = (3519.5*mm, 3534.5*mm)
TILE_ATLAS_GAP_EB_TILES   = (3534.5*mm, 6090.0*mm)
TILE_ATLAS_GAP_EB_END     = (6090.0*mm, 6110.0*mm)
TILE_ATLAS_GAP_EB_PERIOD  = (6090.0 - 3534.5)/140*mm
TILE_ATLAS_GAP_EB_PLATE_R = (2288*mm, 3860*mm)
TILE_ATLAS_GAP_EB_PERIODS = {'A': (12, [9, 25, 28, 30, 48]), 'B': (11, [16, 27, 30, 32, 35]), 'D': (5, [65, 75])}
TILE_ATLAS_GAP_D4  = dict(z=(3210.5*mm, 3519.5*mm), r=(3441.5*mm, 3818.5*mm), steel_r=(3440*mm, 3860*mm), periods=17)
TILE_ATLAS_GAP_C10 = dict(z=(3424.8*mm, 3519.5*mm), r=(2991*mm, 3438*mm), periods=5, period=18.1318*mm, last=4.04*mm,
                          rows=[(2991*mm, 3138*mm), (3141*mm, 3288*mm), (3291*mm, 3438*mm)])
TILE_ATLAS_GAP_GAP   = dict(box=(3504.5*mm, 3519.5*mm), scint=(3506*mm, 3518*mm), box_r=(2308.8*mm, 2978.8*mm),
                            cells={'E2': (2310.8*mm, 2650.8*mm), 'E1': (2652.8*mm, 2976.8*mm)})
TILE_ATLAS_GAP_CRACK = dict(box=(3492*mm, 3500*mm), scint=(3493*mm, 3499*mm), box_r=(1309.4*mm, 2341.4*mm),
                            cells={'E4': (1317.8*mm, 1473.4*mm), 'E3': (1474.0*mm, 2313.4*mm)})
# (tower, sampling) of the ATLAS identifier, section 3
TILE_ATLAS_GAP_ID = {'D4': (8, 2), 'C10': (9, 1), 'E1': (10, 3), 'E2': (11, 3), 'E3': (13, 3), 'E4': (15, 3)}
# polyvinyltoluene of the Run 3 crack scintillators (tile::Polyvinyltoluene of the public GeoModel geometry)
ATLAS_TILE_GAP_MIXTURES = {'ATLAS_TILE_PVT': (1.023002, {'C': 0.914709, 'H': 0.085291})}


def _roundToPeriod(z, z0):
    """Nearest boundary between two 18 mm periods, for periods starting at z0."""
    period = TILE_ATLAS_ABSORBER + TILE_ATLAS_TILE + TILE_ATLAS_CLEARANCE
    return z0 + round((z - z0) / period) * period


def _cellEta(boxes):
    """Eta of the geometric centre of the cell (area centroid of its boxes in the r-z plane) and delta eta taken at
    the mean radius of the cell, over the full z extent of the cell."""
    area = sum((b[1]-b[0])*(b[3]-b[2]) for b in boxes)
    rc = sum((b[1]-b[0])*(b[3]-b[2])*0.5*(b[0]+b[1]) for b in boxes) / area
    zc = sum((b[1]-b[0])*(b[3]-b[2])*0.5*(b[2]+b[3]) for b in boxes) / area
    rmean = 0.5*(min(b[0] for b in boxes) + max(b[1] for b in boxes))
    zmin = min(b[2] for b in boxes); zmax = max(b[3] for b in boxes)
    return math.asinh(zc/rc), math.asinh(zmax/rmean) - math.asinh(zmin/rmean)


def _ticlDeltaEta(name):
    """Delta eta of an ATLAS Tile cell in the TICL table (TICL-GEO-02 of the ATLAS geometry database): the ideal value that ATLAS
    keeps for the cell (TileGeoSectionBuilder::fillDescriptor, TileDetDescrManager.cxx: "keep ideal deta for the cell")."""
    n = name.rstrip('+-')
    special = {'D4': 0.1, 'E3': 0.4, 'E4': 0.12}
    if n in special: return special[n]
    return 0.2 if n.startswith('D') else 0.1


def _cellsFromRows(rows):
    """
    rows: list of (rmin, rmax, [(name, zmin, zmax), ...]); cells with the same name in different rows are one cell.
    Returns the table used by CaloHitMaker: one entry per box (r and z limits, cell index) and one per cell (name,
    eta, delta eta), cells in increasing z of their centre.
    """
    boxes = {}
    for rmin, rmax, cells in rows:
        for name, zmin, zmax in cells:
            boxes.setdefault(name, []).append((rmin, rmax, zmin, zmax))
    def zcentre(name):
        b = boxes[name]; area = sum((x[1]-x[0])*(x[3]-x[2]) for x in b)
        return sum((x[1]-x[0])*(x[3]-x[2])*0.5*(x[2]+x[3]) for x in b) / area
    names = sorted(boxes, key=zcentre)
    table = dict(Names=[], Eta=[], DeltaEta=[], BoxRMin=[], BoxRMax=[], BoxZMin=[], BoxZMax=[], BoxCell=[],
                 AtlasSection=[], AtlasTower=[], AtlasSampling=[], RCentre=[], ZCentre=[])
    for i, name in enumerate(names):
        eta, _ = _cellEta(boxes[name]); deta = _ticlDeltaEta(name)
        table['Names'].append(name); table['Eta'].append(round(eta, 5)); table['DeltaEta'].append(round(deta, 5))
        # ATLAS identifier fields (free-running hits) and area centroid in (r, z) of the cell (the ATLAS time, CaloHitMaker::tileTime)
        section, tower, sampling = atlasTileIdFields(name)
        b = boxes[name]; area = sum((x[1]-x[0])*(x[3]-x[2]) for x in b)
        table['AtlasSection'].append(section); table['AtlasTower'].append(tower); table['AtlasSampling'].append(sampling)
        table['RCentre'].append(sum((x[1]-x[0])*(x[3]-x[2])*0.5*(x[0]+x[1]) for x in b) / area)
        table['ZCentre'].append(zcentre(name))
        for rmin, rmax, zmin, zmax in boxes[name]:
            table['BoxRMin'].append(rmin); table['BoxRMax'].append(rmax)
            table['BoxZMin'].append(zmin); table['BoxZMax'].append(zmax); table['BoxCell'].append(i)
    return table


def _barrelRow(prefix, edges, zend, first=1, crosses_zero=False):
    """Cells of one barrel row, both sides. The side is in the name: '+' for z > 0, '-' for z < 0."""
    e = [_roundToPeriod(x, -TILE_ATLAS_BARREL_HALF_Z) for x in edges]
    cells = []
    if crosses_zero:   # D0: one cell from -e[0] to e[0], no side
        cells.append((f"{prefix}{first}", -e[0], e[0]))
        first += 1
        bounds = e + [zend]
    else:
        bounds = [0.0] + e + [zend]
    for k in range(len(bounds)-1):
        n = first + k
        cells.append((f"{prefix}{n}+", bounds[k], bounds[k+1]))
        cells.append((f"{prefix}{n}-", -bounds[k+1], -bounds[k]))
    return cells


def getAtlasTileCells(sampling_name, side=1, atlas_gap=False):
    """
    ATLAS tile cells for one sampling of the ATLAS-like tile calorimeter, as the (r, z) boxes read by CaloHitMaker.
    sampling_name: 'TileCal1', 'TileCal2', 'TileCal3' (long barrel) or 'TileExt1', 'TileExt2', 'TileExt3';
    side: +1 or -1 for the extended barrel. atlas_gap: the extended barrel at the nominal ATLAS position, with the cells
    of the ATLAS geometry database (see TILE_ATLAS_GAP_* above).
    """
    zb = TILE_ATLAS_BARREL_HALF_Z
    rb = TILE_ATLAS_BARREL_RADII
    re = TILE_ATLAS_EXTENDED_RADII
    if sampling_name == 'TileCal1':
        return _cellsFromRows([(rb[0], rb[1], _barrelRow('A', TILE_ATLAS_CELLS_BARREL_A, zb))])
    if sampling_name == 'TileCal2':
        brow = [(n.replace('B', 'BC', 1) if not n.startswith('B9') else n, z0, z1)
                for n, z0, z1 in _barrelRow('B', TILE_ATLAS_CELLS_BARREL_B, zb)]
        crow = [(n.replace('C', 'BC', 1), z0, z1) for n, z0, z1 in _barrelRow('C', TILE_ATLAS_CELLS_BARREL_C, zb)]
        return _cellsFromRows([(rb[1], TILE_ATLAS_CELLS_BC_RADIUS, brow), (TILE_ATLAS_CELLS_BC_RADIUS, rb[2], crow)])
    if sampling_name == 'TileCal3':
        return _cellsFromRows([(rb[2], rb[3], _barrelRow('D', TILE_ATLAS_CELLS_BARREL_D, zb, first=0, crosses_zero=True))])
    ext = {'TileExt1': ('A', TILE_ATLAS_CELLS_EXT_A, 12, re[0], re[1]),
           'TileExt2': ('B', TILE_ATLAS_CELLS_EXT_B, 11, re[1], re[2]),
           'TileExt3': ('D', TILE_ATLAS_CELLS_EXT_D, 5,  re[2], re[3])}
    prefix, edges, first, rmin, rmax = ext[sampling_name]
    z0, z1 = TILE_ATLAS_EXTENDED_Z_START, TILE_ATLAS_EXTENDED_Z_END
    bounds = [z0] + [_roundToPeriod(x, z0) for x in edges] + [z1]
    if atlas_gap:
        # nominal ATLAS extended barrel: cell boundaries from the number of periods of each cell (TICL-GEO-02)
        z0, z1 = TILE_ATLAS_GAP_EB_TILES
        first, counts = TILE_ATLAS_GAP_EB_PERIODS[prefix]
        bounds = [z0]
        for n in counts: bounds.append(bounds[-1] + n*TILE_ATLAS_GAP_EB_PERIOD)
        bounds[-1] = z1
    s = '+' if side > 0 else '-'
    cells = []
    for k in range(len(bounds)-1):
        lo, hi = (bounds[k], bounds[k+1]) if side > 0 else (-bounds[k+1], -bounds[k])
        cells.append((f"{prefix}{first+k}{s}", lo, hi))
    return _cellsFromRows([(rmin, rmax, cells)])


# ATLAS identifier fields (section, tower, sampling) of each ATLAS tile cell, kept in the cell table and used by the free-running
# hits of simu_trf.py.
# Fields and allowed combinations from the public ATLAS identifier dictionary, Athena (Apache 2.0),
# DetectorDescription/IdDictParser/data/IdDictTileCalorimeter.xml: section 1 = long barrel, 2 = extended barrel;
# sampling 0 = A, 1 = BC (B in the extended barrel), 2 = D; tower = the 0.1 eta tower of the cell. Allowed (section, tower):
# samplings, from the same dictionary: barrel tower 0: 0-2 (D0 only on side +1), 1, 3, 5, 7, 8: 0-1, 2, 4, 6: 0-2, 9: 0;
# extended barrel tower 10: 1-2, 11, 13, 14: 0-1, 12: 0-2, 15: 0.
_ATLAS_TILE_ALLOWED = {1: {0: (0, 1, 2), 1: (0, 1), 2: (0, 1, 2), 3: (0, 1), 4: (0, 1, 2), 5: (0, 1), 6: (0, 1, 2), 7: (0, 1),
                           8: (0, 1), 9: (0,)},
                       2: {10: (1, 2), 11: (0, 1), 12: (0, 1, 2), 13: (0, 1), 14: (0, 1), 15: (0,)}}

def atlasTileIdFields(name):
    """(section, tower, sampling) of the ATLAS identifier of an ATLAS tile cell, from its name (with or without the side
    sign): A1-A10, BC1-BC8, B9, D0-D3 in the long barrel; A12-A16, B11-B15, D5, D6 in the extended barrel."""
    n = name.rstrip('+-')
    letters = n.rstrip('0123456789'); number = int(n[len(letters):])
    if letters == 'A':
        fields = (1, number - 1, 0) if number <= 10 else (2, number - 1, 0)
    elif letters in ('BC', 'B'):
        fields = (1, number - 1, 1) if number <= 9 else (2, number - 1, 1)
    elif letters == 'D':
        fields = (1, 2*number, 2) if number <= 3 else (2, 10 + 2*(number - 5), 2)
    else:
        raise ValueError(f"not an ATLAS tile cell: {name}")
    section, tower, sampling = fields
    if sampling not in _ATLAS_TILE_ALLOWED.get(section, {}).get(tower, ()):
        raise ValueError(f"{name}: ({section}, {tower}, {sampling}) is not in the ATLAS identifier dictionary")
    return fields


def _getAtlasTileLayers(radii, zsize):
    """
    Layout of the three ATLAS-like tile layers: vertical plates with the ATLAS period, as many whole
    periods as fit in zsize (the remainder is left empty, half at each end).
    """
    period = TILE_ATLAS_ABSORBER + TILE_ATLAS_TILE + TILE_ATLAS_CLEARANCE
    nperiods = int(zsize // period)
    return [ dict( Plates            = Plates.Vertical,
                   NofLayers         = nperiods,
                   AbsorberThickness = TILE_ATLAS_ABSORBER,
                   GapThickness      = TILE_ATLAS_TILE,
                   LayerClearance    = TILE_ATLAS_CLEARANCE,
                   RMin              = radii[i],
                   RMax              = radii[i+1] ) for i in range(3) ]


def getTileBarrelCfg(atlas_geometry=False, atlas_cells=False):
    """
    Defines the geometry and readout configuration for the Tile Calorimeter (TileCal) Barrel.

    Constructs the physical volumes (Iron absorber + Scintillator gap) for the
    three longitudinal layers of the Tile Barrel and assigns readout parameters.

    Args:
        atlas_geometry (bool): If True, builds the ATLAS-like layout (tiles normal to the beam line,
                               18 mm period, ATLAS layer radii and z extent; see TILE_ATLAS_* above).
        atlas_cells (bool): If True (needs atlas_geometry), the cells are the ATLAS cells A1-A10, BC1-BC8, B9 and
                            D0-D3 (see TILE_ATLAS_CELLS_* above) instead of the eta x phi grid.

    Returns:
        List[Calorimeter]: A list of configured Calorimeter detector objects for the Tile Barrel.
    """

    basepath = os.environ['LORENZETTI_GEOMETRY_DATA_DIR']

    # TileCal 
    endcap_start = 3704.*mm
    gap_between_extended_barrel = 68.*cm
    tile_barrel_start = 0*m
    tile_barrel_end = (endcap_start - gap_between_extended_barrel)
    tile_barrel_z = (tile_barrel_start + tile_barrel_end) * 2

    if atlas_geometry:
        tile_barrel_z = 2*TILE_ATLAS_BARREL_HALF_Z
        layers = _getAtlasTileLayers( TILE_ATLAS_BARREL_RADII, tile_barrel_z )
    else:
        r1 = 228.3*cm + 4*(6.0*cm + 4.0*cm)
        r2 = r1 + 11*(6.2*cm + 3.8*cm)
        r3 = r2 + 5*(6.2*cm + 3.8*cm)
        layers = [ dict( Plates=Plates.Horizontal, NofLayers=4 , AbsorberThickness=6.0*cm, GapThickness=4.0*cm, RMin=228.3*cm, RMax=r1 ),
                   dict( Plates=Plates.Horizontal, NofLayers=11, AbsorberThickness=6.2*cm, GapThickness=3.8*cm, RMin=r1      , RMax=r2 ),
                   dict( Plates=Plates.Horizontal, NofLayers=5 , AbsorberThickness=6.2*cm, GapThickness=3.8*cm, RMin=r2      , RMax=r3 ) ]


    tilecal1_pv =  PhysicalVolume( Name               = "TILE::TileCal1",
                                   AbsorberMaterial   = "G4_Fe", # absorber
                                   GapMaterial        = "PLASTIC SCINTILLATOR", # gap
                                   **layers[0], # plates, layers, thicknesses and radii
                                   ZSize              = tile_barrel_z,
                                   X=0,Y=0,Z=0, # x,y,z (center in 0,0,0)
                                   Visualization = True,
                                   Color         = 'salmon'
                                   )

    tilecal2_pv =  PhysicalVolume( Name               = "TILE::TileCal2",
                                   AbsorberMaterial   = "G4_Fe", # absorber
                                   GapMaterial        = "PLASTIC SCINTILLATOR", # gap
                                   **layers[1], # plates, layers, thicknesses and radii
                                   ZSize              = tile_barrel_z,
                                   X=0,Y=0,Z=0, # x,y,z (center in 0,0,0)
                                   Visualization = True,
                                   Color         = 'violetred'
                                   )

    tilecal3_pv =  PhysicalVolume( Name               = "TILE::TileCal3",
                                   AbsorberMaterial   = "G4_Fe", # absorber
                                   GapMaterial        = "PLASTIC SCINTILLATOR", # gap
                                   **layers[2], # plates, layers, thicknesses and radii
                                   ZSize              = tile_barrel_z,
                                   X=0,Y=0,Z=0, # x,y,z (center in 0,0,0)
                                   Visualization = True,
                                   Color         = 'orangered'
                                   )


    #tilecal1_pv.Cuts = ProductionCuts(ElectronCut = 1, PositronCut = 1, GammaCut = 1)
    #tilecal2_pv.Cuts = ProductionCuts(ElectronCut = 1, PositronCut = 1, GammaCut = 1)
    #tilecal3_pv.Cuts = ProductionCuts(ElectronCut = 1, PositronCut = 1, GammaCut = 1)


    tilecal1_sv = SensitiveDetector( tilecal1_pv, DeltaEta = 0.1  , DeltaPhi = pi/32 )
    tilecal2_sv = SensitiveDetector( tilecal2_pv, DeltaEta = 0.1  , DeltaPhi = pi/32 )
    tilecal3_sv = SensitiveDetector( tilecal3_pv, DeltaEta = 0.2  , DeltaPhi = pi/32 )
    if atlas_cells:
        if not atlas_geometry:
            raise ValueError("The ATLAS tile cells (atlas_cells) need the ATLAS-like tile geometry (atlas_geometry).")
        tilecal1_sv.Cells = getAtlasTileCells("TileCal1")
        tilecal2_sv.Cells = getAtlasTileCells("TileCal2")
        tilecal3_sv.Cells = getAtlasTileCells("TileCal3")




    # Configure the electronic frontend and the detector parameters
    tilecal1_det = Calorimeter( tilecal1_sv, -6, 4, -3, # sensitive volume, bunch start, bunch end, sampling start,
                                CollectionKey   = "Collection_TileCal1", # collection key
                                Detector        = Detector.TILE, # detector type
                                Sampling        = CaloSampling.TileCal1, # sampling type
                                Shaper          = basepath + "/pulseTile.dat", # pulse shaper
                                Noise           = 20*MeV, # electronic noise
                                Samples         = 7, # how many samples
                                OFWeightsEnergy = [-0.3781,   -0.3572,    0.1808,    0.8125,   0.2767,    -0.2056,    -0.3292], # optimal filter parameters
                                OFWeightsTime   = [0.197277, -2.336666, -18.474749, -0.247639, 14.832119, 4.627806, 1.401852], # values get from COOL, Field 1. 
                              )

    # Configure the electronic frontend and the detector parameters
    tilecal2_det = Calorimeter( tilecal2_sv, -6, 4, -3, # sensitive volume, bunch start, bunch end, sampling start,
                                CollectionKey = "Collection_TileCal2", # collection key
                                Detector      = Detector.TILE, # detector type
                                Sampling      = CaloSampling.TileCal2, # sampling type
                                Shaper        = basepath + "/pulseTile.dat", # pulse shaper
                                Noise         = 20*MeV, # electronic noise
                                Samples       = 7, # how many samples
                                OFWeightsEnergy = [-0.3781,   -0.3572,    0.1808,    0.8125,   0.2767,    -0.2056,    -0.3292], # optimal filter parameters
                                OFWeightsTime   = [0.197277, -2.336666, -18.474749, -0.247639, 14.832119, 4.627806, 1.401852], # values get from COOL, Field 1. 
                              )

    # Configure the electronic frontend and the detector parameters
    tilecal3_det = Calorimeter( tilecal3_sv, -6, 4, -3, # sensitive volume, bunch start, bunch end, sampling start,
                                CollectionKey = "Collection_TileCal3", # collection key
                                Detector      = Detector.TILE, # detector type
                                Sampling      = CaloSampling.TileCal3, # sampling type
                                Shaper        = basepath + "/pulseTile.dat", # pulse shaper
                                Noise         = 20*MeV, # electronic noise
                                Samples       = 7, # how many samples
                                OFWeightsEnergy = [-0.3781,   -0.3572,    0.1808,    0.8125,   0.2767,    -0.2056,    -0.3292], # optimal filter parameters
                                OFWeightsTime   = [0.197277, -2.336666, -18.474749, -0.247639, 14.832119, 4.627806, 1.401852], # values get from COOL, Field 1. 
                              )



    return [tilecal1_det, tilecal2_det, tilecal3_det]






def getTileExtendedCfg(left_side=False, atlas_geometry=False, atlas_cells=False, atlas_gap=False):
    """
    Defines the geometry and readout configuration for the Tile Calorimeter Extended Barrel.

    Constructs the physical volumes and assigns readout parameters for the Extended Barrel.
    Since the detector is symmetric but has distinct physical volumes for A-side and C-side,
    this function allows configuring either side.

    Args:
        left_side (bool): If True, configures the C-side (negative z). 
                          If False, configures the A-side (positive z).
        atlas_geometry (bool): If True, builds the ATLAS-like layout (tiles normal to the beam line,
                               18 mm period, ATLAS layer radii and z extent; see TILE_ATLAS_* above).
        atlas_cells (bool): If True (needs atlas_geometry), the cells are the ATLAS cells A12-A16, B11-B15, D5 and
                            D6 (see TILE_ATLAS_CELLS_* above) instead of the eta x phi grid.
        atlas_gap (bool): If True (needs atlas_cells), the extended barrel at the nominal position of the ATLAS geometry,
                          with its period and cells (see TILE_ATLAS_GAP_* above; F41 conserto 21).

    Returns:
        List[Calorimeter]: A list of configured Calorimeter detector objects for the Tile Extended Barrel.
    """


    # TileExt Barrel
    endcap_start = 3.704*m
    extended_barrel_start = endcap_start
    extended_barrel_zsize = 2.83*m
    basepath = os.environ['LORENZETTI_GEOMETRY_DATA_DIR']
    sign = -1 if left_side else 1
    side_name = 'B' if left_side else 'A'

    if atlas_geometry:
        extended_barrel_start = TILE_ATLAS_EXTENDED_Z_START
        extended_barrel_zsize = TILE_ATLAS_EXTENDED_Z_END - TILE_ATLAS_EXTENDED_Z_START
        layers = _getAtlasTileLayers( TILE_ATLAS_EXTENDED_RADII, extended_barrel_zsize )
        if atlas_gap:
            if not atlas_cells:
                raise ValueError("atlas_gap needs the ATLAS tile cells (atlas_cells).")
            extended_barrel_start = TILE_ATLAS_GAP_EB_TILES[0]
            extended_barrel_zsize = TILE_ATLAS_GAP_EB_TILES[1] - TILE_ATLAS_GAP_EB_TILES[0]
            for lay in layers:
                lay.update( NofLayers = 140, AbsorberThickness = TILE_ATLAS_GAP_EB_PERIOD - TILE_ATLAS_TILE - TILE_ATLAS_CLEARANCE )
    else:
        r1 = 228.3*cm + 4*(6.0*cm + 4.0*cm)
        r2 = r1 + 11*(6.2*cm + 3.8*cm)
        r3 = r2 + 5*(6.2*cm + 3.8*cm)
        layers = [ dict( Plates=Plates.Horizontal, NofLayers=4 , AbsorberThickness=6.0*cm, GapThickness=4.0*cm, RMin=228.3*cm, RMax=r1 ),
                   dict( Plates=Plates.Horizontal, NofLayers=11, AbsorberThickness=6.2*cm, GapThickness=3.8*cm, RMin=r1      , RMax=r2 ),
                   dict( Plates=Plates.Horizontal, NofLayers=5 , AbsorberThickness=6.2*cm, GapThickness=3.8*cm, RMin=r2      , RMax=r3 ) ]


    tilecalExt1_pv =  PhysicalVolume( Name               = "TILE::TileCalExt1::"+side_name,
                                      AbsorberMaterial   = "G4_Fe", # absorber
                                      GapMaterial        = "PLASTIC SCINTILLATOR", # gap
                                      **layers[0], # plates, layers, thicknesses and radii
                                      ZSize              = extended_barrel_zsize  ,
                                      X=0,Y=0,Z=sign*(extended_barrel_start + 0.5*extended_barrel_zsize), # x,y,z 
                                      Visualization = True,
                                      Color         = 'salmon',
                                    )
    tilecalExt2_pv =  PhysicalVolume( Name               = "TILE::TileCalExt2::"+side_name,
                                      AbsorberMaterial   = "G4_Fe", # absorber
                                      GapMaterial        = "PLASTIC SCINTILLATOR", # gap
                                      **layers[1], # plates, layers, thicknesses and radii
                                      ZSize              = extended_barrel_zsize ,
                                      X=0,Y=0,Z=sign*(extended_barrel_start + 0.5*extended_barrel_zsize), # x,y,z 
                                      Visualization = True,
                                      Color         = 'violetred'
                                    )

    tilecalExt3_pv =  PhysicalVolume( Name               = "TILE::TileCalExt3::"+side_name,
                                      AbsorberMaterial   = "G4_Fe", # absorber
                                      GapMaterial        = "PLASTIC SCINTILLATOR", # gap
                                      **layers[2], # plates, layers, thicknesses and radii
                                      ZSize              = extended_barrel_zsize ,
                                      X=0,Y=0,Z=sign*(extended_barrel_start + 0.5*extended_barrel_zsize), # x,y,z 
                                      Visualization = True,
                                      Color         = 'orangered'
                                    )


    tilecalExt1_sv = SensitiveDetector( tilecalExt1_pv, DeltaEta = 0.1  , DeltaPhi = pi/32  )
    tilecalExt2_sv = SensitiveDetector( tilecalExt2_pv, DeltaEta = 0.1  , DeltaPhi = pi/32  )
    tilecalExt3_sv = SensitiveDetector( tilecalExt3_pv, DeltaEta = 0.2  , DeltaPhi = pi/32  )
    if atlas_cells:
        if not atlas_geometry:
            raise ValueError("The ATLAS tile cells (atlas_cells) need the ATLAS-like tile geometry (atlas_geometry).")
        tilecalExt1_sv.Cells = getAtlasTileCells("TileExt1", sign, atlas_gap)
        tilecalExt2_sv.Cells = getAtlasTileCells("TileExt2", sign, atlas_gap)
        tilecalExt3_sv.Cells = getAtlasTileCells("TileExt3", sign, atlas_gap)


    # Configure the electronic frontend and the detector parameters
    tilecalExt1_det = Calorimeter( tilecalExt1_sv, -6, 4, -3, # sensitive volume, bunch start, bunch end, sampling start,
                                   CollectionKey   = "Collection_TileExt1_"+side_name, # collection key
                                   Detector        = Detector.TILE, # detector type
                                   Sampling        = CaloSampling.TileExt1, # sampling type
                                   Shaper          = basepath + "/pulseTile.dat", # pulse shaper
                                   Noise           = 20*MeV, # electronic noise
                                   Samples         = 7, # how many samples
                                   OFWeightsEnergy = [-0.3781,   -0.3572,    0.1808,    0.8125,   0.2767,    -0.2056,    -0.3292], # optimal filter parameters
                                   OFWeightsTime   = [0.197277, -2.336666, -18.474749, -0.247639, 14.832119, 4.627806, 1.401852], # values get from COOL, Field 1. 
                                 )

    # Configure the electronic frontend and the detector parameters
    tilecalExt2_det = Calorimeter( tilecalExt2_sv, -6, 4, -3, # sensitive volume, bunch start, bunch end, sampling start,
                                   CollectionKey   = "Collection_TileExt2_"+side_name, # collection key
                                   Detector        = Detector.TILE, # detector type
                                   Sampling        = CaloSampling.TileExt2, # sampling type
                                   Shaper          = basepath + "/pulseTile.dat", # pulse shaper
                                   Noise           = 20*MeV, # electronic noise
                                   Samples         = 7, # how many samples
                                   OFWeightsEnergy = [-0.3781,   -0.3572,    0.1808,    0.8125,   0.2767,    -0.2056,    -0.3292], # optimal filter parameters
                                   OFWeightsTime   = [0.197277, -2.336666, -18.474749, -0.247639, 14.832119, 4.627806, 1.401852], # values get from COOL, Field 1. 
                                 )

    # Configure the electronic frontend and the detector parameters
    tilecalExt3_det = Calorimeter( tilecalExt3_sv, -6, 4, -3, # sensitive volume, bunch start, bunch end, sampling start,
                                   CollectionKey   = "Collection_TileExt3_"+side_name, # collection key
                                   Detector        = Detector.TILE, # detector type
                                   Sampling        = CaloSampling.TileExt3, # sampling type
                                   Shaper          = basepath + "/pulseTile.dat", # pulse shaper
                                   Noise           = 20*MeV, # electronic noise
                                   Samples         = 7, # how many samples
                                   OFWeightsEnergy = [-0.3781,   -0.3572,    0.1808,    0.8125,   0.2767,    -0.2056,    -0.3292], # optimal filter parameters
                                   OFWeightsTime   = [0.197277, -2.336666, -18.474749, -0.247639, 14.832119, 4.627806, 1.401852], # values get from COOL, Field 1. 
                                 )
    
    return [tilecalExt1_det, tilecalExt2_det, tilecalExt3_det]



def _gapPv(name, absorber, gap, nlayers, absorber_t, gap_t, clearance, r, z, sign, envelope=False):
    za, zb = (z[0], z[1]) if sign > 0 else (-z[1], -z[0])
    pv = PhysicalVolume( Name = name, Plates = Plates.Vertical, AbsorberMaterial = absorber, GapMaterial = gap,
                         NofLayers = nlayers, AbsorberThickness = absorber_t, GapThickness = gap_t, LayerClearance = clearance,
                         RMin = r[0], RMax = r[1], ZSize = z[1] - z[0], X=0, Y=0, Z=0.5*(za + zb), Visualization = True,
                         Color = 'salmon' )
    if envelope: pv.Envelope = True
    return pv


def _gapCell(name, sign, r, z, extra=None):
    """Cell table of one ATLAS gap/ITC cell (one box) for CaloHitMaker (see TILE_ATLAS_GAP_* above)."""
    za, zb = (z[0], z[1]) if sign > 0 else (-z[1], -z[0])
    tower, sampling = TILE_ATLAS_GAP_ID[name]
    rc, zc = 0.5*(r[0] + r[1]), 0.5*(za + zb)
    eta = math.asinh(zc/rc); deta = _ticlDeltaEta(name)
    table = dict(Names=[name + ('+' if sign > 0 else '-')], Eta=[round(eta, 5)], DeltaEta=[round(deta, 5)],
                 BoxRMin=[r[0]], BoxRMax=[r[1]], BoxZMin=[za], BoxZMax=[zb], BoxCell=[0],
                 AtlasSection=[3], AtlasTower=[tower], AtlasSampling=[sampling], RCentre=[rc], ZCentre=[zc],
                 NPmt=[1 if name.startswith('E') else 2])
    if extra: table.update(extra)
    return table


def getAtlasTileGapCfg(left_side=False):
    """
    The ATLAS gap and crack scintillators (E1-E4) and the active ITC (C10, D4) on one side, as Calorimeter samplings with the
    cells, identifiers and special modules of ATLAS (see TILE_ATLAS_GAP_* above; F41 conserto 21). Simulation only.
    """
    basepath = os.environ['LORENZETTI_GEOMETRY_DATA_DIR']
    sign = -1 if left_side else 1
    side_name = 'B' if left_side else 'A'
    out = []
    def calo(sv, key, sampling):
        # eta edges of the cell itself, for the monitoring histograms (the default 0.1 grid leaves E1 with a single edge)
        eta, deta = sv.Cells['Eta'][0], sv.Cells['DeltaEta'][0]
        sv.EtaBins = [round(eta - deta/2, 5), round(eta + deta/2, 5)]; sv.EtaMin = sv.EtaBins[0]; sv.EtaMax = sv.EtaBins[-1]
        return Calorimeter( sv, -6, 4, -3, CollectionKey = key + "_" + side_name, Detector = Detector.TILE, Sampling = sampling,
                            Shaper = basepath + "/pulseTile.dat", Noise = 20*MeV, Samples = 7,
                            OFWeightsEnergy = [-0.3781, -0.3572, 0.1808, 0.8125, 0.2767, -0.2056, -0.3292],
                            OFWeightsTime   = [0.197277, -2.336666, -18.474749, -0.247639, 14.832119, 4.627806, 1.401852] )
    # D4: 17 periods; ATLAS U-shape of the long barrel, BC layer (tile rows 4-5); absent in EBA15 / EBC18 (energy to D5)
    d4 = TILE_ATLAS_GAP_D4
    period = (d4['z'][1] - d4['z'][0]) / d4['periods']
    pv = _gapPv("TILE::ITC::D4::" + side_name, "G4_Fe", "PLASTIC SCINTILLATOR", d4['periods'],
                period - TILE_ATLAS_TILE - TILE_ATLAS_CLEARANCE, TILE_ATLAS_TILE, TILE_ATLAS_CLEARANCE, d4['r'], d4['z'], sign)
    d5 = getAtlasTileCells("TileExt3", sign, atlas_gap=True); i5 = [n.rstrip('+-') for n in d5['Names']].index('D5')
    sv = SensitiveDetector( pv, DeltaEta = 0.1, DeltaPhi = pi/32, Segment = 5 )
    sv.Cells = _gapCell('D4', sign, d4['r'], d4['z'],
                        dict(UShapePart=0, UShapeLayer=1, SpecialModule=[14 if sign > 0 else 17], SpecialNPmt=[0],
                             ReplaceSection=2, ReplaceTower=d5['AtlasTower'][i5], ReplaceSampling=d5['AtlasSampling'][i5],
                             ReplaceRCentre=d5['RCentre'][i5], ReplaceZCentre=d5['ZCentre'][i5],
                             # the hit of D5 in the normal chain: the collection of TileExt3 on this side (segment 0) and the
                             # hash of its D5 without the phi bin (CaloHitMaker::hash, bin = 64 cell + phi)
                             ReplaceCollectionKey="Collection_TileExt3_" + side_name,
                             ReplaceHashBase=int((CaloSampling.TileExt3 + 17*(1 if sign > 0 else 2))*10**7 + 64*i5)))
    out.append( calo(sv, "Collection_TileGapD4", CaloSampling.TileExt3) )
    # C10: 5 periods and a last thin period (rows 1 and 3); the maker volume is an envelope over both; ATLAS U-shape of the
    # long barrel, A layer (tile rows 1-3); one PMT in modules 39-42 and 55-58 (pmt 0 on side C, pmt 1 on side A)
    c10 = TILE_ATLAS_GAP_C10
    env = _gapPv("TILE::ITC::C10::" + side_name, "G4_Fe", "PLASTIC SCINTILLATOR", 1, 1*mm, 1*mm, 0, c10['r'], c10['z'], sign,
                 envelope=True)
    sv = SensitiveDetector( env, DeltaEta = 0.1, DeltaPhi = pi/32, Segment = 5 )
    special = list(range(38, 42)) + list(range(54, 58))
    sv.Cells = _gapCell('C10', sign, c10['r'], c10['z'],
                        dict(UShapePart=0, UShapeLayer=0, SpecialModule=special, SpecialNPmt=[-1 if sign > 0 else 1]*len(special)))
    out.append( calo(sv, "Collection_TileGapC10", CaloSampling.TileExt2) )
    # E1-E4: one PMT (pmt 0)
    for seg, (box, name, material) in enumerate(((TILE_ATLAS_GAP_GAP, 'E1', "PLASTIC SCINTILLATOR"),
                                                 (TILE_ATLAS_GAP_GAP, 'E2', "PLASTIC SCINTILLATOR"),
                                                 (TILE_ATLAS_GAP_CRACK, 'E3', "ATLAS_TILE_PVT"),
                                                 (TILE_ATLAS_GAP_CRACK, 'E4', "ATLAS_TILE_PVT"))):
        r = box['cells'][name]
        z = (box['scint'][0], box['scint'][1] + (1*mm if name in ('E1', 'E2') else 0.5*mm))   # scintillator, then the air of the wrapper (as vacuum)
        pv = _gapPv(f"TILE::Gap::{name}::" + side_name, "Vacuum", material, 1, z[1] - box['scint'][1],
                    box['scint'][1] - box['scint'][0], 0, r, z, sign)
        sv = SensitiveDetector( pv, DeltaEta = 0.1, DeltaPhi = pi/32, Segment = 5 + seg )
        sv.Cells = _gapCell(name, sign, r, box['scint'])
        out.append( calo(sv, f"Collection_TileGap{name}", CaloSampling.TileExt1) )
    return out


def getAtlasTileGapVolumesCfg(left_side=False):
    """
    Passive volumes of the ATLAS gap/ITC and of the nominal extended barrel on one side (see TILE_ATLAS_GAP_* above): the
    front and end plates of the extended barrel, the steel of D4 above its tiles, the volumes of C10 (5 periods and the last
    thin period) inside its envelope, and the aluminium boxes of the gap and crack scintillators. Simulation only.
    """
    from .PhysicalVolume import ProductionCuts
    sign = -1 if left_side else 1
    side_name = 'B' if left_side else 'A'
    vols = []
    def tube(name, material, r, z):
        za, zb = (z[0], z[1]) if sign > 0 else (-z[1], -z[0])
        pv = PhysicalVolume( Name = name + "::" + side_name, Plates = Plates.Vertical, AbsorberMaterial = material,
                             GapMaterial = material, NofLayers = 1, AbsorberThickness = (z[1] - z[0])/2,
                             GapThickness = (z[1] - z[0])/2, RMin = r[0], RMax = r[1], ZSize = z[1] - z[0], X=0, Y=0,
                             Z=0.5*(za + zb), Visualization = True, Color = 'gray' )
        pv.Cuts = ProductionCuts(ElectronCut = 1, PositronCut = 1, GammaCut = 1)
        vols.append(pv)
    tube("DM::TileGap::EBFrontPlate", "G4_Fe", TILE_ATLAS_GAP_EB_PLATE_R, TILE_ATLAS_GAP_EB_FRONT)
    tube("DM::TileGap::EBEndPlate", "G4_Fe", TILE_ATLAS_GAP_EB_PLATE_R, TILE_ATLAS_GAP_EB_END)
    d4 = TILE_ATLAS_GAP_D4
    tube("DM::TileGap::D4Steel", "G4_Fe", (d4['r'][1], d4['steel_r'][1]), d4['z'])
    c10 = TILE_ATLAS_GAP_C10
    z5 = (c10['z'][0], c10['z'][0] + c10['periods']*c10['period'])
    vols.append( _gapPv("TILE::ITC::C10::Periods::" + side_name, "G4_Fe", "PLASTIC SCINTILLATOR", c10['periods'],
                        c10['period'] - TILE_ATLAS_TILE - TILE_ATLAS_CLEARANCE, TILE_ATLAS_TILE, TILE_ATLAS_CLEARANCE,
                        c10['r'], z5, sign) )
    zl = (z5[1], c10['z'][1])
    for k, r in ((1, c10['rows'][0]), (3, c10['rows'][2])):
        vols.append( _gapPv(f"TILE::ITC::C10::Last{k}::" + side_name, "G4_Fe", "PLASTIC SCINTILLATOR", 1,
                            (zl[1] - zl[0]) - TILE_ATLAS_TILE, TILE_ATLAS_TILE, 0, r, zl, sign) )
    tube("DM::TileGap::C10LastSteel", "G4_Fe", (c10['rows'][0][1], c10['rows'][2][0]), zl)
    for name, box in (("Gap", TILE_ATLAS_GAP_GAP), ("Crack", TILE_ATLAS_GAP_CRACK)):
        tube(f"DM::TileGap::{name}BoxFront", "G4_Al", box['box_r'], (box['box'][0], box['box'][0] + 0.5*mm))
        tube(f"DM::TileGap::{name}BoxBack", "G4_Al", box['box_r'], (box['box'][1] - 0.5*mm, box['box'][1]))
    return vols
