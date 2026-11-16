/*
  Copyright (C) 2002-2021 CERN for the benefit of the ATLAS collaboration
*/
// Ported to Lorenzetti from Athena release 23.0.14 (MagneticField/MagFieldElements) for --atlas-run4 (F41 conserto 27); changes: removed the unused include PathResolver/PathResolver.h (and its comment line).

///////////////////////////////////////////////////////////////////
// AtlasMTFieldSvc.cxx, (c) ATLAS Detector software
///////////////////////////////////////////////////////////////////

// ISF_Services include
#include "MagFieldElements/AtlasFieldMap.h"


// ROOT
#include "TFile.h"
#include "TTree.h"



//
// read the map from a ROOT file.
// returns 0 if successful.
//
bool
MagField::AtlasFieldMap::initializeMap(TFile* rootfile,
                                       float solenoidCurrent,
                                       float toroidCurrent)
{
  // save currents
  m_solenoidCurrent = solenoidCurrent;
  m_toroidCurrent = toroidCurrent;

  // open the tree
  TTree* tree = (TTree*)rootfile->Get("BFieldMap");
  // if ( tree == 0 ) {
  //     // no tree
  //     ATH_MSG_ERROR("readMap(): TTree 'BFieldMap' does not exist in ROOT
  //     field map"); return StatusCode::FAILURE;
  // }
  int id;
  double zmin;
  double zmax;
  double rmin;
  double rmax;
  double phimin;
  double phimax;
  double bscale;
  int ncond;
  bool* finite;
  double* p1x;
  double* p1y;
  double* p1z;
  double* p2x;
  double* p2y;
  double* p2z;
  double* curr;
  int nmeshz;
  int nmeshr;
  int nmeshphi;
  double* meshz;
  double* meshr;
  double* meshphi;
  int nfield;
  short* fieldz;
  short* fieldr;
  short* fieldphi;
  // define the fixed-sized branches first
  tree->SetBranchAddress("id", &id);
  tree->SetBranchAddress("zmin", &zmin);
  tree->SetBranchAddress("zmax", &zmax);
  tree->SetBranchAddress("rmin", &rmin);
  tree->SetBranchAddress("rmax", &rmax);
  tree->SetBranchAddress("phimin", &phimin);
  tree->SetBranchAddress("phimax", &phimax);
  tree->SetBranchAddress("bscale", &bscale);
  tree->SetBranchAddress("ncond", &ncond);
  tree->SetBranchAddress("nmeshz", &nmeshz);
  tree->SetBranchAddress("nmeshr", &nmeshr);
  tree->SetBranchAddress("nmeshphi", &nmeshphi);
  tree->SetBranchAddress("nfield", &nfield);
  // prepare arrays - need to know the maximum sizes
  // open the tree of buffer sizes (may not exist in old maps)
  unsigned maxcond(0);

  unsigned maxmeshz(0);

  unsigned maxmeshr(0);

  unsigned maxmeshphi(0);

  unsigned maxfield(0);
  TTree* tmax = (TTree*)rootfile->Get("BFieldMapSize");
  if (tmax != nullptr) {
    tmax->SetBranchAddress("maxcond", &maxcond);
    tmax->SetBranchAddress("maxmeshz", &maxmeshz);
    tmax->SetBranchAddress("maxmeshr", &maxmeshr);
    tmax->SetBranchAddress("maxmeshphi", &maxmeshphi);
    tmax->SetBranchAddress("maxfield", &maxfield);
    tmax->GetEntry(0);
  } else { // "BFieldMapSize" tree does not exist
    for (int i = 0; i < tree->GetEntries(); i++) {
      tree->GetEntry(i);
      maxcond = std::max(maxcond, (unsigned)ncond);
      maxmeshz = std::max(maxmeshz, (unsigned)nmeshz);
      maxmeshr = std::max(maxmeshr, (unsigned)nmeshr);
      maxmeshphi = std::max(maxmeshphi, (unsigned)nmeshphi);
      maxfield = std::max(maxfield, (unsigned)nfield);
    }
  }
  finite = new bool[maxcond];
  p1x = new double[maxcond];
  p1y = new double[maxcond];
  p1z = new double[maxcond];
  p2x = new double[maxcond];
  p2y = new double[maxcond];
  p2z = new double[maxcond];
  curr = new double[maxcond];
  meshz = new double[maxmeshz];
  meshr = new double[maxmeshr];
  meshphi = new double[maxmeshphi];
  fieldz = new short[maxfield];
  fieldr = new short[maxfield];
  fieldphi = new short[maxfield];
  // define the variable length branches
  tree->SetBranchAddress("finite", finite);
  tree->SetBranchAddress("p1x", p1x);
  tree->SetBranchAddress("p1y", p1y);
  tree->SetBranchAddress("p1z", p1z);
  tree->SetBranchAddress("p2x", p2x);
  tree->SetBranchAddress("p2y", p2y);
  tree->SetBranchAddress("p2z", p2z);
  tree->SetBranchAddress("curr", curr);
  tree->SetBranchAddress("meshz", meshz);
  tree->SetBranchAddress("meshr", meshr);
  tree->SetBranchAddress("meshphi", meshphi);
  tree->SetBranchAddress("fieldz", fieldz);
  tree->SetBranchAddress("fieldr", fieldr);
  tree->SetBranchAddress("fieldphi", fieldphi);

  // reserve the space for m_zone so that it won't move as the vector grows
  m_zone.reserve(tree->GetEntries());
  // read all tree and store
  for (int i = 0; i < tree->GetEntries(); i++) {
    tree->GetEntry(i);
    BFieldZone z(id, zmin, zmax, rmin, rmax, phimin, phimax, bscale);
    m_zone.push_back(z);
    m_zone.back().reserve(nmeshz, nmeshr, nmeshphi);
    for (int j = 0; j < ncond; j++) {
      double p1[3];

      double p2[3];
      p1[0] = p1x[j];
      p1[1] = p1y[j];
      p1[2] = p1z[j];
      p2[0] = p2x[j];
      p2[1] = p2y[j];
      p2[2] = p2z[j];
      BFieldCond cond(finite[j], p1, p2, curr[j]);
      m_zone.back().appendCond(cond);
    }
    for (int j = 0; j < nmeshz; j++) {
      m_zone.back().appendMesh(0, meshz[j]);
    }
    for (int j = 0; j < nmeshr; j++) {
      m_zone.back().appendMesh(1, meshr[j]);
    }
    for (int j = 0; j < nmeshphi; j++) {
      m_zone.back().appendMesh(2, meshphi[j]);
    }
    for (int j = 0; j < nfield; j++) {
      BFieldVector<short> field(fieldz[j], fieldr[j], fieldphi[j]);
      m_zone.back().appendField(field);
    }
  }
  // clean up
  tree->Delete();
  delete[] finite;
  delete[] p1x;
  delete[] p1y;
  delete[] p1z;
  delete[] p2x;
  delete[] p2y;
  delete[] p2z;
  delete[] curr;
  delete[] meshz;
  delete[] meshr;
  delete[] meshphi;
  delete[] fieldz;
  delete[] fieldr;
  delete[] fieldphi;
  // build the LUTs
  buildLUT();
  buildZR();

  // setup id for solenoid bfield zone
  BFieldZone* solezone = findZoneSlow(0.0, 0.0, 0.0);
  if (solezone) {
    m_solenoidZoneId = solezone->id();
  }

  return true;
}

