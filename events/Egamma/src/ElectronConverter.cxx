#include "Egamma/ElectronConverter.h"
#include "TTree.h"
#include <parquet/arrow/writer.h>

using namespace xAOD;

bool ElectronConverter::convert(const Electron *electron, Electron_t &electron_t) const {
  if (electron) {
    electron_t.eta = electron->eta();
    electron_t.phi = electron->phi();
    electron_t.et  = electron->et();
    electron_t.e   = electron->e();
    
    electron_t.isEM.clear();
    electron_t.isEM.push_back(electron->isTight());
    electron_t.isEM.push_back(electron->isMedium());
    electron_t.isEM.push_back(electron->isLoose());
    electron_t.isEM.push_back(electron->isVeryLoose());

    electron_t.cluster_key_hash = electron->caloClusterLink().keyHash();
    electron_t.cluster_index    = electron->caloClusterLink().index();

    return true;
  }
  return false;
}

bool ElectronConverter::convert(const Electron_t &electron_t, Electron *&electron) const {
  electron = new xAOD::Electron();
  electron->setEta(electron_t.eta);
  electron->setPhi(electron_t.phi);
  electron->setEt(electron_t.et);
  electron->setE(electron_t.e);

  if (electron_t.isEM.size() >= 4) {
    electron->setIsTight(electron_t.isEM[0]);
    electron->setIsMedium(electron_t.isEM[1]);  
    electron->setIsLoose(electron_t.isEM[2]);
    electron->setIsVeryLoose(electron_t.isEM[3]);
  }

  electron->setCaloCluster(electron_t.cluster_key_hash, electron_t.cluster_index);
  return true;
}

void ElectronConverter::book_ntuple(TTree *tree, Electron_t &buf, ElectronNtupleScalars &scalars,
                                    const std::vector<Gaugi::BranchSpec> &specs,
                                    const std::string &defaultPrefix) const {
  if (!tree) return;
  if (specs.empty()) {
    Gaugi::bindOrBranch(tree, defaultPrefix + "eta",     &buf.eta);
    Gaugi::bindOrBranch(tree, defaultPrefix + "et",      &buf.et);
    Gaugi::bindOrBranch(tree, defaultPrefix + "phi",     &buf.phi);
    Gaugi::bindOrBranch(tree, defaultPrefix + "tight",   &scalars.tight);
    Gaugi::bindOrBranch(tree, defaultPrefix + "medium",  &scalars.medium);
    Gaugi::bindOrBranch(tree, defaultPrefix + "loose",   &scalars.loose);
    Gaugi::bindOrBranch(tree, defaultPrefix + "vloose",  &scalars.vloose);
  } else {
    for (const auto &spec : specs) {
      if      (spec.fieldName == "eta")                                        Gaugi::bindOrBranch(tree, spec.branchName, &buf.eta);
      else if (spec.fieldName == "et")                                         Gaugi::bindOrBranch(tree, spec.branchName, &buf.et);
      else if (spec.fieldName == "e")                                          Gaugi::bindOrBranch(tree, spec.branchName, &buf.e);
      else if (spec.fieldName == "phi")                                        Gaugi::bindOrBranch(tree, spec.branchName, &buf.phi);
      else if (spec.fieldName == "tight"  || spec.fieldName == "isTight")     Gaugi::bindOrBranch(tree, spec.branchName, &scalars.tight);
      else if (spec.fieldName == "medium" || spec.fieldName == "isMedium")    Gaugi::bindOrBranch(tree, spec.branchName, &scalars.medium);
      else if (spec.fieldName == "loose"  || spec.fieldName == "isLoose")     Gaugi::bindOrBranch(tree, spec.branchName, &scalars.loose);
      else if (spec.fieldName == "vloose" || spec.fieldName == "isVeryLoose") Gaugi::bindOrBranch(tree, spec.branchName, &scalars.vloose);
    }
  }
}

void ElectronConverter::to_ntuple(const Electron *el, Electron_t &buf, ElectronNtupleScalars &scalars) const {
  if (!el) {
    buf.e = 0; buf.et = -1; buf.eta = -1; buf.phi = -1;
    buf.isEM.clear();
    scalars.tight = scalars.medium = scalars.loose = scalars.vloose = false;
    return;
  }
  convert(el, buf);
  if (buf.isEM.size() >= 4) {
    scalars.tight  = buf.isEM[0];
    scalars.medium = buf.isEM[1];
    scalars.loose  = buf.isEM[2];
    scalars.vloose = buf.isEM[3];
  } else {
    scalars.tight = scalars.medium = scalars.loose = scalars.vloose = false;
  }
}

