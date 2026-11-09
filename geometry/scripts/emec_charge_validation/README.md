# Validation of the ported EMEC charge collection against Athena 23.0.14 (F41 conserto 29)

The port (`geometry/LArG4EC`, `geometry/GeoSpecialShapes`, `geometry/src/LArG4EC_*.cxx`, `geometry/src/GeoSpecialShapes_*.cxx`) is
compared field by field, in hexadecimal, with `LArG4::EC::EnergyCalculator` of Athena 23.0.14 itself (`libAtlasGeant4.so`), for the four
wheel calculators `EMEC{Pos,Neg}{Inner,Outer}WheelCalculator` configured by `LArG4ECConfig.py`.

1. `python3 generate_steps.py steps.txt` (36000 steps in the local frames of the wheels).
2. Athena (lxplus, centos7 container, `asetup Athena,23.0.14`): build `athena/source` (a minimal work project with the algorithm
   `EmecHarnessAlg`; the private headers of LArG4EC are copies of the release in `athena_private/`), source its `setup.sh` and run
   `python athena/run_harness.py steps.txt athena.txt`. The geometry tag is ATLAS-P2-RUN4-01-01-00.
3. Port: `bash build_port.sh <fork>/geometry <work dir> <label>`, in the Lorenzetti container and on lxplus after the `asetup` (it uses the
   `geant4-config` and `root-config` of the environment).
4. `python3 compare.py athena.txt port_<label>.txt`.

Result (15/10/2026): built in the environment of the Athena release (glibc 2.17, ROOT 6.26/08), the port is identical bit by bit to
Athena in all the fields of the 36000 steps and of the initialization. In the Lorenzetti container (glibc 2.35, ROOT 6.34.00) the inner
wheel is identical; in the outer wheel the coefficients of the sin/cos polynomial of the wave angle (`sincos_poly.cxx`, a degree-5 least
squares fit inverted with `TMatrixDSym::Invert`) differ in their last bits (one element of the normal matrix differs by 1 ulp, from
`pow`; the ROOT 6.34 inversion differs from ROOT 6.26 even with the same matrix), and the energy of a step differs by up to 2.7e-7
(relative; median 1e-9). With the coefficients of Athena imposed (`evaluate_port` with a 6th argument, diagnostic only) the
differences drop to 3.4e-14.

Decision of Luciano (15/10/2026): the outer wheel uses the coefficients computed by Athena 23.0.14, recorded in
geometry/src/GeoSpecialShapes_sincos_poly.cxx (outer_params; the fit code is kept as the reference and still used for the inner wheel).
With them the port is still identical bit by bit to Athena in the environment of the release, and in the Lorenzetti container the
largest difference is 3.4e-14 (relative) in the energy of a step and 4.6e-13 mm in the coordinates rotated to the fan frame (sin/cos
of glibc 2.35 in rotateZ).
