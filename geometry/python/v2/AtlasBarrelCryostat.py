"""
Outer part of the barrel cryostat as in ATLAS, piece by piece (F41 conserto 14b, generated on 09/10/2026 by
Simulacao_MinBias/41_consertos_lorenzetti/c17_emb_ps_atlas/c17c_ps_mae/gerar_criostato_barril.py; do not edit by hand).
Sources: the public ATLAS geometry of the GeoModel project (geometry-ATLAS-R3S-2021-03-00-00.db) and the Run 3
geometry tables CryoCylinders-09, CryoPcons-18 and CryoEars-00, placed as in LArGeoBarrel/src/BarrelCryostatConstruction.cxx.
Not modelled: the iron bolts of the inner wall and the bumpers of the coil (small pieces).
"""

ATLAS_BARREL_CRYOSTAT_MIXTURES = {
    'ATLAS_CRYO_SUPPORT_2280_2926': (0.781944, {'Al': 1.000000}),
    'ATLAS_CRYO_SUPPORT_2290_2923': (0.137420, {'Al': 1.000000}),
    'ATLAS_CRYO_SUPPORT_2290_2926': (0.882666, {'Al': 1.000000}),
    'ATLAS_CRYO_SUPPORT_2290_2996': (0.137420, {'Al': 1.000000}),
    'ATLAS_CRYO_SUPPORT_2490_2923': (0.173691, {'Al': 1.000000}),
    'ATLAS_CRYO_SUPPORT_2490_2926': (0.173691, {'Al': 1.000000}),
    'ATLAS_CRYO_SUPPORT_2490_2996': (0.173691, {'Al': 1.000000}),
    'ATLAS_G10_BAR': (1.720000, {'H': 0.030800, 'O': 0.469800, 'C': 0.209600, 'Si': 0.289800}),
}