//
// Search for the zone that contains a point (z, r, phi)
// This is a linear-search version, used only to construct the LUT.
//
BFieldZone*
MagField::AtlasFieldMap::findZoneSlow(double z, double r, double phi)
{
  for (int j = m_zone.size() - 1; j >= 0; --j) {
    if (m_zone[j].inside(z, r, phi)) {
      return &m_zone[j];
    }
  }
  return nullptr;
}

//
// Build the look-up table used by FindZone().
// Called by readMap()
// It also calls buildLUT() for all zones.
//
void
MagField::AtlasFieldMap::buildLUT()
{

  // make lists of (z,r,phi) edges of all zones
  for (int j = 0; j < 3; j++) { // z, r, phi
    for (unsigned i = 0; i < m_zone.size(); i++) {
      double e[2];
      e[0] = m_zone[i].min(j);
      e[1] = m_zone[i].max(j);
      for (int k = 0; k < 2; k++) {
        // for the phi edge, fit into [-pi,pi]
        if (j == 2 && e[k] > M_PI) {
          e[k] -= 2.0 * M_PI;
        }
        m_edge[j].push_back(e[k]);
      }
    }
    // add -pi and +pi to phi, just in case
    m_edge[2].push_back(-M_PI);
    m_edge[2].push_back(M_PI);
    // sort
    sort(m_edge[j].begin(), m_edge[j].end());
    // remove duplicates
    // must do this by hand to allow small differences due to rounding in phi
    int i = 0;
    for (unsigned k = 1; k < m_edge[j].size(); k++) {
      if (fabs(m_edge[j][i] - m_edge[j][k]) < 1.0e-6) {
        continue;
      }
      m_edge[j][++i] = m_edge[j][k];
    }
    m_edge[j].resize(i + 1);
    // because of the small differences allowed in the comparison above,
    // m_edge[][] values do not exactly match the m_zone[] boundaries.
    // we have to fix this up in order to avoid invalid field values
    // very close to the zone boundaries.
    for (unsigned i = 0; i < m_zone.size(); i++) {
      for (unsigned k = 0; k < m_edge[j].size(); k++) {
        if (fabs(m_zone[i].min(j) - m_edge[j][k]) < 1.0e-6) {
          m_zone[i].adjustMin(j, m_edge[j][k]);
        }
        if (fabs(m_zone[i].max(j) - m_edge[j][k]) < 1.0e-6) {
          m_zone[i].adjustMax(j, m_edge[j][k]);
        }
      }
    }
  }
  // build LUT for edge finding
  for (int j = 0; j < 3; j++) { // z, r, phi
    // find the size of the smallest interval
    double width = m_edge[j].back() - m_edge[j].front();
    double q(width);
    for (unsigned i = 0; i < m_edge[j].size() - 1; i++) {
      q = std::min(q, m_edge[j][i + 1] - m_edge[j][i]);
    }
    // find the number of cells in the LUT
    int n = int(width / q) + 1;
    q = width / (n + 0.5);
    m_invq[j] = 1.0 / q;
    n++;
    // fill the LUT
    int m = 0;
    for (int i = 0; i < n; i++) { // index of LUT
      if (q * i + m_edge[j].front() > m_edge[j][m + 1]) {
        m++;
      }
      m_edgeLUT[j].push_back(m);
    }
  }
  // store min/max for speedup
  m_zmin = m_edge[0].front();
  m_zmax = m_edge[0].back();
  m_rmax = m_edge[1].back();
  // build LUT for zone finding
  m_nz = m_edge[0].size() - 1;
  m_nr = m_edge[1].size() - 1;
  m_nphi = m_edge[2].size() - 1;
  m_zoneLUT.reserve(m_nz * m_nr * m_nphi);
  for (int iz = 0; iz < m_nz; iz++) {
    double z = 0.5 * (m_edge[0][iz] + m_edge[0][iz + 1]);
    for (int ir = 0; ir < m_nr; ir++) {
      double r = 0.5 * (m_edge[1][ir] + m_edge[1][ir + 1]);
      for (int iphi = 0; iphi < m_nphi; iphi++) {
        double phi = 0.5 * (m_edge[2][iphi] + m_edge[2][iphi + 1]);
        const BFieldZone* zone = findZoneSlow(z, r, phi);
        m_zoneLUT.push_back(zone);
      }
    }
  }
  // build LUT in each zone
  for (unsigned i = 0; i < m_zone.size(); i++) {
    m_zone[i].buildLUT();
  }
}

