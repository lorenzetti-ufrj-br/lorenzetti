#ifndef CaloRingsConverter_h
#define CaloRingsConverter_h

#include "CaloRings/CaloRings.h"
#include "GaugiKernel/BranchSpec.h"
#include <vector>
#include <memory>
#include <string>
#include <map>
#include <cstdint>

class TTree;

#ifndef __CLING__
#include <arrow/api.h>
#endif

namespace xAOD {

  struct CaloRings_t {
    uint64_t           cluster_key_hash;
    uint32_t           cluster_index;
    std::vector<float> rings;
  };

#ifndef __CLING__
  struct CaloRings_parquet {
    std::shared_ptr<arrow::FloatBuilder> val_builder;
    std::unique_ptr<arrow::ListBuilder>  list_builder;

    struct ScalarRingBuilder {
      int index;
      std::unique_ptr<arrow::FloatBuilder> builder;
    };
    std::vector<ScalarRingBuilder> scalar_builders;
    std::vector<arrow::ArrayBuilder*> builders;
  };
#endif

  class CaloRingsConverter {
  public:
    CaloRingsConverter() = default;
    ~CaloRingsConverter() = default;

    // Convert an EDM class object into a persistent struct
    bool convert(const CaloRings *rings, CaloRings_t &rings_t) const;

    // Convert a persistent struct into an EDM class object
    bool convert(const CaloRings_t &rings_t, CaloRings *&rings) const;

    // Ntuple (TTree)
    void book_ntuple(TTree *tree, CaloRings_t &buf,
                     std::vector<float> *&ringsPtr,
                     std::map<std::string, float> &scalarRings,
                     const std::vector<Gaugi::BranchSpec> &specs = {},
                     const std::string &defaultName = "rings") const;
    void to_ntuple(const CaloRings *rings, CaloRings_t &buf,
                   std::map<std::string, float> &scalarRings,
                   const std::vector<Gaugi::BranchSpec> &specs = {}) const;

#ifndef __CLING__
    // Parquet (Arrow)
    void book_parquet(std::vector<std::shared_ptr<arrow::Field>> &fields,
                      CaloRings_parquet &buf_parquet,
                      const std::vector<Gaugi::BranchSpec> &specs = {},
                      const std::string &defaultName = "rings") const;
    void to_parquet(const CaloRings_t &buf, CaloRings_parquet &buf_parquet) const;
    void to_parquet(const CaloRings *rings, CaloRings_parquet &buf_parquet) const;
#endif
  };

} // namespace xAOD

#endif
