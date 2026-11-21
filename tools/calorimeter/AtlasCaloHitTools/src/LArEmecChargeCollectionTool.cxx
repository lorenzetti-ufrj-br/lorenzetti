#include "src/LArEmecChargeCollectionTool.h"
#include "GeoV2/EnergyCalculator.h"
#include "GeoV2/EMECDataCSV.h"
#include "GeoV2/LArWheelCalculator.h"
#include "G4Step.hh"
#include "G4AffineTransform.hh"
#include "G4RotationMatrix.hh"
#include "CLHEP/Units/SystemOfUnits.h"
#include "CLHEP/Vector/RotationInterfaces.h"
#include <mutex>
#include <map>
#include <cmath>
#include <atomic>

using namespace CLHEP;

static std::mutex s_emecDiscardMutex;
static long s_emecSteps[2] = {0, 0};
static double s_emecEnergy[2] = {0., 0.};
static long s_emecDiscardedSteps[2] = {0, 0};
static double s_emecDiscardedEnergy[2] = {0., 0.};
static bool s_emecDiscardPrinted = false;

static constexpr bool kEmecShiftEndpointsIndependently = false;

static G4AffineTransform emecTopTransform( bool sideA )
{
  G4AffineTransform world;
  if( sideA ){
    G4AffineTransform cryostat, emecHecLAr, emecMother, wheel;
    cryostat.InverseProduct( world, G4AffineTransform( G4ThreeVector( 0., 0., 6734.5 ) ) );
    emecHecLAr.InverseProduct( cryostat, G4AffineTransform() );
    emecMother.InverseProduct( emecHecLAr, G4AffineTransform() );
    wheel.InverseProduct( emecMother, G4AffineTransform( G4ThreeVector( 0., 0., -6690. + 3700.5 ) ) );
    return wheel;
  }
  const double angle = 180.0 * CLHEP::deg;
  const double c = std::cos( angle ), s = std::sin( angle );
  const double cos1y = 1. - c;
  const CLHEP::HepRep3x3 rep( 0. * 0. + c,         0. * 1. - s * 0.,   0. * 0. + s * 1.,
                              0. * 1. + s * 0.,    cos1y * 1. + c,     cos1y * 0. - s * 0.,
                              0. * 0. - s * 1.,    cos1y * 0. + s * 0., 0. * 0. + c );
  const G4RotationMatrix placement( rep );
  const G4RotationMatrix frot = placement.inverse();
  G4AffineTransform cryostat;
  cryostat.InverseProduct( world, G4AffineTransform( &frot, G4ThreeVector( 0., 0., -6734.5 ) ) );
  G4AffineTransform emecHecLAr, emecMother, wheel;
  emecHecLAr.InverseProduct( cryostat, G4AffineTransform() );
  emecMother.InverseProduct( emecHecLAr, G4AffineTransform() );
  wheel.InverseProduct( emecMother, G4AffineTransform( G4ThreeVector( 0., 0., -6690. + 3700.5 ) ) );
  return wheel;
}

LArEmecChargeCollectionTool::LArEmecChargeCollectionTool( std::string name )
  : IMsgService(name), ICaloEnergyModifierTool(name)
{
  declareProperty( "EmecChargeCollection", m_emecChargeCollection = true );
  declareProperty( "EmecChargeTables"    , m_emecChargeTables = "" );
  declareProperty( "EmecChargeFieldMap"  , m_emecChargeFieldMap = "" );
  declareProperty( "EmecChargeHVMap"     , m_emecChargeHVMap = "" );
  declareProperty( "EmecCompartment"     , m_emecCompartment = 0 );
  declareProperty( "EmecFocalShift"      , m_emecFocalShift = 0.0f );
  declareProperty( "ZMin"                , m_zMin = 0.0f );
  declareProperty( "ZMax"                , m_zMax = 0.0f );
}

