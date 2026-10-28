#include "CaloCluster/CaloClusterConverter.h"
#include "TTree.h"
#include <parquet/arrow/writer.h>
#include <iostream>

using namespace xAOD;

bool CaloClusterConverter::convert(const CaloCluster *clus, CaloCluster_t &clus_t) const {
  if (clus) {
    clus_t.e               = clus->e();
    clus_t.et              = clus->et();
    clus_t.eta             = clus->eta();
    clus_t.phi             = clus->phi();
    clus_t.deta            = clus->deltaEta();
    clus_t.dphi            = clus->deltaPhi();
    clus_t.e0              = clus->e0();
    clus_t.e1              = clus->e1();
    clus_t.e2              = clus->e2();
    clus_t.e3              = clus->e3();
    clus_t.ehad1           = clus->ehad1();
    clus_t.ehad2           = clus->ehad2();
    clus_t.ehad3           = clus->ehad3();
    clus_t.etot            = clus->etot();
    clus_t.e233            = clus->e233();
    clus_t.e237            = clus->e237();
    clus_t.e277            = clus->e277();
    clus_t.emaxs1          = clus->emaxs1();
    clus_t.emaxs2          = clus->emaxs2();
    clus_t.e2tsts1         = clus->e2tsts1();
    clus_t.reta            = clus->reta();
    clus_t.rphi            = clus->rphi();
    clus_t.rhad            = clus->rhad();
    clus_t.rhad1           = clus->rhad1();
    clus_t.eratio          = clus->eratio();
    clus_t.f0              = clus->f0();
    clus_t.f1              = clus->f1();
    clus_t.f2              = clus->f2();
    clus_t.f3              = clus->f3();
    clus_t.weta2           = clus->weta2();
    clus_t.secondR         = clus->secondR();
    clus_t.lambdaCenter    = clus->lambdaCenter();
    clus_t.secondLambda    = clus->secondLambda();
    clus_t.fracMax         = clus->fracMax();
    clus_t.lateralMom      = clus->lateralMom();
    clus_t.longitudinalMom = clus->longitudinalMom();

    clus_t.seed_key_hash   = clus->seedLink().keyHash();
    clus_t.seed_index      = clus->seedLink().index();

    clus_t.cells_key_hash  = clus->cellsKeyHash();
    clus_t.cell_indices    = clus->cellIndices();

    clus_t.cell_links.clear();
    for (auto &cell : clus->cells()) {
      if (cell && cell->descriptor()) {
        clus_t.cell_links.push_back(cell->descriptor()->hash());
      }
    }
    return true;
  }
  return false;
}

bool CaloClusterConverter::convert(const CaloCluster_t &cluster_t, CaloCluster *&cluster) const {
  cluster = new xAOD::CaloCluster(cluster_t.emaxs2,
                                  cluster_t.eta, 
                                  cluster_t.phi, 
                                  cluster_t.deta, 
                                  cluster_t.dphi);
  cluster->setE(cluster_t.e);
  cluster->setEt(cluster_t.et);
  cluster->setE0(cluster_t.e0);
  cluster->setE1(cluster_t.e1);
  cluster->setE2(cluster_t.e2);
  cluster->setE3(cluster_t.e3);
  cluster->setEhad1(cluster_t.ehad1);
  cluster->setEhad2(cluster_t.ehad2);
  cluster->setEhad3(cluster_t.ehad3);
  cluster->setEtot(cluster_t.etot);
  cluster->setE277(cluster_t.e277);
  cluster->setE237(cluster_t.e237);
  cluster->setE233(cluster_t.e233);
  cluster->setReta(cluster_t.reta);
  cluster->setRphi(cluster_t.rphi);
  cluster->setWeta2(cluster_t.weta2);
  cluster->setEratio(cluster_t.eratio);
  cluster->setEmaxs1(cluster_t.emaxs1);
  cluster->setE2tsts1(cluster_t.e2tsts1);
  cluster->setF0(cluster_t.f0);
  cluster->setF1(cluster_t.f1);
  cluster->setF2(cluster_t.f2);
  cluster->setF3(cluster_t.f3);
  cluster->setRhad(cluster_t.rhad);
  cluster->setRhad1(cluster_t.rhad1);
  cluster->setSecondR(cluster_t.secondR);
  cluster->setLambdaCenter(cluster_t.lambdaCenter);
  cluster->setSecondLambda(cluster_t.secondLambda);
  cluster->setFracMax(cluster_t.fracMax);
  cluster->setLateralMom(cluster_t.lateralMom);
  cluster->setLongitudinalMom(cluster_t.longitudinalMom);    

  cluster->setSeed(cluster_t.seed_key_hash, cluster_t.seed_index);
  cluster->setCellsContainerKey(cluster_t.cells_key_hash);
  cluster->setCellIndices(cluster_t.cell_indices);

  return true;
}

