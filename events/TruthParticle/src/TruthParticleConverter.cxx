#include "TruthParticle/TruthParticleContainer.h"
#include "TruthParticle/TruthParticleConverter.h"
#include "TTree.h"
#include <parquet/arrow/writer.h>

using namespace xAOD;

bool TruthParticleConverter::convert(const TruthParticle *truth, TruthParticle_t &truth_t) const {
  if (truth) {
    truth_t.pdgid         = truth->pdgid();
    truth_t.seed_key_hash = truth->seedLink().keyHash();
    truth_t.seed_index    = truth->seedLink().index();
    truth_t.seedid        = truth->seedid();
    truth_t.e             = truth->e();
    truth_t.et            = truth->et();
    truth_t.eta           = truth->eta();
    truth_t.phi           = truth->phi();
    truth_t.px            = truth->px();
    truth_t.py            = truth->py();
    truth_t.pz            = truth->pz();
    truth_t.vx            = truth->vx();
    truth_t.vy            = truth->vy();
    truth_t.vz            = truth->vz();

    return true;
  }
  return false;
}

bool TruthParticleConverter::convert(const TruthParticle_t &truth_t, TruthParticle *&truth) const {
  truth = new xAOD::TruthParticle(truth_t.pdgid,
                                  truth_t.seedid,
                                  truth_t.e,
                                  truth_t.et,
                                  truth_t.eta,
                                  truth_t.phi,
                                  truth_t.px,
                                  truth_t.py,
                                  truth_t.pz,
                                  truth_t.vx,
                                  truth_t.vy,
                                  truth_t.vz);

  if (truth_t.seed_key_hash != 0) {
    truth->setSeed(truth_t.seed_key_hash, truth_t.seed_index);
  }

  return true;
}

void TruthParticleConverter::book_ntuple(TTree *tree, TruthParticleNtupleBuffers &buf,
                                         const std::vector<Gaugi::BranchSpec> &specs,
                                         const std::string &defaultPrefix) const {
  if (!tree) return;
  buf.init();
  if (specs.empty()) {
    Gaugi::bindOrBranch(tree, defaultPrefix + "pdgid", &buf.pdgid);
    Gaugi::bindOrBranch(tree, defaultPrefix + "eta",   &buf.eta);
    Gaugi::bindOrBranch(tree, defaultPrefix + "phi",   &buf.phi);
    Gaugi::bindOrBranch(tree, defaultPrefix + "e",     &buf.e);
    Gaugi::bindOrBranch(tree, defaultPrefix + "et",    &buf.et);
  } else {
    for (const auto &spec : specs) {
      if      (spec.fieldName == "pdgid") Gaugi::bindOrBranch(tree, spec.branchName, &buf.pdgid);
      else if (spec.fieldName == "eta")   Gaugi::bindOrBranch(tree, spec.branchName, &buf.eta);
      else if (spec.fieldName == "phi")   Gaugi::bindOrBranch(tree, spec.branchName, &buf.phi);
      else if (spec.fieldName == "e")     Gaugi::bindOrBranch(tree, spec.branchName, &buf.e);
      else if (spec.fieldName == "et")    Gaugi::bindOrBranch(tree, spec.branchName, &buf.et);
    }
  }
}

void TruthParticleConverter::to_ntuple(const TruthParticleContainer *container, int seedid,
                                       TruthParticleNtupleBuffers &buf) const {
  buf.clear();
  if (!container || seedid < 0) return;
  for (const auto part : *container) {
    if (part->seedid() == seedid) {
      if (buf.pdgid) buf.pdgid->push_back(part->pdgid());
      if (buf.eta)   buf.eta->push_back(part->eta());
      if (buf.phi)   buf.phi->push_back(part->phi());
      if (buf.e)     buf.e->push_back(part->e());
      if (buf.et)    buf.et->push_back(part->et());
    }
  }
}

