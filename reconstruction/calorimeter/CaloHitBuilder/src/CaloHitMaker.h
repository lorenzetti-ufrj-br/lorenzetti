#ifndef CaloHitMaker_h
#define CaloHitMaker_h

#include "GaugiKernel/Algorithm.h"
#include "GaugiKernel/DataHandle.h"
#include "GaugiKernel/AlgTool.h"
#include "CaloHit/CaloHit.h"
#include "CLHEP/Vector/ThreeVector.h"

// the ported ATLAS charge collection of the EM end-cap (geometry/LArG4EC/EnergyCalculator.h; kept out of the dictionary)
namespace LArG4 { namespace EC { class EnergyCalculator; } }



/**
 * @class CaloHitMaker
 * @brief Algorithm to build calorimeter hits during simulation.
 * 
 * Collects energy deposits from Geant4 steps and integrates them into hits
 * corresponding to readout cells.
 */
class CaloHitMaker : public Gaugi::Algorithm
{

  typedef std::map<unsigned long int, xAOD::CaloHit* > collection_map_t;

  public:
  
    /** Contructor **/
    CaloHitMaker( std::string name );
    /** Destructor **/
    ~CaloHitMaker()=default;
    
    /*! initialize the algorithm **/
    virtual StatusCode initialize() override;
    
    /*! Book all histograms into the current storegate **/
    virtual StatusCode bookHistograms( SG::EventContext &ctx ) const override;
    
    /*! Execute in step action step from geant core **/
    virtual StatusCode execute( SG::EventContext &ctx , const G4Step *step) const override;
    
    /*! Execute in ComponentAccumulator **/
    virtual StatusCode execute( SG::EventContext &ctx , int /*evt*/ ) const override;
    
    /*! execute before start the step action **/
    virtual StatusCode pre_execute( SG::EventContext &ctx ) const override;
    
    /*! execute after the step action **/ 
    virtual StatusCode post_execute( SG::EventContext &ctx ) const override;
    
    /*! fill histogram in the end **/
    virtual StatusCode fillHistograms( SG::EventContext &ctx ) const override;
    
    virtual StatusCode finalize() override;

    /*! ATLAS-like EM end-cap (EmecCompartment > 0; geometry/python/v1/EMEC.py, --atlas-emec): the compartment (1-11)
        of the point (x, y, z), in mm, as in the ATLAS simulation (LArG4EC EnergyCalculator::FindIdentifier_Default),
        and, when it is the compartment of this maker, the eta index and the phi bin of its cell; 0 when the point is
        outside the wheel of this maker. Public so that the assignment can be tested from Python. */
    int emecFindCell( double x, double y, double z, int &etaBin, int &phiBin ) const;

    /*! ATLAS-like barrel EM and presampler cells (EmbMode > 0; geometry/python/v1/ECAL.py, --atlas-emb-cells): the cell
        (index in the table CellEta) of the point (x, y, z), in mm, for the sampling and region of this maker, or -1 when
        the point has no cell of that region (see the .cxx). Public so that the assignment can be tested from Python. */
    int embFindCell( double x, double y, double z ) const;
    /*! ATLAS-like barrel presampler (EmbMode = 3): the cell from the gap of the electrode (see the .cxx). */
    int psbGapCell( double x, double y, double z ) const;

  private:
   
    int find( const std::vector<float> &vec, float value) const;
    // phi bin of a step: as find, also trying phi -+ 2 pi (the edges may be shifted out of -pi..pi, see m_phiShift)
    int findPhi( float phi ) const;
    unsigned long int hash(unsigned bin) const;

    /*! collection key */
    std::string m_collectionKey; // output

    std::vector<float> m_etaBins; 
    std::vector<float> m_phiBins; 
    float m_rMin;
    float m_rMax; 
    float m_zMin;
    float m_zMax;
    // the region tested at the midpoint of the step (F41 conserto 36)
    float m_noiseStd;
    // Keep only the energy deposited in the active medium (liquid argon, scintillator)
    bool m_activeEnergyOnly;
    // Apply Birks' law to the energy of each step (scintillator and liquid argon), as in ATLAS
    bool m_birksLaw;
    // Time of the ATLAS simulation for the bunch crossing of the hits (AtlasHitTime; see hitTime)
    bool m_atlasHitTime;
    // Time of the deposit for the bunch crossing of the normal hit (AtlasHitTime): the ATLAS time of the LAr (larHitTime) or of
    // the tile cell (tileTime, without the PMT delays); t0 and t1 the times of the two PMTs (the same as t outside the tile)
    void hitTime( const G4Step *step, int cell, int phiBin, float &t, float &t0, float &t1 ) const;
    double larHitTime( const G4Step *step ) const;
    float birksEnergy( const G4Step *step ) const;