static const std::vector<std::string> s_defaultClusterVars = {
  "eta", "phi", "e", "et", "deta", "dphi",
  "e0", "e1", "e2", "e3", "ehad1", "ehad2", "ehad3", "etot",
  "e233", "e237", "e277", "emaxs1", "emaxs2", "e2tsts1",
  "reta", "rphi", "rhad", "rhad1", "eratio",
  "f0", "f1", "f2", "f3", "weta2",
  "secondR", "lambdaCenter", "secondLambda", "fracMax", "lateralMom", "longitudinalMom"
};

void CaloClusterConverter::book_ntuple(TTree *tree, CaloCluster_t &buf,
                                       const std::vector<Gaugi::BranchSpec> &specs,
                                       const std::string &defaultPrefix) const {
  if (!tree) return;
  std::vector<Gaugi::BranchSpec> activeSpecs = specs;
  if (activeSpecs.empty()) {
    for (const auto &v : s_defaultClusterVars) {
      activeSpecs.push_back({defaultPrefix + v, v, -1});
    }
  }

  for (const auto &spec : activeSpecs) {
    if      (spec.fieldName == "eta")             Gaugi::bindOrBranch(tree, spec.branchName, &buf.eta);
    else if (spec.fieldName == "phi")             Gaugi::bindOrBranch(tree, spec.branchName, &buf.phi);
    else if (spec.fieldName == "e")               Gaugi::bindOrBranch(tree, spec.branchName, &buf.e);
    else if (spec.fieldName == "et")              Gaugi::bindOrBranch(tree, spec.branchName, &buf.et);
    else if (spec.fieldName == "deta")            Gaugi::bindOrBranch(tree, spec.branchName, &buf.deta);
    else if (spec.fieldName == "dphi")            Gaugi::bindOrBranch(tree, spec.branchName, &buf.dphi);
    else if (spec.fieldName == "e0")              Gaugi::bindOrBranch(tree, spec.branchName, &buf.e0);
    else if (spec.fieldName == "e1")              Gaugi::bindOrBranch(tree, spec.branchName, &buf.e1);
    else if (spec.fieldName == "e2")              Gaugi::bindOrBranch(tree, spec.branchName, &buf.e2);
    else if (spec.fieldName == "e3")              Gaugi::bindOrBranch(tree, spec.branchName, &buf.e3);
    else if (spec.fieldName == "ehad1")           Gaugi::bindOrBranch(tree, spec.branchName, &buf.ehad1);
    else if (spec.fieldName == "ehad2")           Gaugi::bindOrBranch(tree, spec.branchName, &buf.ehad2);
    else if (spec.fieldName == "ehad3")           Gaugi::bindOrBranch(tree, spec.branchName, &buf.ehad3);
    else if (spec.fieldName == "etot")            Gaugi::bindOrBranch(tree, spec.branchName, &buf.etot);
    else if (spec.fieldName == "e233")            Gaugi::bindOrBranch(tree, spec.branchName, &buf.e233);
    else if (spec.fieldName == "e237")            Gaugi::bindOrBranch(tree, spec.branchName, &buf.e237);
    else if (spec.fieldName == "e277")            Gaugi::bindOrBranch(tree, spec.branchName, &buf.e277);
    else if (spec.fieldName == "emaxs1")          Gaugi::bindOrBranch(tree, spec.branchName, &buf.emaxs1);
    else if (spec.fieldName == "emaxs2")          Gaugi::bindOrBranch(tree, spec.branchName, &buf.emaxs2);
    else if (spec.fieldName == "e2tsts1")         Gaugi::bindOrBranch(tree, spec.branchName, &buf.e2tsts1);
    else if (spec.fieldName == "reta")            Gaugi::bindOrBranch(tree, spec.branchName, &buf.reta);
    else if (spec.fieldName == "rphi")            Gaugi::bindOrBranch(tree, spec.branchName, &buf.rphi);
    else if (spec.fieldName == "rhad")            Gaugi::bindOrBranch(tree, spec.branchName, &buf.rhad);
    else if (spec.fieldName == "rhad1")           Gaugi::bindOrBranch(tree, spec.branchName, &buf.rhad1);
    else if (spec.fieldName == "eratio")          Gaugi::bindOrBranch(tree, spec.branchName, &buf.eratio);
    else if (spec.fieldName == "f0")              Gaugi::bindOrBranch(tree, spec.branchName, &buf.f0);
    else if (spec.fieldName == "f1")              Gaugi::bindOrBranch(tree, spec.branchName, &buf.f1);
    else if (spec.fieldName == "f2")              Gaugi::bindOrBranch(tree, spec.branchName, &buf.f2);
    else if (spec.fieldName == "f3")              Gaugi::bindOrBranch(tree, spec.branchName, &buf.f3);
    else if (spec.fieldName == "weta2")           Gaugi::bindOrBranch(tree, spec.branchName, &buf.weta2);
    else if (spec.fieldName == "secondR")         Gaugi::bindOrBranch(tree, spec.branchName, &buf.secondR);
    else if (spec.fieldName == "lambdaCenter")    Gaugi::bindOrBranch(tree, spec.branchName, &buf.lambdaCenter);
    else if (spec.fieldName == "secondLambda")    Gaugi::bindOrBranch(tree, spec.branchName, &buf.secondLambda);
    else if (spec.fieldName == "fracMax")         Gaugi::bindOrBranch(tree, spec.branchName, &buf.fracMax);
    else if (spec.fieldName == "lateralMom")      Gaugi::bindOrBranch(tree, spec.branchName, &buf.lateralMom);
    else if (spec.fieldName == "longitudinalMom") Gaugi::bindOrBranch(tree, spec.branchName, &buf.longitudinalMom);
  }
}

