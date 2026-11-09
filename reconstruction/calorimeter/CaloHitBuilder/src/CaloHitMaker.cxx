

#include "CaloHit/CaloHit.h"
#include "CaloHit/CaloHitCollection.h"
#include "EventInfo/EventInfoContainer.h"
#include "CaloHitMaker.h"
#include "CaloFreeRunningHitList.h"
#include "TileUShape.h"
#include "EmbAtlasSampling.h"
#include <algorithm>

#include "G4Kernel/CaloPhiRange.h"
#include "G4Kernel/constants.h"
#include "TVector3.h"
#include "G4SystemOfUnits.hh"
#include "G4Step.hh"
#include "G4Material.hh"
#include "G4VPhysicalVolume.hh"
#include "G4LogicalVolume.hh"
#include <cmath>

#include "TH1F.h"
#include "TH2F.h"
#include "TH2Poly.h"
#include "TGraph.h"
#include <cstdlib>
#include <map>
#include <mutex>
#include <tuple>
#include <memory>
#include <atomic>
#include <stdexcept>

// the ported ATLAS charge collection of the EM end-cap (F41 conserto 29)
#include "LArG4EC/EnergyCalculator.h"
#include "LArG4EC/EMECDataCSV.h"
#include "G4AffineTransform.hh"
#include "G4RotationMatrix.hh"

// Deposits of the EMEC free-running hits with the charge collection, and those discarded because the HV helper of ATLAS throws
// (decision of Luciano of 15/10/2026: no ATLAS hit there), per wheel (0 outer, 1 inner): steps and energy before the correction (the
// energy of the hit without the option); printed at the end of the run by the first EMEC maker that finalizes.
static std::mutex s_emecDiscardMutex;
static long   s_emecSteps[2] = {0, 0}, s_emecDiscardedSteps[2] = {0, 0};
static double s_emecEnergy[2] = {0., 0.}, s_emecDiscardedEnergy[2] = {0., 0.};
static bool   s_emecDiscardPrinted = false;

using namespace Gaugi;
using namespace SG;




/**
 * @class CaloHitMaker
 * @brief Collects energy deposits (Hits) during Geant4 simulation.
 * 
 * This algorithm runs at every Geant4 step. It checks if the energy deposit
 * occurred within the defined volume (Sampling) and integrates the energy
 * into a CaloHit object. It maps geometric position (x,y,z) to readout 
 * identifiers (eta, phi bins).
 * 
 * Properties:
 * - OutputCollectionKey: StoreGate key for the collection of hits.
 * - Eta/PhiBins: Readout segmentation.
 * - RMin/Max, ZMin/Max: Spatial boundaries of the sensitive volume.
 * - Sampling: Identifier for the calorimeter layer.
 */
CaloHitMaker::CaloHitMaker( std::string name ) : 
  IMsgService(name),
  Algorithm()
{
  declareProperty( "OutputCollectionKey"      , m_collectionKey="CaloHitCollection"   ); // output
  
  declareProperty( "EtaBins"                  , m_etaBins                             );
  declareProperty( "PhiBins"                  , m_phiBins                             );
  declareProperty( "RMin"                     , m_rMin                                );
  declareProperty( "RMax"                     , m_rMax                                );
  declareProperty( "ZMin"                     , m_zMin                                );
  declareProperty( "ZMax"                     , m_zMax                                );
  // the region (r, z) of the maker tested at the midpoint of the step instead of its pre-step point (F41 conserto 36): the pre-step point of
  // the first step of a particle entering through the low face sits on the face and was refused by the strict lower bound; with the
  // cells of (r, z) boxes, the box of the step is looked up at the same midpoint (F41 conserto 38)
  declareProperty( "Sampling"                 , m_sampling                            );
  declareProperty( "Segment"                  , m_segment                             );
  declareProperty( "Detector"                 , m_detector                            );
  declareProperty( "BunchIdStart"             , m_bcid_start=-7                       );
  declareProperty( "BunchIdEnd"               , m_bcid_end=8                          );
  declareProperty( "BunchDuration"            , m_bc_duration=25                      );
  declareProperty( "OutputLevel"              , m_outputLevel=1                       );
  declareProperty( "DetailedHistograms"       , m_detailedHistograms=false            );
  declareProperty( "HistogramPath"            , m_histPath="/CaloHitMaker"            );
  declareProperty( "SamplingNoiseStd"         , m_noiseStd=0                          );
  // When true, only steps in the active medium (liquid argon or plastic scintillator) are kept,
  // as in the ATLAS hits; by default the whole energy deposited in the cell volume is kept.
  declareProperty( "ActiveEnergyOnly"         , m_activeEnergyOnly=false              );
  // When true, Birks' law is applied to the energy of each step in the scintillator and in the
  // liquid argon, with the ATLAS simulation constants (see birksEnergy).
  declareProperty( "BirksLaw"                 , m_birksLaw=false                      );
  // When true, the bunch crossing of each deposit in the hits comes from the time of the ATLAS simulation (the time of flight
  // from the interaction point taken out; see hitTime) instead of the global time of the pre-step point.
  declareProperty( "AtlasHitTime"             , m_atlasHitTime=false                  );
  // Cells as (r, z) boxes (ATLAS tile cells, set from geometry/python/v1/TILE.py). When CellEta is empty
  // (the default) the cells are the eta x phi grid given by EtaBins and PhiBins.
  declareProperty( "CellEta"                  , m_cellEta                             );
  declareProperty( "CellDeltaEta"             , m_cellDeltaEta                        );
  declareProperty( "CellBoxRMin"              , m_cellBoxRMin                         );
  declareProperty( "CellBoxRMax"              , m_cellBoxRMax                         );
  declareProperty( "CellBoxZMin"              , m_cellBoxZMin                         );
  declareProperty( "CellBoxZMax"              , m_cellBoxZMax                         );
  declareProperty( "CellBoxIndex"             , m_cellBoxIndex                        );
  // With N > 0, the box of a step is found with the radius on the axis of its module (N modules from phi = 0),
  // r cos(phi - phi_c), as the ATLAS HEC simulation does (see cellRadius); 0 (the default) uses r.
  declareProperty( "CellRadiusModules"        , m_cellRadiusModules=0                 );
  // ATLAS-like EM end-cap (geometry/python/v1/EMEC.py, --atlas-emec): with EmecCompartment > 0 the maker takes only the
  // steps inside the volumes of its wheel (EmecWheel*) whose compartment, found as in the ATLAS simulation, is its own
  // (see emecFindCell); the cells are those of the table (CellEta). 0 (the default): off.
  declareProperty( "EmecCompartment"          , m_emecCompartment=0                   );
  declareProperty( "EmecEtaScale"             , m_emecEtaScale=0                      );
  declareProperty( "EmecEtaOffset"            , m_emecEtaOffset=0                     );
  declareProperty( "EmecMaxEta"               , m_emecMaxEta=0                        );
  declareProperty( "EmecFocalShift"           , m_emecFocalShift=0                    );
  declareProperty( "EmecZSep12"               , m_emecZSep12                          );
  declareProperty( "EmecZSep23"               , m_emecZSep23                          );
  declareProperty( "EmecZInner"               , m_emecZInner                          );
  declareProperty( "EmecWheelRMin"            , m_emecWheelRMin                       );
  declareProperty( "EmecWheelRMax"            , m_emecWheelRMax                       );
  declareProperty( "EmecWheelZMin"            , m_emecWheelZMin                       );
  declareProperty( "EmecWheelZMax"            , m_emecWheelZMax                       );
  // Charge collection of the ATLAS EM end-cap (F41 conserto 29; see emecChargeEnergy): off by default
  declareProperty( "EmecChargeCollection"     , m_emecChargeCollection=false          );
  declareProperty( "EmecChargeTables"         , m_emecChargeTables=""                 );
  declareProperty( "EmecChargeFieldMap"       , m_emecChargeFieldMap=""               );
  declareProperty( "EmecChargeHVMap"          , m_emecChargeHVMap=""                  );
  // ATLAS-like barrel EM and presamplers (geometry/python/v1/ECAL.py, --atlas-emb-cells): with EmbMode > 0 (1 = barrel,
  // 2 = end-cap presampler) the cell of a step inside the limits of the maker comes from its pseudorapidity, for the sampling
  // (0-3) and region (0, 1) of the ATLAS identifier dictionary read by this maker (see embFindCell); the cells are those of
  // the table (CellEta). 0 (the default): off.
  declareProperty( "EmbMode"                  , m_embMode=0                           );
  declareProperty( "EmbSampling"              , m_embSampling=0                       );
  declareProperty( "EmbRegion"                , m_embRegion=0                         );
  // EmbMode = 2: the end-cap presampler moved by EmbZShift (mm) from its nominal |z| (the ATLAS end-cap of the simulation, --atlas-run4;
  // F41 conserto 27); its eta is that of the point moved back, as the local coordinates of the ATLAS simulation. 0 (the default): none.
  declareProperty( "EmbZShift"                , m_embZShift=0                         );
  // EmbMode = 3: ATLAS-like barrel presampler with the cell from the gap of the electrode (see psbGapCell); radius of the
  // middle of the active layer, in mm
  declareProperty( "PsbR0"                    , m_psbR0=0.                            );
  // Barrel EM with the sampling boundaries and rules of the ATLAS simulation (F41 conserto 18, see embSampSeg); false by default
  declareProperty( "EmbSampSeg"               , m_embSampSeg=false                    );
  // Dual readout of the tile cells (two PMTs per cell, as in ATLAS): 0 = off, 1 = ATLAS U-shape, 2 = linear.
  // Only for the tile samplings and only with the ATLAS tile cells (CellEta not empty); see tilePmtWeights.
  declareProperty( "TileDualReadout"          , m_tileDualReadout=0                   );
  // Free-running hits (simu_trf.py --free-running-hits): the deposits of the ATLAS tile cells also go, per PMT and with
  // the identifier and the time of the ATLAS simulation, to the list FreeRunningListKey (see freeRunningTile).
  declareProperty( "FreeRunningHits"          , m_freeRunningHits=false               );
  declareProperty( "FreeRunningListKey"       , m_freeRunningListKey="FreeRunningHits");
  declareProperty( "FreeRunningBinning"       , m_freeRunningBinning=true             );
  declareProperty( "CellAtlasSection"         , m_cellAtlasSection                    );
  declareProperty( "CellAtlasTower"           , m_cellAtlasTower                      );
  declareProperty( "CellAtlasSampling"        , m_cellAtlasSampling                   );
  // (r, z) centre of each ATLAS tile cell, for the ATLAS time of its deposits (see tileTime)
  declareProperty( "CellRCentre"              , m_cellRCentre                         );
  declareProperty( "CellZCentre"              , m_cellZCentre                         );
  // ATLAS-like LAr cells (F41 conserto 19): fields of the ATLAS identifier of the cells of this maker. Part (1 = LArEM, 2 = LArHEC;
  // 0 = not set, the default) and barrel_ec (or pos_neg) choose the point of the step for the ATLAS time (see larHitTime); all of
  // them give the identifier of the free-running hits (see freeRunningLAr).
  declareProperty( "AtlasLArPart"             , m_atlasLArPart=0                      );
  declareProperty( "AtlasBarrelEc"            , m_atlasBarrelEc=0                     );
  declareProperty( "AtlasLArSampling"         , m_atlasLArSampling=0                  );
  declareProperty( "AtlasLArRegion"           , m_atlasLArRegion=0                    );
  declareProperty( "CellAtlasEtaIndex"        , m_cellAtlasEtaIndex                   );
  // Shift of the phi edges of the cells (rad), the half absorber of the ATLAS readout geometry; 0 by default
  declareProperty( "PhiShift"                 , m_phiShift=0.                         );
  // Birks constant of the liquid argon: 0.05832 (default) or 0.0486 (HEC, as ATLAS)
  declareProperty( "BirksLArK"                , m_birksLArK=0.05832                   );
  // ATLAS gap and ITC cells (F41 conserto 21): PMTs per cell, U-shape table, special modules and the replacement cell
  declareProperty( "CellNPmt"                 , m_cellNPmt                            );
  declareProperty( "UShapePart"               , m_uShapePart=-1                       );
  declareProperty( "UShapeLayer"              , m_uShapeLayer=-1                      );
  declareProperty( "SpecialModule"            , m_specialModule                       );
  declareProperty( "SpecialNPmt"              , m_specialNPmt                         );
  declareProperty( "ReplaceSection"           , m_replaceSection=0                    );
  declareProperty( "ReplaceTower"             , m_replaceTower=0                      );
  declareProperty( "ReplaceSampling"          , m_replaceSampling=0                   );
  declareProperty( "ReplaceRCentre"           , m_replaceRCentre=0                    );
  declareProperty( "ReplaceZCentre"           , m_replaceZCentre=0                    );
  declareProperty( "ReplaceCollectionKey"     , m_replaceCollectionKey=""             );
  declareProperty( "ReplaceHashBase"          , m_replaceHashBase=0                   );
  // ATLAS FCal with its electrodes (F41 conserto 22): module (1-3; 0 = off), side (+1, -1), logical volume of its gaps, and
  // the cell (dictionary eta and phi indices) and tile centre of each copy number
  declareProperty( "FCalModule"               , m_fcalModule=0                        );
  declareProperty( "FCalSide"                 , m_fcalSide=1                          );
  declareProperty( "FCalGapVolume"            , m_fcalGapVolume=""                    );
  declareProperty( "FCalCopyEtaIndex"         , m_fcalCopyEtaIndex                    );
  declareProperty( "FCalCopyPhiIndex"         , m_fcalCopyPhiIndex                    );
  declareProperty( "FCalCopyEta"              , m_fcalCopyEta                         );
  declareProperty( "FCalCopyPhi"              , m_fcalCopyPhi                         );
  declareProperty( "FCalCopyDeltaEta"         , m_fcalCopyDeltaEta                    );
  declareProperty( "FCalCopyDeltaPhi"         , m_fcalCopyDeltaPhi                    );
  // grid indices and position (mm) of each electrode, for the cell of the spots of the frozen showers (F41 conserto 23)
  declareProperty( "FCalCopyI"                , m_fcalCopyI                           );
  declareProperty( "FCalCopyJ"                , m_fcalCopyJ                           );
  declareProperty( "FCalCopyX"                , m_fcalCopyX                           );
  declareProperty( "FCalCopyY"                , m_fcalCopyY                           );



}

