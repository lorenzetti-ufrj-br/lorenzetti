#ifndef ICaloTimeCorrectionTool_h
#define ICaloTimeCorrectionTool_h

#include "GaugiKernel/Tool.h"
#include "CaloHitBuilder/CaloHitTypes.h"

class G4Step;

class ICaloTimeCorrectionTool : public Gaugi::Tool {
public:
  ICaloTimeCorrectionTool( std::string name = "ICaloTimeCorrectionTool" ) : IMsgService(name), Tool() {}
  virtual ~ICaloTimeCorrectionTool() = default;

  virtual StatusCode initialize() override { return StatusCode::SUCCESS; }
  virtual StatusCode finalize() override { return StatusCode::SUCCESS; }
  virtual StatusCode execute( SG::EventContext &, Gaugi::EDM * ) const override { return StatusCode::SUCCESS; }

  virtual CellTiming computeTime( const G4Step *step, const CellIdentification &cell ) const = 0;
};

#endif
