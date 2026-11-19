#ifndef CaloFreeRunningHitWriter_h
#define CaloFreeRunningHitWriter_h

#include "GaugiKernel/Algorithm.h"
#include "GaugiKernel/DataHandle.h"
#include "CaloFreeRunningHitList.h"

/**
 * @class CaloFreeRunningHitWriter
 * @brief Writes the per-event CaloFreeRunningHitList as a flat ntuple with the layout of
 *        the ATLAS HITS ntuple: EventNumber plus, per container (TileCalHit, LArHitEMB,
 *        LArHitEMEC, LArHitHEC, LArHitFCAL), the vectors cellID, energy, time, tglobal,
 *        eta, phi and the container specific identification branches.
 *
 * One entry per event. The list holds the tile hits per PMT and the LAr and FCal hits per cell (per time bin with the
 * binning of the ATLAS simulation), filled by CaloHitMaker.
 *
 * Properties:
 * - InputListKey: StoreGate key of the CaloFreeRunningHitList.
 * - InputEventKey: StoreGate key of the EventInfo container (for EventNumber).
 * - NtupleName: name of the output tree (CollectionTree, as in the ATLAS ntuple).
 * - AtlasFormat: the LAr energy and time compressed and filtered as in the ATLAS HITS ntuple (FilterHit_tf), without tglobal.
 */
class CaloFreeRunningHitWriter : public Gaugi::Algorithm
{
  public:

    /** Constructor **/
    CaloFreeRunningHitWriter( std::string name );
    /** Destructor **/
    ~CaloFreeRunningHitWriter()=default;

    virtual StatusCode initialize() override;
    virtual StatusCode bookHistograms( SG::EventContext &ctx ) const override;
    virtual StatusCode pre_execute( SG::EventContext &ctx ) const override;
    virtual StatusCode execute( SG::EventContext &ctx , const G4Step *step) const override;
    virtual StatusCode execute( SG::EventContext &ctx , int /*evt*/ ) const override;
    virtual StatusCode post_execute( SG::EventContext &ctx ) const override;
    virtual StatusCode fillHistograms( SG::EventContext &ctx ) const override;
    virtual StatusCode finalize() override;

  private:

    StatusCode serialize( SG::EventContext &ctx ) const;

    std::string m_inputListKey;
    std::string m_inputEventKey;
    std::string m_ntupleName;
    // the format of the ATLAS HITS ntuple (F41 conserto 25): LAr compressed and filtered as FilterHit_tf, no tglobal branches
    bool m_atlasFormat;
};

#endif
