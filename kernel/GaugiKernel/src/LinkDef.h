#include "GaugiKernel/MsgStream.h"
#include "GaugiKernel/Property.h"
#include "GaugiKernel/Algorithm.h"
#include "GaugiKernel/Tool.h"
#include "GaugiKernel/ITool.h"
#include "GaugiKernel/Timer.h"
#include "GaugiKernel/ComponentAccumulator.h"

#include "GaugiKernel/DataHandle.h"
#include "GaugiKernel/StoreGate.h"
#include "GaugiKernel/EDM.h"
#include "GaugiKernel/StringHash.h"
#include "GaugiKernel/ElementLink.h"
#include <vector>

#ifdef __CINT__

#pragma link off all globals;
#pragma link off all classes;
#pragma link off all functions;
#pragma link C++ nestedclass;


#pragma link C++ class Timer+;
#pragma link C++ class MsgService+;
#pragma link C++ class IMsgService+;
#pragma link C++ class PropertyService+;
#pragma link C++ class Algorithm+;
#pragma link C++ class Gaugi::Tool+;
#pragma link C++ class Gaugi::ITool+;
#pragma link C++ class std::vector<Gaugi::Tool*>+;
#pragma link C++ class Gaugi::ComponentAccumulator+;

#pragma link C++ class Gaugi::EDM+;
#pragma link C++ class SG::EventContext+;
#pragma link C++ class SG::StoreGate+;
#pragma link C++ class SG::DataHandle+;


#endif
