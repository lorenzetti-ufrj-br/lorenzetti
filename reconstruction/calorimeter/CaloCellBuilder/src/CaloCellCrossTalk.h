#ifndef CaloCellCrossTalk_h
#define CaloCellCrossTalk_h

#include "GaugiKernel/Tool.h"
#include "GaugiKernel/Algorithm.h" 
#include "GaugiKernel/DataHandle.h"
#include "GaugiKernel/EDM.h"
#include "CaloCell/CaloDetDescriptor.h"
#include "CaloCell/CaloDetDescriptorCollection.h"
#include "TF1.h"


/**
 * @class CaloCellCrossTalk
 * @brief Algorithm to simulate cell-to-cell cross-talk.
 * 
 * Simulates the leakage of signal from one cell to its neighbors due to
 * capacitive, inductive, or resistive coupling in the readout electronics.
 */
class CaloCellCrossTalk : public Gaugi::Algorithm
{
  public:
    /** Constructor **/
    CaloCellCrossTalk( std::string name );
    ~CaloCellCrossTalk() = default;

    virtual StatusCode initialize() override;    
    /*! Book all histograms into the current storegate **/
    virtual StatusCode bookHistograms( SG::EventContext &ctx ) const override;
    /*! execute before start the step action **/
    virtual StatusCode pre_execute( SG::EventContext &ctx ) const override;
    /*! Execute in step action step from geant core **/
    virtual StatusCode execute( SG::EventContext &ctx , const G4Step *step) const override;
    /*! Execute in ComponentAccumulator **/
    virtual StatusCode execute( SG::EventContext &ctx , int /*evt*/ ) const override;
    /*! execute after the step action **/ 
    virtual StatusCode post_execute( SG::EventContext &ctx ) const override;

    virtual StatusCode finalize() override;
    
    /*! Fill all histograms into the current store gate */
    virtual StatusCode fillHistograms( SG::EventContext & /*ctx*/ ) const override;
    
    /**
     * @brief Add a tool to the post-processing chain.
     * @param tool Pointer to the Tool.
     */
    void push_back( Gaugi::Tool *tool );

  private:

    double  XTalk(double x, bool type) const;
    double  CellFunction(double x, bool type) const;
    float   XTalkTF( float sample, int samp_index, bool diagonal, bool inductive) const;

    /*! The tool list that will be executed into the post execute step */
    std::vector< Gaugi::Tool* > m_toolHandles;

    float m_minEnergy;
    std::string m_collectionKey;
    std::string m_xtcollectionKey;
    std::string m_histPath;

    uint m_Nsamples = 5;
    uint m_tSamp = 25;

    // cts modelling xtalk
    double m_Cx      =  47.000;
    double m_Rf      =   0.078;
    double m_Rin     =   1.200;
    double m_taud    =  15.820;
    double m_taupa   =  17.310;
    double m_td      = 420.000;
    double m_tmax2   = 600.000;
    double m_C1      =  50.000;

    // This value normalize amplitude of the Xt_C to unit
    double m_ToNormXtC = 0.022206;       

    // XTalk amplitude on % values of the Energy
    double m_AmpXt_C;
    double m_AmpXt_L;
    double m_AmpXt_R;
    double m_AmpNoise  = 50;             // Noise amplitude 50 MeV
    double tau_0_mean  = 0;
    double tau_std     = 0.5;

};

using CrossTalkMaker = CaloCellCrossTalk;

#endif
