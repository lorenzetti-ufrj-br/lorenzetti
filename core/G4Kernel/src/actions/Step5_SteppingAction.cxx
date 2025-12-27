
#include "G4Kernel/ComponentAccumulator.h"
#include "G4Kernel/actions/Step5_SteppingAction.h"

#include "G4Step.hh"
#include "G4RunManager.hh"
#include "G4SystemOfUnits.hh"

Step5_SteppingAction::Step5_SteppingAction()
  : IMsgService("Step5_SteppingAction"),
    G4UserStep5_SteppingAction()
{;}

//!=====================================================================

Step5_SteppingAction::~Step5_SteppingAction()
{;}

//!=====================================================================

void Step5_SteppingAction::UserSteppingAction(const G4Step* step)
{
  ComponentAccumulator* acc = static_cast<ComponentAccumulator*> (G4RunManager::GetRunManager()->GetNonConstCurrentRun()); 
  acc->ExecuteEvent(step);
  
  if (acc->timeout())
  {
    acc->lock(); // Force skip the post execute step
    std::string msg = "Event timeout!";
    G4Exception("ComponentAccumulator::UserStep5_SteppingAction()", "WatchDog", EventMustBeAborted, msg.c_str());
  }  
}

//!=====================================================================






