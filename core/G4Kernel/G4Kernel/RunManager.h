
#ifndef RunManager_h
#define RunManager_h

#include "G4VUserDetectorConstruction.hh"
#include "G4Kernel/inputs/PrimaryGenerator.h"
#include "GaugiKernel/Algorithm.h"
#include "GaugiKernel/MsgStream.h"
#include "GaugiKernel/Property.h"


#include <vector>
#include <string>


class RunManager: public MsgService, 
                  public Gaugi::PropertyService
{
  public:

    RunManager( std::string name );
    ~RunManager();
    
    void run( int evt=10000);

    void push_back( Gaugi::Algorithm* );

    void setGenerator( PrimaryGenerator * );

    void setDetectorConstruction( G4VUserDetectorConstruction * );

    void addUICommand( std::string cmd ){
      m_uiCommands.push_back( cmd );
    };

  private:

    void header();
    
    int         m_timeout;
    int         m_nThreads;
    float       m_seed;
    bool        m_useGUI;
    std::string m_output;

    std::vector< Gaugi::Algorithm* >   m_acc;
    PrimaryGenerator                  *m_generator;
    G4VUserDetectorConstruction       *m_detector;
    std::vector< std::string >         m_uiCommands;
};
#endif
