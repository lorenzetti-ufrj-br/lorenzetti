#include "RootStreamParquetMaker.h"
#include "GaugiKernel/EventContext.h"
#include "GaugiKernel/StatusCode.h"
#include "GaugiKernel/MsgStream.h"
#include "EventInfo/EventInfoContainer.h"
#include "EventInfo/SeedContainer.h"
#include "TruthParticle/TruthParticleContainer.h"
#include "CaloCluster/CaloClusterContainer.h"
#include "CaloRings/CaloRingsContainer.h"
#include "Egamma/ElectronContainer.h"

#include <arrow/api.h>
#include <arrow/io/file.h>
#include <parquet/arrow/writer.h>

#include <iostream>

struct RootStreamParquetMaker::Impl
{
  struct ListCol
  {
    std::string name;
    std::shared_ptr<arrow::FloatBuilder> val_builder;
    std::unique_ptr<arrow::ListBuilder> list_builder;
  };

  static void initListCol(ListCol &col, const std::string &name)
  {
    col.name = name;
    col.val_builder = std::make_shared<arrow::FloatBuilder>();
    col.list_builder = std::make_unique<arrow::ListBuilder>(arrow::default_memory_pool(), col.val_builder);
  }

  static void appendList(ListCol &col, const std::vector<float> &vals)
  {
    PARQUET_THROW_NOT_OK(col.list_builder->Append());
    for (float v : vals)
    {
      PARQUET_THROW_NOT_OK(col.val_builder->Append(v));
    }
  }

  // Scalar int builders
  arrow::Int32Builder b_eventNumber;
  arrow::Int32Builder b_runNumber;

  // Scalar float builders
  arrow::FloatBuilder b_avgmu;
  arrow::FloatBuilder b_cl_eta;
  arrow::FloatBuilder b_cl_phi;
  arrow::FloatBuilder b_cl_e;
  arrow::FloatBuilder b_cl_et;
  arrow::FloatBuilder b_cl_deta;
  arrow::FloatBuilder b_cl_dphi;
  arrow::FloatBuilder b_cl_e0;
  arrow::FloatBuilder b_cl_e1;
  arrow::FloatBuilder b_cl_e2;
  arrow::FloatBuilder b_cl_e3;
  arrow::FloatBuilder b_cl_ehad1;
  arrow::FloatBuilder b_cl_ehad2;
  arrow::FloatBuilder b_cl_ehad3;
  arrow::FloatBuilder b_cl_etot;
  arrow::FloatBuilder b_cl_e233;
  arrow::FloatBuilder b_cl_e237;
  arrow::FloatBuilder b_cl_e277;
  arrow::FloatBuilder b_cl_emaxs1;
  arrow::FloatBuilder b_cl_emaxs2;
  arrow::FloatBuilder b_cl_e2tsts1;
  arrow::FloatBuilder b_cl_reta;
  arrow::FloatBuilder b_cl_rphi;
  arrow::FloatBuilder b_cl_rhad;
  arrow::FloatBuilder b_cl_rhad1;
  arrow::FloatBuilder b_cl_eratio;
  arrow::FloatBuilder b_cl_f0;
  arrow::FloatBuilder b_cl_f1;
  arrow::FloatBuilder b_cl_f2;
  arrow::FloatBuilder b_cl_f3;
  arrow::FloatBuilder b_cl_weta2;
  arrow::FloatBuilder b_cl_secondR;
  arrow::FloatBuilder b_cl_lambdaCenter;
  arrow::FloatBuilder b_cl_secondLambda;
  arrow::FloatBuilder b_cl_fracMax;
  arrow::FloatBuilder b_cl_lateralMom;
  arrow::FloatBuilder b_cl_longitudinalMom;

  arrow::FloatBuilder b_el_eta;
  arrow::FloatBuilder b_el_et;
  arrow::FloatBuilder b_el_phi;
  arrow::BooleanBuilder b_el_tight;
  arrow::BooleanBuilder b_el_medium;
  arrow::BooleanBuilder b_el_loose;
  arrow::BooleanBuilder b_el_vloose;

  arrow::FloatBuilder b_truth_cl_eta;
  arrow::FloatBuilder b_truth_cl_phi;
  arrow::FloatBuilder b_truth_cl_e;
  arrow::FloatBuilder b_truth_cl_et;
  arrow::FloatBuilder b_truth_cl_deta;
  arrow::FloatBuilder b_truth_cl_dphi;
  arrow::FloatBuilder b_truth_cl_e0;
  arrow::FloatBuilder b_truth_cl_e1;
  arrow::FloatBuilder b_truth_cl_e2;
  arrow::FloatBuilder b_truth_cl_e3;
  arrow::FloatBuilder b_truth_cl_ehad1;
  arrow::FloatBuilder b_truth_cl_ehad2;
  arrow::FloatBuilder b_truth_cl_ehad3;
  arrow::FloatBuilder b_truth_cl_etot;
  arrow::FloatBuilder b_truth_cl_e233;
  arrow::FloatBuilder b_truth_cl_e237;
  arrow::FloatBuilder b_truth_cl_e277;
  arrow::FloatBuilder b_truth_cl_emaxs1;
  arrow::FloatBuilder b_truth_cl_emaxs2;
  arrow::FloatBuilder b_truth_cl_e2tsts1;
  arrow::FloatBuilder b_truth_cl_reta;
  arrow::FloatBuilder b_truth_cl_rphi;
  arrow::FloatBuilder b_truth_cl_rhad;
  arrow::FloatBuilder b_truth_cl_rhad1;
  arrow::FloatBuilder b_truth_cl_eratio;
  arrow::FloatBuilder b_truth_cl_f0;
  arrow::FloatBuilder b_truth_cl_f1;
  arrow::FloatBuilder b_truth_cl_f2;
  arrow::FloatBuilder b_truth_cl_f3;
  arrow::FloatBuilder b_truth_cl_weta2;
  arrow::FloatBuilder b_truth_cl_secondR;
  arrow::FloatBuilder b_truth_cl_lambdaCenter;
  arrow::FloatBuilder b_truth_cl_secondLambda;
  arrow::FloatBuilder b_truth_cl_fracMax;
  arrow::FloatBuilder b_truth_cl_lateralMom;
  arrow::FloatBuilder b_truth_cl_longitudinalMom;

