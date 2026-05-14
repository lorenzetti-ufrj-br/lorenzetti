

#include "JF17.h"
#include <algorithm>
#include "fastjet/PseudoJet.hh"
#include "fastjet/JetDefinition.hh"
#include "fastjet/ClusterSequence.hh"
#include "helper.h"


using namespace generator;


/**
 * @class JF17
 * @brief Jet filtering algorithm (J17/JF17-like) for event selection.
 *
 * This algorithm filters events based on Jet properties (Anti-Kt). It interfaces with
 * FastJet to cluster particles and selects events where jets fall within specific
 * Pt strings (bins) and pile-up windows. It serves as a generator-level filter
 * to produce specific slice samples (e.g., J0, J1, ... J5).
 * 
 * Properties:
 * - EtaMax/Min: Jet eta acceptance.
 * - MinPt/MaxPt: Jet Transverse Momentum selection range.
 * - Select: Filter mode (e.g. 2 for specific Pythia filter logic).
 * - Eta/PhiWindow: Cluster size.
 */
JF17::JF17(const std::string name , IGenerator *gen): 
  IMsgService(name),
  IAlgorithm(gen)
{
  declareProperty( "EtaMax"         , m_etaMax=1.4                );
  declareProperty( "EtaMin"         , m_etaMin=0                  );
  declareProperty( "MinPt"          , m_minPt=0.0                 );   
  declareProperty( "MaxEMFraction"  , m_maxEMFraction=0.7         );  
  declareProperty( "EtaWindow"      , m_etaWindow=0.4             );
  declareProperty( "PhiWindow"      , m_phiWindow=0.4             );
  declareProperty( "Select"         , m_select=1                  );
}

JF17::~JF17()
{;}


StatusCode JF17::initialize()
{
  setMsgLevel(m_outputLevel);

  MSG_INFO( "Initializing the JF17..." );
  if(generator()->initialize().isFailure()){
    MSG_FATAL("Its not possible to initialize the generator. Abort!");
  }
  return StatusCode::SUCCESS;
}



