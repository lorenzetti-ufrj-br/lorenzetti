
#include "G4Kernel/RunSequence.h"
#include "G4Kernel/actions/SteppingAction.h"

#include "G4Step.hh"
#include "G4RunManager.hh"
#include "G4SystemOfUnits.hh"
#include "G4Track.hh"
#include "G4Kernel/AtlasG4Settings.h"

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

  // LooperKiller of the ATLAS simulation (F41 conserto 24; Athena release 23.0.14, LooperKiller.cxx with MaxSteps 1000000,
  // PrintSteps 100, AbortEvent true, and KillAbortedEvents): a track still alive at step 1000100 is killed and the event is aborted
  // (and so not written). Spots of the frozen showers have no track.
  if( AtlasG4Settings::instance().enabled && step->GetTrack() && step->GetTrack()->GetCurrentStepNumber() >= 1000100 ){
    step->GetTrack()->SetTrackStatus( fStopAndKill );
    acc->lock();
    G4Exception("SteppingAction::UserSteppingAction()", "LooperKiller", EventMustBeAborted, "Looper killed after 1000100 steps");
    return;
  }
  
  if (acc->timeout())
  {
    acc->lock(); // Force skip the post execute step
    std::string msg = "Event timeout!";
    G4Exception("RunSequence::UserSteppingAction()", "WatchDog", EventMustBeAborted, msg.c_str());
  }  
}

//!=====================================================================