    /*! Sampling id for this reconstruction */
    int m_sampling;
    /*! Sampling id segment */
    int m_segment;
    /*! Detector id for this sampling*/
    int m_detector;
    /*! The start bunch crossing id for energy estimation */
    int m_bcid_start;
    /*! The end bunch crossing id for energy estimation */
    int m_bcid_end;
    /*! The time space (in ns) between two bunch crossings */
    float m_bc_duration;
    /*! Base histogram path */
    std::string m_histPath;
    /*! detailed histogram flags */
    bool m_detailedHistograms;

    unsigned int m_nEtaBins;
    unsigned int m_nPhiBins;

    // Cells given as (r, z) boxes instead of the eta x phi grid (ATLAS tile cells; empty by default).
    // One entry per cell: eta of its centre and its delta eta. One entry per box: r and z limits and the
    // index of the cell it belongs to (a cell may be made of several boxes, as BC in the tile barrel).
    std::vector<float> m_cellEta;
    std::vector<float> m_cellDeltaEta;
    std::vector<float> m_cellBoxRMin;
    std::vector<float> m_cellBoxRMax;
    std::vector<float> m_cellBoxZMin;
    std::vector<float> m_cellBoxZMax;
    std::vector<int>   m_cellBoxIndex;
    bool useCells() const { return !m_cellEta.empty(); }

    // Dual readout of the tile cells, as in ATLAS (TileGeoG4SDCalc::MakePmtEdepTime): each cell is read by two
    // PMTs, one on each side of the tiles in phi, and the energy of each step is shared between them according
    // to its azimuthal position across the module. 0 = off (default), 1 = ATLAS U-shape, 2 = linear sharing.
    int m_tileDualReadout;
    bool isTile() const { return m_sampling >= 5 && m_sampling <= 10; }
    void tilePmtWeights( float phiLocal, float z, float &w0, float &w1, bool replaced=false ) const;
    // ATLAS gap and ITC cells (F41 conserto 21): PMTs per cell (2, 1 = only pmt 0, -1 = only pmt 1), U-shape table of the
    // long barrel by tile row (part, layer; -1 = from the sampling), special modules with their number of PMTs (0 = read as
    // the replacement cell) and the replacement cell (D5 for the special D4)
    std::vector<int> m_cellNPmt;
    int m_uShapePart;
    int m_uShapeLayer;
    std::vector<int> m_specialModule;
    std::vector<int> m_specialNPmt;
    int m_replaceSection;
    int m_replaceTower;
    int m_replaceSampling;
    float m_replaceRCentre;
    float m_replaceZCentre;
    // the hit of the replacement cell in the normal chain (the collection of its sampling and its hash without the phi bin):
    // the deposits of the cell in the special modules (npmt = 0) go to that hit. Empty by default.
    std::string m_replaceCollectionKey;
    int m_replaceHashBase;
    int tileNPmt( int cell, int phiBin ) const;
    int findCell( float radius, float z ) const;
    // Radius used to find the (r, z) box of a step: r itself (CellRadiusModules = 0, the default) or, with N modules,
    // the radius on the axis of the module that contains phi, r cos(phi - phi_c), modules of 2 pi / N from phi = 0
    // (moduleY of the ATLAS HEC simulation, LArG4HEC HECGeometry::CalculateIdentifier; ATLAS-like HEC, --atlas-hec).
    int m_cellRadiusModules;
    float cellRadius( float radius, float phi ) const;

    // ATLAS-like EM end-cap (see emecFindCell): the compartment read by this maker (1-11 as in the table s_geometry of
    // EnergyCalculator.cc; 0 = off, the default), its eta scale, offset and last index, the distance from the
    // mechanical to the electric focal point, the boundaries in z between the compartments (EmecSamplingSep: ZSEP12,
    // ZSEP23, ZIW, from the electric focal point, integers in 1e-4 cm as in the database) and the volumes (r, z boxes)
    // of the wheel of the compartment.
    int m_emecCompartment;
    float m_emecEtaScale;
    float m_emecEtaOffset;
    int m_emecMaxEta;
    float m_emecFocalShift;
    std::vector<int> m_emecZSep12;
    std::vector<int> m_emecZSep23;
    std::vector<int> m_emecZInner;
    // z boundary (mm) from a table value in 1e-4 cm, as the ATLAS simulation reads it (value in cm times CLHEP::cm)
    static double emecZ( int value ) { return ( value / 1e4 ) * 10.; }
    std::vector<float> m_emecWheelRMin;
    std::vector<float> m_emecWheelRMax;
    std::vector<float> m_emecWheelZMin;
    std::vector<float> m_emecWheelZMax;

