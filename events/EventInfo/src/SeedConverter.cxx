#include "EventInfo/SeedConverter.h"
#include "TTree.h"

#include <parquet/arrow/writer.h>

using namespace xAOD;

bool SeedConverter::convert(const Seed *seed, Seed_t &seed_t) const {
  if (seed) {
    seed_t.id  = seed->id();
    seed_t.e   = seed->e();
    seed_t.et  = seed->et();
    seed_t.eta = seed->eta();
    seed_t.phi = seed->phi();
    return true;
  }
  return false;
}

bool SeedConverter::convert(const Seed_t &seed_t, Seed *&seed) const {
  seed = new xAOD::Seed(seed_t.id,
                        seed_t.e,
                        seed_t.et,
                        seed_t.eta,
                        seed_t.phi);
  return true;
}

void SeedConverter::book_ntuple(TTree *tree, Seed_t &buf,
                                const std::vector<Gaugi::BranchSpec> &specs,
                                const std::string &defaultPrefix) const {
  if (!tree) return;
  if (specs.empty()) {
    Gaugi::bindOrBranch(tree, defaultPrefix + "eta", &buf.eta);
    Gaugi::bindOrBranch(tree, defaultPrefix + "phi", &buf.phi);
    Gaugi::bindOrBranch(tree, defaultPrefix + "e",   &buf.e);
    Gaugi::bindOrBranch(tree, defaultPrefix + "et",  &buf.et);
  } else {
    for (const auto &spec : specs) {
      if      (spec.fieldName == "eta") Gaugi::bindOrBranch(tree, spec.branchName, &buf.eta);
      else if (spec.fieldName == "phi") Gaugi::bindOrBranch(tree, spec.branchName, &buf.phi);
      else if (spec.fieldName == "e")   Gaugi::bindOrBranch(tree, spec.branchName, &buf.e);
      else if (spec.fieldName == "et")  Gaugi::bindOrBranch(tree, spec.branchName, &buf.et);
      else if (spec.fieldName == "id")  Gaugi::bindOrBranch(tree, spec.branchName, &buf.id);
    }
  }
}

void SeedConverter::to_ntuple(const Seed *seed, Seed_t &buf) const {
  if (!seed) {
    buf.id = -1; buf.e = 0; buf.et = 0; buf.eta = 0; buf.phi = 0;
    return;
  }
  convert(seed, buf);
}

void SeedConverter::book_parquet(std::vector<std::shared_ptr<arrow::Field>> &fields,
                                 Seed_parquet &buf_parquet,
                                 const std::vector<Gaugi::BranchSpec> &specs,
                                 const std::string &defaultPrefix) const {
  buf_parquet.builders.clear();
  if (specs.empty()) {
    buf_parquet.b_eta = std::make_unique<arrow::FloatBuilder>();
    fields.push_back(arrow::field(defaultPrefix + "eta", arrow::float32()));
    buf_parquet.builders.push_back(buf_parquet.b_eta.get());

    buf_parquet.b_phi = std::make_unique<arrow::FloatBuilder>();
    fields.push_back(arrow::field(defaultPrefix + "phi", arrow::float32()));
    buf_parquet.builders.push_back(buf_parquet.b_phi.get());

    buf_parquet.b_e = std::make_unique<arrow::FloatBuilder>();
    fields.push_back(arrow::field(defaultPrefix + "e", arrow::float32()));
    buf_parquet.builders.push_back(buf_parquet.b_e.get());

    buf_parquet.b_et = std::make_unique<arrow::FloatBuilder>();
    fields.push_back(arrow::field(defaultPrefix + "et", arrow::float32()));
    buf_parquet.builders.push_back(buf_parquet.b_et.get());
  } else {
    for (const auto &spec : specs) {
      if (spec.fieldName == "eta") {
        buf_parquet.b_eta = std::make_unique<arrow::FloatBuilder>();
        fields.push_back(arrow::field(spec.branchName, arrow::float32()));
        buf_parquet.builders.push_back(buf_parquet.b_eta.get());
      } else if (spec.fieldName == "phi") {
        buf_parquet.b_phi = std::make_unique<arrow::FloatBuilder>();
        fields.push_back(arrow::field(spec.branchName, arrow::float32()));
        buf_parquet.builders.push_back(buf_parquet.b_phi.get());
      } else if (spec.fieldName == "e") {
        buf_parquet.b_e = std::make_unique<arrow::FloatBuilder>();
        fields.push_back(arrow::field(spec.branchName, arrow::float32()));
        buf_parquet.builders.push_back(buf_parquet.b_e.get());
      } else if (spec.fieldName == "et") {
        buf_parquet.b_et = std::make_unique<arrow::FloatBuilder>();
        fields.push_back(arrow::field(spec.branchName, arrow::float32()));
        buf_parquet.builders.push_back(buf_parquet.b_et.get());
      } else if (spec.fieldName == "id") {
        buf_parquet.b_id = std::make_unique<arrow::Int32Builder>();
        fields.push_back(arrow::field(spec.branchName, arrow::int32()));
        buf_parquet.builders.push_back(buf_parquet.b_id.get());
      }
    }
  }
}

void SeedConverter::to_parquet(const Seed_t &buf, Seed_parquet &buf_parquet) const {
  if (buf_parquet.b_eta != nullptr) PARQUET_THROW_NOT_OK(buf_parquet.b_eta->Append(buf.eta));
  if (buf_parquet.b_phi != nullptr) PARQUET_THROW_NOT_OK(buf_parquet.b_phi->Append(buf.phi));
  if (buf_parquet.b_e != nullptr)   PARQUET_THROW_NOT_OK(buf_parquet.b_e->Append(buf.e));
  if (buf_parquet.b_et != nullptr)  PARQUET_THROW_NOT_OK(buf_parquet.b_et->Append(buf.et));
  if (buf_parquet.b_id != nullptr)  PARQUET_THROW_NOT_OK(buf_parquet.b_id->Append(buf.id));
}

void SeedConverter::to_parquet(const Seed *seed, Seed_parquet &buf_parquet) const {
  Seed_t buf;
  if (!seed) {
    buf.id = -1; buf.e = 0; buf.et = 0; buf.eta = 0; buf.phi = 0;
  } else {
    convert(seed, buf);
  }
  to_parquet(buf, buf_parquet);
}