  arrow::FloatBuilder b_truth_el_eta;
  arrow::FloatBuilder b_truth_el_et;
  arrow::FloatBuilder b_truth_el_phi;
  arrow::BooleanBuilder b_truth_el_tight;
  arrow::BooleanBuilder b_truth_el_medium;
  arrow::BooleanBuilder b_truth_el_loose;
  arrow::BooleanBuilder b_truth_el_vloose;

  arrow::FloatBuilder b_seed_eta;
  arrow::FloatBuilder b_seed_phi;

  // List builders for rings
  std::vector<ListCol> ring_cols;
  ListCol cl_ringsL0_col;
  std::vector<ListCol> truth_ring_cols;
  ListCol truth_cl_ringsL0_col;

  // MC particles list builders
  ListCol mc_pdgid_col;
  ListCol mc_eta_col;
  ListCol mc_phi_col;
  ListCol mc_e_col;
  ListCol mc_et_col;

  int64_t total_rows{0};
};

RootStreamParquetMaker::RootStreamParquetMaker(std::string name)
    : IMsgService(name),
      Algorithm(),
      m_impl(std::make_unique<Impl>())
{
  declareProperty("OutputFile", m_outputFile = "output.parquet");
  declareProperty("InputEventKey", m_eventKey = "EventInfo");
  declareProperty("InputSeedsKey", m_seedsKey = "Seeds");
  declareProperty("InputTruthKey", m_truthKey = "Particles");
  declareProperty("InputClusterKey", m_clusterKey = "Clusters");
  declareProperty("InputElectronKey", m_electronKey = "Electrons");
  declareProperty("InputRingerL0Key", m_ringerL0Key = "RingsL0");
  declareProperty("InputTruthClusterKey", m_truthClusterKey = "TruthClusters");
  declareProperty("InputTruthElectronKey", m_truthElectronKey = "TruthElectrons");
  declareProperty("InputRingerKeys", m_ringerKeys = {"Rings"});
  declareProperty("InputTruthRingerKeys", m_truthRingerKeys = {"TruthRings"});
  declareProperty("OutputLevel", m_outputLevel = 0);
}

RootStreamParquetMaker::~RootStreamParquetMaker()
{
}

StatusCode RootStreamParquetMaker::initialize()
{
  MSG_INFO("Initializing RootStreamParquetMaker with output: " << m_outputFile);

  // Initialize ring columns
  m_impl->ring_cols.resize(m_ringerKeys.size());
  for (size_t i = 0; i < m_ringerKeys.size(); ++i)
  {
    Impl::initListCol(m_impl->ring_cols[i], "cl_rings_" + m_ringerKeys[i]);
  }
  Impl::initListCol(m_impl->cl_ringsL0_col, "cl_ringsL0");

  m_impl->truth_ring_cols.resize(m_truthRingerKeys.size());
  for (size_t i = 0; i < m_truthRingerKeys.size(); ++i)
  {
    Impl::initListCol(m_impl->truth_ring_cols[i], "truth_cl_rings_" + m_truthRingerKeys[i]);
  }
  Impl::initListCol(m_impl->truth_cl_ringsL0_col, "truth_cl_ringsL0");

  // MC particles list columns
  Impl::initListCol(m_impl->mc_pdgid_col, "mc_pdgid");
  Impl::initListCol(m_impl->mc_eta_col, "mc_eta");
  Impl::initListCol(m_impl->mc_phi_col, "mc_phi");
  Impl::initListCol(m_impl->mc_e_col, "mc_e");
  Impl::initListCol(m_impl->mc_et_col, "mc_et");

  return StatusCode::SUCCESS;
}

StatusCode RootStreamParquetMaker::bookHistograms(SG::EventContext & /*ctx*/) const
{
  return StatusCode::SUCCESS;
}

StatusCode RootStreamParquetMaker::pre_execute(SG::EventContext & /*ctx*/) const
{
  return StatusCode::SUCCESS;
}

StatusCode RootStreamParquetMaker::execute(SG::EventContext & /*ctx*/, const G4Step * /*step*/) const
{
  return StatusCode::SUCCESS;
}

StatusCode RootStreamParquetMaker::execute(SG::EventContext & /*ctx*/, int /*evt*/) const
{
  return StatusCode::SUCCESS;
}

StatusCode RootStreamParquetMaker::post_execute(SG::EventContext & /*ctx*/) const
{
  return StatusCode::SUCCESS;
}

