__all__ = ["readAtlasFcalElectrodes", "AtlasFcalModule", "getAtlasFcalCellsCfg"]

"""
The ATLAS forward calorimeter with its electrodes and cells (simu_trf.py --atlas-fcal-cells; F41 conserto 22).

As in the ATLAS simulation (Athena, LArCalorimeter/LArGeoModel/LArGeoFcal FCALConstruction.cxx, LArCalorimeter/LArG4/LArG4FCAL
LArFCALCalculatorBase.cc):
- each module is a tube of absorber holding one liquid argon gap per electrode, at the (X, Y) of the electrode, as long as the
  module; the gap is a ring in FCal1 (its inner copper rod is part of the absorber) and a cylinder holding a tungsten rod in
  FCal2 and FCal3; the cable troughs at the outer radius come before the gaps (dimensions and materials: AtlasFCal.py, from
  the public GeoModel geometry);
- the gaps of a module are numbered 0, 1, 2... in the order of the rows of that module in the table LArFCalElectrodes of the
  ATLAS geometry database (GeoSerialIdentifier(0) in FCALConstruction.cxx), and the cell of a step is the tile of the row of
  its copy number (FCAL_ChannelMap::getTubeByCopyNumber); only the liquid argon of the gaps is sensitive;
- the cell identifier is channel_id(pos_neg, module, eta, phi) of LArFCAL_ID, with phi = characters 3-4 and eta = characters
  6-8 of the tile name (FCAL_ChannelMap::add_tube).
The electrodes of side C sit at the same (X, Y) as those of side A, with z mirrored: the ATLAS geometry turns each module of
side C by 180 degrees about y inside the end-cap C, itself turned by 180 degrees about y, and the cell centres of side C in
the ATLAS HITS ntuple are at the (X, Y) of the table.

The table is read at run time from a CSV file (columns TILENAME, MODNUMBER, X, Y in cm, in the order of the database rows):
geometry/data/LArFCalElectrodes-06.csv, the table LArFCalElectrodes-06 of the Run 3 geometry ATLAS-R3S-2021-03-00-03, from the
SQLite copy of the ATLAS geometry database in CVMFS (/cvmfs/atlas.cern.ch/repo/sw/database/DBRelease/400.2.442/geomDB/geomDB_sqlite),
written by geometry/scripts/fcal_electrodes_from_geomdb.py, which also writes it for another geometry tag.
"""

import csv, math, os
from CaloCell.CaloDefs import Detector, CaloSampling
from GaugiKernel.constants import MeV
from .AtlasFCal import ATLAS_FCAL_CELL_MODULES, ATLAS_FCAL_CELL_MATERIALS
from .PhysicalVolume import ProductionCuts

# Birks constant of the liquid argon in the ATLAS FCal (LArG4FCALConfig.py)
FCAL_BIRKS_K = 0.0486


def readAtlasFcalElectrodes( path ):
    """
    Electrodes of the ATLAS FCal from the CSV file of geometry/scripts/fcal_electrodes_from_geomdb.py: for each module (1-3),
    the list of (x, y, phi index, eta index, I, J), x and y in mm, in the order of the rows of the table (the copy number of the
    gap); I and J are the indices of the electrode in the hexagonal grid of FCAL_ChannelMap.
    """
    out = {1: [], 2: [], 3: []}
    with open( path, newline='' ) as f:
        rows = list( csv.DictReader(f) )
    if rows and 'LARFCALELECTRODES_DATA_ID' in rows[0]:
        rows.sort( key = lambda r: int(r['LARFCALELECTRODES_DATA_ID']) )
    for r in rows:
        name = r['TILENAME']
        out[int(r['MODNUMBER'])].append( (float(r['X']) * 10., float(r['Y']) * 10., int(name[3:5]), int(name[6:9]),
                                          int(r['I']), int(r['J'])) )
    for m in ATLAS_FCAL_CELL_MODULES:
        if len( out[m['module']] ) != m['electrodes']:
            raise RuntimeError( f"FCal{m['module']}: {len(out[m['module']])} electrodes in {path}, "
                                f"{m['electrodes']} in the ATLAS geometry" )
    return out


