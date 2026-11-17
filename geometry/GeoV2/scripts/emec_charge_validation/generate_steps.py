#!/usr/bin/env python3
# F41 conserto 29: test steps to validate the port of the EMEC charge collection (EnergyCalculator::GetCurrent1 and helpers)
# against Athena 23.0.14. The points are in the local frame of the ATLAS wheel (that of its LAr volume: z from 0 to 514 mm from
# the front face, z along the beam), as the EnergyCalculator receives them.
# Output: one line per step: calc x1 y1 z1 x2 y2 z2 edep  (calc: 0 = PosInner, 1 = PosOuter, 2 = NegInner, 3 = NegOuter; mm, MeV)
# The numbers are written with %.17g, which strtod reads back exactly.
# Usage: python3 generate_steps.py steps.txt
import math, random, sys

random.seed(29151026)

# geometry of the wheels from the database (EmecGeometry-01, EmecMagicNumbers-01, EmecWheelParameters-00), as in
# LArWheelCalculator::GetWheelInnerRadius / GetWheelOuterRadius
Z_FRONT = 3691.0 + 11.0          # dMechFocaltoWRP + dWRPtoFrontFace
THICK = 510.0 + 2 * 2.0          # ActiveLength + 2 StraightStartSection
HALF_CRACK = 1.5
R_CUT = 2034.0
def tan_theta(eta): return 2 * math.exp(-eta) / (1 - math.exp(-2 * eta))

def r_limites(inner, z):
    """minimum and maximum radius of the wheel at local z (interpolated as the polycone of EMECConstruction)"""
    zf, zb = Z_FRONT, Z_FRONT + THICK
    if inner:
        rmin = (zf + z) * tan_theta(3.2)
        rmax = (zf + z) * tan_theta(2.5) - HALF_CRACK
    else:
        rmin = (zf + z) * tan_theta(2.5) + HALF_CRACK
        rmax = min((zf + z) * tan_theta(1.375), R_CUT)
    return rmin, rmax

def ponto(inner, z=None, r=None, phi=None, fora=0.0):
    if z is None: z = random.uniform(-fora, THICK + fora)
    rmin, rmax = r_limites(inner, min(max(z, 0.0), THICK))
    if r is None: r = random.uniform(rmin - fora, rmax + fora)
    if phi is None: phi = random.uniform(0, 2 * math.pi)
    return [r * math.cos(phi), r * math.sin(phi), z]

def direcao():
    c = random.uniform(-1, 1); p = random.uniform(0, 2 * math.pi); s = math.sqrt(1 - c * c)
    return [s * math.cos(p), s * math.sin(p), c]

def passo(p1, comp):
    d = direcao()
    return [p1[i] + comp * d[i] for i in range(3)]

def edep(): return 10 ** random.uniform(-4, 0)

linhas = []
def add(calc, p1, p2):
    linhas.append("%d %s %s %.17g" % (calc, " ".join("%.17g" % v for v in p1), " ".join("%.17g" % v for v in p2), edep()))

for calc in range(4):
    inner = calc in (0, 2)
    nfans = 256 if inner else 768
    hwl = 510.0 / (12 if inner else 18)
    # A: random in the volume (and 2 mm beyond its edges), steps of 0.01 to 10 mm
    for _ in range(4000):
        p1 = ponto(inner, fora=2.0); add(calc, p1, passo(p1, 10 ** random.uniform(-2, 1)))
    # B: scans in phi at fixed (r, z), across absorber, LAr and electrode of two periods
    for _ in range(20):
        z = random.uniform(0, THICK); rmin, rmax = r_limites(inner, z); r = random.uniform(rmin, rmax)
        phi0 = random.uniform(0, 2 * math.pi)
        for k in range(150):
            p1 = ponto(inner, z=z, r=r, phi=phi0 + k * (2 * 2 * math.pi / nfans) / 150)
            add(calc, p1, passo(p1, 10 ** random.uniform(-2, -0.3)))
    # C: near the folds (z = 2 + k half-waves), within 3 mm
    for _ in range(1000):
        k = random.randint(0, 2 * (6 if inner else 9))
        z = 2.0 + k * hwl + random.uniform(-3, 3)
        p1 = ponto(inner, z=min(max(z, 0.0), THICK)); add(calc, p1, passo(p1, 10 ** random.uniform(-2, 0.5)))
    # D: edges of the wheel (faces in z, minimum and maximum radius)
    for _ in range(500):
        z = random.choice([random.uniform(0, 0.5), random.uniform(THICK - 0.5, THICK), random.uniform(0, THICK)])
        rmin, rmax = r_limites(inner, z)
        r = random.choice([rmin + random.uniform(0, 1), rmax - random.uniform(0, 1)])
        p1 = ponto(inner, z=z, r=r); add(calc, p1, passo(p1, 10 ** random.uniform(-2, 0.5)))
    # E: long steps (5 to 20 mm), across several gaps
    for _ in range(500):
        p1 = ponto(inner); add(calc, p1, passo(p1, random.uniform(5, 20)))

with open(sys.argv[1], "w") as f:
    f.write("\n".join(linhas) + "\n")
print(len(linhas), "steps in", sys.argv[1])
