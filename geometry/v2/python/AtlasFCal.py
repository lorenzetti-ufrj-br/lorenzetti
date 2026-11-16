"""
The ATLAS forward calorimeter (FCal) as passive material, without cells (F41 conserto 20, generated on 11/10/2026 by
Simulacao_MinBias/41_consertos_lorenzetti/c20_fcal/c20_gerar_fcal.py; do not edit by hand), and the constants of the
FCal with its electrodes at the end of the file (F41 conserto 22, generated on 12/10/2026 by
Simulacao_MinBias/41_consertos_lorenzetti/c22_fcal_celulas/c22_gerar_fcal.py, which also writes the part above).

Source: the public ATLAS geometry of the GeoModel project, geometry-ATLAS-R3S-2021-03-00-00.db
(https://geomodel.web.cern.ch/atlas-geometry-data/old/): the three modules (LAr::FCAL::Module1-3), their absorbers,
electrode gaps and rods, and their position in the end-cap cryostat, without the shift of the installed end-cap
(45 mm). Each module is a tube of the mean mixture of absorber, rods and liquid argon; the liquid argon between the
modules is a tube of liquid argon. Not modelled: the cable troughs at the outer radius and the support structure.
"""

# name: (density in g/cm3, {element symbol: mass fraction})
ATLAS_FCAL_MIXTURES = {
    'ATLAS_FCAL1_MODULE': (8.096758, {'Cu': 0.979824, 'Ar': 0.020176}),
    'ATLAS_FCAL2_MODULE': (14.376014, {'Cu': 0.087091, 'Ar': 0.015865, 'W': 0.870133, 'Fe': 0.008970, 'Ni': 0.017941}),
    'ATLAS_FCAL3_MODULE': (14.088338, {'Cu': 0.084872, 'Ar': 0.018212, 'W': 0.870009, 'Fe': 0.008969, 'Ni': 0.017938}),
}

# tubes (mm); one entry per side
ATLAS_FCAL_VOLUMES = [
    {'kind': 'tube', 'name': 'DM::FCal::FCal1::A', 'material': 'ATLAS_FCAL1_MODULE', 'r0': 72.0, 'r1': 449.6, 'z0': 4668.5, 'z1': 5112.700000000001, 'both': False, 'in_field': False, 'source': 'GeoModel LAr::FCAL::Module, mean mixture'},
    {'kind': 'tube', 'name': 'DM::FCal::FCal1::B', 'material': 'ATLAS_FCAL1_MODULE', 'r0': 72.0, 'r1': 449.6, 'z0': -5112.700000000001, 'z1': -4668.5, 'both': False, 'in_field': False, 'source': 'GeoModel LAr::FCAL::Module, mean mixture'},
    {'kind': 'tube', 'name': 'DM::FCal::FCal2::A', 'material': 'ATLAS_FCAL2_MODULE', 'r0': 79.0, 'r1': 449.6, 'z0': 5128.3, 'z1': 5570.599999999999, 'both': False, 'in_field': False, 'source': 'GeoModel LAr::FCAL::Module, mean mixture'},
    {'kind': 'tube', 'name': 'DM::FCal::FCal2::B', 'material': 'ATLAS_FCAL2_MODULE', 'r0': 79.0, 'r1': 449.6, 'z0': -5570.599999999999, 'z1': -5128.3, 'both': False, 'in_field': False, 'source': 'GeoModel LAr::FCAL::Module, mean mixture'},
    {'kind': 'tube', 'name': 'DM::FCal::FCal3::A', 'material': 'ATLAS_FCAL3_MODULE', 'r0': 86.0, 'r1': 449.6, 'z0': 5602.8, 'z1': 6045.099999999999, 'both': False, 'in_field': False, 'source': 'GeoModel LAr::FCAL::Module, mean mixture'},
    {'kind': 'tube', 'name': 'DM::FCal::FCal3::B', 'material': 'ATLAS_FCAL3_MODULE', 'r0': 86.0, 'r1': 449.6, 'z0': -6045.099999999999, 'z1': -5602.8, 'both': False, 'in_field': False, 'source': 'GeoModel LAr::FCAL::Module, mean mixture'},
    {'kind': 'tube', 'name': 'DM::FCal::LAr12::A', 'material': 'liquidArgon', 'r0': 79.0, 'r1': 449.6, 'z0': 5112.700000000001, 'z1': 5128.3, 'both': False, 'in_field': False, 'source': 'GeoModel LAr::FCAL::LiquidArgonC'},
    {'kind': 'tube', 'name': 'DM::FCal::LAr12::B', 'material': 'liquidArgon', 'r0': 79.0, 'r1': 449.6, 'z0': -5128.3, 'z1': -5112.700000000001, 'both': False, 'in_field': False, 'source': 'GeoModel LAr::FCAL::LiquidArgonC'},
    {'kind': 'tube', 'name': 'DM::FCal::LAr23::A', 'material': 'liquidArgon', 'r0': 86.0, 'r1': 449.6, 'z0': 5570.599999999999, 'z1': 5602.8, 'both': False, 'in_field': False, 'source': 'GeoModel LAr::FCAL::LiquidArgonC'},
    {'kind': 'tube', 'name': 'DM::FCal::LAr23::B', 'material': 'liquidArgon', 'r0': 86.0, 'r1': 449.6, 'z0': -5602.8, 'z1': -5570.599999999999, 'both': False, 'in_field': False, 'source': 'GeoModel LAr::FCAL::LiquidArgonC'},
]


