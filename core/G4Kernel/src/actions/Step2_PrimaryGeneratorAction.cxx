

#include "G4Kernel/actions/Step2_PrimaryGeneratorAction.h"
#include "G4Event.hh"


Step2_PrimaryGeneratorAction::Step2_PrimaryGeneratorAction( PrimaryGenerator *gen): 
  IMsgService("Step2_PrimaryGeneratorAction"),
  G4VUserPrimaryGeneratorAction()
{
  // Need to copy the generator to works on thread mode
  m_generator = gen->copy();
  MSG_INFO( "Create the generator copy" );
  m_generator->initialize();
}


Step2_PrimaryGeneratorAction::~Step2_PrimaryGeneratorAction()
{
  m_generator->finalize();
  delete m_generator;
}


void Step2_PrimaryGeneratorAction::GeneratePrimaries(G4Event* anEvent)
{
  if(m_generator){
    MSG_INFO( "GeneratePrimaryVertex..." );
    m_generator->GeneratePrimaryVertex(anEvent);
  }else
    G4Exception("Step2_PrimaryGeneratorAction::GeneratePrimaries",
                "InvalidSetup", FatalException,
                "Generator is not instanciated.");
}