StatusCode RootStreamParquetMaker::fillHistograms(SG::EventContext &ctx) const
{
  SG::ReadHandle<xAOD::EventInfoContainer> event_container(m_eventKey, ctx);
  if (!event_container.isValid())
  {
    MSG_FATAL("Cannot read xAOD::EventInfoContainer with key " << m_eventKey);
    return StatusCode::FAILURE;
  }

  std::vector<SG::ReadHandle<xAOD::CaloRingsContainer>> ringer_containers;
  for (const auto &key : m_ringerKeys)
    ringer_containers.emplace_back(key, ctx);

  std::vector<SG::ReadHandle<xAOD::CaloRingsContainer>> truth_ringer_containers;
  for (const auto &key : m_truthRingerKeys)
    truth_ringer_containers.emplace_back(key, ctx);

  SG::ReadHandle<xAOD::ElectronContainer> electron_container(m_electronKey, ctx);
  if (!electron_container.isValid())
  {
    MSG_FATAL("Cannot read xAOD::ElectronContainer with key " << m_electronKey);
    return StatusCode::FAILURE;
  }

  SG::ReadHandle<xAOD::SeedContainer> seed_container(m_seedsKey, ctx);
  if (!seed_container.isValid())
  {
    MSG_FATAL("Cannot read xAOD::SeedContainer with key " << m_seedsKey);
    return StatusCode::FAILURE;
  }

  SG::ReadHandle<xAOD::TruthParticleContainer> truth_container(m_truthKey, ctx);
  if (!truth_container.isValid())
  {
    MSG_FATAL("Cannot read xAOD::TruthParticleContainer with key " << m_truthKey);
    return StatusCode::FAILURE;
  }

  SG::ReadHandle<xAOD::CaloRingsContainer> ringerL0_container(m_ringerL0Key, ctx);
  SG::ReadHandle<xAOD::CaloClusterContainer> cluster_container(m_clusterKey, ctx);
  SG::ReadHandle<xAOD::CaloClusterContainer> truth_cluster_container(m_truthClusterKey, ctx);
  SG::ReadHandle<xAOD::ElectronContainer> truth_electron_container(m_truthElectronKey, ctx);

  auto evt = (*event_container).front();
  int eventNumber = evt->eventNumber();
  int runNumber = evt->runNumber();
  float avgmu = evt->averageInteractionsPerCrossing();

  for (auto el : *electron_container)
  {
    auto clus = el->caloCluster();

    const xAOD::CaloRings *cl_ringerL0 = nullptr;
    if (ringerL0_container.isValid())
    {
      for (auto ring : *ringerL0_container)
      {
        if (ring->caloCluster() == clus)
        {
          cl_ringerL0 = ring;
          break;
        }
      }
    }

    const xAOD::CaloCluster *truth_clus = nullptr;
    if (truth_cluster_container.isValid())
    {
      for (auto tr_cl : *truth_cluster_container)
      {
        if (tr_cl->seed() == clus->seed())
        {
          truth_clus = tr_cl;
          break;
        }
      }
    }

    const xAOD::Electron *truth_el = nullptr;
    if (truth_electron_container.isValid())
    {
      for (auto tr_el : *truth_electron_container)
      {
        if (tr_el->caloCluster() && tr_el->caloCluster()->seed() == clus->seed())
        {
          truth_el = tr_el;
          break;
        }
      }
    }

    // Append event-level
    PARQUET_THROW_NOT_OK(m_impl->b_eventNumber.Append(eventNumber));
    PARQUET_THROW_NOT_OK(m_impl->b_runNumber.Append(runNumber));
    PARQUET_THROW_NOT_OK(m_impl->b_avgmu.Append(avgmu));

    // Append cluster kinematics
    PARQUET_THROW_NOT_OK(m_impl->b_cl_eta.Append(clus->eta()));
    PARQUET_THROW_NOT_OK(m_impl->b_cl_phi.Append(clus->phi()));
    PARQUET_THROW_NOT_OK(m_impl->b_cl_e.Append(clus->e()));
    PARQUET_THROW_NOT_OK(m_impl->b_cl_et.Append(clus->et()));
    PARQUET_THROW_NOT_OK(m_impl->b_cl_deta.Append(clus->deltaEta()));
    PARQUET_THROW_NOT_OK(m_impl->b_cl_dphi.Append(clus->deltaPhi()));

    // Append cluster sampling energies
    PARQUET_THROW_NOT_OK(m_impl->b_cl_e0.Append(clus->e0()));
    PARQUET_THROW_NOT_OK(m_impl->b_cl_e1.Append(clus->e1()));
    PARQUET_THROW_NOT_OK(m_impl->b_cl_e2.Append(clus->e2()));
    PARQUET_THROW_NOT_OK(m_impl->b_cl_e3.Append(clus->e3()));
    PARQUET_THROW_NOT_OK(m_impl->b_cl_ehad1.Append(clus->ehad1()));
    PARQUET_THROW_NOT_OK(m_impl->b_cl_ehad2.Append(clus->ehad2()));
    PARQUET_THROW_NOT_OK(m_impl->b_cl_ehad3.Append(clus->ehad3()));
    PARQUET_THROW_NOT_OK(m_impl->b_cl_etot.Append(clus->etot()));

    // Append cluster shower shapes
    PARQUET_THROW_NOT_OK(m_impl->b_cl_e233.Append(clus->e233()));
    PARQUET_THROW_NOT_OK(m_impl->b_cl_e237.Append(clus->e237()));
    PARQUET_THROW_NOT_OK(m_impl->b_cl_e277.Append(clus->e277()));
    PARQUET_THROW_NOT_OK(m_impl->b_cl_emaxs1.Append(clus->emaxs1()));
    PARQUET_THROW_NOT_OK(m_impl->b_cl_emaxs2.Append(clus->emaxs2()));
    PARQUET_THROW_NOT_OK(m_impl->b_cl_e2tsts1.Append(clus->e2tsts1()));
    PARQUET_THROW_NOT_OK(m_impl->b_cl_reta.Append(clus->reta()));
    PARQUET_THROW_NOT_OK(m_impl->b_cl_rphi.Append(clus->rphi()));
    PARQUET_THROW_NOT_OK(m_impl->b_cl_rhad.Append(clus->rhad()));
    PARQUET_THROW_NOT_OK(m_impl->b_cl_rhad1.Append(clus->rhad1()));
    PARQUET_THROW_NOT_OK(m_impl->b_cl_eratio.Append(clus->eratio()));
    PARQUET_THROW_NOT_OK(m_impl->b_cl_f0.Append(clus->f0()));
    PARQUET_THROW_NOT_OK(m_impl->b_cl_f1.Append(clus->f1()));
    PARQUET_THROW_NOT_OK(m_impl->b_cl_f2.Append(clus->f2()));
    PARQUET_THROW_NOT_OK(m_impl->b_cl_f3.Append(clus->f3()));
    PARQUET_THROW_NOT_OK(m_impl->b_cl_weta2.Append(clus->weta2()));

    // Append cluster moments
    PARQUET_THROW_NOT_OK(m_impl->b_cl_secondR.Append(clus->secondR()));
    PARQUET_THROW_NOT_OK(m_impl->b_cl_lambdaCenter.Append(clus->lambdaCenter()));
    PARQUET_THROW_NOT_OK(m_impl->b_cl_secondLambda.Append(clus->secondLambda()));
    PARQUET_THROW_NOT_OK(m_impl->b_cl_fracMax.Append(clus->fracMax()));
    PARQUET_THROW_NOT_OK(m_impl->b_cl_lateralMom.Append(clus->lateralMom()));
    PARQUET_THROW_NOT_OK(m_impl->b_cl_longitudinalMom.Append(clus->longitudinalMom()));

    // Append rings
    for (size_t i = 0; i < m_ringerKeys.size(); ++i)
    {
      std::vector<float> r_vec;
      if (ringer_containers[i].isValid())
      {
        for (auto ring : *ringer_containers[i])
        {
          if (ring->caloCluster() == clus)
          {
            for (auto r : ring->rings())
              r_vec.push_back(r);
            break;
          }
        }
      }
      Impl::appendList(m_impl->ring_cols[i], r_vec);
    }

    std::vector<float> rL0_vec;
    if (cl_ringerL0)
    {
      for (auto r : cl_ringerL0->rings())
        rL0_vec.push_back(r);
    }
    Impl::appendList(m_impl->cl_ringsL0_col, rL0_vec);

    // Append electron PID & kinematics
    PARQUET_THROW_NOT_OK(m_impl->b_el_eta.Append(el->eta()));
    PARQUET_THROW_NOT_OK(m_impl->b_el_et.Append(el->et()));
    PARQUET_THROW_NOT_OK(m_impl->b_el_phi.Append(el->phi()));
    PARQUET_THROW_NOT_OK(m_impl->b_el_tight.Append(el->isTight()));
    PARQUET_THROW_NOT_OK(m_impl->b_el_medium.Append(el->isMedium()));
    PARQUET_THROW_NOT_OK(m_impl->b_el_loose.Append(el->isLoose()));
    PARQUET_THROW_NOT_OK(m_impl->b_el_vloose.Append(el->isVeryLoose()));

    // Append truth cluster
    if (truth_clus)
    {
      PARQUET_THROW_NOT_OK(m_impl->b_truth_cl_eta.Append(truth_clus->eta()));
      PARQUET_THROW_NOT_OK(m_impl->b_truth_cl_phi.Append(truth_clus->phi()));
      PARQUET_THROW_NOT_OK(m_impl->b_truth_cl_e.Append(truth_clus->e()));
      PARQUET_THROW_NOT_OK(m_impl->b_truth_cl_et.Append(truth_clus->et()));
      PARQUET_THROW_NOT_OK(m_impl->b_truth_cl_deta.Append(truth_clus->deltaEta()));
      PARQUET_THROW_NOT_OK(m_impl->b_truth_cl_dphi.Append(truth_clus->deltaPhi()));

      PARQUET_THROW_NOT_OK(m_impl->b_truth_cl_e0.Append(truth_clus->e0()));
      PARQUET_THROW_NOT_OK(m_impl->b_truth_cl_e1.Append(truth_clus->e1()));
      PARQUET_THROW_NOT_OK(m_impl->b_truth_cl_e2.Append(truth_clus->e2()));
      PARQUET_THROW_NOT_OK(m_impl->b_truth_cl_e3.Append(truth_clus->e3()));
      PARQUET_THROW_NOT_OK(m_impl->b_truth_cl_ehad1.Append(truth_clus->ehad1()));
      PARQUET_THROW_NOT_OK(m_impl->b_truth_cl_ehad2.Append(truth_clus->ehad2()));
      PARQUET_THROW_NOT_OK(m_impl->b_truth_cl_ehad3.Append(truth_clus->ehad3()));
      PARQUET_THROW_NOT_OK(m_impl->b_truth_cl_etot.Append(truth_clus->etot()));

      PARQUET_THROW_NOT_OK(m_impl->b_truth_cl_e233.Append(truth_clus->e233()));
      PARQUET_THROW_NOT_OK(m_impl->b_truth_cl_e237.Append(truth_clus->e237()));
      PARQUET_THROW_NOT_OK(m_impl->b_truth_cl_e277.Append(truth_clus->e277()));
      PARQUET_THROW_NOT_OK(m_impl->b_truth_cl_emaxs1.Append(truth_clus->emaxs1()));
      PARQUET_THROW_NOT_OK(m_impl->b_truth_cl_emaxs2.Append(truth_clus->emaxs2()));
      PARQUET_THROW_NOT_OK(m_impl->b_truth_cl_e2tsts1.Append(truth_clus->e2tsts1()));
      PARQUET_THROW_NOT_OK(m_impl->b_truth_cl_reta.Append(truth_clus->reta()));
      PARQUET_THROW_NOT_OK(m_impl->b_truth_cl_rphi.Append(truth_clus->rphi()));
      PARQUET_THROW_NOT_OK(m_impl->b_truth_cl_rhad.Append(truth_clus->rhad()));
      PARQUET_THROW_NOT_OK(m_impl->b_truth_cl_rhad1.Append(truth_clus->rhad1()));
      PARQUET_THROW_NOT_OK(m_impl->b_truth_cl_eratio.Append(truth_clus->eratio()));
      PARQUET_THROW_NOT_OK(m_impl->b_truth_cl_f0.Append(truth_clus->f0()));
      PARQUET_THROW_NOT_OK(m_impl->b_truth_cl_f1.Append(truth_clus->f1()));
      PARQUET_THROW_NOT_OK(m_impl->b_truth_cl_f2.Append(truth_clus->f2()));
      PARQUET_THROW_NOT_OK(m_impl->b_truth_cl_f3.Append(truth_clus->f3()));
      PARQUET_THROW_NOT_OK(m_impl->b_truth_cl_weta2.Append(truth_clus->weta2()));

      PARQUET_THROW_NOT_OK(m_impl->b_truth_cl_secondR.Append(truth_clus->secondR()));
      PARQUET_THROW_NOT_OK(m_impl->b_truth_cl_lambdaCenter.Append(truth_clus->lambdaCenter()));
      PARQUET_THROW_NOT_OK(m_impl->b_truth_cl_secondLambda.Append(truth_clus->secondLambda()));
      PARQUET_THROW_NOT_OK(m_impl->b_truth_cl_fracMax.Append(truth_clus->fracMax()));
      PARQUET_THROW_NOT_OK(m_impl->b_truth_cl_lateralMom.Append(truth_clus->lateralMom()));
      PARQUET_THROW_NOT_OK(m_impl->b_truth_cl_longitudinalMom.Append(truth_clus->longitudinalMom()));
    }
    else
    {
      PARQUET_THROW_NOT_OK(m_impl->b_truth_cl_eta.Append(0.0f));
      PARQUET_THROW_NOT_OK(m_impl->b_truth_cl_phi.Append(0.0f));
      PARQUET_THROW_NOT_OK(m_impl->b_truth_cl_e.Append(0.0f));
      PARQUET_THROW_NOT_OK(m_impl->b_truth_cl_et.Append(0.0f));
      PARQUET_THROW_NOT_OK(m_impl->b_truth_cl_deta.Append(0.0f));
      PARQUET_THROW_NOT_OK(m_impl->b_truth_cl_dphi.Append(0.0f));

      PARQUET_THROW_NOT_OK(m_impl->b_truth_cl_e0.Append(0.0f));
      PARQUET_THROW_NOT_OK(m_impl->b_truth_cl_e1.Append(0.0f));
      PARQUET_THROW_NOT_OK(m_impl->b_truth_cl_e2.Append(0.0f));
      PARQUET_THROW_NOT_OK(m_impl->b_truth_cl_e3.Append(0.0f));
      PARQUET_THROW_NOT_OK(m_impl->b_truth_cl_ehad1.Append(0.0f));
      PARQUET_THROW_NOT_OK(m_impl->b_truth_cl_ehad2.Append(0.0f));
      PARQUET_THROW_NOT_OK(m_impl->b_truth_cl_ehad3.Append(0.0f));
      PARQUET_THROW_NOT_OK(m_impl->b_truth_cl_etot.Append(0.0f));

      PARQUET_THROW_NOT_OK(m_impl->b_truth_cl_e233.Append(0.0f));
      PARQUET_THROW_NOT_OK(m_impl->b_truth_cl_e237.Append(0.0f));
      PARQUET_THROW_NOT_OK(m_impl->b_truth_cl_e277.Append(0.0f));
      PARQUET_THROW_NOT_OK(m_impl->b_truth_cl_emaxs1.Append(0.0f));
      PARQUET_THROW_NOT_OK(m_impl->b_truth_cl_emaxs2.Append(0.0f));
      PARQUET_THROW_NOT_OK(m_impl->b_truth_cl_e2tsts1.Append(0.0f));
      PARQUET_THROW_NOT_OK(m_impl->b_truth_cl_reta.Append(0.0f));
      PARQUET_THROW_NOT_OK(m_impl->b_truth_cl_rphi.Append(0.0f));
      PARQUET_THROW_NOT_OK(m_impl->b_truth_cl_rhad.Append(0.0f));
      PARQUET_THROW_NOT_OK(m_impl->b_truth_cl_rhad1.Append(0.0f));
      PARQUET_THROW_NOT_OK(m_impl->b_truth_cl_eratio.Append(0.0f));
      PARQUET_THROW_NOT_OK(m_impl->b_truth_cl_f0.Append(0.0f));
      PARQUET_THROW_NOT_OK(m_impl->b_truth_cl_f1.Append(0.0f));
      PARQUET_THROW_NOT_OK(m_impl->b_truth_cl_f2.Append(0.0f));
      PARQUET_THROW_NOT_OK(m_impl->b_truth_cl_f3.Append(0.0f));
      PARQUET_THROW_NOT_OK(m_impl->b_truth_cl_weta2.Append(0.0f));

      PARQUET_THROW_NOT_OK(m_impl->b_truth_cl_secondR.Append(0.0f));
      PARQUET_THROW_NOT_OK(m_impl->b_truth_cl_lambdaCenter.Append(0.0f));
      PARQUET_THROW_NOT_OK(m_impl->b_truth_cl_secondLambda.Append(0.0f));
      PARQUET_THROW_NOT_OK(m_impl->b_truth_cl_fracMax.Append(0.0f));
      PARQUET_THROW_NOT_OK(m_impl->b_truth_cl_lateralMom.Append(0.0f));
      PARQUET_THROW_NOT_OK(m_impl->b_truth_cl_longitudinalMom.Append(0.0f));
    }

    // Append truth rings
    for (size_t i = 0; i < m_truthRingerKeys.size(); ++i)
    {
      std::vector<float> tr_vec;
      if (truth_ringer_containers[i].isValid() && truth_clus)
      {
        for (auto ring : *truth_ringer_containers[i])
        {
          if (ring->caloCluster() == truth_clus)
          {
            for (auto r : ring->rings())
              tr_vec.push_back(r);
            break;
          }
        }
      }
      Impl::appendList(m_impl->truth_ring_cols[i], tr_vec);
    }

    std::vector<float> trL0_vec;
    Impl::appendList(m_impl->truth_cl_ringsL0_col, trL0_vec);

    // Append truth electron
    if (truth_el)
    {
      PARQUET_THROW_NOT_OK(m_impl->b_truth_el_eta.Append(truth_el->eta()));
      PARQUET_THROW_NOT_OK(m_impl->b_truth_el_et.Append(truth_el->et()));
      PARQUET_THROW_NOT_OK(m_impl->b_truth_el_phi.Append(truth_el->phi()));
      PARQUET_THROW_NOT_OK(m_impl->b_truth_el_tight.Append(truth_el->isTight()));
      PARQUET_THROW_NOT_OK(m_impl->b_truth_el_medium.Append(truth_el->isMedium()));
      PARQUET_THROW_NOT_OK(m_impl->b_truth_el_loose.Append(truth_el->isLoose()));
      PARQUET_THROW_NOT_OK(m_impl->b_truth_el_vloose.Append(truth_el->isVeryLoose()));
    }
    else
    {
      PARQUET_THROW_NOT_OK(m_impl->b_truth_el_eta.Append(-1.0f));
      PARQUET_THROW_NOT_OK(m_impl->b_truth_el_et.Append(-1.0f));
      PARQUET_THROW_NOT_OK(m_impl->b_truth_el_phi.Append(-1.0f));
      PARQUET_THROW_NOT_OK(m_impl->b_truth_el_tight.Append(false));
      PARQUET_THROW_NOT_OK(m_impl->b_truth_el_medium.Append(false));
      PARQUET_THROW_NOT_OK(m_impl->b_truth_el_loose.Append(false));
      PARQUET_THROW_NOT_OK(m_impl->b_truth_el_vloose.Append(false));
    }

    // Append seed
    auto seed = clus->seed();
    PARQUET_THROW_NOT_OK(m_impl->b_seed_eta.Append(seed->eta()));
    PARQUET_THROW_NOT_OK(m_impl->b_seed_phi.Append(seed->phi()));

    // Append MC particles
    std::vector<float> mc_pdgid_vec;
    std::vector<float> mc_eta_vec;
    std::vector<float> mc_phi_vec;
    std::vector<float> mc_e_vec;
    std::vector<float> mc_et_vec;
    for (auto mc : *truth_container)
    {
      if (mc->seedid() == seed->id())
      {
        mc_pdgid_vec.push_back(static_cast<float>(mc->pdgid()));
        mc_eta_vec.push_back(mc->eta());
        mc_phi_vec.push_back(mc->phi());
        mc_e_vec.push_back(mc->e());
        mc_et_vec.push_back(mc->et());
      }
    }
    Impl::appendList(m_impl->mc_pdgid_col, mc_pdgid_vec);
    Impl::appendList(m_impl->mc_eta_col, mc_eta_vec);
    Impl::appendList(m_impl->mc_phi_col, mc_phi_vec);
    Impl::appendList(m_impl->mc_e_col, mc_e_vec);
    Impl::appendList(m_impl->mc_et_col, mc_et_vec);

    m_impl->total_rows++;
  }

  return StatusCode::SUCCESS;
}