class AtlasFcalModule:
    """
    One module of the ATLAS FCal on one side: the volume built by DetectorConstruction_v2::AddFCalModule and the fields read by
    its CaloHitMaker (FCalModule > 0), which records one hit per tile in the hit collection (sampling FCAL1-FCAL3) and, with the
    free-running hits, feeds LArHitFCAL.
    """
    def __init__( self, m, side, electrodes ):
        self.Module   = m['module']
        self.Side     = side
        sname         = 'A' if side > 0 else 'B'
        self.Name     = f"LAr::FCAL::Module{self.Module}::{sname}"
        self.Absorber = m['absorber']
        self.RodMaterial = m['rod_material']
        self.TroughMaterial = m['trough_material']
        self.RMin = m['rmin'];  self.RMax = m['rmax']
        self.Z    = side * m['zc'];  self.HalfZ = m['halfz']
        self.ZMin = self.Z - self.HalfZ;  self.ZMax = self.Z + self.HalfZ
        self.GapRMin = m['gap_rmin'];  self.GapRMax = m['gap_rmax'];  self.RodR = m['rod_r']
        self.TroughRMin = m['trough_rmin'];  self.TroughRMax = m['trough_rmax']
        self.TroughSPhi = m['trough_sphi'];  self.TroughDPhi = m['trough_dphi'];  self.TroughAngles = list(m['trough_angles'])
        self.X = [e[0] for e in electrodes];  self.Y = [e[1] for e in electrodes]
        self.Cuts = ProductionCuts()
        # cell of each copy number and the centre of its tile (mean of its electrodes; z of the centre of the module)
        self.CopyPhiIndex = [e[2] for e in electrodes]
        self.CopyEtaIndex = [e[3] for e in electrodes]
        # grid indices of each electrode (FCAL_ChannelMap), for the cell of the spots of the frozen showers (F41 conserto 23)
        self.CopyI = [e[4] for e in electrodes];  self.CopyJ = [e[5] for e in electrodes]
        sums = {}
        for x, y, ip, ie, *_ in electrodes:
            s = sums.setdefault( (ip, ie), [0., 0., 0] ); s[0] += x; s[1] += y; s[2] += 1
        centre = {}
        for k, (sx, sy, n) in sums.items():
            x, y = sx / n, sy / n
            centre[k] = ( math.asinh( self.Z / math.hypot(x, y) ), math.atan2(y, x) )
        self.CopyEta = [centre[(e[2], e[3])][0] for e in electrodes]
        self.CopyPhi = [centre[(e[2], e[3])][1] for e in electrodes]
        self.NCells  = len(centre)
        self.Sampling = [CaloSampling.FCAL1, CaloSampling.FCAL2, CaloSampling.FCAL3][self.Module - 1]
        self.Detector = Detector.FCALEM if self.Module == 1 else Detector.FCALHAD
        self.CollectionKey = "Collection_" + self.name()

    # Width of the tile of each copy number, for the hits of the normal chain: the range of eta and phi of the centres of the
    # electrodes of the tile plus one step of the grid (spacing 7.5, 8.179 and 9.0 mm, FCAL_ChannelMap) seen at the centre of
    # the tile; an approximation, since the tiles are not an eta x phi grid. Computed from the current Z (shifted in Run 4).
    def _tileWidths( self ):
        spacing = {1: 7.5, 2: 8.179, 3: 9.0}[self.Module]
        tiles = {}
        for x, y, ip, ie in zip( self.X, self.Y, self.CopyPhiIndex, self.CopyEtaIndex ):
            tiles.setdefault( (ip, ie), [] ).append( (x, y) )
        width = {}
        for k, pts in tiles.items():
            xc = sum(p[0] for p in pts) / len(pts); yc = sum(p[1] for p in pts) / len(pts)
            rc = math.hypot(xc, yc); phic = math.atan2(yc, xc)
            etas = [ math.asinh( self.Z / math.hypot(x, y) ) for x, y in pts ]
            phis = [ math.remainder( math.atan2(y, x) - phic, 2 * math.pi ) for x, y in pts ]
            deta_step = spacing * abs(self.Z) / ( rc * math.hypot(rc, self.Z) )
            dphi_step = spacing / rc
            width[k] = ( max(etas) - min(etas) + deta_step, max(phis) - min(phis) + dphi_step )
        return [ width[(ip, ie)] for ip, ie in zip( self.CopyPhiIndex, self.CopyEtaIndex ) ]
    # Cells of the digitization (CaloCellMaker): one per tile, with the local hash of the hits (bin = 16 eta + phi), the centre and
    # the width of the tile
    @property
    def Tiles( self ):
        out = {}
        for ip, ie, eta, phi, w in zip( self.CopyPhiIndex, self.CopyEtaIndex, self.CopyEta, self.CopyPhi, self._tileWidths() ):
            out.setdefault( 16 * ie + ip, ( eta, phi, w[0], w[1] ) )
        bins = sorted( out )
        return { "Bin": bins, "Eta": [out[b][0] for b in bins], "Phi": [out[b][1] for b in bins],
                 "DeltaEta": [out[b][2] for b in bins], "DeltaPhi": [out[b][3] for b in bins] }
    @property
    def CopyDeltaEta( self ): return [ w[0] for w in self._tileWidths() ]
    @property
    def CopyDeltaPhi( self ): return [ w[1] for w in self._tileWidths() ]

    # interface of a sampling, for CaloHitMaker.py and CaloHitBuilder.py
    def volume( self ):    return self
    def sensitive( self ): return self
    def name( self ):      return self.Name.replace('::', '_')
    Segment = 0
    BunchIdStart = -21
    BunchIdEnd = 3
    # The front end of the digitization: there is no public pulse of the ATLAS FCal, so the module takes the generic LAr pulse of
    # Lorenzetti and the noise and optimal filter weights of HEC1 (geometry/python/v2/HEC.py), as HEC0 does. Not validated.
    StartSamplingBC = -2
    Samples = 5
    DigitNoise = 250*MeV
    OFWeightsEnergy = [-0.0000853580,    0.265132,    0.594162,     0.389505,     0.124353]
    OFWeightsTime   = [-0.0000853580,   -12.870312690734863, -27.39136505126953, 8.075883865356445, 13.768877029418945]
    @property
    def Shaper( self ): return os.environ['LORENZETTI_GEOMETRY_DATA_DIR'] + "/pulseLar.dat"
    # the simulation keeps no noise in the time of flight selection of the hits (CaloHitMaker SamplingNoiseStd)
    Noise = 0
    # for CaloCellMaker.py: the z of the module
    @property
    def sv( self ): return self
    @property
    def pv( self ): return self
    BirksLArK = FCAL_BIRKS_K
    @property
    def EtaBins( self ):
        lo, hi = sorted( (min(self.CopyEta), max(self.CopyEta)) )
        return [lo - 0.01, hi + 0.01]
    PhiBins = [-math.pi, math.pi]
    @property
    def GapVolume( self ): return self.Name + "::Gap"


def getAtlasFcalCellsCfg( electrodes_file ):
    """The six modules of the ATLAS FCal (three per side), with the electrodes of electrodes_file (readAtlasFcalElectrodes)."""
    electrodes = readAtlasFcalElectrodes( electrodes_file )
    return [ AtlasFcalModule( m, side, electrodes[m['module']] ) for side in (+1, -1) for m in ATLAS_FCAL_CELL_MODULES ]