//
// Build the z-r 2d map for fast solenoid field
//
void
MagField::AtlasFieldMap::buildZR()
{
  // delete if previously allocated
  delete m_meshZR;

  // find the solenoid zone
  // solenoid zone always covers 100 < R < 1000, but not necessarily R < 100
  // so we search for the zone that contains a point at R = 200, Z = 0
  const BFieldZone* solezone = findBFieldZone(0.0, 200.0, 0.0);

  // instantiate the new ZR map with the same external coverage as the solenoid
  // zone make sure R = 0 is covered
  m_meshZR =
    new BFieldMeshZR(solezone->zmin(), solezone->zmax(), 0.0, solezone->rmax());

  // reserve the right amount of memroy
  unsigned nmeshz = solezone->nmesh(0);
  unsigned nmeshr = solezone->nmesh(1);
  if (solezone->rmin() > 0.0) {
    nmeshr++;
  }
  m_meshZR->reserve(nmeshz, nmeshr);

  // copy the mesh structure in z/r
  // take care of R = 0 first
  if (solezone->rmin() > 0.0) {
    m_meshZR->appendMesh(1, 0.0);
  }
  // copy the rest
  for (int i = 0; i < 2; i++) {                         // z, r
    for (unsigned j = 0; j < solezone->nmesh(i); j++) { // loop over mesh points
      m_meshZR->appendMesh(i, solezone->mesh(i, j));
    }
  }

  // loop through the mesh and compute the phi-averaged field
  for (unsigned iz = 0; iz < m_meshZR->nmesh(0); iz++) { // loop over z
    double z = m_meshZR->mesh(0, iz);
    for (unsigned ir = 0; ir < m_meshZR->nmesh(1); ir++) { // loop over r
      double r = m_meshZR->mesh(1, ir);
      const int nphi(200); // number of phi slices to average
      double Br = 0.0;
      double Bz = 0.0;
      for (int iphi = 0; iphi < nphi; iphi++) {
        double phi = double(iphi) / double(nphi) * 2. * M_PI;
        double xyz[3];
        xyz[0] = r * cos(phi);
        xyz[1] = r * sin(phi);
        xyz[2] = z;
        double B[3];
        solezone->getB(xyz, B, nullptr);
        Br += B[0] * cos(phi) + B[1] * sin(phi);
        Bz += B[2];
      }
      Br *= 1.0 / double(nphi);
      Bz *= 1.0 / double(nphi);
      m_meshZR->appendField(BFieldVectorZR(Bz, Br));
    }
  }

  // build the internal LUT
  m_meshZR->buildLUT();
}

//
// Approximate memory footprint
//
int
MagField::AtlasFieldMap::memSize() const
{
  int size = 0;
  size += sizeof(BFieldCache);
  size += sizeof(BFieldCacheZR);
  for (unsigned i = 0; i < m_zone.size(); i++) {
    size += m_zone[i].memSize();
  }
  for (int i = 0; i < 3; i++) {
    size += sizeof(double) * m_edge[i].capacity();
    size += sizeof(int) * m_edgeLUT[i].capacity();
  }
  size += sizeof(BFieldZone*) * m_zoneLUT.capacity();
  if (m_meshZR) {
    size += m_meshZR->memSize();
  }
  return size;
}
