#ifndef ElectronConverter_h
#define ElectronConverter_h

#include "Egamma/Electron.h"
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

  struct Electron_t {
    uint64_t          cluster_key_hash;
    uint32_t          cluster_index;
    float             e;
    float             et;
    float             eta;
    float             phi;
    std::vector<bool> isEM;
  };

  struct ElectronNtupleScalars {
    bool tight{false};
    bool medium{false};
    bool loose{false};
    bool vloose{false};
  };

#ifndef __CLING__
  struct Electron_parquet {
    std::unique_ptr<arrow::FloatBuilder>   b_e, b_et, b_eta, b_phi;
    std::unique_ptr<arrow::BooleanBuilder> b_tight, b_medium, b_loose, b_vloose;
    std::vector<arrow::ArrayBuilder*> builders;
  };
#endif

  class ElectronConverter {
  public:
    ElectronConverter() = default;
    ~ElectronConverter() = default;

    // Convert an EDM class object into a persistent struct
    bool convert(const Electron *electron, Electron_t &electron_t) const;

    // Convert a persistent struct into an EDM class object
    bool convert(const Electron_t &electron_t, Electron *&electron) const;

    // Ntuple (TTree)
    void book_ntuple(TTree *tree, Electron_t &buf, ElectronNtupleScalars &scalars,
                     const std::vector<Gaugi::BranchSpec> &specs = {},
                     const std::string &defaultPrefix = "el_") const;
    void to_ntuple(const Electron *el, Electron_t &buf, ElectronNtupleScalars &scalars) const;

#ifndef __CLING__
    // Parquet (Arrow)
    void book_parquet(std::vector<std::shared_ptr<arrow::Field>> &fields,
                      Electron_parquet &buf_parquet,
                      const std::vector<Gaugi::BranchSpec> &specs = {},
                      const std::string &defaultPrefix = "el_") const;
    void to_parquet(const Electron_t &buf, const ElectronNtupleScalars &scalars, Electron_parquet &buf_parquet) const;
    void to_parquet(const Electron *el, Electron_parquet &buf_parquet) const;
#endif
  };

} // namespace xAOD

#endif
