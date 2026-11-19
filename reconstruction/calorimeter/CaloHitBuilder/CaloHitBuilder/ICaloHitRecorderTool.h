#ifndef ICaloHitRecorderTool_h
#define ICaloHitRecorderTool_h

#include "GaugiKernel/Tool.h"
#include "CaloHitBuilder/CaloHitTypes.h"

class G4Step;

class ICaloHitRecorderTool : public Gaugi::Tool {
public:
  ICaloHitRecorderTool( std::string name = "ICaloHitRecorderTool" ) : IMsgService(name), Tool() {}
  virtual ~ICaloHitRecorderTool() = default;

  virtual StatusCode initialize() override { return StatusCode::SUCCESS; }
  virtual StatusCode finalize() override { return StatusCode::SUCCESS; }
  virtual StatusCode execute( SG::EventContext &, Gaugi::EDM * ) const override { return StatusCode::SUCCESS; }

  virtual StatusCode record( SG::EventContext &ctx, const G4Step *step,
                             const CellIdentification &cell, float energy,
                             const CellTiming &timing ) const = 0;
};

#endif
