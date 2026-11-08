"""
Regression of the LAr end-cap shift of AtlasRun4 (F41 conserto 27): builds the detector configuration with and without AtlasRun4 and
checks that every end-cap sampling (presampler, EMEC, HEC) has its volume and every field of its cells that holds an absolute z moved by
the shift of its subsystem (ATLAS_ENDCAP_SIM_SHIFT), away from the interaction point. No simulation is run.
Usage (inside the Lorenzetti environment): python3 atlas_run4_check_cells.py <GeoModel dump of the Run 4 simulation> <field map>
Exit code 0 when all checks pass.
"""
import os, sys, math
from geometry import DetectorConstruction_v1
from geometry.v1.AtlasRun4 import ATLAS_ENDCAP_SIM_SHIFT

kw = dict( UseSolenoidField=True, TileAtlasGeometry=True, TileAtlasCells=True, AtlasMaterialInFront=True, TileAtlasItc=True,
           AtlasEmb=True, AtlasEmbCells=True, AtlasHec=True, AtlasEmec=True, AtlasFcal=True, AtlasFcalCells=True,
           AtlasFcalElectrodes=os.path.join( os.environ['LORENZETTI_GEOMETRY_DATA_DIR'], 'LArFCalElectrodes-06.csv' ),
           AtlasFcalFrozenShowers=True, AtlasG4=True, TileAtlasGap=True, AtlasEndcapCryostat=True, AtlasBarrelCryostat=True )
nominal = DetectorConstruction_v1( "ATLAS", **kw )
run4    = DetectorConstruction_v1( "ATLAS", **kw, AtlasRun4=True, AtlasRun4Geometry=sys.argv[1], AtlasFieldMap=sys.argv[2] )

def shift_of( name ):
    for prefix, shift in ATLAS_ENDCAP_SIM_SHIFT.items():
        if name.startswith( prefix ): return shift
    return None

def close( a, b ): return abs( a - b ) < 1e-6

erros = 0; vistos = 0
assert len( nominal.samplings ) == len( run4.samplings )
for sn, sr in zip( nominal.samplings, run4.samplings ):
    vn, vr = sn.volume(), sr.volume()
    assert vn.Name == vr.Name
    shift = shift_of( vn.Name )
    if shift is None: continue
    if not vn.Name.startswith( ( 'LAr::PSE', 'LAr::EMEC', 'FCal::HEC' ) ): continue
    vistos += 1
    dz = math.copysign( shift, vn.Z )
    falhas = []
    if not close( vr.Z - vn.Z, dz ): falhas.append( 'volume Z %.3f -> %.3f' % ( vn.Z, vr.Z ) )
    cn = getattr( sn.sensitive(), 'Cells', None ) or {}
    cr = getattr( sr.sensitive(), 'Cells', None ) or {}
    if 'EmecFocalShift' in cn and not close( cr['EmecFocalShift'] - cn['EmecFocalShift'], shift ):
        falhas.append( 'EmecFocalShift %s -> %s' % ( cn['EmecFocalShift'], cr['EmecFocalShift'] ) )
    for k in ( 'EmecWheelZMin', 'EmecWheelZMax', 'BoxZMin', 'BoxZMax' ):
        if k in cn:
            for a, b in zip( cn[k], cr[k] ):
                if not close( b - a, math.copysign( shift, a ) ):
                    falhas.append( '%s %s -> %s' % ( k, a, b ) ); break
    if cn.get( 'EmbMode' ) == 2 and not close( cr.get( 'EmbZShift', 0 ), shift ):
        falhas.append( 'EmbZShift %s' % cr.get( 'EmbZShift' ) )
    if falhas:
        erros += 1
        print( 'FALHA', vn.Name, '; '.join( falhas ) )
print( 'samplings da tampa conferidos: %d, com falha: %d' % ( vistos, erros ) )
sys.exit( 1 if erros or vistos == 0 else 0 )
