
__all__ = ["getCrackVolumesCfg", "getDMVolumesCfg", "getAtlasEndcapCryostatCfg", "getAtlasBarrelCryostatCfg", "getAtlasFcalCfg"]

from GaugiKernel.constants import m,cm,mm
from .PhysicalVolume import PhysicalVolume, Plates, ProductionCuts
from .TILE import TILE_ATLAS_BARREL_HALF_Z, TILE_ATLAS_EXTENDED_Z_START
from .ECAL import PSE_ATLAS_R, PSE_ATLAS_Z, PSB_ATLAS_Z
from .AtlasBarrelFront import ATLAS_BARREL_FRONT_MIXTURES, ATLAS_BARREL_FRONT_VOLUMES
from .AtlasFCal import ATLAS_FCAL_VOLUMES
from .AtlasBarrelCryostat import ATLAS_BARREL_CRYOSTAT_VOLUMES


def getCrackVolumesCfg(left_side=False, tile_atlas_geometry=False, tile_atlas_itc=False, atlas_barrel_cryostat=False,
                       atlas_emec=False, atlas_emb_cells=False, atlas_cryostat_pieces=False, tile_atlas_gap=False):
    """
    Dead material in the crack between the barrel and the endcaps.

    Args:
        left_side (bool): If True, the C-side (negative z).
        tile_atlas_geometry (bool): If True, the aluminium block that stands for the ITC fills the gap of the
                                    ATLAS-like tile calorimeter (TILE_ATLAS_BARREL_HALF_Z to
                                    TILE_ATLAS_EXTENDED_Z_START) instead of the default gap.
        tile_atlas_itc (bool): If True (needs tile_atlas_geometry), the gap between the tile barrel and the extended
                               barrel is built as in ATLAS instead of the aluminium block: the plug of the ITC (D4 and
                               C10, passive) and the cables and services (see getAtlasItcCfg).
        atlas_barrel_cryostat (bool): With tile_atlas_itc, the services leave room for the step of the warm vessel of the
                               ATLAS barrel cryostat (see getAtlasBarrelCryostatCfg).
        atlas_emec (bool): With the ATLAS-like EMEC (geometry/python/v1/EMEC.py), the EM crack block ends at the front of
                           the moved end-cap presampler (|z| = 3697 mm) instead of 3717.5 mm, with the same two 43 mm
                           aluminium plates and 96.75 mm of liquid argon in each layer instead of 107 mm (F41 conserto
                           16, decision of 06/10/2026). The space up to the end-cap cryostat cylinders is left empty.
        atlas_emb_cells (bool): With the ATLAS-like barrel cells (geometry/python/v1/ECAL.py), the block has a cavity for the
                           end-cap presampler of ATLAS (|z| = 3622-3626 mm, r = 1231.74-1701.98 mm; see getAtlasPseCfg): the
                           liquid argon layer that contains it is split in z within that radial range (F41 conserto 17,
                           decision of 09/10/2026). Same materials and thicknesses.
        tile_atlas_gap (bool): With the ATLAS gap/crack scintillators and the active ITC (geometry/python/v1/TILE.py, F41
                           conserto 21; needs tile_atlas_itc, atlas_emb_cells and atlas_cryostat_pieces): the first liquid argon
                           layer of the EM crack block leaves room for the aluminium box of the crack scintillators (|z| =
                           3492-3500 mm, r = 1308-2232 mm), the plug of the ITC is not built here (the active D4 and C10 come
                           from TILE.py) and the services fill the space around the ATLAS plug and scintillators.
    """

    sign = -1 if left_side else 1
    side_name = 'B' if left_side else 'A'

    endcap_start = 3704.*mm
    gap_between_extended_barrel = 68.*cm
    crack_material_size = gap_between_extended_barrel
    crack_start = endcap_start - gap_between_extended_barrel
    if tile_atlas_geometry:
        crack_start = TILE_ATLAS_BARREL_HALF_Z
        crack_material_size = TILE_ATLAS_EXTENDED_Z_START - TILE_ATLAS_BARREL_HALF_Z
    crack_em_start = 3400*mm + 35*mm/2



    nlayers=2; absorber=4.3*cm; gap=10.7*cm; zsize=nlayers*(absorber+gap)
    if atlas_emec:
        # the block ends at the front of the moved presampler: 3697 mm = EMEC face 3702 mm - 5 mm (see above)
        crack_em_end = 3697.0*mm
        gap = (crack_em_end - crack_em_start - nlayers*absorber) / nlayers; zsize = nlayers*(absorber+gap)
    crack_em_pv =  PhysicalVolume( Name               = "DM::Crack::EM::"+side_name, 
                                    Plates             = Plates.Vertical, # Logical type
                                    AbsorberMaterial   = "G4_Al", # absorber
                                    GapMaterial        = "liquidArgon", # gap
                                    NofLayers          = nlayers, # layers
                                    AbsorberThickness  = absorber, # abso
                                    GapThickness       = gap, # gap
                                    RMin               = 900*mm, # radio min,
                                    RMax               = 2232*mm, # radio max 
                                    ZSize              = zsize,
                                    X=0,Y=0,Z=sign * (crack_em_start + zsize/2),
                                    Visualization = True,
                                    Color         = 'gray'
                                    )


    nlayers=1; absorber=200*cm; gap=1*mm; rsize=nlayers*(absorber+gap)
    crack_tile_pv =  PhysicalVolume( Name               = "DM::Crack::TILE::"+side_name, 
                                     Plates             = Plates.Horizontal, # Logical type
                                     AbsorberMaterial   = "G4_Al", # absorber
                                     GapMaterial        = "Vacuum", # gap
                                     NofLayers          = nlayers, # layers
                                     AbsorberThickness  = absorber, # abso
                                     GapThickness       = gap, # gap
                                     RMin               = 228.3*cm, #crack_em_pv.RMax, #228.3*cm, # radio min,
                                     RMax               = 228.3*cm + rsize, # radio max 
                                     ZSize              = crack_material_size,
                                     X=0,Y=0,Z=sign * (crack_start + crack_material_size/2),
                                     Visualization = True,
                                     Color         = 'gray'
                                     )


    crack_em_pv.Cuts     = ProductionCuts(ElectronCut = 1, PositronCut = 1, GammaCut = 1)
    crack_tile_pv.Cuts   = ProductionCuts(ElectronCut = 1, PositronCut = 1, GammaCut = 1)

    crack_em = [crack_em_pv]
    if tile_atlas_gap and not (tile_atlas_itc and atlas_emb_cells and atlas_cryostat_pieces):
        raise ValueError("tile_atlas_gap needs tile_atlas_itc, atlas_emb_cells and the ATLAS pieces of the barrel cryostat.")
    if atlas_emb_cells:
        crack_em = _crackWithPresamplerCavity(side_name, sign, crack_em_start, crack_em_pv.NofLayers,
                                              crack_em_pv.AbsorberThickness, crack_em_pv.GapThickness,
                                              crack_slot=CRACK_SCINT_SLOT if tile_atlas_gap else None)

    if tile_atlas_itc:
        if not tile_atlas_geometry:
            raise ValueError("tile_atlas_itc needs tile_atlas_geometry.")
        return crack_em + getAtlasItcCfg(left_side=left_side, atlas_barrel_cryostat=atlas_barrel_cryostat,
                                         atlas_cryostat_pieces=atlas_cryostat_pieces, tile_atlas_gap=tile_atlas_gap)
    return crack_em + [crack_tile_pv]


