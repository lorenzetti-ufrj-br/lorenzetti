#ifndef TruthParticleConverter_h
#define TruthParticleConverter_h

#include "TruthParticle/TruthParticle.h"
#include "TruthParticle/TruthParticleContainer.h"
#include "GaugiKernel/BranchSpec.h"
#include <vector>
#include <memory>
#include <string>
#include <cstdint>

class TTree;

#ifndef __CLING__
#include <arrow/api.h>
#endif

namespace xAOD {

  struct TruthParticle_t {
    int      pdgid;
    uint64_t seed_key_hash;
    uint32_t seed_index;
    int      seedid;
    float    e;
    float    et;
    float    eta;
    float    phi;
    float    px;
    float    py;
    float    pz;
    float    vx; // vertex position x (prod_vx)
    float    vy; // vertex position y
    float    vz; // vertex position z
  };

  struct TruthParticleNtupleBuffers {
    std::vector<float> *pdgid{nullptr};
    std::vector<float> *eta{nullptr};
    std::vector<float> *phi{nullptr};
    std::vector<float> *e{nullptr};
    std::vector<float> *et{nullptr};

    void init() {
      if (!pdgid) pdgid = new std::vector<float>();
      if (!eta)   eta   = new std::vector<float>();
      if (!phi)   phi   = new std::vector<float>();
      if (!e)     e     = new std::vector<float>();
      if (!et)    et    = new std::vector<float>();
    }

    void clear() {
      if (pdgid) pdgid->clear();
      if (eta)   eta->clear();
      if (phi)   phi->clear();
      if (e)     e->clear();
      if (et)    et->clear();
    }
  };

#ifndef __CLING__
  struct TruthParticle_parquet {
    std::shared_ptr<arrow::FloatBuilder> val_pdgid, val_eta, val_phi, val_e, val_et;
    std::unique_ptr<arrow::ListBuilder>  list_pdgid, list_eta, list_phi, list_e, list_et;
    std::vector<arrow::ArrayBuilder*> builders;
  };
#endif

  class TruthParticleConverter {
  public:
    TruthParticleConverter() = default;
    ~TruthParticleConverter() = default;

    bool convert(const TruthParticle *truth, TruthParticle_t &truth_t) const;
    bool convert(const TruthParticle_t &truth_t, TruthParticle *&truth) const;

    // Ntuple (TTree)
    void book_ntuple(TTree *tree, TruthParticleNtupleBuffers &buf,
                     const std::vector<Gaugi::BranchSpec> &specs = {},
                     const std::string &defaultPrefix = "mc_") const;
    void to_ntuple(const TruthParticleContainer *container, int seedid,
                   TruthParticleNtupleBuffers &buf) const;

#ifndef __CLING__
    // Parquet (Arrow)
    void book_parquet(std::vector<std::shared_ptr<arrow::Field>> &fields,
                      TruthParticle_parquet &buf_parquet,
                      const std::vector<Gaugi::BranchSpec> &specs = {},
                      const std::string &defaultPrefix = "mc_") const;
    void to_parquet(const TruthParticleContainer *container, int seedid,
                    TruthParticle_parquet &buf_parquet) const;
#endif
  };

} // namespace xAOD

#endif
