
#include "G4Kernel/ComponentAccumulator.h"
#include "G4Kernel/actions/Step4_EventAction.h"


#include "G4RunManager.hh"
#include "G4Event.hh"
#include "G4UnitsTable.hh"
#include <iomanip>


Step4_EventAction::EventAction()
 : IMsgService("EventAction"), 
   G4UserEventAction()
{;}


Step4_EventAction::~Step4_EventAction()
{;}


void Step4_EventAction::BeginOfEventAction(const G4Event* /*event*/)
{  
  auto* acc = static_cast<ComponentAccumulator*>(G4RunManager::GetRunManager()->GetNonConstCurrentRun());
  MSG_DEBUG( "Step4_EventAction::BeginOfEvent()" );
  acc->BeginOfEvent();
}



void Step4_EventAction::EndOfEventAction(const G4Event* /*event*/)
{
  MSG_DEBUG( "Step4_EventAction::EndOfEvent()" );
  auto* acc = static_cast<ComponentAccumulator*>(G4RunManager::GetRunManager()->GetNonConstCurrentRun());
  acc->EndOfEvent();
}




