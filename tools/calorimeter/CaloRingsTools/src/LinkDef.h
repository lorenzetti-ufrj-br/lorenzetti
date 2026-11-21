#include "src/CaloRingsBaseTool.h"
#include "src/StandardRingsTool.h"
#include "src/AsymRingsTool.h"
#include "src/CrossRingsTool.h"
#include "src/CornerRingsTool.h"
#include "src/StripsRingsTool.h"
#include "src/CustomRingsTool.h"

#ifdef __CINT__

#pragma link off all globals;
#pragma link off all classes;
#pragma link off all functions;
#pragma link C++ nestedclass;

#pragma link C++ class Gaugi::RingSetBase + ;
#pragma link C++ class RingSetBase + ;
#pragma link C++ class RingSet + ;
#pragma link C++ class RingSetAsym + ;
#pragma link C++ class SeedPosC + ;
#pragma link C++ class RingSetCross + ;
#pragma link C++ class SeedPos + ;
#pragma link C++ class RingSetCorner + ;
#pragma link C++ class RingSetStrips + ;
#pragma link C++ class RingSetCustom + ;

#pragma link C++ class Gaugi::CaloRingsBaseTool + ;
#pragma link C++ class Gaugi::StandardRingsTool + ;
#pragma link C++ class Gaugi::AsymRingsTool + ;
#pragma link C++ class Gaugi::CrossRingsTool + ;
#pragma link C++ class Gaugi::CornerRingsTool + ;
#pragma link C++ class Gaugi::StripsRingsTool + ;
#pragma link C++ class Gaugi::CustomRingsTool + ;

#endif