//!=====================================================================

StatusCode CaloHitMaker::initialize()
{
  MSG_INFO("1 Initialize..." << m_outputLevel);

  CHECK_INIT();
  setMsgLevel( (MSG::Level)m_outputLevel );
  m_nEtaBins = m_etaBins.size() - 1;
  m_nPhiBins = m_phiBins.size() - 1;
  if( m_tileDualReadout > 0 && isTile() && !useCells() ){
    MSG_FATAL( "TileDualReadout needs the ATLAS tile cells (CellEta)." );
  }
  if( m_freeRunningHits && isTile() && ( !useCells() || m_tileDualReadout <= 0 ||
                                        m_cellAtlasSection.size() != m_cellEta.size() ) ){
    MSG_FATAL( "FreeRunningHits needs the ATLAS tile cells with their ATLAS identifier fields and the dual readout." );
  }
  if( m_freeRunningHits && isAtlasLAr() && ( !useCells() || m_cellAtlasEtaIndex.size() != m_cellEta.size() ) ){
    MSG_FATAL( "FreeRunningHits needs the dictionary eta index of every ATLAS-like LAr cell (CellAtlasEtaIndex)." );
  }

  if( m_emecCompartment > 0 && ( m_emecZSep12.size() != 44 || m_emecZSep23.size() != 22 || m_emecZInner.size() != 7 ||
                                 m_emecWheelRMin.empty() || m_emecWheelRMin.size() != m_emecWheelRMax.size() ||
                                 m_emecWheelRMin.size() != m_emecWheelZMin.size() ||
                                 m_emecWheelRMin.size() != m_emecWheelZMax.size() ||
                                 m_cellEta.size() != (unsigned)(m_emecMaxEta + 1) || m_nPhiBins % 2 ) ){
    MSG_FATAL( "EmecCompartment needs the tables of the ATLAS-like EM end-cap (geometry/python/v1/EMEC.py)." );
  }

  // Charge collection of the ATLAS EM end-cap (F41 conserto 29): the ported LArG4::EC::EnergyCalculator of the wheel and side of
  // this maker, built once per wheel, side and files (as the four calculators EMEC{Pos,Neg}{Inner,Outer}WheelCalculator of the
  // ATLAS simulation) and shared by the makers of the compartments of that wheel
  if( m_emecChargeCollection ){
    if( m_emecCompartment <= 0 || !m_freeRunningHits || !isAtlasLAr() ){
      MSG_FATAL( "EmecChargeCollection needs an ATLAS-like EM end-cap maker (EmecCompartment) with the free-running hits." );
    }
    const bool inner = ( m_emecCompartment <= 2 );   // compartments 1 and 2: inner wheel (s_geometry of EnergyCalculator.cc)
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
    // the transform to the wheel frame (emecTopTransform) is that of the geometry of the simulation of ATLAS-P2-RUN4-01-01-00
    const double zFront = m_emecFocalShift + m_emecCalculator->calculator()->GetElecFocaltoWRP() +
                          m_emecCalculator->calculator()->GetdWRPtoFrontFace();
    if( zFront != 3745. ){
      MSG_FATAL( "EmecChargeCollection needs the EMEC wheels of the ATLAS simulation geometry (front face at |z| = 3745 mm, --atlas-run4); "
                 "here " << zFront << " mm." );
    }
  }

  if( m_embMode > 0 ){
    // number of cells per side of each region of the dictionary
    int n = -1;
    if     ( m_embMode == 2 ) n = ( m_embSampling == 0 && m_embRegion == 0 ) ? 12 : -1;
    else if( m_embSampling == 0 ) n = ( m_embRegion == 0 ) ? 61 : -1;
    else if( m_embSampling == 1 ) n = ( m_embRegion == 0 ) ? 447 : ( m_embRegion == 1 ? 3 : -1 );
    else if( m_embSampling == 2 ) n = ( m_embRegion == 0 ) ? 56  : ( m_embRegion == 1 ? 1 : -1 );
    else if( m_embSampling == 3 ) n = ( m_embRegion == 0 ) ? 27  : -1;
    if( n < 0 || m_cellEta.size() != (unsigned)n || m_emecCompartment > 0 ){
      MSG_FATAL( "EmbMode needs the cell table of the ATLAS-like barrel EM or presampler (geometry/python/v1/ECAL.py)." );
    }
  }

  if( isFCal() && ( m_fcalModule > 3 || m_fcalGapVolume.empty() || m_fcalCopyEtaIndex.empty() ||
                    m_fcalCopyPhiIndex.size() != m_fcalCopyEtaIndex.size() || m_fcalCopyEta.size() != m_fcalCopyEtaIndex.size() ||
                    m_fcalCopyPhi.size() != m_fcalCopyEtaIndex.size() || m_fcalCopyDeltaEta.size() != m_fcalCopyEtaIndex.size() ||
                    m_fcalCopyDeltaPhi.size() != m_fcalCopyEtaIndex.size() || useCells() ) ){
    MSG_FATAL( "FCalModule needs the cell, centre and width of every electrode (geometry/python/v2/FCAL.py)." );
  }
  // centre and width of each tile, for the hits of the normal chain (one hit per tile)
  if( isFCal() ){
    for( size_t k = 0; k < m_fcalCopyEtaIndex.size(); ++k ){
      const auto tile = std::make_pair( m_fcalCopyEtaIndex[k], m_fcalCopyPhiIndex[k] );
      m_fcalTileCentre.emplace( tile, std::make_pair( m_fcalCopyEta[k], m_fcalCopyPhi[k] ) );
      m_fcalTileWidth.emplace( tile, std::make_pair( m_fcalCopyDeltaEta[k], m_fcalCopyDeltaPhi[k] ) );
    }
  }
  // tube map of FCAL_ChannelMap::add_tube (F41 conserto 23)
  if( isFCal() && !m_fcalCopyI.empty() ){
    const size_t n = m_fcalCopyEtaIndex.size();
    if( m_fcalCopyJ.size() != n || m_fcalCopyX.size() != n || m_fcalCopyY.size() != n || m_fcalCopyI.size() != n ){
      MSG_FATAL( "FCalCopyI, FCalCopyJ, FCalCopyX and FCalCopyY need one entry per electrode." );
    }
    std::map<unsigned int, size_t> first;
    for( size_t k = 0; k < n; ++k ){
      const unsigned int key = ( (unsigned int)( m_fcalCopyJ[k] + 200 ) << 16 ) + (unsigned int)( m_fcalCopyI[k] + 200 );
      m_fcalTubeMap.emplace( key, std::make_pair( m_fcalCopyEtaIndex[k], m_fcalCopyPhiIndex[k] ) );
      first.emplace( key, k );
      m_fcalTileCentre.emplace( std::make_pair( m_fcalCopyEtaIndex[k], m_fcalCopyPhiIndex[k] ),
                                std::make_pair( m_fcalCopyEta[k], m_fcalCopyPhi[k] ) );
    }
    m_fcalFirstTube  = first.begin()->first;
    m_fcalFirstTubeX = m_fcalCopyX[first.begin()->second];
    m_fcalFirstTubeY = m_fcalCopyY[first.begin()->second];
  }

  return StatusCode::SUCCESS;
}

//!=====================================================================