StatusCode RootStreamParquetMaker::finalize()
{
  MSG_INFO("Finalizing RootStreamParquetMaker: writing " << m_impl->total_rows << " rows to " << m_outputFile);

  std::vector<std::shared_ptr<arrow::Field>> fields;
  std::vector<std::shared_ptr<arrow::Array>> arrays;

  auto addScalarField = [&](const std::string &name, std::shared_ptr<arrow::DataType> type, arrow::ArrayBuilder &builder) {
    std::shared_ptr<arrow::Array> arr;
    PARQUET_THROW_NOT_OK(builder.Finish(&arr));
    fields.push_back(arrow::field(name, type));
    arrays.push_back(arr);
  };

  auto addListField = [&](Impl::ListCol &col) {
    std::shared_ptr<arrow::Array> arr;
    PARQUET_THROW_NOT_OK(col.list_builder->Finish(&arr));
    fields.push_back(arrow::field(col.name, arrow::list(arrow::float32())));
    arrays.push_back(arr);
  };

  // Event
  addScalarField("EventNumber", arrow::int32(), m_impl->b_eventNumber);
  addScalarField("RunNumber", arrow::int32(), m_impl->b_runNumber);
  addScalarField("avgmu", arrow::float32(), m_impl->b_avgmu);

  // Cluster kinematics
  addScalarField("cl_eta", arrow::float32(), m_impl->b_cl_eta);
  addScalarField("cl_phi", arrow::float32(), m_impl->b_cl_phi);
  addScalarField("cl_e", arrow::float32(), m_impl->b_cl_e);
  addScalarField("cl_et", arrow::float32(), m_impl->b_cl_et);
  addScalarField("cl_deta", arrow::float32(), m_impl->b_cl_deta);
  addScalarField("cl_dphi", arrow::float32(), m_impl->b_cl_dphi);

  // Cluster sampling energies
  addScalarField("cl_e0", arrow::float32(), m_impl->b_cl_e0);
  addScalarField("cl_e1", arrow::float32(), m_impl->b_cl_e1);
  addScalarField("cl_e2", arrow::float32(), m_impl->b_cl_e2);
  addScalarField("cl_e3", arrow::float32(), m_impl->b_cl_e3);
  addScalarField("cl_ehad1", arrow::float32(), m_impl->b_cl_ehad1);
  addScalarField("cl_ehad2", arrow::float32(), m_impl->b_cl_ehad2);
  addScalarField("cl_ehad3", arrow::float32(), m_impl->b_cl_ehad3);
  addScalarField("cl_etot", arrow::float32(), m_impl->b_cl_etot);

  // Cluster shower shapes
  addScalarField("cl_e233", arrow::float32(), m_impl->b_cl_e233);
  addScalarField("cl_e237", arrow::float32(), m_impl->b_cl_e237);
  addScalarField("cl_e277", arrow::float32(), m_impl->b_cl_e277);
  addScalarField("cl_emaxs1", arrow::float32(), m_impl->b_cl_emaxs1);
  addScalarField("cl_emaxs2", arrow::float32(), m_impl->b_cl_emaxs2);
  addScalarField("cl_e2tsts1", arrow::float32(), m_impl->b_cl_e2tsts1);
  addScalarField("cl_reta", arrow::float32(), m_impl->b_cl_reta);
  addScalarField("cl_rphi", arrow::float32(), m_impl->b_cl_rphi);
  addScalarField("cl_rhad", arrow::float32(), m_impl->b_cl_rhad);
  addScalarField("cl_rhad1", arrow::float32(), m_impl->b_cl_rhad1);
  addScalarField("cl_eratio", arrow::float32(), m_impl->b_cl_eratio);
  addScalarField("cl_f0", arrow::float32(), m_impl->b_cl_f0);
  addScalarField("cl_f1", arrow::float32(), m_impl->b_cl_f1);
  addScalarField("cl_f2", arrow::float32(), m_impl->b_cl_f2);
  addScalarField("cl_f3", arrow::float32(), m_impl->b_cl_f3);
  addScalarField("cl_weta2", arrow::float32(), m_impl->b_cl_weta2);

  // Rings
  for (size_t i = 0; i < m_ringerKeys.size(); ++i)
    addListField(m_impl->ring_cols[i]);
  addListField(m_impl->cl_ringsL0_col);

  // Cluster moments
  addScalarField("cl_secondR", arrow::float32(), m_impl->b_cl_secondR);
  addScalarField("cl_lambdaCenter", arrow::float32(), m_impl->b_cl_lambdaCenter);
  addScalarField("cl_secondLambda", arrow::float32(), m_impl->b_cl_secondLambda);
  addScalarField("cl_fracMax", arrow::float32(), m_impl->b_cl_fracMax);
  addScalarField("cl_lateralMom", arrow::float32(), m_impl->b_cl_lateralMom);
  addScalarField("cl_longitudinalMom", arrow::float32(), m_impl->b_cl_longitudinalMom);

  // Electron
  addScalarField("el_eta", arrow::float32(), m_impl->b_el_eta);
  addScalarField("el_et", arrow::float32(), m_impl->b_el_et);
  addScalarField("el_phi", arrow::float32(), m_impl->b_el_phi);
  addScalarField("el_tight", arrow::boolean(), m_impl->b_el_tight);
  addScalarField("el_medium", arrow::boolean(), m_impl->b_el_medium);
  addScalarField("el_loose", arrow::boolean(), m_impl->b_el_loose);
  addScalarField("el_vloose", arrow::boolean(), m_impl->b_el_vloose);

  // Truth cluster
  addScalarField("truth_cl_eta", arrow::float32(), m_impl->b_truth_cl_eta);
  addScalarField("truth_cl_phi", arrow::float32(), m_impl->b_truth_cl_phi);
  addScalarField("truth_cl_e", arrow::float32(), m_impl->b_truth_cl_e);
  addScalarField("truth_cl_et", arrow::float32(), m_impl->b_truth_cl_et);
  addScalarField("truth_cl_deta", arrow::float32(), m_impl->b_truth_cl_deta);
  addScalarField("truth_cl_dphi", arrow::float32(), m_impl->b_truth_cl_dphi);
  addScalarField("truth_cl_e0", arrow::float32(), m_impl->b_truth_cl_e0);
  addScalarField("truth_cl_e1", arrow::float32(), m_impl->b_truth_cl_e1);
  addScalarField("truth_cl_e2", arrow::float32(), m_impl->b_truth_cl_e2);
  addScalarField("truth_cl_e3", arrow::float32(), m_impl->b_truth_cl_e3);
  addScalarField("truth_cl_ehad1", arrow::float32(), m_impl->b_truth_cl_ehad1);
  addScalarField("truth_cl_ehad2", arrow::float32(), m_impl->b_truth_cl_ehad2);
  addScalarField("truth_cl_ehad3", arrow::float32(), m_impl->b_truth_cl_ehad3);
  addScalarField("truth_cl_etot", arrow::float32(), m_impl->b_truth_cl_etot);
  addScalarField("truth_cl_e233", arrow::float32(), m_impl->b_truth_cl_e233);
  addScalarField("truth_cl_e237", arrow::float32(), m_impl->b_truth_cl_e237);
  addScalarField("truth_cl_e277", arrow::float32(), m_impl->b_truth_cl_e277);
  addScalarField("truth_cl_emaxs1", arrow::float32(), m_impl->b_truth_cl_emaxs1);
  addScalarField("truth_cl_emaxs2", arrow::float32(), m_impl->b_truth_cl_emaxs2);
  addScalarField("truth_cl_e2tsts1", arrow::float32(), m_impl->b_truth_cl_e2tsts1);
  addScalarField("truth_cl_reta", arrow::float32(), m_impl->b_truth_cl_reta);
  addScalarField("truth_cl_rphi", arrow::float32(), m_impl->b_truth_cl_rphi);
  addScalarField("truth_cl_rhad", arrow::float32(), m_impl->b_truth_cl_rhad);
  addScalarField("truth_cl_rhad1", arrow::float32(), m_impl->b_truth_cl_rhad1);
  addScalarField("truth_cl_eratio", arrow::float32(), m_impl->b_truth_cl_eratio);
  addScalarField("truth_cl_f0", arrow::float32(), m_impl->b_truth_cl_f0);
  addScalarField("truth_cl_f1", arrow::float32(), m_impl->b_truth_cl_f1);
  addScalarField("truth_cl_f2", arrow::float32(), m_impl->b_truth_cl_f2);
  addScalarField("truth_cl_f3", arrow::float32(), m_impl->b_truth_cl_f3);
  addScalarField("truth_cl_weta2", arrow::float32(), m_impl->b_truth_cl_weta2);

  // Truth rings
  for (size_t i = 0; i < m_truthRingerKeys.size(); ++i)
    addListField(m_impl->truth_ring_cols[i]);
  addListField(m_impl->truth_cl_ringsL0_col);

  // Truth moments
  addScalarField("truth_cl_secondR", arrow::float32(), m_impl->b_truth_cl_secondR);
  addScalarField("truth_cl_lambdaCenter", arrow::float32(), m_impl->b_truth_cl_lambdaCenter);
  addScalarField("truth_cl_secondLambda", arrow::float32(), m_impl->b_truth_cl_secondLambda);
  addScalarField("truth_cl_fracMax", arrow::float32(), m_impl->b_truth_cl_fracMax);
  addScalarField("truth_cl_lateralMom", arrow::float32(), m_impl->b_truth_cl_lateralMom);
  addScalarField("truth_cl_longitudinalMom", arrow::float32(), m_impl->b_truth_cl_longitudinalMom);

  // Truth electron
  addScalarField("truth_el_eta", arrow::float32(), m_impl->b_truth_el_eta);
  addScalarField("truth_el_et", arrow::float32(), m_impl->b_truth_el_et);
  addScalarField("truth_el_phi", arrow::float32(), m_impl->b_truth_el_phi);
  addScalarField("truth_el_tight", arrow::boolean(), m_impl->b_truth_el_tight);
  addScalarField("truth_el_medium", arrow::boolean(), m_impl->b_truth_el_medium);
  addScalarField("truth_el_loose", arrow::boolean(), m_impl->b_truth_el_loose);
  addScalarField("truth_el_vloose", arrow::boolean(), m_impl->b_truth_el_vloose);

  // Seed
  addScalarField("seed_eta", arrow::float32(), m_impl->b_seed_eta);
  addScalarField("seed_phi", arrow::float32(), m_impl->b_seed_phi);

  // MC truth particles
  addListField(m_impl->mc_pdgid_col);
  addListField(m_impl->mc_eta_col);
  addListField(m_impl->mc_phi_col);
  addListField(m_impl->mc_e_col);
  addListField(m_impl->mc_et_col);

  auto schema = arrow::schema(fields);
  auto table = arrow::Table::Make(schema, arrays);

  PARQUET_ASSIGN_OR_THROW(auto outfile, arrow::io::FileOutputStream::Open(m_outputFile));
  PARQUET_THROW_NOT_OK(parquet::arrow::WriteTable(*table, arrow::default_memory_pool(), outfile));

  MSG_INFO("Successfully wrote " << m_outputFile);
  return StatusCode::SUCCESS;
}