# Room left in the EM crack block for the aluminium box of the ATLAS crack scintillators (|z| and r, mm; F41 conserto 21)
CRACK_SCINT_SLOT = ((3492.0*mm, 3500.0*mm), (1308.0*mm, 2232.0*mm))


def _crackWithPresamplerCavity(side_name, sign, z_start, nlayers, absorber, gap, crack_slot=None):
    """
    DM::Crack::EM as pieces of one material, the same layers (liquid argon, then aluminium, from the interaction point), with
    the liquid argon layer that contains the ATLAS-like end-cap presampler split in z within its radial range (cavity). With
    crack_slot ((z0, z1), (r0, r1)), the liquid argon layer that contains it is split the same way (crack scintillators).
    """
    rmin, rmax = 900*mm, 2232*mm
    vols = []
    def piece(name, material, r0, r1, z0, z1):
        za, zb = (z0, z1) if sign > 0 else (-z1, -z0)
        pv = PhysicalVolume( Name = f"DM::Crack::EM::{name}::{side_name}", Plates = Plates.Vertical,
                             AbsorberMaterial = material, GapMaterial = material, NofLayers = 1,
                             AbsorberThickness = (z1 - z0)/2, GapThickness = (z1 - z0)/2, RMin = r0, RMax = r1,
                             ZSize = z1 - z0, X=0,Y=0,Z=0.5*(za + zb), Visualization = True, Color = 'gray' )
        pv.Cuts = ProductionCuts(ElectronCut = 1, PositronCut = 1, GammaCut = 1)
        vols.append(pv)
    z = z_start; found = False
    for k in range(nlayers):
        z0, z1 = z, z + gap
        if crack_slot and z0 < crack_slot[0][0] and crack_slot[0][1] < z1:
            (sz0, sz1), (sr0, sr1) = crack_slot
            piece(f"LAr{k+1}::Inner", "liquidArgon", rmin, sr0, z0, z1)
            piece(f"LAr{k+1}::Front", "liquidArgon", sr0, sr1, z0, sz0)
            piece(f"LAr{k+1}::Back", "liquidArgon", sr0, sr1, sz1, z1)
        elif z0 < PSE_ATLAS_Z[0] and PSE_ATLAS_Z[1] < z1:
            found = True
            piece(f"LAr{k+1}::Inner", "liquidArgon", rmin, PSE_ATLAS_R[0], z0, z1)
            piece(f"LAr{k+1}::Outer", "liquidArgon", PSE_ATLAS_R[1], rmax, z0, z1)
            piece(f"LAr{k+1}::Front", "liquidArgon", PSE_ATLAS_R[0], PSE_ATLAS_R[1], z0, PSE_ATLAS_Z[0])
            piece(f"LAr{k+1}::Back", "liquidArgon", PSE_ATLAS_R[0], PSE_ATLAS_R[1], PSE_ATLAS_Z[1], z1)
        else:
            piece(f"LAr{k+1}", "liquidArgon", rmin, rmax, z0, z1)
        piece(f"Al{k+1}", "G4_Al", rmin, rmax, z1, z1 + absorber)
        z = z1 + absorber
    if not found:
        raise RuntimeError("DM::Crack::EM: no liquid argon layer contains the end-cap presampler")
    return vols


