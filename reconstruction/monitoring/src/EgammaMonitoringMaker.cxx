#include "EgammaMonitoringMaker.h"
#include "CaloCluster/CaloCluster.h"
#include "CaloCluster/CaloClusterContainer.h"
#include "Egamma/Electron.h"
#include "Egamma/ElectronContainer.h"
#include "EventInfo/EventInfo.h"
#include "EventInfo/EventInfoContainer.h"
#include "CaloRings/CaloRings.h"
#include "CaloRings/CaloRingsContainer.h"

#include "TH1F.h"
#include "TH2F.h"
#include "TMath.h"

#include <cmath>

using namespace Gaugi;
using namespace SG;

EgammaMonitoringMaker::EgammaMonitoringMaker(std::string name)
  : IMsgService(name),
    Algorithm(),
    m_histDir("Expert-Monitoring"),
    m_eventInfoKey("Events"),
    m_clusterKey("Clusters"),
    m_electronKey("Electrons"),
    m_ringsKey("Rings"),
    m_ringsKeys({"Rings", "Rings_Asym", "Rings_Cross", "Rings_Corner", "Rings_Strips", "Rings_Custom"}),
    m_outputLevel(1)
{
  declareProperty("Directory",         m_histDir);
  declareProperty("InputEventInfoKey", m_eventInfoKey);
  declareProperty("InputClusterKey",   m_clusterKey);
  declareProperty("InputElectronKey",  m_electronKey);
  declareProperty("InputRingsKey",     m_ringsKey);
  declareProperty("InputRingsKeys",    m_ringsKeys);
  declareProperty("OutputLevel",       m_outputLevel);
}

EgammaMonitoringMaker::~EgammaMonitoringMaker()
{
}

StatusCode EgammaMonitoringMaker::initialize()
{
  CHECK_INIT();
  setMsgLevel((MSG::Level)m_outputLevel);

  if (!m_ringsKey.empty()) {
    bool found = false;
    for (const auto &k : m_ringsKeys) {
      if (k == m_ringsKey) {
        found = true;
        break;
      }
    }
    if (!found) {
      m_ringsKeys.push_back(m_ringsKey);
    }
  }

  return StatusCode::SUCCESS;
}

TH1F* EgammaMonitoringMaker::book1D(SG::StoreGate *store, const std::string &subDir,
                                    const std::string &name, const std::string &title,
                                    int nbins, float xmin, float xmax) const
{
  if (!store) return nullptr;
  std::string fullDir = subDir.empty() ? m_histDir : (m_histDir + "/" + subDir);
  store->mkdir(fullDir);
  store->cd(fullDir);
  auto *h = new TH1F(name.c_str(), title.c_str(), nbins, xmin, xmax);
  store->add(h);
  return h;
}

TH2F* EgammaMonitoringMaker::book2D(SG::StoreGate *store, const std::string &subDir,
                                    const std::string &name, const std::string &title,
                                    int nbinsX, float xmin, float xmax,
                                    int nbinsY, float ymin, float ymax) const
{
  if (!store) return nullptr;
  std::string fullDir = subDir.empty() ? m_histDir : (m_histDir + "/" + subDir);
  store->mkdir(fullDir);
  store->cd(fullDir);
  auto *h = new TH2F(name.c_str(), title.c_str(), nbinsX, xmin, xmax, nbinsY, ymin, ymax);
  store->add(h);
  return h;
}

void EgammaMonitoringMaker::fill1D(SG::StoreGate *store, const std::string &subDir,
                                   const std::string &name, float value, float weight) const
{
  if (!store || !std::isfinite(value)) return;
  std::string fullDir = subDir.empty() ? m_histDir : (m_histDir + "/" + subDir);
  store->cd(fullDir);
  auto *h = store->hist1(name);
  if (h) {
    h->Fill(value, weight);
  }
}

void EgammaMonitoringMaker::fill2D(SG::StoreGate *store, const std::string &subDir,
                                   const std::string &name, float xval, float yval, float weight) const
{
  if (!store || !std::isfinite(xval) || !std::isfinite(yval)) return;
  std::string fullDir = subDir.empty() ? m_histDir : (m_histDir + "/" + subDir);
  store->cd(fullDir);
  auto *h = store->hist2(name);
  if (h) {
    h->Fill(xval, yval, weight);
  }
}