StatusCode LArEmecChargeCollectionTool::initialize()
{
  if( !m_emecChargeCollection || m_emecCompartment <= 0 ) return StatusCode::SUCCESS;

  const bool inner = ( m_emecCompartment <= 2 );
  const int zside = ( m_zMin + m_zMax > 0 ) ? 1 : -1;
  static std::mutex mutex;
  static std::map<std::tuple<bool, int, std::string, std::string, std::string>,
                  std::unique_ptr<const LArG4::EC::EnergyCalculator>> calculators;
  std::lock_guard<std::mutex> lock( mutex );
  auto key = std::make_tuple( inner, zside, m_emecChargeTables, m_emecChargeFieldMap, m_emecChargeHVMap );
  auto it = calculators.find( key );
  if( it == calculators.end() ){
    const EMECData data = readEMECDataCSV( m_emecChargeTables );
    it = calculators.emplace( key, std::make_unique<const LArG4::EC::EnergyCalculator>( data,
             inner ? LArG4::InnerAbsorberWheel : LArG4::OuterAbsorberWheel, zside, m_emecChargeFieldMap, m_emecChargeHVMap ) ).first;
  }
  m_emecCalculator = it->second.get();
  return StatusCode::SUCCESS;
}

StatusCode LArEmecChargeCollectionTool::finalize()
{
  if( m_emecCalculator ){
    std::lock_guard<std::mutex> lock( s_emecDiscardMutex );
    if( !s_emecDiscardPrinted ){
      s_emecDiscardPrinted = true;
      for( int w = 0; w < 2; ++w )
        MSG_INFO( "EMEC charge collection, " << ( w ? "inner" : "outer" ) << " wheel: " << s_emecSteps[w] << " steps, "
                  << s_emecEnergy[w] << " MeV before the correction; discarded (HV eta range): " << s_emecDiscardedSteps[w]
                  << " steps, " << s_emecDiscardedEnergy[w] << " MeV" );
    }
  }
  return StatusCode::SUCCESS;
}

float LArEmecChargeCollectionTool::modifyEnergy( const G4Step *step, CellIdentification &, float currentEnergy ) const
{
  if( !step || !m_emecCalculator ) return currentEnergy;
  double energy = 0.0;
  const bool kept = emecChargeEnergy( step, energy );
  emecDiscardCount( m_emecCompartment <= 2, currentEnergy, !kept );
  if( kept ) return (float)energy;
  return 0.0f;
}

void LArEmecChargeCollectionTool::emecDiscardCount( bool inner, double energyBefore, bool discarded ) const
{
  std::lock_guard<std::mutex> lock( s_emecDiscardMutex );
  const int w = inner ? 1 : 0;
  ++s_emecSteps[w]; s_emecEnergy[w] += energyBefore;
  if( discarded ){ ++s_emecDiscardedSteps[w]; s_emecDiscardedEnergy[w] += energyBefore; }
}

bool LArEmecChargeCollectionTool::emecChargeEnergy( const G4Step *step, double &energy ) const
{
  const LArG4::EC::EnergyCalculator *calc = m_emecCalculator;
  const bool sideA = ( m_zMin + m_zMax > 0 );
  static const G4AffineTransform topA = emecTopTransform( true ), topB = emecTopTransform( false );
  const G4AffineTransform &top = sideA ? topA : topB;
  auto toLocal = [&]( const G4ThreeVector &g ){ return top.TransformPoint( g ); };
  G4ThreeVector p1 = toLocal( step->GetPreStepPoint()->GetPosition() );
  G4ThreeVector p2 = toLocal( step->GetPostStepPoint()->GetPosition() );
  if( kEmecShiftEndpointsIndependently ){
    p1.rotateZ( emecLArPhiShift( p1 ) );
    p2.rotateZ( emecLArPhiShift( p2 ) );
  }else{
    const double dphi = emecLArPhiShift( ( p1 + p2 ) * 0.5 );
    p1.rotateZ( dphi );
    p2.rotateZ( dphi );
  }
  G4double E = step->GetTotalEnergyDeposit() * ( step->GetTrack() ? step->GetTrack()->GetWeight() : 1. );
  try{
    const G4ThreeVector midpoint = ( p1 + p2 ) * 0.5;
    const G4double wholeStepLengthCm = step->GetStepLength() / cm;
    const G4double gap = calc->GapSize( midpoint );
    const G4double efield = 0.01 * calc->Voltage( midpoint ) / gap;
    E = calc->Birks( E, wholeStepLengthCm, efield );
    energy = calc->ChargeCollection( E, p1, p2 );
    return true;
  }catch( const std::exception &e ){
    static std::atomic<long> nExceptions{0};
    const long n = ++nExceptions;
    if( n <= 10 || ( n & (n - 1) ) == 0 )
      MSG_WARNING( "EMEC charge collection: " << e.what() << " for the step at local (" << p1.x() << ", " << p1.y() << ", "
                   << p1.z() << "); deposit discarded (" << n << " so far)" );
    return false;
  }
}