StatusCode JF17::execute( generator::Event &ctx )
{

  HepMC3::GenEvent evt( HepMC3::Units::GEV, HepMC3::Units::MM);
  // Generate main event. Quit if too many failures.
  if (generator()->execute(evt).isFailure()){
    return StatusCode::FAILURE;
  }
  
 
  const auto main_event_t = sample_t();
  const auto main_event_z = sample_z();

 

  //ParticleHelper::ParticleFilter filter( m_select, m_etaMax + .05, m_etaMin - 0.05, 0.7, 0.05 );
  //filter.filter(evt);



  // Map to link PseudoJet back to HepMC3::GenParticle
  std::vector<const HepMC3::GenParticle*> particles_in_jets;
  std::vector<fastjet::PseudoJet> input_particles;
  
  for (const auto& part : evt.particles()){
    
    if (!ParticleHelper::isVisible(part.get())) continue;

    // Only consider final state particles.
    if( part->status() != 1 ) continue;
    
    float eta = part->momentum().eta();
    if (std::abs(eta) > m_etaMax) continue;
    if (std::abs(eta) < m_etaMin) continue;

    fastjet::PseudoJet j(part->momentum().px(), part->momentum().py(), part->momentum().pz(), part->momentum().e());
    
    // Store index in user_index to retrieve the particle later
    j.set_user_index( particles_in_jets.size() );
    input_particles.push_back( j );
    particles_in_jets.push_back( part.get() );
  }

  //MSG_DEBUG("Input particles for FastJet: " << input_particles.size());

  // Clusterize hadrons
  fastjet::JetDefinition jet_def(fastjet::antikt_algorithm, 0.4);
  fastjet::ClusterSequence clust_seq(input_particles, jet_def);

  auto inclusive_jets = fastjet::sorted_by_pt(clust_seq.inclusive_jets(m_minPt/1e3) );

  if ( inclusive_jets.empty() ){
    MSG_WARNING("inclusive_jets.empty()");
    throw NotInterestingEvent();
  }

  bool ok = false;

  for ( const auto &jet : inclusive_jets ){

    float energy_em = 0;

    for (const auto &sub : jet.constituents() ){
      const HepMC3::GenParticle* part = particles_in_jets[sub.user_index()];
      int pid = std::abs(part->pid());
      //MSG_DEBUG("Jet constituent PID: " << pid);
      if ( pid==11 || pid==22 ) {
        //MSG_DEBUG("Jet constituent PID: " << pid << " is electron or photon. e = " << sub.e());
        energy_em += sub.e();
      }
    }

    float em_frac = energy_em / jet.e();
    MSG_INFO("Jet EM fraction: " << em_frac);
    MSG_INFO("Jet Pt: " << jet.pt());
    MSG_INFO("Jet eta: " << jet.eta());
    MSG_INFO("Jet phi: " << jet.phi());
    MSG_INFO("Jet e: " << jet.e());
   
    if (jet.pt() > m_minPt/1e3 && em_frac > m_maxEMFraction){
      ok=true;
      auto seed = generator::Seed( jet.eta(), jet.phi() );

      for ( auto& p : jet.constituents() )
      {
        const HepMC3::GenParticle* part = particles_in_jets[p.user_index()];
        
        // Window check (FastJet's eta/phi)
        if( std::abs(p.eta() - jet.eta()) <= m_etaWindow/2.0 && 
            std::abs(p.phi() - jet.phi()) <= m_phiWindow/2.0 )
          {
            float xProd = 0, yProd = 0, zProd = 0, tProd = 0;
            if (part->production_vertex()) {
              xProd = part->production_vertex()->position().x();
              yProd = part->production_vertex()->position().y();
              zProd = part->production_vertex()->position().z() + main_event_z;
              tProd = part->production_vertex()->position().t() + main_event_t;
            }

            seed.emplace_back( 1, 0, 
                               part->pid(), 
                               part->momentum().px(), 
                               part->momentum().py(), 
                               part->momentum().pz() , 
                               part->momentum().eta(), 
                               part->momentum().phi(), 
                               xProd, yProd, zProd, tProd,
                               part->momentum().e(), 
                               part->momentum().pt() ); 
          }
      }// end constituents

      ctx.push_back( seed );
    } // end jet
  } // end inclusive_jets

  if ( !ok ){
    MSG_WARNING( "There is no valid jet.");
    throw NotInterestingEvent();
  }


  ctx.setEventNumber(evt.event_number());
  
  // Print all particles and clusters
  int cx=0;
  for ( auto seed : *ctx ){
    
    MSG_INFO( "======== Cluster " << cx << " ==========" );
    float etot=0.0;
    for ( auto p : *seed ){
      etot+= p.eT;
      MSG_INFO( "Eta =" << p.eta << " Phi = " << p.phi << " Pt = " << p.eT );
    }

    MSG_INFO( "Eta_center =" << seed.eta() << " Phi_center = " << seed.phi() << " Et = " << etot );
    MSG_INFO( "========================================" );
    cx++;
  }
  
  return StatusCode::SUCCESS;
}


StatusCode JF17::finalize()
{
  MSG_INFO( "Finalize the JF17 Event." );
  //m_generator.stat();
  return StatusCode::SUCCESS;
}


bool JF17::isTruthElectronFromAny(const HepMC3::GenParticle *particle ) const
{
  int pdg = std::abs(particle->pid());
  if (pdg == 11) { // É um elétron
      auto prodVtx = particle->production_vertex();

      if (prodVtx) {
          MSG_WARNING("Electron PDG: " << pdg);
          // Itera sobre as partículas que entram no vértice (as "Mães")
          for (auto& mother : prodVtx->particles_in()) {
              int m_pdg = std::abs(mother->pid());
              MSG_WARNING("Mother PDG: " << m_pdg);
              // --- LÓGICA JF17 PARA MC_ORIGIN ---
              // 1. Verificar se vem de Hádron Pesado (B ou C)
              if ((m_pdg / 100 == 5 || m_pdg / 1000 == 5) || // B-Hadrons
                  (m_pdg / 100 == 4 || m_pdg / 1000 == 4)) { // C-Hadrons
                  // Define mcType = 4 e mcOrigin = 26 ou 25
                  return true;
              }
              // 2. Verificar se vem de Fóton (Conversão)
              else if (m_pdg == 22) {
                  // Define mcType = 2 (ou 4 dependendo da análise) e mcOrigin = 9
                  return true;
              }
              // 3. Verificar se é ruído de jato leve (Light Flavor)
              else if (m_pdg < 100) {
                  // Origens de QCD/Djets (mcOrigin 42 ou similar)
                  return true;
              }
          }
      }else{
        MSG_WARNING("Electron has no production vertex");
      }
  }else{
    MSG_WARNING("Particle is not an electron");
  }
  return false;
}
