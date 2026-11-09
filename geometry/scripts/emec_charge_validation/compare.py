#!/usr/bin/env python3
# F41 conserto 29: compares, field by field and bit by bit, the output of the Athena harness with that of the port.
# Each different numeric field is measured in ulp. Usage: python3 compare.py athena.txt port.txt
import math, struct, sys
from collections import Counter

def ulps(a, b):
    if math.isnan(a) and math.isnan(b): return 0
    if a == b: return 0
    ia = struct.unpack('<q', struct.pack('<d', a))[0]; ib = struct.unpack('<q', struct.pack('<d', b))[0]
    if ia < 0: ia = -(ia & 0x7fffffffffffffff)
    if ib < 0: ib = -(ib & 0x7fffffffffffffff)
    return abs(ia - ib)

A = open(sys.argv[1]).read().split("\n"); B = open(sys.argv[2]).read().split("\n")
print("lines:", len(A), len(B))
nlin = ndif = 0; maxu = 0; cols = Counter(); exemplos = []
# columns of S: 0 'S', 1 idx, 2 gap, 3 HV, 4 efield, 5 birks, 6 CC1, 7 electrode distance, then the two points
nomes = {2: "gap", 3: "HV", 4: "efield", 5: "birks", 6: "CC1", 7: "electrode_distance"}
cc_rel = 0.0
for la, lb in zip(A, B):
    if la == lb: continue
    nlin += 1
    ta, tb = la.split(), lb.split()
    if len(ta) != len(tb) or ta[0] != "S":
        exemplos.append((la[:200], lb[:200])); ndif += 1; continue
    for k, (x, y) in enumerate(zip(ta, tb)):
        if x == y: continue
        ndif += 1; cols[nomes.get(k, k)] += 1
        try:
            fx, fy = float.fromhex(x), float.fromhex(y)
            u = ulps(fx, fy); maxu = max(maxu, u)
            if k == 6 and fx != 0: cc_rel = max(cc_rel, abs(fy / fx - 1))
        except ValueError:
            exemplos.append((x, y))
print("different lines:", nlin, " different fields:", ndif, " largest difference (ulp):", maxu)
print("fields that differ (column: times):", dict(cols.most_common(20)))
print("largest relative difference of the energy (CC1):", cc_rel)
for e in exemplos[:10]: print("  not numeric:", e)
