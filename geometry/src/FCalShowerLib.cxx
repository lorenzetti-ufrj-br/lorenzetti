/*
  Copyright (C) 2002-2020 CERN for the benefit of the ATLAS collaboration
*/
#include "FCalShowerLib.h"

#include "G4Track.hh"
#include "G4ParticleDefinition.hh"
#include "TFile.h"
#include "TTree.h"
#include "TParameter.h"
#include <cmath>
#include <memory>
#include <stdexcept>

// See FCalShowerLib.h. Line references are to FCALDistEtaEnergyShowerLib.cxx of the Athena release 23.0.14.

FCalShowerLib::FCalShowerLib( const std::string &fileName )
{
  std::unique_ptr<TFile> f( TFile::Open( fileName.c_str(), "READ" ) );
  if( !f || f->IsZombie() ) throw std::runtime_error( "FCalShowerLib: cannot open " + fileName );
  auto *ver = (TParameter<int>*) f->Get( "version" );
  if( !ver || ( ver->GetVal() != 5 && ver->GetVal() != 3 ) ) throw std::runtime_error( "FCalShowerLib: not an FCal library version 5 or 3: " + fileName );
  const bool compat = ver->GetVal() == 3;
  auto *meta = (TTree*) f->Get( "meta" );
  auto *lib  = (TTree*) f->Get( "library" );
  if( !meta || !lib ) throw std::runtime_error( "FCalShowerLib: no meta or library tree in " + fileName );

  // meta: detector name and particle (IShowerLib::readMeta)
  char detector[256] = {0};
  Int_t particle = 0;
  meta->SetBranchAddress( "detector", detector );
  meta->SetBranchAddress( "particle", &particle );
  meta->GetEntry( 0 );
  m_detector = detector;
  m_particle = particle;
  meta->ResetBranchAddresses();

  // library (read, :615-695)
  const Long64_t nentr = lib->GetEntriesFast();
  if( nentr < 3 ) throw std::runtime_error( "FCalShowerLib: empty library in " + fileName );
  Float_t x, y, z, e, time;
  lib->SetBranchAddress( "x", &x );
  lib->SetBranchAddress( "y", &y );
  lib->SetBranchAddress( "z", &z );
  lib->SetBranchAddress( "e", &e );
  lib->SetBranchAddress( "time", &time );
  Long64_t entr = 0;
  if( !compat ){
    lib->GetEntry( entr++ );
    m_xrodcent = x; m_yrodcent = y; m_step = z;
  }else{
    m_xrodcent = -748.12; m_yrodcent = -717.719; m_step = 7.5;
  }
  do {
    lib->GetEntry( entr++ );
    const int ndists = (int)( x + 0.1 );
    etabin &curetabin = m_libData[y];
    for( int i = 0; i < ndists; ++i ){
      lib->GetEntry( entr++ );
      const int nsh = (int)( x + 0.1 );
      distbin &curbin = curetabin[y];
      for( int j = 0; j < nsh; ++j ){
        lib->GetEntry( entr++ );
        const int nhits = (int)( x + 0.1 );
        Shower &shower = curbin[e];          // as Athena: a repeated energy adds its spots to the same shower
        shower.rSize = y; shower.zSize = z;
        for( int k = 0; k < nhits; ++k ){
          lib->GetEntry( entr++ );
          shower.spots.push_back( Spot{ G4ThreeVector( x, y, z ), e, time } );
        }
      }
    }
  } while( entr < nentr );
  lib->ResetBranchAddresses();
  if( entr != nentr ) throw std::runtime_error( "FCalShowerLib: inconsistent library " + fileName );
}

// distance of (x, y) to the nearest rod of the ideal hexagonal grid of the library (:39-54)
float FCalShowerLib::distance( double x, double y ) const
{
  const double stepy = m_step * std::sqrt(3.) / 2.;
  const double dy = std::fmod( y - m_yrodcent, stepy );
  const int ny = int( ( y - m_yrodcent ) / stepy );
  const double dx0 = ( ny % 2 ) * m_step / 2.;
  const double dx = std::fmod( x - m_xrodcent - dx0, m_step );
  const double d1 = std::sqrt( dx*dx + dy*dy );
  const double d2 = std::sqrt( (m_step-dx)*(m_step-dx) + dy*dy );
  const double d3 = std::sqrt( (m_step/2.-dx)*(m_step/2.-dx) + (stepy-dy)*(stepy-dy) );
  float dd = d1;
  if( dd > d2 ) dd = d2;
  if( dd > d3 ) dd = d3;
  return dd;
}

