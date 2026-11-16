#ifndef CaloFreeRunningHitList_h
#define CaloFreeRunningHitList_h

#include "GaugiKernel/DataHandle.h"
#include <cmath>
#include <map>
#include <tuple>
#include <vector>

/**
 * @class CaloFreeRunningHitList
 * @brief Per-event list of the tile hits in the layout of the ATLAS HITS ntuple (one entry per PMT and time bin, or per
 *        PMT and Geant4 step without binning), and of the ATLAS-like LAr and FCal cells (one entry per cell and time bin,
 *        see addLAr; F41 consertos 19 and 22), filled by CaloHitMaker when simu_trf.py runs with --free-running-hits and
 *        written by CaloFreeRunningHitWriter.
 *
 * With binning (bin width delta > 0), add() follows TileSimHit::add of the ATLAS simulation (Athena,
 * TileCalorimeter/TileSimEvent/src/TileSimHit.cxx): a deposit of a PMT goes to an existing bin of the same PMT when
 * |t - t_bin| < delta/2, otherwise it opens a new bin at t = delta * nearbyint(t/delta). The energies of a bin are summed;
 * the extra tglobal of a bin is the energy weighted mean of the Geant4 global times of its deposits.
 *
 * The event context only gives const access to recorded objects, so the vectors are mutable and add() is const (the
 * same situation as CaloHitMaker filling the CaloHit objects of a const collection). Each event is simulated by a single
 * thread, so the list of an event is never filled concurrently.
 */
class CaloFreeRunningHitList : public SG::DataHandle
{
  public:

    CaloFreeRunningHitList()=default;
    ~CaloFreeRunningHitList()=default;

    void add( long long cellID, double energy, double time, double tglobal, double eta, double phi,
              int sampling, int side, int module, int tower, double delta ) const
    {
      if( delta > 0 ){
        auto &bins = m_bins[cellID];
        for( size_t i : bins ){
          if( std::fabs(time - m_time[i]) < delta/2. ){
            m_energy[i]    += energy;
            m_sumETglobal[i] += energy * tglobal;
            return;
          }
        }
        bins.push_back( m_cellID.size() );
        push( cellID, energy, delta * std::nearbyint(time/delta), tglobal, eta, phi, sampling, side, module, tower );
      }else{
        push( cellID, energy, time, tglobal, eta, phi, sampling, side, module, tower );
      }
    }

    /*! LAr deposit (F41 conserto 19): with timeBin >= 0 the deposits of a cell in the same time bin (LArG4SimpleSD,
        TimeBinType Default) go to one entry, with the energy weighted mean time (LArHit::Add and finalize); timeBin < 0:
        one entry per deposit. det: 1 = EMB, 2 = EMEC, 3 = HEC, 4 = FCAL (F41 conserto 22; the container of the ATLAS ntuple).
        The fields sampling, barrel_ec (or pos_neg) and region of the dictionary go to sampling, side and module; in the FCAL,
        the module goes to sampling and pos_neg to side. source: the sensitive detector of the ATLAS simulation that makes the hit
        (0: the Geant4 steps; 1: the spots of the frozen showers, the FCALFastSimDedicatedSD of Athena). Each source keeps its own
        entries, as each SD of the SimpleSDWrapper of Athena keeps its own time bins and all write to the same collection without
        merging (FCALSDTool, SDWrapper::EndOfAthenaEvent, release 23.0.14; F41 conserto 28): a cell can have one entry per source
        in the same time bin. */
    void addLAr( long long cellID, double energy, double time, double tglobal, double eta, double phi,
                 int sampling, int barrelEc, int region, int det, int timeBin, int source = 0 ) const
    {
      if( timeBin >= 0 ){
        auto &entry = m_larBins[std::make_tuple(cellID, timeBin, source)];
        if( entry > 0 ){
          size_t i = entry - 1;
          m_energy[i] += energy;  m_sumET[i] += energy * time;  m_sumETglobal[i] += energy * tglobal;
          return;
        }
        entry = m_cellID.size() + 1;
      }
      push( cellID, energy, time, tglobal, eta, phi, sampling, barrelEc, region, 0, det );
      m_source.back() = source;
    }