# The gap between the tile barrel (|z| < 2808 mm) and the extended barrel (|z| > 3554 mm) as in ATLAS. The gap "is filled
# with cables and services for the inner detector as well as power supplies and services for the barrel liquid-argon
# calorimeter"; "at the outer radius of the detector, a reduced section of a standard tile-calorimeter sub-module, the
# plug, provides additional coverage" (JINST 3 (2008) S08003, sec. 5.5). Boxes from fig. 5.12 of the same paper:
# D4 z 3225-3535 mm, r 3461-3850 mm; C10 z 3444-3531 mm, r 2988-3457 mm.
# - Plug: tiles normal to the beam line with the period of the ATLAS-like tile calorimeter (14 mm steel, 3 mm
#   scintillator, 1 mm clearance), passive (no cells): D4 with 17 periods (z 3227-3533 mm), C10 with 4 (3451.5-3523.5 mm).
# - Cables and services: the mass is not given by the paper; aluminium with 5% of the volume, from a fit of the
#   interaction lengths at the end of the tile calorimeter to fig. 5.2 of the paper for |eta| = 0.85 to 1.05 (the fit
#   gives 0 to 5%), in three boxes around the plug, in shells of 50 mm or less.
# Not modelled: the gap and cryostat scintillators E1-E4.
ATLAS_ITC_SERVICES_FRACTION = 0.05

def getAtlasItcCfg(left_side=False, atlas_barrel_cryostat=False, atlas_cryostat_pieces=False, tile_atlas_gap=False):
    """
    Plug of the ITC and services of the gap (see above). With atlas_barrel_cryostat the services leave room for the step of
    the warm vessel of the barrel cryostat (r = 2250 to 2775 mm, |z| = 2865 to 3405 mm; see getAtlasBarrelCryostatCfg),
    keeping the same 5% of aluminium in the remaining volume. With atlas_cryostat_pieces (the ATLAS pieces of the barrel
    cryostat, F41 conserto 14b) the step of the warm vessel starts at |z| = 2850 mm, as in the ATLAS geometry.
    """
    sign = -1 if left_side else 1
    side_name = 'B' if left_side else 'A'
    period = 18*mm; steel = 14*mm; tile = 3*mm; clearance = 1*mm
    volumes = []
    plug = () if tile_atlas_gap else (("D4", 17, 3380*mm, 3461*mm, 3850*mm), ("C10", 4, 3487.5*mm, 2988*mm, 3457*mm))
    for name, nper, zc, rmin, rmax in plug:
        pv = PhysicalVolume( Name               = "DM::ITC::"+name+"::"+side_name,
                             Plates             = Plates.Vertical,
                             AbsorberMaterial   = "G4_Fe",
                             GapMaterial        = "PLASTIC SCINTILLATOR",
                             NofLayers          = nper,
                             AbsorberThickness  = steel,
                             GapThickness       = tile,
                             LayerClearance     = clearance,
                             RMin               = rmin,
                             RMax               = rmax,
                             ZSize              = nper*period,
                             X=0,Y=0,Z=sign*zc,
                             Visualization = True,
                             Color         = 'gray' )
        pv.Cuts = ProductionCuts(ElectronCut = 1, PositronCut = 1, GammaCut = 1)
        volumes.append(pv)
    caixas = ((2808*mm, 3225*mm, 2283*mm, 3850*mm), (3225*mm, 3444*mm, 2283*mm, 3461*mm), (3444*mm, 3554*mm, 2283*mm, 2988*mm))
    if atlas_barrel_cryostat:
        caixas = ((2808*mm, 2864.95*mm, 2283*mm, 3850*mm), (2865*mm, 3225*mm, 2775.05*mm, 3850*mm),
                  (3225*mm, 3405*mm, 2775.05*mm, 3461*mm), (3405.05*mm, 3444*mm, 2283*mm, 3461*mm),
                  (3444*mm, 3554*mm, 2283*mm, 2988*mm))
    if atlas_cryostat_pieces:
        caixas = ((2808*mm, 2849.95*mm, 2283*mm, 3850*mm), (2850*mm, 3225*mm, 2775.05*mm, 3850*mm)) + caixas[2:]
    if tile_atlas_gap:
        # around the ATLAS plug (D4 from z = 3210.5 mm, r > 3440 mm; C10 from 3424.8 mm, r > 2989.5 mm), the crack box (3492-3500 mm,
        # r < 2342.8 mm), the gap box (3504.5-3519.5 mm) and the nominal extended barrel (from 3519.5 mm); see TILE.py
        caixas = ((2808*mm, 2849.95*mm, 2283*mm, 3850*mm), (2850*mm, 3210.45*mm, 2775.05*mm, 3850*mm),
                  (3210.5*mm, 3405*mm, 2775.05*mm, 3439.95*mm), (3405.05*mm, 3424.75*mm, 2283*mm, 3439.95*mm),
                  (3424.8*mm, 3491.95*mm, 2283*mm, 2989.45*mm), (3492*mm, 3500*mm, 2342.85*mm, 2989.45*mm),
                  (3500.05*mm, 3504.45*mm, 2283*mm, 2989.45*mm))
    for i, (z1, z2, r1, r2) in enumerate(caixas):
        nlayers = max(1, int(round((r2 - r1) / (50*mm)))); layer = (r2 - r1) / nlayers
        pv = PhysicalVolume( Name               = "DM::ITC::Services%d::%s" % (i+1, side_name),
                             Plates             = Plates.Horizontal,
                             AbsorberMaterial   = "G4_Al",
                             GapMaterial        = "Vacuum",
                             NofLayers          = nlayers,
                             AbsorberThickness  = ATLAS_ITC_SERVICES_FRACTION*layer,
                             GapThickness       = (1 - ATLAS_ITC_SERVICES_FRACTION)*layer,
                             RMin               = r1,
                             RMax               = r2,
                             ZSize              = z2 - z1,
                             X=0,Y=0,Z=sign*(z1 + z2)/2,
                             Visualization = True,
                             Color         = 'gray' )
        pv.Cuts = ProductionCuts(ElectronCut = 1, PositronCut = 1, GammaCut = 1)
        volumes.append(pv)
    return volumes