    // Charge collection of the ATLAS EM end-cap (F41 conserto 29, --atlas-emec-charge-collection): with EmecChargeCollection the
    // energy of the free-running hits of this EMEC maker is the one of the ATLAS simulation (Athena 23.0.14, LArG4::EC::
    // EnergyCalculator::Process_Default with EnergyCorrection = 8): Birks' law with the local field 0.01 HV / gap at the middle of
    // the step and the current of the charge collection (CalculateChargeCollection1), computed by the ported ATLAS code
    // (geometry/LArG4EC, geometry/GeoSpecialShapes) on the step brought to the frame of the ATLAS wheel and moved in phi into the
    // liquid argon of the accordion (see emecChargeEnergy). The tables of the wheels (EmecChargeTables), the field map
    // (EmecChargeFieldMap, ec.fieldzv03) and the HV map (EmecChargeHVMap, HVEMECMap_v02.dat) are files of geometry/data.
    bool m_emecChargeCollection;
    std::string m_emecChargeTables;
    std::string m_emecChargeFieldMap;
    std::string m_emecChargeHVMap;
    const LArG4::EC::EnergyCalculator *m_emecCalculator = nullptr;   // shared by the makers of the same wheel and side
    bool emecChargeEnergy( const G4Step *step, double &energy ) const;
    void emecDiscardCount( bool inner, double energyBefore, bool discarded ) const;
    double emecLArPhiShift( const CLHEP::Hep3Vector &p ) const;

    // ATLAS-like barrel EM and presampler cells (see embFindCell): mode (0 = off, the default; 1 = barrel; 2 = end-cap
    // presampler), sampling (0-3) and region (0 or 1) of the ATLAS identifier dictionary read by this maker.
    int m_embMode;
    int m_embSampling;
    int m_embRegion;
    // EmbMode = 2: |z| subtracted before the eta of the end-cap presampler (the shift of the ATLAS end-cap, F41 conserto 27)
    double m_embZShift;
    // EmbMode = 3: radius of the middle of the active layer of the barrel presampler (mm)
    double m_psbR0;
    // Barrel EM (EmbMode = 1, EmbSampling 1-3) with the sampling, region and cell of the ATLAS simulation (F41 conserto 18):
    // fiducial cuts and Geometry::SampSeg of LArBarrelGeometry (see embSampSeg); the maker takes the steps of the whole
    // accordion (its radial limits are not applied) and keeps those of its own sampling and region.
    bool m_embSampSeg;
  public:
    /*! ATLAS SampSeg for the point (x, y, z), in mm: 1 if active (then region, sampling and eta index of the dictionary), 0 if
        not. Public so that the assignment can be tested from Python. */
    int embSampSeg( double x, double y, double z, int &region, int &sampling, int &ieta ) const;
  private:

    // Free-running hits (simu_trf.py --free-running-hits): every deposit of the ATLAS tile cells also goes, per PMT, with
    // the identifier and the time of the ATLAS simulation, to a per-event list written in the layout of the ATLAS HITS
    // ntuple (CaloFreeRunningHitWriter). See freeRunningTile.
    bool m_freeRunningHits;
    std::string m_freeRunningListKey;
    bool m_freeRunningBinning;
    // ATLAS identifier fields (free-running hits) and (r, z) centre (tileTime) of each cell (same order as m_cellEta;
    // geometry/python/v2/TILE.py)
    std::vector<int>   m_cellAtlasSection;
    std::vector<int>   m_cellAtlasTower;
    std::vector<int>   m_cellAtlasSampling;
    std::vector<float> m_cellRCentre;
    std::vector<float> m_cellZCentre;
    void freeRunningTile( SG::EventContext &ctx, const G4Step *step, int cell, int phiBin, float edep, float w0,
                          float w1, int npmt=2 ) const;
    // ATLAS time of a deposit in a tile cell (TileGeoG4SDCalc::MakePmtEdepTime with DoTOFCorrection): the global time tglobal of
    // the post-step point, the time t of the cell and the delays dtUp (PMT 1) and dtDown (PMT 0); see freeRunningTile
    void tileTime( const G4Step *step, int cell, int phiBin, int npmt, double &tglobal, double &t, double &dtUp,
                   double &dtDown ) const;