double LArEmecChargeCollectionTool::emecLArPhiShift( const CLHEP::Hep3Vector &p ) const
{
  const LArG4::EC::EnergyCalculator *calc = m_emecCalculator;
  const LArWheelCalculator *lwc = calc->calculator(), *elc = calc->electrodeCalculator();
  const double r = p.perp(), z = p.z(), phi = p.phi();
  const double step = lwc->GetFanStepOnPhi();
  const int nFans = lwc->GetNumberOfFans();
  auto at = [&]( double ph ){ return CLHEP::Hep3Vector( r * std::cos(ph), r * std::sin(ph), z ); };
  auto dist = [&]( const LArWheelCalculator *c, double theta, int fan, double ph ){
    CLHEP::Hep3Vector q = at( ph ); q.rotateZ( -theta ); return c->DistanceToTheNeutralFibre( q, fan ); };
  auto root = []( auto f, double lo, double hi ){
    double flo = f(lo), fhi = f(hi);
    if( flo == 0 ) return lo;
    if( fhi == 0 ) return hi;
    if( ( flo < 0 ) == ( fhi < 0 ) ) return std::nan("");
    for(;;){
      const double m = 0.5 * ( lo + hi );
      if( m <= lo || m >= hi ) return m;
      const double fm = f(m);
      if( fm == 0 ) return m;
      if( ( fm < 0 ) == ( flo < 0 ) ){ lo = m; flo = fm; } else { hi = m; }
    }
  };
  CLHEP::Hep3Vector pa = p; int fa = 0;
  const double da = lwc->DistanceToTheNearestFan( pa, fa );
  const double theta = phi - pa.phi();
  const double thLo = ( da >= 0 ) ? theta : theta - step, thHi = thLo + step;
  const int fanLo = ( da >= 0 ) ? fa : ( fa + nFans - 1 ) % nFans, fanHi = ( fanLo + 1 ) % nFans;
  const double hA = lwc->GetFanHalfThickness(), hE = elc->GetFanHalfThickness();
  const double phA0 = root( [&]( double x ){ return dist( lwc, thLo, fanLo, x ); }, phi - step, phi );
  const double phA1 = root( [&]( double x ){ return dist( lwc, thHi, fanHi, x ); }, phi, phi + step );
  const double phMid = 0.5 * ( phA0 + phA1 );
  CLHEP::Hep3Vector pe = at( phMid ); int fe = 0;
  elc->DistanceToTheNearestFan( pe, fe );
  const double thE = phMid - pe.phi();
  auto dE = [&]( double x ){ return dist( elc, thE, fe, x ); };
  const double phE = root( dE, phA0, phA1 );
  const double s1 = root( [&]( double x ){ return dist( lwc, thLo, fanLo, x ) - hA; }, phA0, phE );
  const double s2 = root( [&]( double x ){ return dE(x) + hE; }, phA0, phE );
  const double s3 = root( [&]( double x ){ return dE(x) - hE; }, phE, phA1 );
  const double s4 = root( [&]( double x ){ return dist( lwc, thHi, fanHi, x ) + hA; }, phE, phA1 );
  const double l1 = s2 - s1, l2 = s4 - s3;
  if( !( l1 > 0 && l2 > 0 && phA1 > phA0 ) ){
    static std::atomic<long> nFailures{0};
    const long n = ++nFailures;
    if( n <= 10 || ( n & (n - 1) ) == 0 )
      MSG_WARNING( "EMEC charge collection: no liquid argon found around the local point (" << p.x() << ", " << p.y() << ", "
                   << p.z() << "); not moved (" << n << " so far)" );
    return 0.;
  }
  const double f = ( phi - phA0 ) / ( phA1 - phA0 );
  const double t = f * ( l1 + l2 );
  const double phNew = ( t < l1 ) ? s1 + t : s3 + ( t - l1 );
  return phNew - phi;
}