# The outer cylinders of the end-cap cryostat as in ATLAS. Each end-cap cryostat is made of two aluminium vessels, a cold
# vessel filled with liquid argon inside a warm vessel (JINST 3 (2008) S08003, sec. 5.4 and fig. 5.25: outer radius
# 2.25 m, length 3.17 m). The thicknesses come from the LAr calorimeter TDR (CERN/LHCC 96-41, fig. 3-3 and fig. 5-i):
# - warm vessel: outer cylinder of 20 mm, outer diameter 4560 mm (r = 2260 to 2280 mm), 2630 mm long from the front
#   face, which is at z = 3500 mm, nominal; front wall of 15 mm;
# - cold vessel: outer cylinder of 35 mm, inner diameter 4280 mm (r = 2140 to 2175 mm), 3015 mm long, starting 3 mm
#   behind the warm front wall; front wall of 65 mm, back wall of 88 mm;
# - the end-cap cryostats sit 40 mm further from the interaction point than nominal (JINST 3 S08003, sec. 5.2).
# The cold vessel is full of liquid argon: between the outer radius of the EMEC (2042 mm) and the cold cylinder the argon
# is dead material (no cells). The cylinders start at the end of DM::Crack::EM (z = 3717.5 mm), which already stands for
# the front walls. Aluminium alloy 5083 is taken as G4_Al.
# Not modelled: the step of the warm vessel to an outer diameter of 4950 mm in its last 535 mm (behind the end of the
# tile calorimeter), the thicker back part of the cold cylinder, the feed-throughs and the cables.
ATLAS_ENDCAP_CRYOSTAT_SHIFT = 40*mm
ATLAS_ENDCAP_CRYOSTAT_START = 3717.55*mm   # end of DM::Crack::EM (3717.5 mm)

def getAtlasEndcapCryostatCfg(left_side=False):
    """
    Outer cylinders of the end-cap cryostat and the liquid argon between the EMEC and the cold vessel, as in ATLAS
    (see above). Simulation only.
    """
    sign = -1 if left_side else 1
    side_name = 'B' if left_side else 'A'
    warm_front = 3500*mm + ATLAS_ENDCAP_CRYOSTAT_SHIFT
    cold_front = warm_front + 15*mm + 3*mm
    z1 = ATLAS_ENDCAP_CRYOSTAT_START
    volumes = []
    #                name      material        r1          r2          z2
    for name, material, r1, r2, z2 in (("Warm",  "G4_Al",       2260*mm,    2280*mm, warm_front + 2630*mm),
                                       ("Cold",  "G4_Al",       2140.05*mm, 2175*mm, cold_front + 3015*mm),
                                       ("LAr",   "liquidArgon", 2042.05*mm, 2140*mm, cold_front + 3015*mm - 88*mm)):
        pv = PhysicalVolume( Name               = "DM::EndcapCryostat::"+name+"::"+side_name,
                             Plates             = Plates.Horizontal,
                             AbsorberMaterial   = material,
                             GapMaterial        = "Vacuum",
                             NofLayers          = 1,
                             AbsorberThickness  = (r2 - r1) - 0.01*mm,
                             GapThickness       = 0.01*mm,
                             RMin               = r1,
                             RMax               = r2,
                             ZSize              = z2 - z1,
                             X=0,Y=0,Z=sign*(z1 + z2)/2,
                             Visualization = True,
                             Color         = 'gray' )
        pv.Cuts = ProductionCuts(ElectronCut = 1, PositronCut = 1, GammaCut = 1)
        volumes.append(pv)
    return volumes