ATLAS_BARREL_CRYOSTAT_VOLUMES = [
    dict(kind='tube', name='DM::BarrelCryostat::Cylinder0', material='G4_Al', r0=2140.000, r1=2170.000, z0=-2996.000, z1=2996.000, in_field=False),  # CryoCylinders-09, Barrel::CryoMother cylinder #0
    dict(kind='tube', name='DM::BarrelCryostat::Cylinder1::A', material='G4_Al', r0=2170.000, r1=2280.000, z0=2926.000, z1=2996.000, in_field=False),  # CryoCylinders-09, Barrel::CryoMother cylinder #1
    dict(kind='tube', name='DM::BarrelCryostat::Cylinder1::B', material='G4_Al', r0=2170.000, r1=2280.000, z0=-2996.000, z1=-2926.000, in_field=False),  # CryoCylinders-09, Barrel::CryoMother cylinder #1
    dict(kind='tube', name='DM::BarrelCryostat::Cylinder2::A', material='G4_Al', r0=2215.000, r1=2265.000, z0=2996.000, z1=3227.000, in_field=False),  # CryoCylinders-09, Barrel::CryoMother cylinder #2
    dict(kind='tube', name='DM::BarrelCryostat::Cylinder2::B', material='G4_Al', r0=2215.000, r1=2265.000, z0=-3227.000, z1=-2996.000, in_field=False),  # CryoCylinders-09, Barrel::CryoMother cylinder #2
    dict(kind='tube', name='DM::BarrelCryostat::Cylinder3::A', material='G4_Al', r0=2190.000, r1=2280.000, z0=3227.000, z1=3317.000, in_field=False),  # CryoCylinders-09, Barrel::CryoMother cylinder #3
    dict(kind='tube', name='DM::BarrelCryostat::Cylinder3::B', material='G4_Al', r0=2190.000, r1=2280.000, z0=-3317.000, z1=-3227.000, in_field=False),  # CryoCylinders-09, Barrel::CryoMother cylinder #3
    dict(kind='tube', name='DM::BarrelCryostat::Cylinder5', material='G4_Al', r0=2220.000, r1=2250.000, z0=-2850.000, z1=2850.000, in_field=False),  # CryoCylinders-09, Barrel::CryoMother cylinder #5
    dict(kind='tube', name='DM::BarrelCryostat::Cylinder6::A', material='G4_Al', r0=2220.000, r1=2711.000, z0=2850.000, z1=2900.000, in_field=False),  # CryoCylinders-09, Barrel::CryoMother cylinder #6
    dict(kind='tube', name='DM::BarrelCryostat::Cylinder6::B', material='G4_Al', r0=2220.000, r1=2711.000, z0=-2900.000, z1=-2850.000, in_field=False),  # CryoCylinders-09, Barrel::CryoMother cylinder #6
    dict(kind='tube', name='DM::BarrelCryostat::Cylinder7::A', material='G4_Al', r0=2711.000, r1=2775.000, z0=2850.000, z1=3390.000, in_field=False),  # CryoCylinders-09, Barrel::CryoMother cylinder #7
    dict(kind='tube', name='DM::BarrelCryostat::Cylinder7::B', material='G4_Al', r0=2711.000, r1=2775.000, z0=-3390.000, z1=-2850.000, in_field=False),  # CryoCylinders-09, Barrel::CryoMother cylinder #7
    dict(kind='tube', name='DM::BarrelCryostat::Cylinder8::A', material='G4_Al', r0=2516.000, r1=2711.000, z0=3340.000, z1=3390.000, in_field=False),  # CryoCylinders-09, Barrel::CryoMother cylinder #8
    dict(kind='tube', name='DM::BarrelCryostat::Cylinder8::B', material='G4_Al', r0=2516.000, r1=2711.000, z0=-3390.000, z1=-3340.000, in_field=False),  # CryoCylinders-09, Barrel::CryoMother cylinder #8
    dict(kind='tube', name='DM::BarrelCryostat::Cylinder9::A', material='G4_Al', r0=2516.000, r1=2690.000, z0=3390.000, z1=3405.000, in_field=False),  # CryoCylinders-09, Barrel::CryoMother cylinder #9
    dict(kind='tube', name='DM::BarrelCryostat::Cylinder9::B', material='G4_Al', r0=2516.000, r1=2690.000, z0=-3405.000, z1=-3390.000, in_field=False),  # CryoCylinders-09, Barrel::CryoMother cylinder #9
    dict(kind='pcon', name='DM::BarrelCryostat::ColdEndWall::A', material='G4_Al', planes=[(3267.000, 1537.220, 2190.000), (3287.000, 1565.500, 2190.000), (3287.000, 1850.000, 2190.000), (3302.000, 1850.000, 2190.000)], in_field=False),  # CryoPcons-18 OuterWall planes 28-31
    dict(kind='pcon', name='DM::BarrelCryostat::ColdEndWall::B', material='G4_Al', planes=[(-3302.000, 1850.000, 2190.000), (-3287.000, 1850.000, 2190.000), (-3287.000, 1565.500, 2190.000), (-3267.000, 1537.220, 2190.000)], in_field=False),  # CryoPcons-18 OuterWall planes 0-3
    dict(kind='pcon', name='DM::BarrelCryostat::WarmEndWall::A', material='G4_Al', planes=[(3367.000, 1700.000, 2516.000), (3385.000, 1520.000, 2516.000), (3385.000, 1401.000, 2516.000), (3405.000, 1401.000, 2516.000)], in_field=False),  # InnerEndWall (Pcon, public GeoModel geometry)
    dict(kind='pcon', name='DM::BarrelCryostat::WarmEndWall::B', material='G4_Al', planes=[(-3405.000, 1401.000, 2516.000), (-3385.000, 1401.000, 2516.000), (-3385.000, 1520.000, 2516.000), (-3367.000, 1700.000, 2516.000)], in_field=False),  # InnerEndWall, mirrored
    dict(kind='tube', name='DM::BarrelCryostat::Support_R2280_Z2926::A', material='ATLAS_CRYO_SUPPORT_2280_2926', r0=2280.000, r1=2290.000, z0=2926.000, z1=2996.000, in_field=False),  # CryoEars-00 ears (0.290) and legs (0.000), phi-averaged aluminium
    dict(kind='tube', name='DM::BarrelCryostat::Support_R2280_Z2926::B', material='ATLAS_CRYO_SUPPORT_2280_2926', r0=2280.000, r1=2290.000, z0=-2996.000, z1=-2926.000, in_field=False),  # CryoEars-00 ears (0.290) and legs (0.000), phi-averaged aluminium
    dict(kind='tube', name='DM::BarrelCryostat::Support_R2290_Z2923::A', material='ATLAS_CRYO_SUPPORT_2290_2923', r0=2290.000, r1=2490.000, z0=2923.000, z1=2926.000, in_field=False),  # CryoEars-00 ears (0.000) and legs (0.051), phi-averaged aluminium
    dict(kind='tube', name='DM::BarrelCryostat::Support_R2290_Z2923::B', material='ATLAS_CRYO_SUPPORT_2290_2923', r0=2290.000, r1=2490.000, z0=-2926.000, z1=-2923.000, in_field=False),  # CryoEars-00 ears (0.000) and legs (0.051), phi-averaged aluminium
    dict(kind='tube', name='DM::BarrelCryostat::Support_R2290_Z2926::A', material='ATLAS_CRYO_SUPPORT_2290_2926', r0=2290.000, r1=2490.000, z0=2926.000, z1=2996.000, in_field=False),  # CryoEars-00 ears (0.276) and legs (0.051), phi-averaged aluminium
    dict(kind='tube', name='DM::BarrelCryostat::Support_R2290_Z2926::B', material='ATLAS_CRYO_SUPPORT_2290_2926', r0=2290.000, r1=2490.000, z0=-2996.000, z1=-2926.000, in_field=False),  # CryoEars-00 ears (0.276) and legs (0.051), phi-averaged aluminium
    dict(kind='tube', name='DM::BarrelCryostat::Support_R2290_Z2996::A', material='ATLAS_CRYO_SUPPORT_2290_2996', r0=2290.000, r1=2490.000, z0=2996.000, z1=3019.000, in_field=False),  # CryoEars-00 ears (0.000) and legs (0.051), phi-averaged aluminium
    dict(kind='tube', name='DM::BarrelCryostat::Support_R2290_Z2996::B', material='ATLAS_CRYO_SUPPORT_2290_2996', r0=2290.000, r1=2490.000, z0=-3019.000, z1=-2996.000, in_field=False),  # CryoEars-00 ears (0.000) and legs (0.051), phi-averaged aluminium
    dict(kind='tube', name='DM::BarrelCryostat::Support_R2490_Z2923::A', material='ATLAS_CRYO_SUPPORT_2490_2923', r0=2490.000, r1=2710.000, z0=2923.000, z1=2926.000, in_field=False),  # CryoEars-00 ears (0.000) and legs (0.064), phi-averaged aluminium
    dict(kind='tube', name='DM::BarrelCryostat::Support_R2490_Z2923::B', material='ATLAS_CRYO_SUPPORT_2490_2923', r0=2490.000, r1=2710.000, z0=-2926.000, z1=-2923.000, in_field=False),  # CryoEars-00 ears (0.000) and legs (0.064), phi-averaged aluminium
    dict(kind='tube', name='DM::BarrelCryostat::Support_R2490_Z2926::A', material='ATLAS_CRYO_SUPPORT_2490_2926', r0=2490.000, r1=2710.000, z0=2926.000, z1=2996.000, in_field=False),  # CryoEars-00 ears (0.000) and legs (0.064), phi-averaged aluminium
    dict(kind='tube', name='DM::BarrelCryostat::Support_R2490_Z2926::B', material='ATLAS_CRYO_SUPPORT_2490_2926', r0=2490.000, r1=2710.000, z0=-2996.000, z1=-2926.000, in_field=False),  # CryoEars-00 ears (0.000) and legs (0.064), phi-averaged aluminium
    dict(kind='tube', name='DM::BarrelCryostat::Support_R2490_Z2996::A', material='ATLAS_CRYO_SUPPORT_2490_2996', r0=2490.000, r1=2710.000, z0=2996.000, z1=3019.000, in_field=False),  # CryoEars-00 ears (0.000) and legs (0.064), phi-averaged aluminium
    dict(kind='tube', name='DM::BarrelCryostat::Support_R2490_Z2996::B', material='ATLAS_CRYO_SUPPORT_2490_2996', r0=2490.000, r1=2710.000, z0=-3019.000, z1=-2996.000, in_field=False),  # CryoEars-00 ears (0.000) and legs (0.064), phi-averaged aluminium
    dict(kind='tube', name='DM::BarrelCryostat::Inner0', material='liquidArgon', r0=1973.420, r1=1980.000, z0=-3165.000, z1=3165.000, in_field=False),  # TotalLAr (dead argon)
    dict(kind='tube', name='DM::BarrelCryostat::Inner1', material='liquidArgon', r0=1980.000, r1=1983.580, z0=-3205.000, z1=3205.000, in_field=False),  # TotalLAr (dead argon)
    dict(kind='tube', name='DM::BarrelCryostat::Inner2', material='liquidArgon', r0=1983.580, r1=2003.500, z0=-3.000, z1=3.000, in_field=False),  # TotalLAr (dead argon)
    dict(kind='tube', name='DM::BarrelCryostat::Inner3::A', material='ATLAS_G10_BAR', r0=1983.580, r1=2003.500, z0=3.000, z1=3165.000, in_field=False),  # GTENB (LAr::G10_bar), back G10 ring of the EM barrel
    dict(kind='tube', name='DM::BarrelCryostat::Inner3::B', material='ATLAS_G10_BAR', r0=1983.580, r1=2003.500, z0=-3165.000, z1=-3.000, in_field=False),  # GTENB (LAr::G10_bar), back G10 ring of the EM barrel
    dict(kind='tube', name='DM::BarrelCryostat::Inner4::A', material='liquidArgon', r0=1983.580, r1=2003.500, z0=3165.000, z1=3205.000, in_field=False),  # TotalLAr (dead argon)
    dict(kind='tube', name='DM::BarrelCryostat::Inner4::B', material='liquidArgon', r0=1983.580, r1=2003.500, z0=-3205.000, z1=-3165.000, in_field=False),  # TotalLAr (dead argon)
    dict(kind='tube', name='DM::BarrelCryostat::Inner5', material='liquidArgon', r0=2003.500, r1=2015.500, z0=-90.000, z1=90.000, in_field=False),  # TotalLAr (dead argon)
    dict(kind='tube', name='DM::BarrelCryostat::Inner6::A', material='G4_Fe', r0=2003.500, r1=2015.500, z0=90.000, z1=136.000, in_field=False),  # HalfLAr support ring (std::Iron)
    dict(kind='tube', name='DM::BarrelCryostat::Inner6::B', material='G4_Fe', r0=2003.500, r1=2015.500, z0=-136.000, z1=-90.000, in_field=False),  # HalfLAr support ring (std::Iron)
    dict(kind='tube', name='DM::BarrelCryostat::Inner7::A', material='liquidArgon', r0=2003.500, r1=2015.500, z0=136.000, z1=769.000, in_field=False),  # TotalLAr (dead argon)
    dict(kind='tube', name='DM::BarrelCryostat::Inner7::B', material='liquidArgon', r0=2003.500, r1=2015.500, z0=-769.000, z1=-136.000, in_field=False),  # TotalLAr (dead argon)
    dict(kind='tube', name='DM::BarrelCryostat::Inner8::A', material='G4_Fe', r0=2003.500, r1=2015.500, z0=769.000, z1=849.000, in_field=False),  # HalfLAr support ring (std::Iron)
    dict(kind='tube', name='DM::BarrelCryostat::Inner8::B', material='G4_Fe', r0=2003.500, r1=2015.500, z0=-849.000, z1=-769.000, in_field=False),  # HalfLAr support ring (std::Iron)
    dict(kind='tube', name='DM::BarrelCryostat::Inner9::A', material='liquidArgon', r0=2003.500, r1=2015.500, z0=849.000, z1=1215.000, in_field=False),  # TotalLAr (dead argon)
    dict(kind='tube', name='DM::BarrelCryostat::Inner9::B', material='liquidArgon', r0=2003.500, r1=2015.500, z0=-1215.000, z1=-849.000, in_field=False),  # TotalLAr (dead argon)
    dict(kind='tube', name='DM::BarrelCryostat::Inner10::A', material='G4_Fe', r0=2003.500, r1=2015.500, z0=1215.000, z1=1295.000, in_field=False),  # HalfLAr support ring (std::Iron)
    dict(kind='tube', name='DM::BarrelCryostat::Inner10::B', material='G4_Fe', r0=2003.500, r1=2015.500, z0=-1295.000, z1=-1215.000, in_field=False),  # HalfLAr support ring (std::Iron)
    dict(kind='tube', name='DM::BarrelCryostat::Inner11::A', material='liquidArgon', r0=2003.500, r1=2015.500, z0=1295.000, z1=1710.000, in_field=False),  # TotalLAr (dead argon)
    dict(kind='tube', name='DM::BarrelCryostat::Inner11::B', material='liquidArgon', r0=2003.500, r1=2015.500, z0=-1710.000, z1=-1295.000, in_field=False),  # TotalLAr (dead argon)
    dict(kind='tube', name='DM::BarrelCryostat::Inner12::A', material='G4_Fe', r0=2003.500, r1=2015.500, z0=1710.000, z1=1790.000, in_field=False),  # HalfLAr support ring (std::Iron)
    dict(kind='tube', name='DM::BarrelCryostat::Inner12::B', material='G4_Fe', r0=2003.500, r1=2015.500, z0=-1790.000, z1=-1710.000, in_field=False),  # HalfLAr support ring (std::Iron)
    dict(kind='tube', name='DM::BarrelCryostat::Inner13::A', material='liquidArgon', r0=2003.500, r1=2015.500, z0=1790.000, z1=2276.000, in_field=False),  # TotalLAr (dead argon)
    dict(kind='tube', name='DM::BarrelCryostat::Inner13::B', material='liquidArgon', r0=2003.500, r1=2015.500, z0=-2276.000, z1=-1790.000, in_field=False),  # TotalLAr (dead argon)
    dict(kind='tube', name='DM::BarrelCryostat::Inner14::A', material='G4_Fe', r0=2003.500, r1=2015.500, z0=2276.000, z1=2356.000, in_field=False),  # HalfLAr support ring (std::Iron)
    dict(kind='tube', name='DM::BarrelCryostat::Inner14::B', material='G4_Fe', r0=2003.500, r1=2015.500, z0=-2356.000, z1=-2276.000, in_field=False),  # HalfLAr support ring (std::Iron)
    dict(kind='tube', name='DM::BarrelCryostat::Inner15::A', material='liquidArgon', r0=2003.500, r1=2015.500, z0=2356.000, z1=2828.000, in_field=False),  # TotalLAr (dead argon)
    dict(kind='tube', name='DM::BarrelCryostat::Inner15::B', material='liquidArgon', r0=2003.500, r1=2015.500, z0=-2828.000, z1=-2356.000, in_field=False),  # TotalLAr (dead argon)
    dict(kind='tube', name='DM::BarrelCryostat::Inner16::A', material='G4_Fe', r0=2003.500, r1=2015.500, z0=2828.000, z1=2908.000, in_field=False),  # HalfLAr support ring (std::Iron)
    dict(kind='tube', name='DM::BarrelCryostat::Inner16::B', material='G4_Fe', r0=2003.500, r1=2015.500, z0=-2908.000, z1=-2828.000, in_field=False),  # HalfLAr support ring (std::Iron)
    dict(kind='tube', name='DM::BarrelCryostat::Inner17::A', material='liquidArgon', r0=2003.500, r1=2015.500, z0=2908.000, z1=3205.000, in_field=False),  # TotalLAr (dead argon)
    dict(kind='tube', name='DM::BarrelCryostat::Inner17::B', material='liquidArgon', r0=2003.500, r1=2015.500, z0=-3205.000, z1=-2908.000, in_field=False),  # TotalLAr (dead argon)
    dict(kind='tube', name='DM::BarrelCryostat::Inner18', material='liquidArgon', r0=2015.500, r1=2056.000, z0=-90.000, z1=90.000, in_field=False),  # TotalLAr (dead argon)
    dict(kind='tube', name='DM::BarrelCryostat::Inner19::A', material='G4_Fe', r0=2015.500, r1=2056.000, z0=90.000, z1=100.000, in_field=False),  # HalfLAr support ring (std::Iron)
    dict(kind='tube', name='DM::BarrelCryostat::Inner19::B', material='G4_Fe', r0=2015.500, r1=2056.000, z0=-100.000, z1=-90.000, in_field=False),  # HalfLAr support ring (std::Iron)
    dict(kind='tube', name='DM::BarrelCryostat::Inner20::A', material='liquidArgon', r0=2015.500, r1=2056.000, z0=100.000, z1=392.000, in_field=False),  # TotalLAr (dead argon)
    dict(kind='tube', name='DM::BarrelCryostat::Inner20::B', material='liquidArgon', r0=2015.500, r1=2056.000, z0=-392.000, z1=-100.000, in_field=False),  # TotalLAr (dead argon)
    dict(kind='tube', name='DM::BarrelCryostat::Inner21::A', material='G4_Fe', r0=2015.500, r1=2056.000, z0=392.000, z1=402.000, in_field=False),  # HalfLAr support ring (std::Iron)
    dict(kind='tube', name='DM::BarrelCryostat::Inner21::B', material='G4_Fe', r0=2015.500, r1=2056.000, z0=-402.000, z1=-392.000, in_field=False),  # HalfLAr support ring (std::Iron)
    dict(kind='tube', name='DM::BarrelCryostat::Inner22::A', material='liquidArgon', r0=2015.500, r1=2056.000, z0=402.000, z1=804.000, in_field=False),  # TotalLAr (dead argon)
    dict(kind='tube', name='DM::BarrelCryostat::Inner22::B', material='liquidArgon', r0=2015.500, r1=2056.000, z0=-804.000, z1=-402.000, in_field=False),  # TotalLAr (dead argon)
    dict(kind='tube', name='DM::BarrelCryostat::Inner23::A', material='G4_Fe', r0=2015.500, r1=2056.000, z0=804.000, z1=814.000, in_field=False),  # HalfLAr support ring (std::Iron)
    dict(kind='tube', name='DM::BarrelCryostat::Inner23::B', material='G4_Fe', r0=2015.500, r1=2056.000, z0=-814.000, z1=-804.000, in_field=False),  # HalfLAr support ring (std::Iron)
    dict(kind='tube', name='DM::BarrelCryostat::Inner24::A', material='liquidArgon', r0=2015.500, r1=2056.000, z0=814.000, z1=1250.000, in_field=False),  # TotalLAr (dead argon)
    dict(kind='tube', name='DM::BarrelCryostat::Inner24::B', material='liquidArgon', r0=2015.500, r1=2056.000, z0=-1250.000, z1=-814.000, in_field=False),  # TotalLAr (dead argon)
    dict(kind='tube', name='DM::BarrelCryostat::Inner25::A', material='G4_Fe', r0=2015.500, r1=2056.000, z0=1250.000, z1=1260.000, in_field=False),  # HalfLAr support ring (std::Iron)
    dict(kind='tube', name='DM::BarrelCryostat::Inner25::B', material='G4_Fe', r0=2015.500, r1=2056.000, z0=-1260.000, z1=-1250.000, in_field=False),  # HalfLAr support ring (std::Iron)
    dict(kind='tube', name='DM::BarrelCryostat::Inner26::A', material='liquidArgon', r0=2015.500, r1=2056.000, z0=1260.000, z1=1745.000, in_field=False),  # TotalLAr (dead argon)
    dict(kind='tube', name='DM::BarrelCryostat::Inner26::B', material='liquidArgon', r0=2015.500, r1=2056.000, z0=-1745.000, z1=-1260.000, in_field=False),  # TotalLAr (dead argon)
    dict(kind='tube', name='DM::BarrelCryostat::Inner27::A', material='G4_Fe', r0=2015.500, r1=2056.000, z0=1745.000, z1=1755.000, in_field=False),  # HalfLAr support ring (std::Iron)
    dict(kind='tube', name='DM::BarrelCryostat::Inner27::B', material='G4_Fe', r0=2015.500, r1=2056.000, z0=-1755.000, z1=-1745.000, in_field=False),  # HalfLAr support ring (std::Iron)
    dict(kind='tube', name='DM::BarrelCryostat::Inner28::A', material='liquidArgon', r0=2015.500, r1=2056.000, z0=1755.000, z1=2311.000, in_field=False),  # TotalLAr (dead argon)
    dict(kind='tube', name='DM::BarrelCryostat::Inner28::B', material='liquidArgon', r0=2015.500, r1=2056.000, z0=-2311.000, z1=-1755.000, in_field=False),  # TotalLAr (dead argon)
    dict(kind='tube', name='DM::BarrelCryostat::Inner29::A', material='G4_Fe', r0=2015.500, r1=2056.000, z0=2311.000, z1=2321.000, in_field=False),  # HalfLAr support ring (std::Iron)
    dict(kind='tube', name='DM::BarrelCryostat::Inner29::B', material='G4_Fe', r0=2015.500, r1=2056.000, z0=-2321.000, z1=-2311.000, in_field=False),  # HalfLAr support ring (std::Iron)
    dict(kind='tube', name='DM::BarrelCryostat::Inner30::A', material='liquidArgon', r0=2015.500, r1=2056.000, z0=2321.000, z1=2863.000, in_field=False),  # TotalLAr (dead argon)
    dict(kind='tube', name='DM::BarrelCryostat::Inner30::B', material='liquidArgon', r0=2015.500, r1=2056.000, z0=-2863.000, z1=-2321.000, in_field=False),  # TotalLAr (dead argon)
    dict(kind='tube', name='DM::BarrelCryostat::Inner31::A', material='G4_Fe', r0=2015.500, r1=2056.000, z0=2863.000, z1=2873.000, in_field=False),  # HalfLAr support ring (std::Iron)
    dict(kind='tube', name='DM::BarrelCryostat::Inner31::B', material='G4_Fe', r0=2015.500, r1=2056.000, z0=-2873.000, z1=-2863.000, in_field=False),  # HalfLAr support ring (std::Iron)
    dict(kind='tube', name='DM::BarrelCryostat::Inner32::A', material='liquidArgon', r0=2015.500, r1=2056.000, z0=2873.000, z1=3205.000, in_field=False),  # TotalLAr (dead argon)
    dict(kind='tube', name='DM::BarrelCryostat::Inner32::B', material='liquidArgon', r0=2015.500, r1=2056.000, z0=-3205.000, z1=-2873.000, in_field=False),  # TotalLAr (dead argon)
    dict(kind='tube', name='DM::BarrelCryostat::Inner33', material='liquidArgon', r0=2056.000, r1=2091.200, z0=-3.000, z1=3.000, in_field=False),  # TotalLAr (dead argon)
    dict(kind='tube', name='DM::BarrelCryostat::Inner34::A', material='G4_Al', r0=2056.000, r1=2091.200, z0=3.000, z1=75.000, in_field=False),  # TotalLAr cylinder 20 (Al ring)
    dict(kind='tube', name='DM::BarrelCryostat::Inner34::B', material='G4_Al', r0=2056.000, r1=2091.200, z0=-75.000, z1=-3.000, in_field=False),  # TotalLAr cylinder 20 (Al ring)
    dict(kind='tube', name='DM::BarrelCryostat::Inner35::A', material='liquidArgon', r0=2056.000, r1=2091.200, z0=75.000, z1=90.000, in_field=False),  # TotalLAr (dead argon)
    dict(kind='tube', name='DM::BarrelCryostat::Inner35::B', material='liquidArgon', r0=2056.000, r1=2091.200, z0=-90.000, z1=-75.000, in_field=False),  # TotalLAr (dead argon)
    dict(kind='tube', name='DM::BarrelCryostat::Inner36::A', material='G4_Fe', r0=2056.000, r1=2091.200, z0=90.000, z1=100.000, in_field=False),  # HalfLAr support ring (std::Iron)
    dict(kind='tube', name='DM::BarrelCryostat::Inner36::B', material='G4_Fe', r0=2056.000, r1=2091.200, z0=-100.000, z1=-90.000, in_field=False),  # HalfLAr support ring (std::Iron)
    dict(kind='tube', name='DM::BarrelCryostat::Inner37::A', material='liquidArgon', r0=2056.000, r1=2091.200, z0=100.000, z1=392.000, in_field=False),  # TotalLAr (dead argon)
    dict(kind='tube', name='DM::BarrelCryostat::Inner37::B', material='liquidArgon', r0=2056.000, r1=2091.200, z0=-392.000, z1=-100.000, in_field=False),  # TotalLAr (dead argon)
    dict(kind='tube', name='DM::BarrelCryostat::Inner38::A', material='G4_Fe', r0=2056.000, r1=2091.200, z0=392.000, z1=402.000, in_field=False),  # HalfLAr support ring (std::Iron)
    dict(kind='tube', name='DM::BarrelCryostat::Inner38::B', material='G4_Fe', r0=2056.000, r1=2091.200, z0=-402.000, z1=-392.000, in_field=False),  # HalfLAr support ring (std::Iron)
    dict(kind='tube', name='DM::BarrelCryostat::Inner39::A', material='liquidArgon', r0=2056.000, r1=2091.200, z0=402.000, z1=804.000, in_field=False),  # TotalLAr (dead argon)
    dict(kind='tube', name='DM::BarrelCryostat::Inner39::B', material='liquidArgon', r0=2056.000, r1=2091.200, z0=-804.000, z1=-402.000, in_field=False),  # TotalLAr (dead argon)
    dict(kind='tube', name='DM::BarrelCryostat::Inner40::A', material='G4_Fe', r0=2056.000, r1=2091.200, z0=804.000, z1=814.000, in_field=False),  # HalfLAr support ring (std::Iron)
    dict(kind='tube', name='DM::BarrelCryostat::Inner40::B', material='G4_Fe', r0=2056.000, r1=2091.200, z0=-814.000, z1=-804.000, in_field=False),  # HalfLAr support ring (std::Iron)
    dict(kind='tube', name='DM::BarrelCryostat::Inner41::A', material='liquidArgon', r0=2056.000, r1=2091.200, z0=814.000, z1=1250.000, in_field=False),  # TotalLAr (dead argon)
    dict(kind='tube', name='DM::BarrelCryostat::Inner41::B', material='liquidArgon', r0=2056.000, r1=2091.200, z0=-1250.000, z1=-814.000, in_field=False),  # TotalLAr (dead argon)
    dict(kind='tube', name='DM::BarrelCryostat::Inner42::A', material='G4_Fe', r0=2056.000, r1=2091.200, z0=1250.000, z1=1260.000, in_field=False),  # HalfLAr support ring (std::Iron)
    dict(kind='tube', name='DM::BarrelCryostat::Inner42::B', material='G4_Fe', r0=2056.000, r1=2091.200, z0=-1260.000, z1=-1250.000, in_field=False),  # HalfLAr support ring (std::Iron)
    dict(kind='tube', name='DM::BarrelCryostat::Inner43::A', material='liquidArgon', r0=2056.000, r1=2091.200, z0=1260.000, z1=1745.000, in_field=False),  # TotalLAr (dead argon)
    dict(kind='tube', name='DM::BarrelCryostat::Inner43::B', material='liquidArgon', r0=2056.000, r1=2091.200, z0=-1745.000, z1=-1260.000, in_field=False),  # TotalLAr (dead argon)
    dict(kind='tube', name='DM::BarrelCryostat::Inner44::A', material='G4_Fe', r0=2056.000, r1=2091.200, z0=1745.000, z1=1755.000, in_field=False),  # HalfLAr support ring (std::Iron)
    dict(kind='tube', name='DM::BarrelCryostat::Inner44::B', material='G4_Fe', r0=2056.000, r1=2091.200, z0=-1755.000, z1=-1745.000, in_field=False),  # HalfLAr support ring (std::Iron)
    dict(kind='tube', name='DM::BarrelCryostat::Inner45::A', material='liquidArgon', r0=2056.000, r1=2091.200, z0=1755.000, z1=2311.000, in_field=False),  # TotalLAr (dead argon)
    dict(kind='tube', name='DM::BarrelCryostat::Inner45::B', material='liquidArgon', r0=2056.000, r1=2091.200, z0=-2311.000, z1=-1755.000, in_field=False),  # TotalLAr (dead argon)
    dict(kind='tube', name='DM::BarrelCryostat::Inner46::A', material='G4_Fe', r0=2056.000, r1=2091.200, z0=2311.000, z1=2321.000, in_field=False),  # HalfLAr support ring (std::Iron)
    dict(kind='tube', name='DM::BarrelCryostat::Inner46::B', material='G4_Fe', r0=2056.000, r1=2091.200, z0=-2321.000, z1=-2311.000, in_field=False),  # HalfLAr support ring (std::Iron)
    dict(kind='tube', name='DM::BarrelCryostat::Inner47::A', material='liquidArgon', r0=2056.000, r1=2091.200, z0=2321.000, z1=2863.000, in_field=False),  # TotalLAr (dead argon)
    dict(kind='tube', name='DM::BarrelCryostat::Inner47::B', material='liquidArgon', r0=2056.000, r1=2091.200, z0=-2863.000, z1=-2321.000, in_field=False),  # TotalLAr (dead argon)
    dict(kind='tube', name='DM::BarrelCryostat::Inner48::A', material='G4_Fe', r0=2056.000, r1=2091.200, z0=2863.000, z1=2873.000, in_field=False),  # HalfLAr support ring (std::Iron)
    dict(kind='tube', name='DM::BarrelCryostat::Inner48::B', material='G4_Fe', r0=2056.000, r1=2091.200, z0=-2873.000, z1=-2863.000, in_field=False),  # HalfLAr support ring (std::Iron)
    dict(kind='tube', name='DM::BarrelCryostat::Inner49::A', material='liquidArgon', r0=2056.000, r1=2091.200, z0=2873.000, z1=3205.000, in_field=False),  # TotalLAr (dead argon)
    dict(kind='tube', name='DM::BarrelCryostat::Inner49::B', material='liquidArgon', r0=2056.000, r1=2091.200, z0=-3205.000, z1=-2873.000, in_field=False),  # TotalLAr (dead argon)
    dict(kind='tube', name='DM::BarrelCryostat::Inner50', material='liquidArgon', r0=2091.200, r1=2103.200, z0=-3.000, z1=3.000, in_field=False),  # TotalLAr (dead argon)
    dict(kind='tube', name='DM::BarrelCryostat::Inner51::A', material='G4_Al', r0=2091.200, r1=2103.200, z0=3.000, z1=75.000, in_field=False),  # TotalLAr cylinder 20 (Al ring)
    dict(kind='tube', name='DM::BarrelCryostat::Inner51::B', material='G4_Al', r0=2091.200, r1=2103.200, z0=-75.000, z1=-3.000, in_field=False),  # TotalLAr cylinder 20 (Al ring)
    dict(kind='tube', name='DM::BarrelCryostat::Inner52::A', material='liquidArgon', r0=2091.200, r1=2103.200, z0=75.000, z1=90.000, in_field=False),  # TotalLAr (dead argon)
    dict(kind='tube', name='DM::BarrelCryostat::Inner52::B', material='liquidArgon', r0=2091.200, r1=2103.200, z0=-90.000, z1=-75.000, in_field=False),  # TotalLAr (dead argon)
    dict(kind='tube', name='DM::BarrelCryostat::Inner53::A', material='G4_Fe', r0=2091.200, r1=2103.200, z0=90.000, z1=136.000, in_field=False),  # HalfLAr support ring (std::Iron)
    dict(kind='tube', name='DM::BarrelCryostat::Inner53::B', material='G4_Fe', r0=2091.200, r1=2103.200, z0=-136.000, z1=-90.000, in_field=False),  # HalfLAr support ring (std::Iron)
    dict(kind='tube', name='DM::BarrelCryostat::Inner54::A', material='liquidArgon', r0=2091.200, r1=2103.200, z0=136.000, z1=357.000, in_field=False),  # TotalLAr (dead argon)
    dict(kind='tube', name='DM::BarrelCryostat::Inner54::B', material='liquidArgon', r0=2091.200, r1=2103.200, z0=-357.000, z1=-136.000, in_field=False),  # TotalLAr (dead argon)
    dict(kind='tube', name='DM::BarrelCryostat::Inner55::A', material='G4_Fe', r0=2091.200, r1=2103.200, z0=357.000, z1=437.000, in_field=False),  # HalfLAr support ring (std::Iron)
    dict(kind='tube', name='DM::BarrelCryostat::Inner55::B', material='G4_Fe', r0=2091.200, r1=2103.200, z0=-437.000, z1=-357.000, in_field=False),  # HalfLAr support ring (std::Iron)
    dict(kind='tube', name='DM::BarrelCryostat::Inner56::A', material='liquidArgon', r0=2091.200, r1=2103.200, z0=437.000, z1=769.000, in_field=False),  # TotalLAr (dead argon)
    dict(kind='tube', name='DM::BarrelCryostat::Inner56::B', material='liquidArgon', r0=2091.200, r1=2103.200, z0=-769.000, z1=-437.000, in_field=False),  # TotalLAr (dead argon)
    dict(kind='tube', name='DM::BarrelCryostat::Inner57::A', material='G4_Fe', r0=2091.200, r1=2103.200, z0=769.000, z1=849.000, in_field=False),  # HalfLAr support ring (std::Iron)
    dict(kind='tube', name='DM::BarrelCryostat::Inner57::B', material='G4_Fe', r0=2091.200, r1=2103.200, z0=-849.000, z1=-769.000, in_field=False),  # HalfLAr support ring (std::Iron)
    dict(kind='tube', name='DM::BarrelCryostat::Inner58::A', material='liquidArgon', r0=2091.200, r1=2103.200, z0=849.000, z1=1215.000, in_field=False),  # TotalLAr (dead argon)
    dict(kind='tube', name='DM::BarrelCryostat::Inner58::B', material='liquidArgon', r0=2091.200, r1=2103.200, z0=-1215.000, z1=-849.000, in_field=False),  # TotalLAr (dead argon)
    dict(kind='tube', name='DM::BarrelCryostat::Inner59::A', material='G4_Fe', r0=2091.200, r1=2103.200, z0=1215.000, z1=1295.000, in_field=False),  # HalfLAr support ring (std::Iron)
    dict(kind='tube', name='DM::BarrelCryostat::Inner59::B', material='G4_Fe', r0=2091.200, r1=2103.200, z0=-1295.000, z1=-1215.000, in_field=False),  # HalfLAr support ring (std::Iron)
    dict(kind='tube', name='DM::BarrelCryostat::Inner60::A', material='liquidArgon', r0=2091.200, r1=2103.200, z0=1295.000, z1=1710.000, in_field=False),  # TotalLAr (dead argon)
    dict(kind='tube', name='DM::BarrelCryostat::Inner60::B', material='liquidArgon', r0=2091.200, r1=2103.200, z0=-1710.000, z1=-1295.000, in_field=False),  # TotalLAr (dead argon)
    dict(kind='tube', name='DM::BarrelCryostat::Inner61::A', material='G4_Fe', r0=2091.200, r1=2103.200, z0=1710.000, z1=1790.000, in_field=False),  # HalfLAr support ring (std::Iron)
    dict(kind='tube', name='DM::BarrelCryostat::Inner61::B', material='G4_Fe', r0=2091.200, r1=2103.200, z0=-1790.000, z1=-1710.000, in_field=False),  # HalfLAr support ring (std::Iron)
    dict(kind='tube', name='DM::BarrelCryostat::Inner62::A', material='liquidArgon', r0=2091.200, r1=2103.200, z0=1790.000, z1=2276.000, in_field=False),  # TotalLAr (dead argon)
    dict(kind='tube', name='DM::BarrelCryostat::Inner62::B', material='liquidArgon', r0=2091.200, r1=2103.200, z0=-2276.000, z1=-1790.000, in_field=False),  # TotalLAr (dead argon)
    dict(kind='tube', name='DM::BarrelCryostat::Inner63::A', material='G4_Fe', r0=2091.200, r1=2103.200, z0=2276.000, z1=2356.000, in_field=False),  # HalfLAr support ring (std::Iron)
    dict(kind='tube', name='DM::BarrelCryostat::Inner63::B', material='G4_Fe', r0=2091.200, r1=2103.200, z0=-2356.000, z1=-2276.000, in_field=False),  # HalfLAr support ring (std::Iron)
    dict(kind='tube', name='DM::BarrelCryostat::Inner64::A', material='liquidArgon', r0=2091.200, r1=2103.200, z0=2356.000, z1=2828.000, in_field=False),  # TotalLAr (dead argon)
    dict(kind='tube', name='DM::BarrelCryostat::Inner64::B', material='liquidArgon', r0=2091.200, r1=2103.200, z0=-2828.000, z1=-2356.000, in_field=False),  # TotalLAr (dead argon)
    dict(kind='tube', name='DM::BarrelCryostat::Inner65::A', material='G4_Fe', r0=2091.200, r1=2103.200, z0=2828.000, z1=2908.000, in_field=False),  # HalfLAr support ring (std::Iron)
    dict(kind='tube', name='DM::BarrelCryostat::Inner65::B', material='G4_Fe', r0=2091.200, r1=2103.200, z0=-2908.000, z1=-2828.000, in_field=False),  # HalfLAr support ring (std::Iron)
    dict(kind='tube', name='DM::BarrelCryostat::Inner66::A', material='liquidArgon', r0=2091.200, r1=2103.200, z0=2908.000, z1=3205.000, in_field=False),  # TotalLAr (dead argon)
    dict(kind='tube', name='DM::BarrelCryostat::Inner66::B', material='liquidArgon', r0=2091.200, r1=2103.200, z0=-3205.000, z1=-2908.000, in_field=False),  # TotalLAr (dead argon)
    dict(kind='tube', name='DM::BarrelCryostat::Inner67', material='liquidArgon', r0=2103.200, r1=2140.000, z0=-3.000, z1=3.000, in_field=False),  # TotalLAr (dead argon)
    dict(kind='tube', name='DM::BarrelCryostat::Inner68::A', material='G4_Al', r0=2103.200, r1=2140.000, z0=3.000, z1=75.000, in_field=False),  # TotalLAr cylinder 20 (Al ring)
    dict(kind='tube', name='DM::BarrelCryostat::Inner68::B', material='G4_Al', r0=2103.200, r1=2140.000, z0=-75.000, z1=-3.000, in_field=False),  # TotalLAr cylinder 20 (Al ring)
    dict(kind='tube', name='DM::BarrelCryostat::Inner69::A', material='liquidArgon', r0=2103.200, r1=2140.000, z0=75.000, z1=3205.000, in_field=False),  # TotalLAr (dead argon)
    dict(kind='tube', name='DM::BarrelCryostat::Inner69::B', material='liquidArgon', r0=2103.200, r1=2140.000, z0=-3205.000, z1=-75.000, in_field=False),  # TotalLAr (dead argon)
]
