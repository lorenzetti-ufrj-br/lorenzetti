#ifndef CaloClusterConverter_h
#define CaloClusterConverter_h

/** simulator includes **/
#include "CaloCluster/CaloCluster.h"
#include "GaugiKernel/BranchSpec.h"
#include <map>
#include <vector>
#include <memory>
#include <string>
#include <cstdint>

class TTree;

#ifndef __CLING__
#include <arrow/api.h>
#endif

namespace xAOD {

  typedef std::map<int, const xAOD::CaloCluster*> cluster_links_t;

  struct CaloCluster_t {
    float e;
    float et;
    float eta;
    float phi;
    float deta;
    float dphi;
    float e0;
    float e1;
    float e2;
    float e3;
    float ehad1;
    float ehad2;
    float ehad3;
    float etot;
    float e233;
    float e237;
    float e277;
    float emaxs1;
    float emaxs2;
    float e2tsts1;
    float reta;
    float rphi;
    float rhad;
    float rhad1;
    float eratio;
    float f0;
    float f1;
    float f2;
    float f3;
    float weta2;
    float secondR;
    float lambdaCenter;
    float secondLambda;
    float fracMax;
    float lateralMom;
    float longitudinalMom;
    std::vector<unsigned long int> cell_links;
    
    uint64_t cells_key_hash;
    std::vector<uint32_t> cell_indices;

    uint64_t seed_key_hash;
    uint32_t seed_index;
  };

#ifndef __CLING__
  struct CaloCluster_parquet {
    std::unique_ptr<arrow::FloatBuilder> b_e;
    std::unique_ptr<arrow::FloatBuilder> b_et;
    std::unique_ptr<arrow::FloatBuilder> b_eta;
    std::unique_ptr<arrow::FloatBuilder> b_phi;
    std::unique_ptr<arrow::FloatBuilder> b_deta;
    std::unique_ptr<arrow::FloatBuilder> b_dphi;
    std::unique_ptr<arrow::FloatBuilder> b_e0, b_e1, b_e2, b_e3;
    std::unique_ptr<arrow::FloatBuilder> b_ehad1, b_ehad2, b_ehad3, b_etot;
    std::unique_ptr<arrow::FloatBuilder> b_e233, b_e237, b_e277, b_emaxs1, b_emaxs2, b_e2tsts1;
    std::unique_ptr<arrow::FloatBuilder> b_reta, b_rphi, b_rhad, b_rhad1, b_eratio;
    std::unique_ptr<arrow::FloatBuilder> b_f0, b_f1, b_f2, b_f3, b_weta2;
    std::unique_ptr<arrow::FloatBuilder> b_secondR, b_lambdaCenter, b_secondLambda, b_fracMax;
    std::unique_ptr<arrow::FloatBuilder> b_lateralMom, b_longitudinalMom;
    std::vector<arrow::ArrayBuilder*> builders;
  };
#endif

  class CaloClusterConverter {
  public:
    CaloClusterConverter() = default;
    ~CaloClusterConverter() = default;

    // Convert an EDM class object into a persistent struct
    bool convert(const CaloCluster *clus, CaloCluster_t &clus_t) const;

    // Convert a persistent struct into an EDM class object
    bool convert(const CaloCluster_t &cluster_t, CaloCluster *&cluster) const;

    // Ntuple (TTree)
    void book_ntuple(TTree *tree, CaloCluster_t &buf,
                     const std::vector<Gaugi::BranchSpec> &specs = {},
                     const std::string &defaultPrefix = "cl_") const;
    void to_ntuple(const CaloCluster *clus, CaloCluster_t &buf) const;

#ifndef __CLING__
    // Parquet (Arrow)
    void book_parquet(std::vector<std::shared_ptr<arrow::Field>> &fields,
                      CaloCluster_parquet &buf_parquet,
                      const std::vector<Gaugi::BranchSpec> &specs = {},
                      const std::string &defaultPrefix = "cl_") const;
    void to_parquet(const CaloCluster_t &buf, CaloCluster_parquet &buf_parquet) const;
    void to_parquet(const CaloCluster *clus, CaloCluster_parquet &buf_parquet) const;
#endif
  };

} // namespace xAOD

#endif