def getAtlasBarrelFrontCfg():
    """
    The material in front of the accordion of the barrel as in ATLAS, piece by piece (geometry/python/v1/AtlasBarrelFront.py):
    the warm inner wall of the cryostat (inside the solenoid field volume for |z| < 2900 mm), the solenoid in its five
    cylinders, the cold inner wall with its conical end, the liquid argon bath, the presampler mother (around the active
    argon of ECAL.py) and the front of the EM barrel (summing boards, motherboards, cables, G10 ring, absorber tips), and the
    argon between the cone of the cold wall and the end of the accordion. The materials are the mixtures of
    ATLAS_BARREL_FRONT_MIXTURES (defined by DetectorConstruction_v1). F41 conserto 17c, 09/10/2026.
    """
    return _volumesFromTable(ATLAS_BARREL_FRONT_VOLUMES)


def getAtlasFcalCfg(cells=False):
    """
    The ATLAS forward calorimeter as passive material, without cells, on both sides (geometry/python/v1/AtlasFCal.py): the
    three modules as tubes of the mean mixture of absorber, rods and liquid argon (ATLAS_FCAL_MIXTURES, defined by
    DetectorConstruction_v1) and the liquid argon between them, at the nominal z of the public GeoModel geometry. F41
    conserto 20, 11/10/2026.

    Args:
        cells (bool): If True, only the liquid argon between the modules: the modules themselves are built with their
                      electrodes (geometry/python/v1/FCAL.py, --atlas-fcal-cells; F41 conserto 22).
    """
    table = [v for v in ATLAS_FCAL_VOLUMES if not (cells and '::LAr' not in v['name'])]
    return _volumesFromTable(table)


def _volumesFromTable(table):
    """Dead-material volumes from a generated table (AtlasBarrelFront.py, AtlasBarrelCryostat.py): tubes and polycones of
    one material each."""
    vols = []
    for v in table:
        if v['kind'] == 'tube':
            pv = PhysicalVolume( Name = v['name'], Plates = Plates.Horizontal, AbsorberMaterial = v['material'],
                                 GapMaterial = v['material'], NofLayers = 1, AbsorberThickness = (v['r1'] - v['r0'])/2,
                                 GapThickness = (v['r1'] - v['r0'])/2, RMin = v['r0'], RMax = v['r1'],
                                 ZSize = v['z1'] - v['z0'], X=0,Y=0,Z=0.5*(v['z0'] + v['z1']), Visualization = True,
                                 Color = 'gray', InSolenoidField = v['in_field'] )
        else:
            zs = [p[0] for p in v['planes']]; rmins = [p[1] for p in v['planes']]; rmaxs = [p[2] for p in v['planes']]
            pv = PhysicalVolume( Name = v['name'], Plates = Plates.Polycone, AbsorberMaterial = v['material'],
                                 GapMaterial = v['material'], NofLayers = 1, AbsorberThickness = 0, GapThickness = 0,
                                 RMin = min(rmins), RMax = max(rmaxs), ZSize = max(zs) - min(zs), X=0,Y=0,
                                 Z=0.5*(max(zs) + min(zs)), Visualization = True, Color = 'gray', ZPlanes = zs,
                                 RMinPlanes = rmins, RMaxPlanes = rmaxs, InSolenoidField = v['in_field'] )
        pv.Cuts = ProductionCuts(ElectronCut = 1, PositronCut = 1, GammaCut = 1)
        vols.append(pv)
    return vols


