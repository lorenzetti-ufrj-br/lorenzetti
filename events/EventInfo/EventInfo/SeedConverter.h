#ifndef SeedConverter_h
#define SeedConverter_h

/** simulator includes **/
#include "EventInfo/SeedContainer.h"
#include "GaugiKernel/BranchSpec.h"
#include <vector>
#include <memory>
#include <string>

class TTree;

#ifndef __CLING__
#include <arrow/api.h>
#endif

namespace xAOD {

    typedef std::map<int, const xAOD::Seed*> seed_links_t;

    struct Seed_t {
        int id;
        float e;
        float et;
        float eta;
        float phi;
    };

#ifndef __CLING__
    struct Seed_parquet {
        std::unique_ptr<arrow::Int32Builder> b_id;
        std::unique_ptr<arrow::FloatBuilder> b_e;
        std::unique_ptr<arrow::FloatBuilder> b_et;
        std::unique_ptr<arrow::FloatBuilder> b_eta;
        std::unique_ptr<arrow::FloatBuilder> b_phi;
        std::vector<arrow::ArrayBuilder*> builders;
    };
#endif

    class SeedConverter {
    public:
        SeedConverter() = default;
        ~SeedConverter() = default;

        // convert a class object into a struct
        bool convert(const Seed *seed, Seed_t &seed_t) const;
        bool convert(const Seed_t &seed_t, Seed *&seed) const;

        // Ntuple (TTree)
        void book_ntuple(TTree *tree, Seed_t &buf,
                         const std::vector<Gaugi::BranchSpec> &specs = {},
                         const std::string &defaultPrefix = "seed_") const;
        void to_ntuple(const Seed *seed, Seed_t &buf) const;

#ifndef __CLING__
        // Parquet (Arrow)
        void book_parquet(std::vector<std::shared_ptr<arrow::Field>> &fields,
                          Seed_parquet &buf_parquet,
                          const std::vector<Gaugi::BranchSpec> &specs = {},
                          const std::string &defaultPrefix = "seed_") const;
        void to_parquet(const Seed_t &buf, Seed_parquet &buf_parquet) const;
        void to_parquet(const Seed *seed, Seed_parquet &buf_parquet) const;
#endif
    };

} // namespace xAOD

#endif
