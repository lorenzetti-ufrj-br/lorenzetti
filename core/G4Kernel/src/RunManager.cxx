

#include "G4Kernel/RunManager.h"
#include "G4Kernel/actions/ActionInitialization.h"
#include "GaugiKernel/Algorithm.h"



#ifdef G4MULTITHREADED
#include "G4MTRunManager.hh"
#include <thread> 
#include <X11/Xlib.h>
#else
#include "G4RunManager.hh"
#endif
#include "G4UImanager.hh"
#include "G4UIcommand.hh"
#include "FTFP_BERT.hh"
#include "Randomize.hh"
#include "G4VisExecutive.hh"
#include "G4UIExecutive.hh"

#include <stdlib.h>
#include <unistd.h>
#include <iostream>
#include "time.h"
#include <cstdlib>


RunManager::RunManager( std::string name ): 
  IMsgService( name ),
  PropertyService(),
  m_detector(nullptr),
  m_uiCommands()
{
  
  declareProperty( "NumberOfThreads", m_nThreads=1              );
  declareProperty( "OutputFile"     , m_output="Example.root"   );
  declareProperty( "Seed"           , m_seed=0                  );
  declareProperty( "Timeout"        , m_timeout = 3*60          ); // 3 minutes as default
  declareProperty( "UseGUI"         , m_useGUI=false            );
  MSG_INFO( "Run manager was created." );

}

RunManager::~RunManager() 
{;}


void RunManager::push_back( Gaugi::Algorithm *alg )
{
  m_acc.push_back( alg );
}


void RunManager::setGenerator( PrimaryGenerator *gen )
{
  m_generator = gen;
}

void RunManager::setDetectorConstruction( G4VUserDetectorConstruction *det )
{
  m_detector = det;
}


void RunManager::run( int evt )
{

  header();
  
  int argc=1;
  char* argv[1] = {"app"};

  G4UIExecutive* ui = 0;
  if ( m_useGUI ) {
    ui = new G4UIExecutive(argc,argv);
  }

  MSG_INFO( "Create the random generator..." );

  // Choose the Random engine
  G4Random::setTheEngine(new CLHEP::RanecuEngine);
  MSG_INFO( "set seed as " << m_seed );

  //G4long seed = abs(((time(NULL) * 181) * ((getpid() - 83) * 359)) % 104729);
  //G4long seed = abs(((time(NULL) * 181) * ((83) * 359)) % 104729);
  CLHEP::HepRandom::setTheSeed(m_seed);
  MSG_INFO( "Building the manager+..." );

  // Construct the default run manager
#ifdef G4MULTITHREADED  
  MSG_INFO( "Create MT Manager..." );

  G4MTRunManager * runManager = new G4MTRunManager;
  MSG_INFO( "Create MT Manager... done" );

  if ( m_nThreads > 0 ) {
    MSG_INFO( "Create MT Manager with " << m_nThreads << " threads..." );

    runManager->SetNumberOfThreads(m_nThreads);
    MSG_INFO( "Create MT Manager with " << m_nThreads << " threads... done"  );

  }
#else
  MSG_INFO( "Create Manager" );
  G4RunManager * runManager = new G4RunManager;
#endif


  MSG_INFO( "Building the detector..." );
  if( !m_detector ){
    MSG_FATAL( "You must instantiate the detector contruction first. Abort!" );
  }else{
    runManager->SetUserInitialization(m_detector);
  }

  G4VModularPhysicsList* physicsList = new FTFP_BERT;
  runManager->SetUserInitialization(physicsList);

  MSG_INFO( "Creating the action initalizer..." );
  MSG_INFO( m_output );
  ActionInitialization* actionInitialization = new ActionInitialization(m_nThreads, m_timeout, m_generator, m_acc, m_output);
  runManager->SetUserInitialization(actionInitialization);

  MSG_INFO( "Creating the vis executive...");
  G4VisManager* visManager = new G4VisExecutive;
  visManager->Initialize();
  G4UImanager* UImanager = G4UImanager::GetUIpointer();
  
  std::stringstream runCommand; runCommand << "/run/beamOn " << evt ;
  m_uiCommands.push_back( runCommand.str() );
  UImanager->ApplyCommand("/run/initialize");
  UImanager->ApplyCommand("/run/printProgress 1");
  UImanager->ApplyCommand("/run/verbose 2");
  for ( auto cmd : m_uiCommands ){
    UImanager->ApplyCommand( cmd );
  }
  if(m_useGUI){
    ui->SessionStart();
    delete ui;
  }


  delete runManager;
  delete visManager;
}



// Print this header before start
void RunManager::header()
{
  std::cout <<"    __                              _   _   _  "       << std::endl;  
	std::cout <<"   / /  ___  _ __ ___ _ __  _______| |_| |_(_) "       << std::endl;
	std::cout <<"  / /  / _ \\| '__/ _ \\ '_ \\|_  / _ \\ __| __| | "   << std::endl;
	std::cout <<" / /__| (_) | | |  __/ | | |/ /  __/ |_| |_| | "       << std::endl;
	std::cout <<" \\____/\\___/|_|  \\___|_| |_/___\\___|\\__|\\__|_| " << std::endl;
  
  std::cout << std::endl;
  std::cout << "Empowering Physics Performance and Analysis with Low-level Calorimetry Data." << std::endl;
  std::cout << std::endl;
  std::cout << "Universidade Federal do Rio de Janeiro (UFRJ/COPPE), Brazil" << std::endl;
  //std::cout << "Authors: Joao Victor da Fonseca Pinto (jodafons@cern.ch), Werner Freund (wsfreund@cern.ch), ..." << std::endl;
  


  std::vector<std::string> s{"Using Gaugi as core...", "Using Geant4 as simulator layer...", "Power up..."};

  for( unsigned dot=0; dot<3; ++dot ){
    sleep(1); // Wait 1 seconds
    std::cout << s[dot] << std::endl;
  }
  sleep(2); // Wait 2 seconds
}


