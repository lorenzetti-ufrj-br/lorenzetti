
#include "CaloFreeRunningHitWriter.h"
#include "EventInfo/EventInfoContainer.h"
#include "TTree.h"
#include <string>
#include <vector>
#include <cstring>
#include <cstdint>

using namespace Gaugi;
using namespace SG;


namespace {

  /*
   * Branch buffers of one ATLAS-like hit container (TileCalHit_*, LArHitEMB_*, ...).
   *
   * Booking and linking follow the RootStreamHITMaker pattern: the tree is created once
   * per thread in bookHistograms and, at every event, fresh buffers are attached with
   * SetBranchAddress, filled and released after TTree::Fill. The algorithm object is
   * shared by the Geant4 threads, so no buffer lives in the algorithm itself.
   */
  struct Container {

    std::string prefix;
    std::vector<std::string> idNames;   // container specific integer branches, in order

    std::vector<long long> *cellID;
    std::vector<double>    *energy;
    std::vector<double>    *time;
    std::vector<double>    *tglobal;
    std::vector<double>    *eta;
    std::vector<double>    *phi;
    std::vector<int>       *ids[4];
    bool withTglobal = true;   // false in the format of the ATLAS HITS ntuple (F41 conserto 25)

    Container( std::string p, std::vector<std::string> names ) : prefix(p), idNames(names)
    {
      cellID  = new std::vector<long long>();
      energy  = new std::vector<double>();
      time    = new std::vector<double>();
      tglobal = new std::vector<double>();
      eta     = new std::vector<double>();
      phi     = new std::vector<double>();
      for (int k=0; k<4; ++k) ids[k] = new std::vector<int>();
    }

    Container( const Container & ) = delete;
    Container& operator=( const Container & ) = delete;

    ~Container()
    {
      delete cellID; delete energy; delete time; delete tglobal; delete eta; delete phi;
      for (int k=0; k<4; ++k) delete ids[k];
    }

    std::string name( std::string leaf ) const { return prefix + "_" + leaf; }

    // create the branches (once per tree)
    void book( TTree *tree )
    {
      tree->Branch( name("cellID").c_str()  , cellID  );
      tree->Branch( name("energy").c_str()  , energy  );
      tree->Branch( name("time").c_str()    , time    );
      if( withTglobal ) tree->Branch( name("tglobal").c_str() , tglobal );
      tree->Branch( name("eta").c_str()     , eta     );
      tree->Branch( name("phi").c_str()     , phi     );
      for (size_t k=0; k<idNames.size(); ++k)
        tree->Branch( name(idNames[k]).c_str(), ids[k] );
    }

    // attach these buffers to the existing branches (every event)
    void link( TTree *tree )
    {
      tree->SetBranchAddress( name("cellID").c_str()  , &cellID  );
      tree->SetBranchAddress( name("energy").c_str()  , &energy  );
      tree->SetBranchAddress( name("time").c_str()    , &time    );
      if( withTglobal ) tree->SetBranchAddress( name("tglobal").c_str() , &tglobal );
      tree->SetBranchAddress( name("eta").c_str()     , &eta     );
      tree->SetBranchAddress( name("phi").c_str()     , &phi     );
      for (size_t k=0; k<idNames.size(); ++k)
        tree->SetBranchAddress( name(idNames[k]).c_str(), &ids[k] );
    }

    void push( long long id, double e, double t, double tg, double et, double ph,
               int i0=0, int i1=0, int i2=0, int i3=0 )
    {
      cellID->push_back(id);
      energy->push_back(e);
      time->push_back(t);
      tglobal->push_back(tg);
      eta->push_back(et);
      phi->push_back(ph);
      int v[4] = {i0, i1, i2, i3};
      for (size_t k=0; k<idNames.size(); ++k) ids[k]->push_back(v[k]);
    }
  };