def getDMVolumesCfg(tile_atlas_geometry=False, atlas_material_in_front=False, atlas_barrel_cryostat=False,
                    atlas_emb_cells=False):
    """
    Dead material around the barrel calorimeters.

    Args:
        atlas_barrel_cryostat (bool): If True, the two 100 mm aluminium shells around the barrel (DM::LAr::Boundary and
                                    DM::TILE::Boundary) are replaced by the outer part of the ATLAS barrel cryostat (see
                                    getAtlasBarrelCryostatCfg). Needs the services of the gap of tile_atlas_itc.
        tile_atlas_geometry (bool): If True, the aluminium shell inside the tile barrel follows the length of the
                                    ATLAS-like tile barrel (|z| < TILE_ATLAS_BARREL_HALF_Z).
        atlas_material_in_front (bool): If True, the material in front of the barrel electromagnetic calorimeter
                                    follows ATLAS (see getAtlasMaterialInFrontCfg): the solenoid, the cryostat wall
                                    in front of the presampler and the material between the presampler and the
                                    accordion. Without it (the default) only 40 mm of aluminium stand in front of the
                                    presampler.
        atlas_emb_cells (bool): With the ATLAS-like barrel presampler (r = 1413.9-1426.9 mm, |z| = 3-3101 mm; ECAL.py), the
                                    80 mm envelope of aluminium in front of it moves to r = 1305-1385 mm and, as the material
                                    between the presampler and the accordion, ends at |z| = 3101 mm (room for the conical cold
                                    wall); same thicknesses (F41 conserto 17, decision of 09/10/2026). Together with
                                    atlas_material_in_front, the envelope, the solenoid mixture and the material between
                                    the presampler and the accordion are replaced by the ATLAS pieces of
                                    getAtlasBarrelFrontCfg (F41 conserto 17c).
    """

    ecal_barrel_start = 0*m
    ecal_barrel_end   = 3.4*m
    ecal_barrel_z     = (ecal_barrel_start + ecal_barrel_end) * 2

    endcap_start = 3704.*mm
    gap_between_extended_barrel = 68.*cm

    tile_barrel_start = 0*m
    tile_barrel_end = (endcap_start - gap_between_extended_barrel)
    tile_barrel_z = (tile_barrel_start + tile_barrel_end) * 2
    if tile_atlas_geometry:
        tile_barrel_z = 2*TILE_ATLAS_BARREL_HALF_Z

    psb_rmin = 1460*mm
    ps_boundary_z = ecal_barrel_z
    if atlas_emb_cells:
        psb_rmin = 1385*mm; ps_boundary_z = 2*PSB_ATLAS_Z[1]

    nlayers=2; absorber=2*cm; gap=2*cm; rsize=nlayers*(absorber+gap)
    if atlas_material_in_front:
        # Same 80 mm envelope, with 2 x 33.8 = 67.6 mm of aluminium (0.76 X0) instead of 40 mm (see getAtlasMaterialInFrontCfg)
        absorber=ATLAS_CRYOSTAT_AL_THICKNESS/nlayers; gap=rsize/nlayers - absorber
    dm_pv =  PhysicalVolume( Name               = "DM::PS::Boundary", 
                             Plates             = Plates.Horizontal, # Logical type
                             AbsorberMaterial   = "G4_Al", # absorber
                             GapMaterial        = "Vacuum", # gap
                             NofLayers          = nlayers, # layers
                             AbsorberThickness  = absorber, # abso
                             GapThickness       = gap, # gap
                             RMin               = psb_rmin - rsize, #crack_em_pv.RMax, #228.3*cm, # radio min,
                             RMax               = psb_rmin, # radio max 
                             ZSize              = ps_boundary_z,
                             X=0,Y=0,Z=0,
                             Visualization = True,
                             Color         = 'gray'
                             )


    nlayers=1; absorber=10*cm; gap=3*mm; rsize=nlayers*(absorber+gap)
    ecal_boundary_pv =   PhysicalVolume( Name               = "DM::LAr::Boundary", 
                                         Plates             = Plates.Horizontal, # Logical type
                                         AbsorberMaterial   = "G4_Al", # absorber
                                         GapMaterial        = "Vacuum", # gap
                                         NofLayers          = nlayers, # layers
                                         AbsorberThickness  = absorber, # abso
                                         GapThickness       = gap, # gap
                                         RMin               = 198*cm, #crack_em_pv.RMax, #228.3*cm, # radio min,
                                         RMax               = 198*cm + rsize, # radio max 
                                         ZSize              = ecal_barrel_z,
                                         X=0,Y=0,Z=0,
                                         Visualization = True,
                                         Color         = 'gray'
                                         )

    nlayers=1; absorber=10*cm; gap=3*mm; rsize=nlayers*(absorber+gap)
    tilecal_boundary_pv =   PhysicalVolume( Name               = "DM::TILE::Boundary", 
                                            Plates             = Plates.Horizontal, # Logical type
                                            AbsorberMaterial   = "G4_Al", # absorber
                                            GapMaterial        = "Vacuum", # gap
                                            NofLayers          = nlayers, # layers
                                            AbsorberThickness  = absorber, # abso
                                            GapThickness       = gap, # gap
                                            RMin               = 218*cm, #crack_em_pv.RMax, #228.3*cm, # radio min,
                                            RMax               = 218*cm + rsize, # radio max 
                                            ZSize              = tile_barrel_z,
                                            X=0,Y=0,Z=0,
                                            Visualization = True,
                                            Color         = 'gray'
                                            )


    dm_pv.Cuts                  = ProductionCuts(ElectronCut = 1, PositronCut = 1, GammaCut = 1)
    ecal_boundary_pv.Cuts       = ProductionCuts(ElectronCut = 1, PositronCut = 1, GammaCut = 1)
    tilecal_boundary_pv.Cuts    = ProductionCuts(ElectronCut = 1, PositronCut = 1, GammaCut = 1)

    barrel_front = atlas_emb_cells and atlas_material_in_front
    front = [] if barrel_front else [dm_pv]
    if atlas_barrel_cryostat and barrel_front:
        # the ATLAS pieces of the barrel cryostat (F41 conserto 14b)
        volumes = front + _volumesFromTable(ATLAS_BARREL_CRYOSTAT_VOLUMES)
    elif atlas_barrel_cryostat:
        # The two 100 mm aluminium shells are replaced by the outer part of the ATLAS barrel cryostat
        volumes = front + getAtlasBarrelCryostatCfg(atlas_emb_cells=atlas_emb_cells)
    else:
        volumes = front + [ecal_boundary_pv, tilecal_boundary_pv]
    if barrel_front:
        volumes.extend( getAtlasBarrelFrontCfg() )
    elif atlas_material_in_front:
        volumes.extend( getAtlasMaterialInFrontCfg(atlas_emb_cells=atlas_emb_cells) )
    return volumes


