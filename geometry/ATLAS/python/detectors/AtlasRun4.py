"""
The ATLAS Run 4 geometry of the simulation (F41 conserto 27, --atlas-run4): the geometry of the ATLAS simulation of the
reference production (ATLAS-P2-RUN4-01-01-00, Athena 23.0.14), read from its GeoModel SQLite dump made in the simulation mode
(DumpGeo with Common.ProductionStep=Simulation; geometry/scripts/atlas_run4_dumpgeo.sh).

LAr end-cap position: the ATLAS simulation places the end-cap cryostat at |z| = 6734.5 mm (LArPosition-10, LARCRYO_EC_POS), with the
alignment off. Its presampler, EMEC, HEC and FCal sit 43 to 45 mm further from the interaction point than the nominal numbers of the
readout geometry used by the ATLAS-like end-cap options (PresamplerPosition ZPOS, LArWheelCalculator, HecNominals, FCal without the
shift). shiftLArEndcap moves each of them by its own ATLAS_ENDCAP_SIM_SHIFT. The cells move with them, as in ATLAS, where the end-cap identifiers come from
local coordinates (LArG4EC PresamplerGeometry.cc: local z plus the nominal front face; LArWheelCalculator: the wheel frame; HEC and
FCal: the module frame).
"""

__all__ = ["ATLAS_ENDCAP_SIM_SHIFT", "shiftLArEndcap", "TILE_ENDCAP_SIM_SHIFT", "shiftTileEndcap"]

import math
from GaugiKernel.constants import mm

# |z| of each part of the end-cap of the ATLAS simulation minus its nominal |z| in the ATLAS-like options, measured in the dump of
# ATLAS-P2-RUN4-01-01-00 (simulation mode, alignment off): presampler argon 3667-3671 against 3622-3626 mm; front face of the EMEC wheels
# 3745 against 3702 mm (LAr::EMEC::Pos::OuterWheel, 514 mm thick); front of the liquid argon of the HEC wheels 4321 and 5178 against
# 4277 and 5134 mm (LAr::HEC::LiquidArgon, HecNominals); FCal1 4713.5-5157.7 against 4668.5-5112.7 mm. By prefix of the volume names
# built by the ATLAS-like end-cap options (ECAL.py getAtlasPseCfg, EMEC.py, HEC.py, AtlasFCal.py, FCAL.py).
ATLAS_ENDCAP_SIM_SHIFT = {
    'LAr::PSE' : 45.0*mm,
    'LAr::EMEC': 43.0*mm,
    'FCal::HEC': 44.0*mm,
    'DM::HEC'  : 44.0*mm,
    'DM::FCal' : 45.0*mm,
    'LAr::FCAL': 45.0*mm,
}


def _shiftOf( name ):
    for prefix, shift in ATLAS_ENDCAP_SIM_SHIFT.items():
        if name.startswith( prefix ): return shift
    return None


def _isEndcap( name ):
    return _shiftOf( name ) is not None


def _shiftVolume( pv, dz ):
    pv.Z += dz; pv.ZMin += dz; pv.ZMax += dz
    if getattr( pv, 'ZPlanes', None ):
        pv.ZPlanes = [ z + dz for z in pv.ZPlanes ]


