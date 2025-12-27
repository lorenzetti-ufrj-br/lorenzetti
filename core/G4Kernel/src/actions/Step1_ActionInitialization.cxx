
#include "G4Kernel/actions/Step1_ActionInitialization.h"
#include "G4Kernel/actions/Step2_PrimaryGeneratorAction.h"
#include "G4Kernel/actions/Step3_RunAction.h"
#include "G4Kernel/actions/Step4_EventAction.h"
#include "G4Kernel/actions/Step5_SteppingAction.h"
#include "G4MTRunManager.hh"
#include <iostream>

Step1_ActionInitialization::Step1_ActionInitialization( int numberOfThreads,
                                                        int timeout,
                                                        PrimaryGenerator *gen,
                                                        std::vector<Gaugi::Algorithm*> acc , 
                                                        std::string output)
 : 
  IMsgService("Step1_ActionInitialization"), 
  G4VUserActionInitialization(),
  m_acc(acc),
  m_generator(gen),
  m_output(output),
  m_numberOfThreads(numberOfThreads),
  m_timeout(timeout)
{

  for ( auto toolHandle : m_acc )
  { 
    MSG_INFO( "Initializing the tool with name " << toolHandle->name() );
    if ( toolHandle->initialize().isFailure() )
    {
      MSG_ERROR("It's not possible to initialize the tool with name: " << toolHandle->name() );
    }
  } 

}


Step1_ActionInitialization::~Step1_ActionInitialization()
{
  MSG_INFO( "~Step1_ActionInitialization()" );
  for ( auto toolHandle : m_acc )
  { 
    if ( toolHandle->finalize().isFailure() )
    {
      MSG_ERROR("It's not possible to finalize the tool with name: " << toolHandle->name() );
    }
  }
}


void Step1_ActionInitialization::BuildForMaster() const
{
  //SetUserAction(new RunAction(m_acc, m_output));
}


void Step1_ActionInitialization::Build() const
{
  MSG_INFO( "Build()" );
  SetUserAction(new Step2_PrimaryGeneratorAction(m_generator));
  SetUserAction(new Step3_RunAction(m_numberOfThreads, m_timeout, m_acc, m_output));
  SetUserAction(new Step4_EventAction());
  SetUserAction(new Step5_SteppingAction());
}  