  // The persistent LAr hit of the ATLAS HITS (LArHitContainerCnv_p2 with CxxUtils Compressor, release 23.0.14; copies in the F41 notes of
  // the group, c19_lar_cellid_flag/fontes_athena/): energy reduced to 18 bits with sign (Compressor::reduce, 9 bits of mantissa, rounded)
  // and time to the 16 upper bits of the float (Compressor::reduceToUS, rounded), read back as float.
  float atlasCompressEnergy( float value )
  {
    uint32_t u; std::memcpy( &u, &value, 4 );
    const int bshift = 32 - 18;
    const uint32_t rounding = 1u << (bshift - 1);
    const uint32_t vmax = (0x7f7u << 20) | (0x000fffffu ^ rounding);
    const uint32_t in = ( (u & 0x7fffffffu) > vmax ) ? (u >> bshift) : ((u + rounding) >> bshift);
    const uint32_t back = in << bshift;
    float out; std::memcpy( &out, &back, 4 );
    return out;
  }
  float atlasCompressTime( float value )
  {
    uint32_t u; std::memcpy( &u, &value, 4 );
    const uint32_t in = ( (u & 0x7fffffffu) > 0x7f7f7fffu ) ? (u >> 16) : ((u + 0x8000u) >> 16);
    const uint32_t back = (in & 0xffffu) << 16;
    float out; std::memcpy( &out, &back, 4 );
    return out;
  }
  // LArHitFilter of FilterHit_tf (LArHitFilter.cxx:14-32, 140-215): keeps a LAr hit when its (compressed) energy is above the cut of
  // its table and layer. EMB uses the table ical 0 and EMEC, HEC and FCAL the table ical 1, and the layer of every one of them is
  // LArEM_ID::sampling of its identifier, the bits 22-21 of the compact identifier. Defects of ATLAS kept on purpose (notes of the
  // group, achados_athena_para_reportar.md): for the HEC this field is (region << 1) | (eta >> 3) and for the FCAL the two upper bits of
  // the eta index of the tile, not their layers.
  bool atlasFilterKeeps( int det, long long cellID, float energy )
  {
    static const double cut[2][4] = { {0.05, 0.2, 0.1, 0.1}, {0.05, 0.1, 0.05, 0.05} };
    const unsigned long long id32 = ( (unsigned long long)cellID ) >> 32;
    const int layer = (int)( (id32 >> 21) & 3 );
    return energy > cut[ det == 1 ? 0 : 1 ][ layer ];
  }
}


CaloFreeRunningHitWriter::CaloFreeRunningHitWriter( std::string name ) :
  IMsgService(name),
  Algorithm()
{
  declareProperty( "InputListKey"   , m_inputListKey="FreeRunningHits"  );
  declareProperty( "InputEventKey"  , m_inputEventKey="Events"          );
  declareProperty( "NtupleName"     , m_ntupleName="CollectionTree"     );
  declareProperty( "OutputLevel"    , m_outputLevel=1                   );
  // the format of the ATLAS HITS ntuple (F41 conserto 25): LAr compressed and filtered as FilterHit_tf, no tglobal branches
  declareProperty( "AtlasFormat"    , m_atlasFormat=false               );
}

//!=====================================================================

StatusCode CaloFreeRunningHitWriter::initialize()
{
  CHECK_INIT();
  setMsgLevel( (MSG::Level)m_outputLevel );
  MSG_INFO("Input List Key: "  << m_inputListKey);
  MSG_INFO("Input Event Key: " << m_inputEventKey);
  MSG_INFO("Ntuple Name: "     << m_ntupleName);
  return StatusCode::SUCCESS;
}

//!=====================================================================

StatusCode CaloFreeRunningHitWriter::finalize()
{
  return StatusCode::SUCCESS;
}

//!=====================================================================

StatusCode CaloFreeRunningHitWriter::bookHistograms( SG::EventContext &ctx ) const
{
  auto store = ctx.getStoreGateSvc();
  store->cd();

  TTree *tree = new TTree( m_ntupleName.c_str(), "" );

  int eventNumber = 0;
  tree->Branch( "EventNumber", &eventNumber, "EventNumber/I" );

  // Same branch names as the ATLAS flat HITS ntuple, plus tglobal (extra)
  Container tile("TileCalHit", {"sampling", "side", "module", "tower"});
  Container emb ("LArHitEMB" , {"region", "sampling", "barrel_ec"});
  Container emec("LArHitEMEC", {"region", "sampling", "barrel_ec"});
  Container hec ("LArHitHEC" , {"region", "sampling", "pos_neg"});
  Container fcal("LArHitFCAL", {"module"});
  for( Container *c : {&tile, &emb, &emec, &hec, &fcal} ) c->withTglobal = !m_atlasFormat;
  tile.book(tree);
  emb.book(tree);
  emec.book(tree);
  hec.book(tree);
  fcal.book(tree);

  // the booking buffers die here; every event attaches its own
  tree->ResetBranchAddresses();

  store->add( tree );
  return StatusCode::SUCCESS;
}

//!=====================================================================

StatusCode CaloFreeRunningHitWriter::pre_execute( EventContext &/*ctx*/ ) const
{
  return StatusCode::SUCCESS;
}

//!=====================================================================

StatusCode CaloFreeRunningHitWriter::execute( EventContext &/*ctx*/, const G4Step * /*step*/ ) const
{
  return StatusCode::SUCCESS;
}

//!=====================================================================

StatusCode CaloFreeRunningHitWriter::execute( EventContext &/*ctx*/, int /*evt*/ ) const
{
  return StatusCode::SUCCESS;
}

//!=====================================================================

StatusCode CaloFreeRunningHitWriter::post_execute( EventContext &/*ctx*/ ) const
{
  return StatusCode::SUCCESS;
}

//!=====================================================================

StatusCode CaloFreeRunningHitWriter::fillHistograms( EventContext &ctx ) const
{
  return serialize(ctx);
}

//!=====================================================================

