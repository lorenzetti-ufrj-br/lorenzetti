#include "CaloRings/CaloRingsConverter.h"
#include "TTree.h"
#include <parquet/arrow/writer.h>

using namespace xAOD;

bool CaloRingsConverter::convert(const CaloRings *rings, CaloRings_t &rings_t) const {
  if (rings) {
    rings_t.cluster_key_hash = rings->caloClusterLink().keyHash();
    rings_t.cluster_index    = rings->caloClusterLink().index();
    rings_t.rings            = rings->rings();
    return true;
  }
  return false;
}

bool CaloRingsConverter::convert(const CaloRings_t &rings_t, CaloRings *&rings) const {
  rings = new xAOD::CaloRings();
  rings->setRings(rings_t.rings);
  rings->setCaloCluster(rings_t.cluster_key_hash, rings_t.cluster_index);
  return true;
}

void CaloRingsConverter::book_ntuple(TTree *tree, CaloRings_t &buf,
                                     std::vector<float> *&ringsPtr,
                                     std::map<std::string, float> &scalarRings,
                                     const std::vector<Gaugi::BranchSpec> &specs,
                                     const std::string &defaultName) const {
  if (!tree) return;
  if (specs.empty()) {
    ringsPtr = &buf.rings;
    Gaugi::bindOrBranch(tree, defaultName, &ringsPtr);
  } else {
    for (const auto &spec : specs) {
      if (spec.fieldName == "rings" && spec.index < 0) {
        ringsPtr = &buf.rings;
        Gaugi::bindOrBranch(tree, spec.branchName, &ringsPtr);
      } else if (spec.fieldName == "rings" && spec.index >= 0) {
        scalarRings[spec.branchName] = 0.0f;
        Gaugi::bindOrBranch(tree, spec.branchName, &scalarRings[spec.branchName]);
      }
    }
  }
}

void CaloRingsConverter::to_ntuple(const CaloRings *rings, CaloRings_t &buf,
                                   std::map<std::string, float> &scalarRings,
                                   const std::vector<Gaugi::BranchSpec> &specs) const {
  buf.rings.clear();
  if (rings) {
    convert(rings, buf);
  }
  for (const auto &spec : specs) {
    if (spec.fieldName == "rings" && spec.index >= 0) {
      scalarRings[spec.branchName] = (spec.index < (int)buf.rings.size()) ? buf.rings[spec.index] : 0.0f;
    }
  }
}

void CaloRingsConverter::book_parquet(std::vector<std::shared_ptr<arrow::Field>> &fields,
                                      CaloRings_parquet &buf_parquet,
                                      const std::vector<Gaugi::BranchSpec> &specs,
                                      const std::string &defaultName) const {
  buf_parquet.builders.clear();
  buf_parquet.scalar_builders.clear();
  if (specs.empty()) {
    buf_parquet.val_builder = std::make_shared<arrow::FloatBuilder>();
    buf_parquet.list_builder = std::make_unique<arrow::ListBuilder>(arrow::default_memory_pool(), buf_parquet.val_builder);
    fields.push_back(arrow::field(defaultName, arrow::list(arrow::float32())));
    buf_parquet.builders.push_back(buf_parquet.list_builder.get());
  } else {
    for (const auto &spec : specs) {
      if (spec.fieldName == "rings" && spec.index < 0) {
        buf_parquet.val_builder = std::make_shared<arrow::FloatBuilder>();
        buf_parquet.list_builder = std::make_unique<arrow::ListBuilder>(arrow::default_memory_pool(), buf_parquet.val_builder);
        fields.push_back(arrow::field(spec.branchName, arrow::list(arrow::float32())));
        buf_parquet.builders.push_back(buf_parquet.list_builder.get());
      } else if (spec.fieldName == "rings" && spec.index >= 0) {
        auto b = std::make_unique<arrow::FloatBuilder>();
        fields.push_back(arrow::field(spec.branchName, arrow::float32()));
        buf_parquet.builders.push_back(b.get());
        buf_parquet.scalar_builders.push_back({spec.index, std::move(b)});
      }
    }
  }
}

void CaloRingsConverter::to_parquet(const CaloRings_t &buf, CaloRings_parquet &buf_parquet) const {
  if (buf_parquet.list_builder != nullptr) {
    PARQUET_THROW_NOT_OK(buf_parquet.list_builder->Append());
    for (float v : buf.rings) {
      PARQUET_THROW_NOT_OK(buf_parquet.val_builder->Append(v));
    }
  }
  for (const auto &sc : buf_parquet.scalar_builders) {
    float val = (sc.index >= 0 && sc.index < (int)buf.rings.size()) ? buf.rings[sc.index] : 0.0f;
    PARQUET_THROW_NOT_OK(sc.builder->Append(val));
  }
}

void CaloRingsConverter::to_parquet(const CaloRings *rings, CaloRings_parquet &buf_parquet) const {
  CaloRings_t buf;
  if (rings) {
    convert(rings, buf);
  }
  to_parquet(buf, buf_parquet);
}