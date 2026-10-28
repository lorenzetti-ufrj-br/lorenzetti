#include "EventInfo/EventInfoConverter.h"
#include "TTree.h"

#include <parquet/arrow/writer.h>

using namespace xAOD;

bool EventInfoConverter::convert(const EventInfo *event, EventInfo_t &event_t) const {
  if (event) {
    event_t.runNumber   = event->runNumber();
    event_t.eventNumber = event->eventNumber();
    event_t.avgmu       = event->avgmu();
    event_t.totmu       = event->totmu();
    return true;
  }
  return false;
}

bool EventInfoConverter::convert(const EventInfo_t &event_t, EventInfo *&event) const {
  event = new xAOD::EventInfo();
  event->setRunNumber(event_t.runNumber);
  event->setEventNumber(event_t.eventNumber);
  event->setAvgmu(event_t.avgmu);
  event->setTotmu(event_t.totmu);
  return true;
}

void EventInfoConverter::book_ntuple(TTree *tree, EventInfo_t &buf,
                                     const std::vector<Gaugi::BranchSpec> &specs,
                                     const std::string &defaultPrefix) const {
  if (!tree) return;
  if (specs.empty()) {
    Gaugi::bindOrBranch(tree, defaultPrefix + "EventNumber", &buf.eventNumber);
    Gaugi::bindOrBranch(tree, defaultPrefix + "RunNumber",   &buf.runNumber);
    Gaugi::bindOrBranch(tree, defaultPrefix + "avgmu",       &buf.avgmu);
    Gaugi::bindOrBranch(tree, defaultPrefix + "totmu",       &buf.totmu);
  } else {
    for (const auto &spec : specs) {
      if      (spec.fieldName == "eventNumber" || spec.fieldName == "EventNumber") Gaugi::bindOrBranch(tree, spec.branchName, &buf.eventNumber);
      else if (spec.fieldName == "runNumber"   || spec.fieldName == "RunNumber")   Gaugi::bindOrBranch(tree, spec.branchName, &buf.runNumber);
      else if (spec.fieldName == "avgmu")                                           Gaugi::bindOrBranch(tree, spec.branchName, &buf.avgmu);
      else if (spec.fieldName == "totmu")                                           Gaugi::bindOrBranch(tree, spec.branchName, &buf.totmu);
    }
  }
}

void EventInfoConverter::to_ntuple(const EventInfo *info, EventInfo_t &buf) const {
  convert(info, buf);
}

void EventInfoConverter::book_parquet(std::vector<std::shared_ptr<arrow::Field>> &fields,
                                      EventInfo_parquet &buf_parquet,
                                      const std::vector<Gaugi::BranchSpec> &specs,
                                      const std::string &defaultPrefix) const {
  buf_parquet.builders.clear();
  if (specs.empty()) {
    buf_parquet.b_eventNumber = std::make_unique<arrow::Int32Builder>();
    fields.push_back(arrow::field(defaultPrefix + "EventNumber", arrow::int32()));
    buf_parquet.builders.push_back(buf_parquet.b_eventNumber.get());

    buf_parquet.b_runNumber = std::make_unique<arrow::Int32Builder>();
    fields.push_back(arrow::field(defaultPrefix + "RunNumber", arrow::int32()));
    buf_parquet.builders.push_back(buf_parquet.b_runNumber.get());

    buf_parquet.b_avgmu = std::make_unique<arrow::FloatBuilder>();
    fields.push_back(arrow::field(defaultPrefix + "avgmu", arrow::float32()));
    buf_parquet.builders.push_back(buf_parquet.b_avgmu.get());

    buf_parquet.b_totmu = std::make_unique<arrow::FloatBuilder>();
    fields.push_back(arrow::field(defaultPrefix + "totmu", arrow::float32()));
    buf_parquet.builders.push_back(buf_parquet.b_totmu.get());
  } else {
    for (const auto &spec : specs) {
      if (spec.fieldName == "eventNumber" || spec.fieldName == "EventNumber") {
        buf_parquet.b_eventNumber = std::make_unique<arrow::Int32Builder>();
        fields.push_back(arrow::field(spec.branchName, arrow::int32()));
        buf_parquet.builders.push_back(buf_parquet.b_eventNumber.get());
      } else if (spec.fieldName == "runNumber" || spec.fieldName == "RunNumber") {
        buf_parquet.b_runNumber = std::make_unique<arrow::Int32Builder>();
        fields.push_back(arrow::field(spec.branchName, arrow::int32()));
        buf_parquet.builders.push_back(buf_parquet.b_runNumber.get());
      } else if (spec.fieldName == "avgmu") {
        buf_parquet.b_avgmu = std::make_unique<arrow::FloatBuilder>();
        fields.push_back(arrow::field(spec.branchName, arrow::float32()));
        buf_parquet.builders.push_back(buf_parquet.b_avgmu.get());
      } else if (spec.fieldName == "totmu") {
        buf_parquet.b_totmu = std::make_unique<arrow::FloatBuilder>();
        fields.push_back(arrow::field(spec.branchName, arrow::float32()));
        buf_parquet.builders.push_back(buf_parquet.b_totmu.get());
      }
    }
  }
}

void EventInfoConverter::to_parquet(const EventInfo_t &buf, EventInfo_parquet &buf_parquet) const {
  if (buf_parquet.b_eventNumber != nullptr) PARQUET_THROW_NOT_OK(buf_parquet.b_eventNumber->Append(static_cast<int32_t>(buf.eventNumber)));
  if (buf_parquet.b_runNumber != nullptr)   PARQUET_THROW_NOT_OK(buf_parquet.b_runNumber->Append(static_cast<int32_t>(buf.runNumber)));
  if (buf_parquet.b_avgmu != nullptr)       PARQUET_THROW_NOT_OK(buf_parquet.b_avgmu->Append(buf.avgmu));
  if (buf_parquet.b_totmu != nullptr)       PARQUET_THROW_NOT_OK(buf_parquet.b_totmu->Append(buf.totmu));
}

void EventInfoConverter::to_parquet(const EventInfo *info, EventInfo_parquet &buf_parquet) const {
  EventInfo_t buf;
  convert(info, buf);
  to_parquet(buf, buf_parquet);
}