StatusCode EgammaMonitoringMaker::bookHistograms(SG::EventContext &ctx) const
{
  auto store = ctx.getStoreGateSvc();
  if (!store) {
    MSG_FATAL("StoreGate service not available in EventContext!");
    return StatusCode::FAILURE;
  }

  store->mkdir(m_histDir);

  // 1. EventInfo
  book1D(store, "EventInfo", "avgmu", "Average Interactions per Crossing;\\langle\\mu\\rangle;Events", 100, 0.0, 100.0);
  book1D(store, "EventInfo", "totmu", "Total Interactions per Crossing;\\mu_{tot};Events", 100, 0.0, 100.0);
  book1D(store, "EventInfo", "n_clusters", "Number of CaloClusters per Event;N_{clusters};Events", 30, 0.0, 30.0);
  book1D(store, "EventInfo", "n_electrons", "Number of Electrons per Event;N_{electrons};Events", 10, 0.0, 10.0);

  // 2. Kinematics
  book1D(store, "Kinematics", "cl_et", "CaloCluster Transverse Energy;E_{T} [GeV];Clusters", 100, 0.0, 100.0);
  book1D(store, "Kinematics", "cl_e", "CaloCluster Total Energy;E [GeV];Clusters", 100, 0.0, 150.0);
  book1D(store, "Kinematics", "cl_eta", "CaloCluster \\eta;\\eta;Clusters", 100, -5.0, 5.0);
  book1D(store, "Kinematics", "cl_phi", "CaloCluster \\phi;\\phi [rad];Clusters", 64, -TMath::Pi(), TMath::Pi());
  book1D(store, "Kinematics", "el_et", "Electron Transverse Energy;E_{T} [GeV];Electrons", 100, 0.0, 100.0);
  book1D(store, "Kinematics", "el_e", "Electron Total Energy;E [GeV];Electrons", 100, 0.0, 150.0);
  book1D(store, "Kinematics", "el_eta", "Electron \\eta;\\eta;Electrons", 100, -5.0, 5.0);
  book1D(store, "Kinematics", "el_phi", "Electron \\phi;\\phi [rad];Electrons", 64, -TMath::Pi(), TMath::Pi());

  // 3. Shower Shapes (TrigEgammaMonitoring standard)
  book1D(store, "ShowerShapes", "reta", "Shower Shape R_{\\eta};R_{\\eta} (E_{3\\times 7} / E_{7\\times 7});Clusters", 100, 0.4, 1.05);
  book1D(store, "ShowerShapes", "rphi", "Shower Shape R_{\\phi};R_{\\phi} (E_{3\\times 3} / E_{3\\times 7});Clusters", 100, 0.4, 1.05);
  book1D(store, "ShowerShapes", "weta2", "Lateral Shower Width w_{\\eta 2};w_{\\eta 2};Clusters", 100, 0.0, 0.035);
  book1D(store, "ShowerShapes", "f1", "First Sampling Energy Fraction f_{1};f_{1};Clusters", 100, 0.0, 0.8);
  book1D(store, "ShowerShapes", "f3", "Third Sampling Energy Fraction f_{3};f_{3};Clusters", 100, 0.0, 0.5);
  book1D(store, "ShowerShapes", "eratio", "E_{ratio} (Strip Sampling 1);E_{ratio};Clusters", 100, 0.0, 1.05);
  book1D(store, "ShowerShapes", "rhad", "Hadronic Leakage R_{had};R_{had} (E_{T}^{had} / E_{T}^{EM});Clusters", 100, -0.05, 0.35);

  // 4. Cluster Moments
  book1D(store, "Moments", "secondLambda", "Second Lambda Moment;\\langle\\lambda^{2}\\rangle [mm^{2}];Clusters", 100, 0.0, 50000.0);
  book1D(store, "Moments", "secondR", "Second Radial Moment;\\langle r^{2}\\rangle [mm^{2}];Clusters", 100, 0.0, 10000.0);
  book1D(store, "Moments", "centerLambda", "Shower Depth Center \\lambda_{center};\\lambda_{center} [mm];Clusters", 100, 0.0, 1000.0);
  book1D(store, "Moments", "fracMax", "Energy Fraction of Most Energetic Cell;f_{max};Clusters", 100, 0.0, 1.0);
  book1D(store, "Moments", "lateral", "Lateral Shower Moment;Lateral Moment;Clusters", 100, 0.0, 1.0);
  book1D(store, "Moments", "longitudinal", "Longitudinal Shower Moment;Longitudinal Moment;Clusters", 100, 0.0, 1.0);

  // 5. PID and Working Points
  auto *hPid = book1D(store, "PID", "electron_pid_pass", "Electron Identification Decisions;Working Point;Candidates", 4, 0.0, 4.0);
  if (hPid) {
    std::vector<std::string> labels{"VeryLoose", "Loose", "Medium", "Tight"};
    store->setLabels(hPid, labels);
  }

  // 6. Rings Profiles (Standard and specialised topologies)
  for (const auto &key : m_ringsKeys) {
    if (key == "Rings") {
      book1D(store, "Rings", "rings_profile", "Standard Rings Profile;Ring Index;Energy [GeV]", 100, 0.0, 100.0);
    } else if (key == "Rings_Asym") {
      book1D(store, "Rings", "rings_asym_profile", "Asymmetric Rings Profile (4 quadrants);Ring Index;Energy [GeV]", 277, 0.0, 277.0);
    } else if (key == "Rings_Cross") {
      book1D(store, "Rings", "rings_cross_profile", "Cross Rings Profile (4 arms);Ring Index;Energy [GeV]", 400, 0.0, 400.0);
    } else if (key == "Rings_Corner") {
      book1D(store, "Rings", "rings_corner_profile", "Corner Rings Profile (4 diagonal corners);Ring Index;Energy [GeV]", 400, 0.0, 400.0);
    } else if (key == "Rings_Strips") {
      book1D(store, "Rings", "rings_strips_profile", "Strips Rings Profile (1D projection);Ring Index;Energy [GeV]", 338, 0.0, 338.0);
    } else if (key == "Rings_Custom") {
      book1D(store, "Rings", "rings_custom_profile", "Custom Rings Profile (shifted rings);Ring Index;Energy [GeV]", 100, 0.0, 100.0);
    } else {
      std::string histName = key + "_profile";
      book1D(store, "Rings", histName, key + " Profile;Ring Index;Energy [GeV]", 500, 0.0, 500.0);
    }
  }

  // 7. 2D Correlations
  book2D(store, "Correlations", "reta_vs_eta", "R_{\\eta} vs \\eta;\\eta;R_{\\eta}", 50, -2.5, 2.5, 50, 0.5, 1.05);
  book2D(store, "Correlations", "weta2_vs_et", "w_{\\eta 2} vs E_{T};E_{T} [GeV];w_{\\eta 2}", 50, 0.0, 100.0, 50, 0.0, 0.035);
  book2D(store, "Correlations", "rhad_vs_eta", "R_{had} vs \\eta;\\eta;R_{had}", 50, -2.5, 2.5, 50, -0.05, 0.35);

  MSG_INFO("EgammaMonitoringMaker histogram booking completo no StoreGate sob '" << m_histDir << "'.");
  return StatusCode::SUCCESS;
}