void CaloClusterConverter::to_ntuple(const CaloCluster *clus, CaloCluster_t &buf) const {
  if (!clus) {
    buf.e = 0; buf.et = 0; buf.eta = 0; buf.phi = 0;
    buf.deta = 0; buf.dphi = 0;
    buf.e0 = 0; buf.e1 = 0; buf.e2 = 0; buf.e3 = 0;
    buf.ehad1 = 0; buf.ehad2 = 0; buf.ehad3 = 0; buf.etot = 0;
    buf.e233 = 0; buf.e237 = 0; buf.e277 = 0; buf.emaxs1 = 0; buf.emaxs2 = 0; buf.e2tsts1 = 0;
    buf.reta = 0; buf.rphi = 0; buf.rhad = 0; buf.rhad1 = 0; buf.eratio = 0;
    buf.f0 = 0; buf.f1 = 0; buf.f2 = 0; buf.f3 = 0; buf.weta2 = 0;
    buf.secondR = 0; buf.lambdaCenter = 0; buf.secondLambda = 0; buf.fracMax = 0;
    buf.lateralMom = 0; buf.longitudinalMom = 0;
    return;
  }
  convert(clus, buf);
}

void CaloClusterConverter::book_parquet(std::vector<std::shared_ptr<arrow::Field>> &fields,
                                        CaloCluster_parquet &buf_parquet,
                                        const std::vector<Gaugi::BranchSpec> &specs,
                                        const std::string &defaultPrefix) const {
  buf_parquet.builders.clear();
  std::vector<Gaugi::BranchSpec> activeSpecs = specs;
  if (activeSpecs.empty()) {
    for (const auto &v : s_defaultClusterVars) {
      activeSpecs.push_back({defaultPrefix + v, v, -1});
    }
  }

  for (const auto &spec : activeSpecs) {
    auto addFloat = [&](std::unique_ptr<arrow::FloatBuilder> &b) {
      b = std::make_unique<arrow::FloatBuilder>();
      fields.push_back(arrow::field(spec.branchName, arrow::float32()));
      buf_parquet.builders.push_back(b.get());
    };

    if      (spec.fieldName == "eta")             addFloat(buf_parquet.b_eta);
    else if (spec.fieldName == "phi")             addFloat(buf_parquet.b_phi);
    else if (spec.fieldName == "e")               addFloat(buf_parquet.b_e);
    else if (spec.fieldName == "et")              addFloat(buf_parquet.b_et);
    else if (spec.fieldName == "deta")            addFloat(buf_parquet.b_deta);
    else if (spec.fieldName == "dphi")            addFloat(buf_parquet.b_dphi);
    else if (spec.fieldName == "e0")              addFloat(buf_parquet.b_e0);
    else if (spec.fieldName == "e1")              addFloat(buf_parquet.b_e1);
    else if (spec.fieldName == "e2")              addFloat(buf_parquet.b_e2);
    else if (spec.fieldName == "e3")              addFloat(buf_parquet.b_e3);
    else if (spec.fieldName == "ehad1")           addFloat(buf_parquet.b_ehad1);
    else if (spec.fieldName == "ehad2")           addFloat(buf_parquet.b_ehad2);
    else if (spec.fieldName == "ehad3")           addFloat(buf_parquet.b_ehad3);
    else if (spec.fieldName == "etot")            addFloat(buf_parquet.b_etot);
    else if (spec.fieldName == "e233")            addFloat(buf_parquet.b_e233);
    else if (spec.fieldName == "e237")            addFloat(buf_parquet.b_e237);
    else if (spec.fieldName == "e277")            addFloat(buf_parquet.b_e277);
    else if (spec.fieldName == "emaxs1")          addFloat(buf_parquet.b_emaxs1);
    else if (spec.fieldName == "emaxs2")          addFloat(buf_parquet.b_emaxs2);
    else if (spec.fieldName == "e2tsts1")         addFloat(buf_parquet.b_e2tsts1);
    else if (spec.fieldName == "reta")            addFloat(buf_parquet.b_reta);
    else if (spec.fieldName == "rphi")            addFloat(buf_parquet.b_rphi);
    else if (spec.fieldName == "rhad")            addFloat(buf_parquet.b_rhad);
    else if (spec.fieldName == "rhad1")           addFloat(buf_parquet.b_rhad1);
    else if (spec.fieldName == "eratio")          addFloat(buf_parquet.b_eratio);
    else if (spec.fieldName == "f0")              addFloat(buf_parquet.b_f0);
    else if (spec.fieldName == "f1")              addFloat(buf_parquet.b_f1);
    else if (spec.fieldName == "f2")              addFloat(buf_parquet.b_f2);
    else if (spec.fieldName == "f3")              addFloat(buf_parquet.b_f3);
    else if (spec.fieldName == "weta2")           addFloat(buf_parquet.b_weta2);
    else if (spec.fieldName == "secondR")         addFloat(buf_parquet.b_secondR);
    else if (spec.fieldName == "lambdaCenter")    addFloat(buf_parquet.b_lambdaCenter);
    else if (spec.fieldName == "secondLambda")    addFloat(buf_parquet.b_secondLambda);
    else if (spec.fieldName == "fracMax")         addFloat(buf_parquet.b_fracMax);
    else if (spec.fieldName == "lateralMom")      addFloat(buf_parquet.b_lateralMom);
    else if (spec.fieldName == "longitudinalMom") addFloat(buf_parquet.b_longitudinalMom);
  }
}

