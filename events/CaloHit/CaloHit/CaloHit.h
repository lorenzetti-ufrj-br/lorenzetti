#ifndef CaloHit_h
#define CaloHit_h

#include "CaloCell/enumeration.h"
#include "GaugiKernel/EDM.h"
#include "GaugiKernel/macros.h"
#include "G4Step.hh"
#include "globals.hh"



namespace xAOD{

  class CaloHit: public Gaugi::EDM
  {  
    public:

      CaloHit():EDM(){};

      /** Contructor **/
      CaloHit( 
               // eta/phi position at the detector, deta/dphi size into the detector, radius
               float eta, 
               float phi, 
               float deta, 
               float dphi,
               // Hash
               unsigned long int hash,
               // Hit identification
               CaloSampling sampling, 
               Detector detector,
               // bunch crossing information
               float bc_duration, 
               int bcid_start, 
               int bcid_end 
              );

      /** Destructor **/
      ~CaloHit()=default;
      
      /*! Fill the deposit energy into the Hit */
      void fill( const G4Step * );
      void fill( const G4Step *, float sampNoiseStd ); // 
      // Same as above, with the energy given by the caller (e.g. after Birks' law)
      void fill( const G4Step *, float sampNoiseStd, float edep );
      /*! Dual readout of the tile cells (two photomultipliers per cell, as in ATLAS): add the energy seen by
          each PMT, already weighted by the caller, in the bunch crossing of the step. Used only when the
          cell was created with setDualReadout(true). */
      void fillPmt( const G4Step *, float edep_pmt0, float edep_pmt1 );
      /*! Same as fill( step, sampNoiseStd, edep ) and fillPmt, with the time (ns) that chooses the bunch crossing given by the
          caller instead of the global time of the pre-step point (the ATLAS time, CaloHitMaker AtlasHitTime). fillPmtAt takes
          the time of each PMT. */
      void fillAt( float t, float sampNoiseStd, float edep );
      void fillPmtAt( float t0, float edep_pmt0, float t1, float edep_pmt1 );
      /** Zeroize the pulse/sample vectors **/
      void clear();


      /*
       * Hit identification
       */

      /*! Hit eta center */
      PRIMITIVE_SETTER_AND_GETTER( float, m_eta, setEta, eta );
      /*! Hit phi center */
      PRIMITIVE_SETTER_AND_GETTER( float, m_phi, setPhi, phi );
      /*! Hit delta eta */
      PRIMITIVE_SETTER_AND_GETTER( float, m_deta, setDeltaEta , deltaEta);
      /*! Hit delta phi */
      PRIMITIVE_SETTER_AND_GETTER( float, m_dphi, setDeltaPhi, deltaPhi );
      /*! Hit hash */
      PRIMITIVE_SETTER_AND_GETTER( unsigned long int, m_hash, setHash, hash );
      /*! Hit sampling id */
      PRIMITIVE_SETTER_AND_GETTER( CaloSampling  , m_sampling , setSampling   , sampling  );
      /*! Hit layer id */
      PRIMITIVE_SETTER_AND_GETTER( Detector  , m_detector  , setDetector    , detector   );
     



      /*! Energy deposity from simulated hits **/
      float edep( int bc_id=0 ) const{
        if (m_edep.count(bc_id)){
          return m_edep.at(bc_id);
        }else{// return zero case bc not exist
          return 0;
        }
      }

      void edep( int bc_id, float e ){
        m_edep[bc_id] += e;
      }

      /*! Dual readout of the tile cells: energy seen by the PMT 0 or 1 per bunch crossing **/
      float edepPmt( int pmt, int bc_id=0 ) const{
        const auto &m = m_edepPmt[pmt ? 1 : 0];
        return m.count(bc_id) ? m.at(bc_id) : 0;
      }

      void edepPmt( int pmt, int bc_id, float e ){
        m_edepPmt[pmt ? 1 : 0][bc_id] += e;
      }

      /*! True when the cell is read by two PMTs (tile cells with the dual readout option) */
      PRIMITIVE_SETTER_AND_GETTER( bool, m_dualReadout, setDualReadout, dualReadout );

      /*! Time of flight from simulated hits **/ //
      float tof( int bc_id=0 ) const{
        if (m_tof.count(bc_id)){
          return m_tof.at(bc_id);
        }else{// return zero case bc not exist
          return 0;
        }
      }


      void tof( int bc_id, float t ){ //setter
        m_tof[bc_id] = t;
        // if (m_tof[bc_id] == float(0)){
        //   m_tof[bc_id] = t;
        // }
        // else{
        //   m_tof[bc_id] = (m_tof[bc_id] + t)/2; //simple moving average with w=2
        // }
      }
      
      /*
       * Bunch crossing information
       */

      /*! Bunch crossing id start */
      PRIMITIVE_SETTER_AND_GETTER( int, m_bcid_start  , set_bcid_start  , bcid_start    );
      /*! Bunch crossing id end */
      PRIMITIVE_SETTER_AND_GETTER( int, m_bcid_end    , set_bcid_end    , bcid_end      );
      /* Time space (in ns) between two bunch crossings */
      PRIMITIVE_SETTER_AND_GETTER( float, m_bc_duration , set_bc_duration , bc_duration );
      /*! Time (in ns) for each bunch crossing */
      PRIMITIVE_SETTER_AND_GETTER( std::vector<float> , m_time , setTime , time   );



    private:
 
      int find( float value) const ;
       

      /*! id sample */
      CaloSampling m_sampling;
      /*! id layer */
      Detector m_detector;

      
      /*! eta center */
      float m_eta;
      /*! phi center */
      float m_phi;
      /*! delta eta */
      float m_deta;
      /*! delta phi */
      float m_dphi;
      /*! bunch crossing start id */
      int m_bcid_start;
      /*! bunch crossing end id */
      int m_bcid_end;
      /*! bunch crossing space in ns between two bunchs */
      float m_bc_duration;


      /*! time (in ns) for each bunch between bcid_start and bcid_end */
      std::vector<float> m_time;
      /*! energy deposit between bcid_start and bcid_end */
      std::map< int, float> m_edep;
      /*!time of flight of a particle between bcid_start and bcid_end */
      std::map< int, float> m_tof;
      /*! energy seen by each of the two PMTs between bcid_start and bcid_end (dual readout only) */
      std::map< int, float> m_edepPmt[2];
      bool m_dualReadout = false;
      bool m_firstHit = false;
      /*! Access information unique ID number */
      unsigned long int m_hash;

  };

}
#endif
