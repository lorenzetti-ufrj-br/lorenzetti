#include "src/TileDualReadoutSplitTool.h"
#include "src/TileUShape.h"
#include "G4Step.hh"
#include <cmath>
#include <algorithm>

TileDualReadoutSplitTool::TileDualReadoutSplitTool( std::string name )
  : IMsgService(name), ICaloEnergyModifierTool(name)
{
  declareProperty( "TileDualReadout", m_tileDualReadout = 1 );
  declareProperty( "Sampling"       , m_sampling = 0 );
  declareProperty( "PhiBins"        , m_phiBins );
  declareProperty( "UShapePart"     , m_uShapePart = -1 );
  declareProperty( "UShapeLayer"    , m_uShapeLayer = -1 );
}

float TileDualReadoutSplitTool::modifyEnergy( const G4Step *step, CellIdentification &cell, float currentEnergy ) const
{
  if( !step || !cell.hasDualReadout || m_tileDualReadout <= 0 ) return currentEnergy;

  const int npmt = cell.tileNPmt;
  float w0 = 1.0f, w1 = 0.0f;

  if( npmt == 2 || npmt == 0 ){
    G4ThreeVector pos = step->GetPreStepPoint()->GetPosition();
    float phiLocal = std::remainder( pos.phi() - cell.phi, 2 * M_PI );
    tilePmtWeights( phiLocal, (float)pos.z(), w0, w1, npmt == 0 );
  } else if( npmt == 1 ){
    w0 = 1.0f; w1 = 0.0f;
  } else {
    w0 = 0.0f; w1 = 1.0f;
  }

  cell.pmtWeight0 = w0;
  cell.pmtWeight1 = w1;

  return currentEnergy;
}

void TileDualReadoutSplitTool::tilePmtWeights( float phiLocal, float z, float &w0, float &w1, bool replaced ) const
{
  if( m_tileDualReadout == 1 ){
    int layer = (m_sampling - 5) % 3;
    int part  = (m_sampling <= 7) ? 0 : ( z > 0 ? 1 : 2 ); // LB, EBA (z > 0), EBC (z < 0)
    if( replaced ){ part = ( z > 0 ? 1 : 2 ); layer = 2; }
    else if( m_uShapePart >= 0 ){ part = m_uShapePart; layer = m_uShapeLayer; }
    const double *t = TileUShape::table( part, layer );
    w1 = (float)TileUShape::amplitude( t, -phiLocal );
    w0 = (float)TileUShape::amplitude( t,  phiLocal );
    return;
  }
  const float halfDeltaPhi = m_phiBins.size() > 1 ? std::abs( m_phiBins[1] - m_phiBins[0] ) / 2 : 0.049f;
  float u = std::tan( phiLocal ) / std::tan( halfDeltaPhi );
  u = std::max( -1.f, std::min( 1.f, u ) );
  w1 = 0.5f + 0.2f * u;
  w0 = 1.0f - w1;
}