static void initListCol(std::shared_ptr<arrow::FloatBuilder> &val_b,
                        std::unique_ptr<arrow::ListBuilder> &list_b,
                        std::vector<std::shared_ptr<arrow::Field>> &fields,
                        std::vector<arrow::ArrayBuilder*> &builders,
                        const std::string &name) {
  val_b = std::make_shared<arrow::FloatBuilder>();
  list_b = std::make_unique<arrow::ListBuilder>(arrow::default_memory_pool(), val_b);
  fields.push_back(arrow::field(name, arrow::list(arrow::float32())));
  builders.push_back(list_b.get());
}

void TruthParticleConverter::book_parquet(std::vector<std::shared_ptr<arrow::Field>> &fields,
                                          TruthParticle_parquet &buf_parquet,
                                          const std::vector<Gaugi::BranchSpec> &specs,
                                          const std::string &defaultPrefix) const {
  buf_parquet.builders.clear();
  if (specs.empty()) {
    initListCol(buf_parquet.val_pdgid, buf_parquet.list_pdgid, fields, buf_parquet.builders, defaultPrefix + "pdgid");
    initListCol(buf_parquet.val_eta,   buf_parquet.list_eta,   fields, buf_parquet.builders, defaultPrefix + "eta");
    initListCol(buf_parquet.val_phi,   buf_parquet.list_phi,   fields, buf_parquet.builders, defaultPrefix + "phi");
    initListCol(buf_parquet.val_e,     buf_parquet.list_e,     fields, buf_parquet.builders, defaultPrefix + "e");
    initListCol(buf_parquet.val_et,    buf_parquet.list_et,    fields, buf_parquet.builders, defaultPrefix + "et");
  } else {
    for (const auto &spec : specs) {
      if      (spec.fieldName == "pdgid") initListCol(buf_parquet.val_pdgid, buf_parquet.list_pdgid, fields, buf_parquet.builders, spec.branchName);
      else if (spec.fieldName == "eta")   initListCol(buf_parquet.val_eta,   buf_parquet.list_eta,   fields, buf_parquet.builders, spec.branchName);
      else if (spec.fieldName == "phi")   initListCol(buf_parquet.val_phi,   buf_parquet.list_phi,   fields, buf_parquet.builders, spec.branchName);
      else if (spec.fieldName == "e")     initListCol(buf_parquet.val_e,     buf_parquet.list_e,     fields, buf_parquet.builders, spec.branchName);
      else if (spec.fieldName == "et")    initListCol(buf_parquet.val_et,    buf_parquet.list_et,    fields, buf_parquet.builders, spec.branchName);
    }
  }
}

void TruthParticleConverter::to_parquet(const TruthParticleContainer *container, int seedid,
                                        TruthParticle_parquet &buf_parquet) const {
  std::vector<float> v_pdgid, v_eta, v_phi, v_e, v_et;
  if (container != nullptr && seedid >= 0) {
    for (const auto part : *container) {
      if (part != nullptr && part->seedid() == seedid) {
        v_pdgid.push_back(part->pdgid());
        v_eta.push_back(part->eta());
        v_phi.push_back(part->phi());
        v_e.push_back(part->e());
        v_et.push_back(part->et());
      }
    }
  }

  auto appendList = [](auto &list_b, auto &val_b, const std::vector<float> &vals) {
    if (list_b != nullptr && val_b != nullptr) {
      PARQUET_THROW_NOT_OK(list_b->Append());
      for (float val : vals) {
        PARQUET_THROW_NOT_OK(val_b->Append(val));
      }
    }
  };

  appendList(buf_parquet.list_pdgid, buf_parquet.val_pdgid, v_pdgid);
  appendList(buf_parquet.list_eta,   buf_parquet.val_eta,   v_eta);
  appendList(buf_parquet.list_phi,   buf_parquet.val_phi,   v_phi);
  appendList(buf_parquet.list_e,     buf_parquet.val_e,     v_e);
  appendList(buf_parquet.list_et,    buf_parquet.val_et,    v_et);
}
