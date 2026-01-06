
#include "G4Kernel/RunSequence.h"
#include "G4Kernel/actions/EventAction.h"


#include "G4RunManager.hh"
#include "G4Event.hh"
#include "G4UnitsTable.hh"
#include <iomanip>


EventAction::EventAction()
 : IMsgService("EventAction"), 
   G4UserEventAction()
{;}


EventAction::~EventAction()
{;}


void EventAction::BeginOfEventAction(const G4Event* /*event*/)
{  
  auto* acc = static_cast<RunSequence*>(G4RunManager::GetRunManager()->GetNonConstCurrentRun());
  MSG_DEBUG( "EventAction::BeginOfEvent()" );
  acc->BeginOfEvent();
}



void EventAction::EndOfEventAction(const G4Event* /*event*/)
{
  MSG_DEBUG( "EventAction::EndOfEvent()" );
  auto* acc = static_cast<RunSequence*>(G4RunManager::GetRunManager()->GetNonConstCurrentRun());
  acc->EndOfEvent();
}