# The outer part of the barrel cryostat as in ATLAS: two aluminium vessels, a cold vessel filled with liquid argon inside a
# warm vessel (JINST 3 (2008) S08003, sec. 5.4). Dimensions from the LAr calorimeter TDR (CERN/LHCC 96-41, fig. 3-2, p. 67):
# - cold vessel: outer cylinder of 30 mm, inner diameter 4280 mm (r = 2140 to 2170 mm), inner length 6534 mm
#   (|z| < 3267 mm), end walls of 30 mm (|z| = 3267 to 3297 mm), and at each end a step of 220 mm up to an outer diameter
#   of 4577 mm (r = 2258.5 to 2288.5 mm, |z| = 3077 to 3297 mm) for the feed-throughs;
# - warm vessel: outer cylinder of 30 mm, outer diameter 4500 mm (r = 2220 to 2250 mm), length 6810 mm (|z| < 3405 mm),
#   end walls of 50 mm (|z| = 3355 to 3405 mm), and at each end a step of 540 mm up to a diameter of 5550 mm (r up to
#   2775 mm, |z| = 2865 to 3405 mm);
# - the cold vessel is full of liquid argon: between the EM calorimeter and the cold cylinder it is dead material (no cells).
# The walls of the steps are not dimensioned in the figure and are taken as 30 mm like the other walls. The EM barrel of
# Lorenzetti is 250 mm longer than in ATLAS (|z| < 3400 against 3150 mm): the end walls only cover r > 1980 mm, outside it.
# Inside the warm step there is vacuum (the feed-throughs are not modelled). Needs tile_atlas_itc: the services of the gap
# leave room for the warm step (see getAtlasItcCfg).
ATLAS_BARREL_CRYOSTAT_LAR_RMIN = 1980.05*mm   # outside the EM barrel (r < 1980 mm by default, 1973.4 mm with atlas_emb)

def getAtlasBarrelCryostatCfg(atlas_emb_cells=False):
    """
    Outer part of the barrel cryostat as in ATLAS (see above). Simulation only. With atlas_emb_cells the dead liquid argon
    ends at |z| = 3205 mm, where the LArElectronics of the ATLAS-like barrel starts (ECAL.py, getAtlasEmbEndCfg; F41
    conserto 17, decision of 09/10/2026).
    """
    def pv(name, plates, material, r1, r2, z1, z2):
        if plates == Plates.Horizontal:
            absorber, gap = (r2 - r1) - 0.01*mm, 0.01*mm
        else:
            absorber, gap = (z2 - z1) - 0.01*mm, 0.01*mm
        p = PhysicalVolume( Name               = "DM::BarrelCryostat::"+name,
                            Plates             = plates,
                            AbsorberMaterial   = material,
                            GapMaterial        = "Vacuum",
                            NofLayers          = 1,
                            AbsorberThickness  = absorber,
                            GapThickness       = gap,
                            RMin               = r1,
                            RMax               = r2,
                            ZSize              = z2 - z1,
                            X=0,Y=0,Z=(z1 + z2)/2,
                            Visualization = True,
                            Color         = 'gray' )
        p.Cuts = ProductionCuts(ElectronCut = 1, PositronCut = 1, GammaCut = 1)
        return p
    H, V = Plates.Horizontal, Plates.Vertical
    rlar = ATLAS_BARREL_CRYOSTAT_LAR_RMIN
    # the three long volumes span both sides
    volumes = [pv("ColdCylinder", H, "G4_Al",       2140.05*mm, 2170*mm, -3076.95*mm, 3076.95*mm),
               pv("WarmCylinder", H, "G4_Al",       2220*mm,    2250*mm, -2864.95*mm, 2864.95*mm),
               pv("LAr",          H, "liquidArgon", rlar,       2140*mm, -(3205.0*mm if atlas_emb_cells else 3266.95*mm),
                                                                          3205.0*mm if atlas_emb_cells else 3266.95*mm)]
    for sign, side in ((1, 'A'), (-1, 'B')):
        for name, plates, material, r1, r2, z1, z2 in (
                ("ColdStepWall",  V, "G4_Al",       2140.05*mm, 2258.5*mm,  3077*mm,    3107*mm),
                ("ColdStepOuter", H, "G4_Al",       2258.5*mm,  2288.5*mm,  3077*mm,    3297*mm),
                ("ColdStepLAr",   H, "liquidArgon", 2140.05*mm, 2258.45*mm, 3107.05*mm, 3266.95*mm),
                ("ColdEndWall",   V, "G4_Al",       rlar,       2258.45*mm, 3267*mm,    3297*mm),
                ("WarmStepWall",  V, "G4_Al",       2220*mm,    2745*mm,    2865*mm,    2895*mm),
                ("WarmStepOuter", H, "G4_Al",       2745*mm,    2775*mm,    2865*mm,    3405*mm),
                ("WarmEndWall",   V, "G4_Al",       rlar,       2744.95*mm, 3355*mm,    3405*mm)):
            za, zb = (z1, z2) if sign > 0 else (-z2, -z1)
            volumes.append(pv(name+"::"+side, plates, material, r1, r2, za, zb))
    return volumes


