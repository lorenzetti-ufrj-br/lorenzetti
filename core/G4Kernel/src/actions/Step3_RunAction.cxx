
#include "G4Kernel/ComponentAccumulator.h"
#include "G4Kernel/actions/Step3_RunAction.h"

#include "G4Run.hh"
#include "G4RunManager.hh"
#include "G4UnitsTable.hh"
#include "G4SystemOfUnits.hh"

#include "G4TransportationManager.hh"
#include "G4FieldManager.hh"
#include "G4Field.hh"
#include "G4ChordFinder.hh"

#include <iostream>

Step3_RunAction::Step3_RunAction( int numberOfThreads, int timeout, std::vector<Gaugi::Algorithm*> acc, std::string output )
 : IMsgService("Step3_RunAction"),
   G4UserRunAction(),
   m_acc(acc),
   m_output(output),
   m_numberOfThreads(numberOfThreads),
   m_timeout(timeout)
{;}


Step3_RunAction::~Step3_RunAction()
{
  MSG_INFO( "~Step3_RunAction()" );	
  //delete G4AnalysisManager::Instance();  
}


G4Run* Step3_RunAction::GenerateRun()
{
  MSG_INFO("Creating the ComponentAccumulator..");
  return new ComponentAccumulator(m_numberOfThreads, m_timeout, m_acc, m_output);
}


void Step3_RunAction::BeginOfRunAction(const G4Run* /*run*/)
{
  MSG_INFO( "Step3_RunAction::BeginOfRunAction" );
}


void Step3_RunAction::EndOfRunAction(const G4Run* /*run*/)
{;}