def shiftLArEndcap( volumes, samplings, fcal_modules ):
    """
    Moves the LAr end-cap volumes, hit makers and FCal modules away from the interaction point on each side (ATLAS_ENDCAP_SIM_SHIFT), with the fields of
    their cells that hold an absolute z: the electric focal point and the wheel boxes of the EMEC (the boundaries ZSEP and ZIW are measured
    from the focal point and move with it), the (r, z) boxes of the HEC cells, and the z subtracted from the end-cap presampler before its
    eta (EmbZShift). The eta of the centre of the FCal tiles (metadata of the hits) follows the module.
    """
    done = set()
    for pv in volumes:
        if _isEndcap( pv.Name ) and id(pv) not in done:
            _shiftVolume( pv, math.copysign( _shiftOf( pv.Name ), pv.Z ) ); done.add( id(pv) )
    # Several samplings of the EMEC and of the HEC share one volume: the volume moves once, but the cells of EVERY sampling move with it
    # (each hit maker has its own Cells; a set by Cells keeps a shared one from moving twice).
    cells_done = set()
    for s in samplings:
        pv = s.volume()
        if not _isEndcap( pv.Name ): continue
        sign = 1 if pv.Z > 0 else -1
        shift = _shiftOf( pv.Name )
        if id(pv) not in done:
            _shiftVolume( pv, sign * shift ); done.add( id(pv) )
        cells = getattr( s.sensitive(), 'Cells', None )
        if not cells or id(cells) in cells_done: continue
        cells_done.add( id(cells) )
        if 'EmecFocalShift' in cells:
            cells['EmecFocalShift'] = cells['EmecFocalShift'] + shift
            for k in ('EmecWheelZMin', 'EmecWheelZMax'):
                cells[k] = [ z + math.copysign( shift, z ) for z in cells[k] ]
        if 'BoxZMin' in cells:
            for k in ('BoxZMin', 'BoxZMax'):
                cells[k] = [ z + math.copysign( shift, z ) for z in cells[k] ]
        if cells.get('EmbMode') == 2:
            cells['EmbZShift'] = shift
    for fm in fcal_modules:
        if id(fm) in done: continue
        dz = math.copysign( _shiftOf( fm.Name ), fm.Z )
        rs = [ fm.Z / math.sinh(eta) for eta in fm.CopyEta ]
        fm.Z += dz; fm.ZMin += dz; fm.ZMax += dz
        fm.CopyEta = [ math.asinh( fm.Z / r ) for r in rs ]
        done.add( id(fm) )


# The extended barrel, the ITC, the gap and the crack of the tile calorimeter in the ATLAS simulation of Run 4 (F41 conserto 35,
# --tile-atlas-run4): the dump of ATLAS-P2-RUN4-01-01-00 (simulation mode) places them, with respect to the nominal positions of the
# ATLAS-like options (the ZOFFSET of TILB, conserto 21), 40 mm further on side A and 30 mm further on side C (the installed shift of
# TileGlobals): measured with scans of 0.5 mm along z (the crack scintillator 3493-3499.5 against 3533-3539.5 mm, the gap scintillator
# 3506-3518.5 against 3546-3558.5 mm, the front plate of the extended barrel 3520-3534.5 against 3560-3574.5 mm on side A; the C10 and the
# end of the extended barrel 39.5 mm further on side C, including the phase of the tiles in the period, which is not changed here); the
# envelopes of the dump: Crack 3536 / -3526 mm, Gap 3552 / -3542 mm, ITC 3405 / -3395 mm, EBarrel 4854 / -4844 mm.
TILE_ENDCAP_SIM_SHIFT = { +1: 40.0*mm, -1: 30.0*mm }
_TILE_ENDCAP_PREFIXES = ( 'TILE::TileCalExt', 'TILE::ITC', 'TILE::Gap', 'DM::TileGap' )


def shiftTileEndcap( volumes, samplings ):
    """
    Moves the volumes of the extended barrel, ITC, gap and crack of the tile calorimeter away from the interaction point by
    TILE_ENDCAP_SIM_SHIFT, with the (r, z) boxes of their cells and the centre and eta of each cell (metadata of the hits).
    """
    def dz( z ): return TILE_ENDCAP_SIM_SHIFT[+1] if z > 0 else -TILE_ENDCAP_SIM_SHIFT[-1]
    def isTileEndcap( name ): return name.startswith( _TILE_ENDCAP_PREFIXES )
    done = set()
    for pv in volumes:
        if isTileEndcap( pv.Name ) and id(pv) not in done:
            _shiftVolume( pv, dz( pv.Z ) ); done.add( id(pv) )
    cells_done = set()
    for s in samplings:
        pv = s.volume()
        if not isTileEndcap( pv.Name ): continue
        if id(pv) not in done:
            _shiftVolume( pv, dz( pv.Z ) ); done.add( id(pv) )
        cells = getattr( s.sensitive(), 'Cells', None )
        if not cells or id(cells) in cells_done: continue
        cells_done.add( id(cells) )
        d = dz( pv.Z )
        for k in ( 'BoxZMin', 'BoxZMax', 'ZCentre' ):
            if k in cells: cells[k] = [ z + d for z in cells[k] ]
        if 'ZCentre' in cells and 'RCentre' in cells and 'Eta' in cells:
            cells['Eta'] = [ round( math.asinh( z / r ), 5 ) for z, r in zip( cells['ZCentre'], cells['RCentre'] ) ]