StatusCode CaloHitMaker::finalize()
{
  // charge collection of the ATLAS EM end-cap (F41 conserto 29): the deposits discarded because the HV helper of ATLAS throws
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

//!=====================================================================

StatusCode CaloHitMaker::bookHistograms( SG::EventContext &ctx ) const
{
  MSG_DEBUG("Booking histograms...");
  auto store = ctx.getStoreGateSvc();

  store->mkdir(m_histPath);

  // Create the 2D histogram for monitoring purpose
  store->add(new TH2F( "hits_edep", "Hit Energy (Truth); #eta; #phi; Energy [MeV]", m_nEtaBins, m_etaBins.data(), m_nPhiBins, m_phiBins.data() ) );
  
  return StatusCode::SUCCESS;
}

//!=====================================================================

/**
 * @brief Prepare the hit collection before processing steps.
 * 
 * Initializes the CaloHitCollection in the event store. Pre-populates it with 
 * empty hits for every defined readout cell (bin) to be ready for energy accumulation.
 * This ensures that every cell has a corresponding object, even if empty.
 */
StatusCode CaloHitMaker::pre_execute( EventContext &ctx ) const
{
  // One free-running hit list per event, shared by every sampling: the first maker of the sequence creates it.
  if( m_freeRunningHits && !ctx.exist(m_freeRunningListKey) ){
    SG::WriteHandle<CaloFreeRunningHitList> list( m_freeRunningListKey, ctx );
    list.record( std::unique_ptr<CaloFreeRunningHitList>(new CaloFreeRunningHitList()) );
  }

  // Build the CaloHitCollection and attach into the EventContext
  // Create the hit collection into the event context
  SG::WriteHandle<xAOD::CaloHitCollection> collection( m_collectionKey, ctx );
  collection.record( std::unique_ptr<xAOD::CaloHitCollection>(new xAOD::CaloHitCollection()) );

  // ATLAS FCal with its cells: one hit per tile of this module and side, bin = 16 eta + phi (eta 0-62, phi 0-15), with the centre
  // of the tile (mean position of its electrodes) and its width
  if( isFCal() ){
    for( const auto &c : m_fcalTileCentre ){
      const auto &w = m_fcalTileWidth.at( c.first );
      const unsigned bin = 16 * c.first.first + c.first.second;
      auto *hit = new xAOD::CaloHit( c.second.first, c.second.second, w.first, w.second, hash(bin),
                                     (CaloSampling)m_sampling, (Detector)m_detector,
                                     m_bc_duration, m_bcid_start, m_bcid_end );
      if( !collection->insert( hit->hash(), hit) ){
        MSG_FATAL( "It is not possible to include hit hash ("<< hit->hash() << ") into the collection. hash already exist.");
      }
    }
    return StatusCode::SUCCESS;
  }

  float deltaEta = std::abs(m_etaBins[1] - m_etaBins[0]);
  float deltaPhi = std::abs(m_phiBins[1] - m_phiBins[0]);

  // Cells given as (r, z) boxes: one hit per cell and phi slice, cells in the order of the table (increasing z),
  // with the eta and delta eta of the table; the local hash follows the same rule as the eta x phi grid.
  if( useCells() ){
    for ( unsigned cell = 0; cell < m_cellEta.size(); ++cell ){
      for ( unsigned phiBin = 0; phiBin < m_nPhiBins; ++phiBin ){
        // No hit for a cell absent in this module in ATLAS (D4 in EBA15 and EBC18): its deposits go to the replacement cell
        if( !m_replaceCollectionKey.empty() && tileNPmt( cell, phiBin ) == 0 ) continue;
        float phiCenter = m_phiBins[phiBin] + deltaPhi / 2;
        unsigned bin = m_nPhiBins * cell + phiBin;
        auto *hit = new xAOD::CaloHit( m_cellEta[cell], phiCenter, m_cellDeltaEta[cell], deltaPhi, hash(bin),
                                       (CaloSampling)m_sampling,
                                       (Detector)m_detector,
                                       m_bc_duration, m_bcid_start, m_bcid_end );
        hit->setDualReadout( m_tileDualReadout > 0 && isTile() );
        if( !collection->insert( hit->hash(), hit) )
        {
          MSG_FATAL( "It is not possible to include hit hash ("<< hit->hash() << ") into the collection. hash already exist.");
        }
      }
    }
    MSG_DEBUG("Pre_execute done.");
    return StatusCode::SUCCESS;
  }

  //
  // Prepare all sensitive objects like a two dimensional histogram
  //
  for ( unsigned etaBin = 0; etaBin < m_nEtaBins; ++etaBin){ // Rows

    //if (std::abs(m_etaBins[etaBin]) == std::abs(m_etaBins[etaBin+1]))
    //  continue;

    for ( unsigned phiBin = 0; phiBin < m_nPhiBins; ++phiBin){ // Cols

      float etaCenter = m_etaBins[etaBin] + deltaEta / 2;
      float phiCenter = m_phiBins[phiBin] + deltaPhi / 2;
     
      // local hash
      unsigned bin = m_nPhiBins * etaBin + phiBin;
      
      // Create the calorimeter cell
      auto *hit = new xAOD::CaloHit( etaCenter, phiCenter, deltaEta, deltaPhi, hash(bin), 
                                     (CaloSampling)m_sampling,
                                     (Detector)m_detector,
                                     m_bc_duration, m_bcid_start, m_bcid_end );
      if( !collection->insert( hit->hash(), hit) )
      {
        MSG_FATAL( "It is not possible to include hit hash ("<< hit->hash() << ") into the collection. hash already exist.");
      }

    } // Loop over phi bins
  }// Loop over eta bins

  MSG_DEBUG("Pre_execute done.");
  return StatusCode::SUCCESS;
}

//!=====================================================================

/**
 * @brief Execution per Geant4 Step.
 * 
 * Invoked by the framework for every particle step.
 * 1. Checks if the step is within the geometric bounds of this calorimeter volume.
 * 2. Calculates the corresponding eta/phi bin.
 * 3. Retrieves the specific Hit object for that bin.
 * 4. Adds the energy deposit to the Hit.
 */
StatusCode CaloHitMaker::execute( EventContext &ctx , const G4Step *step ) const
{
  // Spots of the frozen showers of the ATLAS FCal (F41 conserto 23): only for the FCal makers
  if( isShowerSpot(step) ){
    if( isFCal() && !m_fcalTubeMap.empty() ) fcalSpot( ctx, step );
    return StatusCode::SUCCESS;
  }

  // ATLAS FCal with its electrodes: the cell from the copy number of the gap, to the hit of its tile and the free-running hits
  if( isFCal() ){
    fcalStep( ctx, step );
    return StatusCode::SUCCESS;
  }

  SG::ReadHandle<xAOD::CaloHitCollection> collection( m_collectionKey, ctx );

  if( !collection.isValid() ){
    MSG_FATAL("It's not possible to retrieve the CaloHitCollection using this key: " << m_collectionKey);
  }

  // Active medium only: a Geant4 step never crosses a volume boundary, so the material
  // of its pre-step point is the material where the energy was deposited.
  if( m_activeEnergyOnly ){
    const G4Material *material = step->GetPreStepPoint()->GetMaterial();
    if( !material ) return StatusCode::SUCCESS;
    const G4String &materialName = material->GetName();
    if( materialName != "liquidArgon" && materialName != "PLASTIC SCINTILLATOR" && materialName != "ATLAS_TILE_PVT" )
      return StatusCode::SUCCESS;
  }

  // Get the position
  G4ThreeVector pos = step->GetPreStepPoint()->GetPosition();

  // Apply all necessary transformation (x,y,z) to (eta,phi,r) coordinates
  // Get ATLAS coordinates (in transverse plane xy)
  auto vpos = TVector3( pos.x(), pos.y(), pos.z());
  float eta = vpos.PseudoRapidity();
  float phi = vpos.Phi();
  float radius = vpos.Perp();

  // In plan xy (the ATLAS-like barrel EM with SampSeg takes the whole accordion: its sampling comes from embSampSeg). The region of this
  // maker is tested at the midpoint of the step, which is always inside the volume of the step. At the pre-step point, the first step of a
  // particle entering through the low face (lower z or lower r) sits on that face and was refused by the strict lower bound, while on the
  // opposite side the entry face is accepted by <=.
  const bool sampSeg = m_embSampSeg && m_embMode == 1 && m_embSampling > 0;
  const G4ThreeVector rpos = 0.5*( pos + step->GetPostStepPoint()->GetPosition() );
  const float rradius = rpos.perp();
  if( !sampSeg && !(rradius > m_rMin && rradius <= m_rMax) )
    return StatusCode::SUCCESS;

  if( !(rpos.z() > m_zMin && rpos.z() <= m_zMax))
    return StatusCode::SUCCESS;

  int etaBin, phiBin;
  if( m_emecCompartment > 0 ){
    // ATLAS-like EM end-cap: the step is taken only inside the wheel of this maker and in its compartment
    if( emecFindCell( pos.x(), pos.y(), pos.z(), etaBin, phiBin ) != m_emecCompartment )
      return StatusCode::SUCCESS;
  }else if( sampSeg ){
    // ATLAS-like barrel EM with the sampling of the ATLAS simulation: only the active steps of this sampling and region
    int region, sampling, ieta;
    if( !embSampSeg( pos.x(), pos.y(), pos.z(), region, sampling, ieta ) ) return StatusCode::SUCCESS;
    if( sampling != m_embSampling || region != m_embRegion ) return StatusCode::SUCCESS;
    etaBin = ieta - ( ( m_embSampling == 1 && m_embRegion == 0 ) ? 1 : 0 );   // the strip 0 does not exist
    if( etaBin < 0 || etaBin >= (int)m_cellEta.size() ) return StatusCode::SUCCESS;
    phiBin = findPhi(phi);
    if(phiBin < 0)
      return StatusCode::SUCCESS;
  }else if( m_embMode > 0 ){
    // ATLAS-like barrel EM and presamplers: the cell from the pseudorapidity of the step, within the region of this maker
    etaBin = embFindCell( pos.x(), pos.y(), pos.z() );
    if(etaBin < 0)
      return StatusCode::SUCCESS;
    phiBin = findPhi(phi);
    if(phiBin < 0)
      return StatusCode::SUCCESS;
  }else{
    // Row of the cell: the eta bin of the grid, or the cell of the (r, z) boxes. With StepMidpointRegion the boxes are looked up at
    // the same point as the region test, the midpoint of the step (F41 conserto 38): a step that crosses a thin volume whose box is
    // the volume itself (the gap and crack scintillators E1-E4, 6 to 12 mm, crossed by a muon in one step) starts on the face of the
    // box, and its pre-step point was refused by the strict lower bound of findCell.
    const bool boxMidpoint = useCells();
    const float cellPhi = boxMidpoint ? (float)rpos.phi() : phi;
    etaBin = useCells() ? findCell(cellRadius(boxMidpoint ? rradius : radius, cellPhi), boxMidpoint ? (float)rpos.z() : (float)pos.z())
                        : find(m_etaBins, eta);

    if(etaBin < 0)
      return StatusCode::SUCCESS;

    phiBin = findPhi(cellPhi);

    if(phiBin < 0)
      return StatusCode::SUCCESS;
  }

  int bin = m_nPhiBins * etaBin + phiBin;

  xAOD::CaloHit *hit=nullptr;

  // The cell is absent in this module in ATLAS (D4 in EBA15 and EBC18) and has no hit: the deposit goes to the hit of the
  // replacement cell (D5 of the same module), as in the ATLAS simulation (the free-running hits too, freeRunningTile)
  const bool replacedCell = !m_replaceCollectionKey.empty() && tileNPmt( etaBin, phiBin ) == 0;

  if( replacedCell || collection->retrieve(hash(bin), hit) ){
    if( replacedCell ){
      SG::ReadHandle<xAOD::CaloHitCollection> replaced( m_replaceCollectionKey, ctx );
      xAOD::CaloHit *replacedHit = nullptr;
      if( !replaced.isValid() || !replaced->retrieve( (unsigned long int)m_replaceHashBase + phiBin, replacedHit ) ){
        MSG_FATAL( "No hit of the replacement cell in " << m_replaceCollectionKey << " for the phi bin " << phiBin );
      }
      hit = replacedHit;
    }
    // hit->fill( step );
    const float edep = m_birksLaw ? birksEnergy(step) : (float)step->GetTotalEnergyDeposit();
    float tHit = 0, tPmt0 = 0, tPmt1 = 0;
    if( m_atlasHitTime ){
      hitTime( step, etaBin, phiBin, tHit, tPmt0, tPmt1 );
      hit->fillAt( tHit, 1*m_noiseStd, edep );
    }else if( m_birksLaw )
      hit->fill( step , 1*m_noiseStd, edep );
    else
      hit->fill( step , 1*m_noiseStd); // hit with tof selection sensible by 1*sigma of sampling noise.
    // Dual readout: the same energy shared between the two PMTs by the position across the module
    if( hit->dualReadout() ){
      // number of PMTs of the cell in this module: 2, 1 (only pmt 0), -1 (only pmt 1) or 0 (the cell is read as the
      // replacement cell, as D4 in EBA15 and EBC18); see tileNPmt
      const int npmt = tileNPmt( etaBin, phiBin );
      float w0, w1;
      if( npmt == 2 || npmt == 0 )
        tilePmtWeights( std::remainder( phi - hit->phi(), 2 * M_PI ), pos.z(), w0, w1, npmt == 0 );
      else if( npmt == 1 ){ w0 = 1; w1 = 0; }
      else                { w0 = 0; w1 = 1; }
      if( m_atlasHitTime ) hit->fillPmtAt( tPmt0, edep * w0, tPmt1, edep * w1 );
      else                 hit->fillPmt( step, edep * w0, edep * w1 );
      // Free-running hits: the same deposit and PMT weights, with the ATLAS identifier and time
      if( m_freeRunningHits && edep > 0 )
        freeRunningTile( ctx, step, etaBin, phiBin, edep, w0, w1, npmt );
    }
    // Free-running hits of the ATLAS-like LAr cells: the same deposit, with the ATLAS identifier and time
    // (with the charge collection of the ATLAS EM end-cap, F41 conserto 29, the energy of the free-running hit is the one of the
    // ATLAS simulation, emecChargeEnergy; the hit collection keeps edep)
    if( m_freeRunningHits && isAtlasLAr() && edep > 0 )
    {
      if( !m_emecCalculator ){
        freeRunningLAr( ctx, step, etaBin, phiBin, edep );
      }else{
        double energy = 0;
        const bool kept = emecChargeEnergy( step, energy );
        emecDiscardCount( m_emecCompartment <= 2, edep, !kept );
        if( kept ) freeRunningLAr( ctx, step, etaBin, phiBin, (float)energy );
      }
    }
  }else{
    MSG_FATAL( "Its not possible to retrieve the hit. Bin ("<< bin << ") not exist");
  }
  
  return StatusCode::SUCCESS;
}

//!=====================================================================

//!=====================================================================

// Weights of the two PMTs of a tile cell for a step at the azimuthal distance phiLocal (rad) from the centre of the
// module, following the ATLAS simulation (Athena, TileGeoG4SDCalc::MakePmtEdepTime):
// - U-shape (TileDualReadout = 1, Ushape = 1 in Athena): the measured response of each PMT across the tile,
//   TileGeoG4SDCalc::Tile_1D_profileRescaled, tables per layer (A, BC, D) for the long barrel and for each extended
//   barrel (TileUShape.h). As in Athena, the PMT 1 reads the table at -phiLocal and the PMT 0 at +phiLocal, and the
//   two weights do not add up exactly to 1.
// - linear (TileDualReadout = 2, Ushape = 0 in Athena): w1 = 0.3 + 0.2 dy1/halfY = 0.5 + 0.2 u, w0 = 1 - w1, with
//   u = tan(phiLocal)/tan(dphi/2) from -1 to 1 across the module (the tile edges taken as radial lines).
// Convention (not checked against the orientation of the ATLAS local axes): the PMT 1 is the one on the side of
// larger phi, on both sides of the detector.
// Number of PMTs of a tile cell in the module of the phi bin (F41 conserto 21): CellNPmt of the cell (2 by default; 1 for
// E1-E4, read by pmt 0), unless the module is in SpecialModule (modules 0-63 from phi = 0, as in TileDetDescr), where it is
// SpecialNPmt: 1 = only pmt 0, -1 = only pmt 1, 0 = read as the replacement cell (Athena TileGeoG4LookupBuilder: special C10
// with one PMT, D4 absent in EBA15 and EBC18).
int CaloHitMaker::tileNPmt( int cell, int phiBin ) const
{
  int npmt = ( cell >= 0 && cell < (int)m_cellNPmt.size() ) ? m_cellNPmt[cell] : 2;
  if( m_specialModule.empty() ) return npmt;
  const double twoPi = 2 * M_PI, modWidth = twoPi / 64;
  double phiCentre = 0.5 * ( m_phiBins[phiBin] + m_phiBins[phiBin+1] );
  double phi0 = phiCentre < 0 ? phiCentre + twoPi : phiCentre;
  int module = (int)std::floor( phi0 / modWidth ) % 64;
  for( size_t i = 0; i < m_specialModule.size(); ++i )
    if( m_specialModule[i] == module ) return m_specialNPmt[i];
  return npmt;
}

// The ATLAS ITC (F41 conserto 21) uses the tables of the long barrel by tile row (Tile_1D_profileRescaled: nDetector != 2;
// C10 rows 1-3 = A, D4 rows 4-5 = BC): UShapePart and UShapeLayer; the special D4 read as D5 (replaced) uses the D table
// of its extended barrel.
void CaloHitMaker::tilePmtWeights( float phiLocal, float z, float &w0, float &w1, bool replaced ) const
{
  if( m_tileDualReadout == 1 ){
    // layer: TileCal1/TileExt1 = A, TileCal2/TileExt2 = BC (B), TileCal3/TileExt3 = D
    int layer = (m_sampling - 5) % 3;
    int part  = (m_sampling <= 7) ? 0 : ( z > 0 ? 1 : 2 ); // LB, EBA (z > 0), EBC (z < 0)
    if( replaced ){ part = ( z > 0 ? 1 : 2 ); layer = 2; }
    else if( m_uShapePart >= 0 ){ part = m_uShapePart; layer = m_uShapeLayer; }
    const double *t = TileUShape::table( part, layer );
    w1 = TileUShape::amplitude( t, -phiLocal );
    w0 = TileUShape::amplitude( t,  phiLocal );
    return;
  }
  const float halfDeltaPhi = std::abs( m_phiBins[1] - m_phiBins[0] ) / 2;
  float u = std::tan( phiLocal ) / std::tan( halfDeltaPhi );
  u = std::max( -1.f, std::min( 1.f, u ) );
  w1 = 0.5 + 0.2 * u;
  w0 = 1 - w1;
}

//!=====================================================================

// Free-running hits of the ATLAS tile cells, per PMT, with the identifier and the time of the ATLAS simulation.
// Sources (Athena, public, Apache 2.0; copies and report in the F41/F39 notes of the group):
// - identifier: the pmt_id of the ATLAS identifier dictionary (DetectorDescription/IdDictParser/data/
//   IdDictTileCalorimeter.xml), packed in 64 bits as the IdDict code does (IdDictDictionary, IdentifierField):
//   subdet (Tile = index 2) in bits 63-61, section 60-58, side 57-54 (index: -1 -> 0, +1 -> 2), module 53-46,
//   tower 45-40, sampling 39-36, pmt 35-34 (adc 33-32 = 0); checked against Calorimeter/CaloIdentifier/share/TileID_test.ref.
//   The PMT on the side of larger phi ("up") is pmt 1, the other pmt 0 (the convention of tilePmtWeights); D0 is side +1.
// - module m covers phi in [m, m+1] * 2 pi / 64 (TileDetDescr); side +1 for z > 0.
// - time (TileGeoG4SDCalc::MakePmtEdepTime, DoTOFCorrection = true, refraction index 1.59 of tile and fibre): the global
//   time at the post-step point, plus [r_cell (n - 2 / sin(theta_cell)) + |x| (1 - n sin(theta_hit))] / c, where r_cell and
//   theta_cell are those of the centre of the cell and x the post-step position; each PMT adds
//   n (dy - r_cell tan(pi/64)) / c, dy the distance of the step to the edge of the tile on the side of the other PMT
//   (here: the edges of the module at +-pi/64 around its centre, from the pre-step position, as for the PMT weights).
//   If the time of a PMT passes TimeCut = 350.5 ns, both go to the late hit time 99995 ns without the PMT delays; the
//   energy is kept.
// - time binning (option FreeRunningBinning; TileGeoG4SDCalc::deltaT, DeltaTHit = {0.5, -75.25, 75.25, 5.}): bins of
//   0.5 ns for -75.25 < t < 75.25 ns, 5 ns elsewhere (see CaloFreeRunningHitList::add).
// Cells of the ATLAS gap and ITC (F41 conserto 21): npmt = 1 or -1 (one PMT: pmt 0 or pmt 1, as E1-E4 and the special C10)
// has no PMT delay (Athena adds deltaT only with two PMTs); npmt = 0 (D4 in EBA15 and EBC18) is read as the replacement
// cell (D5: ReplaceSection, ReplaceTower, ReplaceSampling, ReplaceRCentre, ReplaceZCentre), with two PMTs.
void CaloHitMaker::freeRunningTile( SG::EventContext &ctx, const G4Step *step, int cell, int phiBin, float edep,
                                    float w0, float w1, int npmt ) const
{
  SG::ReadHandle<CaloFreeRunningHitList> list( m_freeRunningListKey, ctx );
  if( !list.isValid() ){
    MSG_FATAL("It's not possible to retrieve the CaloFreeRunningHitList using this key: " << m_freeRunningListKey);
  }
  const double n = 1.59, timeCut = 350.5, lateHitTime = 99995., tanPi64 = std::tan(M_PI / 64);
  const double cLight = CLHEP::c_light;   // mm/ns

  // identifier fields
  const double twoPi = 2 * M_PI, modWidth = twoPi / 64;
  double phiCentre = 0.5 * ( m_phiBins[phiBin] + m_phiBins[phiBin+1] );
  double phi0 = phiCentre < 0 ? phiCentre + twoPi : phiCentre;
  int module = (int)std::floor( phi0 / modWidth ) % 64;
  double moduleCentre = std::remainder( (module + 0.5) * modWidth, twoPi );
  const bool replaced = ( npmt == 0 );
  int section  = replaced ? m_replaceSection  : m_cellAtlasSection[cell];
  int tower    = replaced ? m_replaceTower    : m_cellAtlasTower[cell];
  int sampling = replaced ? m_replaceSampling : m_cellAtlasSampling[cell];
  double rCell = replaced ? m_replaceRCentre : m_cellRCentre[cell];
  double zCell = replaced ? m_replaceZCentre : m_cellZCentre[cell];
  int side     = ( zCell >= 0 || (section == 1 && sampling == 2 && tower == 0) ) ? +1 : -1;
  auto pmtId = [&]( int pmt ) -> long long {
    unsigned long long id = (2ULL << 61) | ((unsigned long long)section << 58) | ((unsigned long long)(side > 0 ? 2 : 0) << 54)
                          | ((unsigned long long)module << 46) | ((unsigned long long)tower << 40)
                          | ((unsigned long long)sampling << 36) | ((unsigned long long)pmt << 34);
    return (long long)id;
  };

  // time of the deposit (ns) and the delays of the two PMTs
  double tglobal, t, dtUp, dtDown;
  tileTime( step, cell, phiBin, npmt, tglobal, t, dtUp, dtDown );
  if( t + dtUp > timeCut || t + dtDown > timeCut ){
    t = lateHitTime; dtUp = dtDown = 0.0;
  }
  double delta = m_freeRunningBinning ? ( ( t > -75.25 && t < 75.25 ) ? 0.5 : 5.0 ) : 0.0;

  double eta = m_cellEta[cell];
  if( w1 * edep > 0 ) list->add( pmtId(1), w1 * edep, t + dtUp,   tglobal, eta, moduleCentre, sampling, side, module, tower, delta );
  if( w0 * edep > 0 ) list->add( pmtId(0), w0 * edep, t + dtDown, tglobal, eta, moduleCentre, sampling, side, module, tower, delta );
}

// ATLAS time of a deposit in a tile cell (sources and formula in the comment of freeRunningTile): tglobal the global time of the
// post-step point, t = tglobal + [r_cell (n - 2 / sin(theta_cell)) + |x| (1 - n sin(theta_hit))] / c, and the delays of the
// PMTs across the tile, dtUp (PMT 1) and dtDown (PMT 0), zero for a cell with one PMT. The time cut (TimeCut) is not applied here.
void CaloHitMaker::tileTime( const G4Step *step, int cell, int phiBin, int npmt, double &tglobal, double &t, double &dtUp,
                             double &dtDown ) const
{
  const double n = 1.59, tanPi64 = std::tan(M_PI / 64);
  const double cLight = CLHEP::c_light;   // mm/ns
  const double twoPi = 2 * M_PI, modWidth = twoPi / 64;
  double phiCentre = 0.5 * ( m_phiBins[phiBin] + m_phiBins[phiBin+1] );
  double phi0 = phiCentre < 0 ? phiCentre + twoPi : phiCentre;
  int module = (int)std::floor( phi0 / modWidth ) % 64;
  double moduleCentre = std::remainder( (module + 0.5) * modWidth, twoPi );
  const bool replaced = ( npmt == 0 );
  double rCell = replaced ? m_replaceRCentre : m_cellRCentre[cell];
  double zCell = replaced ? m_replaceZCentre : m_cellZCentre[cell];
  // time of the deposit (ns)
  const G4ThreeVector post = step->GetPostStepPoint()->GetPosition();
  const G4ThreeVector pre  = step->GetPreStepPoint()->GetPosition();
  tglobal = step->GetPostStepPoint()->GetGlobalTime() / ns;
  double sinThCell = rCell / std::sqrt( rCell*rCell + zCell*zCell );
  double cosThHit = post.cosTheta();
  t = tglobal + ( rCell * ( n - 2.0 / sinThCell ) + post.mag() * ( 1.0 - n * std::sqrt( 1.0 - cosThHit*cosThHit ) ) ) / cLight;
  // PMT delays: light across the tile to each edge; local frame of the module from the pre-step position
  double phiLocal = std::remainder( pre.phi() - moduleCentre, twoPi );
  double rPre = pre.perp();
  double xLocal = rPre * std::cos(phiLocal), yLocal = rPre * std::sin(phiLocal);
  double halfWidth = xLocal * tanPi64;
  double dyUp = halfWidth - yLocal;     // to the edge on the side of larger phi (PMT 1 reads there)
  double dyDown = halfWidth + yLocal;
  dtUp   = n * ( dyUp   - rCell * tanPi64 ) / cLight;
  dtDown = n * ( dyDown - rCell * tanPi64 ) / cLight;
  if( npmt == 1 || npmt == -1 ) dtUp = dtDown = 0.0;   // one PMT: no delay across the tile (Athena: only with two PMTs)
}

// ATLAS time of a deposit in the liquid argon, as the ATLAS simulation (Athena, public, Apache 2.0; LArBarrelCalculator and
// LArBarrelPresamplerCalculator: pre-step; EnergyCalculator, LArEndcapPresamplerCalculator, LArHECWheelCalculator,
// LArFCALCalculatorBase: mean of pre- and post-step): the global time minus |r|/c of the same point, in ns. A maker without the
// ATLAS LAr cells takes the mean of pre- and post-step.
double CaloHitMaker::larHitTime( const G4Step *step ) const
{
  const G4StepPoint *preP = step->GetPreStepPoint(), *postP = step->GetPostStepPoint();
  if( std::abs(m_atlasBarrelEc) == 1 && m_atlasLArPart == 1 )
    return preP->GetGlobalTime() / ns - preP->GetPosition().mag() / CLHEP::c_light;
  const double tglobal = 0.5 * ( preP->GetGlobalTime() + postP->GetGlobalTime() ) / ns;
  return tglobal - ( 0.5 * ( preP->GetPosition() + postP->GetPosition() ) ).mag() / CLHEP::c_light;
}

// Time (ns) that chooses the bunch crossing of a deposit in the hit collection of the normal chain, with AtlasHitTime: the time of
// the ATLAS simulation, so that a particle from the interaction point at the speed of light is in time (bunch crossing 0) in every
// calorimeter. Tile cells of ATLAS (samplings TileCal1 to TileExt3 with the cell centres): tileTime, the cell without the PMT
// delays for the hit, each PMT with its delay for edep_pmt0 and edep_pmt1. Elsewhere: larHitTime, the same for both PMTs.
void CaloHitMaker::hitTime( const G4Step *step, int cell, int phiBin, float &t, float &t0, float &t1 ) const
{
  if( m_sampling >= 5 && m_sampling <= 10 && cell >= 0 && cell < (int)m_cellRCentre.size() ){
    double tglobal, tc, dtUp, dtDown;
    tileTime( step, cell, phiBin, tileNPmt( cell, phiBin ), tglobal, tc, dtUp, dtDown );
    t = (float)tc; t0 = (float)( tc + dtDown ); t1 = (float)( tc + dtUp );
    return;
  }
  t = t0 = t1 = (float)larHitTime( step );
}

//!=====================================================================

// Free-running hits of the ATLAS-like LAr cells (F41 conserto 19), with the identifier and the time of the ATLAS simulation.
// Sources (Athena, public, Apache 2.0; copies and report in the F41 notes of the group, c19_lar_cellid_flag/):
// - identifier: channel_id(barrel_ec, sampling, region, eta, phi) of LArEM_ID / LArHEC_ID (LArG4SimpleSD::ConvertID), the
//   32-bit compact identifier in the upper half of the 64-bit integer, as in the ATLAS HITS ntuple. Bit layout of the 32
//   bits (bit 31 first), read from the ATLAS HITS ntuple (c19_bits_5k.py; 100% of its LAr entries decode to the branches):
//   LArEM: LArCalorimeter 1 (3 bits) | part 3 (3) | barrel_ec index in {-3,-2,-1,1,2,3} (3) | sampling (2) | region (3) |
//   eta (9) | phi (8) | 0 (1); LArHEC: 1 (3) | part 4 (3) | pos_neg -2 -> 0, +2 -> 1 (1) | sampling (2) | region (1) | eta (4) |
//   phi (6) | 0 (12).
// - eta index: the dictionary index of the cell (CellAtlasEtaIndex); phi index: the phi slice from phi = 0, growing with phi
//   on both sides, as in the ATLAS HITS ntuple; the edges carry the half-absorber shift (PhiShift, already in PhiBins).
// - time (LArBarrelCalculator, LArBarrelPresamplerCalculator: pre-step; EnergyCalculator, LArEndcapPresamplerCalculator,
//   LArHECWheelCalculator: mean of pre- and post-step): global time minus |r|/c of the same point, in ns.
// - energy: the deposit of the step in the liquid argon, with Birks' law (BirksLaw, BirksLArK).
// - time binning (option FreeRunningBinning; LArG4SimpleSD::getTimeBin, TimeBinType = Default): bin 0 for t < 0, bins of
//   2.5 ns up to 10 ns, of 5 ns up to 50 ns, of 25 ns up to 100 ns and one bin above; the deposits of a cell in the same
//   bin are summed, with the energy weighted mean time (LArHit::Add, finalize). No time window (the SD does not call
//   isInTime).
void CaloHitMaker::freeRunningLAr( SG::EventContext &ctx, const G4Step *step, int cell, int phiBin, float edep ) const
{
  SG::ReadHandle<CaloFreeRunningHitList> list( m_freeRunningListKey, ctx );
  if( !list.isValid() ){
    MSG_FATAL("It's not possible to retrieve the CaloFreeRunningHitList using this key: " << m_freeRunningListKey);
  }
  const double cLight = CLHEP::c_light;   // mm/ns
  const int nPhi = (int)m_nPhiBins;
  // phi slice from phi = 0: the bin of the -pi..pi grid (shifted by PhiShift) moved by half a turn
  const int phiIndex = ( phiBin + nPhi / 2 ) % nPhi;
  const int etaIndex = m_cellAtlasEtaIndex[cell];
  unsigned long long id32 = 0;
  int det = 0;
  if( m_atlasLArPart == 1 ){
    static const int beValues[6] = {-3, -2, -1, 1, 2, 3};
    int beIndex = -1;
    for( int k = 0; k < 6; ++k ) if( beValues[k] == m_atlasBarrelEc ) beIndex = k;
    if( beIndex < 0 ){ MSG_FATAL( "AtlasBarrelEc " << m_atlasBarrelEc << " is not a LArEM barrel_ec" ); }
    id32 = (1ULL << 29) | (3ULL << 26) | ((unsigned long long)beIndex << 23) | ((unsigned long long)m_atlasLArSampling << 21)
         | ((unsigned long long)m_atlasLArRegion << 18) | ((unsigned long long)etaIndex << 9) | ((unsigned long long)phiIndex << 1);
    det = ( std::abs(m_atlasBarrelEc) == 1 ) ? 1 : 2;
  }else{
    id32 = (1ULL << 29) | (4ULL << 26) | ((unsigned long long)(m_atlasBarrelEc > 0 ? 1 : 0) << 25)
         | ((unsigned long long)m_atlasLArSampling << 23) | ((unsigned long long)m_atlasLArRegion << 22)
         | ((unsigned long long)etaIndex << 18) | ((unsigned long long)phiIndex << 12);
    det = 3;
  }
  const long long cellID = (long long)( id32 << 32 );

  // time of the deposit (ns): pre-step in the barrel (EMB and barrel presampler), mean of pre and post elsewhere
  const G4StepPoint *preP = step->GetPreStepPoint(), *postP = step->GetPostStepPoint();
  double tglobal, mag;
  if( std::abs(m_atlasBarrelEc) == 1 && m_atlasLArPart == 1 ){
    tglobal = preP->GetGlobalTime() / ns;
    mag = preP->GetPosition().mag();
  }else{
    tglobal = 0.5 * ( preP->GetGlobalTime() + postP->GetGlobalTime() ) / ns;
    mag = ( 0.5 * ( preP->GetPosition() + postP->GetPosition() ) ).mag();
  }
  const double t = tglobal - mag / cLight;
  int timeBin = -1;   // -1: no binning (one entry per step)
  if( m_freeRunningBinning ){
    if     ( t < 0.   ) timeBin = 0;
    else if( t < 10.  ) timeBin = (int)( t / 2.5 );
    else if( t < 50.  ) timeBin = 4 + (int)( ( t - 10. ) / 5. );
    else if( t < 100. ) timeBin = 12 + (int)( ( t - 50. ) / 25. );
    else                timeBin = 14;
  }
  // nominal centre of the cell (with the half-absorber shift of its edges)
  const double phiCentre = std::remainder( 0.5 * ( m_phiBins[phiBin] + m_phiBins[phiBin+1] ), 2 * M_PI );
  list->addLAr( cellID, edep / MeV, t, tglobal, m_cellEta[cell], phiCentre, m_atlasLArSampling, m_atlasBarrelEc,
                m_atlasLArRegion, det, timeBin );
}

//!=====================================================================

// A step in the ATLAS FCal with its electrodes (F41 conserto 22), as the ATLAS simulation takes it: the hit of its tile and, with the
// free-running hits, LArHitFCAL (Athena, LArCalorimeter/LArG4/LArG4FCAL/src/LArFCALCalculatorBase.cc; copies and report in the F41
// notes of the group, c22_fcal_celulas/):
// - sensitive: only the liquid argon gaps of the module (LArG4SDToolConfig.py: LAr::FCAL::Module<m>::Gap); not the rods;
// - cell: the tile of the copy number of the gap (FCAL_ChannelMap::getTubeByCopyNumber), from the table LArFCalElectrodes of
//   the ATLAS geometry database (geometry/python/v2/FCAL.py);
// - identifier: channel_id(pos_neg, module, eta, phi) of LArFCAL_ID, pos_neg = +2 for the mid point of the step at z > 0 and -2
//   otherwise; the 32-bit compact identifier in the upper half of the 64-bit integer, with the bit layout read from the ATLAS
//   HITS ntuple (c22_bits_fcal_5k.py): LArCalorimeter 1 (3 bits) | part 5 (3) | pos_neg -2 -> 0, +2 -> 1 (1) | module - 1 (2) |
//   eta (6) | phi (4) | 0 (13);
// - energy: the deposit of the step with Birks' law (BirksLaw, BirksLArK = 0.0486 as LArG4FCALConfig.py, field 10 kV/cm); no
//   high voltage scale (FCALHVEnable is false by default);
// - time: in the hit of its tile (fcalFillHit), the ATLAS time of the liquid argon (larHitTime) with AtlasHitTime, the global time of
//   the pre-step point without it; in the free-running hits, the mean of the pre- and post-step global times minus |r|/c of the mid
//   point, in ns, with the time bins and sums of the other LAr (LArG4SimpleSD, TimeBinType Default; see freeRunningLAr) and no time
//   window.
void CaloHitMaker::fcalStep( SG::EventContext &ctx, const G4Step *step ) const
{
  const G4StepPoint *preP = step->GetPreStepPoint(), *postP = step->GetPostStepPoint();
  const G4VPhysicalVolume *pv = preP->GetPhysicalVolume();
  if( !pv || pv->GetLogicalVolume()->GetName() != m_fcalGapVolume ) return;
  if( m_activeEnergyOnly ){
    const G4Material *material = preP->GetMaterial();
    if( !material || material->GetName() != "liquidArgon" ) return;
  }
  const int copy = pv->GetCopyNo();
  if( copy < 0 || copy >= (int)m_fcalCopyEtaIndex.size() ){
    MSG_FATAL( "FCal module " << m_fcalModule << ": copy number " << copy << " without a cell" );
  }
  const float edep = m_birksLaw ? birksEnergy(step) : (float)step->GetTotalEnergyDeposit();
  if( edep <= 0 ) return;
  // hit of the normal chain: the ATLAS time of the liquid argon (AtlasHitTime) or the global time of the pre-step point
  fcalFillHit( ctx, m_fcalCopyEtaIndex[copy], m_fcalCopyPhiIndex[copy], edep,
               m_atlasHitTime ? (float)larHitTime( step ) : (float)( preP->GetGlobalTime() / ns ) );
  if( !m_freeRunningHits ) return;

  SG::ReadHandle<CaloFreeRunningHitList> list( m_freeRunningListKey, ctx );
  if( !list.isValid() ){
    MSG_FATAL("It's not possible to retrieve the CaloFreeRunningHitList using this key: " << m_freeRunningListKey);
  }
  const G4ThreeVector mid = 0.5 * ( preP->GetPosition() + postP->GetPosition() );
  const int posNeg = mid.z() > 0 ? 2 : -2;
  const unsigned long long id32 = (1ULL << 29) | (5ULL << 26) | ((unsigned long long)(posNeg > 0 ? 1 : 0) << 25)
                                | ((unsigned long long)(m_fcalModule - 1) << 23)
                                | ((unsigned long long)m_fcalCopyEtaIndex[copy] << 17)
                                | ((unsigned long long)m_fcalCopyPhiIndex[copy] << 13);
  const long long cellID = (long long)( id32 << 32 );
  const double tglobal = 0.5 * ( preP->GetGlobalTime() + postP->GetGlobalTime() ) / ns;
  const double t = tglobal - mid.mag() / CLHEP::c_light;
  int timeBin = -1;   // -1: no binning (one entry per step)
  if( m_freeRunningBinning ){
    if     ( t < 0.   ) timeBin = 0;
    else if( t < 10.  ) timeBin = (int)( t / 2.5 );
    else if( t < 50.  ) timeBin = 4 + (int)( ( t - 10. ) / 5. );
    else if( t < 100. ) timeBin = 12 + (int)( ( t - 50. ) / 25. );
    else                timeBin = 14;
  }
  // the module goes to the field sampling of the list (LArHitFCAL_module), pos_neg to side
  list->addLAr( cellID, edep / MeV, t, tglobal, m_fcalCopyEta[copy], m_fcalCopyPhi[copy], m_fcalModule, posNeg, 0, 4, timeBin );
}

//!=====================================================================

// The deposit of an FCal step or spot in the hit of its tile, in the bunch crossing of the global time of the pre-step point, as the
// other hits of the normal chain (CaloHit::fill)
void CaloHitMaker::fcalFillHit( SG::EventContext &ctx, int eta, int phi, float edep, float t ) const
{
  SG::ReadHandle<xAOD::CaloHitCollection> collection( m_collectionKey, ctx );
  if( !collection.isValid() ){
    MSG_FATAL("It's not possible to retrieve the CaloHitCollection using this key: " << m_collectionKey);
  }
  xAOD::CaloHit *hit = nullptr;
  if( !collection->retrieve( hash( 16 * eta + phi ), hit ) ){
    MSG_FATAL( "FCal module " << m_fcalModule << ": no hit for the tile (" << eta << ", " << phi << ")" );
  }
  hit->fillAt( t, 1*m_noiseStd, edep );
}

bool CaloHitMaker::isShowerSpot( const G4Step *step )
{
  return step->GetPreStepPoint()->GetTouchable() == nullptr;
}

// Cell of a point (x, y) in the frame of the module, in mm, as FCAL_ChannelMap::getTileID of the Athena release 23.0.14 used by the
// ATLAS production we compare with (copy in the F41 notes of the group, c23_chuveiros_congelados/fontes_athena/r23.0.14/): the tube of
// the hexagonal grid (tubeDx = spacing / 2, tubeDy = spacing * sqrt(3) / 2; spacing 7.5, 8.179 and 9.0 mm), the offset taken from the
// first tube of the map, the parity of the grid corrected as in Athena, and the tile of that tube; false if there is no tube there.
bool CaloHitMaker::fcalTileID( double x, double y, int &eta, int &phi ) const
{
  static const double spacing[3] = { 7.5, 8.179, 9.0 };
  const double tubeDx = spacing[m_fcalModule - 1] / 2., tubeDy = spacing[m_fcalModule - 1] * std::sqrt(3.) / 2.;
  int ktx = (int)( x / tubeDx );
  int kty = (int)( y / tubeDy );
  if( x < 0. ) ktx--;
  if( y < 0. ) kty--;
  const unsigned int firstId = m_fcalFirstTube;
  int ix = ktx + ( (int)( (firstId & 0xffff) - m_fcalFirstTubeX / tubeDx ) ) + 1;
  int iy = kty + ( (int)( (firstId >> 16) - m_fcalFirstTubeY / tubeDy ) ) + 1;
  const int isOddEven = ( ( (firstId >> 16) % 2 ) + ( firstId % 2 ) ) % 2;
  bool movex = false;
  if( ( iy % 2 ) != ( ( ix + isOddEven ) % 2 ) ){
    const double yc = y / tubeDy - kty - 0.5;
    if( std::fabs(yc) > 0.5 / std::sqrt(3) ){
      double xk = x / tubeDx - ktx;
      if( xk > 0.5 ) xk = 1 - xk;
      const double yn = 0.5 - xk * ( 1. / 3 );
      if( std::fabs(yc) > std::fabs(yn) ){
        if( yc > 0 ) iy++; else iy--;
      }else movex = true;
    }else movex = true;
    if( movex ){
      if( x / tubeDx - ktx > 0.5 ) ix++; else ix--;
    }
  }
  const unsigned int tubeID = ( (unsigned int)iy << 16 ) + (unsigned int)ix;
  auto it = m_fcalTubeMap.find( tubeID );
  if( it == m_fcalTubeMap.end() ) return false;
  eta = it->second.first; phi = it->second.second;
  return true;
}

// A spot of a frozen shower (F41 conserto 23; Athena FCALFastSimDedicatedSD::ProcessSpot, release 23.0.14): the spot of this
// maker's module and side (z inside the module), the cell by the position in the frame of the module (the global x and y: the
// electrodes of side C sit at the same x and y as those of side A, geometry/python/v1/FCAL.py), the energy of the spot as it comes
// (no Birks, weight 1), the time of the spot (already the shower time plus the global time of the particle minus |r|/c). Spots
// outside every module or outside every tile are dropped, as in Athena.
void CaloHitMaker::fcalSpot( SG::EventContext &ctx, const G4Step *step ) const
{
  const G4StepPoint *preP = step->GetPreStepPoint();
  const G4ThreeVector pos = preP->GetPosition();
  if( !( pos.z() > m_zMin && pos.z() <= m_zMax ) ) return;
  const double edep = step->GetTotalEnergyDeposit();
  if( edep <= 0 ) return;
  int etaIndex, phiIndex;
  if( !fcalTileID( (float)pos.x(), (float)pos.y(), etaIndex, phiIndex ) ) return;   // float, as Athena passes it
  // hit of the normal chain: the time of the spot is already the ATLAS time (AtlasHitTime); without it, the global time
  // (|r|/c added back), the convention of the other deposits
  const float tSpot = (float)( preP->GetGlobalTime() / ns );
  fcalFillHit( ctx, etaIndex, phiIndex, (float)edep,
               m_atlasHitTime ? tSpot : (float)( tSpot + pos.mag() / CLHEP::c_light ) );
  if( !m_freeRunningHits ) return;
  SG::ReadHandle<CaloFreeRunningHitList> list( m_freeRunningListKey, ctx );
  if( !list.isValid() ){
    MSG_FATAL("It's not possible to retrieve the CaloFreeRunningHitList using this key: " << m_freeRunningListKey);
  }
  const int posNeg = pos.z() > 0 ? 2 : -2;
  const unsigned long long id32 = (1ULL << 29) | (5ULL << 26) | ((unsigned long long)(posNeg > 0 ? 1 : 0) << 25)
                                | ((unsigned long long)(m_fcalModule - 1) << 23)
                                | ((unsigned long long)etaIndex << 17) | ((unsigned long long)phiIndex << 13);
  const long long cellID = (long long)( id32 << 32 );
  const double t = preP->GetGlobalTime() / ns;
  const double tglobal = t + pos.mag() / CLHEP::c_light;   // extra branch: the time without the -|r|/c of the ATLAS convention
  int timeBin = -1;
  if( m_freeRunningBinning ){
    if     ( t < 0.   ) timeBin = 0;
    else if( t < 10.  ) timeBin = (int)( t / 2.5 );
    else if( t < 50.  ) timeBin = 4 + (int)( ( t - 10. ) / 5. );
    else if( t < 100. ) timeBin = 12 + (int)( ( t - 50. ) / 25. );
    else                timeBin = 14;
  }
  const auto &c = m_fcalTileCentre.at( std::make_pair( etaIndex, phiIndex ) );
  // source 1: the hit of the FCALFastSimDedicatedSD, kept apart from the Geant4 steps of the same cell and bin (F41 conserto 28)
  list->addLAr( cellID, edep / MeV, t, tglobal, c.first, c.second, m_fcalModule, posNeg, 0, 4, timeBin, 1 );
}

//!=====================================================================

// Energy of the step after Birks' law, following the ATLAS simulation (Athena):
// - plastic scintillator (TileGeoG4SDCalc::BirkLaw): E / (1 + kB dE/dx), kB = 0.02002 g/(MeV cm2)
//   ("value updated for G4 10.6.p03"), second-order term 0, only for charged particles,
//   kB scaled by 7.2/12.6 for charge above 1;
// - liquid argon (LArG4BirksLaw): E (1 + k/F 1.51) / (1 + k/F (dE/dx)/rho), k = BirksLArK (0.05832; 0.0486 in the HEC,
//   as LArG4HECConfig.py),
//   rho = 1.396 g/cm3, F = 10 kV/cm (the constant field of the ATLAS barrel, presamplers and HEC),
//   with the correction for heavily ionising particles above 969 MeV/cm.
// Other materials are left unchanged.
float CaloHitMaker::birksEnergy( const G4Step *step ) const
{
  // the deposit times the weight of the track (1 unless a Russian roulette of the ATLAS settings acted; F41 conserto 24), before Birks,
  // as the ATLAS simulation does it (LAr calculators: GetTotalEnergyDeposit() * GetWeight(); TileGeoG4SDCalc): the saturation of a
  // track of weight 10 is computed with 10 times its dE/dx, as in ATLAS
  const double edep = step->GetTotalEnergyDeposit() * ( step->GetTrack() ? step->GetTrack()->GetWeight() : 1. );
  const double length = step->GetStepLength();
  const G4Material *material = step->GetPreStepPoint()->GetMaterial();
  if( !material || edep <= 0 || length <= 0 ) return (float)edep;
  const G4String &name = material->GetName();

  if( name == "PLASTIC SCINTILLATOR" ){
    const double charge = step->GetPreStepPoint()->GetCharge();
    if( charge == 0. ) return (float)edep;
    double kB = 0.02002 * g / (MeV * cm2);
    if( std::abs(charge) > 1.0 ) kB *= 7.2 / 12.6;
    const double dedx = edep / length / material->GetDensity();
    return (float)( edep / (1. + kB * dedx) );
  }

  if( name == "liquidArgon" ){
    const double dE = edep / MeV;
    const double dX = length / cm;
    if( dX < 1e-5 ) return (float)edep;
    const double kOverField = m_birksLArK / 10.;
    double dEdX = dE / dX;
    const double corrected = dE * (1 + kOverField * 1.51) / (1 + kOverField * dEdX / 1.396);
    if( dEdX > 12000.0 ) dEdX = 12000.0;
    const double kHIP = (dEdX > 969.) ? 0.000754 * dEdX + 0.2692 : 1.0;
    return (float)( corrected * kHIP * MeV );
  }

  return (float)edep;
}

//!=====================================================================

// Charge collection of the ATLAS EM end-cap (F41 conserto 29, --atlas-emec-charge-collection): the energy that the ATLAS simulation
// records for a step in the liquid argon of an EMEC wheel (Athena 23.0.14, LArCalorimeter/LArG4/LArG4EC/src/EnergyCalculator.cc,
// Process_Default with the default EnergyCorrection = 8), computed by the ported ATLAS code (geometry/LArG4EC, geometry/GeoSpecialShapes;
// copies of the sources and the validation against Athena in the F41 notes of the group, c29_emec_energia/):
// - frame: the pre- and post-step points are brought to the local frame of the ATLAS wheel (the frame of the liquid argon volume
//   LAr::EMEC::{Pos,Neg}::{Inner,Outer}Wheel, where FindIdentifier_Default takes them with GetTopTransform): z from the front face
//   of the wheel, |z| - (EmecFocalShift + dElecFocaltoWRP + dWRPtoFrontFace), the same front face as the cells (emecFindCell); on
//   side B the end-cap is rotated by 180 degrees around y (LArDetectorFactory.cxx: RotateY3D(180 deg)), so x changes sign. In the
//   geometry of the simulation of ATLAS-P2-RUN4-01-01-00 the wheels are at |z| = 3745 mm with no other rotation.
// - liquid argon of the accordion: the EMEC of Lorenzetti is made of planar layers, so the point may be where ATLAS has an absorber
//   or an electrode. The step is moved in phi, at the same r and z, into the liquid argon of the same fan period (option (b),
//   decided by Luciano): emecLArPhiShift gives the shift for the middle of the step and the same shift moves both points (rigid
//   shift, confirmed by Luciano on 15/10/2026); kEmecShiftEndpointsIndependently = true would move each point by its own shift.
// - Birks' law with the local field 0.01 HV / gap at the middle of the step (GetGapSize and the HV of HVHelper, HVEMECMap_v02.dat),
//   on the deposit times the weight of the track, with the step length (LArG4BirksLaw, k = 0.05832, LAr density 1.396 g/cm3);
// - the energy of the hit: CalculateChargeCollection1 (GetCurrent1) of the energy after Birks between the two points.
static constexpr bool kEmecShiftEndpointsIndependently = false;

// The transform from the global frame to the frame of the wheel composed as in the ATLAS simulation (decisions of Luciano of
// 15/10/2026: side B, then side A by the rule of following the ATLAS source), level by level as G4NavigationHistory does it
// (G4NavigationLevelRep: InverseProduct of the transform of the level above and G4AffineTransform(GetRotation(), GetTranslation()) of the
// placement; G4PVPlacement(G4Transform3D) keeps the inverse of the rotation, none when it is the identity), with the placements of the
// geometry of the simulation of ATLAS-P2-RUN4-01-01-00 (GeoModel, Geo2G4):
// - LAr::Endcap::Cryostat::MotherVolume: side A, LArPosition LARCRYO_EC_POS (translation z = +6734.5 mm, no rotation; LArPosition-10);
//   side B, LARCRYO_EC_NEG (z = -6734.5 mm) times GeoTrf::RotateY3D(180 deg) (LArDetectorFactory.cxx), the Eigen AngleAxis matrix
//   [[c, 0, s], [0, 1, 0], [-s, 0, c]] with c = cos(pi) = -1 and s = sin(pi) = 1.2246e-16 of the double pi;
// - EmecHecLAr and LAr::EMEC::Mother (LArPosition EMEC_POS and EMEC_NEG, zero): identity;
// - the wheel: refSystemTransform, TranslateZ(ZPLANE of EMEC::Mother - 3639.5 mm) = TranslateZ(-3050.5 - 3639.5 = -6690 mm) (CryoPcons-21-
//   HGTD), then TranslateZ(zWheelRefPoint + dWRPtoFrontFace = 3689.5 + 11 = 3700.5 mm) (EMECConstruction.cxx), one translation -2989.5 mm;
// - the world and the CALO envelope of the ATLAS simulation: identity (no offset in G4GeometryToolConfig.py).
// Valid for the geometry of --atlas-run4 (wheel front at |z| = 3745 mm).
static G4AffineTransform emecTopTransform( bool sideA )
{
  G4AffineTransform world;                                         // the world and the CALO envelope
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
  // Eigen::AngleAxisd(angle, UnitY).toRotationMatrix(), element by element
  const double cos1y = 1. - c;   // (1 - c) * axis.y()
  const CLHEP::HepRep3x3 rep( 0. * 0. + c,         0. * 1. - s * 0.,   0. * 0. + s * 1.,
                              0. * 1. + s * 0.,    cos1y * 1. + c,     cos1y * 0. - s * 0.,
                              0. * 0. - s * 1.,    cos1y * 0. + s * 0., 0. * 0. + c );
  const G4RotationMatrix placement( rep );
  const G4RotationMatrix frot = placement.inverse();   // G4PVPlacement(G4Transform3D): NewPtrRotMatrix(getRotation().inverse())
  G4AffineTransform cryostat;
  cryostat.InverseProduct( world, G4AffineTransform( &frot, G4ThreeVector( 0., 0., -6734.5 ) ) );
  G4AffineTransform emecHecLAr, emecMother, wheel;
  emecHecLAr.InverseProduct( cryostat, G4AffineTransform() );
  emecMother.InverseProduct( emecHecLAr, G4AffineTransform() );
  wheel.InverseProduct( emecMother, G4AffineTransform( G4ThreeVector( 0., 0., -6690. + 3700.5 ) ) );
  return wheel;
}

void CaloHitMaker::emecDiscardCount( bool inner, double energyBefore, bool discarded ) const
{
  std::lock_guard<std::mutex> lock( s_emecDiscardMutex );
  const int w = inner ? 1 : 0;
  ++s_emecSteps[w]; s_emecEnergy[w] += energyBefore;
  if( discarded ){ ++s_emecDiscardedSteps[w]; s_emecDiscardedEnergy[w] += energyBefore; }
}

bool CaloHitMaker::emecChargeEnergy( const G4Step *step, double &energy ) const
{
  const LArG4::EC::EnergyCalculator *calc = m_emecCalculator;
  const LArWheelCalculator *lwc = calc->calculator();
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
  // Process_Default
  G4double E = step->GetTotalEnergyDeposit() * ( step->GetTrack() ? step->GetTrack()->GetWeight() : 1. );
  try{
    const G4ThreeVector midpoint = ( p1 + p2 ) * 0.5;
    const G4double wholeStepLengthCm = step->GetStepLength() / cm;
    const G4double gap = calc->GapSize( midpoint );
    const G4double efield = 0.01 * calc->Voltage( midpoint ) / gap; // estimate Efield[KV/cm]
    E = calc->Birks( E, wholeStepLengthCm, efield );
    energy = calc->ChargeCollection( E, p1, p2 );
    return true;
  }catch( const std::exception &e ){
    // HVHelper::GetEtaSection throws when the point is outside the eta range of the HV sectors of the wheel (steps at the conical edges
    // of the planar slices of the wheels of Lorenzetti, beyond the cone of the ATLAS wheel). Decision of Luciano of 15/10/2026: the deposit
    // is discarded (there is no liquid argon of the ATLAS wheel there, so no ATLAS hit).
    static std::atomic<long> nExceptions{0};
    const long n = ++nExceptions;
    if( n <= 10 || ( n & (n - 1) ) == 0 )
      MSG_WARNING( "EMEC charge collection: " << e.what() << " for the step at local (" << p1.x() << ", " << p1.y() << ", "
                   << p1.z() << "); deposit discarded (" << n << " so far)" );
    return false;
  }
}

//!=====================================================================

// Shift in phi (rad) that brings the point p (local frame of the ATLAS wheel) into the liquid argon of its fan period, at the same r
// and z, preserving its fraction of the period (option (b) of the plan approved by Luciano; F41 conserto 29). At the (r, z) of the
// point, with the ported LArWheelCalculator of the absorbers and of the electrodes of the wheel:
// - the fan period is the phi interval between the neutral fibres of the two absorbers around the point (the nearest absorber, from
//   DistanceToTheNearestFan, and the next one on the side of the point);
// - the liquid argon of the period is made of two intervals: from the surface of the lower absorber (distance to its neutral fibre
//   equal to its half thickness, GetFanHalfThickness) to the surface of the electrode (distance to the electrode neutral fibre equal
//   to minus the electrode half thickness), and from the other surface of the electrode to the surface of the upper absorber; the
//   distances are those of DistanceToTheNeutralFibre, the same that decide inside and outside in the ATLAS wheel;
// - the fraction f of the point in the full period is mapped linearly onto the cumulated length of the two intervals.
// Each boundary is found by bisection in phi down to the resolution of a double (no tolerance). If a boundary is not bracketed (it
// should not happen) the point is not moved.
double CaloHitMaker::emecLArPhiShift( const CLHEP::Hep3Vector &p ) const
{
  const LArG4::EC::EnergyCalculator *calc = m_emecCalculator;
  const LArWheelCalculator *lwc = calc->calculator(), *elc = calc->electrodeCalculator();
  const double r = p.perp(), z = p.z(), phi = p.phi();
  const double step = lwc->GetFanStepOnPhi();
  const int nFans = lwc->GetNumberOfFans();
  auto at = [&]( double ph ){ return CLHEP::Hep3Vector( r * std::cos(ph), r * std::sin(ph), z ); };
  // signed distance to the neutral fibre of the fan of the calculator c rotated by theta (fan number fan)
  auto dist = [&]( const LArWheelCalculator *c, double theta, int fan, double ph ){
    CLHEP::Hep3Vector q = at( ph ); q.rotateZ( -theta ); return c->DistanceToTheNeutralFibre( q, fan ); };
  // bisection of f between lo and hi (opposite signs) down to the resolution of a double; NaN if not bracketed
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
  // the nearest absorber: its rotation and number; the period goes from the absorber below the point to the one above it
  CLHEP::Hep3Vector pa = p; int fa = 0;
  const double da = lwc->DistanceToTheNearestFan( pa, fa );
  const double theta = phi - pa.phi();
  const double thLo = ( da >= 0 ) ? theta : theta - step, thHi = thLo + step;
  const int fanLo = ( da >= 0 ) ? fa : ( fa + nFans - 1 ) % nFans, fanHi = ( fanLo + 1 ) % nFans;
  const double hA = lwc->GetFanHalfThickness(), hE = elc->GetFanHalfThickness();
  const double phA0 = root( [&]( double x ){ return dist( lwc, thLo, fanLo, x ); }, phi - step, phi );
  const double phA1 = root( [&]( double x ){ return dist( lwc, thHi, fanHi, x ); }, phi, phi + step );
  // the electrode between the two absorbers
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

//!=====================================================================

// standlone execute
StatusCode CaloHitMaker::execute( EventContext &/*ctx*/, int /*evt*/ ) const
{
  MSG_ERROR("This method can not be execute in standalone mode.");
  return StatusCode::FAILURE;
}

//!=====================================================================

StatusCode CaloHitMaker::post_execute( EventContext &/*ctx*/ ) const
{
  return StatusCode::SUCCESS;
}

//!=====================================================================

StatusCode CaloHitMaker::fillHistograms( EventContext &ctx ) const
{
  // the FCal makers have one eta bin and one phi bin (FCAL.py), so the eta x phi monitoring histogram is not filled
  if( isFCal() ) return StatusCode::SUCCESS;
  auto store = ctx.getStoreGateSvc();
  SG::ReadHandle<xAOD::CaloHitCollection> collection( m_collectionKey, ctx );

  if( !collection.isValid() ){
    MSG_FATAL("It's not possible to retrieve the CaloHitCollection using this key: " << m_collectionKey);
  }

  store->cd(m_histPath);

  
  for ( const auto& p : **collection.ptr() ){ 

    const auto *hit = p.second;
    
    {// Fill truth energy 2D histograms
      int x = store->hist2("hits_edep")->GetXaxis()->FindBin(hit->eta());
      int y = store->hist2("hits_edep")->GetYaxis()->FindBin(hit->phi());
      int bin = store->hist2("hits_edep")->GetBin(x,y,0);
      float energy = store->hist2("hits_edep")->GetBinContent( bin );
      store->hist2("hits_edep")->SetBinContent( bin, (energy + hit->edep()) );
    }
  }

  return StatusCode::SUCCESS;
}

//!=====================================================================

// Cell of the (r, z) boxes that contains the point (rmin < r <= rmax, zmin < z <= zmax), or -1
int CaloHitMaker::findCell( float radius, float z ) const
{
  for ( unsigned box = 0; box < m_cellBoxIndex.size(); ++box ){
    if( radius > m_cellBoxRMin[box] && radius <= m_cellBoxRMax[box] &&
        z > m_cellBoxZMin[box] && z <= m_cellBoxZMax[box] )
      return m_cellBoxIndex[box];
  }
  return -1;
}

//!=====================================================================

// Radius used to find the (r, z) box of a step. With CellRadiusModules = N > 0: the distance to the beam line measured
// on the axis of the module that contains phi, r cos(phi - phi_c), with modules of 2 pi / N from phi = 0 and phi_c
// the centre of the module. This is moduleY of the ATLAS HEC simulation (Athena, LArCalorimeter/LArG4/LArG4HEC/src/
// HECGeometry.cc, CalculateIdentifier: |y| of the step in the frame of its module), for 32 modules with the first
// one starting at phi = 0 (phi0 = 0 of the HEC in the ATLAS identifier dictionary). N = 0 (default): r.
float CaloHitMaker::cellRadius( float radius, float phi ) const
{
  if( m_cellRadiusModules <= 0 ) return radius;
  const double twoPi = 2 * M_PI, width = twoPi / m_cellRadiusModules;
  double phi0 = phi < 0 ? phi + twoPi : phi;
  int module = (int)std::floor( phi0 / width );
  if( module >= m_cellRadiusModules ) module = m_cellRadiusModules - 1;
  return (float)( radius * std::cos( phi0 - (module + 0.5) * width ) );
}

//!=====================================================================

// ATLAS-like EM end-cap (geometry/python/v1/EMEC.py, --atlas-emec). Compartment of the point (x, y, z), in mm, as in the
// ATLAS simulation (Athena, LArCalorimeter/LArG4/LArG4EC/src/EnergyCalculator.cc, FindIdentifier_Default):
// - the point is first required to be inside one of the volumes of the wheel of this maker (EmecWheel*); otherwise 0;
// - pforcell = (x, y, |z| - EmecFocalShift): the point seen from the electric focal point of its side (side B mirrored);
//   eta is its pseudorapidity (as CLHEP Hep3Vector::pseudoRapidity) and zf = |z| - EmecFocalShift;
// - the tables ZIW, ZSEP12, ZSEP23 come in 1e-4 cm and are converted as ATLAS does (emecZ);
// - inner wheel (compartments 1 and 2): ipad = int((eta - 2.5) / 0.1) within 0-6; compartment 1 if zf < ZIW[ipad], else 2;
// - outer wheel: ipad = int((eta - 1.4) / 0.025) within 0-43; if zf < ZSEP12[ipad] the compartment follows eta (> 2.4: 3,
//   > 2.0: 4, > 1.8: 5, > 1.5: 6, > 1.425: 7, else 10); else, if zf < ZSEP23[ipad / 2], 8 (eta > 1.425) or 11; else 9.
// When the compartment is that of this maker: eta index int(eta EmecEtaScale - EmecEtaOffset) within [0, EmecMaxEta],
// and the phi slice k of 2 pi / N from phi = 0 (N = number of phi bins), stored in the bin of the -pi..pi grid of the
// same slice, (k + N/2) mod N. The rules of the ATLAS simulation at the edges (high-voltage buses, kapton at the edges of
// the wheels, validhit = false) are not applied: the indices are kept within their limits as in ATLAS.
int CaloHitMaker::emecFindCell( double x, double y, double z, int &etaBin, int &phiBin ) const
{
  etaBin = -1; phiBin = -1;
  const double r = std::sqrt( x*x + y*y );
  bool inWheel = false;
  for ( unsigned box = 0; box < m_emecWheelRMin.size(); ++box ){
    if( r > m_emecWheelRMin[box] && r <= m_emecWheelRMax[box] && z > m_emecWheelZMin[box] && z <= m_emecWheelZMax[box] ){
      inWheel = true;
      break;
    }
  }
  if( !inWheel ) return 0;

  const double zf = std::abs(z) - m_emecFocalShift;
  const double mag = std::sqrt( x*x + y*y + zf*zf );
  double eta;
  if( mag == 0 ) eta = 0;
  else if( mag == zf ) eta = 1.0E72;
  else if( mag == -zf ) eta = -1.0E72;
  else eta = 0.5 * std::log( (mag + zf) / (mag - zf) );

  int compartment = 0;
  if( m_emecCompartment <= 2 ){ // inner wheel
    int ipad = (int)( (eta - 2.5) / 0.1 );
    if( ipad < 0 ) ipad = 0;
    if( ipad > 6 ) ipad = 6;
    compartment = ( zf < emecZ(m_emecZInner[ipad]) ) ? 1 : 2;
  }else{ // outer wheel
    int ipad = (int)( (eta - 1.4) / 0.025 );
    if( ipad < 0 ) ipad = 0;
    if( ipad > 43 ) ipad = 43;
    if( zf < emecZ(m_emecZSep12[ipad]) ){
      if     ( eta > 2.4   ) compartment = 3;
      else if( eta > 2.0   ) compartment = 4;
      else if( eta > 1.8   ) compartment = 5;
      else if( eta > 1.5   ) compartment = 6;
      else if( eta > 1.425 ) compartment = 7;
      else                   compartment = 10;
    }else if( zf < emecZ(m_emecZSep23[ipad/2]) ){
      compartment = ( eta > 1.425 ) ? 8 : 11;
    }else{
      compartment = 9;
    }
  }
  if( compartment != m_emecCompartment ) return compartment;

  etaBin = (int)( eta * (double)m_emecEtaScale - (double)m_emecEtaOffset );
  if( etaBin < 0 ) etaBin = 0;
  if( etaBin > m_emecMaxEta ) etaBin = m_emecMaxEta;

  const int nPhi = (int)m_phiBins.size() - 1;
  // phi edges shifted by the half absorber of the ATLAS readout geometry (PhiShift; the PhiBins come shifted the same way)
  double phi = std::atan2( y, x ) - m_phiShift;
  while( phi < 0 ) phi += 2 * M_PI;
  while( phi >= 2 * M_PI ) phi -= 2 * M_PI;
  int k = (int)std::floor( phi / ( 2 * M_PI / nPhi ) );
  if( k >= nPhi ) k = nPhi - 1;
  phiBin = ( k + nPhi / 2 ) % nPhi;
  return compartment;
}

//!=====================================================================

// ATLAS-like barrel EM and presampler cells (geometry/python/v1/ECAL.py, --atlas-emb-cells). End-cap presampler (EmbMode
// = 2): as in the ATLAS simulation (LArCalorimeter/LArG4/LArG4EC/src/PresamplerGeometry.cc, CalculateIdentifier),
// etaBin = int(|eta| * 40 - 60), 12 -> 11 when |eta| < 1.801, kept if 0-11. Barrel presampler (EmbMode = 1, EmbSampling = 0):
// int(|eta|/0.025), 0-60 (the ATLAS simulation finds it from the electrode gap of each module, LArBarrelPresamplerGeometry;
// not modelled). Barrel EM (EmbMode = 1, EmbSampling 1-3): cell of the point (x, y, z), in mm, for the
// sampling (EmbSampling) and region (EmbRegion) of this maker, with the index formulas of the ATLAS simulation (Athena,
// LArCalorimeter/LArG4/LArG4Barrel/src/LArBarrelGeometry.cxx, CalculateIdentifier), kept only within the regions of the
// ATLAS identifier dictionary (IdDictLArCalorimeter):
// - eta: pseudorapidity of the point seen from the origin (as CLHEP Hep3Vector::pseudoRapidity); a = |eta|;
// - region 0 (a < 1.4): EMB1 strip int(a/0.025*8.), indices 1-447 (the strip 0 does not exist, inactive in ATLAS);
//   EMB2 int(a/0.025), 0-55; EMB3 int(a/0.025)/2, 0-26;
// - region 1 (1.4 <= a < 1.475): EMB1 int((a - 1.4)/0.025), 0-2; EMB2 the single cell 0; no EMB3;
// - otherwise, or when the index falls outside the region, -1: the step is not kept (above |eta| = 1.475 the ATLAS
//   simulation marks it inactive).
// The cell is the index minus the first index of the region. The sampling is the volume of the maker: the radial
// boundaries of ATLAS between the samplings and its rules at the edges of the barrel are not applied.
// ATLAS-like barrel presampler (EmbMode = 3, F41 conserto 17c): the cell from the gap of the electrode, as in the ATLAS
// simulation (Athena, LArCalorimeter/LArG4/LArG4Barrel/src/LArBarrelPresamplerGeometry.cxx, findCell, and the module table of
// LArGeoBarrel/src/BarrelPresamplerConstruction.cxx): module from the first cathode of each module, gap from the distance in
// z to the first cathode corrected by the tilt of the electrodes, cell = gap / gaps per cell (8 cells in modules 0-6, 5 in
// module 7, 18 gaps per cell there), plus the cells of the previous modules. The distance to the middle of the active layer
// is r - PsbR0 (the ATLAS code uses the normal of the flat sector; the Lorenzetti layer is a cylinder). -1 outside the modules.
int CaloHitMaker::psbGapCell( double x, double y, double z ) const
{
  static const double mod[8][6] = { {286.4, 56, 56, -25., 4.987, 4.2}, {295.74, 64, 64, -12., 4.621, 0.3},
                                    {321.1, 72, 72, 0., 4.46, 0.9}, {356.8, 80, 80, 0., 4.46, 0.9},
                                    {404.8, 88, 88, 0., 4.6, 0.9}, {478.4, 104, 104, 0., 4.6, 0.95},
                                    {563.2, 128, 128, 0., 4.4, 1.05}, {380.6, 86, 87, 0., 4.4, 0.95} };
  static const double cmm = 1 - 0.0026, eps = 0.007, zmin = 3.0, cathode = 0.270;
  static double endModule[8], firstCathode[8], pitch[8], tiltTan[8];
  static int ncell[8], ngap[8];
  static const bool init = [](){
    for( int i = 0; i < 8; ++i ){
      endModule[i] = (i == 0 ? zmin : endModule[i-1]) + (mod[i][0]*cmm + 2*eps) + eps;
      firstCathode[i] = (i == 0 ? zmin : endModule[i-1]) + mod[i][5]*cmm + cathode*cmm/2. + 2*eps;
      pitch[i] = mod[i][4]*cmm;
      tiltTan[i] = std::tan( mod[i][3]*M_PI/180. );
      ncell[i] = (i < 7) ? 8 : 5;
      ngap[i] = (i < 7) ? (int)( (mod[i][1] + 0.1)/ncell[i] ) : 18;
    }
    return true;
  }();
  (void)init;
  const double z2 = std::fabs( z );
  if( z2 < zmin || z2 > endModule[7] ) return -1;
  int module = 0;
  for( int i = 1; i < 8; ++i ){
    if( firstCathode[i] >= z2 ) break;
    module++;
  }
  const double dist = std::sqrt( x*x + y*y ) - m_psbR0;
  double deltaz = z2 - ( firstCathode[module] + dist*tiltTan[module] );
  if( deltaz < 0 ){
    if( module > 0 ){
      module--;
      deltaz = z2 - ( firstCathode[module] + dist*tiltTan[module] );
    }else{
      deltaz = 0;
    }
  }
  const int gap = (int)( deltaz/pitch[module] );
  int etaBin = gap/ngap[module];
  if( etaBin >= ncell[module] ) etaBin = ncell[module] - 1;
  for( int i = 0; i < module; ++i ) etaBin += ncell[i];
  if( etaBin < 0 || etaBin > 60 ) return -1;
  return etaBin;
}


int CaloHitMaker::embFindCell( double x, double y, double z ) const
{
  if( m_embMode == 3 ) return psbGapCell( x, y, z );
  if( m_embMode == 2 && m_embZShift != 0 ) z = std::copysign( std::fabs(z) - m_embZShift, z );
  const double mag = std::sqrt( x*x + y*y + z*z );
  double eta;
  if( mag == 0 ) eta = 0;
  else if( mag == z ) eta = 1.0E72;
  else if( mag == -z ) eta = -1.0E72;
  else eta = 0.5 * std::log( (mag + z) / (mag - z) );
  const double aeta = std::fabs( eta );
  const double deta = 0.025, etaMaxS1 = 1.4, etaMax = 1.475;
  int ieta = -1, first = 0, last = -1;
  if( m_embMode == 2 ){
    ieta = (int)( aeta * 40. - 60. );
    if( ieta == 12 && aeta < 1.801 ) ieta = 11;
    first = 0; last = 11;
  }else if( m_embSampling == 0 ){
    if( !(aeta < 1.525) ) return -1;
    ieta = (int)( aeta / deta ); first = 0; last = 60;
  }else if( m_embRegion == 0 ){
    if( !(aeta < etaMaxS1) ) return -1;
    if     ( m_embSampling == 1 ){ ieta = (int)( aeta / deta * 8. );        first = 1; last = 447; }
    else if( m_embSampling == 2 ){ ieta = (int)( aeta / deta );             first = 0; last = 55;  }
    else if( m_embSampling == 3 ){ ieta = ( (int)( aeta / deta ) ) / 2;     first = 0; last = 26;  }
  }else if( m_embRegion == 1 ){
    if( !(aeta >= etaMaxS1 && aeta < etaMax) ) return -1;
    if     ( m_embSampling == 1 ){ ieta = (int)( (aeta - etaMaxS1) / deta ); first = 0; last = 2; }
    else if( m_embSampling == 2 ){ ieta = 0;                                 first = 0; last = 0; }
  }
  if( ieta < first || ieta > last ) return -1;
  return ieta - first;
}

//!=====================================================================

// ATLAS-like barrel EM with the sampling of the ATLAS simulation (F41 conserto 18). Copy of the public ATLAS code (Athena, Apache
// 2.0; copies in the F41 notes of the group): LArBarrelCalculator::FiducialCuts and Geometry::SampSeg of LArG4Barrel/src/
// LArBarrelGeometry.cxx, with the boundaries Rmax1 and Rmax2 of LArBarrelSampling.h (EmbAtlasSampling.h). The point is taken in
// the half-barrel frame as |z| and |eta| (eta seen from the origin, as embFindCell). Constants: LArEMBRadiusInnerAccordion
// 1500.024 mm, LArEMBFiducialRmax 1960 mm and LArEMBMaxEtaAcceptance 1.475 (BarrelGeometry RIN_AC, ROUT_AC and ETACUT of the
// ATLAS geometry database, tag BarrelGeometry-03); LArEMBfiducialMothZmin 4 mm and LArEMBfiducialMothZmax 3150 mm (BarrelLongDiv,
// not in the public copies: the values of the comments of LArBarrelGeometry.cxx and LArBarrelCalculator.cxx, "currently 3150,
// should be changed in database to become 3164"); R_min_highz 1548 mm, 7 mm of readout strips at the edges, 1.1 mm inactive
// between S1 and S2, as in SampSeg. Returns 1 for an active point, with the region (0, 1), sampling (1-3) and eta index of the
// dictionary; 0 otherwise (the ATLAS simulation drops the step: cellID = 0, or calibration hits outside the fiducial region).
int CaloHitMaker::embSampSeg( double x, double y, double z, int &iregion, int &isampling, int &ieta ) const
{
  using EmbAtlasSampling::Rmax1;
  using EmbAtlasSampling::Rmax2;
  static const double Eta_max = 1.475, R_min_acc = 1500.024, R_max_acc = 1960., Z_min_acc = 4., Z_max_acc = 3150.;
  static const double R_min_highz = 1548., deltaz = 7., Dr_s12 = 1.1, Eta_max_s1 = 1.4, Eta_max_s3 = 1.325, deta = 0.025;
  static const double zmax1 = Z_max_acc - deltaz, zmax2 = Z_max_acc - 2.*deltaz, zmax3 = Z_max_acc - 3.*deltaz,
                      zmax4 = Z_max_acc - 4.*deltaz, zmax5 = Z_max_acc - 5.*deltaz, zmax6 = Z_max_acc - 6.*deltaz,
                      zmax7 = Z_max_acc - 7.*deltaz;
  static const double rmax1 = R_max_acc - deltaz, rmax2 = R_max_acc - 2.*deltaz, rmax3 = R_max_acc - 3.*deltaz,
                      rmax4 = R_max_acc - 4.*deltaz;
  static const double Z_max_lowr = std::sinh(Eta_max) * R_min_acc;
  static const double dzdr = (Z_max_acc - Z_max_lowr) / (R_min_highz - R_min_acc);

  iregion = -1; isampling = -1; ieta = -1;
  const double radius = std::sqrt( x*x + y*y );
  const double mag = std::sqrt( x*x + y*y + z*z );
  const double az = std::fabs( z );
  if( mag == 0 || mag == az ) return 0;
  const double aeta = 0.5 * std::log( (mag + az) / (mag - az) );

  // LArBarrelCalculator::FiducialCuts
  if( radius < R_min_acc || radius > R_max_acc || aeta > Eta_max || az < Z_min_acc || az > Z_max_acc ) return 0;

  // Geometry::SampSeg
  int iactive = 1;
  if( aeta < Eta_max_s1 ){
    const int istrip = (int)( aeta / deta * 8. );
    if( istrip < 0 || istrip >= 448 ) return 0;
    const double r12 = Rmax1[istrip];
    const int imid = (int)( aeta / deta );
    if( imid < 0 || imid >= 56 ) return 0;
    const double r23 = Rmax2[imid];
    iregion = 0;
    if( radius <= r12 ){
      isampling = 1; ieta = istrip;
      if( ieta == 0 ) iactive = 0;
    }else if( radius < (r12 + Dr_s12) ){
      isampling = 1; ieta = istrip; iactive = 0;
    }else{
      if( aeta < Eta_max_s3 ){
        if( radius <= r23 ){
          isampling = 2; ieta = imid;
        }else{
          if     ( az > zmax1 ){ isampling = 2; ieta = 55; }
          else if( az > zmax2 ){ isampling = 2; ieta = 54; }
          else if( az > zmax3 ){ isampling = 2; ieta = 53; }
          else if( az > zmax4 ){ isampling = 3; ieta = 26; }
          else if( aeta < 1.3 && az > zmax5 ){ isampling = 2; ieta = 52; }
          else if( aeta < 1.3 && az > zmax6 ){ isampling = 2; ieta = 51; }
          else if( radius > rmax4 && az < zmax5 && aeta > 1.2 ){
            if     ( radius > rmax1 ){ isampling = 2; ieta = 51; }
            else if( radius > rmax2 ){ isampling = 3; ieta = 25; }
            else if( radius > rmax3 ){
              if( az < zmax7 ){ isampling = 2; ieta = 50; }
              else            { isampling = 3; ieta = 25; }
            }else{
              if( aeta < 1.25 ){ isampling = 2; ieta = 49; }
              else             { isampling = 3; ieta = 25; }
            }
          }else{
            isampling = 3; ieta = imid / 2;
          }
        }
        // energy deposited along the readout strips across the back goes to the middle
        if( isampling == 3 && az < zmax4 && ( radius < rmax4 || aeta < 1.2 ) ){
          const double etastr = ( imid % 2 == 0 ) ? 0.025 * imid : 0.025 * ( imid + 1 );
          const double delta = radius * ( std::sinh(etastr) - std::sinh(aeta) ) / std::cosh(etastr);
          double deltastr;
          if      ( aeta < 0.475 ) deltastr = 1.5;
          else if ( aeta < 0.80  ) deltastr = 2.75;
          else if ( aeta < 0.85  ) deltastr = 1.5;
          else if ( aeta < 1.1   ) deltastr = 2.75;
          else                     deltastr = 3.25;
          if( std::fabs(delta) < deltastr ){ isampling = 2; ieta = imid; }
        }
      }else{
        isampling = 2; ieta = imid;
        if     ( az > zmax1 ) ieta = 55;
        else if( az > zmax2 && aeta < 1.375 ) ieta = 54;
      }
    }
  }
  if( aeta >= Eta_max_s1 && aeta < Eta_max ){
    const double r12 = Rmax1[447];
    const double r23 = Z_max_acc / std::sinh(aeta);
    const double zmax = Z_max_lowr + dzdr * ( radius - R_min_acc );
    iregion = 1;
    if( radius <= r12 ){
      isampling = 1; ieta = (int)( (aeta - Eta_max_s1) / deta );
      if( az > zmax ) iactive = 0;
    }else if( radius < (r12 + Dr_s12) ){
      isampling = 1; ieta = (int)( (aeta - Eta_max_s1) / deta ); iactive = 0;
    }else if( radius <= r23 ){
      isampling = 2; ieta = 0;
      if( az > zmax ) iactive = 0;
    }else{
      isampling = 2; ieta = 0; iactive = 0;
    }
  }
  if( aeta > Eta_max ) iactive = 0;
  if( az > Z_max_acc || radius > R_max_acc || radius < R_min_acc || aeta > Eta_max ) iactive = 0;
  return iactive;
}

//!=====================================================================

int CaloHitMaker::find( const std::vector<float> &vec, float value) const
{
  auto binIterator = std::adjacent_find( vec.begin(), vec.end(), [=](float left, float right){ return left < value and value <= right; }  );
  if ( binIterator == vec.end() ) return -1;
  return  binIterator - vec.begin();
}

int CaloHitMaker::findPhi( float phi ) const
{
  int bin = find( m_phiBins, phi );
  if( bin < 0 ) bin = find( m_phiBins, phi + 2 * M_PI );
  if( bin < 0 ) bin = find( m_phiBins, phi - 2 * M_PI );
  return bin;
}

//!=====================================================================
/*
class CaloSampling(EnumStringification):
    PSB       = 0
    PSE       = 1
    EMB1      = 2
    EMB2      = 3
    EMB3      = 4
    TileCal1  = 5
    TileCal2  = 6
    TileCal3  = 7
    TileExt1  = 8
    TileExt2  = 9
    TileExt3  = 10
    EMEC1     = 11
    EMEC2     = 12
    EMEC3     = 13
    HEC1      = 14
    HEC2      = 15
    HEC3      = 16
    HEC0      = 60   (ATLAS-like HEC, --atlas-hec)
    FCAL1-3   = 61-63 (ATLAS FCal cells, --atlas-fcal-cells)
*/
unsigned long int CaloHitMaker::hash(unsigned bin) const
{
  // NOTE: Max of 4,294,967,295 for unsigned long int (10 digits)

  // two for sammpling+side (0-99), one for segment (0-9) and six for bin index (0-999999), 9 digits
  if(m_zMin > 0){ // Right side 
    return ( (m_sampling + 1*17 ) * 1e7 + m_segment * 1e6 + bin);
  }else if(m_zMax < 0){// Left side
    return ( (m_sampling + 2*17 ) * 1e7 + m_segment * 1e6 + bin);
  }else{ // Center (barrel)
    return ( (m_sampling + 0*17 ) * 1e7 + m_segment * 1e6 + bin);
  }
}