# ---- F41 conserto 22: the FCal with its electrodes (--atlas-fcal-cells; geometry/python/v1/FCAL.py) ----
# Materials of the GeoModel geometry (density in g/cm3, mass fractions): LAr::FCal1Absorber, LAr::FCal23Absorber,
# LAr::FCal23Slugs (the rods of FCal2 and FCal3) and LAr::FCalCableHarness (the cable troughs).
ATLAS_FCAL_CELL_MATERIALS = {
    'ATLAS_FCAL1_ABSORBER': (8.701013, {'Cu': 0.994, 'Ar': 0.006}),
    'ATLAS_FCAL23_ABSORBER': (14.390022, {'Cu': 0.15, 'Ar': 0.01, 'W': 0.8148, 'Fe': 0.0084, 'Ni': 0.0168}),
    'ATLAS_FCAL23_SLUGS': (18.600029, {'W': 0.97, 'Fe': 0.01, 'Ni': 0.02}),
    'ATLAS_FCAL_CABLE_HARNESS': (5.185008, {'Cu': 0.864, 'C': 0.046997, 'H': 0.001793, 'O': 0.014228, 'N': 0.004982, 'Ar': 0.068}),
}

# One entry per module (mm, rad), from the GeoModel volumes LAr::FCAL::Module<m>::Absorber, ::Gap, ::Rod and ::CableTrough:
# the absorber tube centred at zc (nominal, without the 45 mm shift of the installed end-cap), the liquid argon gap of
# each electrode (a ring in FCal1, whose inner copper rod is part of the absorber; a cylinder holding a tungsten rod in
# FCal2 and FCal3), as long as the module, and the cable troughs (sector trough_sphi..trough_sphi+trough_dphi rotated
# about z by each angle of the GeoModel SerialTransformer), placed before the gaps as in the GeoModel.
ATLAS_FCAL_CELL_MODULES = [
    {'module': 1, 'rmin': 72.0, 'rmax': 449.6, 'zc': 4890.6, 'halfz': 222.1, 'absorber': 'ATLAS_FCAL1_ABSORBER', 'gap_rmin': 2.355, 'gap_rmax': 2.622, 'rod_r': 0.0, 'rod_material': '', 'electrodes': 12260, 'trough_material': 'ATLAS_FCAL_CABLE_HARNESS', 'trough_rmin': 439.6, 'trough_rmax': 449.6, 'trough_sphi': 0.1472621556370216, 'trough_dphi': 0.098174770424681, 'trough_angles': [0.0, 0.3926990816987241, 0.7853981633974482, 1.1780972450961722, 1.5707963267948963, 1.9634954084936205, 2.3561944901923444, 2.7488935718910685, 3.1415926535897927, 3.534291735288517, 3.926990816987241, 4.319689898685965, 4.712388980384689, 5.105088062083413, 5.497787143782137, 5.890486225480862]},
    {'module': 2, 'rmin': 79.0, 'rmax': 449.6, 'zc': 5349.45, 'halfz': 221.15, 'absorber': 'ATLAS_FCAL23_ABSORBER', 'gap_rmin': 0.0, 'gap_rmax': 2.84, 'rod_r': 2.465, 'rod_material': 'ATLAS_FCAL23_SLUGS', 'electrodes': 10200, 'trough_material': 'ATLAS_FCAL_CABLE_HARNESS', 'trough_rmin': 439.6, 'trough_rmax': 449.6, 'trough_sphi': 0.1472621556370216, 'trough_dphi': 0.098174770424681, 'trough_angles': [0.0, 0.3926990816987241, 0.7853981633974482, 1.1780972450961722, 1.5707963267948963, 1.9634954084936205, 2.3561944901923444, 2.7488935718910685, 3.1415926535897927, 3.534291735288517, 3.926990816987241, 4.319689898685965, 4.712388980384689, 5.105088062083413, 5.497787143782137, 5.890486225480862]},
    {'module': 3, 'rmin': 86.0, 'rmax': 449.6, 'zc': 5823.95, 'halfz': 221.15, 'absorber': 'ATLAS_FCAL23_ABSORBER', 'gap_rmin': 0.0, 'gap_rmax': 3.25, 'rod_r': 2.75, 'rod_material': 'ATLAS_FCAL23_SLUGS', 'electrodes': 8224, 'trough_material': 'ATLAS_FCAL_CABLE_HARNESS', 'trough_rmin': 439.6, 'trough_rmax': 449.6, 'trough_sphi': 0.1472621556370216, 'trough_dphi': 0.098174770424681, 'trough_angles': [0.1963495408493621, 0.3926990816987241, 0.7853981633974483, 0.9817477042468103, 1.178097245096172, 1.570796326794897, 1.767145867644259, 1.963495408493621, 2.356194490192345, 2.552544031041707, 2.748893571891069, 3.141592653589793, 3.337942194439155, 3.534291735288517, 3.926990816987241, 4.123340357836604, 4.319689898685966, 4.71238898038469, 4.908738521234052, 5.105088062083414, 5.497787143782138, 5.6941366846315, 5.890486225480863, 6.283185307179586]},
]
