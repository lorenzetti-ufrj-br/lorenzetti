#include "src/CaloCellMaker.h"
#include "src/CaloCellMerge.h"
#include "src/CaloCellNoiseSuppression.h"
#include "src/CaloCellCrossTalk.h"
#include "src/electronics/PulseGenerator.h"
#include "src/electronics/OptimalFilter.h"
#include "src/electronics/ConstrainedOptimalFilter.h"
#include "src/electronics/PulsePerturber.h"

#ifdef __CINT__

#pragma link off all globals;
#pragma link off all classes;
#pragma link off all functions;
#pragma link C++ nestedclass;

#pragma link C++ class CaloCellMaker+;
#pragma link C++ class CaloCellMerge+;
#pragma link C++ class CaloCellNoiseSupression+;
#pragma link C++ class CaloCellNoiseSuppression+;
#pragma link C++ class CaloCellFilter+;
#pragma link C++ class CaloCellCrossTalk+;
#pragma link C++ class CrossTalkMaker+;

#pragma link C++ class PulseGenerator+;
#pragma link C++ class OptimalFilter+;
#pragma link C++ class ConstrainedOptimalFilter+;
#pragma link C++ class PulsePerturber+;

#endif