void CaloClusterConverter::to_parquet(const CaloCluster_t &buf, CaloCluster_parquet &buf_parquet) const {
  if (buf_parquet.b_eta != nullptr)             PARQUET_THROW_NOT_OK(buf_parquet.b_eta->Append(buf.eta));
  if (buf_parquet.b_phi != nullptr)             PARQUET_THROW_NOT_OK(buf_parquet.b_phi->Append(buf.phi));
  if (buf_parquet.b_e != nullptr)               PARQUET_THROW_NOT_OK(buf_parquet.b_e->Append(buf.e));
  if (buf_parquet.b_et != nullptr)              PARQUET_THROW_NOT_OK(buf_parquet.b_et->Append(buf.et));
  if (buf_parquet.b_deta != nullptr)            PARQUET_THROW_NOT_OK(buf_parquet.b_deta->Append(buf.deta));
  if (buf_parquet.b_dphi != nullptr)            PARQUET_THROW_NOT_OK(buf_parquet.b_dphi->Append(buf.dphi));
  if (buf_parquet.b_e0 != nullptr)              PARQUET_THROW_NOT_OK(buf_parquet.b_e0->Append(buf.e0));
  if (buf_parquet.b_e1 != nullptr)              PARQUET_THROW_NOT_OK(buf_parquet.b_e1->Append(buf.e1));
  if (buf_parquet.b_e2 != nullptr)              PARQUET_THROW_NOT_OK(buf_parquet.b_e2->Append(buf.e2));
  if (buf_parquet.b_e3 != nullptr)              PARQUET_THROW_NOT_OK(buf_parquet.b_e3->Append(buf.e3));
  if (buf_parquet.b_ehad1 != nullptr)           PARQUET_THROW_NOT_OK(buf_parquet.b_ehad1->Append(buf.ehad1));
  if (buf_parquet.b_ehad2 != nullptr)           PARQUET_THROW_NOT_OK(buf_parquet.b_ehad2->Append(buf.ehad2));
  if (buf_parquet.b_ehad3 != nullptr)           PARQUET_THROW_NOT_OK(buf_parquet.b_ehad3->Append(buf.ehad3));
  if (buf_parquet.b_etot != nullptr)            PARQUET_THROW_NOT_OK(buf_parquet.b_etot->Append(buf.etot));
  if (buf_parquet.b_e233 != nullptr)            PARQUET_THROW_NOT_OK(buf_parquet.b_e233->Append(buf.e233));
  if (buf_parquet.b_e237 != nullptr)            PARQUET_THROW_NOT_OK(buf_parquet.b_e237->Append(buf.e237));
  if (buf_parquet.b_e277 != nullptr)            PARQUET_THROW_NOT_OK(buf_parquet.b_e277->Append(buf.e277));
  if (buf_parquet.b_emaxs1 != nullptr)          PARQUET_THROW_NOT_OK(buf_parquet.b_emaxs1->Append(buf.emaxs1));
  if (buf_parquet.b_emaxs2 != nullptr)          PARQUET_THROW_NOT_OK(buf_parquet.b_emaxs2->Append(buf.emaxs2));
  if (buf_parquet.b_e2tsts1 != nullptr)         PARQUET_THROW_NOT_OK(buf_parquet.b_e2tsts1->Append(buf.e2tsts1));
  if (buf_parquet.b_reta != nullptr)            PARQUET_THROW_NOT_OK(buf_parquet.b_reta->Append(buf.reta));
  if (buf_parquet.b_rphi != nullptr)            PARQUET_THROW_NOT_OK(buf_parquet.b_rphi->Append(buf.rphi));
  if (buf_parquet.b_rhad != nullptr)            PARQUET_THROW_NOT_OK(buf_parquet.b_rhad->Append(buf.rhad));
  if (buf_parquet.b_rhad1 != nullptr)           PARQUET_THROW_NOT_OK(buf_parquet.b_rhad1->Append(buf.rhad1));
  if (buf_parquet.b_eratio != nullptr)          PARQUET_THROW_NOT_OK(buf_parquet.b_eratio->Append(buf.eratio));
  if (buf_parquet.b_f0 != nullptr)              PARQUET_THROW_NOT_OK(buf_parquet.b_f0->Append(buf.f0));
  if (buf_parquet.b_f1 != nullptr)              PARQUET_THROW_NOT_OK(buf_parquet.b_f1->Append(buf.f1));
  if (buf_parquet.b_f2 != nullptr)              PARQUET_THROW_NOT_OK(buf_parquet.b_f2->Append(buf.f2));
  if (buf_parquet.b_f3 != nullptr)              PARQUET_THROW_NOT_OK(buf_parquet.b_f3->Append(buf.f3));
  if (buf_parquet.b_weta2 != nullptr)           PARQUET_THROW_NOT_OK(buf_parquet.b_weta2->Append(buf.weta2));
  if (buf_parquet.b_secondR != nullptr)         PARQUET_THROW_NOT_OK(buf_parquet.b_secondR->Append(buf.secondR));
  if (buf_parquet.b_lambdaCenter != nullptr)    PARQUET_THROW_NOT_OK(buf_parquet.b_lambdaCenter->Append(buf.lambdaCenter));
  if (buf_parquet.b_secondLambda != nullptr)    PARQUET_THROW_NOT_OK(buf_parquet.b_secondLambda->Append(buf.secondLambda));
  if (buf_parquet.b_fracMax != nullptr)         PARQUET_THROW_NOT_OK(buf_parquet.b_fracMax->Append(buf.fracMax));
  if (buf_parquet.b_lateralMom != nullptr)      PARQUET_THROW_NOT_OK(buf_parquet.b_lateralMom->Append(buf.lateralMom));
  if (buf_parquet.b_longitudinalMom != nullptr) PARQUET_THROW_NOT_OK(buf_parquet.b_longitudinalMom->Append(buf.longitudinalMom));
}

void CaloClusterConverter::to_parquet(const CaloCluster *clus, CaloCluster_parquet &buf_parquet) const {
  CaloCluster_t buf;
  to_ntuple(clus, buf);
  to_parquet(buf, buf_parquet);
}