    // ATLAS-like LAr cells (F41 conserto 19; --atlas-emb-cells, --atlas-emec, --atlas-hec): the fields of the ATLAS identifier of
    // the cells of this maker (AtlasLArPart: 1 = LArEM, 2 = LArHEC, 0 = not set, the default; barrel_ec or pos_neg, sampling and
    // region of the dictionary, and the dictionary eta index of each cell, same order as m_cellEta). Part and barrel_ec choose the
    // point of the step for the ATLAS time (larHitTime: pre-step in the barrel, mean of pre- and post-step elsewhere); all of them
    // give the identifier of the free-running hits (freeRunningLAr).
    int m_atlasLArPart;
    int m_atlasBarrelEc;
    int m_atlasLArSampling;
    int m_atlasLArRegion;
    std::vector<int> m_cellAtlasEtaIndex;
    bool isAtlasLAr() const { return m_atlasLArPart > 0; }
    void freeRunningLAr( SG::EventContext &ctx, const G4Step *step, int cell, int phiBin, float edep ) const;
    // Shift (rad) of the phi edges of the cells, the half absorber of the ATLAS readout geometry (EMB and barrel presampler
    // -pi/1024 on side A, +pi/1024 on side C; EMEC and end-cap presampler -+pi/768; 0, the default, elsewhere). The phi
    // edges (PhiBins) come already shifted from Python; the maker uses it for the cells found from atan2 (emecFindCell).
    float m_phiShift;
    // Birks constant of the liquid argon (k of LArG4BirksLaw): 0.05832 (default; ATLAS barrel, presamplers and EMEC) or
    // 0.0486 (ATLAS HEC and FCAL, LArG4HECConfig.py)
    double m_birksLArK;

    // ATLAS FCal with its electrodes (F41 conserto 22; geometry/python/v1/FCAL.py, --atlas-fcal-cells): with FCalModule > 0
    // (1-3) the maker takes only the steps in the liquid argon gaps of its module (the logical volume FCalGapVolume), the cell
    // of a step is the tile of the copy number of its gap (FCalCopyEtaIndex, FCalCopyPhiIndex; the centre of the tile in
    // FCalCopyEta, FCalCopyPhi), as in the ATLAS simulation (LArFCALCalculatorBase), and the deposits go only to the
    // hit collection (one hit per tile, bin = 16 eta + phi, centre FCalCopyEta/Phi and width FCalCopyDeltaEta/Phi) and, with the
    // free-running hits, to LArHitFCAL. 0 (the default): off.
    int m_fcalModule;
    int m_fcalSide;
    std::string m_fcalGapVolume;
    std::vector<int>   m_fcalCopyEtaIndex;
    std::vector<int>   m_fcalCopyPhiIndex;
    std::vector<float> m_fcalCopyEta;
    std::vector<float> m_fcalCopyPhi;
    std::vector<float> m_fcalCopyDeltaEta;
    std::vector<float> m_fcalCopyDeltaPhi;
    std::map<std::pair<int,int>, std::pair<float,float>> m_fcalTileWidth;
    // the deposit of an FCal step or spot in the hit of its tile (hit collection of the normal chain)
    void fcalFillHit( SG::EventContext &ctx, int eta, int phi, float edep, float t ) const;
    bool isFCal() const { return m_fcalModule > 0; }
    void fcalStep( SG::EventContext &ctx, const G4Step *step ) const;
    // Frozen showers of the ATLAS FCal (F41 conserto 23): the grid indices (I, J) and position (mm) of each electrode, the tube map
    // of FCAL_ChannelMap (key ((J + 200) << 16) + (I + 200) -> tile eta and phi indices, the first tube and its position) and the
    // tile centre of each (eta, phi); a spot of a frozen shower is a G4Step without touchable (see fcalSpot).
    std::vector<int>   m_fcalCopyI;
    std::vector<int>   m_fcalCopyJ;
    std::vector<float> m_fcalCopyX;
    std::vector<float> m_fcalCopyY;
    std::map<unsigned int, std::pair<int,int>> m_fcalTubeMap;
    unsigned int m_fcalFirstTube;
    double m_fcalFirstTubeX, m_fcalFirstTubeY;
    std::map<std::pair<int,int>, std::pair<float,float>> m_fcalTileCentre;
    bool fcalTileID( double x, double y, int &eta, int &phi ) const;
    void fcalSpot( SG::EventContext &ctx, const G4Step *step ) const;
  public:
    /*! A step that is a spot of a frozen shower (no touchable). */
    static bool isShowerSpot( const G4Step *step );
  private:
};


#endif