void ElectronConverter::book_parquet(std::vector<std::shared_ptr<arrow::Field>> &fields,
                                     Electron_parquet &buf_parquet,
                                     const std::vector<Gaugi::BranchSpec> &specs,
                                     const std::string &defaultPrefix) const {
  buf_parquet.builders.clear();
  if (specs.empty()) {
    buf_parquet.b_eta = std::make_unique<arrow::FloatBuilder>();
    fields.push_back(arrow::field(defaultPrefix + "eta", arrow::float32()));
    buf_parquet.builders.push_back(buf_parquet.b_eta.get());

    buf_parquet.b_et = std::make_unique<arrow::FloatBuilder>();
    fields.push_back(arrow::field(defaultPrefix + "et", arrow::float32()));
    buf_parquet.builders.push_back(buf_parquet.b_et.get());

    buf_parquet.b_phi = std::make_unique<arrow::FloatBuilder>();
    fields.push_back(arrow::field(defaultPrefix + "phi", arrow::float32()));
    buf_parquet.builders.push_back(buf_parquet.b_phi.get());

    buf_parquet.b_tight = std::make_unique<arrow::BooleanBuilder>();
    fields.push_back(arrow::field(defaultPrefix + "tight", arrow::boolean()));
    buf_parquet.builders.push_back(buf_parquet.b_tight.get());

    buf_parquet.b_medium = std::make_unique<arrow::BooleanBuilder>();
    fields.push_back(arrow::field(defaultPrefix + "medium", arrow::boolean()));
    buf_parquet.builders.push_back(buf_parquet.b_medium.get());

    buf_parquet.b_loose = std::make_unique<arrow::BooleanBuilder>();
    fields.push_back(arrow::field(defaultPrefix + "loose", arrow::boolean()));
    buf_parquet.builders.push_back(buf_parquet.b_loose.get());

    buf_parquet.b_vloose = std::make_unique<arrow::BooleanBuilder>();
    fields.push_back(arrow::field(defaultPrefix + "vloose", arrow::boolean()));
    buf_parquet.builders.push_back(buf_parquet.b_vloose.get());
  } else {
    for (const auto &spec : specs) {
      if (spec.fieldName == "eta") {
        buf_parquet.b_eta = std::make_unique<arrow::FloatBuilder>();
        fields.push_back(arrow::field(spec.branchName, arrow::float32()));
        buf_parquet.builders.push_back(buf_parquet.b_eta.get());
      } else if (spec.fieldName == "et") {
        buf_parquet.b_et = std::make_unique<arrow::FloatBuilder>();
        fields.push_back(arrow::field(spec.branchName, arrow::float32()));
        buf_parquet.builders.push_back(buf_parquet.b_et.get());
      } else if (spec.fieldName == "e") {
        buf_parquet.b_e = std::make_unique<arrow::FloatBuilder>();
        fields.push_back(arrow::field(spec.branchName, arrow::float32()));
        buf_parquet.builders.push_back(buf_parquet.b_e.get());
      } else if (spec.fieldName == "phi") {
        buf_parquet.b_phi = std::make_unique<arrow::FloatBuilder>();
        fields.push_back(arrow::field(spec.branchName, arrow::float32()));
        buf_parquet.builders.push_back(buf_parquet.b_phi.get());
      } else if (spec.fieldName == "tight" || spec.fieldName == "isTight") {
        buf_parquet.b_tight = std::make_unique<arrow::BooleanBuilder>();
        fields.push_back(arrow::field(spec.branchName, arrow::boolean()));
        buf_parquet.builders.push_back(buf_parquet.b_tight.get());
      } else if (spec.fieldName == "medium" || spec.fieldName == "isMedium") {
        buf_parquet.b_medium = std::make_unique<arrow::BooleanBuilder>();
        fields.push_back(arrow::field(spec.branchName, arrow::boolean()));
        buf_parquet.builders.push_back(buf_parquet.b_medium.get());
      } else if (spec.fieldName == "loose" || spec.fieldName == "isLoose") {
        buf_parquet.b_loose = std::make_unique<arrow::BooleanBuilder>();
        fields.push_back(arrow::field(spec.branchName, arrow::boolean()));
        buf_parquet.builders.push_back(buf_parquet.b_loose.get());
      } else if (spec.fieldName == "vloose" || spec.fieldName == "isVeryLoose") {
        buf_parquet.b_vloose = std::make_unique<arrow::BooleanBuilder>();
        fields.push_back(arrow::field(spec.branchName, arrow::boolean()));
        buf_parquet.builders.push_back(buf_parquet.b_vloose.get());
      }
    }
  }
}

void ElectronConverter::to_parquet(const Electron_t &buf, const ElectronNtupleScalars &scalars, Electron_parquet &buf_parquet) const {
  if (buf_parquet.b_eta != nullptr)    PARQUET_THROW_NOT_OK(buf_parquet.b_eta->Append(buf.eta));
  if (buf_parquet.b_et != nullptr)     PARQUET_THROW_NOT_OK(buf_parquet.b_et->Append(buf.et));
  if (buf_parquet.b_e != nullptr)      PARQUET_THROW_NOT_OK(buf_parquet.b_e->Append(buf.e));
  if (buf_parquet.b_phi != nullptr)    PARQUET_THROW_NOT_OK(buf_parquet.b_phi->Append(buf.phi));
  if (buf_parquet.b_tight != nullptr)  PARQUET_THROW_NOT_OK(buf_parquet.b_tight->Append(scalars.tight));
  if (buf_parquet.b_medium != nullptr) PARQUET_THROW_NOT_OK(buf_parquet.b_medium->Append(scalars.medium));
  if (buf_parquet.b_loose != nullptr)  PARQUET_THROW_NOT_OK(buf_parquet.b_loose->Append(scalars.loose));
  if (buf_parquet.b_vloose != nullptr) PARQUET_THROW_NOT_OK(buf_parquet.b_vloose->Append(scalars.vloose));
}

void ElectronConverter::to_parquet(const Electron *el, Electron_parquet &buf_parquet) const {
  Electron_t buf;
  ElectronNtupleScalars scalars;
  to_ntuple(el, buf, scalars);
  to_parquet(buf, scalars, buf_parquet);
}