StatusCode EgammaMonitoringMaker::pre_execute(SG::EventContext &/*ctx*/) const
{
  return StatusCode::SUCCESS;
}

StatusCode EgammaMonitoringMaker::execute(SG::EventContext &/*ctx*/, const G4Step * /*step*/) const
{
  return StatusCode::SUCCESS;
}

StatusCode EgammaMonitoringMaker::execute(SG::EventContext &/*ctx*/, int /*evt*/) const
{
  return StatusCode::SUCCESS;
}

StatusCode EgammaMonitoringMaker::post_execute(SG::EventContext &/*ctx*/) const
{
  return StatusCode::SUCCESS;
}

StatusCode EgammaMonitoringMaker::fillHistograms(SG::EventContext &ctx) const
{
  auto store = ctx.getStoreGateSvc();
  if (!store) {
    MSG_ERROR("StoreGate service not available in EventContext!");
    return StatusCode::FAILURE;
  }

  // 1. Inspeciona EventInfo
  SG::ReadHandle<xAOD::EventInfoContainer> events(m_eventInfoKey, ctx);
  if (events.isValid() && !events->empty()) {
    const auto *eventInfo = events->at(0);
    if (eventInfo) {
      fill1D(store, "EventInfo", "avgmu", eventInfo->avgmu());
      fill1D(store, "EventInfo", "totmu", eventInfo->totmu());
    }
  }

  // 2. Inspeciona CaloClusters
  SG::ReadHandle<xAOD::CaloClusterContainer> clusters(m_clusterKey, ctx);
  if (clusters.isValid()) {
    fill1D(store, "EventInfo", "n_clusters", static_cast<float>(clusters->size()));

    for (const auto *cl : *clusters) {
      if (!cl) continue;
      float et_gev = cl->et() / 1000.0f;
      float e_gev  = cl->e() / 1000.0f;
      float eta    = cl->eta();
      float phi    = cl->phi();

      fill1D(store, "Kinematics", "cl_et", et_gev);
      fill1D(store, "Kinematics", "cl_e", e_gev);
      fill1D(store, "Kinematics", "cl_eta", eta);
      fill1D(store, "Kinematics", "cl_phi", phi);

      // Shower Shapes
      fill1D(store, "ShowerShapes", "reta", cl->reta());
      fill1D(store, "ShowerShapes", "rphi", cl->rphi());
      fill1D(store, "ShowerShapes", "weta2", cl->weta2());
      fill1D(store, "ShowerShapes", "f1", cl->f1());
      fill1D(store, "ShowerShapes", "f3", cl->f3());
      fill1D(store, "ShowerShapes", "eratio", cl->eratio());
      fill1D(store, "ShowerShapes", "rhad", cl->rhad());

      // Moments
      fill1D(store, "Moments", "secondLambda", cl->secondLambda());
      fill1D(store, "Moments", "secondR", cl->secondR());
      fill1D(store, "Moments", "centerLambda", cl->lambdaCenter());
      fill1D(store, "Moments", "fracMax", cl->fracMax());
      fill1D(store, "Moments", "lateral", cl->lateralMom());
      fill1D(store, "Moments", "longitudinal", cl->longitudinalMom());

      // Correlations
      fill2D(store, "Correlations", "reta_vs_eta", eta, cl->reta());
      fill2D(store, "Correlations", "weta2_vs_et", et_gev, cl->weta2());
      fill2D(store, "Correlations", "rhad_vs_eta", eta, cl->rhad());
    }
  }

  // 3. Inspeciona Electrons
  SG::ReadHandle<xAOD::ElectronContainer> electrons(m_electronKey, ctx);
  if (electrons.isValid()) {
    fill1D(store, "EventInfo", "n_electrons", static_cast<float>(electrons->size()));

    for (const auto *el : *electrons) {
      if (!el) continue;
      float et_gev = el->et() / 1000.0f;
      float e_gev  = el->e() / 1000.0f;
      float eta    = el->eta();
      float phi    = el->phi();

      fill1D(store, "Kinematics", "el_et", et_gev);
      fill1D(store, "Kinematics", "el_e", e_gev);
      fill1D(store, "Kinematics", "el_eta", eta);
      fill1D(store, "Kinematics", "el_phi", phi);

      if (el->isVeryLoose()) fill1D(store, "PID", "electron_pid_pass", 0.5f);
      if (el->isLoose())     fill1D(store, "PID", "electron_pid_pass", 1.5f);
      if (el->isMedium())    fill1D(store, "PID", "electron_pid_pass", 2.5f);
      if (el->isTight())     fill1D(store, "PID", "electron_pid_pass", 3.5f);
    }
  }

  // 4. Inspeciona Rings
  for (const auto &key : m_ringsKeys) {
    if (key.empty()) continue;
    SG::ReadHandle<xAOD::CaloRingsContainer> rings(key, ctx);
    if (rings.isValid()) {
      std::string histName = "rings_profile";
      if (key == "Rings_Asym") histName = "rings_asym_profile";
      else if (key == "Rings_Cross") histName = "rings_cross_profile";
      else if (key == "Rings_Corner") histName = "rings_corner_profile";
      else if (key == "Rings_Strips") histName = "rings_strips_profile";
      else if (key == "Rings_Custom") histName = "rings_custom_profile";
      else if (key != "Rings") histName = key + "_profile";

      for (const auto *rg : *rings) {
        if (!rg) continue;
        const auto &vec = rg->rings();
        for (size_t r = 0; r < vec.size(); ++r) {
          fill1D(store, "Rings", histName, static_cast<float>(r), vec[r] / 1000.0f);
        }
      }
    }
  }

  return StatusCode::SUCCESS;
}

StatusCode EgammaMonitoringMaker::finalize()
{
  return StatusCode::SUCCESS;
}