    size_t size() const { return m_cellID.size(); }
    /*! 0 = tile, 1 = EMB, 2 = EMEC, 3 = HEC, 4 = FCAL */
    const std::vector<int>&       det()      const { return m_det;      }
    /*! sensitive detector that made the entry (addLAr): 0 = Geant4 steps, 1 = frozen shower spots */
    const std::vector<int>&       source()   const { return m_source;   }
    /*! hit time: the bin centre (tile, with binning) or the energy weighted mean time of the entry (LAr) [ns] */
    std::vector<double> hitTime() const
    {
      std::vector<double> t( m_cellID.size() );
      for( size_t i=0; i<t.size(); ++i )
        t[i] = ( m_det[i] > 0 && m_energy[i] > 0 ) ? m_sumET[i] / m_energy[i] : m_time[i];
      return t;
    }

    const std::vector<long long>& cellID()   const { return m_cellID;   }
    const std::vector<double>&    energy()   const { return m_energy;   }
    const std::vector<double>&    time()     const { return m_time;     }
    const std::vector<double>&    eta()      const { return m_eta;      }
    const std::vector<double>&    phi()      const { return m_phi;      }
    const std::vector<int>&       sampling() const { return m_sampling; }
    const std::vector<int>&       side()     const { return m_side;     }
    const std::vector<int>&       module()   const { return m_module;   }
    const std::vector<int>&       tower()    const { return m_tower;    }
    /*! energy weighted mean of the Geant4 global times of the deposits of each entry [ns] */
    std::vector<double> tglobal() const
    {
      std::vector<double> t( m_cellID.size() );
      for( size_t i=0; i<t.size(); ++i ) t[i] = m_energy[i] > 0 ? m_sumETglobal[i] / m_energy[i] : m_firstTglobal[i];
      return t;
    }

  private:

    void push( long long cellID, double energy, double time, double tglobal, double eta, double phi,
               int sampling, int side, int module, int tower, int det = 0 ) const
    {
      m_cellID.push_back(cellID);   m_energy.push_back(energy);   m_time.push_back(time);
      m_sumET.push_back(energy * time);   m_det.push_back(det);   m_source.push_back(0);
      m_sumETglobal.push_back(energy * tglobal);   m_firstTglobal.push_back(tglobal);
      m_eta.push_back(eta);   m_phi.push_back(phi);
      m_sampling.push_back(sampling);   m_side.push_back(side);   m_module.push_back(module);   m_tower.push_back(tower);
    }

    /*! ATLAS PMT identifier (64-bit compact Identifier of the ATLAS identifier dictionary) */
    mutable std::vector<long long> m_cellID;
    /*! visible energy [MeV] */
    mutable std::vector<double>    m_energy;
    /*! hit time of the ATLAS simulation (TileGeoG4SDCalc) [ns]; bin centre with binning */
    mutable std::vector<double>    m_time;
    mutable std::vector<double>    m_sumETglobal;
    mutable std::vector<double>    m_firstTglobal;
    /*! centre of the cell in eta, centre of the module in phi */
    mutable std::vector<double>    m_eta;
    mutable std::vector<double>    m_phi;
    /*! ATLAS fields: sampling (0 A, 1 BC/B, 2 D), side (+1 for z > 0), module (0-63), tower */
    mutable std::vector<int>       m_sampling;
    mutable std::vector<int>       m_side;
    mutable std::vector<int>       m_module;
    mutable std::vector<int>       m_tower;
    /*! entries (bins) of each PMT, for the binning */
    mutable std::map<long long, std::vector<size_t>> m_bins;
    /*! LAr: sum of energy x time of each entry, detector of each entry, and entry + 1 of each (cell, time bin) */
    mutable std::vector<double>    m_sumET;
    mutable std::vector<int>       m_det;
    mutable std::vector<int>       m_source;
    mutable std::map<std::tuple<long long, int, int>, size_t> m_larBins;
};

#endif
