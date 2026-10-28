#ifndef EventInfoConverter_h
#define EventInfoConverter_h

/** simulator includes **/
#include "EventInfo/EventInfoContainer.h"
#include "GaugiKernel/BranchSpec.h"
#include <vector>
#include <memory>
#include <string>

class TTree;

#ifndef __CLING__
#include <arrow/api.h>
#endif

namespace xAOD {

    struct EventInfo_t {
        float runNumber;
        float eventNumber;
        float avgmu;
        float totmu;
    };

#ifndef __CLING__
    struct EventInfo_parquet {
        std::unique_ptr<arrow::Int32Builder> b_eventNumber;
        std::unique_ptr<arrow::Int32Builder> b_runNumber;
        std::unique_ptr<arrow::FloatBuilder> b_avgmu;
        std::unique_ptr<arrow::FloatBuilder> b_totmu;
        std::vector<arrow::ArrayBuilder*> builders;
    };
#endif

    class EventInfoConverter {
    public:
        EventInfoConverter() = default;
        ~EventInfoConverter() = default;

        // convert a class object into a struct
        bool convert(const EventInfo *info, EventInfo_t &info_t) const;
        bool convert(const EventInfo_t &info_t, EventInfo *&info) const;

        // Ntuple (TTree)
        void book_ntuple(TTree *tree, EventInfo_t &buf,
                         const std::vector<Gaugi::BranchSpec> &specs = {},
                         const std::string &defaultPrefix = "") const;
        void to_ntuple(const EventInfo *info, EventInfo_t &buf) const;

#ifndef __CLING__
        // Parquet (Arrow)
        void book_parquet(std::vector<std::shared_ptr<arrow::Field>> &fields,
                          EventInfo_parquet &buf_parquet,
                          const std::vector<Gaugi::BranchSpec> &specs = {},
                          const std::string &defaultPrefix = "") const;
        void to_parquet(const EventInfo_t &buf, EventInfo_parquet &buf_parquet) const;
        void to_parquet(const EventInfo *info, EventInfo_parquet &buf_parquet) const;
#endif
    };

} // namespace xAOD

#endif