StatusCode CaloFreeRunningHitWriter::serialize( EventContext &ctx ) const
{
  MSG_DEBUG("Serialize free-running hits...");
  auto store = ctx.getStoreGateSvc();
  store->cd();
  TTree *tree = store->tree(m_ntupleName);
  if ( !tree ){
    MSG_FATAL("It's not possible to retrieve the tree " << m_ntupleName << " from the store");
  }

  // EventNumber
  int eventNumber = -1;
  {
    SG::ReadHandle<xAOD::EventInfoContainer> event(m_inputEventKey, ctx);
    if( event.isValid() && !(**event.ptr()).empty() ){
      eventNumber = (**event.ptr()).front()->eventNumber();
    }else{
      MSG_WARNING( "It's not possible to read the xAOD::EventInfoContainer using this key " << m_inputEventKey << ". EventNumber set to -1." );
    }
  }
  tree->SetBranchAddress( "EventNumber", &eventNumber );

  Container tile("TileCalHit", {"sampling", "side", "module", "tower"});
  Container emb ("LArHitEMB" , {"region", "sampling", "barrel_ec"});
  Container emec("LArHitEMEC", {"region", "sampling", "barrel_ec"});
  Container hec ("LArHitHEC" , {"region", "sampling", "pos_neg"});
  Container fcal("LArHitFCAL", {"module"});   // filled with --atlas-fcal-cells (F41 conserto 22); empty without it
  for( Container *c : {&tile, &emb, &emec, &hec, &fcal} ) c->withTglobal = !m_atlasFormat;
  tile.link(tree);
  emb.link(tree);
  emec.link(tree);
  hec.link(tree);
  fcal.link(tree);

  SG::ReadHandle<CaloFreeRunningHitList> list(m_inputListKey, ctx);
  if( !list.isValid() ){
    MSG_FATAL("It's not possible to read the CaloFreeRunningHitList from this Context using this key " << m_inputListKey );
  }

  double etot = 0;
  std::vector<double> tglobal = list->tglobal();
  std::vector<double> hitTime = list->hitTime();
  // order of the entries: as filled, except that the FCAL entries of the frozen shower spots go after those of the Geant4 steps, as
  // the FCALFastSimDedicatedSD writes after the SDs of the modules in SDWrapper::EndOfAthenaEvent (F41 conserto 28)
  std::vector<size_t> order;
  order.reserve( list->size() );
  for ( size_t i = 0; i < list->size(); ++i ) if( !( list->det()[i] == 4 && list->source()[i] == 1 ) ) order.push_back( i );
  for ( size_t i = 0; i < list->size(); ++i ) if(    list->det()[i] == 4 && list->source()[i] == 1   ) order.push_back( i );
  for ( size_t i : order )
  {
    const int det = list->det()[i];
    if( det == 0 ){
      // tile hits (per PMT), with the ATLAS identifier fields filled by CaloHitMaker::freeRunningTile
      tile.push( list->cellID()[i], list->energy()[i], hitTime[i], tglobal[i], list->eta()[i], list->phi()[i],
                 list->sampling()[i], list->side()[i], list->module()[i], list->tower()[i] );
    }else if( m_atlasFormat && !atlasFilterKeeps( det, list->cellID()[i], atlasCompressEnergy( list->energy()[i] ) ) ){
      // LAr hit below the cut of FilterHit_tf (F41 conserto 25)
      continue;
    }else if( det == 4 ){
      // FCAL hits (F41 conserto 22; CaloHitMaker::fcalStep): the module, kept in the field sampling of the list
      fcal.push( list->cellID()[i], m_atlasFormat ? atlasCompressEnergy( list->energy()[i] ) : list->energy()[i],
                 m_atlasFormat ? atlasCompressTime( hitTime[i] ) : hitTime[i], tglobal[i], list->eta()[i], list->phi()[i],
                 list->sampling()[i] );
    }else{
      // LAr hits (F41 conserto 19; CaloHitMaker::freeRunningLAr): region, sampling, barrel_ec / pos_neg, in the order of
      // the ATLAS ntuple branches (the list keeps sampling, barrel_ec and region in sampling, side and module)
      Container &c = ( det == 1 ) ? emb : ( det == 2 ? emec : hec );
      c.push( list->cellID()[i], m_atlasFormat ? atlasCompressEnergy( list->energy()[i] ) : list->energy()[i],
              m_atlasFormat ? atlasCompressTime( hitTime[i] ) : hitTime[i], tglobal[i], list->eta()[i], list->phi()[i],
              list->module()[i], list->sampling()[i], list->side()[i] );
    }
    etot += list->energy()[i];
  }

  MSG_DEBUG("Event " << eventNumber << ": " << list->size() << " free-running hits, total energy " << etot << " MeV");

  tree->Fill();
  // the buffers die at the end of this scope: detach them from the tree
  tree->ResetBranchAddresses();

  return StatusCode::SUCCESS;
}