// the bins of the track and the shower of nearest kinetic energy (:256-312)
bool FCalShowerLib::find( const G4Track *track, const distbin *&bin, distbin::const_iterator &nearest ) const
{
  const double x = track->GetPosition().getX(), y = track->GetPosition().getY();
  const float dist = distance( x, y );
  double eta = track->GetPosition().eta();
  if( eta < 0 ) eta = -eta;
  int particleCode = track->GetDefinition()->GetPDGEncoding();
  if( particleCode < 0 ) particleCode = -particleCode;
  if( particleCode != m_particle || eta < 3.0 ) return false;
  auto libit = m_libData.upper_bound( eta );
  if( libit != m_libData.begin() ) --libit;
  auto etait = libit->second.upper_bound( dist );
  if( etait != libit->second.begin() ) --etait;
  if( etait->second.empty() ) return false;
  const double trenergy = track->GetKineticEnergy();
  auto distit = etait->second.lower_bound( trenergy );
  if( distit == etait->second.end() ) --distit;
  else if( distit != etait->second.begin() ){
    auto distitch = distit; --distitch;
    if( ( distit->first - trenergy ) > ( trenergy - distitch->first ) ) --distit;
  }
  bin = &etait->second;
  nearest = distit;
  return true;
}

// getShower (:247-357): the random shift within 1% and the energy scale
bool FCalShowerLib::getShower( const G4Track *track, int randomShift, std::vector<Spot> &out ) const
{
  out.clear();
  const distbin *bin = nullptr;
  distbin::const_iterator distit;
  if( !find( track, bin, distit ) ) return false;
  if( randomShift > 0 ){
    const double upperEnergy = distit->first * 1.01;
    for( int i = 0; i < randomShift; ++i ){
      ++distit;
      if( distit == bin->end() ){ --distit; break; }
      if( distit->first > upperEnergy ) break;
    }
  }
  if( randomShift < 0 && distit != bin->begin() ){
    const double lowerEnergy = distit->first * 0.99;
    for( int i = 0; i > randomShift; --i ){
      --distit;
      if( distit == bin->begin() ) break;
      if( lowerEnergy > distit->first ) break;
    }
  }
  const float energyScale = track->GetKineticEnergy() / distit->first;
  out.reserve( distit->second.spots.size() );
  for( const auto &s : distit->second.spots ){
    // EnergySpot keeps float energy and time (ShowerEnergySpot, EnergySpot): the scaled energy as in Athena
    out.push_back( Spot{ s.position, (float)( (float)s.energy * energyScale ), s.time } );
  }
  return true;
}

// getContainmentZ, getContainmentR (:359-549): mean size of the nearest shower and up to two on each side within 1%
double FCalShowerLib::containment( const G4Track *track, bool zSize ) const
{
  const distbin *bin = nullptr;
  distbin::const_iterator distit;
  if( !find( track, bin, distit ) ) return 0;
  auto size = [zSize]( const Shower &s ){ return zSize ? s.zSize : s.rSize; };
  double rez = size( distit->second );
  int actualNumFS = 1;
  const int spread = 2;
  const double upperEnergy = distit->first * 1.01;
  auto distiter = distit;
  for( int i = 0; i < spread; ++i ){
    ++distiter;
    if( distiter == bin->end() ) break;
    if( upperEnergy < distiter->first ) break;
    rez += size( distiter->second ); actualNumFS++;
  }
  distiter = distit;
  if( distiter != bin->begin() ){
    const double lowerEnergy = distit->first * 0.99;
    for( int i = 0; i < spread; ++i ){
      --distiter;
      if( lowerEnergy > distiter->first ) break;
      rez += size( distiter->second ); actualNumFS++;
      if( distiter == bin->begin() ) break;
    }
  }
  return rez / actualNumFS;
}

double FCalShowerLib::getContainmentZ( const G4Track *track ) const { return containment( track, true  ); }
double FCalShowerLib::getContainmentR( const G4Track *track ) const { return containment( track, false ); }
