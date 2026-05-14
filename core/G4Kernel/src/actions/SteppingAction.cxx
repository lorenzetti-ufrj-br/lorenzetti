
#include "G4Kernel/RunSequence.h"
#include "G4Kernel/actions/SteppingAction.h"

#include "G4Step.hh"
#include "G4RunManager.hh"
#include "G4SystemOfUnits.hh"

SteppingAction::SteppingAction()
  : IMsgService("SteppingAction"),
    G4UserSteppingAction()
{;}

//!=====================================================================

SteppingAction::~SteppingAction()
{;}

//!=====================================================================

void SteppingAction::UserSteppingAction(const G4Step* step)
{
  RunSequence* acc = static_cast<RunSequence*> (G4RunManager::GetRunManager()->GetNonConstCurrentRun()); 
  acc->ExecuteEvent(step);
  
  if (acc->timeout())
  {
    acc->lock(); // Force skip the post execute step
    std::string msg = "Event timeout!";
    G4Exception("RunSequence::UserSteppingAction()", "WatchDog", EventMustBeAborted, msg.c_str());
  }  
}

//!=====================================================================






