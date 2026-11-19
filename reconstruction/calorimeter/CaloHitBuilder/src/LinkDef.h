#include "CaloHitBuilder/CaloHitTypes.h"
#include "CaloHitBuilder/ICaloCellIdentifierTool.h"
#include "CaloHitBuilder/ICaloEnergyModifierTool.h"
#include "CaloHitBuilder/ICaloTimeCorrectionTool.h"
#include "CaloHitBuilder/ICaloHitRecorderTool.h"
#include "src/CaloHitMaker.h"
#include "src/CaloHitMerge.h"
#include "src/CaloHitPileupMerge.h"

#ifdef __CINT__

#pragma link off all globals;
#pragma link off all classes;
#pragma link off all functions;
#pragma link C++ nestedclass;

#pragma link C++ struct CellIdentification+;
#pragma link C++ struct CellTiming+;
#pragma link C++ class ICaloCellIdentifierTool+;
#pragma link C++ class ICaloEnergyModifierTool+;
#pragma link C++ class ICaloTimeCorrectionTool+;
#pragma link C++ class ICaloHitRecorderTool+;

#pragma link C++ class CaloHitMaker+;
#pragma link C++ class CaloHitMerge+;
#pragma link C++ class CaloHitPileupMerge+;
#pragma link C++ class std::vector<long long>+;

#endif
