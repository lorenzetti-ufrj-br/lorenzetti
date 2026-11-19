#ifndef ICaloCellIdentifierTool_h
#define ICaloCellIdentifierTool_h

#include "GaugiKernel/Tool.h"
#include "CaloHitBuilder/CaloHitTypes.h"
#include "CaloHit/CaloHitCollection.h"

class G4Step;

class ICaloCellIdentifierTool : public Gaugi::Tool {
public:
  ICaloCellIdentifierTool( std::string name = "ICaloCellIdentifierTool" ) : IMsgService(name), Tool() {}
  virtual ~ICaloCellIdentifierTool() = default;

  virtual StatusCode initialize() override { return StatusCode::SUCCESS; }
  virtual StatusCode finalize() override { return StatusCode::SUCCESS; }
  virtual StatusCode execute( SG::EventContext &, Gaugi::EDM * ) const override { return StatusCode::SUCCESS; }

  virtual StatusCode preExecute( SG::EventContext &ctx, xAOD::CaloHitCollection *collection ) const = 0;
  virtual CellIdentification identify( const G4Step *step ) const = 0;
};

#endif