# Material in front of the barrel electromagnetic calorimeter as in ATLAS, in radiation lengths at normal incidence
# (X0 from PDG 2024: Al 88.97 mm, Cu 14.36 mm). Where the room is too short for aluminium alone, a copper plate is added
# so that the shell has the ATLAS X0 in the available space.
# - Cryostat wall in front of the presampler: 0.76 X0 = 67.6 mm of Al. ATLAS has 1.86 X0 in front of the presampler at
#   eta = 0 (JINST 3 (2008) S08003, fig. 5.1, top left), of which about 0.44 X0 are the inner detector (taken from the
#   Run 2 inner detector, ATLAS-TDR-030, fig. 2.6) and 0.66 X0 the solenoid (JINST 3 S08003, sec. 2.1.1). The cryostat
#   is made of two aluminium vessels (JINST 3 S08003, sec. 5.4); here its aluminium stays in the 80 mm envelope in front
#   of the presampler (r = 1380 to 1460 mm), outside the volume of the solenoid field.
# - Solenoid: 0.66 X0 (JINST 3 S08003, sec. 2.1.1) in the 50 mm of the coil (inner and outer diameter 2.46 and 2.56 m,
#   length 5.8 m; JINST 3 S08003, table 2.1): 1.68 mm of Cu and 48.32 mm of Al.
# - Between the presampler and the accordion: 0.60 X0, the 0.68 X0 of ATLAS between the presampler and the accordion
#   (fig. 5.1, top left, at eta = 0) less the 11 mm of liquid argon of the presampler; in the 28.9 mm between the
#   presampler (r = 1471.01 mm) and the first layer (r = 1500 mm): 4.71 mm of Cu and 24.19 mm of Al.
# Not modelled: the tapered walls of the cryostat, the end-cap cryostat walls and the services; the inner detector
# (a separate step).
ATLAS_CRYOSTAT_AL_THICKNESS = 67.6*mm

def getAtlasMaterialInFrontCfg(atlas_emb_cells=False):
    """
    Solenoid and material between the presampler and the accordion of the barrel, as in ATLAS (see above).
    The cryostat wall is set in getDMVolumesCfg (DM::PS::Boundary). With atlas_emb_cells the material between the
    presampler and the accordion ends at |z| = 3101 mm (same radii and thicknesses; F41 conserto 17).
    """
    solenoid_pv = PhysicalVolume( Name               = "DM::Solenoid",
                                  Plates             = Plates.Horizontal,
                                  AbsorberMaterial   = "G4_Cu",
                                  GapMaterial        = "G4_Al",
                                  NofLayers          = 1,
                                  AbsorberThickness  = 1.68*mm,
                                  GapThickness       = 48.32*mm,
                                  RMin               = 1230.05*mm,   # just outside the solenoid field volume (r < 1230 mm)
                                  RMax               = 1280.05*mm,
                                  ZSize              = 2*2900*mm,
                                  X=0,Y=0,Z=0,
                                  Visualization = True,
                                  Color         = 'gray'
                                  )
    ps_accordion_pv = PhysicalVolume( Name               = "DM::PS::Accordion",
                                      Plates             = Plates.Horizontal,
                                      AbsorberMaterial   = "G4_Cu",
                                      GapMaterial        = "G4_Al",
                                      NofLayers          = 1,
                                      AbsorberThickness  = 4.71*mm,
                                      GapThickness       = 24.19*mm,
                                      RMin               = 1471.05*mm,   # the presampler ends at 1471.01 mm
                                      RMax               = 1499.95*mm,   # the first layer starts at 1500 mm
                                      ZSize              = 2*PSB_ATLAS_Z[1] if atlas_emb_cells else 2*3.4*m,
                                      X=0,Y=0,Z=0,
                                      Visualization = True,
                                      Color         = 'gray'
                                      )
    solenoid_pv.Cuts     = ProductionCuts(ElectronCut = 1, PositronCut = 1, GammaCut = 1)
    ps_accordion_pv.Cuts = ProductionCuts(ElectronCut = 1, PositronCut = 1, GammaCut = 1)
    return [solenoid_pv, ps_accordion_pv]
